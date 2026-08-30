"""Unit tests for GapService module."""

import pytest
from app.models import (
    ClarificationReason,
    QuestionPriority,
    ProcurementRequirements,
    ComparisonMatrixRow,
    RequirementEvaluationResult,
    VendorFactSheet,
    CategoryExtractionResult,
    EvidenceCitationModel,
    ContradictionFindingModel,
    ContradictionStatus,
    RiskSeverity,
)
from app.services.gap_service import GapService


def test_gap_service_missing_requirement():
    """Verify missing requirement generates a MISSING_REQUIREMENT gap."""
    gs = GapService()
    reqs = ProcurementRequirements(warranty_value=12, warranty_unit="months")

    matrix_rows = [
        ComparisonMatrixRow(
            category="Warranty",
            requirement_label="Minimum Warranty (12 months)",
            vendor_evaluations={
                "Vendor Alpha": RequirementEvaluationResult(
                    requirement_id="REQ_WARRANTY",
                    category="Warranty",
                    vendor_name="Vendor Alpha",
                    status="MISSING",
                    explanation="No warranty duration found in proposal.",
                    comparison_rule="vendor_warranty >= 12 months",
                )
            },
        )
    ]

    gaps = gs.detect_session_gaps("sess_gap_1", matrix_rows=matrix_rows, requirements=reqs)

    assert len(gaps) == 1
    g = gaps[0]
    assert g.vendor_name == "Vendor Alpha"
    assert g.reason == ClarificationReason.MISSING_REQUIREMENT
    assert g.requirement_id == "REQ_WARRANTY"
    assert g.source_status == "MISSING"


def test_gap_service_meets_compliant_fact_zero_questions():
    """Verify fully compliant MEETS requirement status produces 0 questions."""
    gs = GapService()

    matrix_rows = [
        ComparisonMatrixRow(
            category="Warranty",
            requirement_label="Minimum Warranty (12 months)",
            vendor_evaluations={
                "Vendor Alpha": RequirementEvaluationResult(
                    requirement_id="REQ_WARRANTY",
                    category="Warranty",
                    vendor_name="Vendor Alpha",
                    status="MEETS",
                    explanation="Vendor warranty is 24 months (Meets requirement).",
                    comparison_rule="vendor_warranty >= 12 months",
                )
            },
        )
    ]

    gaps = gs.detect_session_gaps("sess_gap_2", matrix_rows=matrix_rows)
    assert len(gaps) == 0  # 0 questions for resolved compliant facts!


def test_gap_service_conflicting_information():
    """Verify Phase 5 contradiction generates a CONFLICTING_INFORMATION gap."""
    gs = GapService()

    c1 = EvidenceCitationModel(evidence_id="E1", vendor_name="Vendor Beta", source_filename="b.pdf", start_page=3, end_page=3, chunk_id="c1", excerpt_text="30 days timeline.")
    c2 = EvidenceCitationModel(evidence_id="E2", vendor_name="Vendor Beta", source_filename="b.pdf", start_page=9, end_page=9, chunk_id="c2", excerpt_text="45 days timeline.")

    ctrs = [
        ContradictionFindingModel(
            contradiction_id="ctr_beta_1",
            vendor_name="Vendor Beta",
            category="Timeline",
            severity=RiskSeverity.HIGH,
            statement_a="30 days timeline",
            statement_b="45 days timeline",
            context_a="Page 3",
            context_b="Page 9",
            evidence_a=[c1],
            evidence_b=[c2],
            reason="Conflicting implementation schedules.",
            status=ContradictionStatus.CONFIRMED_CONTRADICTION,
        )
    ]

    gaps = gs.detect_session_gaps("sess_gap_3", contradictions=ctrs)

    assert len(gaps) == 1
    g = gaps[0]
    assert g.vendor_name == "Vendor Beta"
    assert g.reason == ClarificationReason.CONFLICTING_INFORMATION
    assert g.priority == QuestionPriority.HIGH
    assert len(g.evidence_citations) == 2


def test_gap_service_pricing_ambiguity_range():
    """Verify price range generates a PRICING_AMBIGUITY gap."""
    gs = GapService()

    cit = EvidenceCitationModel(evidence_id="E1", vendor_name="Vendor Gamma", source_filename="g.pdf", start_page=1, end_page=1, chunk_id="c1", excerpt_text="Pricing ranges from $180,000 to $220,000 annually.")
    fact_sheets = [
        VendorFactSheet(
            vendor_name="Vendor Gamma",
            categories=[
                CategoryExtractionResult(
                    category="Pricing",
                    status="FOUND",
                    raw_value="$180,000 to $220,000",
                    summary="Price range from $180,000 to $220,000",
                    evidence_citations=[cit],
                )
            ],
        )
    ]

    gaps = gs.detect_session_gaps("sess_gap_4", fact_sheets=fact_sheets)

    assert len(gaps) >= 1
    p_gaps = [g for g in gaps if g.reason == ClarificationReason.PRICING_AMBIGUITY]
    assert len(p_gaps) == 1
    assert p_gaps[0].priority == QuestionPriority.HIGH
