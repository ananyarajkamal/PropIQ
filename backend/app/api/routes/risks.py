"""FastAPI route handler for contract risk and contradiction intelligence."""

from typing import Dict, List, Optional
from fastapi import APIRouter, HTTPException, status
from app.config import Config
from app.validators import validate_session_id
from app.models import (
    RiskAnalysisRequest,
    RiskAnalysisResponse,
    RiskFindingModel,
    ContradictionFindingModel,
    RiskSeverity,
    RiskStatus,
    VendorFactSheet,
)
from app.services.vector_store import get_vector_store
from app.services.retrieval_service import SessionNotFoundError
from app.services.risk_service import RiskService
from app.services.contradiction_service import ContradictionService
from app.services.rate_limiter import get_rate_limiter, get_operation_lock
from app.api.routes.comparison import FACT_SHEETS_CACHE

router = APIRouter()

# In-memory cache for session risk analysis responses
RISK_ANALYSIS_CACHE: Dict[str, RiskAnalysisResponse] = {}


def clear_risk_cache(session_id: str):
    """Clear cached risk findings if proposal session changes."""
    if session_id in RISK_ANALYSIS_CACHE:
        del RISK_ANALYSIS_CACHE[session_id]


@router.post(
    "/analyze",
    response_model=RiskAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyze evidence-grounded contract risks and intra-vendor contradictions",
)
async def analyze_contract_risks(request: RiskAnalysisRequest) -> RiskAnalysisResponse:
    """Analyze contract risks and intra-vendor statement contradictions with caching and zero-Groq requirement re-evaluations."""
    try:
        sid = validate_session_id(request.session_id)
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err),
        ) from err

    # Rate limiting & operation lock
    rate_limiter = get_rate_limiter()
    rate_limiter.check_rate_limit(sid, "risks_analyze")

    op_lock = get_operation_lock()
    lock_key = op_lock.acquire_lock(sid, "risks_analyze")

    try:
        vector_store = get_vector_store()
        if not vector_store.has_session(sid):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Analysis session '{sid}' not found or index not built.",
            )

        # Cache check: If generic findings already exist and user only edited requirements (Rule 3),
        # recalculate requirement impact locally in Python with 0 additional Groq calls!
        if sid in RISK_ANALYSIS_CACHE and not request.vendor_name:
            cached_resp = RISK_ANALYSIS_CACHE[sid]

            # Local Python re-linking of requirements without Groq calls!
            updated_findings: List[RiskFindingModel] = []
            for f in cached_resp.risk_findings:
                rel_reqs: List[str] = []
                if request.requirements:
                    if f.category.value == "AUTO_RENEWAL" and request.requirements.renewal_preference:
                        rel_reqs.append("REQ_RENEWAL")
                    elif f.category.value in {"LIABILITY_CAP", "UNCAPPED_LIABILITY"} and request.requirements.liability_requirement:
                        rel_reqs.append("REQ_LIABILITY")
                    elif f.category.value in {"TERMINATION_RESTRICTION", "EARLY_TERMINATION_FEE"} and request.requirements.termination_requirement:
                        rel_reqs.append("REQ_TERMINATION")
                    elif f.category.value == "SUPPORT_LIMITATION" and request.requirements.support_requirement:
                        rel_reqs.append("REQ_SUPPORT")

                f_copy = f.copy()
                f_copy.related_requirement_ids = rel_reqs
                updated_findings.append(f_copy)

            cached_resp.risk_findings = updated_findings
            return cached_resp

        fact_sheets: Optional[List[VendorFactSheet]] = FACT_SHEETS_CACHE.get(sid)

        # 1. Execute Risk Service
        risk_service = RiskService()
        risk_findings = risk_service.analyze_session_risks(
            session_id=sid,
            requirements=request.requirements,
            fact_sheets=fact_sheets,
            vendor_name_filter=request.vendor_name,
        )

        # 2. Execute Contradiction Service
        contradiction_service = ContradictionService()
        contradiction_findings = contradiction_service.analyze_session_contradictions(
            session_id=sid,
            fact_sheets=fact_sheets,
            vendor_name_filter=request.vendor_name,
        )

        # 3. Calculate Summary Counts
        high_count = sum(1 for f in risk_findings if f.severity in {RiskSeverity.HIGH, RiskSeverity.CRITICAL})
        med_count = sum(1 for f in risk_findings if f.severity == RiskSeverity.MEDIUM)
        clarify_count = sum(1 for f in risk_findings if f.status == RiskStatus.NEEDS_CLARIFICATION or f.severity == RiskSeverity.LOW)
        ctr_count = len(contradiction_findings)

        response = RiskAnalysisResponse(
            status="success",
            session_id=sid,
            risk_findings=risk_findings,
            contradiction_findings=contradiction_findings,
            high_priority_count=high_count,
            medium_priority_count=med_count,
            needs_clarification_count=clarify_count,
            contradictions_count=ctr_count,
            privacy_notice=Config.PRIVACY_NOTICE,
        )

        import hashlib
        import json
        rf_raw = json.dumps([r.model_dump() for r in risk_findings] + [c.model_dump() for c in contradiction_findings], sort_keys=True, default=str)
        rf_fp = hashlib.sha256(rf_raw.encode("utf-8")).hexdigest()[:12]

        from app.services.session_state_service import get_session_state_service
        from app.models import ModuleStatus
        state_service = get_session_state_service()
        state_service.set_module_status(sid, "risks_contradictions", ModuleStatus.COMPLETED, fingerprint=rf_fp)

        if not request.vendor_name:
            RISK_ANALYSIS_CACHE[sid] = response

        return response

    finally:
        op_lock.release_lock(lock_key)
