"""FastAPI route handler for evidence retrieval search."""

from fastapi import APIRouter, HTTPException, status
from app.models import RetrievalRequestModel, RetrievalResponseModel
from app.services.retrieval_service import (
    RetrievalService,
    SessionNotFoundError,
)

router = APIRouter()


@router.post(
    "/search",
    response_model=RetrievalResponseModel,
    status_code=status.HTTP_200_OK,
    summary="Search FAISS vector store for procurement evidence chunks",
)
async def search_evidence(request: RetrievalRequestModel) -> RetrievalResponseModel:
    """Retrieve nearest evidence chunks from session FAISS vector store.

    Validates query and session ID, generates local query embedding, searches
    the session-isolated FAISS index, applies optional vendor filtering, and
    returns evidence cards with page-level citations.
    """
    retrieval_service = RetrievalService()

    try:
        response = retrieval_service.search_evidence(
            session_id=request.session_id,
            query=request.query,
            vendor_name=request.vendor_name,
            top_k=request.top_k,
        )
        return response
    except SessionNotFoundError as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(err),
        ) from err
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err),
        ) from err
