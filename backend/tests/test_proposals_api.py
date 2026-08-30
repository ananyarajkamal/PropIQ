"""Unit tests for proposal processing API router endpoint."""

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


def test_process_proposals_success_2_files():
    """Verify processing 2 valid PDF proposals returns 200 OK, session_id, and summaries."""
    pdf1 = make_pdf_bytes("Vendor 1 Proposal text content with $10,000 price.")
    pdf2 = make_pdf_bytes("Vendor 2 Proposal text content with $12,000 price.")

    multipart = [
        ("files", ("proposal1.pdf", pdf1, "application/pdf")),
        ("files", ("proposal2.pdf", pdf2, "application/pdf")),
        ("vendor_names", (None, "Vendor Alpha")),
        ("vendor_names", (None, "Vendor Beta")),
    ]

    response = client.post("/api/proposals/process", files=multipart)
    assert response.status_code == 200

    resp_json = response.json()
    assert resp_json["status"] == "success"
    assert resp_json["session_id"].startswith("sess_")
    assert resp_json["total_proposals"] == 2
    assert len(resp_json["proposals"]) == 2
    assert resp_json["proposals"][0]["vendor_name"] == "Vendor Alpha"
    assert resp_json["proposals"][1]["vendor_name"] == "Vendor Beta"
    assert resp_json["proposals"][0]["status"] == "Ready for Analysis"


def test_process_proposals_rejected_fewer_than_2():
    """Verify uploading 1 proposal returns 400 Bad Request."""
    pdf1 = make_pdf_bytes("Single vendor proposal")
    multipart = [
        ("files", ("proposal1.pdf", pdf1, "application/pdf")),
        ("vendor_names", (None, "Solo Vendor")),
    ]

    response = client.post("/api/proposals/process", files=multipart)
    assert response.status_code == 400
    assert "at least 2 proposals" in response.json()["detail"]


def test_process_proposals_rejected_duplicate_vendor_names():
    """Verify uploading duplicate vendor names returns 400 Bad Request."""
    pdf1 = make_pdf_bytes("Vendor proposal 1")
    pdf2 = make_pdf_bytes("Vendor proposal 2")

    multipart = [
        ("files", ("proposal1.pdf", pdf1, "application/pdf")),
        ("files", ("proposal2.pdf", pdf2, "application/pdf")),
        ("vendor_names", (None, "Acme Corp")),
        ("vendor_names", (None, "  ACME CORP  ")),  # Case-insensitive duplicate
    ]

    response = client.post("/api/proposals/process", files=multipart)
    assert response.status_code == 400
    assert "unique" in response.json()["detail"].lower()


def test_process_proposals_rejected_non_pdf_file():
    """Verify uploading a non-PDF file extension returns 400 Bad Request."""
    pdf1 = make_pdf_bytes("Vendor proposal 1")
    txt_file = b"Plain text file"

    multipart = [
        ("files", ("proposal1.pdf", pdf1, "application/pdf")),
        ("files", ("proposal2.txt", txt_file, "text/plain")),
        ("vendor_names", (None, "Vendor 1")),
        ("vendor_names", (None, "Vendor 2")),
    ]

    response = client.post("/api/proposals/process", files=multipart)
    assert response.status_code == 400
    assert "only pdf files are supported" in response.json()["detail"].lower()


def test_get_session_summary_success():
    """Verify GET /api/proposals/session/{session_id} hydrates active session metadata."""
    pdf1 = make_pdf_bytes("Vendor 1 Proposal text content.")
    pdf2 = make_pdf_bytes("Vendor 2 Proposal text content.")

    multipart = [
        ("files", ("prop1.pdf", pdf1, "application/pdf")),
        ("files", ("prop2.pdf", pdf2, "application/pdf")),
        ("vendor_names", (None, "Alpha Corp")),
        ("vendor_names", (None, "Beta Inc")),
    ]

    proc_res = client.post("/api/proposals/process", files=multipart)
    assert proc_res.status_code == 200
    session_id = proc_res.json()["session_id"]

    summary_res = client.get(f"/api/proposals/session/{session_id}")
    assert summary_res.status_code == 200
    sdata = summary_res.json()
    assert sdata["status"] == "success"
    assert sdata["session_id"] == session_id
    assert sdata["total_proposals"] == 2
    assert len(sdata["proposals"]) == 2
    assert sdata["proposals"][0]["vendor_name"] in ["Alpha Corp", "Beta Inc"]


def test_get_session_summary_expired_or_invalid():
    """Verify GET /api/proposals/session/{session_id} returns 404 for invalid session."""
    response = client.get("/api/proposals/session/sess_nonexistent_12345")
    assert response.status_code == 404
    assert "expired or not found" in response.json()["detail"].lower()

