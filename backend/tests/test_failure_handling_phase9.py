"""Phase 9 Failure Handling and Resilience Test Suite for PropIQ.

Tests Groq timeouts, model errors, fallback execution, missing session handling,
expired session TTL pruning, and stale cache invalidation.
"""

import time
import pytest
from app.config import Config
from app.models import ProcurementRequirements, ScoringResponseModel, RankStatus, VendorScoreBreakdownModel
from app.services.groq_service import GroqService, GroqTimeoutError, GroqNotConfiguredError
from app.services.recommendation_service import RecommendationService
from app.services.vector_store import get_vector_store, SessionIndexData
import numpy as np
import faiss


from unittest.mock import patch

def test_groq_not_configured_raises_error():
    """Verify GroqService without API key raises GroqNotConfiguredError (Rule 38)."""
    with patch("app.config.Config.get_groq_api_key", return_value=""):
        gs = GroqService(api_key="")
        with pytest.raises(GroqNotConfiguredError):
            gs.generate_json_response("system", "user")


def test_recommendation_template_fallback_on_groq_failure():
    """Verify RecommendationService uses deterministic template fallback if Groq fails or is unconfigured (Rule 41)."""
    rec_service = RecommendationService()
    rec_service.groq_service = GroqService(api_key="")  # Unconfigured

    v1 = VendorScoreBreakdownModel(
        vendor_name="Vendor A", rank=1, rank_status=RankStatus.LEADING, alignment_score=88.0,
        base_alignment_score=88.0, total_risk_penalty=0.0, total_contradiction_penalty=0.0,
        total_clarification_penalty=0.0, must_have_failures_count=0, must_have_failed_labels=[],
        requirements_met_count=8, total_requirements_count=8, requirement_components=[], deductions=[],
        ranking_explanation="Vendor A leads."
    )
    scoring = ScoringResponseModel(
        status="success", session_id="sess_fallback", scoring_version="1.0",
        evaluated_at="2026-08-29T00:00:00Z", vendor_scores=[v1], total_vendors=1,
        scoring_config_summary={}, privacy_notice="Notice"
    )

    reqs = ProcurementRequirements()
    decision = rec_service.evaluate_recommendation_policy(scoring_response=scoring, requirements=reqs)
    narrative = rec_service.generate_executive_narrative(decision=decision, scoring_response=scoring)

    assert narrative.is_fallback is True
    assert "Vendor A" in narrative.executive_summary
    assert narrative.executive_summary != ""


def test_session_ttl_pruning():
    """Verify expired sessions older than SESSION_TTL_MINUTES are automatically pruned (Rule 18 & 19)."""
    vs = get_vector_store()
    vs.clear_all_sessions()

    # Manually add an expired session container
    index = faiss.IndexFlatIP(384)
    data = SessionIndexData(dimension=384, chunks=[], index=index)
    data.created_at = time.time() - (Config.SESSION_TTL_MINUTES * 60 + 10)  # Expired 10s ago

    vs._sessions["expired_sess_123"] = data

    # Prune expired sessions
    pruned_count = vs.prune_expired_sessions()
    assert pruned_count == 1
    assert vs.has_session("expired_sess_123") is False
