"""Unit tests for RecommendationService policy logic and executive decision brief synthesis."""

import pytest
from app.models import (
    RecommendationState,
    RequirementPriority,
    RankStatus,
    ProcurementRequirements,
    ScoringResponseModel,
    VendorScoreBreakdownModel,
    RequirementScoreComponentModel,
    RiskFindingModel,
    RiskCategory,
    RiskSeverity,
    ContradictionFindingModel,
    ContradictionStatus,
    ClarificationQuestionModel,
    ClarificationReason,
    QuestionPriority,
    EvidenceCitationModel,
)
from app.services.recommendation_service import RecommendationService


def build_mock_scoring(
    v1_score: float = 88.0,
    v2_score: float = 78.0,
    v1_must_have_failures: int = 0,
    v1_rank_status: RankStatus = RankStatus.LEADING,
) -> ScoringResponseModel:
    """Construct mock ScoringResponseModel for testing recommendation policy rules."""
    cit = EvidenceCitationModel(
        evidence_id="E1",
        vendor_name="Vendor A",
        source_filename="a.pdf",
        start_page=1,
        end_page=1,
        chunk_id="c1",
        excerpt_text="Excerpt",
    )

    v1 = VendorScoreBreakdownModel(
        vendor_name="Vendor A",
        rank=1,
        rank_status=v1_rank_status,
        alignment_score=v1_score,
        base_alignment_score=v1_score,
        total_risk_penalty=0.0,
        total_contradiction_penalty=0.0,
        total_clarification_penalty=0.0,
        must_have_failures_count=v1_must_have_failures,
        must_have_failed_labels=["Minimum SLA Uptime (99.9%)"] if v1_must_have_failures > 0 else [],
        requirements_met_count=8,
        total_requirements_count=8,
        requirement_components=[],
        deductions=[],
        ranking_explanation="Vendor A leads.",
    )

    v2 = VendorScoreBreakdownModel(
        vendor_name="Vendor B",
        rank=2,
        rank_status=RankStatus.COMPETITIVE if v1_rank_status != RankStatus.TIED else RankStatus.TIED,
        alignment_score=v2_score,
        base_alignment_score=v2_score,
        total_risk_penalty=0.0,
        total_contradiction_penalty=0.0,
        total_clarification_penalty=0.0,
        must_have_failures_count=0,
        must_have_failed_labels=[],
        requirements_met_count=7,
        total_requirements_count=8,
        requirement_components=[],
        deductions=[],
        ranking_explanation="Vendor B ranks 2nd.",
    )

    return ScoringResponseModel(
        status="success",
        session_id="sess_rec_test",
        scoring_version="1.0",
        evaluated_at="2026-08-29T00:00:00Z",
        vendor_scores=[v1, v2],
        total_vendors=2,
        scoring_config_summary={},
        privacy_notice="Notice",
    )


def test_recommendation_unconditional_recommended():
    """Verify clean Rank 1 vendor with wide score gap returns RECOMMENDED."""
    rec_service = RecommendationService()
    scoring = build_mock_scoring(v1_score=88.0, v2_score=78.0)
    reqs = ProcurementRequirements()

    decision = rec_service.evaluate_recommendation_policy(scoring_response=scoring, requirements=reqs)
    assert decision.recommendation_state == RecommendationState.RECOMMENDED
    assert decision.recommended_vendor == "Vendor A"
    assert decision.score_gap == 10.0
    assert decision.is_clear_leader is True
    assert decision.is_close_leader is False


# --- Boundary Tests (Phase 8 Policy Hardening Section 3) ---

def test_score_gap_boundary_0_4_tied():
    """Verify score gap of 0.4 (< 0.5 tie threshold) produces NO_CLEAR_RECOMMENDATION (Tied)."""
    rec_service = RecommendationService()
    scoring = build_mock_scoring(v1_score=80.4, v2_score=80.0)
    reqs = ProcurementRequirements()

    decision = rec_service.evaluate_recommendation_policy(scoring_response=scoring, requirements=reqs)
    assert decision.recommendation_state == RecommendationState.NO_CLEAR_RECOMMENDATION
    assert decision.recommended_vendor is None
    assert decision.is_close_leader is False
    assert decision.is_clear_leader is False


def test_score_gap_boundary_0_50_close_leader():
    """Verify score gap of 0.50 (exact tie threshold) produces RECOMMENDED with is_close_leader = True."""
    rec_service = RecommendationService()
    scoring = build_mock_scoring(v1_score=80.5, v2_score=80.0)
    reqs = ProcurementRequirements()

    decision = rec_service.evaluate_recommendation_policy(scoring_response=scoring, requirements=reqs)
    assert decision.recommendation_state == RecommendationState.RECOMMENDED
    assert decision.recommended_vendor == "Vendor A"
    assert decision.score_gap == 0.5
    assert decision.is_close_leader is True
    assert decision.is_clear_leader is False


def test_score_gap_boundary_0_6_close_leader():
    """Verify score gap of 0.6 produces RECOMMENDED with is_close_leader = True."""
    rec_service = RecommendationService()
    scoring = build_mock_scoring(v1_score=80.6, v2_score=80.0)
    reqs = ProcurementRequirements()

    decision = rec_service.evaluate_recommendation_policy(scoring_response=scoring, requirements=reqs)
    assert decision.recommendation_state == RecommendationState.RECOMMENDED
    assert decision.recommended_vendor == "Vendor A"
    assert decision.score_gap == 0.6
    assert decision.is_close_leader is True
    assert decision.is_clear_leader is False


def test_score_gap_boundary_1_9_close_leader():
    """Verify score gap of 1.9 (< 2.0 threshold) produces is_close_leader = True."""
    rec_service = RecommendationService()
    scoring = build_mock_scoring(v1_score=81.9, v2_score=80.0)
    reqs = ProcurementRequirements()

    decision = rec_service.evaluate_recommendation_policy(scoring_response=scoring, requirements=reqs)
    assert decision.recommendation_state == RecommendationState.RECOMMENDED
    assert decision.recommended_vendor == "Vendor A"
    assert decision.score_gap == 1.9
    assert decision.is_close_leader is True
    assert decision.is_clear_leader is False


def test_score_gap_boundary_2_00_clear_leader():
    """Verify score gap of 2.00 (exact CLOSE_LEADER_THRESHOLD) produces is_clear_leader = True."""
    rec_service = RecommendationService()
    scoring = build_mock_scoring(v1_score=82.0, v2_score=80.0)
    reqs = ProcurementRequirements()

    decision = rec_service.evaluate_recommendation_policy(scoring_response=scoring, requirements=reqs)
    assert decision.recommendation_state == RecommendationState.RECOMMENDED
    assert decision.recommended_vendor == "Vendor A"
    assert decision.score_gap == 2.0
    assert decision.is_close_leader is False
    assert decision.is_clear_leader is True


def test_score_gap_boundary_2_1_clear_leader():
    """Verify score gap of 2.1 (> 2.0 threshold) produces is_clear_leader = True."""
    rec_service = RecommendationService()
    scoring = build_mock_scoring(v1_score=82.1, v2_score=80.0)
    reqs = ProcurementRequirements()

    decision = rec_service.evaluate_recommendation_policy(scoring_response=scoring, requirements=reqs)
    assert decision.recommendation_state == RecommendationState.RECOMMENDED
    assert decision.recommended_vendor == "Vendor A"
    assert decision.score_gap == 2.1
    assert decision.is_close_leader is False
    assert decision.is_clear_leader is True


# --- Contradiction Materiality Tests (Phase 8 Policy Hardening Section 4) ---

def test_confirmed_pricing_contradiction_forces_further_review():
    """Verify CONFIRMED contradiction in Pricing (CORE_COMMERCIAL) forces FURTHER_REVIEW_REQUIRED."""
    rec_service = RecommendationService()
    scoring = build_mock_scoring(v1_score=90.0, v2_score=75.0)
    reqs = ProcurementRequirements()
    cit = EvidenceCitationModel(evidence_id="E1", vendor_name="Vendor A", source_filename="a.pdf", start_page=1, end_page=1, chunk_id="c1", excerpt_text="Text")

    ctrs = [
        ContradictionFindingModel(
            contradiction_id="ctr_price",
            vendor_name="Vendor A",
            category="Pricing",
            severity=RiskSeverity.HIGH,
            statement_a="$10,000",
            statement_b="$15,000",
            evidence_a=[cit],
            evidence_b=[cit],
            reason="Inconsistent pricing terms",
            status=ContradictionStatus.CONFIRMED_CONTRADICTION,
        )
    ]

    decision = rec_service.evaluate_recommendation_policy(scoring_response=scoring, requirements=reqs, contradictions=ctrs)
    assert decision.recommendation_state == RecommendationState.FURTHER_REVIEW_REQUIRED
    assert decision.recommended_vendor is None
    assert decision.has_core_commercial_contradiction is True


def test_confirmed_sla_contradiction_forces_further_review():
    """Verify CONFIRMED contradiction in SLA (CORE_COMMERCIAL) forces FURTHER_REVIEW_REQUIRED."""
    rec_service = RecommendationService()
    scoring = build_mock_scoring(v1_score=90.0, v2_score=75.0)
    reqs = ProcurementRequirements()
    cit = EvidenceCitationModel(evidence_id="E1", vendor_name="Vendor A", source_filename="a.pdf", start_page=1, end_page=1, chunk_id="c1", excerpt_text="Text")

    ctrs = [
        ContradictionFindingModel(
            contradiction_id="ctr_sla",
            vendor_name="Vendor A",
            category="SLA",
            severity=RiskSeverity.HIGH,
            statement_a="99.9%",
            statement_b="99.0%",
            evidence_a=[cit],
            evidence_b=[cit],
            reason="Inconsistent SLA claims",
            status=ContradictionStatus.CONFIRMED_CONTRADICTION,
        )
    ]

    decision = rec_service.evaluate_recommendation_policy(scoring_response=scoring, requirements=reqs, contradictions=ctrs)
    assert decision.recommendation_state == RecommendationState.FURTHER_REVIEW_REQUIRED
    assert decision.recommended_vendor is None
    assert decision.has_core_commercial_contradiction is True


def test_confirmed_timeline_contradiction_forces_further_review():
    """Verify CONFIRMED contradiction in Implementation Timeline (CORE_COMMERCIAL) forces FURTHER_REVIEW_REQUIRED."""
    rec_service = RecommendationService()
    scoring = build_mock_scoring(v1_score=90.0, v2_score=75.0)
    reqs = ProcurementRequirements()
    cit = EvidenceCitationModel(evidence_id="E1", vendor_name="Vendor A", source_filename="a.pdf", start_page=1, end_page=1, chunk_id="c1", excerpt_text="Text")

    ctrs = [
        ContradictionFindingModel(
            contradiction_id="ctr_time",
            vendor_name="Vendor A",
            category="Implementation Timeline",
            severity=RiskSeverity.HIGH,
            statement_a="30 days",
            statement_b="90 days",
            evidence_a=[cit],
            evidence_b=[cit],
            reason="Inconsistent deployment timeline",
            status=ContradictionStatus.CONFIRMED_CONTRADICTION,
        )
    ]

    decision = rec_service.evaluate_recommendation_policy(scoring_response=scoring, requirements=reqs, contradictions=ctrs)
    assert decision.recommendation_state == RecommendationState.FURTHER_REVIEW_REQUIRED
    assert decision.recommended_vendor is None
    assert decision.has_core_commercial_contradiction is True


def test_confirmed_non_core_contradiction_produces_conditional():
    """Verify CONFIRMED contradiction in non-core category produces RECOMMENDED_WITH_CONDITIONS."""
    rec_service = RecommendationService()
    scoring = build_mock_scoring(v1_score=90.0, v2_score=75.0)
    reqs = ProcurementRequirements()
    cit = EvidenceCitationModel(evidence_id="E1", vendor_name="Vendor A", source_filename="a.pdf", start_page=1, end_page=1, chunk_id="c1", excerpt_text="Text")

    ctrs = [
        ContradictionFindingModel(
            contradiction_id="ctr_noncore",
            vendor_name="Vendor A",
            category="Marketing Assets",
            severity=RiskSeverity.LOW,
            statement_a="Logo allowed",
            statement_b="Logo restricted",
            evidence_a=[cit],
            evidence_b=[cit],
            reason="Minor branding disagreement",
            status=ContradictionStatus.CONFIRMED_CONTRADICTION,
        )
    ]

    decision = rec_service.evaluate_recommendation_policy(scoring_response=scoring, requirements=reqs, contradictions=ctrs)
    assert decision.recommendation_state == RecommendationState.RECOMMENDED_WITH_CONDITIONS
    assert decision.recommended_vendor == "Vendor A"
    assert decision.has_core_commercial_contradiction is False


def test_potential_contradiction_produces_conditional():
    """Verify POTENTIAL contradiction produces RECOMMENDED_WITH_CONDITIONS."""
    rec_service = RecommendationService()
    scoring = build_mock_scoring(v1_score=90.0, v2_score=75.0)
    reqs = ProcurementRequirements()
    cit = EvidenceCitationModel(evidence_id="E1", vendor_name="Vendor A", source_filename="a.pdf", start_page=1, end_page=1, chunk_id="c1", excerpt_text="Text")

    ctrs = [
        ContradictionFindingModel(
            contradiction_id="ctr_pot",
            vendor_name="Vendor A",
            category="Pricing",
            severity=RiskSeverity.MEDIUM,
            statement_a="Annual billing",
            statement_b="Monthly billing",
            evidence_a=[cit],
            evidence_b=[cit],
            reason="Potential billing frequency ambiguity",
            status=ContradictionStatus.POTENTIAL_CONTRADICTION,
        )
    ]

    decision = rec_service.evaluate_recommendation_policy(scoring_response=scoring, requirements=reqs, contradictions=ctrs)
    assert decision.recommendation_state == RecommendationState.RECOMMENDED_WITH_CONDITIONS
    assert decision.recommended_vendor == "Vendor A"
    assert decision.has_core_commercial_contradiction is False


def test_context_dependent_and_dismissed_contradiction_no_downgrade():
    """Verify CONTEXT_DEPENDENT and DISMISSED contradictions cause 0 recommendation state downgrade."""
    rec_service = RecommendationService()
    scoring = build_mock_scoring(v1_score=90.0, v2_score=75.0)
    reqs = ProcurementRequirements()
    cit = EvidenceCitationModel(evidence_id="E1", vendor_name="Vendor A", source_filename="a.pdf", start_page=1, end_page=1, chunk_id="c1", excerpt_text="Text")

    ctrs = [
        ContradictionFindingModel(
            contradiction_id="ctr_ctx",
            vendor_name="Vendor A",
            category="Pricing",
            severity=RiskSeverity.LOW,
            statement_a="Enterprise plan $100",
            statement_b="Standard plan $50",
            evidence_a=[cit],
            evidence_b=[cit],
            reason="Different tier context",
            status=ContradictionStatus.CONTEXT_DEPENDENT,
        ),
        ContradictionFindingModel(
            contradiction_id="ctr_dsm",
            vendor_name="Vendor A",
            category="SLA",
            severity=RiskSeverity.LOW,
            statement_a="Draft 99%",
            statement_b="Final 99.9%",
            evidence_a=[cit],
            evidence_b=[cit],
            reason="Superceded draft",
            status=ContradictionStatus.DISMISSED,
        ),
    ]

    decision = rec_service.evaluate_recommendation_policy(scoring_response=scoring, requirements=reqs, contradictions=ctrs)
    assert decision.recommendation_state == RecommendationState.RECOMMENDED
    assert decision.recommended_vendor == "Vendor A"
    assert decision.has_core_commercial_contradiction is False


# --- Determinism Test (Phase 8 Policy Hardening Section 5) ---

def test_repeated_runs_policy_determinism():
    """Verify repeated execution of policy with identical state produces 100% identical outputs."""
    rec_service = RecommendationService()
    scoring = build_mock_scoring(v1_score=86.0, v2_score=85.0)  # Close leader gap 1.0 pt
    reqs = ProcurementRequirements()

    results = []
    for _ in range(10):
        decision = rec_service.evaluate_recommendation_policy(scoring_response=scoring, requirements=reqs)
        results.append(decision)

    first = results[0]
    for d in results[1:]:
        assert d.recommended_vendor == first.recommended_vendor
        assert d.recommendation_state == first.recommendation_state
        assert d.score_gap == first.score_gap
        assert d.is_close_leader == first.is_close_leader
        assert d.is_clear_leader == first.is_clear_leader
        assert d.has_core_commercial_contradiction == first.has_core_commercial_contradiction
        assert d.alignment_score == first.alignment_score
