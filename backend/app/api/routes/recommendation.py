"""FastAPI route handler for evidence-backed recommendation and executive decision brief."""

import hashlib
import json
import logging
from typing import Dict, Optional
from fastapi import APIRouter, HTTPException, status
from app.config import Config
from app.validators import validate_session_id
from app.models import (
    RecommendationRequestModel,
    RecommendationResponseModel,
    ProcurementRequirements,
    ComparisonMatrixRow,
    RiskFindingModel,
    ContradictionFindingModel,
    ClarificationQuestionModel,
    ScoringResponseModel,
)
from app.services.vector_store import get_vector_store
from app.services.recommendation_service import RecommendationService
from app.services.rate_limiter import get_rate_limiter, get_operation_lock
from app.api.routes.comparison import COMPARISON_CACHE
from app.api.routes.risks import RISK_ANALYSIS_CACHE
from app.api.routes.clarifications import CLARIFICATION_CACHE
from app.api.routes.scoring import SCORING_CACHE, derive_scoring_cache_fingerprint

router = APIRouter()

# In-memory cache for versioned recommendation responses
RECOMMENDATION_CACHE: Dict[str, RecommendationResponseModel] = {}


def clear_recommendation_cache(session_id: str):
    """Clear cached recommendation responses for a session when proposals change."""
    keys_to_delete = [k for k in RECOMMENDATION_CACHE.keys() if k.startswith(f"{session_id}_")]
    for k in keys_to_delete:
        del RECOMMENDATION_CACHE[k]


def derive_recommendation_cache_fingerprint(
    session_id: str,
    scoring_fingerprint: str,
    reqs: ProcurementRequirements,
    risk_findings: Optional[list],
    contradictions: Optional[list],
    clarifications: Optional[list],
) -> str:
    """Derive deterministic cache fingerprint for recommendation service (Rule 19)."""
    policy_ver = Config.RECOMMENDATION_POLICY_VERSION
    reqs_hash = hashlib.sha256(json.dumps(reqs.model_dump(), sort_keys=True, default=str).encode()).hexdigest()[:12]
    risk_hash = hashlib.sha256(json.dumps([r.model_dump() for r in (risk_findings or [])], sort_keys=True, default=str).encode()).hexdigest()[:12]
    ctr_hash = hashlib.sha256(json.dumps([c.model_dump() for c in (contradictions or [])], sort_keys=True, default=str).encode()).hexdigest()[:12]
    clrf_hash = hashlib.sha256(json.dumps([q.model_dump() for q in (clarifications or [])], sort_keys=True, default=str).encode()).hexdigest()[:12]

    return f"{session_id}_pol{policy_ver}_scfp{scoring_fingerprint}_req{reqs_hash}_rsk{risk_hash}_ctr{ctr_hash}_clrf{clrf_hash}"


@router.post(
    "/generate",
    response_model=RecommendationResponseModel,
    status_code=status.HTTP_200_OK,
    summary="Generate evidence-backed executive recommendation decision brief",
)
async def generate_recommendation(request: RecommendationRequestModel) -> RecommendationResponseModel:
    """Generate evidence-backed recommendation decision brief using trusted server state (Rule 37-39)."""
    try:
        sid = validate_session_id(request.session_id)
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err),
        ) from err

    # Rate limiting & operation lock
    rate_limiter = get_rate_limiter()
    rate_limiter.check_rate_limit(sid, "recommendation_generate")

    op_lock = get_operation_lock()
    lock_key = op_lock.acquire_lock(sid, "recommendation_generate")

    try:
        vector_store = get_vector_store()
        if not vector_store.has_session(sid):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Analysis session '{sid}' not found or index not built.",
            )

        # 1. Retrieve Phase 4 comparison state
        comp_resp = COMPARISON_CACHE.get(sid)
        if not comp_resp or not comp_resp.matrix_rows:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Requirement comparison must be evaluated for session '{sid}' before generating recommendation.",
            )

        reqs: ProcurementRequirements = request.requirements or comp_resp.requirements
        matrix_rows = comp_resp.matrix_rows

        # 2. Retrieve Phase 5 risk & contradiction state
        risk_resp = RISK_ANALYSIS_CACHE.get(sid)
        risk_findings = risk_resp.risk_findings if risk_resp else None
        contradictions = risk_resp.contradiction_findings if risk_resp else None

        # 3. Retrieve Phase 6 clarification state
        clrf_resp = CLARIFICATION_CACHE.get(sid)
        clarifications = clrf_resp.questions if clrf_resp else None

        # 4. Retrieve Phase 7 scoring response - MUST be explicitly COMPLETED
        from app.services.session_state_service import get_session_state_service
        from app.models import ModuleStatus
        state_service = get_session_state_service()

        rnk_st = state_service.get_module_status(sid, "ranking")
        if rnk_st != ModuleStatus.COMPLETED:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Recommendation Brief is blocked because Vendor Ranking is {rnk_st.value}.",
            )

        scoring_service_fp = derive_scoring_cache_fingerprint(
            session_id=sid,
            requirements=reqs,
            matrix_rows=matrix_rows,
            risk_findings=risk_findings,
            contradictions=contradictions,
            clarifications=clarifications,
        )

        scoring_resp = SCORING_CACHE.get(scoring_service_fp)
        if not scoring_resp:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Recommendation Brief is blocked because Vendor Ranking cache is missing or stale.",
            )

        # Derive recommendation cache fingerprint (Rule 19)
        rec_cache_fp = derive_recommendation_cache_fingerprint(
            session_id=sid,
            scoring_fingerprint=scoring_service_fp,
            reqs=reqs,
            risk_findings=risk_findings,
            contradictions=contradictions,
            clarifications=clarifications,
        )

        # Return cached recommendation response if identical upstream fingerprint exists
        if rec_cache_fp in RECOMMENDATION_CACHE:
            return RECOMMENDATION_CACHE[rec_cache_fp]

        # Execute Recommendation Service
        rec_service = RecommendationService()
        decision = rec_service.evaluate_recommendation_policy(
            scoring_response=scoring_resp,
            requirements=reqs,
            risk_findings=risk_findings,
            contradictions=contradictions,
            clarifications=clarifications,
        )

        narrative = rec_service.generate_executive_narrative(
            decision=decision,
            scoring_response=scoring_resp,
        )

        import datetime
        response = RecommendationResponseModel(
            status="success",
            session_id=sid,
            recommendation_policy_version=Config.RECOMMENDATION_POLICY_VERSION,
            generated_at=datetime.datetime.utcnow().isoformat() + "Z",
            decision=decision,
            narrative=narrative,
            privacy_notice=Config.PRIVACY_NOTICE,
        )

        RECOMMENDATION_CACHE[rec_cache_fp] = response
        return response

    finally:
        op_lock.release_lock(lock_key)


@router.get(
    "/{session_id}",
    response_model=RecommendationResponseModel,
    status_code=status.HTTP_200_OK,
    summary="Get cached recommendation brief for a session",
)
async def get_recommendation(session_id: str) -> RecommendationResponseModel:
    """Retrieve cached recommendation brief for an active session."""
    try:
        sid = validate_session_id(session_id)
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err),
        ) from err

    matching_keys = [k for k in RECOMMENDATION_CACHE.keys() if k.startswith(f"{sid}_")]
    if not matching_keys:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recommendation brief has not been generated for session '{sid}'.",
        )
    return RECOMMENDATION_CACHE[matching_keys[-1]]
