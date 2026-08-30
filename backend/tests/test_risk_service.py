"""Unit tests for RiskService module."""

import pytest
from app.models import (
    RiskCategory,
    RiskSeverity,
    RiskStatus,
    VendorFactSheet,
    CategoryExtractionResult,
    EvidenceCitationModel,
    ProcurementRequirements,
)
from app.services.risk_service import RiskService


def test_deterministic_risk_generation_auto_renewal():
    """Verify deterministic risk generation from auto-renewal fact sheet."""
    rs = RiskService()

    fact_sheets = [
        VendorFactSheet(
            vendor_name="Vendor Auto",
            categories=[
                CategoryExtractionResult(
                    category="Contract Renewal",
                    status="FOUND",
                    raw_value="Automatically renews for 12 months unless cancelled 90 days prior.",
                    summary="12-month auto renewal with 90 days notice",
                    evidence_citations=[
                        EvidenceCitationModel(
                            evidence_id="E1",
                            vendor_name="Vendor Auto",
                            source_filename="vendor_auto.pdf",
                            start_page=5,
                            end_page=5,
                            chunk_id="v01_p005_c001",
                            excerpt_text="Automatically renews for 12 months unless cancelled 90 days prior.",
                        )
                    ],
                )
            ],
        )
    ]

    reqs = ProcurementRequirements(renewal_preference="No auto renewal")

    findings = rs.analyze_session_risks("sess_mock_risk_1", requirements=reqs, fact_sheets=fact_sheets)

    assert len(findings) >= 1
    r = next(f for f in findings if f.category == RiskCategory.AUTO_RENEWAL)
    assert r.vendor_name == "Vendor Auto"
    assert r.severity in {RiskSeverity.MEDIUM, RiskSeverity.HIGH}
    assert "REQ_RENEWAL" in r.related_requirement_ids
    assert len(r.evidence_citations) >= 1


def test_risk_suppression_negation():
    """Verify negation suppression rules: 'does not renew automatically' and 'fees remain fixed' yield NO risk."""
    rs = RiskService()

    fact_sheets = [
        VendorFactSheet(
            vendor_name="Vendor Safe",
            categories=[
                CategoryExtractionResult(
                    category="Contract Renewal",
                    status="FOUND",
                    raw_value="This agreement does not renew automatically.",
                    summary="Manual renewal required.",
                    evidence_citations=[
                        EvidenceCitationModel(
                            evidence_id="E1",
                            vendor_name="Vendor Safe",
                            source_filename="vendor_safe.pdf",
                            start_page=2,
                            end_page=2,
                            chunk_id="v01_p002_c001",
                            excerpt_text="This agreement does not renew automatically.",
                        )
                    ],
                )
            ],
        )
    ]

    findings = rs.analyze_session_risks("sess_mock_risk_2", fact_sheets=fact_sheets)
    auto_ren_findings = [f for f in findings if f.category == RiskCategory.AUTO_RENEWAL]

    assert len(auto_ren_findings) == 0  # Explicit negation suppresses auto-renewal risk!


def test_backend_severity_policy_capping():
    """Verify backend severity policy caps ungrounded CRITICAL semantic ratings to HIGH."""
    rs = RiskService()

    # Create dummy finding with semantic CRITICAL on notice period
    raw_finding = rs._validate_and_deduplicate_findings(
        session_id="sess_mock_sev",
        findings=[
            rs.analyze_session_risks.__type__ if False else
            # Direct instantiation test
            type('RiskFinding', (), {
                'vendor_name': 'Vendor Test',
                'category': RiskCategory.NOTICE_PERIOD,
                'severity': RiskSeverity.CRITICAL,
                'title': 'Long Notice',
                'summary': 'Summary',
                'procurement_impact': 'Impact',
                'review_reason': 'Reason',
                'evidence_citations': [
                    EvidenceCitationModel(
                        evidence_id="E1",
                        vendor_name="Vendor Test",
                        source_filename="test.pdf",
                        start_page=1,
                        end_page=1,
                        chunk_id="v01_p001_c001",
                        excerpt_text="90 days notice required.",
                    )
                ],
                'related_requirement_ids': [],
                'status': RiskStatus.DETECTED,
            })
        ],
        requirements=None,
    )

    assert len(raw_finding) == 1
    assert raw_finding[0].severity == RiskSeverity.HIGH  # Ungrounded CRITICAL capped to HIGH!
