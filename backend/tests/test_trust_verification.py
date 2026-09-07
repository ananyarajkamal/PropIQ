"""Tests for PropIQ Trust, Evidence Grounding, and Affirmative Risk Verification.

Verifies the 3 core trust pillars:
1. Clause presence vs. meeting a requirement (no false MEETS; conflicting terms FAIL, indeterminate terms produce NEEDS_REVIEW).
2. Evidence grounding and topical validation (cross-category citation collisions rejected, ungrounded claims marked UNVERIFIED).
3. Topical similarity vs. affirmative risk creation (negatives/safe harbors NOT flagged, affirmative risks DETECTED).
"""

import pytest
from app.models import (
    ProcurementRequirements,
    VendorFactSheet,
    CategoryExtractionResult,
    EvidenceCitationModel,
    RequirementPriority,
    RiskCategory,
    RiskStatus,
    RiskFindingModel,
)
from app.services.comparison_service import ComparisonService
from app.services.evidence_validator import EvidenceValidator
from app.services.risk_service import RiskService
from app.services.scoring_service import ScoringService
from app.services.gap_service import GapService


# ==============================================================================
# Pillar 1: Finding a clause vs. Meeting a requirement
# ==============================================================================

def test_termination_clause_restriction_fails_anytime_requirement():
    """Buyer wants cancellation at any time; vendor allows only after two years.
    
    Must NOT mark MEETS simply because a cancellation clause was found.
    Must mark FAILS due to conflicting lock-in restriction.
    """
    comp = ComparisonService()
    reqs = ProcurementRequirements(
        termination_requirement="Cancellation at any time",
        termination_priority=RequirementPriority.MUST_HAVE,
    )

    # Vendor has a cancellation clause, but it restricts cancellation to after 2 years
    fs_vendor = VendorFactSheet(
        vendor_name="Restricted Vendor",
        categories=[
            CategoryExtractionResult(
                category="Termination / Exit",
                status="FOUND",
                raw_value="cancellation is allowed only after two years",
                summary="Cancellation permitted only after initial two years.",
                evidence_citations=[],
                is_verified=True,
            )
        ],
    )

    res = comp.evaluate_session_comparison(
        session_id="sess_trust_1",
        requirements=reqs,
        fact_sheets=[fs_vendor],
    )

    eval_res = res.matrix_rows[0].vendor_evaluations["Restricted Vendor"]
    assert eval_res.status == "FAILS", f"Expected FAILS, got {eval_res.status}: {eval_res.explanation}"
    assert "restricts" in eval_res.explanation.lower() or "fail" in eval_res.explanation.lower()


def test_termination_indeterminate_clause_marks_needs_review():
    """When a clause is found but cannot establish whether requirement is met,
    display 'NEEDS_REVIEW' instead of 'MEETS'.
    """
    comp = ComparisonService()
    reqs = ProcurementRequirements(
        termination_requirement="Cancellation at any time",
        termination_priority=RequirementPriority.HIGH,
    )

    # Vendor mentions termination in general without clear convenience / anytime terms
    fs_vendor = VendorFactSheet(
        vendor_name="Vague Vendor",
        categories=[
            CategoryExtractionResult(
                category="Termination / Exit",
                status="FOUND",
                raw_value="Standard termination procedures apply as set forth in master services handbook",
                summary="Termination follows master services handbook.",
                evidence_citations=[],
                is_verified=True,
            )
        ],
    )

    res = comp.evaluate_session_comparison(
        session_id="sess_trust_2",
        requirements=reqs,
        fact_sheets=[fs_vendor],
    )

    eval_res = res.matrix_rows[0].vendor_evaluations["Vague Vendor"]
    assert eval_res.status == "NEEDS_REVIEW", f"Expected NEEDS_REVIEW, got {eval_res.status}: {eval_res.explanation}"


def test_termination_confirmed_anytime_marks_meets():
    """When vendor terms explicitly confirm cancellation at any time without restriction,
    status is MEETS.
    """
    comp = ComparisonService()
    reqs = ProcurementRequirements(
        termination_requirement="Buyer wants cancellation at any time",
        termination_priority=RequirementPriority.HIGH,
    )

    fs_vendor = VendorFactSheet(
        vendor_name="Flexible Vendor",
        categories=[
            CategoryExtractionResult(
                category="Termination / Exit",
                status="FOUND",
                raw_value="Customer may terminate for convenience at any time with 30 days notice",
                summary="Convenience termination permitted at any time.",
                evidence_citations=[],
                is_verified=True,
            )
        ],
    )

    res = comp.evaluate_session_comparison(
        session_id="sess_trust_3",
        requirements=reqs,
        fact_sheets=[fs_vendor],
    )

    eval_res = res.matrix_rows[0].vendor_evaluations["Flexible Vendor"]
    assert eval_res.status == "MEETS", f"Expected MEETS, got {eval_res.status}: {eval_res.explanation}"


def test_textual_liability_unsupported_or_indeterminate_not_marked_meets():
    """Textual requirements must not default to MEETS simply because text was extracted."""
    comp = ComparisonService()
    reqs = ProcurementRequirements(
        liability_requirement="Uncapped liability for data breaches",
    )

    # Vendor caps liability
    fs_capped = VendorFactSheet(
        vendor_name="Capped Vendor",
        categories=[
            CategoryExtractionResult(
                category="Liability",
                status="FOUND",
                raw_value="Aggregate liability shall not exceed 12 months fees paid",
                summary="Liability capped at 12 months fees.",
                evidence_citations=[],
                is_verified=True,
            )
        ],
    )

    res = comp.evaluate_session_comparison(
        session_id="sess_trust_4",
        requirements=reqs,
        fact_sheets=[fs_capped],
    )

    eval_res = res.matrix_rows[0].vendor_evaluations["Capped Vendor"]
    assert eval_res.status == "FAILS", f"Expected FAILS, got {eval_res.status}: {eval_res.explanation}"


# ==============================================================================
# Pillar 2: Evidence Grounding & Citation Validation
# ==============================================================================

def test_evidence_validator_rejects_cross_category_number_collision():
    """Implementation 30 days must NOT validate or attach to Payment Terms Net 30."""
    implementation_excerpt = "The implementation and onboarding process will take 30 days from contract signing."
    payment_claim = "Net 30 days"

    # Payment Terms requires payment topical markers, which are absent in implementation excerpt
    is_valid = EvidenceValidator.validate_claim_topical_support(
        category="Payment Terms",
        raw_value=payment_claim,
        excerpt_text=implementation_excerpt,
    )
    assert not is_valid, "EvidenceValidator should reject implementation text for payment terms claim"


def test_evidence_validator_accepts_grounded_payment_citation():
    """Proper payment invoice excerpt validates successfully for Payment Terms."""
    payment_excerpt = "Invoices are payable within 30 days of receipt via electronic bank transfer."
    payment_claim = "Net 30"

    is_valid = EvidenceValidator.validate_claim_topical_support(
        category="Payment Terms",
        raw_value=payment_claim,
        excerpt_text=payment_excerpt,
    )
    assert is_valid, "EvidenceValidator should accept valid payment terms excerpt"


def test_unverified_category_propagation_in_comparison_and_scoring():
    """When an extracted claim is marked UNVERIFIED, comparison must propagate UNVERIFIED
    and scoring must NOT treat it as confirmed or increment requirements_met_count.
    """
    comp = ComparisonService()
    scoring = ScoringService()

    reqs = ProcurementRequirements(
        payment_terms="Net 30",
        payment_priority=RequirementPriority.MUST_HAVE,
    )

    # Vendor has an unverified payment claim (e.g. AI claimed 30 days without supporting citation)
    fs_unverified = VendorFactSheet(
        vendor_name="Unverified Vendor",
        categories=[
            CategoryExtractionResult(
                category="Payment Terms",
                status="UNVERIFIED",
                raw_value=None,
                summary="Payment terms unverified in proposal evidence.",
                evidence_citations=[],
                is_verified=False,
            )
        ],
    )

    comp_res = comp.evaluate_session_comparison(
        session_id="sess_trust_unverified",
        requirements=reqs,
        fact_sheets=[fs_unverified],
    )

    eval_res = comp_res.matrix_rows[0].vendor_evaluations["Unverified Vendor"]
    assert eval_res.status == "UNVERIFIED"
    assert not eval_res.is_verified

    score_res = scoring.evaluate_session_scoring(
        session_id="sess_trust_unverified",
        requirements=reqs,
        matrix_rows=comp_res.matrix_rows,
    )

    v_score = score_res.vendor_scores[0]
    # Requirements met must be 0
    assert v_score.requirements_met_count == 0
    # Must-have failed/unverified labels must flag this requirement
    assert len(v_score.must_have_failed_labels) > 0


def test_gap_service_generates_zero_citations_for_unverified_fact():
    """Gap service must not attach unrelated citations to an UNVERIFIED gap."""
    gap_srv = GapService()
    comp = ComparisonService()

    reqs = ProcurementRequirements(
        payment_terms="Net 30",
        payment_priority=RequirementPriority.HIGH,
    )

    fs_unverified = VendorFactSheet(
        vendor_name="Vendor X",
        categories=[
            CategoryExtractionResult(
                category="Payment Terms",
                status="UNVERIFIED",
                raw_value=None,
                summary="No verifying evidence found.",
                evidence_citations=[],
                is_verified=False,
            )
        ],
    )

    comp_res = comp.evaluate_session_comparison(
        session_id="sess_gap_test",
        requirements=reqs,
        fact_sheets=[fs_unverified],
    )

    gaps = gap_srv.detect_session_gaps(
        session_id="sess_gap_test",
        matrix_rows=comp_res.matrix_rows,
        requirements=reqs,
    )

    unverified_gaps = [g for g in gaps if g.source_status == "UNVERIFIED"]
    assert len(unverified_gaps) == 1
    assert len(unverified_gaps[0].evidence_citations) == 0, "UNVERIFIED gap must have 0 citations"


# ==============================================================================
# Pillar 3: Topical Similarity vs. Affirmative Risk Creation
# ==============================================================================

def test_risk_verification_rejects_negative_ai_training_statement():
    """'We will never use your data for AI training' must NOT be flagged as a DATA_USAGE risk."""
    risk_srv = RiskService()

    negative_clause = "We will never use your data for AI training or machine learning models under any circumstances."
    creates_risk = risk_srv._verify_risk_in_clause(RiskCategory.DATA_USAGE, negative_clause)

    assert not creates_risk, "Negative clause must NOT be flagged as creating DATA_USAGE risk"


def test_risk_verification_detects_affirmative_ai_training_clause():
    """'We may use your data for AI training' MUST be detected as a DATA_USAGE risk."""
    risk_srv = RiskService()

    affirmative_clause = "Company reserves the right to use customer data to train machine learning models and improve services."
    creates_risk = risk_srv._verify_risk_in_clause(RiskCategory.DATA_USAGE, affirmative_clause)

    assert creates_risk, "Affirmative clause MUST be detected as creating DATA_USAGE risk"


def test_risk_verification_rejects_fixed_price_statement():
    """'Fees will remain fixed and no price increase shall occur' must NOT be flagged as PRICE_ESCALATION."""
    risk_srv = RiskService()

    fixed_price_clause = "All subscription fees remain fixed for the duration of the initial term, and no price increase will occur."
    creates_risk = risk_srv._verify_risk_in_clause(RiskCategory.PRICE_ESCALATION, fixed_price_clause)

    assert not creates_risk, "Fixed price protection clause must NOT be flagged as PRICE_ESCALATION risk"


def test_risk_verification_detects_affirmative_price_escalation():
    """'Vendor reserves the right to increase fees annually by up to 8%' MUST be detected."""
    risk_srv = RiskService()

    escalation_clause = "Vendor reserves the right to annual price increase of up to 8% upon contract renewal."
    creates_risk = risk_srv._verify_risk_in_clause(RiskCategory.PRICE_ESCALATION, escalation_clause)

    assert creates_risk, "Affirmative price escalation clause MUST be detected as PRICE_ESCALATION risk"
