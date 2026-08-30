"""Test suite verifying zero Groq API calls during Requirements save, edit, and re-evaluation."""

import numpy as np
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from app.main import app
from app.api.routes.comparison import FACT_SHEETS_CACHE, COMPARISON_CACHE
from app.models import VendorFactSheet, CategoryExtractionResult, ChunkMetadata

client = TestClient(app)


def test_save_requirements_zero_groq_calls():
    """Verify POST /api/analysis/requirements succeeds with 0 Groq calls even if Groq is unconfigured or rate-limited."""
    from app.services.vector_store import get_vector_store
    vs = get_vector_store()
    sid = "test_session_requirements_zero_groq_001"
    
    dummy_chunk = ChunkMetadata(
        chunk_id="v01_p001_c001",
        vendor_name="Northstar Systems",
        source_filename="northstar.pdf",
        vendor_index=1,
        start_page=1,
        end_page=1,
        text="Sample text",
        character_count=11,
    )
    embeddings = np.array([[0.1] * 384], dtype=np.float32)
    vs.create_session_index(sid, embeddings=embeddings, chunks=[dummy_chunk])

    req_payload = {
        "session_id": sid,
        "requirements": {
            "budget_ceiling": 150000.0,
            "budget_currency": "USD",
            "budget_priority": "HIGH",
            "timeline_value": 30.0,
            "timeline_unit": "days",
            "timeline_priority": "HIGH",
            "minimum_sla": 99.9,
            "sla_priority": "MUST_HAVE",
        }
    }

    # Patch GroqService to fail if called
    with patch("app.services.groq_service.GroqService.extract_category_evidence") as mock_groq:
        mock_groq.side_effect = RuntimeError("Groq should NOT be called during requirements save!")

        response = client.post("/api/analysis/requirements", json=req_payload)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["session_id"] == sid
        assert mock_groq.call_count == 0


def test_requirements_edit_runs_local_comparison_zero_groq_calls():
    """Verify editing requirements with pre-existing fact sheets re-runs local comparison with 0 Groq calls."""
    from app.services.vector_store import get_vector_store
    vs = get_vector_store()
    sid = "test_session_requirements_edit_zero_groq_002"

    dummy_chunk = ChunkMetadata(
        chunk_id="v01_p001_c001",
        vendor_name="Northstar Systems",
        source_filename="northstar.pdf",
        vendor_index=1,
        start_page=1,
        end_page=1,
        text="Sample text",
        character_count=11,
    )
    embeddings = np.array([[0.1] * 384], dtype=np.float32)
    vs.create_session_index(sid, embeddings=embeddings, chunks=[dummy_chunk])

    # Populate FACT_SHEETS_CACHE for session to simulate pre-extracted proposal facts
    FACT_SHEETS_CACHE[sid] = [
        VendorFactSheet(
            vendor_name="Northstar Systems",
            categories=[
                CategoryExtractionResult(
                    category="Pricing",
                    status="FOUND",
                    raw_value="$120,000 USD",
                    summary="Annual cost $120,000 USD",
                    evidence_citations=[],
                ),
                CategoryExtractionResult(
                    category="Timeline",
                    status="FOUND",
                    raw_value="30 days",
                    summary="Deployment timeline 30 days",
                    evidence_citations=[],
                ),
            ]
        )
    ]

    initial_reqs = {
        "session_id": sid,
        "requirements": {
            "budget_ceiling": 150000.0,
            "budget_currency": "USD",
            "timeline_value": 30.0,
            "timeline_unit": "days",
        }
    }

    with patch("app.services.groq_service.GroqService.extract_category_evidence") as mock_groq:
        mock_groq.side_effect = RuntimeError("Groq should NOT be called during requirement comparison re-evaluation!")

        # 1. Save requirements
        save_resp = client.post("/api/analysis/requirements", json=initial_reqs)
        assert save_resp.status_code == 200

        # 2. Evaluate comparison
        comp_resp = client.post("/api/comparison/evaluate", json=initial_reqs)
        assert comp_resp.status_code == 200
        comp_data = comp_resp.json()
        assert comp_data["status"] == "success"

        # 3. Edit requirements
        edited_reqs = {
            "session_id": sid,
            "requirements": {
                "budget_ceiling": 150000.0,
                "budget_currency": "USD",
                "timeline_value": 45.0,  # Changed from 30 to 45 days
                "timeline_unit": "days",
            }
        }

        # 4. Re-evaluate comparison after edit
        edited_comp_resp = client.post("/api/comparison/evaluate", json=edited_reqs)
        assert edited_comp_resp.status_code == 200
        edited_comp_data = edited_comp_resp.json()
        assert edited_comp_data["status"] == "success"

        # Verify Groq was NEVER called!
        assert mock_groq.call_count == 0
