"""Gap Detection Service for PropIQ.

Identifies information gaps (MISSING, UNCLEAR, CONFLICTING, PARTIAL, pricing ambiguities,
SLA gaps, risk clarification needs) across Phase 3 extraction results, Phase 4 comparison results,
Phase 5 risk findings, and Phase 5 contradictions. Enforces strict zero-question policy for resolved compliant facts.
"""

import hashlib
import logging
import re
from typing import Dict, List, Optional, Any, Set, Tuple
from app.models import (
    GapModel,
    ClarificationReason,
    QuestionPriority,
    EvidenceCitationModel,
    ProcurementRequirements,
    VendorFactSheet,
    RequirementEvaluationResult,
    ComparisonMatrixRow,
    RiskFindingModel,
    ContradictionFindingModel,
    RiskSeverity,
)

logger = logging.getLogger("propiq_backend")


class GapService:
    """Service handling deterministic identification and prioritization of clarification gaps returning typed GapModel instances."""

    def detect_session_gaps(
        self,
        session_id: str,
        fact_sheets: Optional[List[VendorFactSheet]] = None,
        matrix_rows: Optional[List[ComparisonMatrixRow]] = None,
        risk_findings: Optional[List[RiskFindingModel]] = None,
        contradictions: Optional[List[ContradictionFindingModel]] = None,
        requirements: Optional[ProcurementRequirements] = None,
        vendor_name_filter: Optional[str] = None,
    ) -> List[GapModel]:
        """Detect all clarification gaps for vendors in a session returning typed GapModel list (Rule 3)."""
        gaps: List[GapModel] = []

        # 1. Detect Gaps from Phase 4 Comparison Matrix (Missing, Unclear, Conflicting, Partial)
        if matrix_rows:
            comp_gaps = self._detect_comparison_matrix_gaps(session_id, matrix_rows, requirements)
            gaps.extend(comp_gaps)

        # 2. Detect Gaps from Phase 3 Fact Sheets (Ambiguities, conditional features, pricing ranges)
        if fact_sheets:
            fact_gaps = self._detect_fact_sheet_gaps(session_id, fact_sheets, requirements)
            gaps.extend(fact_gaps)

        # 3. Detect Gaps from Phase 5 Contradictions
        if contradictions:
            ctr_gaps = self._detect_contradiction_gaps(session_id, contradictions)
            gaps.extend(ctr_gaps)

        # 4. Detect Gaps from Phase 5 Contract Risks (Requirement-linked risks requiring clarification)
        if risk_findings and requirements:
            risk_gaps = self._detect_risk_linked_gaps(session_id, risk_findings, requirements)
            gaps.extend(risk_gaps)

        # Filter by vendor name if requested
        if vendor_name_filter:
            gaps = [g for g in gaps if g.vendor_name.lower() == vendor_name_filter.lower()]

        # Deduplicate overlapping gaps per vendor
        deduped = self._deduplicate_gaps(gaps)
        return deduped

    def _generate_canonical_gap_id(
        self,
        session_id: str,
        vendor_name: str,
        reason: ClarificationReason,
        target_key: str,
    ) -> str:
        """Generate deterministic gap ID from canonical identity (Rule 7)."""
        raw = f"{session_id}_{vendor_name.lower()}_{reason.value}_{target_key.lower()}"
        h = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:12]
        return f"gap_{h}"

    def _detect_comparison_matrix_gaps(
        self,
        session_id: str,
        matrix_rows: List[ComparisonMatrixRow],
        requirements: Optional[ProcurementRequirements],
    ) -> List[GapModel]:
        """Convert Phase 4 evaluation results into GapModel instances."""
        gaps: List[GapModel] = []

        for row in matrix_rows:
            for vname, eval_res in row.vendor_evaluations.items():
                status = eval_res.status

                # Rule 4: Rule out NOT_ANALYZED or ANALYSIS_FAILED
                if status in {"NOT_ANALYZED", "ANALYSIS_FAILED"}:
                    continue

                # Rule: MEETS status facts generate 0 questions!
                if status == "MEETS":
                    continue

                if status == "MISSING":
                    # Determine priority based on requirement category & user requirements
                    prio = QuestionPriority.HIGH if eval_res.requirement_id in {"REQ_PRICING", "REQ_CERTIFICATIONS", "REQ_LIABILITY"} else QuestionPriority.MEDIUM
                    if eval_res.requirement_id == "REQ_PRICING" and requirements and requirements.budget_ceiling:
                        prio = QuestionPriority.HIGH

                    reason = ClarificationReason.MISSING_REQUIREMENT
                    if eval_res.requirement_id == "REQ_CERTIFICATIONS":
                        reason = ClarificationReason.CERTIFICATION_CLARIFICATION

                    gap_id = self._generate_canonical_gap_id(session_id, vname, reason, eval_res.requirement_id)
                    gaps.append(
                        GapModel(
                            gap_id=gap_id,
                            vendor_name=vname,
                            reason=reason,
                            priority=prio,
                            source_status="MISSING",
                            requirement_id=eval_res.requirement_id,
                            requirement_label=row.requirement_label,
                            evidence_ids=[],
                            evidence_citations=[],  # Rule 5: 0 citations for MISSING/NOT_FOUND!
                            gap_summary=f"Requirement '{row.requirement_label}' is missing from proposal evidence.",
                        )
                    )

                elif status == "UNCLEAR":
                    reason = ClarificationReason.UNCLEAR_INFORMATION
                    if eval_res.requirement_id == "REQ_PRICING":
                        reason = ClarificationReason.PRICING_AMBIGUITY
                    elif eval_res.requirement_id == "REQ_SLA":
                        reason = ClarificationReason.SLA_CLARIFICATION
                    elif eval_res.requirement_id == "REQ_SUPPORT":
                        reason = ClarificationReason.SUPPORT_CLARIFICATION

                    gap_id = self._generate_canonical_gap_id(session_id, vname, reason, eval_res.requirement_id)
                    e_ids = [c.chunk_id for c in eval_res.evidence_citations if c.chunk_id]
                    gaps.append(
                        GapModel(
                            gap_id=gap_id,
                            vendor_name=vname,
                            reason=reason,
                            priority=QuestionPriority.MEDIUM if eval_res.requirement_id not in {"REQ_PRICING", "REQ_LIABILITY"} else QuestionPriority.HIGH,
                            source_status="UNCLEAR",
                            requirement_id=eval_res.requirement_id,
                            requirement_label=row.requirement_label,
                            raw_values=eval_res.raw_vendor_value,
                            evidence_ids=e_ids,
                            evidence_citations=eval_res.evidence_citations,  # Rule 5: >=1 citation for UNCLEAR
                            gap_summary=eval_res.explanation,
                        )
                    )

                elif status == "CONFLICTING":
                    gap_id = self._generate_canonical_gap_id(session_id, vname, ClarificationReason.CONFLICTING_INFORMATION, eval_res.requirement_id)
                    e_ids = [c.chunk_id for c in eval_res.evidence_citations if c.chunk_id]
                    gaps.append(
                        GapModel(
                            gap_id=gap_id,
                            vendor_name=vname,
                            reason=ClarificationReason.CONFLICTING_INFORMATION,
                            priority=QuestionPriority.HIGH,
                            source_status="CONFLICTING",
                            requirement_id=eval_res.requirement_id,
                            requirement_label=row.requirement_label,
                            raw_values=eval_res.raw_vendor_value,
                            evidence_ids=e_ids,
                            evidence_citations=eval_res.evidence_citations,  # Rule 5: >=2 citations for CONFLICTING
                            gap_summary=f"Conflicting details found regarding {row.requirement_label}.",
                        )
                    )

                elif status == "PARTIAL":
                    prio = QuestionPriority.MEDIUM
                    reason = ClarificationReason.PARTIAL_COMPLIANCE
                    if eval_res.requirement_id == "REQ_CERTIFICATIONS":
                        reason = ClarificationReason.CERTIFICATION_CLARIFICATION

                    gap_id = self._generate_canonical_gap_id(session_id, vname, reason, eval_res.requirement_id)
                    e_ids = [c.chunk_id for c in eval_res.evidence_citations if c.chunk_id]
                    gaps.append(
                        GapModel(
                            gap_id=gap_id,
                            vendor_name=vname,
                            reason=reason,
                            priority=prio,
                            source_status="PARTIAL",
                            requirement_id=eval_res.requirement_id,
                            requirement_label=row.requirement_label,
                            raw_values=eval_res.raw_vendor_value,
                            evidence_ids=e_ids,
                            evidence_citations=eval_res.evidence_citations,
                            gap_summary=eval_res.explanation,
                        )
                    )

        return gaps

    def _detect_fact_sheet_gaps(
        self,
        session_id: str,
        fact_sheets: List[VendorFactSheet],
        requirements: Optional[ProcurementRequirements],
    ) -> List[GapModel]:
        """Detect pricing range, conditional feature, and payment ambiguities from raw fact sheets."""
        gaps: List[GapModel] = []

        for sheet in fact_sheets:
            vname = sheet.vendor_name
            for cat in sheet.categories:
                val = (cat.raw_value or "").lower()
                summary = (cat.summary or "").lower()
                combined = f"{val} {summary}"

                # Pricing Ambiguities: Check price range regex or "range" FIRST before checking generic "from"
                if cat.category in {"Pricing", "Pricing Structure", "Total Price"}:
                    if re.search(r"\$\d+.*to.*\$\d+", combined) or "range" in combined:
                        gap_id = self._generate_canonical_gap_id(session_id, vname, ClarificationReason.PRICING_AMBIGUITY, "range")
                        e_ids = [c.chunk_id for c in cat.evidence_citations if c.chunk_id]
                        gaps.append(
                            GapModel(
                                gap_id=gap_id,
                                vendor_name=vname,
                                reason=ClarificationReason.PRICING_AMBIGUITY,
                                priority=QuestionPriority.HIGH,
                                source_status="UNCLEAR",
                                requirement_id="REQ_PRICING",
                                requirement_label="Pricing & Budget",
                                raw_values=cat.raw_value,
                                evidence_ids=e_ids,
                                evidence_citations=cat.evidence_citations,
                                gap_summary="Proposal lists a price range rather than a single fixed fee.",
                            )
                        )
                    elif "start" in combined or "starting" in combined or "from" in combined:
                        gap_id = self._generate_canonical_gap_id(session_id, vname, ClarificationReason.PRICING_AMBIGUITY, "starting_at")
                        e_ids = [c.chunk_id for c in cat.evidence_citations if c.chunk_id]
                        gaps.append(
                            GapModel(
                                gap_id=gap_id,
                                vendor_name=vname,
                                reason=ClarificationReason.PRICING_AMBIGUITY,
                                priority=QuestionPriority.HIGH if requirements and requirements.budget_ceiling else QuestionPriority.MEDIUM,
                                source_status="UNCLEAR",
                                requirement_id="REQ_PRICING",
                                requirement_label="Pricing & Budget",
                                raw_values=cat.raw_value,
                                evidence_ids=e_ids,
                                evidence_citations=cat.evidence_citations,
                                gap_summary="Proposal lists 'starting at' pricing rather than fixed total cost.",
                            )
                        )
                    elif "implementation" not in combined and "onboarding" not in combined:
                        if cat.status == "FOUND":
                            gap_id = self._generate_canonical_gap_id(session_id, vname, ClarificationReason.PRICING_AMBIGUITY, "impl_fee")
                            e_ids = [c.chunk_id for c in cat.evidence_citations if c.chunk_id]
                            gaps.append(
                                GapModel(
                                    gap_id=gap_id,
                                    vendor_name=vname,
                                    reason=ClarificationReason.PRICING_AMBIGUITY,
                                    priority=QuestionPriority.MEDIUM,
                                    source_status="UNCLEAR",
                                    requirement_id="REQ_PRICING",
                                    requirement_label="Pricing & Budget",
                                    raw_values=cat.raw_value,
                                    evidence_ids=e_ids,
                                    evidence_citations=cat.evidence_citations,
                                    gap_summary="Proposal lists subscription price but does not specify whether implementation or onboarding fees apply.",
                                )
                            )

                # Conditional Feature Gaps: 24/7 support available only under Premium
                if cat.category in {"Support / SLA", "Support Hours"} and ("premium" in combined or "add-on" in combined or "tier" in combined):
                    if requirements and requirements.support_requirement:
                        gap_id = self._generate_canonical_gap_id(session_id, vname, ClarificationReason.CONDITIONAL_FEATURE, "support_tier")
                        e_ids = [c.chunk_id for c in cat.evidence_citations if c.chunk_id]
                        gaps.append(
                            GapModel(
                                gap_id=gap_id,
                                vendor_name=vname,
                                reason=ClarificationReason.CONDITIONAL_FEATURE,
                                priority=QuestionPriority.MEDIUM,
                                source_status="UNCLEAR",
                                requirement_id="REQ_SUPPORT",
                                requirement_label="Support Availability",
                                raw_values=cat.raw_value,
                                evidence_ids=e_ids,
                                evidence_citations=cat.evidence_citations,
                                gap_summary="24/7 or critical support appears restricted to a higher support tier or paid add-on.",
                            )
                        )

                # Payment Clarifications: "to be agreed" or upfront milestone missing
                if cat.category in {"Payment Terms", "Payment Schedule"} and ("agreed" in combined or "tbd" in combined or "upfront" in combined):
                    gap_id = self._generate_canonical_gap_id(session_id, vname, ClarificationReason.PAYMENT_CLARIFICATION, "payment_schedule")
                    e_ids = [c.chunk_id for c in cat.evidence_citations if c.chunk_id]
                    gaps.append(
                        GapModel(
                            gap_id=gap_id,
                            vendor_name=vname,
                            reason=ClarificationReason.PAYMENT_CLARIFICATION,
                            priority=QuestionPriority.MEDIUM,
                            source_status="UNCLEAR",
                            requirement_id="REQ_PAYMENT",
                            requirement_label="Payment Terms",
                            raw_values=cat.raw_value,
                            evidence_ids=e_ids,
                            evidence_citations=cat.evidence_citations,
                            gap_summary="Payment schedule or invoice terms require explicit milestone definition.",
                        )
                    )

        return gaps

    def _detect_contradiction_gaps(
        self,
        session_id: str,
        contradictions: List[ContradictionFindingModel],
    ) -> List[GapModel]:
        """Convert Phase 5 intra-vendor contradictions into GapModel instances (Rule 5: Dual evidence preserved!)."""
        gaps: List[GapModel] = []

        for ctr in contradictions:
            if ctr.status in {"CONFIRMED_CONTRADICTION", "POTENTIAL_CONTRADICTION"}:
                cits = (ctr.evidence_a or []) + (ctr.evidence_b or [])
                e_ids = [c.chunk_id for c in cits if c.chunk_id]
                gap_id = self._generate_canonical_gap_id(session_id, ctr.vendor_name, ClarificationReason.CONFLICTING_INFORMATION, ctr.contradiction_id)

                gaps.append(
                    GapModel(
                        gap_id=gap_id,
                        vendor_name=ctr.vendor_name,
                        reason=ClarificationReason.CONFLICTING_INFORMATION,
                        priority=QuestionPriority.HIGH,
                        source_status="CONFLICTING",
                        related_contradiction_id=ctr.contradiction_id,
                        raw_values=f"Statement A: {ctr.statement_a} | Statement B: {ctr.statement_b}",
                        evidence_ids=e_ids,
                        evidence_citations=cits,  # Rule 5: Preserves evidence from BOTH sides!
                        gap_summary=f"Inconsistent claims found regarding {ctr.category}: Statement A ({ctr.context_a}) vs Statement B ({ctr.context_b}).",
                    )
                )

        return gaps

    def _detect_risk_linked_gaps(
        self,
        session_id: str,
        risk_findings: List[RiskFindingModel],
        requirements: ProcurementRequirements,
    ) -> List[GapModel]:
        """Convert requirement-linked Phase 5 contract risks into GapModel instances (Rule 9: Requires requirement intersection!)."""
        gaps: List[GapModel] = []

        for r in risk_findings:
            # Rule 9: Do NOT generate clarification merely because risk exists unless requirement conflicts/intersects!
            if r.severity in {RiskSeverity.HIGH, RiskSeverity.CRITICAL} and r.related_requirement_ids:
                req_id = r.related_requirement_ids[0]
                reason = ClarificationReason.RISK_CLARIFICATION

                if r.category.value == "AUTO_RENEWAL":
                    reason = ClarificationReason.RENEWAL_CLARIFICATION
                elif r.category.value in {"TERMINATION_RESTRICTION", "EARLY_TERMINATION_FEE"}:
                    reason = ClarificationReason.TERMINATION_CLARIFICATION
                elif r.category.value in {"LIABILITY_CAP", "UNCAPPED_LIABILITY"}:
                    reason = ClarificationReason.OTHER_REVIEW_REQUIRED

                gap_id = self._generate_canonical_gap_id(session_id, r.vendor_name, reason, r.risk_id)
                e_ids = [c.chunk_id for c in r.evidence_citations if c.chunk_id]

                gaps.append(
                    GapModel(
                        gap_id=gap_id,
                        vendor_name=r.vendor_name,
                        reason=reason,
                        priority=QuestionPriority.HIGH,
                        source_status="RISK_LINKED",
                        requirement_id=req_id,
                        related_risk_id=r.risk_id,
                        evidence_ids=e_ids,
                        evidence_citations=r.evidence_citations,
                        gap_summary=f"High contractual concern detected ({r.title}). Clarification needed to confirm alternative options.",
                    )
                )

        return gaps

    def _deduplicate_gaps(self, gaps: List[GapModel]) -> List[GapModel]:
        """Deduplicate overlapping clarification gaps per vendor."""
        deduped: List[GapModel] = []
        seen_keys: Set[Tuple[str, str, str]] = set()

        for g in gaps:
            key = (g.vendor_name.lower(), g.reason.value, (g.requirement_id or g.gap_id).lower())
            if key not in seen_keys:
                seen_keys.add(key)
                deduped.append(g)

        return deduped
