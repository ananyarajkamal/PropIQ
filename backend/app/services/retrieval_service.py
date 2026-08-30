"""Evidence retrieval service for PropIQ.

Orchestrates query embedding generation, FAISS vector store search,
vendor filtering, and evidence metadata mapping.
"""

from typing import List, Optional
from app.models import (
    RetrievalResultModel,
    RetrievalResponseModel,
)
from app.validators import validate_non_empty_string
from app.services.embedding_service import EmbeddingService
from app.services.vector_store import get_vector_store

DEFAULT_TOP_K = 5
MAX_TOP_K = 20


class RetrievalError(Exception):
    """Base exception for evidence retrieval failures."""
    pass


class SessionNotFoundError(RetrievalError):
    """Exception raised when requesting retrieval for an unknown or expired session."""
    pass


class RetrievalService:
    """Service handling procurement evidence search and metadata formatting."""

    def __init__(
        self,
        embedding_service: Optional[EmbeddingService] = None,
    ):
        self.embedding_service = embedding_service or EmbeddingService()
        self.vector_store = get_vector_store()

    def search_evidence(
        self,
        session_id: str,
        query: str,
        vendor_name: Optional[str] = None,
        top_k: int = DEFAULT_TOP_K,
    ) -> RetrievalResponseModel:
        """Search session vector store for relevant procurement evidence chunks.

        Args:
            session_id: Active session identifier string.
            query: Search query text string.
            vendor_name: Optional vendor name to filter evidence by vendor.
            top_k: Number of top matches to retrieve (1 to 20, default 5).

        Returns:
            Structured RetrievalResponseModel object.

        Raises:
            SessionNotFoundError: If session_id is not indexed in vector store.
            ValueError: If query is blank or top_k is invalid.
        """
        # 1. Validate query first
        clean_query = validate_non_empty_string(query, field_name="query")
        if len(clean_query) > 500:
            clean_query = clean_query[:500]

        # 2. Validate session_id
        clean_session_id = validate_non_empty_string(session_id, field_name="session_id")
        if not self.vector_store.has_session(clean_session_id):
            raise SessionNotFoundError(
                f"Analysis session '{clean_session_id}' not found or index not built."
            )

        # 3. Validate top_k
        if not isinstance(top_k, int) or top_k < 1:
            top_k = DEFAULT_TOP_K
        top_k = min(top_k, MAX_TOP_K)

        # 4. Clean vendor_name filter if provided
        clean_vendor = vendor_name.strip() if (vendor_name and vendor_name.strip()) else None

        # 5. Generate normalized query embedding
        query_vector = self.embedding_service.embed_query(clean_query)

        # 6. Execute search in vector store
        try:
            raw_matches = self.vector_store.search(
                session_id=clean_session_id,
                query_vector=query_vector,
                top_k=top_k,
                vendor_name=clean_vendor,
            )
        except KeyError as err:
            raise SessionNotFoundError(str(err)) from err

        # 7. Format results into Pydantic models with 3-decimal precision scores
        formatted_results: List[RetrievalResultModel] = []
        for rank_idx, (chunk, score) in enumerate(raw_matches, start=1):
            rounded_score = round(max(0.0, min(1.0, float(score))), 3)
            
            formatted_results.append(
                RetrievalResultModel(
                    rank=rank_idx,
                    vendor_name=chunk.vendor_name,
                    source_filename=chunk.source_filename,
                    start_page=chunk.start_page,
                    end_page=chunk.end_page,
                    chunk_id=chunk.chunk_id,
                    text=chunk.text,
                    similarity_score=rounded_score,
                )
            )

        return RetrievalResponseModel(
            status="success",
            query=clean_query,
            session_id=clean_session_id,
            vendor_filter=clean_vendor,
            total_results=len(formatted_results),
            results=formatted_results,
        )
