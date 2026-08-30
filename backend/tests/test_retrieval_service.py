"""Unit tests for evidence retrieval service."""

import numpy as np
import pytest
from app.models import ChunkMetadata
from app.services.embedding_service import EmbeddingService
from app.services.vector_store import get_vector_store
from app.services.retrieval_service import (
    RetrievalService,
    SessionNotFoundError,
)


def test_retrieval_service_search_success():
    """Verify end-to-end retrieval search using real embedding service."""
    embedding_service = EmbeddingService()
    vector_store = get_vector_store()

    texts = [
        "Northstar Systems provides 99.9% availability SLA guarantee.",
        "Meridian Labs payment terms require 50% upfront payment.",
    ]
    chunks = [
        ChunkMetadata(
            chunk_id="v01_p001_c001",
            vendor_name="Northstar Systems",
            source_filename="northstar.pdf",
            start_page=1,
            end_page=1,
            character_count=len(texts[0]),
            text=texts[0],
        ),
        ChunkMetadata(
            chunk_id="v02_p001_c001",
            vendor_name="Meridian Labs",
            source_filename="meridian.pdf",
            start_page=1,
            end_page=1,
            character_count=len(texts[1]),
            text=texts[1],
        ),
    ]

    embeddings = embedding_service.embed_texts(texts)
    session_id = "sess_retrieval_test"
    vector_store.create_session_index(session_id, embeddings, chunks)

    service = RetrievalService(embedding_service=embedding_service)

    # Query for SLA
    response = service.search_evidence(session_id=session_id, query="uptime SLA commitment", top_k=2)

    assert response.status == "success"
    assert response.total_results >= 1
    top_result = response.results[0]
    assert top_result.vendor_name == "Northstar Systems"
    assert top_result.start_page == 1
    assert "99.9%" in top_result.text
    assert 0.0 <= top_result.similarity_score <= 1.0


def test_retrieval_service_unknown_session():
    """Verify SessionNotFoundError raised for non-existent session."""
    service = RetrievalService()
    with pytest.raises(SessionNotFoundError):
        service.search_evidence("sess_non_existent", "payment terms")


def test_retrieval_service_blank_query():
    """Verify ValueError raised for blank query."""
    service = RetrievalService()
    with pytest.raises(ValueError):
        service.search_evidence("sess_test", "   ")
