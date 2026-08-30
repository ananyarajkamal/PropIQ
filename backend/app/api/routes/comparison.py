"""FastAPI route handler for deterministic terminology normalization and requirement comparison."""

import time
import logging
from typing import Dict, List
from fastapi import APIRouter, HTTPException, status
from app.models import (
    ExtractionRequest,
    ComparisonResponse,
    VendorFactSheet,
)
from app.services.vector_store import get_vector_store
from app.services.retrieval_service import SessionNotFoundError
from app.services.groq_service import (
    GroqNotConfiguredError,
    GroqTimeoutError,
    GroqRateLimitError,
    GroqError,
)
from app.services.extraction_service import ExtractionService
from app.services.comparison_service import ComparisonService

logger = logging.getLogger("propiq_backend")

router = APIRouter()

# In-memory cache storing session vendor fact sheets.
# Populated by POST /prepare (explicit extraction step).
# Comparison /evaluate only uses this cache — never triggers Groq itself.
FACT_SHEETS_CACHE: Dict[str, List[VendorFactSheet]] = {}
COMPARISON_CACHE: Dict[str, ComparisonResponse] = {}


def clear_fact_sheets_cache(session_id: str):
    """Clear cached fact sheets and comparison for a session if proposals change."""
    if session_id in FACT_SHEETS_CACHE:
        del FACT_SHEETS_CACHE[session_id]
    if session_id in COMPARISON_CACHE:
        del COMPARISON_CACHE[session_id]


@router.post(
    "/prepare",
    status_code=status.HTTP_200_OK,
    summary="Extract and cache vendor fact sheets for comparison (Groq extraction step)",
)
async def prepare_vendor_facts(request: ExtractionRequest):
    """Explicitly extract vendor fact sheets from proposal evidence and cache them.

    This is the only endpoint that calls Groq. Must be called once before /evaluate.
    Subsequent /evaluate calls with the same session will use the cache (0 Groq calls).
    """
    t_start = time.time()
    logger.info("comparison.start: Preparing vendor fact extraction for session '%s'", request.session_id)

    vector_store = get_vector_store()
    if not vector_store.has_session(request.session_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analysis session '{request.session_id}' not found or index not built.",
        )
    logger.info("comparison.session_loaded: Session '%s' loaded from vector store in %.3fs", request.session_id, time.time() - t_start)

    # Check cache first - only reuse if valid fact sheets with extracted facts exist
    if request.session_id in FACT_SHEETS_CACHE:
        fact_sheets = FACT_SHEETS_CACHE[request.session_id]
        has_valid_facts = any(
            any(cat.status in {"FOUND", "UNCLEAR", "CONFLICTING"} for cat in fs.categories)
            for fs in fact_sheets
        ) if fact_sheets else False

        if has_valid_facts:
            logger.info(
                "comparison.facts_loaded: Reusing %d cached fact sheets for session '%s' (0 Groq calls, %.3fs)",
                len(fact_sheets),
                request.session_id,
                time.time() - t_start,
            )
            return {
                "status": "ready",
                "session_id": request.session_id,
                "vendors_cached": len(fact_sheets),
                "vendor_names": [fs.vendor_name for fs in fact_sheets],
            }
        else:
            # Invalidate stale/empty cache entry so fresh extraction runs
            del FACT_SHEETS_CACHE[request.session_id]

    extraction_service = ExtractionService()
    try:
        t_ext = time.time()
        extract_resp = extraction_service.extract_vendor_fact_sheets(
            session_id=request.session_id,
            requirements=request.requirements,
            vendor_name_filter=request.vendor_name,
        )
        fact_sheets = extract_resp.vendor_fact_sheets
        FACT_SHEETS_CACHE[request.session_id] = fact_sheets
        logger.info(
            "comparison.facts_loaded: Extracted and cached %d vendor fact sheets in %.2fs",
            len(fact_sheets),
            time.time() - t_ext,
        )
    except SessionNotFoundError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err)) from err
    except GroqNotConfiguredError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Proposal analysis is not configured on this server.",
        ) from err
    except GroqTimeoutError as err:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Proposal analysis timed out. Please try again.",
        ) from err
    except GroqRateLimitError as err:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Vendor analysis is temporarily rate limited. Please wait a moment and try again.",
        ) from err
    except GroqError as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Vendor analysis error: {str(err)}",
        ) from err

    logger.info("comparison.response_ready: Total preparation time for session '%s': %.2fs", request.session_id, time.time() - t_start)

    return {
        "status": "ready",
        "session_id": request.session_id,
        "vendors_cached": len(fact_sheets),
        "vendor_names": [fs.vendor_name for fs in fact_sheets],
    }


@router.post(
    "/evaluate",
    response_model=ComparisonResponse,
    status_code=status.HTTP_200_OK,
    summary="Evaluate deterministic requirement comparison matrix (0 Groq calls)",
)
async def evaluate_requirement_comparison(request: ExtractionRequest) -> ComparisonResponse:
    """Execute deterministic Python requirement comparison rules against cached vendor facts.

    Requires vendor facts to be pre-cached via POST /prepare.
    Makes ZERO Groq calls — purely deterministic Python normalization and evaluation.
    """
    t_start = time.time()
    logger.info("comparison.start: Evaluating comparison matrix for session '%s'", request.session_id)

    vector_store = get_vector_store()
    if not vector_store.has_session(request.session_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analysis session '{request.session_id}' not found or index not built.",
        )
    logger.info("comparison.session_loaded: Session '%s' loaded in %.3fs", request.session_id, time.time() - t_start)

    # Require pre-cached facts — never trigger Groq inline from comparison
    if request.session_id not in FACT_SHEETS_CACHE:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "FACTS_NOT_READY: Vendor analysis has not been run yet for this session. "
                "Please run vendor analysis first before comparing."
            ),
        )

    fact_sheets = FACT_SHEETS_CACHE[request.session_id]
    logger.info("comparison.facts_loaded: Loaded %d cached fact sheets in %.3fs", len(fact_sheets), time.time() - t_start)

    # Execute deterministic Python comparison — zero additional Groq calls
    t_eval = time.time()
    comparison_service = ComparisonService()
    logger.info("comparison.normalization_complete: Normalization rules initialized in %.3fs", time.time() - t_eval)

    comparison_response = comparison_service.evaluate_session_comparison(
        session_id=request.session_id,
        requirements=request.requirements,
        fact_sheets=fact_sheets,
    )
    logger.info("comparison.evaluation_complete: Python matrix evaluation completed in %.3fs", time.time() - t_eval)

    import hashlib
    import json
    comp_raw = json.dumps([r.model_dump() for r in comparison_response.matrix_rows], sort_keys=True, default=str)
    comp_fp = hashlib.sha256(comp_raw.encode("utf-8")).hexdigest()[:12]

    from app.services.session_state_service import get_session_state_service
    from app.models import ModuleStatus
    state_service = get_session_state_service()
    state_service.set_module_status(request.session_id, "comparison", ModuleStatus.COMPLETED, fingerprint=comp_fp)

    COMPARISON_CACHE[request.session_id] = comparison_response
    logger.info("comparison.response_ready: Total evaluation response prepared in %.3fs", time.time() - t_start)

    return comparison_response
