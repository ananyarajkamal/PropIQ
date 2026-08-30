"""FastAPI route handler for proposal uploading, validation, parsing, chunking, embedding, and FAISS indexing."""

import json
from typing import List, Union
from fastapi import APIRouter, File, Form, UploadFile, Request, HTTPException, status

from app.config import Config
from app.validators import (
    validate_vendor_name,
    sanitize_filename,
    validate_pdf_magic_header,
    generate_secure_session_id,
)
from app.models import (
    ProposalProcessingResponse,
    ProposalProcessSummary,
    ChunkMetadata,
)
from app.services.pdf_parser import (
    parse_pdf_bytes,
    PasswordProtectedPDFError,
    CorruptedPDFError,
    ScannedPDFError,
    PageLimitExceededError,
    TextLimitExceededError,
)
from app.services.chunker import chunk_document_pages
from app.services.embedding_service import EmbeddingService
from app.services.vector_store import get_vector_store
from app.services.rate_limiter import get_rate_limiter
from app.api.routes.comparison import clear_fact_sheets_cache
from app.api.routes.risks import clear_risk_cache
from app.api.routes.clarifications import clear_clarification_cache
from app.api.routes.scoring import clear_scoring_cache
from app.api.routes.recommendation import clear_recommendation_cache

router = APIRouter()


def parse_vendor_names_input(raw_vendor_names: Union[List[str], str]) -> List[str]:
    """Parse vendor names from form input whether passed as repeated fields or JSON string."""
    if isinstance(raw_vendor_names, str):
        trimmed = raw_vendor_names.strip()
        if trimmed.startswith("[") and trimmed.endswith("]"):
            try:
                parsed = json.loads(trimmed)
                if isinstance(parsed, list):
                    return [str(v) for v in parsed]
            except Exception:
                pass
        return [v.strip() for v in trimmed.split(",") if v.strip()]
    elif isinstance(raw_vendor_names, list):
        if len(raw_vendor_names) == 1 and raw_vendor_names[0].strip().startswith("["):
            return parse_vendor_names_input(raw_vendor_names[0])
        return [str(v) for v in raw_vendor_names]
    return []


@router.post(
    "/process",
    response_model=ProposalProcessingResponse,
    status_code=status.HTTP_200_OK,
    summary="Validate, parse, chunk, embed, and index proposal PDFs",
)
async def process_proposals(
    request: Request,
    files: List[UploadFile] = File(..., description="2 to 5 vendor proposal PDF files"),
    vendor_names: List[str] = Form(..., description="Corresponding vendor names for each PDF"),
) -> ProposalProcessingResponse:
    """Validate, parse, chunk, embed, and index 2 to 5 vendor proposal PDFs.

    Validates file format, PDF magic header, size limit (20MB), file count (2-5),
    vendor uniqueness, PyMuPDF page/text limits, text chunking, local sentence-transformers
    embeddings generation, and session FAISS index creation.
    """
    # Pre-Session Abuse-Control: Rate limit per client IP before session creation (Section 2)
    client_ip = request.client.host if (request.client and request.client.host) else "127.0.0.1"
    rate_limiter = get_rate_limiter()
    rate_limiter.check_rate_limit(session_id=f"ip_{client_ip}", endpoint_key="proposals_process")

    # Parse vendor names flexibly
    clean_vendor_inputs = parse_vendor_names_input(vendor_names)

    # 1. Validate total proposal file count
    file_count = len(files)
    if file_count < Config.MIN_PROPOSALS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Upload at least {Config.MIN_PROPOSALS} proposals.",
        )
    if file_count > Config.MAX_PROPOSALS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"A maximum of {Config.MAX_PROPOSALS} proposals is supported.",
        )

    # 2. Validate matching vendor names count
    if len(clean_vendor_inputs) != file_count:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The number of vendor names must match the number of uploaded PDF files.",
        )

    # 3. Validate individual vendor names & uniqueness
    validated_vendor_names: List[str] = []
    seen_vendor_names_lower = set()

    for idx, raw_name in enumerate(clean_vendor_inputs):
        try:
            valid_name = validate_vendor_name(raw_name)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid vendor name at position {idx + 1}: {str(exc)}",
            ) from exc

        name_lower = valid_name.lower()
        if name_lower in seen_vendor_names_lower:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Vendor names must be unique across all uploaded proposals. Duplicate detected: '{valid_name}'.",
            )
        seen_vendor_names_lower.add(name_lower)
        validated_vendor_names.append(valid_name)

    # 4. Process each uploaded PDF file
    summaries: List[ProposalProcessSummary] = []
    all_session_chunks: List[ChunkMetadata] = []
    total_chunks_count = 0

    for idx, file in enumerate(files):
        vname = validated_vendor_names[idx]
        safe_filename = sanitize_filename(file.filename or f"proposal_{idx+1}.pdf")

        if not safe_filename.lower().endswith(".pdf"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File '{file.filename}' is invalid. Only PDF files are supported.",
            )

        file_bytes = await file.read()
        file_size_bytes = len(file_bytes)

        if file_size_bytes > Config.MAX_FILE_SIZE_BYTES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File '{safe_filename}' exceeds maximum allowed size of {Config.MAX_FILE_SIZE_BYTES // (1024*1024)}MB.",
            )

        try:
            validate_pdf_magic_header(file_bytes)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File '{safe_filename}' is not a valid PDF document (magic header check failed).",
            ) from exc

        try:
            pages_extracted, total_chars, page_count = parse_pdf_bytes(
                pdf_bytes=file_bytes,
                filename=safe_filename,
            )
        except (PasswordProtectedPDFError, CorruptedPDFError, ScannedPDFError, PageLimitExceededError, TextLimitExceededError) as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(exc),
            ) from exc
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to extract text from '{safe_filename}': {str(exc)}",
            ) from exc

        chunks = chunk_document_pages(
            vendor_name=vname,
            source_filename=safe_filename,
            vendor_index=idx + 1,
            pages=pages_extracted,
        )

        chunk_count = len(chunks)
        total_chunks_count += chunk_count
        all_session_chunks.extend(chunks)

        summaries.append(
            ProposalProcessSummary(
                vendor_name=vname,
                filename=safe_filename,
                file_size_bytes=file_size_bytes,
                page_count=page_count,
                character_count=total_chars,
                chunk_count=chunk_count,
                status="Ready for Analysis",
                warnings=[],
            )
        )

    # 5. Generate local embeddings and build session FAISS vector index using high-entropy session ID
    session_id = generate_secure_session_id()
    embedding_service = EmbeddingService()

    try:
        chunk_texts = [c.text for c in all_session_chunks]
        embeddings = embedding_service.embed_texts(chunk_texts)

        vector_store = get_vector_store()
        vector_store.create_session_index(
            session_id=session_id,
            embeddings=embeddings,
            chunks=all_session_chunks,
        )
        from app.services.session_state_service import get_session_state_service
        state_service = get_session_state_service()
        state_service.on_proposals_changed(session_id, proposal_fp=f"prop_{session_id}_{len(summaries)}")

        clear_fact_sheets_cache(session_id)
        clear_risk_cache(session_id)
        clear_clarification_cache(session_id)
        clear_scoring_cache(session_id)
        clear_recommendation_cache(session_id)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to build vector search index: {str(exc)}",
        ) from exc

    return ProposalProcessingResponse(
        status="success",
        session_id=session_id,
        message="Proposals successfully parsed, chunked, embedded, and indexed in FAISS.",
        proposals=summaries,
        total_proposals=len(summaries),
        total_chunks=total_chunks_count,
    )


@router.get(
    "/session/{session_id}",
    summary="Get current analysis session summary metadata for hydration",
)
async def get_session_summary(session_id: str):
    """Retrieve session metadata for frontend hydration without re-parsing PDFs."""
    vector_store = get_vector_store()
    if not vector_store.has_session(session_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis session expired or not found. Please start a new analysis.",
        )

    session_data = vector_store._sessions.get(session_id)
    if not session_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session data unreadable.",
        )

    # Group chunks by vendor to build proposal summaries
    vendor_map = {}
    for chunk in session_data.chunks:
        key = (chunk.vendor_name, chunk.source_filename)
        if key not in vendor_map:
            vendor_map[key] = {
                "vendor_name": chunk.vendor_name,
                "filename": chunk.source_filename,
                "chunk_count": 0,
                "max_page": 1,
            }
        vendor_map[key]["chunk_count"] += 1
        if chunk.end_page > vendor_map[key]["max_page"]:
            vendor_map[key]["max_page"] = chunk.end_page

    summaries = []
    for (vname, fname), info in vendor_map.items():
        summaries.append({
            "vendor_name": vname,
            "filename": fname,
            "file_size_bytes": 0,
            "page_count": info["max_page"],
            "character_count": 0,
            "chunk_count": info["chunk_count"],
            "status": "Ready for Analysis",
            "warnings": [],
        })

    return {
        "status": "success",
        "session_id": session_id,
        "proposals": summaries,
        "total_proposals": len(summaries),
        "total_chunks": len(session_data.chunks),
    }
