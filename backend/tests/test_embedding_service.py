"""Unit tests for local sentence-transformers embedding service."""

import numpy as np
import pytest
from app.services.embedding_service import EmbeddingService


def test_embedding_service_dimension():
    """Verify embedding service dimension query."""
    service = EmbeddingService()
    dim = service.get_dimension()
    assert dim == 384


def test_embedding_service_embed_texts():
    """Verify batch embedding generation and L2 normalization."""
    service = EmbeddingService()
    texts = [
        "Northstar Systems payment terms are Net 30 days.",
        "Meridian Labs implementation timeline is 6 weeks.",
    ]

    embeddings = service.embed_texts(texts)

    assert isinstance(embeddings, np.ndarray)
    assert embeddings.shape == (2, 384)
    assert embeddings.dtype == np.float32

    # Check L2 unit normalization (norm should be ~1.0)
    norms = np.linalg.norm(embeddings, axis=1)
    assert np.allclose(norms, 1.0, atol=1e-4)


def test_embedding_service_embed_query():
    """Verify single query embedding generation."""
    service = EmbeddingService()
    query_vector = service.embed_query("uptime SLA commitment")

    assert query_vector.shape == (1, 384)
    norm = np.linalg.norm(query_vector)
    assert np.isclose(norm, 1.0, atol=1e-4)


def test_embedding_service_empty_texts():
    """Verify handling of empty or blank text lists."""
    service = EmbeddingService()
    embeddings = service.embed_texts(["  ", ""])
    assert embeddings.shape == (2, 384)
