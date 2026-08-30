"""Unit tests for risks API router endpoint POST /api/risks/analyze."""

import fitz
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.api.routes.comparison import FACT_SHEETS_CACHE
from app.models import VendorFactSheet, CategoryExtractionResult, EvidenceCitationModel

client = TestClient(app)


def make_pdf_bytes(text: str) -> bytes:
    """Generate in-memory valid PDF bytes for endpoint testing."""
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), text)
    data = doc.tobytes()
    doc.close()
    return data


def test_risks_analyze_endpoint_success():
    """Verify POST /api/risks/analyze returns risk and contradiction findings."""
    pdf1 = make_pdf_bytes("Northstar proposal: Automatically renews for 12 months unless cancelled 90 days prior. Unlimited liability.")
    pdf2 = make_pdf_bytes("Meridian proposal: Pricing fixed. Implementation 45 days.")

    multipart = [
        ("files", ("northstar.pdf", pdf1, "application/pdf")),
        ("files", ("meridian.pdf", pdf2, "application/pdf")),
        ("vendor_names", (None, "Northstar Systems")),
        ("vendor_names", (None, "Meridian Labs")),
    ]

    process_resp = client.post("/api/proposals/process", files=multipart)
    assert process_resp.status_code == 200
    session_id = process_resp.json()["session_id"]

    # Pre-populate FACT_SHEETS_CACHE for session to test offline API
    cit1 = EvidenceCitationModel(
        evidence_id="E1",
        vendor_name="Northstar Systems",
        source_filename="northstar.pdf",
        start_page=1,
        end_page=1,
        chunk_id="v01_p001_c001",
        excerpt_text="Automatically renews for 12 months unless cancelled 90 days prior.",
    )
    FACT_SHEETS_CACHE[session_id] = [
        VendorFactSheet(
            vendor_name="Northstar Systems",
            categories=[
                CategoryExtractionResult(
                    category="Contract Renewal",
                    status="FOUND",
                    raw_value="Automatically renews for 12 months unless cancelled 90 days prior.",
                    summary="12-month auto renewal with 90 days notice",
                    evidence_citations=[cit1],
                )
            ],
        )
    ]

    analyze_payload = {
        "session_id": session_id,
        "requirements": {
            "renewal_preference": "No auto renewal",
        },
    }

    resp = client.post("/api/risks/analyze", json=analyze_payload)
    assert resp.status_code == 200
    data = resp.json()

    assert data["status"] == "success"
    assert "risk_findings" in data
    assert "contradiction_findings" in data
    assert "high_priority_count" in data
    assert "medium_priority_count" in data
