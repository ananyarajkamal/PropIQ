"""FastAPI route handler for procurement requirements and structured evidence extraction."""

from fastapi import APIRouter, HTTPException, status
from app.validators import validate_session_id
from app.models import (
    ProcurementRequirements,
    ExtractionRequest,
    ExtractionResponse,
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
from app.services.rate_limiter import get_rate_limiter, get_operation_lock
from app.api.routes.comparison import COMPARISON_CACHE
from app.api.routes.clarifications import clear_clarification_cache
from app.api.routes.scoring import clear_scoring_cache
from app.api.routes.recommendation import clear_recommendation_cache

router = APIRouter()


def has_at_least_one_requirement(reqs: ProcurementRequirements) -> bool:
    """Check if at least one procurement requirement is non-empty."""
    if reqs.budget_ceiling is not None:
        return True
    if reqs.timeline_value is not None:
        return True
    if reqs.minimum_sla is not None:
        return True
    if reqs.payment_terms and reqs.payment_terms.strip():
        return True
    if reqs.certifications and any(c.strip() for c in reqs.certifications):
        return True
    if reqs.warranty_value is not None:
        return True
    if reqs.liability_requirement and reqs.liability_requirement.strip():
        return True
    if reqs.renewal_preference and reqs.renewal_preference.strip():
        return True
    if reqs.termination_requirement and reqs.termination_requirement.strip():
        return True
    if reqs.support_requirement and reqs.support_requirement.strip():
        return True
    if reqs.custom_requirements and any(c.strip() for c in reqs.custom_requirements):
        return True
    return False


from app.api.routes.comparison import COMPARISON_CACHE

@router.post(
    "/requirements",
    status_code=status.HTTP_200_OK,
    summary="Save procurement evaluation requirements for active session",
)
async def save_requirements(request: ExtractionRequest):
    """Validate and save procurement evaluation requirements for session."""
    try:
        sid = validate_session_id(request.session_id)
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err),
        ) from err

    vector_store = get_vector_store()
    if not vector_store.has_session(sid):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analysis session '{sid}' not found or index not built.",
        )

    if not has_at_least_one_requirement(request.requirements):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please specify at least one procurement evaluation requirement.",
        )

    # Derive requirement fingerprint
    import hashlib
    import json
    reqs_raw = json.dumps(request.requirements.model_dump(), sort_keys=True, default=str)
    reqs_fp = hashlib.sha256(reqs_raw.encode("utf-8")).hexdigest()[:12]

    from app.services.session_state_service import get_session_state_service
    state_service = get_session_state_service()
    state_service.on_requirements_changed(sid, reqs_fp)

    # Invalidate cached comparison, scoring, and recommendation state for session so new requirements trigger fresh local evaluation
    if sid in COMPARISON_CACHE:
        del COMPARISON_CACHE[sid]
    clear_clarification_cache(sid)
    clear_scoring_cache(sid)
    clear_recommendation_cache(sid)

    return {
        "status": "success",
        "session_id": sid,
        "message": "Procurement requirements saved successfully.",
    }


@router.post(
    "/extract",
    response_model=ExtractionResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute evidence-grounded structured extraction for session vendor proposals",
)
async def extract_vendor_facts(request: ExtractionRequest) -> ExtractionResponse:
    """Execute category-specific targeted retrieval, Evidence Pack creation, Groq extraction, and citation validation."""
    try:
        sid = validate_session_id(request.session_id)
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err),
        ) from err

    # Rate limiting & operation lock
    rate_limiter = get_rate_limiter()
    rate_limiter.check_rate_limit(sid, "analysis_extract")

    op_lock = get_operation_lock()
    lock_key = op_lock.acquire_lock(sid, "analysis_extract")

    try:
        vector_store = get_vector_store()
        if not vector_store.has_session(sid):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Analysis session '{sid}' not found or index not built.",
            )

        if not has_at_least_one_requirement(request.requirements):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Please specify at least one procurement requirement before analyzing vendor details.",
            )

        extraction_service = ExtractionService()

        try:
            response = extraction_service.extract_vendor_fact_sheets(
                session_id=sid,
                requirements=request.requirements,
                vendor_name_filter=request.vendor_name,
            )
            return response
        except SessionNotFoundError as err:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(err),
            ) from err
        except GroqNotConfiguredError as err:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="AI analysis is not configured on this server.",
            ) from err
        except GroqTimeoutError as err:
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="AI analysis timed out. Please try again.",
            ) from err
        except GroqRateLimitError as err:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="AI analysis is temporarily rate limited. Please try again shortly.",
            ) from err
        except GroqError as err:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Vendor extraction error: {str(err)}",
            ) from err
    finally:
        op_lock.release_lock(lock_key)


@router.get(
    "/workflow-state/{session_id}",
    summary="Get authoritative workflow states and module execution statuses for active session",
)
async def get_workflow_state(session_id: str):
    """Retrieve explicit session module execution statuses and version fingerprints."""
    try:
        sid = validate_session_id(session_id)
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err),
        ) from err

    from app.services.session_state_service import get_session_state_service
    state_service = get_session_state_service()
    return state_service.get_session_workflow_state(sid)
