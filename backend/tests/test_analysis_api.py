"""Unit tests for analysis API router endpoints."""

import fitz
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def make_pdf_bytes(text: str) -> bytes:
    """Generate in-memory valid PDF bytes for endpoint testing."""
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), text)
    data = doc.tobytes()
    doc.close()
    return data


def test_requirements_endpoint_success():
    """Verify POST /api/analysis/requirements validates and saves session requirements."""
    pdf1 = make_pdf_bytes("Northstar proposal text")
    pdf2 = make_pdf_bytes("Meridian proposal text")

    multipart = [
        ("files", ("northstar.pdf", pdf1, "application/pdf")),
        ("files", ("meridian.pdf", pdf2, "application/pdf")),
        ("vendor_names", (None, "Northstar Systems")),
        ("vendor_names", (None, "Meridian Labs")),
    ]

    process_resp = client.post("/api/proposals/process", files=multipart)
    assert process_resp.status_code == 200
    session_id = process_resp.json()["session_id"]

    req_payload = {
        "session_id": session_id,
        "requirements": {
            "budget_ceiling": 200000,
            "minimum_sla": 99.9,
            "payment_terms": "Net 30",
            "certifications": ["ISO 27001"],
        },
    }

    req_resp = client.post("/api/analysis/requirements", json=req_payload)
    assert req_resp.status_code == 200
    assert req_resp.json()["status"] == "success"


def test_requirements_endpoint_rejected_blank():
    """Verify submitting empty requirements returns 400 Bad Request."""
    pdf1 = make_pdf_bytes("Northstar proposal text")
    pdf2 = make_pdf_bytes("Meridian proposal text")

    multipart = [
        ("files", ("northstar.pdf", pdf1, "application/pdf")),
        ("files", ("meridian.pdf", pdf2, "application/pdf")),
        ("vendor_names", (None, "Northstar Systems")),
        ("vendor_names", (None, "Meridian Labs")),
    ]

    process_resp = client.post("/api/proposals/process", files=multipart)
    session_id = process_resp.json()["session_id"]

    req_payload = {
        "session_id": session_id,
        "requirements": {},  # No fields specified
    }

    req_resp = client.post("/api/analysis/requirements", json=req_payload)
    assert req_resp.status_code == 400
    assert "at least one procurement evaluation requirement" in req_resp.json()["detail"]
