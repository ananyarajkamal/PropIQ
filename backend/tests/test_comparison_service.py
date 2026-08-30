"""Unit tests for ComparisonService module."""

import pytest
from app.models import (
    ProcurementRequirements,
    VendorFactSheet,
    CategoryExtractionResult,
)
from app.services.comparison_service import ComparisonService


def test_comparison_demo_scenario_timeline():
    """Verify demo scenario: 720 hours (MEETS), 45 days (FAILS), 4 weeks (MEETS) against 30-day max timeline."""
    cs = ComparisonService()
    reqs = ProcurementRequirements(timeline_value=30, timeline_unit="days")

    fact_sheets = [
        VendorFactSheet(
            vendor_name="Vendor A",
            categories=[
                CategoryExtractionResult(
                    category="Delivery / Implementation",
                    status="FOUND",
                    raw_value="720 hours implementation schedule",
                    summary="720 hours deployment",
                )
            ],
        ),
        VendorFactSheet(
            vendor_name="Vendor B",
            categories=[
                CategoryExtractionResult(
                    category="Delivery / Implementation",
                    status="FOUND",
                    raw_value="45 days deployment timeline",
                    summary="45 days deployment",
                )
            ],
        ),
        VendorFactSheet(
            vendor_name="Vendor C",
            categories=[
                CategoryExtractionResult(
                    category="Delivery / Implementation",
                    status="FOUND",
                    raw_value="4 weeks total timeline",
                    summary="4 weeks deployment",
                )
            ],
        ),
    ]

    res = cs.evaluate_session_comparison("sess_demo", reqs, fact_sheets)

    assert len(res.matrix_rows) == 1
    row = res.matrix_rows[0]
    evals = row.vendor_evaluations

    # Vendor A (720 hours = 30 days) -> MEETS
    assert evals["Vendor A"].status == "MEETS"
    assert evals["Vendor A"].normalized_vendor_value == "30.0 days"

    # Vendor B (45 days) -> FAILS
    assert evals["Vendor B"].status == "FAILS"
    assert evals["Vendor B"].normalized_vendor_value == "45.0 days"

    # Vendor C (4 weeks = 28 days) -> MEETS
    assert evals["Vendor C"].status == "MEETS"
    assert evals["Vendor C"].normalized_vendor_value == "28.0 days"


def test_comparison_payment_buyer_perspective():
    """Verify buyer-perspective rule: Net 45 meets Net 30 requirement because longer payment terms favor cash flow."""
    cs = ComparisonService()
    reqs = ProcurementRequirements(payment_terms="Net 30")

    fact_sheets = [
        VendorFactSheet(
            vendor_name="Vendor Net45",
            categories=[CategoryExtractionResult(category="Payment Terms", status="FOUND", raw_value="Net 45 days", summary="Net 45")],
        ),
        VendorFactSheet(
            vendor_name="Vendor Net15",
            categories=[CategoryExtractionResult(category="Payment Terms", status="FOUND", raw_value="Net 15 days", summary="Net 15")],
        ),
    ]

    res = cs.evaluate_session_comparison("sess_pay", reqs, fact_sheets)
    row = res.matrix_rows[0]

    assert row.vendor_evaluations["Vendor Net45"].status == "MEETS"
    assert row.vendor_evaluations["Vendor Net15"].status == "FAILS"


def test_comparison_certifications_required_set():
    """Verify certification set comparison: MEETS when all present, PARTIAL when subset present."""
    cs = ComparisonService()
    reqs = ProcurementRequirements(certifications=["ISO 27001", "SOC 2 Type II"])

    fact_sheets = [
        VendorFactSheet(
            vendor_name="Vendor Both",
            categories=[CategoryExtractionResult(category="Certifications", status="FOUND", raw_value="ISO 27001, SOC 2 Type II accredited", summary="Both")],
        ),
        VendorFactSheet(
            vendor_name="Vendor ISO Only",
            categories=[CategoryExtractionResult(category="Certifications", status="FOUND", raw_value="ISO-27001 certified", summary="ISO only")],
        ),
    ]

    res = cs.evaluate_session_comparison("sess_certs", reqs, fact_sheets)
    row = res.matrix_rows[0]

    assert row.vendor_evaluations["Vendor Both"].status == "MEETS"
    assert row.vendor_evaluations["Vendor ISO Only"].status == "PARTIAL"


def test_comparison_currency_mismatch():
    """Verify currency mismatch yields UNCLEAR without inventing FX conversion rates."""
    cs = ComparisonService()
    reqs = ProcurementRequirements(budget_ceiling=200000, budget_currency="USD")

    fact_sheets = [
        VendorFactSheet(
            vendor_name="Vendor INR",
            categories=[CategoryExtractionResult(category="Pricing", status="FOUND", raw_value="₹5,00,000 annually", summary="INR pricing")],
        ),
    ]

    res = cs.evaluate_session_comparison("sess_curr", reqs, fact_sheets)
    eval_res = res.matrix_rows[0].vendor_evaluations["Vendor INR"]

    assert eval_res.status == "UNCLEAR"
    assert "Currency mismatch" in eval_res.explanation
