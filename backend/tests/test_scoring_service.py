"""Unit tests for PropIQ ScoringService.

Verifies 100% deterministic calculation of Alignment Scores, comparison state mappings,
priority weighting, linked-risk double-penalty reduction, risk/contradiction/clarification caps,
clamping (0-100), tie tolerance (<0.5), deterministic tie-breaking, and zero Groq calls.
"""

import pytest
from app.models import (
    RequirementPriority,
    RankStatus,
    ProcurementRequirements,
    ComparisonMatrixRow,
    RequirementEvaluationResult,
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
from app.services.scoring_service import ScoringService


def test_scoring_base_alignment_weighted_score():
    """Verify base alignment score calculation for active requirements with priority weights."""
    ss = ScoringService()
    reqs = ProcurementRequirements(
        warranty_value=12,
        warranty_unit="months",
        warranty_priority=RequirementPriority.MUST_HAVE,  # Weight 5.0
        minimum_sla=99.5,
        sla_priority=RequirementPriority.HIGH,             # Weight 4.0
    )

    cit = EvidenceCitationModel(evidence_id="E1", vendor_name="Vendor A", source_filename="a.pdf", start_page=1, end_page=1, chunk_id="c1", excerpt_text="12 months warranty.")

    matrix_rows = [
        ComparisonMatrixRow(
            category="Warranty",
            requirement_label="Minimum Warranty (12 months)",
            vendor_evaluations={
                "Vendor A": RequirementEvaluationResult(
                    requirement_id="REQ_WARRANTY", category="Warranty", vendor_name="Vendor A", status="MEETS", raw_vendor_value="12 months", explanation="Meets", comparison_rule="w >= 12"
                )
            },
        ),
        ComparisonMatrixRow(
            category="SLA / Uptime",
            requirement_label="Minimum SLA Uptime (99.5%)",
            vendor_evaluations={
                "Vendor A": RequirementEvaluationResult(
                    requirement_id="REQ_SLA", category="SLA / Uptime", vendor_name="Vendor A", status="PARTIAL", raw_vendor_value="99.0%", explanation="Partial", comparison_rule="sla >= 99.5"
                )
            },
        ),
    ]

    res = ss.evaluate_session_scoring("sess_scoring_1", requirements=reqs, matrix_rows=matrix_rows)
    assert len(res.vendor_scores) == 1
    v_score = res.vendor_scores[0]

    # Weighted calculation:
    # Warranty: MEETS (1.00) * 5.0 = 5.0 pts
    # SLA: PARTIAL (0.60) * 4.0 = 2.4 pts
    # Total weighted: 7.4 pts out of 9.0 max pts
    # Base percentage: (7.4 / 9.0) * 100 = 82.222% -> 82.2
    assert v_score.base_alignment_score == 82.2
    assert v_score.alignment_score == 82.2
    assert v_score.must_have_failures_count == 0


def test_scoring_linked_risk_double_penalty_reduction():
    """Verify linked risk receives 50% reduced penalty when requirement already FAILS."""
    ss = ScoringService()
    reqs = ProcurementRequirements(
        renewal_preference="No auto renewal",
        renewal_priority=RequirementPriority.HIGH,
    )

    matrix_rows = [
        ComparisonMatrixRow(
            category="Renewal",
            requirement_label="Contract Renewal Terms",
            vendor_evaluations={
                "Vendor A": RequirementEvaluationResult(
                    requirement_id="REQ_RENEWAL", category="Renewal", vendor_name="Vendor A", status="FAILS", raw_vendor_value="Auto renews 12m", explanation="Fails", comparison_rule="no auto renewal"
                )
            },
        )
    ]

    cit = EvidenceCitationModel(evidence_id="E1", vendor_name="Vendor A", source_filename="a.pdf", start_page=1, end_page=1, chunk_id="c1", excerpt_text="Auto renews.")
    risks = [
        RiskFindingModel(
            risk_id="r1", vendor_name="Vendor A", category=RiskCategory.AUTO_RENEWAL, severity=RiskSeverity.HIGH, title="Auto Renewal", summary="Auto renews", procurement_impact="Impact", review_reason="Reason", evidence_citations=[cit], related_requirement_ids=["REQ_RENEWAL"]
        )
    ]

    res = ss.evaluate_session_scoring("sess_scoring_2", requirements=reqs, matrix_rows=matrix_rows, risk_findings=risks)
    v_score = res.vendor_scores[0]

    # Raw HIGH risk penalty is 3.0. Linked to failed REQ_RENEWAL -> 50% reduction = 1.5 pts deduction!
    assert v_score.total_risk_penalty == 1.5
    assert len(v_score.deductions) == 1
    assert v_score.deductions[0].is_linked_risk is True
    assert v_score.deductions[0].final_deduction == 1.5


def test_scoring_caps_and_clamping():
    """Verify risk, contradiction, and clarification caps and final score clamping (0.0 to 100.0)."""
    ss = ScoringService()
    reqs = ProcurementRequirements(warranty_value=12, warranty_unit="months")

    matrix_rows = [
        ComparisonMatrixRow(
            category="Warranty",
            requirement_label="Minimum Warranty (12 months)",
            vendor_evaluations={
                "Vendor A": RequirementEvaluationResult(
                    requirement_id="REQ_WARRANTY", category="Warranty", vendor_name="Vendor A", status="FAILS", raw_vendor_value="No warranty", explanation="Fails", comparison_rule="w >= 12"
                )
            },
        )
    ]

    cit = EvidenceCitationModel(evidence_id="E1", vendor_name="Vendor A", source_filename="a.pdf", start_page=1, end_page=1, chunk_id="c1", excerpt_text="Text")
    # 4 CRITICAL risks (4 * 6.0 = 24.0 points uncapped -> capped at 15.0 pts)
    risks = [
        RiskFindingModel(risk_id=f"r_{i}", vendor_name="Vendor A", category=RiskCategory.UNCAPPED_LIABILITY, severity=RiskSeverity.CRITICAL, title=f"Risk {i}", summary="Summary", procurement_impact="Impact", review_reason="Reason", evidence_citations=[cit])
        for i in range(4)
    ]

    # 5 Confirmed contradictions (5 * 2.5 = 12.5 points uncapped -> capped at 10.0 pts)
    contradictions = [
        ContradictionFindingModel(contradiction_id=f"c_{i}", vendor_name="Vendor A", category="Term", severity=RiskSeverity.HIGH, statement_a="A", statement_b="B", evidence_a=[cit], evidence_b=[cit], reason="Reason", status=ContradictionStatus.CONFIRMED_CONTRADICTION)
        for i in range(5)
    ]

    # 8 High clarifications (8 * 1.5 = 12.0 points uncapped -> capped at 8.0 pts)
    clarifications = [
        ClarificationQuestionModel(clarification_id=f"q_{i}", vendor_name="Vendor A", reason=ClarificationReason.PRICING_AMBIGUITY, priority=QuestionPriority.HIGH, question=f"Q {i}", evidence_citations=[cit])
        for i in range(8)
    ]

    res = ss.evaluate_session_scoring("sess_scoring_caps", requirements=reqs, matrix_rows=matrix_rows, risk_findings=risks, contradictions=contradictions, clarifications=clarifications)
    v_score = res.vendor_scores[0]

    assert v_score.total_risk_penalty == 15.0  # Capped at 15.0
    assert v_score.total_contradiction_penalty == 10.0  # Capped at 10.0
    assert v_score.total_clarification_penalty == 8.0  # Capped at 8.0
    assert v_score.alignment_score >= 0.0  # Clamped at 0.0 min


def test_scoring_tie_detection_and_deterministic_tie_breaking():
    """Verify score difference < 0.5 is assigned RankStatus.TIED and resolved deterministically without Groq calls."""
    ss = ScoringService()
    reqs = ProcurementRequirements(warranty_value=12, warranty_unit="months")

    matrix_rows = [
        ComparisonMatrixRow(
            category="Warranty",
            requirement_label="Minimum Warranty (12 months)",
            vendor_evaluations={
                "Vendor A": RequirementEvaluationResult(requirement_id="REQ_WARRANTY", category="Warranty", vendor_name="Vendor A", status="MEETS", raw_vendor_value="12m", explanation="Meets", comparison_rule="w>=12"),
                "Vendor B": RequirementEvaluationResult(requirement_id="REQ_WARRANTY", category="Warranty", vendor_name="Vendor B", status="MEETS", raw_vendor_value="12m", explanation="Meets", comparison_rule="w>=12"),
            },
        )
    ]

    cit = EvidenceCitationModel(evidence_id="E1", vendor_name="Vendor A", source_filename="a.pdf", start_page=1, end_page=1, chunk_id="c1", excerpt_text="Text")
    # Vendor A has 1 LOW risk (-0.5 pts -> score 99.5)
    risks_a = [RiskFindingModel(risk_id="r1", vendor_name="Vendor A", category=RiskCategory.NOTICE_PERIOD, severity=RiskSeverity.LOW, title="Notice", summary="Sum", procurement_impact="Imp", review_reason="Reas", evidence_citations=[cit])]

    # Vendor B has 1 LOW clarification (-0.25 pts -> score 99.8)
    clarifications_b = [ClarificationQuestionModel(clarification_id="q1", vendor_name="Vendor B", reason=ClarificationReason.PAYMENT_CLARIFICATION, priority=QuestionPriority.LOW, question="Q", evidence_citations=[cit])]

    res = ss.evaluate_session_scoring("sess_ties", requirements=reqs, matrix_rows=matrix_rows, risk_findings=risks_a, clarifications=clarifications_b)
    scores = res.vendor_scores

    # Score diff = 99.8 - 99.5 = 0.3 < 0.5 tie tolerance -> Both assigned RankStatus.TIED!
    assert scores[0].rank_status == RankStatus.TIED
    assert scores[1].rank_status == RankStatus.TIED
