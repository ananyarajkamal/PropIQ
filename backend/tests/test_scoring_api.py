"""API integration tests for POST /api/scoring/evaluate."""

import numpy as np
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.api.routes.comparison import COMPARISON_CACHE
from app.api.routes.scoring import SCORING_CACHE, clear_scoring_cache
from app.models import (
    ComparisonResponse,
    ComparisonMatrixRow,
    RequirementEvaluationResult,
    ProcurementRequirements,
    RequirementPriority,
    ChunkMetadata,
)

client = TestClient(app)


def setup_mock_session(session_id: str = "sess_api_scoring_1"):
    """Populate vector store session and comparison cache for testing."""
    from app.services.vector_store import get_vector_store
    vs = get_vector_store()

    # Reset & create vector store session
    if vs.has_session(session_id):
        vs.delete_session(session_id)

    dummy_embeddings = np.zeros((2, 384), dtype=np.float32)
    dummy_chunks = [
        ChunkMetadata(chunk_id="c1", vendor_name="Northstar Systems", source_filename="n.pdf", start_page=1, end_page=1, character_count=10, text="text1"),
        ChunkMetadata(chunk_id="c2", vendor_name="Meridian Labs", source_filename="m.pdf", start_page=1, end_page=1, character_count=10, text="text2"),
    ]
    vs.create_session_index(session_id, dummy_embeddings, dummy_chunks)

    reqs = ProcurementRequirements(
        warranty_value=12,
        warranty_unit="months",
        warranty_priority=RequirementPriority.MUST_HAVE,
    )

    rows = [
        ComparisonMatrixRow(
            category="Warranty",
            requirement_label="Minimum Warranty (12 months)",
            vendor_evaluations={
                "Northstar Systems": RequirementEvaluationResult(
                    requirement_id="REQ_WARRANTY", category="Warranty", vendor_name="Northstar Systems", status="MEETS", raw_vendor_value="12m", explanation="Meets requirement", comparison_rule="w>=12"
                ),
                "Meridian Labs": RequirementEvaluationResult(
                    requirement_id="REQ_WARRANTY", category="Warranty", vendor_name="Meridian Labs", status="MISSING", explanation="No warranty listed", comparison_rule="w>=12"
                ),
            },
        )
    ]

    comp_resp = ComparisonResponse(
        status="success",
        session_id=session_id,
        requirements=reqs,
        matrix_rows=rows,
        vendor_summary_counts={"Northstar Systems": {"MEETS": 1}, "Meridian Labs": {"MISSING": 1}},
        privacy_notice="Notice",
    )

    COMPARISON_CACHE[session_id] = comp_resp

    import hashlib
    import json
    reqs_fp = hashlib.sha256(json.dumps(reqs.model_dump(), sort_keys=True, default=str).encode()).hexdigest()[:12]
    comp_fp = hashlib.sha256(json.dumps([r.model_dump() for r in rows], sort_keys=True, default=str).encode()).hexdigest()[:12]
    risk_fp = hashlib.sha256(json.dumps([], sort_keys=True, default=str).encode()).hexdigest()[:12]
    clrf_fp = hashlib.sha256(json.dumps([], sort_keys=True, default=str).encode()).hexdigest()[:12]

    from app.services.session_state_service import get_session_state_service
    from app.models import ModuleStatus
    state_service = get_session_state_service()
    state_service.on_proposals_changed(session_id, f"prop_{session_id}")
    state_service.on_requirements_changed(session_id, reqs_fp)
    state_service.set_module_status(session_id, "comparison", ModuleStatus.COMPLETED, comp_fp)
    state_service.set_module_status(session_id, "risks_contradictions", ModuleStatus.COMPLETED, risk_fp)
    state_service.set_module_status(session_id, "clarifications", ModuleStatus.COMPLETED, clrf_fp)

    return session_id, reqs


def test_scoring_evaluate_endpoint_success():
    """Verify POST /api/scoring/evaluate returns 200 OK with deterministic score breakdown."""
    sid, reqs = setup_mock_session("sess_api_scoring_1")

    payload = {"session_id": sid, "requirements": reqs.model_dump()}
    response = client.post("/api/scoring/evaluate", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "success"
    assert data["session_id"] == sid
    assert data["total_vendors"] == 2
    assert len(data["vendor_scores"]) == 2

    v1 = data["vendor_scores"][0]
    assert v1["vendor_name"] == "Northstar Systems"
    assert v1["rank"] == 1
    assert v1["alignment_score"] == 100.0

    v2 = data["vendor_scores"][1]
    assert v2["vendor_name"] == "Meridian Labs"
    assert v2["rank"] == 2
    assert v2["alignment_score"] == 0.0  # MISSING receives 0.0 points -> 0.0%


def test_scoring_evaluate_unknown_session_404():
    """Verify POST /api/scoring/evaluate returns 404 for unknown session ID."""
    payload = {"session_id": "non_existent_session"}
    response = client.post("/api/scoring/evaluate", json=payload)
    assert response.status_code == 404


def test_scoring_api_trust_boundary_injection_rejected():
    """Verify client-injected fake scores or penalties are ignored by backend API (Rule 40 & 93)."""
    sid, reqs = setup_mock_session("sess_api_scoring_trust")

    # Client attempts to send fake score 100 and rank 1 for Meridian Labs
    payload = {
        "session_id": sid,
        "requirements": reqs.model_dump(),
        "score": 100.0,
        "rank": 1,
        "risk_penalty": 0.0,
    }
    response = client.post("/api/scoring/evaluate", json=payload)
    assert response.status_code == 200
    data = response.json()

    # Backend MUST compute trusted score: Meridian Labs remains rank 2 with score 0.0!
    meridian = next(v for v in data["vendor_scores"] if v["vendor_name"] == "Meridian Labs")
    assert meridian["rank"] == 2
    assert meridian["alignment_score"] == 0.0


def test_versioned_scoring_cache_hit_and_invalidation():
    """Verify versioned cache identity hit on identical upstream state and invalidation on requirement edit (Hardening Fix 1)."""
    sid, reqs = setup_mock_session("sess_api_scoring_cache_ver")

    # 1. Initial request -> cache miss, calculated & stored under deterministic fingerprint
    res1 = client.post("/api/scoring/evaluate", json={"session_id": sid, "requirements": reqs.model_dump()})
    assert res1.status_code == 200
    cache_keys_1 = [k for k in SCORING_CACHE.keys() if k.startswith(f"{sid}_")]
    assert len(cache_keys_1) == 1
    fp1 = cache_keys_1[0]

    # 2. Second request with same upstream state -> cache hit on fingerprint
    res2 = client.post("/api/scoring/evaluate", json={"session_id": sid, "requirements": reqs.model_dump()})
    assert res2.status_code == 200
    assert fp1 in SCORING_CACHE

    # 3. Requirement priority edit -> saved requirements update fingerprint -> re-evaluate comparison
    old_comp_resp = COMPARISON_CACHE[sid]
    reqs_edited = reqs.model_copy(update={"warranty_priority": RequirementPriority.LOW})
    client.post("/api/analysis/requirements", json={"session_id": sid, "requirements": reqs_edited.model_dump()})
    COMPARISON_CACHE[sid] = old_comp_resp

    import hashlib
    import json
    from app.services.session_state_service import get_session_state_service
    from app.models import ModuleStatus
    state_service = get_session_state_service()

    comp_rows = old_comp_resp.matrix_rows
    comp_fp = hashlib.sha256(json.dumps([r.model_dump() for r in comp_rows], sort_keys=True, default=str).encode()).hexdigest()[:12]
    clrf_fp = hashlib.sha256(json.dumps([], sort_keys=True, default=str).encode()).hexdigest()[:12]

    state_service.set_module_status(sid, "comparison", ModuleStatus.COMPLETED, comp_fp)
    state_service.set_module_status(sid, "clarifications", ModuleStatus.COMPLETED, clrf_fp)

    res3 = client.post("/api/scoring/evaluate", json={"session_id": sid, "requirements": reqs_edited.model_dump()})
    assert res3.status_code == 200
    cache_keys_2 = [k for k in SCORING_CACHE.keys() if k.startswith(f"{sid}_")]
    assert fp1 not in SCORING_CACHE  # Old fingerprint invalidated when requirements changed!
    assert len(cache_keys_2) == 1


def test_zero_groq_calls_on_scoring_and_rescore(monkeypatch):
    """Verify 0 Groq calls are made during initial scoring and requirement priority rescore (Rule 114)."""
    sid, reqs = setup_mock_session("sess_api_scoring_zero_groq")

    groq_call_counter = 0

    def mock_groq_generate(*args, **kwargs):
        nonlocal groq_call_counter
        groq_call_counter += 1
        return '{"test": true}'

    from app.services.groq_service import GroqService
    monkeypatch.setattr(GroqService, "generate_json_response", mock_groq_generate)

    # Initial scoring evaluation
    res1 = client.post("/api/scoring/evaluate", json={"session_id": sid, "requirements": reqs.model_dump()})
    assert res1.status_code == 200

    # Rescore with edited requirement priority
    old_comp_resp = COMPARISON_CACHE[sid]
    reqs_edited = reqs.model_copy(update={"warranty_priority": RequirementPriority.LOW})
    client.post("/api/analysis/requirements", json={"session_id": sid, "requirements": reqs_edited.model_dump()})
    COMPARISON_CACHE[sid] = old_comp_resp

    import hashlib
    import json
    from app.services.session_state_service import get_session_state_service
    from app.models import ModuleStatus
    state_service = get_session_state_service()

    comp_rows = old_comp_resp.matrix_rows
    comp_fp = hashlib.sha256(json.dumps([r.model_dump() for r in comp_rows], sort_keys=True, default=str).encode()).hexdigest()[:12]
    clrf_fp = hashlib.sha256(json.dumps([], sort_keys=True, default=str).encode()).hexdigest()[:12]

    state_service.set_module_status(sid, "comparison", ModuleStatus.COMPLETED, comp_fp)
    state_service.set_module_status(sid, "clarifications", ModuleStatus.COMPLETED, clrf_fp)

    res2 = client.post("/api/scoring/evaluate", json={"session_id": sid, "requirements": reqs_edited.model_dump()})
    assert res2.status_code == 200

    # Verify ZERO Groq calls were executed!
    assert groq_call_counter == 0
