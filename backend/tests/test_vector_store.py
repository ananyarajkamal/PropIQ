"""Unit tests for FAISS vector store service."""

import numpy as np
import pytest
from app.models import ChunkMetadata
from app.services.vector_store import VectorStore


def make_dummy_chunk(chunk_id: str, vendor_name: str, text: str) -> ChunkMetadata:
    """Helper creating a dummy ChunkMetadata object."""
    return ChunkMetadata(
        chunk_id=chunk_id,
        vendor_name=vendor_name,
        source_filename=f"{vendor_name.lower()}_proposal.pdf",
        start_page=1,
        end_page=1,
        character_count=len(text),
        text=text,
    )


def test_vector_store_session_isolation():
    """Verify vector search is strictly isolated between sessions."""
    store = VectorStore()
    dim = 4
    
    # Session A
    vecs_a = np.array([[1.0, 0.0, 0.0, 0.0]], dtype=np.float32)
    chunks_a = [make_dummy_chunk("v01_p001_c001", "Vendor A", "Session A text")]
    store.create_session_index("sess_A", vecs_a, chunks_a)

    # Session B
    vecs_b = np.array([[0.0, 1.0, 0.0, 0.0]], dtype=np.float32)
    chunks_b = [make_dummy_chunk("v02_p001_c001", "Vendor B", "Session B text")]
    store.create_session_index("sess_B", vecs_b, chunks_b)

    # Search Session A
    query_a = np.array([[1.0, 0.0, 0.0, 0.0]], dtype=np.float32)
    results_a = store.search("sess_A", query_a, top_k=5)
    assert len(results_a) == 1
    assert results_a[0][0].vendor_name == "Vendor A"

    # Search Session B with same query vector
    results_b = store.search("sess_B", query_a, top_k=5)
    assert len(results_b) == 1
    assert results_b[0][0].vendor_name == "Vendor B"


def test_vector_store_vendor_filtering():
    """Verify vendor-specific search filtering."""
    store = VectorStore()
    dim = 4
    
    vecs = np.array([
        [1.0, 0.0, 0.0, 0.0],
        [0.9, 0.1, 0.0, 0.0],
    ], dtype=np.float32)

    chunks = [
        make_dummy_chunk("v01_p001_c001", "Northstar Systems", "Northstar SLA 99.9%"),
        make_dummy_chunk("v02_p001_c001", "Meridian Labs", "Meridian SLA 99.5%"),
    ]

    store.create_session_index("sess_filter", vecs, chunks)

    # Filter to Meridian Labs only
    query = np.array([[1.0, 0.0, 0.0, 0.0]], dtype=np.float32)
    results = store.search("sess_filter", query, top_k=5, vendor_name="Meridian Labs")

    assert len(results) == 1
    assert results[0][0].vendor_name == "Meridian Labs"


def test_vector_store_delete_session():
    """Verify session cleanup."""
    store = VectorStore()
    vecs = np.array([[1.0, 0.0, 0.0, 0.0]], dtype=np.float32)
    chunks = [make_dummy_chunk("c1", "V1", "text")]
    
    store.create_session_index("sess_del", vecs, chunks)
    assert store.has_session("sess_del") is True

    store.delete_session("sess_del")
    assert store.has_session("sess_del") is False
