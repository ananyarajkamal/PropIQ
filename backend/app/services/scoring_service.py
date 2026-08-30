"""Deterministic Vendor Scoring and Transparent Ranking Service for PropIQ.

Calculates vendor Alignment Scores (0.0 to 100.0) from Phase 4 requirement evaluation matrix,
Phase 5 risk findings, Phase 5 contradictions, and Phase 6 clarification gaps.
Enforces 100% deterministic Python calculation with 0 Groq calls.
"""

from decimal import Decimal, ROUND_HALF_UP
import datetime
import logging
import re
from typing import Dict, List, Optional, Any, Set, Tuple
from app.config import Config
from app.models import (
    RequirementPriority,
    RankStatus,
    RequirementScoreComponentModel,
    ScoreDeductionModel,
    VendorScoreBreakdownModel,
    ScoringResponseModel,
    ProcurementRequirements,
    ComparisonMatrixRow,
    RequirementEvaluationResult,
    RiskFindingModel,
    RiskCategory,
    RiskSeverity,
    RiskStatus,
    ContradictionFindingModel,
    ContradictionStatus,
    ClarificationQuestionModel,
    ClarificationReason,
    QuestionPriority,
    EvidenceCitationModel,
)

logger = logging.getLogger("propiq_backend")


class ScoringService:
    """Service executing 100% deterministic vendor scoring and transparent ranking."""

    def __init__(self, config_override: Optional[Dict[str, Any]] = None):
        self.config = config_override or Config.SCORING_CONFIG
        self.priority_weights = self.config["priority_weights"]
        self.state_scores = self.config["state_scores"]
        self.risk_penalties = self.config["risk_penalties"]
        self.risk_penalty_cap = float(self.config["risk_penalty_cap"])
        self.linked_risk_reduction = float(self.config.get("linked_risk_reduction_factor", 0.50))
        self.contradiction_penalties = self.config["contradiction_penalties"]
        self.contradiction_penalty_cap = float(self.config["contradiction_penalty_cap"])
        self.clarification_penalties = self.config["clarification_penalties"]
        self.clarification_penalty_cap = float(self.config["clarification_penalty_cap"])
        self.tie_tolerance = float(self.config.get("tie_tolerance", 0.5))

    def evaluate_session_scoring(
        self,
        session_id: str,
        requirements: ProcurementRequirements,
        matrix_rows: List[ComparisonMatrixRow],
        risk_findings: Optional[List[RiskFindingModel]] = None,
        contradictions: Optional[List[ContradictionFindingModel]] = None,
        clarifications: Optional[List[ClarificationQuestionModel]] = None,
        vendor_name_filter: Optional[str] = None,
    ) -> ScoringResponseModel:
        """Evaluate transparent vendor scores and ranking using trusted server state (0 Groq calls!)."""
        # 1. Identify all unique vendors from comparison matrix
        vendor_names: List[str] = []
        if matrix_rows and matrix_rows[0].vendor_evaluations:
            vendor_names = list(matrix_rows[0].vendor_evaluations.keys())

        if vendor_name_filter:
            vendor_names = [v for v in vendor_names if v.lower() == vendor_name_filter.lower()]

        if not vendor_names:
            return ScoringResponseModel(
                status="success",
                session_id=session_id,
                scoring_version=self.config.get("scoring_version", "1.0"),
                evaluated_at=datetime.datetime.utcnow().isoformat() + "Z",
                vendor_scores=[],
                total_vendors=0,
                scoring_config_summary=self.config,
                privacy_notice=Config.PRIVACY_NOTICE,
            )

        # 2. Compute raw score breakdowns for each vendor
        raw_breakdowns: List[Dict[str, Any]] = []
        for vname in vendor_names:
            v_risks = [r for r in risk_findings if r.vendor_name == vname] if risk_findings is not None else None
            v_ctrs = [c for c in contradictions if c.vendor_name == vname] if contradictions is not None else None
            v_clrfs = [q for q in clarifications if q.vendor_name == vname] if clarifications is not None else None

            breakdown = self._calculate_vendor_score(
                vendor_name=vname,
                requirements=requirements,
                matrix_rows=matrix_rows,
                risk_findings=v_risks,
                contradictions=v_ctrs,
                clarifications=v_clrfs,
            )
            raw_breakdowns.append(breakdown)

        # 3. Sort vendors and assign ranks with tie detection (Rule 30 & Rule 31)
        ranked_scores = self._rank_and_resolve_ties(raw_breakdowns)

        return ScoringResponseModel(
            status="success",
            session_id=session_id,
            scoring_version=self.config.get("scoring_version", "1.0"),
            evaluated_at=datetime.datetime.utcnow().isoformat() + "Z",
            vendor_scores=ranked_scores,
            total_vendors=len(ranked_scores),
            scoring_config_summary=self.config,
            privacy_notice=Config.PRIVACY_NOTICE,
        )

    def _calculate_vendor_score(
        self,
        vendor_name: str,
        requirements: ProcurementRequirements,
        matrix_rows: List[ComparisonMatrixRow],
        risk_findings: Optional[List[RiskFindingModel]] = None,
        contradictions: Optional[List[ContradictionFindingModel]] = None,
        clarifications: Optional[List[ClarificationQuestionModel]] = None,
    ) -> Dict[str, Any]:
        """Calculate base weighted score, canonical issue deductions, and caps for one vendor."""
        risk_analysis_status = "COMPLETED" if risk_findings is not None else "NOT_ANALYZED"
        if risk_findings is not None and len(risk_findings) == 0:
            risk_analysis_status = "COMPLETED_NO_FINDINGS"

        contradiction_analysis_status = "COMPLETED" if contradictions is not None else "NOT_ANALYZED"
        if contradictions is not None and len(contradictions) == 0:
            contradiction_analysis_status = "COMPLETED_NO_FINDINGS"

        clarification_analysis_status = "COMPLETED" if clarifications is not None else "NOT_ANALYZED"
        if clarifications is not None and len(clarifications) == 0:
            clarification_analysis_status = "COMPLETED_NO_FINDINGS"

        active_risks = risk_findings or []
        active_ctrs = contradictions or []
        active_clrfs = clarifications or []
        # 1. Base Requirement Weighted Score Calculation (Rule 10 & 11)
        components: List[RequirementScoreComponentModel] = []
        total_weighted_points = 0.0
        total_max_points = 0.0
        must_have_failed_labels: List[str] = []
        must_have_failed_count = 0
        requirements_met_count = 0

        failed_requirement_ids: Set[str] = set()

        for row in matrix_rows:
            eval_res = row.vendor_evaluations.get(vendor_name)
            if not eval_res:
                continue

            req_id = eval_res.requirement_id
            prio = self._get_requirement_priority(req_id, requirements)
            weight = self.priority_weights.get(prio.value, 3.0)

            state_score = self.state_scores.get(eval_res.status, 0.20)
            w_pts = state_score * weight

            total_weighted_points += w_pts
            total_max_points += weight

            if eval_res.status == "MEETS":
                requirements_met_count += 1
            elif eval_res.status in {"FAILS", "MISSING", "UNCLEAR", "CONFLICTING"}:
                failed_requirement_ids.add(req_id)
                if prio == RequirementPriority.MUST_HAVE:
                    must_have_failed_count += 1
                    must_have_failed_labels.append(row.requirement_label)

            components.append(
                RequirementScoreComponentModel(
                    requirement_id=req_id,
                    requirement_label=row.requirement_label,
                    priority=prio,
                    weight=weight,
                    comparison_status=eval_res.status,
                    status_score=state_score,
                    weighted_points=round(w_pts, 2),
                    max_points=weight,
                    raw_vendor_value=eval_res.raw_vendor_value,
                    normalized_vendor_value=eval_res.normalized_vendor_value,
                    evidence_citations=eval_res.evidence_citations,
                )
            )

        # Base alignment score percentage (0.0 to 100.0)
        base_alignment_score = (
            (total_weighted_points / total_max_points) * 100.0 if total_max_points > 0 else 100.0
        )

        deductions: List[ScoreDeductionModel] = []
        canonical_issues_seen: Set[str] = set()

        # 2. Risk Deductions & Canonical Issue Linking (Rule 15, 17, 20)
        uncapped_risk_penalties = 0.0
        for risk in active_risks:
            if risk.status in {RiskStatus.NOT_DETECTED}:
                continue

            raw_pen = float(self.risk_penalties.get(risk.severity.value, 1.5))
            linked_req = risk.related_requirement_ids[0] if risk.related_requirement_ids else None
            is_linked = False

            # Check if this issue is already penalized under requirement comparison
            if linked_req and linked_req in failed_requirement_ids:
                is_linked = True
                final_pen = raw_pen * self.linked_risk_reduction  # 50% reduced penalty
                exp_text = f"Reduced from -{raw_pen} to -{final_pen} points because this concern is already reflected in the requirement evaluation result."
            else:
                final_pen = raw_pen
                exp_text = f"Identified contract risk ({risk.severity.value}): {risk.title}."

            uncapped_risk_penalties += final_pen
            deductions.append(
                ScoreDeductionModel(
                    deduction_id=risk.risk_id,
                    category=risk.category.value,
                    type="RISK",
                    label=risk.title,
                    severity_or_priority=risk.severity.value,
                    raw_penalty=raw_pen,
                    final_deduction=final_pen,
                    is_linked_risk=is_linked,
                    linked_requirement_id=linked_req,
                    explanation=exp_text,
                    evidence_citations=risk.evidence_citations,
                )
            )

        # Apply Risk Penalty Cap (Rule 16: Max 15.0 pts)
        total_risk_penalty = min(self.risk_penalty_cap, uncapped_risk_penalties)

        # 3. Contradiction Deductions (Rule 18: Max 10.0 pts)
        uncapped_ctr_penalties = 0.0
        for ctr in active_ctrs:
            if ctr.status in {ContradictionStatus.DISMISSED, ContradictionStatus.CONTEXT_DEPENDENT}:
                continue

            raw_pen = float(self.contradiction_penalties.get(ctr.status.value, 1.0))
            if ctr.status == ContradictionStatus.CONFIRMED_CONTRADICTION:
                raw_pen = float(self.contradiction_penalties.get("CONFIRMED_CONTRADICTION", 2.5))

            uncapped_ctr_penalties += raw_pen
            cits = (ctr.evidence_a or []) + (ctr.evidence_b or [])
            deductions.append(
                ScoreDeductionModel(
                    deduction_id=ctr.contradiction_id,
                    category=ctr.category,
                    type="CONTRADICTION",
                    label=f"Statement Contradiction ({ctr.category})",
                    severity_or_priority=ctr.severity.value,
                    raw_penalty=raw_pen,
                    final_deduction=raw_pen,
                    is_linked_risk=False,
                    explanation=f"Conflicting statement claims: {ctr.reason}",
                    evidence_citations=cits,
                )
            )

        # Apply Contradiction Penalty Cap (Rule 18: Max 10.0 pts)
        total_contradiction_penalty = min(self.contradiction_penalty_cap, uncapped_ctr_penalties)

        # 4. Clarification Deductions (Rule 19: Max 8.0 pts)
        uncapped_clrf_penalties = 0.0
        for q in active_clrfs:
            raw_pen = float(self.clarification_penalties.get(q.priority.value, 0.75))
            linked_req = q.requirement_id
            is_linked = False

            if linked_req and linked_req in failed_requirement_ids:
                is_linked = True
                final_pen = raw_pen * self.linked_risk_reduction  # 50% reduced penalty
                exp_text = f"Reduced from -{raw_pen} to -{final_pen} points because this gap is already reflected in requirement scoring."
            else:
                final_pen = raw_pen
                exp_text = f"Unresolved clarification item ({q.priority.value} priority): {q.reason.value.replace('_', ' ')}."

            uncapped_clrf_penalties += final_pen
            deductions.append(
                ScoreDeductionModel(
                    deduction_id=q.clarification_id,
                    category=q.reason.value,
                    type="CLARIFICATION",
                    label=f"Clarification: {q.reason.value.replace('_', ' ')}",
                    severity_or_priority=q.priority.value,
                    raw_penalty=raw_pen,
                    final_deduction=final_pen,
                    is_linked_risk=is_linked,
                    linked_requirement_id=linked_req,
                    explanation=exp_text,
                    evidence_citations=q.evidence_citations,
                )
            )

        # Apply Clarification Penalty Cap (Rule 19: Max 8.0 pts)
        total_clarification_penalty = min(self.clarification_penalty_cap, uncapped_clrf_penalties)

        # 5. Final Alignment Score Calculation, Clamping & Precision (Rule 22 & Rule 23)
        raw_final_score = base_alignment_score - (total_risk_penalty + total_contradiction_penalty + total_clarification_penalty)

        # Clamp between 0.0 and 100.0
        clamped_score = max(0.0, min(100.0, raw_final_score))
        final_alignment_score = float(
            Decimal(str(clamped_score)).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
        )
        if final_alignment_score == -0.0:
            final_alignment_score = 0.0

        base_alignment_score_formatted = float(
            Decimal(str(base_alignment_score)).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
        )

        return {
            "vendor_name": vendor_name,
            "base_alignment_score": base_alignment_score_formatted,
            "total_risk_penalty": round(total_risk_penalty, 2),
            "total_contradiction_penalty": round(total_contradiction_penalty, 2),
            "total_clarification_penalty": round(total_clarification_penalty, 2),
            "risk_analysis_status": risk_analysis_status,
            "contradiction_analysis_status": contradiction_analysis_status,
            "clarification_analysis_status": clarification_analysis_status,
            "must_have_failures_count": must_have_failed_count,
            "must_have_failed_labels": must_have_failed_labels,
            "requirements_met_count": requirements_met_count,
            "total_requirements_count": len(components),
            "alignment_score": final_alignment_score,
            "requirement_components": components,
            "deductions": deductions,

            # Raw values for tie breaking
            "raw_high_critical_risks": sum(1 for r in active_risks if r.severity in {RiskSeverity.HIGH, RiskSeverity.CRITICAL}),
            "raw_high_clarifications": sum(1 for q in active_clrfs if q.priority == QuestionPriority.HIGH),
        }

    def _rank_and_resolve_ties(
        self,
        breakdowns: List[Dict[str, Any]],
    ) -> List[VendorScoreBreakdownModel]:
        """Sort vendors, resolve ties deterministically, and generate breakdown models."""
        sorted_raw = sorted(
            breakdowns,
            key=lambda b: (
                -b["alignment_score"],
                b["must_have_failures_count"],
                -b["base_alignment_score"],
                b["raw_high_critical_risks"],
                b["raw_high_clarifications"],
                b["vendor_name"],
            )
        )

        result_models: List[VendorScoreBreakdownModel] = []
        n_vendors = len(sorted_raw)

        for idx, item in enumerate(sorted_raw):
            rank = idx + 1
            score = item["alignment_score"]

            is_tied = False
            if idx > 0 and abs(score - sorted_raw[idx - 1]["alignment_score"]) < self.tie_tolerance:
                is_tied = True
            if idx < n_vendors - 1 and abs(score - sorted_raw[idx + 1]["alignment_score"]) < self.tie_tolerance:
                is_tied = True

            if is_tied:
                r_status = RankStatus.TIED
            elif rank == 1:
                r_status = RankStatus.LEADING
            elif rank == 2:
                r_status = RankStatus.COMPETITIVE
            else:
                r_status = RankStatus.BEHIND

            explanation = self._generate_deterministic_explanation(
                vendor_name=item["vendor_name"],
                rank=rank,
                alignment_score=score,
                rank_status=r_status,
                met_count=item["requirements_met_count"],
                total_count=item["total_requirements_count"],
                must_have_failures=item["must_have_failures_count"],
                must_have_labels=item["must_have_failed_labels"],
                risk_pen=item["total_risk_penalty"],
                ctr_pen=item["total_contradiction_penalty"],
                clrf_pen=item["total_clarification_penalty"],
                risk_status=item["risk_analysis_status"],
                ctr_status=item["contradiction_analysis_status"],
                clrf_status=item["clarification_analysis_status"],
                deductions_count=len(item["deductions"]),
            )

            result_models.append(
                VendorScoreBreakdownModel(
                    vendor_name=item["vendor_name"],
                    rank=rank,
                    rank_status=r_status,
                    alignment_score=score,
                    base_alignment_score=item["base_alignment_score"],
                    total_risk_penalty=item["total_risk_penalty"],
                    total_contradiction_penalty=item["total_contradiction_penalty"],
                    total_clarification_penalty=item["total_clarification_penalty"],
                    risk_analysis_status=item["risk_analysis_status"],
                    contradiction_analysis_status=item["contradiction_analysis_status"],
                    clarification_analysis_status=item["clarification_analysis_status"],
                    must_have_failures_count=item["must_have_failures_count"],
                    must_have_failed_labels=item["must_have_failed_labels"],
                    requirements_met_count=item["requirements_met_count"],
                    total_requirements_count=item["total_requirements_count"],
                    requirement_components=item["requirement_components"],
                    deductions=item["deductions"],
                    ranking_explanation=explanation,
                )
            )

        return result_models

    def _generate_deterministic_explanation(
        self,
        vendor_name: str,
        rank: int,
        alignment_score: float,
        rank_status: RankStatus,
        met_count: int,
        total_count: int,
        must_have_failures: int,
        must_have_labels: List[str],
        risk_pen: float,
        ctr_pen: float,
        clrf_pen: float,
        risk_status: str,
        ctr_status: str,
        clrf_status: str,
        deductions_count: int,
    ) -> str:
        """Generate concise, evidence-backed deterministic ranking explanation string."""
        rank_suffix = "st" if rank == 1 else "nd" if rank == 2 else "rd" if rank == 3 else "th"

        if must_have_failures > 0:
            status_desc = f"{vendor_name} is UNQUALIFIED due to {must_have_failures} mandatory (Must Have) requirement failure{'s' if must_have_failures > 1 else ''} with a {alignment_score} raw alignment score."
        elif rank_status == RankStatus.TIED:
            status_desc = f"{vendor_name} is tied for position with a {alignment_score} alignment score."
        else:
            status_text = "currently leads" if rank == 1 else "ranks"
            status_desc = f"{vendor_name} {status_text} {rank}{rank_suffix} with a {alignment_score} alignment score."

        met_desc = f"It satisfies {met_count} of {total_count} evaluated requirements."

        if must_have_failures > 0:
            must_desc = f"Note: {must_have_failures} Must Have requirement{'s' if must_have_failures > 1 else ''} ({', '.join(must_have_labels)}) were not met."
        else:
            must_desc = "It satisfies all configured Must Have requirements."

        total_ded = risk_pen + ctr_pen + clrf_pen
        if total_ded > 0:
            ded_desc = f"Score adjustments: -{risk_pen} pts risk concerns, -{ctr_pen} pts statement contradictions, -{clrf_pen} pts open clarifications."
        elif risk_status == "NOT_ANALYZED" and ctr_status == "NOT_ANALYZED" and clrf_status == "NOT_ANALYZED":
            ded_desc = "Risk, contradiction, and clarification analyses have not been performed for this session."
        else:
            ded_desc = "No risk or clarification score deductions were applied."

        return f"{status_desc} {met_desc} {must_desc} {ded_desc}"

    def _get_requirement_priority(
        self,
        requirement_id: str,
        requirements: ProcurementRequirements,
    ) -> RequirementPriority:
        """Retrieve user-configured requirement priority weight."""
        if requirement_id == "REQ_PRICING":
            return requirements.budget_priority
        elif requirement_id == "REQ_TIMELINE":
            return requirements.timeline_priority
        elif requirement_id == "REQ_SLA":
            return requirements.sla_priority
        elif requirement_id == "REQ_PAYMENT":
            return requirements.payment_priority
        elif requirement_id == "REQ_CERTIFICATIONS":
            return requirements.certifications_priority
        elif requirement_id == "REQ_WARRANTY":
            return requirements.warranty_priority
        elif requirement_id == "REQ_LIABILITY":
            return requirements.liability_priority
        elif requirement_id == "REQ_RENEWAL":
            return requirements.renewal_priority
        elif requirement_id == "REQ_TERMINATION":
            return requirements.termination_priority
        elif requirement_id == "REQ_SUPPORT":
            return requirements.support_priority
        elif requirement_id.startswith("REQ_CUSTOM_"):
            try:
                idx = int(requirement_id.split("_")[-1]) - 1
                if requirements.custom_priorities and idx < len(requirements.custom_priorities):
                    return requirements.custom_priorities[idx]
            except Exception:
                pass
        return RequirementPriority.MEDIUM
