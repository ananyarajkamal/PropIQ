"""Unit tests for clarifications API router endpoint POST /api/clarifications/generate."""

import fitz
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.api.routes.comparison import COMPARISON_CACHE, FACT_SHEETS_CACHE
from app.models import (
    ComparisonResponse,
    ComparisonMatrixRow,
    RequirementEvaluationResult,
    ProcurementRequirements,
    VendorFactSheet,
    CategoryExtractionResult,
    EvidenceCitationModel,
)

client = TestClient(app)


def make_pdf_bytes(text: str) -> bytes:
    """Generate in-memory valid PDF bytes for endpoint testing."""
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), text)
    data = doc.tobytes()
    doc.close()
    return data


def test_clarifications_generate_endpoint_success():
    """Verify POST /api/clarifications/generate returns vendor questions and counts."""
    pdf1 = make_pdf_bytes("Northstar proposal: Automatically renews for 12 months unless cancelled 90 days prior.")
    pdf2 = make_pdf_bytes("Meridian proposal: Pricing starting at $150,000.")

    multipart = [
        ("files", ("northstar.pdf", pdf1, "application/pdf")),
        ("files", ("meridian.pdf", pdf2, "application/pdf")),
        ("vendor_names", (None, "Northstar Systems")),
        ("vendor_names", (None, "Meridian Labs")),
    ]

    process_resp = client.post("/api/proposals/process", files=multipart)
    assert process_resp.status_code == 200
    session_id = process_resp.json()["session_id"]

    # Pre-populate COMPARISON_CACHE for session to test offline API
    COMPARISON_CACHE[session_id] = ComparisonResponse(
        status="success",
        session_id=session_id,
        requirements=ProcurementRequirements(warranty_value=12, warranty_unit="months"),
        matrix_rows=[
            ComparisonMatrixRow(
                category="Warranty",
                requirement_label="Minimum Warranty (12 months)",
                vendor_evaluations={
                    "Northstar Systems": RequirementEvaluationResult(
                        requirement_id="REQ_WARRANTY",
                        category="Warranty",
                        vendor_name="Northstar Systems",
                        status="MISSING",
                        explanation="No warranty duration found in proposal.",
                        comparison_rule="vendor_warranty >= 12 months",
                    )
                },
            )
        ],
        vendor_summary_counts={"Northstar Systems": {"MISSING": 1}},
        privacy_notice="Notice",
    )

    from app.services.session_state_service import get_session_state_service
    from app.models import ModuleStatus
    state_service = get_session_state_service()
    state_service.set_module_status(session_id, "comparison", ModuleStatus.COMPLETED, fingerprint="comp_test")
    state_service.set_module_status(session_id, "risks_contradictions", ModuleStatus.COMPLETED, fingerprint="risk_test")

    payload = {
        "session_id": session_id,
        "requirements": {
            "warranty_value": 12,
            "warranty_unit": "months",
        },
    }

    resp = client.post("/api/clarifications/generate", json=payload)
    assert resp.status_code == 200
    data = resp.json()

    assert data["status"] == "success"
    assert "questions" in data
    assert data["total_questions"] >= 1
    assert "vendor_question_counts" in data
    assert data["vendor_question_counts"]["Northstar Systems"] >= 1


def test_clarifications_unknown_session_404():
    """Verify POST /api/clarifications/generate returns HTTP 404 for unknown session ID."""
    resp = client.post(
        "/api/clarifications/generate",
        json={"session_id": "sess_non_existent_12345"},
    )
    assert resp.status_code == 404
    assert "not found" in resp.json()["detail"].lower()
