"""Unit tests for ClarificationService module."""

import pytest
from app.models import (
    ClarificationReason,
    QuestionPriority,
    ClarificationGenerationMethod,
    ProcurementRequirements,
    ComparisonMatrixRow,
    RequirementEvaluationResult,
    EvidenceCitationModel,
    ContradictionFindingModel,
    ContradictionStatus,
    RiskSeverity,
)
from app.services.clarification_service import ClarificationService


def test_clarification_service_deterministic_template_warranty():
    """Verify deterministic template question generation for missing warranty."""
    cs = ClarificationService()
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
                    explanation="No warranty duration found.",
                    comparison_rule="vendor_warranty >= 12 months",
                )
            },
        )
    ]

    questions = cs.generate_session_clarifications("sess_clrf_1", matrix_rows=matrix_rows, requirements=reqs)

    assert len(questions) == 1
    q = questions[0]
    assert q.vendor_name == "Vendor Alpha"
    assert q.reason == ClarificationReason.MISSING_REQUIREMENT
    assert q.generation_method == ClarificationGenerationMethod.TEMPLATE
    assert "warranty" in q.question.lower()
    assert "minimum 12" in q.context.lower()


def test_clarification_service_conflicting_timeline_wording():
    """Verify non-accusatory neutral wording for conflicting implementation timelines."""
    cs = ClarificationService()

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

    questions = cs.generate_session_clarifications("sess_clrf_2", contradictions=ctrs)

    assert len(questions) == 1
    q = questions[0]
    assert q.priority == QuestionPriority.HIGH
    assert "contradicts itself" not in q.question.lower()  # Neutral non-accusatory wording!
    assert "30 days and 45 days" in q.question
    assert len(q.evidence_citations) == 2


def test_clarification_service_deduplication():
    """Verify deduplication removes duplicate question intents per vendor."""
    cs = ClarificationService()
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
                    explanation="No warranty duration found.",
                    comparison_rule="vendor_warranty >= 12 months",
                )
            },
        ),
        # Duplicate row with same requirement_id & status
        ComparisonMatrixRow(
            category="Warranty",
            requirement_label="Minimum Warranty (12 months)",
            vendor_evaluations={
                "Vendor Alpha": RequirementEvaluationResult(
                    requirement_id="REQ_WARRANTY",
                    category="Warranty",
                    vendor_name="Vendor Alpha",
                    status="MISSING",
                    explanation="No warranty duration found.",
                    comparison_rule="vendor_warranty >= 12 months",
                )
            },
        ),
    ]

    questions = cs.generate_session_clarifications("sess_clrf_3", matrix_rows=matrix_rows, requirements=reqs)

    assert len(questions) == 1  # Deduplicated!
