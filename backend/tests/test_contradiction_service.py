"""Unit tests for ContradictionService module."""

import pytest
from app.models import (
    VendorFactSheet,
    CategoryExtractionResult,
    EvidenceCitationModel,
    ContradictionStatus,
    RiskSeverity,
)
from app.services.contradiction_service import ContradictionService


def test_phase3_conflicting_fact_extraction():
    """Verify Phase 3 CONFLICTING extracted facts are directly converted into contradiction findings."""
    cs = ContradictionService()

    cit1 = EvidenceCitationModel(
        evidence_id="E1",
        vendor_name="Vendor Dual",
        source_filename="vendor_dual.pdf",
        start_page=2,
        end_page=2,
        chunk_id="v01_p002_c001",
        excerpt_text="Implementation schedule is 30 calendar days.",
    )
    cit2 = EvidenceCitationModel(
        evidence_id="E2",
        vendor_name="Vendor Dual",
        source_filename="vendor_dual.pdf",
        start_page=14,
        end_page=14,
        chunk_id="v01_p014_c003",
        excerpt_text="Implementation requires 45 business days minimum.",
    )

    fact_sheets = [
        VendorFactSheet(
            vendor_name="Vendor Dual",
            categories=[
                CategoryExtractionResult(
                    category="Delivery / Implementation",
                    status="CONFLICTING",
                    raw_value="30 days on page 2 vs 45 days on page 14",
                    summary="Implementation timeline stated as 30 days and 45 days in different sections.",
                    notes="Conflicting implementation schedules found in proposal.",
                    evidence_citations=[cit1, cit2],
                )
            ],
        )
    ]

    findings = cs.analyze_session_contradictions("sess_mock_ctr_1", fact_sheets=fact_sheets)

    assert len(findings) >= 1
    c = findings[0]
    assert c.vendor_name == "Vendor Dual"  # Same-vendor enforcement!
    assert c.status == ContradictionStatus.CONFIRMED_CONTRADICTION
    assert len(c.evidence_a) >= 1
    assert len(c.evidence_b) >= 1


def test_false_positive_control_plan_tiers():
    """Verify false-positive control: Standard 8x5 vs Premium 24x7 support is excluded from contradictions."""
    cs = ContradictionService()

    c1 = EvidenceCitationModel(evidence_id="E1", vendor_name="V", source_filename="f.pdf", start_page=1, end_page=1, chunk_id="c1", excerpt_text="Standard support operates 8x5.")
    c2 = EvidenceCitationModel(evidence_id="E2", vendor_name="V", source_filename="f.pdf", start_page=2, end_page=2, chunk_id="c2", excerpt_text="Premium support operates 24x7.")

    raw_candidates = [
        type('ContradictionFinding', (), {
            'vendor_name': 'V',
            'category': 'Support',
            'severity': RiskSeverity.MEDIUM,
            'statement_a': 'Standard support is 8x5',
            'statement_b': 'Premium support is 24x7',
            'context_a': 'Page 1',
            'context_b': 'Page 2',
            'evidence_a': [c1],
            'evidence_b': [c2],
            'reason': 'Plan tier support hours',
            'status': ContradictionStatus.POTENTIAL_CONTRADICTION,
        })
    ]

    filtered = cs._validate_and_filter_contradictions(raw_candidates)
    assert len(filtered) == 0  # Excluded by plan-tier false-positive control!


def test_false_positive_control_initial_vs_renewal():
    """Verify false-positive control: Initial 12m term vs 24m renewal term is excluded from contradictions."""
    cs = ContradictionService()

    c1 = EvidenceCitationModel(evidence_id="E1", vendor_name="V", source_filename="f.pdf", start_page=1, end_page=1, chunk_id="c1", excerpt_text="Initial term is 12 months.")
    c2 = EvidenceCitationModel(evidence_id="E2", vendor_name="V", source_filename="f.pdf", start_page=2, end_page=2, chunk_id="c2", excerpt_text="Each renewal term is 24 months.")

    raw_candidates = [
        type('ContradictionFinding', (), {
            'vendor_name': 'V',
            'category': 'Term',
            'severity': RiskSeverity.MEDIUM,
            'statement_a': 'Initial term is 12 months',
            'statement_b': 'Renewal term is 24 months',
            'context_a': 'Page 1',
            'context_b': 'Page 2',
            'evidence_a': [c1],
            'evidence_b': [c2],
            'reason': 'Initial vs renewal term difference',
            'status': ContradictionStatus.POTENTIAL_CONTRADICTION,
        })
    ]

    filtered = cs._validate_and_filter_contradictions(raw_candidates)
    assert len(filtered) == 0  # Excluded by initial vs renewal false-positive control!
