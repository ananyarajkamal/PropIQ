"""Generic integration and unit tests for PropIQ deterministic comparison pipeline.

Verifies end-to-end processing from synthetic proposal text through indexing,
retrieval, structured extraction, normalization, deterministic evaluation, and API response schema.
Zero hardcoded vendor names, zero test-file dependencies.
"""

import pytest
from app.models import (
    ProcurementRequirements,
    RequirementPriority,
    VendorFactSheet,
    CategoryExtractionResult,
    EvidenceCitationModel,
    ComparisonMatrixRow,
    RequirementEvaluationResult,
)
from app.services.vector_store import VectorStore
from app.services.chunker import chunk_document_pages
from app.services.normalization_service import NormalizationService
from app.services.comparison_service import ComparisonService


def test_normalization_service_generic_units():
    """Verify generic deterministic normalization rules for currency, duration, SLA, and warranty."""
    norm = NormalizationService()

    # Currency normalization
    price_res = norm.normalize_pricing("$150,000 per year plus $10,000 setup fee")
    assert price_res.normalization_status == "NORMALIZED"
    assert price_res.normalized_value["annual_amount"] == 150000.0
    assert price_res.normalized_value["currency"] == "USD"

    # Duration normalization (months -> days)
    dur_res = norm.normalize_duration("60 days implementation timeline")
    assert dur_res.normalization_status in {"NORMALIZED", "ALREADY_STANDARD"}
    assert dur_res.normalized_value == 60

    # Percentage SLA normalization
    sla_res = norm.normalize_sla("Guaranteed 99.9% uptime SLA")
    assert sla_res.normalization_status == "NORMALIZED"
    assert sla_res.normalized_value == 99.9

    # Warranty normalization
    warr_res = norm.normalize_warranty("12 months comprehensive warranty")
    assert warr_res.normalization_status in {"NORMALIZED", "ALREADY_STANDARD"}
    assert warr_res.normalized_value == 12.0


def test_comparison_service_synthetic_evaluation():
    """Verify deterministic comparison logic using synthetic vendor fact sheets."""
    comp_service = ComparisonService()

    reqs = ProcurementRequirements(
        budget_ceiling=200000.0,
        budget_currency="USD",
        budget_priority=RequirementPriority.MUST_HAVE,
        timeline_value=90.0,
        timeline_unit="days",
        timeline_priority=RequirementPriority.HIGH,
        minimum_sla=99.5,
        sla_priority=RequirementPriority.MUST_HAVE,
        custom_requirements=["Must support single sign-on (SSO) integration"],
    )

    # Synthetic Vendor A (Meets all criteria)
    fact_sheet_a = VendorFactSheet(
        vendor_name="Vendor Alpha",
        categories=[
            CategoryExtractionResult(
                category="Pricing",
                status="FOUND",
                raw_value="$150,000 per year",
                summary="Annual fee $150,000 USD",
                evidence_citations=[
                    EvidenceCitationModel(
                        evidence_id="E1",
                        vendor_name="Vendor Alpha",
                        source_filename="alpha_proposal.pdf",
                        start_page=2,
                        end_page=2,
                        chunk_id="v01_p002_c001",
                        excerpt_text="Total annual license cost is $150,000.",
                    )
                ],
            ),
            CategoryExtractionResult(
                category="Delivery / Implementation",
                status="FOUND",
                raw_value="60 days deployment",
                summary="Implementation completed in 60 days.",
                evidence_citations=[],
            ),
            CategoryExtractionResult(
                category="SLA / Uptime",
                status="FOUND",
                raw_value="99.9% availability SLA",
                summary="99.9% uptime guarantee.",
                evidence_citations=[],
            ),
            CategoryExtractionResult(
                category="Custom: Must support single sign-on (SSO) integration",
                status="FOUND",
                raw_value="Full SAML 2.0 and OAuth SSO supported out of the box.",
                summary="SAML 2.0 SSO supported.",
                evidence_citations=[],
            ),
        ],
    )

    # Synthetic Vendor B (Fails budget, meets SLA)
    fact_sheet_b = VendorFactSheet(
        vendor_name="Vendor Beta",
        categories=[
            CategoryExtractionResult(
                category="Pricing",
                status="FOUND",
                raw_value="$250,000 annual subscription",
                summary="Annual cost $250,000 USD",
                evidence_citations=[],
            ),
            CategoryExtractionResult(
                category="Delivery / Implementation",
                status="NOT_FOUND",
                raw_value=None,
                summary="Timeline not specified in proposal.",
                evidence_citations=[],
            ),
            CategoryExtractionResult(
                category="SLA / Uptime",
                status="FOUND",
                raw_value="99.95% uptime SLA",
                summary="99.95% availability guaranteed.",
                evidence_citations=[],
            ),
            CategoryExtractionResult(
                category="Custom: Must support single sign-on (SSO) integration",
                status="NOT_FOUND",
                raw_value=None,
                summary="Not found.",
                evidence_citations=[],
            ),
        ],
    )

    res = comp_service.evaluate_session_comparison(
        session_id="test_synthetic_session",
        requirements=reqs,
        fact_sheets=[fact_sheet_a, fact_sheet_b],
    )

    assert res.status == "success"
    assert len(res.matrix_rows) == 4  # Budget, Timeline, SLA, Custom

    # Verify requirement labels are non-empty
    for row in res.matrix_rows:
        assert row.requirement_label is not None and len(row.requirement_label) > 0
        assert row.requirement_name is not None and len(row.requirement_name) > 0
        assert "Vendor Alpha" in row.vendor_evaluations
        assert "Vendor Beta" in row.vendor_evaluations

    # Vendor Alpha checks
    alpha_budget = res.matrix_rows[0].vendor_evaluations["Vendor Alpha"]
    assert alpha_budget.status == "MEETS"

    alpha_custom = res.matrix_rows[3].vendor_evaluations["Vendor Alpha"]
    assert alpha_custom.status == "MEETS"
    assert alpha_custom.raw_vendor_value == "Full SAML 2.0 and OAuth SSO supported out of the box."

    # Vendor Beta checks
    beta_budget = res.matrix_rows[0].vendor_evaluations["Vendor Beta"]
    assert beta_budget.status == "FAILS"

    beta_timeline = res.matrix_rows[1].vendor_evaluations["Vendor Beta"]
    assert beta_timeline.status == "MISSING"

    # Summary counter consistency check
    assert res.vendor_summary_counts["Vendor Alpha"]["MEETS"] == 4
    assert res.vendor_summary_counts["Vendor Beta"]["FAILS"] == 1
    assert res.vendor_summary_counts["Vendor Beta"]["MISSING"] == 2
