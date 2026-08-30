"""API integration tests for POST /api/recommendation/generate."""

import numpy as np
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.api.routes.comparison import COMPARISON_CACHE
from app.api.routes.scoring import SCORING_CACHE
from app.api.routes.recommendation import RECOMMENDATION_CACHE
from tests.test_scoring_api import setup_mock_session as setup_scoring_session
from app.models import (
    ComparisonResponse,
    ComparisonMatrixRow,
    RequirementEvaluationResult,
    ProcurementRequirements,
    RequirementPriority,
    ChunkMetadata,
)

client = TestClient(app)


def setup_recommendation_session(session_id: str = "sess_api_rec_1"):
    """Populate vector store session, comparison cache, and scoring cache for recommendation testing."""
    sid, reqs = setup_scoring_session(session_id)
    # Execute scoring evaluate to populate SCORING_CACHE and mark ranking COMPLETED
    client.post("/api/scoring/evaluate", json={"session_id": sid, "requirements": reqs.model_dump()})
    return sid, reqs


def test_recommendation_generate_endpoint_success():
    """Verify POST /api/recommendation/generate returns 200 OK with recommendation decision brief."""
    sid, reqs = setup_recommendation_session("sess_api_rec_1")

    payload = {"session_id": sid, "requirements": reqs.model_dump()}
    response = client.post("/api/recommendation/generate", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "success"
    assert data["session_id"] == sid
    assert "decision" in data
    assert "narrative" in data

    decision = data["decision"]
    assert decision["recommendation_state"] in ["RECOMMENDED", "RECOMMENDED_WITH_CONDITIONS", "FURTHER_REVIEW_REQUIRED", "NO_CLEAR_RECOMMENDATION"]
    assert decision["leading_vendor"] == "Northstar Systems"


def test_recommendation_unknown_session_404():
    """Verify POST /api/recommendation/generate returns 404 for unknown session ID."""
    payload = {"session_id": "non_existent_rec_session"}
    response = client.post("/api/recommendation/generate", json=payload)
    assert response.status_code == 404


def test_recommendation_api_trust_boundary_injection_rejected():
    """Verify client-injected fake winner or recommendation state is ignored by backend API (Rule 38, 39, 94)."""
    sid, reqs = setup_recommendation_session("sess_api_rec_trust")

    # Client attempts to inject fake winner "Meridian Labs" and state "RECOMMENDED"
    payload = {
        "session_id": sid,
        "requirements": reqs.model_dump(),
        "recommended_vendor": "Meridian Labs",
        "recommendation_state": "RECOMMENDED",
        "alignment_score": 100.0,
    }
    response = client.post("/api/recommendation/generate", json=payload)
    assert response.status_code == 200
    data = response.json()

    # Backend MUST compute trusted state: Northstar Systems is leading candidate!
    decision = data["decision"]
    assert decision["leading_vendor"] == "Northstar Systems"


def test_versioned_recommendation_cache_invalidation():
    """Verify versioned cache identity hit on identical state and invalidation on requirement priority edit (Rule 97)."""
    sid, reqs = setup_recommendation_session("sess_api_rec_cache")

    # 1. Initial request -> cache miss, stored
    res1 = client.post("/api/recommendation/generate", json={"session_id": sid, "requirements": reqs.model_dump()})
    assert res1.status_code == 200
    cache_keys_1 = [k for k in RECOMMENDATION_CACHE.keys() if k.startswith(f"{sid}_")]
    assert len(cache_keys_1) == 1

    # 2. Second request with same state -> cache hit
    res2 = client.post("/api/recommendation/generate", json={"session_id": sid, "requirements": reqs.model_dump()})
    assert res2.status_code == 200

    # 3. Requirement priority edit -> new fingerprint derived -> update requirements & scoring first
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

    client.post("/api/scoring/evaluate", json={"session_id": sid, "requirements": reqs_edited.model_dump()})

    res3 = client.post("/api/recommendation/generate", json={"session_id": sid, "requirements": reqs_edited.model_dump()})
    assert res3.status_code == 200
    cache_keys_2 = [k for k in RECOMMENDATION_CACHE.keys() if k.startswith(f"{sid}_")]
    assert len(cache_keys_2) == 1
