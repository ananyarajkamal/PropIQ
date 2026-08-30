"""Unit tests for comparison API router endpoints."""

import fitz
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.api.routes.comparison import FACT_SHEETS_CACHE
from app.models import VendorFactSheet, CategoryExtractionResult

client = TestClient(app)


def make_pdf_bytes(text: str) -> bytes:
    """Generate in-memory valid PDF bytes for endpoint testing."""
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), text)
    data = doc.tobytes()
    doc.close()
    return data


def test_comparison_endpoint_success():
    """Verify POST /api/comparison/evaluate returns structured requirement matrix."""
    pdf1 = make_pdf_bytes("Northstar proposal: Pricing $180,000 annually. Implementation 720 hours. ISO 27001 certified.")
    pdf2 = make_pdf_bytes("Meridian proposal: Pricing $250,000 annually. Implementation 45 days. SOC 2 certified.")

    multipart = [
        ("files", ("northstar.pdf", pdf1, "application/pdf")),
        ("files", ("meridian.pdf", pdf2, "application/pdf")),
        ("vendor_names", (None, "Northstar Systems")),
        ("vendor_names", (None, "Meridian Labs")),
    ]

    process_resp = client.post("/api/proposals/process", files=multipart)
    assert process_resp.status_code == 200
    session_id = process_resp.json()["session_id"]

    # Populate FACT_SHEETS_CACHE for session to test deterministic Python comparison API offline
    FACT_SHEETS_CACHE[session_id] = [
        VendorFactSheet(
            vendor_name="Northstar Systems",
            categories=[
                CategoryExtractionResult(category="Pricing", status="FOUND", raw_value="$180,000 annually", summary="$180,000"),
                CategoryExtractionResult(category="Delivery / Implementation", status="FOUND", raw_value="720 hours", summary="720 hours"),
                CategoryExtractionResult(category="Certifications", status="FOUND", raw_value="ISO 27001", summary="ISO 27001"),
            ],
        ),
        VendorFactSheet(
            vendor_name="Meridian Labs",
            categories=[
                CategoryExtractionResult(category="Pricing", status="FOUND", raw_value="$250,000 annually", summary="$250,000"),
                CategoryExtractionResult(category="Delivery / Implementation", status="FOUND", raw_value="45 days", summary="45 days"),
                CategoryExtractionResult(category="Certifications", status="FOUND", raw_value="SOC 2", summary="SOC 2"),
            ],
        ),
    ]

    eval_payload = {
        "session_id": session_id,
        "requirements": {
            "budget_ceiling": 200000,
            "timeline_value": 30,
            "timeline_unit": "days",
            "certifications": ["ISO 27001"],
        },
    }

    comp_resp = client.post("/api/comparison/evaluate", json=eval_payload)
    assert comp_resp.status_code == 200
    data = comp_resp.json()
    assert data["status"] == "success"
    assert len(data["matrix_rows"]) >= 3
    assert "vendor_summary_counts" in data
