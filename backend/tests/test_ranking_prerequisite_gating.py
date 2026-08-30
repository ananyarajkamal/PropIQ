"""Comprehensive test suite for PropIQ Vendor Ranking Prerequisite Gating.

Validates explicit module execution statuses (NOT_STARTED, RUNNING, COMPLETED, FAILED, STALE),
dependency-aware cache invalidation, version fingerprint staleness, and structured HTTP 409 responses.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models import (
    ProcurementRequirements,
    ComparisonMatrixRow,
    RequirementEvaluationResult,
    ComparisonResponse,
    RiskAnalysisResponse,
    ClarificationResponseModel,
    ModuleStatus,
)
from app.services.vector_store import get_vector_store
from app.services.session_state_service import get_session_state_service, SESSION_WORKFLOW_STATES
from app.api.routes.comparison import COMPARISON_CACHE, FACT_SHEETS_CACHE
from app.api.routes.risks import RISK_ANALYSIS_CACHE
from app.api.routes.clarifications import CLARIFICATION_CACHE
from app.api.routes.scoring import SCORING_CACHE
from app.api.routes.recommendation import RECOMMENDATION_CACHE

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_session_state():
    """Reset session state and in-memory caches before each test."""
    SESSION_WORKFLOW_STATES.clear()
    COMPARISON_CACHE.clear()
    FACT_SHEETS_CACHE.clear()
    RISK_ANALYSIS_CACHE.clear()
    CLARIFICATION_CACHE.clear()
    SCORING_CACHE.clear()
    RECOMMENDATION_CACHE.clear()
    yield


def setup_mock_session(session_id: str = "sess_gating_test_12345"):
    """Initialize mock session index in vector store and state service."""
    import numpy as np
    from app.models import ChunkMetadata
    vector_store = get_vector_store()
    if vector_store.has_session(session_id):
        vector_store.delete_session(session_id)

    dummy_embeddings = np.zeros((2, 384), dtype=np.float32)
    dummy_chunks = [
        ChunkMetadata(chunk_id="c1", vendor_name="Vendor Alpha", source_filename="a.pdf", start_page=1, end_page=1, character_count=10, text="text1"),
        ChunkMetadata(chunk_id="c2", vendor_name="Vendor Beta", source_filename="b.pdf", start_page=1, end_page=1, character_count=10, text="text2"),
    ]
    vector_store.create_session_index(session_id, dummy_embeddings, dummy_chunks)

    state_service = get_session_state_service()
    state_service.on_proposals_changed(session_id, proposal_fp=f"prop_{session_id}")
    return session_id


def test_comparison_completed_but_risks_not_started_blocks_ranking():
    """Verify ranking endpoint returns HTTP 409 when comparison is complete but risks are NOT_STARTED."""
    sid = setup_mock_session()
    state_service = get_session_state_service()

    import hashlib
    import json

    # Save requirements
    reqs = ProcurementRequirements(budget_ceiling=100000)
    reqs_fp = hashlib.sha256(json.dumps(reqs.model_dump(), sort_keys=True, default=str).encode()).hexdigest()[:12]
    state_service.on_requirements_changed(sid, reqs_fp)

    rows = [
        ComparisonMatrixRow(
            requirement_id="REQ_BUDGET",
            category="Pricing",
            requirement_name="Budget Ceiling",
            requirement_label="Budget Ceiling",
            buyer_target_summary="Target $100k",
            vendor_evaluations={
                "Vendor Alpha": RequirementEvaluationResult(
                    requirement_id="REQ_BUDGET",
                    category="Pricing",
                    vendor_name="Vendor Alpha",
                    status="MEETS",
                    explanation="Within budget",
                    comparison_rule="b <= 100k",
                )
            }
        )
    ]
    comp_fp = hashlib.sha256(json.dumps([r.model_dump() for r in rows], sort_keys=True, default=str).encode()).hexdigest()[:12]

    # Set comparison COMPLETED
    state_service.set_module_status(sid, "comparison", ModuleStatus.COMPLETED, fingerprint=comp_fp)
    COMPARISON_CACHE[sid] = ComparisonResponse(
        status="success",
        session_id=sid,
        requirements=reqs,
        matrix_rows=rows,
        vendor_summary_counts={"Vendor Alpha": {"MEETS": 1}},
        privacy_notice="Notice",
    )

    # Attempt evaluate scoring while risks_contradictions is NOT_STARTED
    resp = client.post("/api/scoring/evaluate", json={"session_id": sid, "requirements": reqs.model_dump()})
    assert resp.status_code == 409
    data = resp.json()
    assert data["ranking_status"] == "BLOCKED"
    assert "risks_contradictions" in data["blocking_prerequisites"]


def test_completed_risks_and_clarifications_with_zero_findings_allows_ranking():
    """Verify ranking succeeds when upstream modules are COMPLETED even with 0 findings ([])."""
    sid = setup_mock_session()
    state_service = get_session_state_service()

    import hashlib
    import json

    reqs = ProcurementRequirements(budget_ceiling=100000)
    reqs_fp = hashlib.sha256(json.dumps(reqs.model_dump(), sort_keys=True, default=str).encode()).hexdigest()[:12]
    state_service.on_requirements_changed(sid, reqs_fp)

    rows = [
        ComparisonMatrixRow(
            requirement_id="REQ_BUDGET",
            category="Pricing",
            requirement_name="Budget Ceiling",
            requirement_label="Budget Ceiling",
            buyer_target_summary="Target $100k",
            vendor_evaluations={
                "Vendor Alpha": RequirementEvaluationResult(
                    requirement_id="REQ_BUDGET",
                    category="Pricing",
                    vendor_name="Vendor Alpha",
                    status="MEETS",
                    explanation="Within budget",
                    comparison_rule="b <= 100k",
                )
            }
        )
    ]
    comp_fp = hashlib.sha256(json.dumps([r.model_dump() for r in rows], sort_keys=True, default=str).encode()).hexdigest()[:12]

    # 1. Comparison COMPLETED
    comp_resp = ComparisonResponse(
        status="success",
        session_id=sid,
        requirements=reqs,
        matrix_rows=rows,
        vendor_summary_counts={"Vendor Alpha": {"MEETS": 1}},
        privacy_notice="Notice",
    )
    COMPARISON_CACHE[sid] = comp_resp
    state_service.set_module_status(sid, "comparison", ModuleStatus.COMPLETED, fingerprint=comp_fp)

    # 2. Risks & Contradictions COMPLETED with [] findings
    RISK_ANALYSIS_CACHE[sid] = RiskAnalysisResponse(
        status="success",
        session_id=sid,
        risk_findings=[],
        contradiction_findings=[],
        high_priority_count=0,
        medium_priority_count=0,
        needs_clarification_count=0,
        contradictions_count=0,
        privacy_notice="Notice",
    )
    risk_fp = hashlib.sha256(json.dumps([], sort_keys=True, default=str).encode()).hexdigest()[:12]
    state_service.set_module_status(sid, "risks_contradictions", ModuleStatus.COMPLETED, fingerprint=risk_fp)

    # 3. Clarifications COMPLETED with [] questions
    CLARIFICATION_CACHE[sid] = ClarificationResponseModel(
        status="success",
        session_id=sid,
        questions=[],
        total_questions=0,
        high_priority_count=0,
        medium_priority_count=0,
        low_priority_count=0,
        conflicting_details_count=0,
        vendor_question_counts={},
        privacy_notice="Notice",
    )
    clrf_fp = hashlib.sha256(json.dumps([], sort_keys=True, default=str).encode()).hexdigest()[:12]
    state_service.set_module_status(sid, "clarifications", ModuleStatus.COMPLETED, fingerprint=clrf_fp)

    # Scoring should now execute successfully
    resp = client.post("/api/scoring/evaluate", json={"session_id": sid, "requirements": reqs.model_dump()})
    assert resp.status_code == 200, resp.json()
    data = resp.json()
    assert data["status"] == "success"
    assert len(data["vendor_scores"]) > 0


def test_failed_risk_analysis_blocks_ranking():
    """Verify ranking is BLOCKED if risk analysis module status is FAILED."""
    sid = setup_mock_session()
    state_service = get_session_state_service()

    state_service.set_module_status(sid, "comparison", ModuleStatus.COMPLETED, fingerprint="comp_v1")
    state_service.set_module_status(sid, "risks_contradictions", ModuleStatus.FAILED, error_msg="Groq Timeout")

    resp = client.post("/api/scoring/evaluate", json={"session_id": sid})
    assert resp.status_code == 409
    data = resp.json()
    assert data["prerequisites"]["risks_contradictions"] == "FAILED"


def test_requirement_change_invalidates_downstream_ranking_and_recommendation():
    """Verify saving new requirements marks comparison/ranking STALE while preserving requirement-independent risks."""
    sid = setup_mock_session()
    state_service = get_session_state_service()

    # 1. Complete all V1 analyses
    state_service.on_requirements_changed(sid, "reqs_v1")
    state_service.set_module_status(sid, "comparison", ModuleStatus.COMPLETED, fingerprint="comp_v1")
    state_service.set_module_status(sid, "risks_contradictions", ModuleStatus.COMPLETED, fingerprint="risk_v1")
    state_service.set_module_status(sid, "clarifications", ModuleStatus.COMPLETED, fingerprint="clrf_v1")
    state_service.set_module_status(sid, "ranking", ModuleStatus.COMPLETED, fingerprint="rnk_v1")

    # Verify ranking is initial COMPLETED
    assert state_service.get_module_status(sid, "ranking") == ModuleStatus.COMPLETED

    # 2. Change requirements to V2
    client.post("/api/analysis/requirements", json={
        "session_id": sid,
        "requirements": {"budget_ceiling": 200000}
    })

    # Verification:
    # - risks_contradictions remains COMPLETED (requirement-independent!)
    # - comparison, clarifications, ranking become STALE/NOT_STARTED
    assert state_service.get_module_status(sid, "risks_contradictions") == ModuleStatus.COMPLETED
    assert state_service.get_module_status(sid, "ranking") in {ModuleStatus.STALE, ModuleStatus.NOT_STARTED}

    # Attempt ranking now -> BLOCKED
    resp = client.post("/api/scoring/evaluate", json={"session_id": sid})
    assert resp.status_code == 409


def test_recommendation_requires_completed_ranking():
    """Verify recommendation endpoint blocks if ranking has not been completed."""
    sid = setup_mock_session()
    COMPARISON_CACHE[sid] = ComparisonResponse(
        status="success",
        session_id=sid,
        requirements=ProcurementRequirements(),
        matrix_rows=[
            ComparisonMatrixRow(
                requirement_id="REQ_BUDGET", category="Pricing", requirement_name="Budget", requirement_label="Budget", buyer_target_summary="Target", vendor_evaluations={"Vendor Alpha": RequirementEvaluationResult(requirement_id="REQ_BUDGET", category="Pricing", vendor_name="Vendor Alpha", status="MEETS", explanation="ok", comparison_rule="rule")}
            )
        ],
        vendor_summary_counts={"Vendor Alpha": {"MEETS": 1}},
        privacy_notice="Notice",
    )

    resp = client.post("/api/recommendation/generate", json={"session_id": sid})
    assert resp.status_code == 409
    assert "Vendor Ranking" in resp.json()["detail"]
