"""FastAPI route handler for procurement vendor clarification question generation."""

from typing import Dict, List, Optional
from fastapi import APIRouter, HTTPException, status
from app.config import Config
from app.validators import validate_session_id
from app.models import (
    ClarificationRequestModel,
    ClarificationResponseModel,
    ClarificationQuestionModel,
    QuestionPriority,
    ClarificationReason,
    VendorFactSheet,
    ComparisonMatrixRow,
    RiskFindingModel,
    ContradictionFindingModel,
)
from app.services.vector_store import get_vector_store
from app.services.clarification_service import ClarificationService
from app.services.rate_limiter import get_rate_limiter, get_operation_lock
from app.api.routes.comparison import FACT_SHEETS_CACHE, COMPARISON_CACHE
from app.api.routes.risks import RISK_ANALYSIS_CACHE

router = APIRouter()

# In-memory cache for session clarification responses
CLARIFICATION_CACHE: Dict[str, ClarificationResponseModel] = {}


def clear_clarification_cache(session_id: str):
    """Clear cached clarification questions if proposal session changes."""
    if session_id in CLARIFICATION_CACHE:
        del CLARIFICATION_CACHE[session_id]


@router.post(
    "/generate",
    response_model=ClarificationResponseModel,
    status_code=status.HTTP_200_OK,
    summary="Generate vendor clarification questions from analysis gaps",
)
async def generate_vendor_clarifications(request: ClarificationRequestModel) -> ClarificationResponseModel:
    """Generate evidence and requirement-linked vendor clarification questions with trusted server state retrieval (Rule 2)."""
    try:
        sid = validate_session_id(request.session_id)
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err),
        ) from err

    # Rate limiting & operation lock
    rate_limiter = get_rate_limiter()
    rate_limiter.check_rate_limit(sid, "clarifications_generate")

    op_lock = get_operation_lock()
    lock_key = op_lock.acquire_lock(sid, "clarifications_generate")

    try:
        vector_store = get_vector_store()
        if not vector_store.has_session(sid):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Analysis session '{sid}' not found or index not built.",
            )

        # Prerequisite check: Clarifications requires Comparison and Risks & Contradictions to be COMPLETED
        from app.services.session_state_service import get_session_state_service
        from app.models import ModuleStatus
        state_service = get_session_state_service()

        comp_st = state_service.get_module_status(sid, "comparison")
        risk_st = state_service.get_module_status(sid, "risks_contradictions")

        if comp_st != ModuleStatus.COMPLETED or risk_st != ModuleStatus.COMPLETED:
            missing = []
            if comp_st != ModuleStatus.COMPLETED:
                missing.append(f"comparison ({comp_st.value})")
            if risk_st != ModuleStatus.COMPLETED:
                missing.append(f"risks_contradictions ({risk_st.value})")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Clarification generation is blocked until required upstream analyses are complete. Incomplete: {', '.join(missing)}.",
            )

        # Cache check: Re-evaluations on requirement edits reuse session analysis facts
        if sid in CLARIFICATION_CACHE and not request.vendor_name:
            cached_resp = CLARIFICATION_CACHE[sid]
            return cached_resp

        # Rule 2: Retrieve trusted session analysis artifacts server-side using session_id
        fact_sheets: Optional[List[VendorFactSheet]] = FACT_SHEETS_CACHE.get(sid)

        comp_resp = COMPARISON_CACHE.get(sid)
        matrix_rows: Optional[List[ComparisonMatrixRow]] = comp_resp.matrix_rows if comp_resp else None

        risk_resp = RISK_ANALYSIS_CACHE.get(sid)
        risk_findings: Optional[List[RiskFindingModel]] = risk_resp.risk_findings if risk_resp else None
        contradictions: Optional[List[ContradictionFindingModel]] = risk_resp.contradiction_findings if risk_resp else None

        reqs = request.requirements or (comp_resp.requirements if comp_resp else None)

        # Execute Clarification Service
        clarification_service = ClarificationService()
        questions = clarification_service.generate_session_clarifications(
            session_id=sid,
            fact_sheets=fact_sheets,
            matrix_rows=matrix_rows,
            risk_findings=risk_findings,
            contradictions=contradictions,
            requirements=reqs,
            vendor_name_filter=request.vendor_name,
        )

        # Calculate Summary Counts
        high_count = sum(1 for q in questions if q.priority == QuestionPriority.HIGH)
        med_count = sum(1 for q in questions if q.priority == QuestionPriority.MEDIUM)
        low_count = sum(1 for q in questions if q.priority == QuestionPriority.LOW)
        conf_count = sum(1 for q in questions if q.reason == ClarificationReason.CONFLICTING_INFORMATION)

        vendor_counts: Dict[str, int] = {}
        for q in questions:
            vendor_counts[q.vendor_name] = vendor_counts.get(q.vendor_name, 0) + 1

        response = ClarificationResponseModel(
            status="success",
            session_id=sid,
            questions=questions,
            total_questions=len(questions),
            high_priority_count=high_count,
            medium_priority_count=med_count,
            low_priority_count=low_count,
            conflicting_details_count=conf_count,
            vendor_question_counts=vendor_counts,
            privacy_notice=Config.PRIVACY_NOTICE,
        )

        import hashlib
        import json
        q_raw = json.dumps([q.model_dump() for q in questions], sort_keys=True, default=str)
        q_fp = hashlib.sha256(q_raw.encode("utf-8")).hexdigest()[:12]
        state_service.set_module_status(sid, "clarifications", ModuleStatus.COMPLETED, fingerprint=q_fp)

        if not request.vendor_name:
            CLARIFICATION_CACHE[sid] = response

        return response

    finally:
        op_lock.release_lock(lock_key)
