"""FastAPI route handler for deterministic vendor scoring and transparent ranking."""

import hashlib
import json
import logging
from typing import Dict, List, Optional
from fastapi import APIRouter, HTTPException, status
from app.config import Config
from app.validators import validate_session_id
from app.models import (
    ScoringRequestModel,
    ScoringResponseModel,
    VendorScoreBreakdownModel,
    ProcurementRequirements,
    ComparisonMatrixRow,
    RiskFindingModel,
    ContradictionFindingModel,
    ClarificationQuestionModel,
)
from app.services.vector_store import get_vector_store
from app.services.scoring_service import ScoringService
from app.services.rate_limiter import get_rate_limiter
from app.api.routes.comparison import FACT_SHEETS_CACHE, COMPARISON_CACHE
from app.api.routes.risks import RISK_ANALYSIS_CACHE
from app.api.routes.clarifications import CLARIFICATION_CACHE

router = APIRouter()

# In-memory cache for versioned scoring responses (Key: Cache Fingerprint Hash)
SCORING_CACHE: Dict[str, ScoringResponseModel] = {}


def clear_scoring_cache(session_id: str):
    """Clear cached scoring responses for a session when proposals change."""
    keys_to_delete = [k for k in SCORING_CACHE.keys() if k.startswith(f"{session_id}_")]
    for k in keys_to_delete:
        del SCORING_CACHE[k]


def derive_scoring_cache_fingerprint(
    session_id: str,
    requirements: ProcurementRequirements,
    matrix_rows: List[ComparisonMatrixRow],
    risk_findings: Optional[List[RiskFindingModel]],
    contradictions: Optional[List[ContradictionFindingModel]],
    clarifications: Optional[List[ClarificationQuestionModel]],
) -> str:
    """Derive deterministic cache fingerprint hash from backend trusted server state (Hardening Fix 1)."""
    # 1. Requirements Hash
    reqs_raw = json.dumps(requirements.model_dump(), sort_keys=True, default=str)
    reqs_hash = hashlib.sha256(reqs_raw.encode("utf-8")).hexdigest()[:12]

    # 2. Comparison Matrix Hash
    comp_raw = json.dumps([r.model_dump() for r in matrix_rows], sort_keys=True, default=str)
    comp_hash = hashlib.sha256(comp_raw.encode("utf-8")).hexdigest()[:12]

    # 3. Risk Findings Hash
    risk_raw = json.dumps([r.model_dump() for r in (risk_findings or [])], sort_keys=True, default=str)
    risk_hash = hashlib.sha256(risk_raw.encode("utf-8")).hexdigest()[:12]

    # 4. Contradictions Hash
    ctr_raw = json.dumps([c.model_dump() for c in (contradictions or [])], sort_keys=True, default=str)
    ctr_hash = hashlib.sha256(ctr_raw.encode("utf-8")).hexdigest()[:12]

    # 5. Clarifications Hash
    clrf_raw = json.dumps([q.model_dump() for q in (clarifications or [])], sort_keys=True, default=str)
    clrf_hash = hashlib.sha256(clrf_raw.encode("utf-8")).hexdigest()[:12]

    # Combined Cache Fingerprint Key
    scoring_ver = Config.SCORING_VERSION
    return f"{session_id}_v{scoring_ver}_req{reqs_hash}_comp{comp_hash}_rsk{risk_hash}_ctr{ctr_hash}_clrf{clrf_hash}"


@router.post(
    "/evaluate",
    response_model=ScoringResponseModel,
    status_code=status.HTTP_200_OK,
    summary="Evaluate transparent deterministic vendor alignment scores and ranking",
)
async def evaluate_vendor_scoring(request: ScoringRequestModel) -> ScoringResponseModel:
    """Evaluate deterministic vendor alignment scores and transparent ranking using trusted server state (Rule 40 & Hardening Fix 1)."""
    try:
        sid = validate_session_id(request.session_id)
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err),
        ) from err

    # Session rate limiting
    rate_limiter = get_rate_limiter()
    rate_limiter.check_rate_limit(sid, "scoring_evaluate")

    vector_store = get_vector_store()
    if not vector_store.has_session(sid):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analysis session '{sid}' not found or index not built.",
        )

    # Retrieve trusted server-side analysis artifacts
    comp_resp = COMPARISON_CACHE.get(sid)
    if not comp_resp or not comp_resp.matrix_rows:
        comp_rows = []
        reqs = request.requirements
    else:
        comp_rows = comp_resp.matrix_rows
        reqs = request.requirements or comp_resp.requirements

    risk_resp = RISK_ANALYSIS_CACHE.get(sid)
    risk_findings: Optional[List[RiskFindingModel]] = risk_resp.risk_findings if risk_resp is not None else []
    contradictions: Optional[List[ContradictionFindingModel]] = risk_resp.contradiction_findings if risk_resp is not None else []

    clrf_resp = CLARIFICATION_CACHE.get(sid)
    clarifications: Optional[List[ClarificationQuestionModel]] = clrf_resp.questions if clrf_resp is not None else []

    # Derive current fingerprints for prerequisite validation
    reqs_fp = hashlib.sha256(json.dumps(reqs.model_dump(), sort_keys=True, default=str).encode()).hexdigest()[:12] if reqs else None
    comp_fp = hashlib.sha256(json.dumps([r.model_dump() for r in comp_rows], sort_keys=True, default=str).encode()).hexdigest()[:12] if comp_rows else None
    risk_fp = hashlib.sha256(json.dumps([r.model_dump() for r in (risk_findings or [])] + [c.model_dump() for c in (contradictions or [])], sort_keys=True, default=str).encode()).hexdigest()[:12] if (risk_findings is not None or contradictions is not None) else None
    clrf_fp = hashlib.sha256(json.dumps([q.model_dump() for q in (clarifications or [])], sort_keys=True, default=str).encode()).hexdigest()[:12] if clarifications is not None else None

    from app.services.session_state_service import get_session_state_service
    from app.models import ModuleStatus
    from fastapi.responses import JSONResponse
    state_service = get_session_state_service()

    blocked_model = state_service.check_ranking_prerequisites(
        session_id=sid,
        current_reqs_fp=reqs_fp,
        current_comp_fp=comp_fp,
        current_risk_fp=risk_fp,
        current_clrf_fp=clrf_fp,
    )

    if blocked_model is not None:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content=blocked_model.model_dump(),
        )

    # Derive server-side trusted cache fingerprint
    cache_fingerprint = derive_scoring_cache_fingerprint(
        session_id=sid,
        requirements=reqs,
        matrix_rows=comp_rows,
        risk_findings=risk_findings,
        contradictions=contradictions,
        clarifications=clarifications,
    )

    # Return cached response if exact upstream analysis state fingerprint matches
    if cache_fingerprint in SCORING_CACHE and not request.vendor_name:
        return SCORING_CACHE[cache_fingerprint]

    # Execute 100% Deterministic Scoring Engine (0 Groq calls!)
    scoring_service = ScoringService()
    response = scoring_service.evaluate_session_scoring(
        session_id=sid,
        requirements=reqs,
        matrix_rows=comp_rows,
        risk_findings=risk_findings,
        contradictions=contradictions,
        clarifications=clarifications,
        vendor_name_filter=request.vendor_name,
    )

    state_service.set_module_status(sid, "ranking", ModuleStatus.COMPLETED, fingerprint=cache_fingerprint)

    if not request.vendor_name:
        SCORING_CACHE[cache_fingerprint] = response

    return response


@router.get(
    "/{session_id}",
    response_model=ScoringResponseModel,
    status_code=status.HTTP_200_OK,
    summary="Get cached vendor alignment scores and ranking for a session",
)
async def get_vendor_scoring(session_id: str) -> ScoringResponseModel:
    """Retrieve cached vendor alignment scores for an active session."""
    try:
        sid = validate_session_id(session_id)
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err),
        ) from err

    matching_keys = [k for k in SCORING_CACHE.keys() if k.startswith(f"{sid}_")]
    if not matching_keys:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vendor scoring has not been evaluated for session '{sid}'.",
        )
    return SCORING_CACHE[matching_keys[-1]]
