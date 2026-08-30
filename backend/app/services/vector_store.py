"""FAISS vector store service for PropIQ.

Manages in-memory FAISS IndexFlatIP vector indexes isolated by analysis session,
preserving evidence metadata and supporting vendor-specific filtering and session TTL pruning.
"""

import time
import logging
from typing import Dict, List, Optional, Tuple
import numpy as np
import faiss
from app.config import Config
from app.models import ChunkMetadata

logger = logging.getLogger("propiq_backend")


class SessionIndexData:
    """Container holding FAISS index and associated evidence metadata for a single session."""

    def __init__(self, dimension: int, chunks: List[ChunkMetadata], index: faiss.IndexFlatIP):
        self.dimension = dimension
        self.chunks = chunks
        self.index = index
        self.created_at = time.time()


class VectorStore:
    """Service for managing session-isolated FAISS vector indexes."""

    def __init__(self):
        self._sessions: Dict[str, SessionIndexData] = {}

    def create_session_index(
        self,
        session_id: str,
        embeddings: np.ndarray,
        chunks: List[ChunkMetadata],
    ) -> None:
        """Create and populate a session-isolated FAISS index.

        Args:
            session_id: Unique session identifier string.
            embeddings: Float32 numpy array of normalized vector embeddings (N, D).
            chunks: Matching list of ChunkMetadata items (length N).

        Raises:
            ValueError: If vector count does not match chunk count or embeddings are empty.
        """
        if not session_id or not session_id.strip():
            raise ValueError("session_id cannot be empty.")

        # Prune expired sessions prior to creating new index
        self.prune_expired_sessions()

        vector_count, dimension = embeddings.shape
        if vector_count != len(chunks):
            raise ValueError(
                f"Embedding vector count ({vector_count}) does not match chunk count ({len(chunks)})."
            )

        if vector_count == 0:
            raise ValueError("Cannot create FAISS index with 0 vectors.")

        # Ensure float32 contiguous array
        vecs_f32 = np.ascontiguousarray(embeddings, dtype=np.float32)

        # Create FAISS IndexFlatIP (Inner Product for normalized vectors = Cosine Similarity)
        index = faiss.IndexFlatIP(dimension)
        index.add(vecs_f32)

        # Store session container
        self._sessions[session_id] = SessionIndexData(
            dimension=dimension,
            chunks=list(chunks),
            index=index,
        )

        logger.info(
            "Created FAISS vector index for session '%s' (%d vectors, %d dimensions).",
            session_id,
            vector_count,
            dimension,
        )

    def has_session(self, session_id: str) -> bool:
        """Check if an active vector index exists for a session.

        Args:
            session_id: Session identifier string.

        Returns:
            True if session index exists and is not expired, False otherwise.
        """
        self.prune_expired_sessions()
        return session_id in self._sessions

    def get_session_chunk_count(self, session_id: str) -> int:
        """Get total indexed chunk count for a session."""
        if not self.has_session(session_id):
            return 0
        return len(self._sessions[session_id].chunks)

    def get_session_vendors(self, session_id: str) -> List[str]:
        """Get unique list of vendor names indexed in a session.

        Args:
            session_id: Session identifier string.

        Returns:
            List of distinct vendor name strings.
        """
        if not self.has_session(session_id):
            return []
        chunks = self._sessions[session_id].chunks
        vendors = []
        seen = set()
        for c in chunks:
            v = c.vendor_name.strip()
            if v and v not in seen:
                seen.add(v)
                vendors.append(v)
        return vendors

    def search(
        self,
        session_id: str,
        query_vector: np.ndarray,
        top_k: int = 5,
        vendor_name: Optional[str] = None,
    ) -> List[Tuple[ChunkMetadata, float]]:
        """Search the session-isolated FAISS index for nearest evidence chunks.

        Args:
            session_id: Target session identifier.
            query_vector: L2-normalized query embedding (1, D).
            top_k: Maximum number of results to return (default 5).
            vendor_name: Optional vendor name to filter results by vendor.

        Returns:
            List of (ChunkMetadata, similarity_score) tuples.

        Raises:
            KeyError: If session_id does not exist in vector store.
        """
        if not self.has_session(session_id):
            raise KeyError(f"Session '{session_id}' not found in vector store.")

        session_data = self._sessions[session_id]
        total_chunks = len(session_data.chunks)
        if total_chunks == 0:
            return []

        # Request more candidates if filtering by vendor name
        fetch_k = min(total_chunks, max(top_k * 5, 20))
        query_f32 = np.ascontiguousarray(query_vector, dtype=np.float32)

        scores, indices = session_data.index.search(query_f32, fetch_k)

        matched_results: List[Tuple[ChunkMetadata, float]] = []
        clean_target_vendor = vendor_name.strip().lower() if (vendor_name and vendor_name.strip()) else None

        for score, idx in zip(scores[0], indices[0]):
            if idx < 0 or idx >= total_chunks:
                continue

            chunk = session_data.chunks[idx]

            # Apply strict vendor filtering (Vendor Isolation)
            if clean_target_vendor and chunk.vendor_name.strip().lower() != clean_target_vendor:
                continue

            matched_results.append((chunk, float(score)))

            if len(matched_results) >= top_k:
                break

        return matched_results

    def prune_expired_sessions(self, ttl_minutes: int = Config.SESSION_TTL_MINUTES) -> int:
        """Prune sessions older than TTL.

        Args:
            ttl_minutes: Session lifetime in minutes.

        Returns:
            Count of expired sessions removed.
        """
        now = time.time()
        max_age_seconds = ttl_minutes * 60.0
        expired_sids = [
            sid for sid, data in self._sessions.items()
            if (now - data.created_at) > max_age_seconds
        ]
        for sid in expired_sids:
            del self._sessions[sid]
            logger.info("Pruned expired session '%s' (TTL %d mins).", sid, ttl_minutes)
        return len(expired_sids)

    def delete_session(self, session_id: str) -> bool:
        """Remove and clean vector index for a session.

        Args:
            session_id: Session identifier string.

        Returns:
            True if session was removed, False if it was not found.
        """
        if session_id in self._sessions:
            del self._sessions[session_id]
            logger.info("Deleted vector index for session '%s'.", session_id)
            return True
        return False

    def clear_all_sessions(self) -> None:
        """Clear all active session vector indexes."""
        self._sessions.clear()


# Global singleton instance for vector store management
_GLOBAL_VECTOR_STORE = VectorStore()


def get_vector_store() -> VectorStore:
    """Retrieve global VectorStore instance."""
    return _GLOBAL_VECTOR_STORE
