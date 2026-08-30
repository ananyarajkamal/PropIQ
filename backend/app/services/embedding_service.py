"""Local sentence-transformers embedding service for PropIQ.

Generates 100% local text embeddings using sentence-transformers (all-MiniLM-L6-v2)
with L2 unit normalization for cosine similarity search.
"""

import logging
from typing import List, Optional
import numpy as np
from sentence_transformers import SentenceTransformer
from app.config import Config

logger = logging.getLogger("propiq_backend")

# Global singleton instance for model reuse
_EMBEDDING_MODEL_INSTANCE: Optional[SentenceTransformer] = None
DEFAULT_MODEL_NAME = "all-MiniLM-L6-v2"


def get_embedding_model(model_name: str = DEFAULT_MODEL_NAME) -> SentenceTransformer:
    """Retrieve or initialize the singleton SentenceTransformer embedding model."""
    global _EMBEDDING_MODEL_INSTANCE
    if _EMBEDDING_MODEL_INSTANCE is None:
        logger.info("Initializing local embedding model '%s'...", model_name)
        try:
            _EMBEDDING_MODEL_INSTANCE = SentenceTransformer(model_name)
            logger.info("Embedding model '%s' initialized successfully.", model_name)
        except Exception as exc:
            logger.error("Failed to initialize embedding model '%s': %s", model_name, str(exc))
            raise RuntimeError(f"Embedding model initialization failed: {str(exc)}") from exc

    return _EMBEDDING_MODEL_INSTANCE


def get_embedding_service() -> "EmbeddingService":
    """Factory function retrieving singleton EmbeddingService instance."""
    return EmbeddingService()


class EmbeddingService:
    """Service providing local text embedding generation and vector normalization."""

    def __init__(self, model_name: str = DEFAULT_MODEL_NAME):
        self.model_name = model_name

    def get_model(self) -> SentenceTransformer:
        """Get loaded model instance."""
        return get_embedding_model(self.model_name)

    def get_dimension(self) -> int:
        """Query actual embedding vector dimension from the loaded model."""
        model = self.get_model()
        dim = model.get_sentence_embedding_dimension()
        return int(dim) if dim is not None else 384

    def normalize_vectors(self, vectors: np.ndarray) -> np.ndarray:
        """L2-normalize float32 vectors for inner-product cosine similarity."""
        if vectors.size == 0:
            return vectors.astype(np.float32)

        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        norms = np.maximum(norms, 1e-12)  # Avoid division by zero
        normalized = vectors / norms
        return normalized.astype(np.float32)

    def embed_texts(self, texts: List[str], batch_size: int = 32) -> np.ndarray:
        """Generate normalized embeddings for a list of chunk text strings."""
        if not texts:
            dim = self.get_dimension()
            return np.empty((0, dim), dtype=np.float32)

        clean_texts = [t if (isinstance(t, str) and t.strip()) else "empty chunk" for t in texts]

        model = self.get_model()
        raw_embeddings = model.encode(
            clean_texts,
            batch_size=batch_size,
            show_progress_bar=False,
            convert_to_numpy=True,
        )

        return self.normalize_vectors(raw_embeddings)

    def embed_query(self, query_str: str) -> np.ndarray:
        """Generate normalized embedding for a single search query string."""
        clean_query = query_str.strip() if (isinstance(query_str, str) and query_str.strip()) else "query"
        model = self.get_model()
        raw_embedding = model.encode([clean_query], show_progress_bar=False, convert_to_numpy=True)
        return self.normalize_vectors(raw_embedding)

    def embed_text(self, text: str) -> List[float]:
        """Generate 1D list float embedding for a single text string."""
        arr = self.embed_query(text)
        return arr[0].tolist()

    def cosine_similarity(self, emb1: List[float], emb2: List[float]) -> float:
        """Calculate cosine similarity between two normalized 1D float vectors."""
        v1 = np.array(emb1, dtype=np.float32)
        v2 = np.array(emb2, dtype=np.float32)
        return float(np.dot(v1, v2))

