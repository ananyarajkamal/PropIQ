"""Unit tests for retrieval search API endpoint."""

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


def test_retrieval_api_end_to_end():
    """Verify processing proposals and executing retrieval search via REST API."""
    pdf1 = make_pdf_bytes("Northstar Systems annual contract pricing is $180,000. Payment Net 30 days.")
    pdf2 = make_pdf_bytes("Meridian Labs SLA guarantee is 99.5% uptime. Payment 50% upfront.")

    multipart = [
        ("files", ("northstar.pdf", pdf1, "application/pdf")),
        ("files", ("meridian.pdf", pdf2, "application/pdf")),
        ("vendor_names", (None, "Northstar Systems")),
        ("vendor_names", (None, "Meridian Labs")),
    ]

    process_resp = client.post("/api/proposals/process", files=multipart)
    assert process_resp.status_code == 200
    
    session_id = process_resp.json()["session_id"]
    assert session_id.startswith("sess_")

    # Search for payment terms
    search_payload = {
        "session_id": session_id,
        "query": "payment terms and upfront payment",
        "top_k": 2,
    }

    search_resp = client.post("/api/retrieval/search", json=search_payload)
    assert search_resp.status_code == 200

    results = search_resp.json()["results"]
    assert len(results) >= 1
    assert results[0]["chunk_id"].startswith("v")
    assert 0.0 <= results[0]["similarity_score"] <= 1.0

    # Search with Vendor filter
    filtered_payload = {
        "session_id": session_id,
        "query": "pricing",
        "vendor_name": "Northstar Systems",
        "top_k": 2,
    }

    filtered_resp = client.post("/api/retrieval/search", json=filtered_payload)
    assert filtered_resp.status_code == 200

    filtered_results = filtered_resp.json()["results"]
    assert len(filtered_results) == 1
    assert filtered_results[0]["vendor_name"] == "Northstar Systems"


def test_retrieval_api_unknown_session():
    """Verify searching an unknown session ID returns 404 Not Found."""
    search_payload = {
        "session_id": "sess_non_existent_12345",
        "query": "payment terms",
    }
    response = client.post("/api/retrieval/search", json=search_payload)
    assert response.status_code == 404
