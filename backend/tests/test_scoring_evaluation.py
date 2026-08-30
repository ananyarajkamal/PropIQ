"""Evaluation test suite for PropIQ Phase 7 Deterministic Scoring & Transparent Ranking.

Evaluates Controlled 4-Vendor Dataset (Rule 70), 8-Requirement Priority Array (Rule 71),
Non-Trivial Manual Score Calculation Verification (Hardening Fix 2), Property Tests (Rule 74),
Determinism (100 runs) (Rule 79), and Monotonicity Tests (Rule 75-78).
"""

from decimal import Decimal, ROUND_HALF_UP
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


def test_non_trivial_manual_score_calculation_verification():
    """Verify non-trivial vendor score against an independently calculated math benchmark (Hardening Fix 2)."""
    ss = ScoringService()

    # 5 Active Requirements across different priorities
    reqs = ProcurementRequirements(
        minimum_sla=99.9, sla_priority=RequirementPriority.MUST_HAVE,                # Weight 5.0
        budget_ceiling=200000, budget_priority=RequirementPriority.HIGH,              # Weight 4.0
        timeline_value=30, timeline_priority=RequirementPriority.HIGH,                # Weight 4.0
        warranty_value=12, warranty_priority=RequirementPriority.MEDIUM,              # Weight 3.0
        support_requirement="24/7", support_priority=RequirementPriority.LOW,          # Weight 1.0
    )

    cit = EvidenceCitationModel(evidence_id="E1", vendor_name="Vendor Hardened", source_filename="h.pdf", start_page=1, end_page=1, chunk_id="c1", excerpt_text="Text")

    matrix_rows = [
        ComparisonMatrixRow(category="SLA", requirement_label="SLA (99.9%)", vendor_evaluations={
            "Vendor Hardened": RequirementEvaluationResult(requirement_id="REQ_SLA", category="SLA", vendor_name="Vendor Hardened", status="MEETS", raw_vendor_value="99.9%", explanation="Meets", comparison_rule="sla>=99.9")
        }),
        ComparisonMatrixRow(category="Budget", requirement_label="Budget ($200k)", vendor_evaluations={
            "Vendor Hardened": RequirementEvaluationResult(requirement_id="REQ_PRICING", category="Budget", vendor_name="Vendor Hardened", status="PARTIAL", raw_vendor_value="$220k", explanation="Partial", comparison_rule="p<=200k")
        }),
        ComparisonMatrixRow(category="Timeline", requirement_label="Timeline (30d)", vendor_evaluations={
            "Vendor Hardened": RequirementEvaluationResult(requirement_id="REQ_TIMELINE", category="Timeline", vendor_name="Vendor Hardened", status="FAILS", raw_vendor_value="60d", explanation="Fails", comparison_rule="t<=30")
        }),
        ComparisonMatrixRow(category="Warranty", requirement_label="Warranty (12m)", vendor_evaluations={
            "Vendor Hardened": RequirementEvaluationResult(requirement_id="REQ_WARRANTY", category="Warranty", vendor_name="Vendor Hardened", status="MISSING", raw_vendor_value=None, explanation="Missing", comparison_rule="w>=12")
        }),
        ComparisonMatrixRow(category="Support", requirement_label="Support (24/7)", vendor_evaluations={
            "Vendor Hardened": RequirementEvaluationResult(requirement_id="REQ_SUPPORT", category="Support", vendor_name="Vendor Hardened", status="MEETS", raw_vendor_value="24/7", explanation="Meets", comparison_rule="sup==24/7")
        }),
    ]

    # Deductions
    risks = [
        # Risk 1: Linked to failed REQ_TIMELINE (Raw 3.0 pts * 0.5 reduction = 1.5 pts)
        RiskFindingModel(risk_id="r1", vendor_name="Vendor Hardened", category=RiskCategory.NOTICE_PERIOD, severity=RiskSeverity.HIGH, title="Timeline Risk", summary="Delay", procurement_impact="Imp", review_reason="Reas", evidence_citations=[cit], related_requirement_ids=["REQ_TIMELINE"]),
        # Risk 2: Unlinked CRITICAL risk (6.0 pts)
        RiskFindingModel(risk_id="r2", vendor_name="Vendor Hardened", category=RiskCategory.UNCAPPED_LIABILITY, severity=RiskSeverity.CRITICAL, title="Uncapped Liability", summary="Uncapped", procurement_impact="Imp", review_reason="Reas", evidence_citations=[cit]),
    ]

    contradictions = [
        # Contradiction 1: Potential contradiction (1.0 pt)
        ContradictionFindingModel(contradiction_id="c1", vendor_name="Vendor Hardened", category="Terms", severity=RiskSeverity.MEDIUM, statement_a="A", statement_b="B", evidence_a=[cit], evidence_b=[cit], reason="Conflict", status=ContradictionStatus.POTENTIAL_CONTRADICTION)
    ]

    clarifications = [
        # Clarification 1: Linked to missing REQ_WARRANTY (Raw MEDIUM 0.75 pts * 0.5 reduction = 0.375 pts)
        ClarificationQuestionModel(clarification_id="q1", vendor_name="Vendor Hardened", reason=ClarificationReason.SUPPORT_CLARIFICATION, priority=QuestionPriority.MEDIUM, question="Warranty confirm?", requirement_id="REQ_WARRANTY", evidence_citations=[cit])
    ]

    # --- INDEPENDENT MANUAL CALCULATION BENCHMARK ---
    # 1. Base Weighted Score:
    # REQ_SLA: MEETS (1.00) * 5.0 = 5.0
    # REQ_PRICING: PARTIAL (0.60) * 4.0 = 2.4
    # REQ_TIMELINE: FAILS (0.00) * 4.0 = 0.0
    # REQ_WARRANTY: MISSING (0.00) * 3.0 = 0.0
    # REQ_SUPPORT: MEETS (1.00) * 1.0 = 1.0
    manual_weighted_numerator = 5.0 + 2.4 + 0.0 + 0.0 + 1.0  # 8.4
    manual_total_weight = 5.0 + 4.0 + 4.0 + 3.0 + 1.0         # 17.0
    manual_base_alignment = (manual_weighted_numerator / manual_total_weight) * 100.0  # 49.4117647...%

    # 2. Risk Penalties:
    # r1: 3.0 * 0.5 = 1.5
    # r2: 6.0
    manual_risk_penalty = 1.5 + 6.0  # 7.5

    # 3. Contradiction Penalty:
    manual_ctr_penalty = 1.0

    # 4. Clarification Penalty:
    manual_clrf_penalty = 0.75 * 0.5  # 0.375

    # 5. Final Math:
    manual_raw_final = manual_base_alignment - (manual_risk_penalty + manual_ctr_penalty + manual_clrf_penalty)
    # 49.4117647 - 8.875 = 40.5367647...
    manual_clamped_final = max(0.0, min(100.0, manual_raw_final))
    manual_expected_score = float(Decimal(str(manual_clamped_final)).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))
    # 40.5

    # Run Scoring Service
    res = ss.evaluate_session_scoring(
        "sess_manual_eval",
        requirements=reqs,
        matrix_rows=matrix_rows,
        risk_findings=risks,
        contradictions=contradictions,
        clarifications=clarifications,
    )

    actual_score = res.vendor_scores[0].alignment_score

    print("\n--- NON-TRIVIAL MANUAL SCORE VERIFICATION BENCHMARK ---")
    print(f"Manual Weighted Numerator: {manual_weighted_numerator}")
    print(f"Manual Total Weight: {manual_total_weight}")
    print(f"Manual Base Alignment Score: {manual_base_alignment:.2f}%")
    print(f"Manual Risk Penalty: -{manual_risk_penalty:.2f} pts")
    print(f"Manual Contradiction Penalty: -{manual_ctr_penalty:.2f} pts")
    print(f"Manual Clarification Penalty: -{manual_clrf_penalty:.3f} pts")
    print(f"Manual Unclamped Score: {manual_raw_final:.4f}")
    print(f"Manual Expected Rounded Score: {manual_expected_score}")
    print(f"Actual ScoringService Output: {actual_score}")

    assert abs(actual_score - manual_expected_score) == 0.0


def test_controlled_4_vendor_scoring_and_ranking_dataset():
    """Evaluate Controlled 4-Vendor Dataset across 8 Procurement Requirements (Rules 70, 71, 72, 73)."""
    ss = ScoringService()

    reqs = ProcurementRequirements(
        budget_ceiling=200000, budget_priority=RequirementPriority.HIGH,            # Weight 4.0
        timeline_value=30, timeline_priority=RequirementPriority.HIGH,               # Weight 4.0
        minimum_sla=99.9, sla_priority=RequirementPriority.MUST_HAVE,                 # Weight 5.0
        payment_terms="Net 30", payment_priority=RequirementPriority.MEDIUM,        # Weight 3.0
        certifications=["SOC 2 Type II"], certifications_priority=RequirementPriority.MUST_HAVE,  # Weight 5.0
        warranty_value=12, warranty_priority=RequirementPriority.MEDIUM,             # Weight 3.0
        renewal_preference="No auto renewal", renewal_priority=RequirementPriority.HIGH,  # Weight 4.0
        support_requirement="24/7", support_priority=RequirementPriority.MEDIUM,       # Weight 3.0
    )

    cit = EvidenceCitationModel(evidence_id="E1", vendor_name="Vendor", source_filename="f.pdf", start_page=1, end_page=1, chunk_id="c1", excerpt_text="Evidence text.")

    matrix_rows = [
        ComparisonMatrixRow(category="Budget", requirement_label="Budget Ceiling ($200k)", vendor_evaluations={
            "Vendor A": RequirementEvaluationResult(requirement_id="REQ_PRICING", category="Budget", vendor_name="Vendor A", status="MEETS", raw_vendor_value="$150k", explanation="Meets", comparison_rule="p<=200k"),
            "Vendor B": RequirementEvaluationResult(requirement_id="REQ_PRICING", category="Budget", vendor_name="Vendor B", status="MEETS", raw_vendor_value="$120k", explanation="Meets", comparison_rule="p<=200k"),
            "Vendor C": RequirementEvaluationResult(requirement_id="REQ_PRICING", category="Budget", vendor_name="Vendor C", status="UNCLEAR", raw_vendor_value="Range", explanation="Unclear", comparison_rule="p<=200k"),
            "Vendor D": RequirementEvaluationResult(requirement_id="REQ_PRICING", category="Budget", vendor_name="Vendor D", status="MEETS", raw_vendor_value="$180k", explanation="Meets", comparison_rule="p<=200k"),
        }),
        ComparisonMatrixRow(category="Timeline", requirement_label="Deployment Timeline (30 days)", vendor_evaluations={
            "Vendor A": RequirementEvaluationResult(requirement_id="REQ_TIMELINE", category="Timeline", vendor_name="Vendor A", status="MEETS", raw_vendor_value="30 days", explanation="Meets", comparison_rule="t<=30"),
            "Vendor B": RequirementEvaluationResult(requirement_id="REQ_TIMELINE", category="Timeline", vendor_name="Vendor B", status="MEETS", raw_vendor_value="25 days", explanation="Meets", comparison_rule="t<=30"),
            "Vendor C": RequirementEvaluationResult(requirement_id="REQ_TIMELINE", category="Timeline", vendor_name="Vendor C", status="MISSING", raw_vendor_value=None, explanation="Missing", comparison_rule="t<=30"),
            "Vendor D": RequirementEvaluationResult(requirement_id="REQ_TIMELINE", category="Timeline", vendor_name="Vendor D", status="MEETS", raw_vendor_value="30 days", explanation="Meets", comparison_rule="t<=30"),
        }),
        ComparisonMatrixRow(category="SLA", requirement_label="Minimum SLA Uptime (99.9%)", vendor_evaluations={
            "Vendor A": RequirementEvaluationResult(requirement_id="REQ_SLA", category="SLA", vendor_name="Vendor A", status="MEETS", raw_vendor_value="99.9%", explanation="Meets", comparison_rule="sla>=99.9"),
            "Vendor B": RequirementEvaluationResult(requirement_id="REQ_SLA", category="SLA", vendor_name="Vendor B", status="FAILS", raw_vendor_value="99.0%", explanation="Fails SLA", comparison_rule="sla>=99.9"),
            "Vendor C": RequirementEvaluationResult(requirement_id="REQ_SLA", category="SLA", vendor_name="Vendor C", status="PARTIAL", raw_vendor_value="99.5%", explanation="Partial", comparison_rule="sla>=99.9"),
            "Vendor D": RequirementEvaluationResult(requirement_id="REQ_SLA", category="SLA", vendor_name="Vendor D", status="MEETS", raw_vendor_value="99.9%", explanation="Meets", comparison_rule="sla>=99.9"),
        }),
        ComparisonMatrixRow(category="Payment", requirement_label="Payment Terms (Net 30)", vendor_evaluations={
            "Vendor A": RequirementEvaluationResult(requirement_id="REQ_PAYMENT", category="Payment", vendor_name="Vendor A", status="MEETS", raw_vendor_value="Net 30", explanation="Meets", comparison_rule="p==Net 30"),
            "Vendor B": RequirementEvaluationResult(requirement_id="REQ_PAYMENT", category="Payment", vendor_name="Vendor B", status="MEETS", raw_vendor_value="Net 30", explanation="Meets", comparison_rule="p==Net 30"),
            "Vendor C": RequirementEvaluationResult(requirement_id="REQ_PAYMENT", category="Payment", vendor_name="Vendor C", status="UNCLEAR", raw_vendor_value="To be agreed", explanation="Unclear", comparison_rule="p==Net 30"),
            "Vendor D": RequirementEvaluationResult(requirement_id="REQ_PAYMENT", category="Payment", vendor_name="Vendor D", status="MEETS", raw_vendor_value="Net 30", explanation="Meets", comparison_rule="p==Net 30"),
        }),
        ComparisonMatrixRow(category="Certifications", requirement_label="Required Certifications (SOC 2 Type II)", vendor_evaluations={
            "Vendor A": RequirementEvaluationResult(requirement_id="REQ_CERTIFICATIONS", category="Certifications", vendor_name="Vendor A", status="MEETS", raw_vendor_value="SOC 2 Type II", explanation="Meets", comparison_rule="cert in certs"),
            "Vendor B": RequirementEvaluationResult(requirement_id="REQ_CERTIFICATIONS", category="Certifications", vendor_name="Vendor B", status="MEETS", raw_vendor_value="SOC 2 Type II", explanation="Meets", comparison_rule="cert in certs"),
            "Vendor C": RequirementEvaluationResult(requirement_id="REQ_CERTIFICATIONS", category="Certifications", vendor_name="Vendor C", status="MISSING", raw_vendor_value=None, explanation="Missing", comparison_rule="cert in certs"),
            "Vendor D": RequirementEvaluationResult(requirement_id="REQ_CERTIFICATIONS", category="Certifications", vendor_name="Vendor D", status="MEETS", raw_vendor_value="SOC 2 Type II", explanation="Meets", comparison_rule="cert in certs"),
        }),
        ComparisonMatrixRow(category="Warranty", requirement_label="Minimum Warranty (12 months)", vendor_evaluations={
            "Vendor A": RequirementEvaluationResult(requirement_id="REQ_WARRANTY", category="Warranty", vendor_name="Vendor A", status="MEETS", raw_vendor_value="12 months", explanation="Meets", comparison_rule="w>=12"),
            "Vendor B": RequirementEvaluationResult(requirement_id="REQ_WARRANTY", category="Warranty", vendor_name="Vendor B", status="MEETS", raw_vendor_value="12 months", explanation="Meets", comparison_rule="w>=12"),
            "Vendor C": RequirementEvaluationResult(requirement_id="REQ_WARRANTY", category="Warranty", vendor_name="Vendor C", status="PARTIAL", raw_vendor_value="6 months", explanation="Partial", comparison_rule="w>=12"),
            "Vendor D": RequirementEvaluationResult(requirement_id="REQ_WARRANTY", category="Warranty", vendor_name="Vendor D", status="MEETS", raw_vendor_value="12 months", explanation="Meets", comparison_rule="w>=12"),
        }),
        ComparisonMatrixRow(category="Renewal", requirement_label="Renewal Terms", vendor_evaluations={
            "Vendor A": RequirementEvaluationResult(requirement_id="REQ_RENEWAL", category="Renewal", vendor_name="Vendor A", status="MEETS", raw_vendor_value="No auto renewal", explanation="Meets", comparison_rule="no auto renewal"),
            "Vendor B": RequirementEvaluationResult(requirement_id="REQ_RENEWAL", category="Renewal", vendor_name="Vendor B", status="MEETS", raw_vendor_value="No auto renewal", explanation="Meets", comparison_rule="no auto renewal"),
            "Vendor C": RequirementEvaluationResult(requirement_id="REQ_RENEWAL", category="Renewal", vendor_name="Vendor C", status="FAILS", raw_vendor_value="Auto renews", explanation="Fails", comparison_rule="no auto renewal"),
            "Vendor D": RequirementEvaluationResult(requirement_id="REQ_RENEWAL", category="Renewal", vendor_name="Vendor D", status="FAILS", raw_vendor_value="Auto renews", explanation="Fails", comparison_rule="no auto renewal"),
        }),
        ComparisonMatrixRow(category="Support", requirement_label="Support Availability (24/7)", vendor_evaluations={
            "Vendor A": RequirementEvaluationResult(requirement_id="REQ_SUPPORT", category="Support", vendor_name="Vendor A", status="MEETS", raw_vendor_value="24/7 Support", explanation="Meets", comparison_rule="sup==24/7"),
            "Vendor B": RequirementEvaluationResult(requirement_id="REQ_SUPPORT", category="Support", vendor_name="Vendor B", status="MEETS", raw_vendor_value="24/7 Support", explanation="Meets", comparison_rule="sup==24/7"),
            "Vendor C": RequirementEvaluationResult(requirement_id="REQ_SUPPORT", category="Support", vendor_name="Vendor C", status="UNCLEAR", raw_vendor_value="Business hours", explanation="Unclear", comparison_rule="sup==24/7"),
            "Vendor D": RequirementEvaluationResult(requirement_id="REQ_SUPPORT", category="Support", vendor_name="Vendor D", status="MEETS", raw_vendor_value="24/7 Support", explanation="Meets", comparison_rule="sup==24/7"),
        }),
    ]

    risks_d = [
        RiskFindingModel(risk_id="r1", vendor_name="Vendor D", category=RiskCategory.UNCAPPED_LIABILITY, severity=RiskSeverity.CRITICAL, title="Uncapped Liability", summary="Uncapped", procurement_impact="High", review_reason="Reason", evidence_citations=[cit]),
        RiskFindingModel(risk_id="r2", vendor_name="Vendor D", category=RiskCategory.UNILATERAL_CHANGE_RIGHTS, severity=RiskSeverity.CRITICAL, title="Unilateral Changes", summary="Unilateral", procurement_impact="High", review_reason="Reason", evidence_citations=[cit]),
    ]

    res = ss.evaluate_session_scoring("sess_eval_4v", requirements=reqs, matrix_rows=matrix_rows, risk_findings=risks_d)
    v_scores = res.vendor_scores

    assert len(v_scores) == 4

    va = next(v for v in v_scores if v.vendor_name == "Vendor A")
    assert va.alignment_score == 100.0
    assert va.rank == 1

    vb = next(v for v in v_scores if v.vendor_name == "Vendor B")
    assert vb.must_have_failures_count == 1
    assert vb.alignment_score == 83.9

    vd = next(v for v in v_scores if v.vendor_name == "Vendor D")
    assert vd.total_risk_penalty == 12.0
    assert vd.alignment_score == 75.1


def test_scoring_property_range_determinism_and_monotonicity():
    """Verify Property Range [0, 100] (Rule 74), Determinism (100 runs) (Rule 79), and Monotonicity (Rule 75-78)."""
    ss = ScoringService()
    reqs = ProcurementRequirements(warranty_value=12, warranty_unit="months")

    matrix_rows = [
        ComparisonMatrixRow(
            category="Warranty",
            requirement_label="Minimum Warranty (12 months)",
            vendor_evaluations={
                "Vendor A": RequirementEvaluationResult(requirement_id="REQ_WARRANTY", category="Warranty", vendor_name="Vendor A", status="MEETS", raw_vendor_value="12m", explanation="Meets", comparison_rule="w>=12")
            },
        )
    ]

    scores_set = set()
    for _ in range(100):
        res = ss.evaluate_session_scoring("sess_det", requirements=reqs, matrix_rows=matrix_rows)
        scores_set.add(res.vendor_scores[0].alignment_score)
    assert len(scores_set) == 1

    res = ss.evaluate_session_scoring("sess_det", requirements=reqs, matrix_rows=matrix_rows)
    assert 0.0 <= res.vendor_scores[0].alignment_score <= 100.0

    score_before = res.vendor_scores[0].alignment_score
    cit = EvidenceCitationModel(evidence_id="E1", vendor_name="Vendor A", source_filename="f.pdf", start_page=1, end_page=1, chunk_id="c1", excerpt_text="Text")
    risks = [RiskFindingModel(risk_id="r1", vendor_name="Vendor A", category=RiskCategory.AUTO_RENEWAL, severity=RiskSeverity.HIGH, title="Auto Renewal", summary="Sum", procurement_impact="Imp", review_reason="Reas", evidence_citations=[cit])]

    res_after = ss.evaluate_session_scoring("sess_det", requirements=reqs, matrix_rows=matrix_rows, risk_findings=risks)
    score_after = res_after.vendor_scores[0].alignment_score

    assert score_after <= score_before
