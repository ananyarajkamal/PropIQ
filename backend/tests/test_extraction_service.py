"""Unit tests for structured extraction service and citation validation."""

from typing import List, Dict, Optional
import numpy as np
import pytest
from app.models import (
    ProcurementRequirements,
    ChunkMetadata,
)
from app.services.vector_store import get_vector_store
from app.services.retrieval_service import RetrievalService
from app.services.groq_service import GroqService
from app.services.extraction_service import ExtractionService


class MockGroqService(GroqService):
    """Mock GroqService returning deterministic extraction responses."""

    def extract_category_evidence(self, vendor_name: str, category: str, evidence_pack: List[Dict], requirement_context: Optional[str] = None):
        if not evidence_pack:
            return {"status": "NOT_FOUND", "raw_value": None, "summary": "Not found.", "cited_evidence_ids": [], "notes": None}
        
        if "Pricing" in category:
            return {
                "status": "FOUND",
                "raw_value": "$180,000 annually",
                "summary": "Annual contract cost is $180,000.",
                "cited_evidence_ids": ["E1"],
                "notes": None,
            }
        elif "Warranty" in category:
            return {
                "status": "NOT_FOUND",
                "raw_value": None,
                "summary": "No warranty clause found.",
                "cited_evidence_ids": [],
                "notes": None,
            }
        elif "Hallucinated" in category:
            return {
                "status": "FOUND",
                "raw_value": "Fake value",
                "summary": "Fake summary",
                "cited_evidence_ids": ["E99"],
                "notes": None,
            }
        
    def extract_vendor_fact_sheet_batch(
        self,
        vendor_name: str,
        categories: List[str],
        evidence_pack: List[Dict],
        requirement_contexts: Optional[Dict[str, str]] = None,
    ):
        res = {}
        for cat in categories:
            res[cat] = self.extract_category_evidence(
                vendor_name, cat, evidence_pack, requirement_contexts.get(cat) if requirement_contexts else None
            )
        return res


def test_extraction_service_citation_validation():
    """Verify backend citation validation filters hallucinated evidence IDs."""
    vector_store = get_vector_store()
    
    session_id = "sess_extraction_test"
    chunks = [
        ChunkMetadata(
            chunk_id="v01_p002_c001",
            vendor_name="Northstar Systems",
            source_filename="northstar.pdf",
            start_page=2,
            end_page=2,
            character_count=50,
            text="Annual contract price for Northstar Systems is $180,000.",
        )
    ]
    vecs = np.random.randn(1, 384).astype(np.float32)
    vector_store.create_session_index(session_id, vecs, chunks)

    mock_groq = MockGroqService(api_key="gsk_mock")
    extraction_service = ExtractionService(groq_service=mock_groq)

    reqs = ProcurementRequirements(budget_ceiling=200000)
    response = extraction_service.extract_vendor_fact_sheets(session_id=session_id, requirements=reqs)

    assert response.status == "success"
    assert len(response.vendor_fact_sheets) == 1
    
    fact_sheet = response.vendor_fact_sheets[0]
    assert fact_sheet.vendor_name == "Northstar Systems"

    # Check Pricing category result
    pricing_cat = next(c for c in fact_sheet.categories if c.category == "Pricing")
    assert pricing_cat.status == "FOUND"
    assert pricing_cat.raw_value == "$180,000 annually"
    assert len(pricing_cat.evidence_citations) == 1
    
    citation = pricing_cat.evidence_citations[0]
    assert citation.evidence_id == "E1"
    assert citation.vendor_name == "Northstar Systems"
    assert citation.source_filename == "northstar.pdf"
    assert citation.start_page == 2
    assert citation.chunk_id == "v01_p002_c001"
