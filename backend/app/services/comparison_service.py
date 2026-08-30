"""Deterministic requirement comparison service module for PropIQ.

Executes Python inequality and matching rules comparing normalized vendor proposal facts
against procurement requirements. Evaluates controlled states: MEETS, PARTIAL, FAILS,
MISSING, UNCLEAR, CONFLICTING with deterministic natural-language explanations.
"""

import logging
from typing import Dict, List, Optional, Any
from app.models import (
    ProcurementRequirements,
    VendorFactSheet,
    CategoryExtractionResult,
    EvidenceCitationModel,
    RequirementEvaluationResult,
    ComparisonMatrixRow,
    ComparisonResponse,
    NormalizedValueModel,
)
from app.config import Config
from app.services.normalization_service import NormalizationService

logger = logging.getLogger("propiq_backend")


class ComparisonService:
    """Service handling deterministic requirement comparison and matrix generation."""

    def __init__(self, normalizer: Optional[NormalizationService] = None):
        self.normalizer = normalizer or NormalizationService()

    def evaluate_session_comparison(
        self,
        session_id: str,
        requirements: ProcurementRequirements,
        fact_sheets: List[VendorFactSheet],
    ) -> ComparisonResponse:
        """Evaluate procurement requirements deterministically across all vendors in session.

        Args:
            session_id: Active session identifier.
            requirements: ProcurementRequirements object.
            fact_sheets: List of VendorFactSheet objects from Phase 3.

        Returns:
            ComparisonResponse containing matrix rows and factual status counts.
        """
        vendors = [fs.vendor_name for fs in fact_sheets]
        matrix_rows: List[ComparisonMatrixRow] = []

        # Vendor factual status counters
        summary_counts: Dict[str, Dict[str, int]] = {
            vname: {"MEETS": 0, "PARTIAL": 0, "FAILS": 0, "MISSING": 0, "UNCLEAR": 0, "CONFLICTING": 0}
            for vname in vendors
        }

        # 1. Budget Ceiling Requirement
        if requirements.budget_ceiling is not None:
            row = self._evaluate_budget_requirement(requirements, fact_sheets)
            matrix_rows.append(row)
            self._update_summary_counts(row, summary_counts)

        # 2. Timeline Requirement
        if requirements.timeline_value is not None:
            row = self._evaluate_timeline_requirement(requirements, fact_sheets)
            matrix_rows.append(row)
            self._update_summary_counts(row, summary_counts)

        # 3. Minimum SLA Requirement
        if requirements.minimum_sla is not None:
            row = self._evaluate_sla_requirement(requirements, fact_sheets)
            matrix_rows.append(row)
            self._update_summary_counts(row, summary_counts)

        # 4. Payment Terms Requirement
        if requirements.payment_terms:
            row = self._evaluate_payment_requirement(requirements, fact_sheets)
            matrix_rows.append(row)
            self._update_summary_counts(row, summary_counts)

        # 5. Required Certifications
        if requirements.certifications:
            row = self._evaluate_certifications_requirement(requirements, fact_sheets)
            matrix_rows.append(row)
            self._update_summary_counts(row, summary_counts)

        # 6. Warranty Requirement
        if requirements.warranty_value is not None:
            row = self._evaluate_warranty_requirement(requirements, fact_sheets)
            matrix_rows.append(row)
            self._update_summary_counts(row, summary_counts)

        # 7. Liability Cap Requirement
        if requirements.liability_requirement:
            row = self._evaluate_liability_requirement(requirements, fact_sheets)
            matrix_rows.append(row)
            self._update_summary_counts(row, summary_counts)

        # 8. Renewal Preference
        if requirements.renewal_preference:
            row = self._evaluate_renewal_requirement(requirements, fact_sheets)
            matrix_rows.append(row)
            self._update_summary_counts(row, summary_counts)

        # 9. Termination Requirement
        if requirements.termination_requirement:
            row = self._evaluate_termination_requirement(requirements, fact_sheets)
            matrix_rows.append(row)
            self._update_summary_counts(row, summary_counts)

        # 10. Support Requirement
        if requirements.support_requirement:
            row = self._evaluate_support_requirement(requirements, fact_sheets)
            matrix_rows.append(row)
            self._update_summary_counts(row, summary_counts)

        # 11. Custom Requirements
        for idx, custom_req in enumerate(requirements.custom_requirements):
            if custom_req.strip():
                row = self._evaluate_custom_requirement(custom_req.strip(), idx + 1, fact_sheets)
                matrix_rows.append(row)
                self._update_summary_counts(row, summary_counts)

        return ComparisonResponse(
            status="success",
            session_id=session_id,
            requirements=requirements,
            matrix_rows=matrix_rows,
            vendor_summary_counts=summary_counts,
            privacy_notice=Config.PRIVACY_NOTICE,
        )

    def _update_summary_counts(self, row: ComparisonMatrixRow, summary_counts: Dict[str, Dict[str, int]]):
        """Update vendor status summary counters."""
        for vname, res in row.vendor_evaluations.items():
            if vname in summary_counts:
                st = res.status
                if st in summary_counts[vname]:
                    summary_counts[vname][st] += 1

    def _get_category_result(self, fact_sheet: VendorFactSheet, category_name: str) -> Optional[CategoryExtractionResult]:
        """Find CategoryExtractionResult in VendorFactSheet matching category_name."""
        for cat in fact_sheet.categories:
            if cat.category == category_name or cat.category.startswith(category_name):
                return cat
        return None

    # --- Evaluation Handlers ---

    def _evaluate_budget_requirement(self, reqs: ProcurementRequirements, fact_sheets: List[VendorFactSheet]) -> ComparisonMatrixRow:
        evals: Dict[str, RequirementEvaluationResult] = {}
        ceiling = reqs.budget_ceiling
        req_curr = reqs.budget_currency or "USD"
        label = f"Budget Ceiling <= {req_curr} {ceiling:,.2f}"

        for fs in fact_sheets:
            cat_res = self._get_category_result(fs, "Pricing")
            if not cat_res or cat_res.status == "NOT_FOUND":
                evals[fs.vendor_name] = self._make_missing_res("REQ_PRICING", "Pricing", fs.vendor_name, cat_res)
                continue
            if cat_res.status == "UNCLEAR":
                evals[fs.vendor_name] = self._make_unclear_res("REQ_PRICING", "Pricing", fs.vendor_name, cat_res)
                continue
            if cat_res.status == "CONFLICTING":
                evals[fs.vendor_name] = self._make_conflicting_res("REQ_PRICING", "Pricing", fs.vendor_name, cat_res)
                continue

            # FOUND state -> Normalize pricing
            norm = self.normalizer.normalize_pricing(cat_res.raw_value)
            if not norm.normalized_value or not isinstance(norm.normalized_value, dict):
                evals[fs.vendor_name] = RequirementEvaluationResult(
                    requirement_id="REQ_PRICING",
                    category="Pricing",
                    vendor_name=fs.vendor_name,
                    status="UNCLEAR",
                    raw_vendor_value=cat_res.raw_value,
                    explanation="Pricing details could not be parsed into a numeric amount.",
                    evidence_citations=cat_res.evidence_citations,
                    comparison_rule="vendor_annual_cost <= budget_ceiling",
                    normalization_status=norm.normalization_status,
                )
                continue

            v_curr = norm.normalized_value.get("currency", "USD")
            v_cost = norm.normalized_value.get("annual_amount")

            # Currency mismatch check (No live FX rates)
            if v_curr != req_curr:
                evals[fs.vendor_name] = RequirementEvaluationResult(
                    requirement_id="REQ_PRICING",
                    category="Pricing",
                    vendor_name=fs.vendor_name,
                    status="UNCLEAR",
                    raw_vendor_value=cat_res.raw_value,
                    normalized_vendor_value=f"{v_curr} {v_cost:,.2f}",
                    normalized_unit=v_curr,
                    explanation=f"Currency mismatch ({v_curr} vs required {req_curr}): conversion required before comparison.",
                    evidence_citations=cat_res.evidence_citations,
                    comparison_rule="vendor_currency == required_currency",
                    normalization_status=norm.normalization_status,
                )
                continue

            if v_cost <= ceiling:
                explanation = f"Vendor annual cost of {v_curr} {v_cost:,.2f} meets the budget ceiling of {req_curr} {ceiling:,.2f}."
                status_val = "MEETS"
            else:
                explanation = f"Vendor annual cost of {v_curr} {v_cost:,.2f} exceeds the budget ceiling of {req_curr} {ceiling:,.2f}."
                status_val = "FAILS"

            evals[fs.vendor_name] = RequirementEvaluationResult(
                requirement_id="REQ_PRICING",
                category="Pricing",
                vendor_name=fs.vendor_name,
                status=status_val,
                raw_vendor_value=cat_res.raw_value,
                normalized_vendor_value=f"{v_curr} {v_cost:,.2f}",
                normalized_unit=v_curr,
                explanation=explanation,
                evidence_citations=cat_res.evidence_citations,
                comparison_rule=f"vendor_cost ({v_cost}) <= budget_ceiling ({ceiling})",
                normalization_status=norm.normalization_status,
            )

        return ComparisonMatrixRow(
            category="Pricing",
            requirement_label=label,
            requirement_name="Budget Ceiling",
            buyer_target_summary=f"<= {req_curr} {ceiling:,.2f}",
            vendor_evaluations=evals,
        )

    def _evaluate_timeline_requirement(self, reqs: ProcurementRequirements, fact_sheets: List[VendorFactSheet]) -> ComparisonMatrixRow:
        evals: Dict[str, RequirementEvaluationResult] = {}
        target_val = reqs.timeline_value
        target_unit = reqs.timeline_unit or "days"
        
        # Max bound implementation requirement
        max_days = target_val * (30.4375 if target_unit == "months" else 7.0 if target_unit == "weeks" else 1.0)
        label = f"Maximum Timeline <= {target_val} {target_unit}"

        for fs in fact_sheets:
            cat_res = self._get_category_result(fs, "Delivery / Implementation")
            if not cat_res or cat_res.status == "NOT_FOUND":
                evals[fs.vendor_name] = self._make_missing_res("REQ_TIMELINE", "Delivery / Implementation", fs.vendor_name, cat_res)
                continue
            if cat_res.status == "UNCLEAR":
                evals[fs.vendor_name] = self._make_unclear_res("REQ_TIMELINE", "Delivery / Implementation", fs.vendor_name, cat_res)
                continue
            if cat_res.status == "CONFLICTING":
                evals[fs.vendor_name] = self._make_conflicting_res("REQ_TIMELINE", "Delivery / Implementation", fs.vendor_name, cat_res)
                continue

            norm = self.normalizer.normalize_duration(cat_res.raw_value)
            if norm.normalized_value is None:
                evals[fs.vendor_name] = RequirementEvaluationResult(
                    requirement_id="REQ_TIMELINE",
                    category="Delivery / Implementation",
                    vendor_name=fs.vendor_name,
                    status="UNCLEAR",
                    raw_vendor_value=cat_res.raw_value,
                    explanation="Implementation timeline could not be parsed into a duration.",
                    evidence_citations=cat_res.evidence_citations,
                    comparison_rule="vendor_days <= max_days",
                    normalization_status=norm.normalization_status,
                )
                continue

            # Handle range vs single value
            if isinstance(norm.normalized_value, dict):
                min_d = norm.normalized_value.get("min", 0)
                max_d = norm.normalized_value.get("max", 0)
                if max_d <= max_days:
                    st = "MEETS"
                    exp = f"Vendor timeline range ({cat_res.raw_value}) falls within maximum requirement of {target_val} {target_unit}."
                elif min_d <= max_days:
                    st = "PARTIAL"
                    exp = f"Vendor timeline range ({cat_res.raw_value}) partially exceeds maximum requirement of {target_val} {target_unit}."
                else:
                    st = "FAILS"
                    exp = f"Vendor timeline range ({cat_res.raw_value}) exceeds maximum requirement of {target_val} {target_unit}."
                
                evals[fs.vendor_name] = RequirementEvaluationResult(
                    requirement_id="REQ_TIMELINE",
                    category="Delivery / Implementation",
                    vendor_name=fs.vendor_name,
                    status=st,
                    raw_vendor_value=cat_res.raw_value,
                    normalized_vendor_value=f"{max_d} days max",
                    normalized_unit="days",
                    explanation=exp,
                    evidence_citations=cat_res.evidence_citations,
                    comparison_rule=f"vendor_max_days ({max_d}) <= max_days ({max_days})",
                    normalization_status=norm.normalization_status,
                )
            else:
                v_days = norm.normalized_value
                if norm.normalized_unit == "months":
                    v_days_calc = v_days * 30.4375
                    disp_norm = f"{v_days} months"
                else:
                    v_days_calc = v_days
                    disp_norm = f"{v_days} days"

                if v_days_calc <= max_days:
                    st = "MEETS"
                    exp = f"{cat_res.raw_value} equals {disp_norm}, matching the maximum allowed implementation timeline of {target_val} {target_unit}."
                else:
                    st = "FAILS"
                    exp = f"Vendor implementation timeline is {disp_norm}, exceeding the maximum requirement of {target_val} {target_unit}."

                evals[fs.vendor_name] = RequirementEvaluationResult(
                    requirement_id="REQ_TIMELINE",
                    category="Delivery / Implementation",
                    vendor_name=fs.vendor_name,
                    status=st,
                    raw_vendor_value=cat_res.raw_value,
                    normalized_vendor_value=disp_norm,
                    normalized_unit="days",
                    explanation=exp,
                    evidence_citations=cat_res.evidence_citations,
                    comparison_rule=f"vendor_days ({v_days_calc}) <= max_days ({max_days})",
                    normalization_status=norm.normalization_status,
                )

        return ComparisonMatrixRow(
            category="Delivery / Implementation",
            requirement_label=label,
            requirement_name="Deployment Timeline",
            buyer_target_summary=f"<= {target_val} {target_unit}",
            vendor_evaluations=evals,
        )

    def _evaluate_sla_requirement(self, reqs: ProcurementRequirements, fact_sheets: List[VendorFactSheet]) -> ComparisonMatrixRow:
        evals: Dict[str, RequirementEvaluationResult] = {}
        min_sla = reqs.minimum_sla
        label = f"Minimum SLA >= {min_sla}% Uptime"

        for fs in fact_sheets:
            cat_res = self._get_category_result(fs, "SLA / Uptime")
            if not cat_res or cat_res.status == "NOT_FOUND":
                evals[fs.vendor_name] = self._make_missing_res("REQ_SLA", "SLA / Uptime", fs.vendor_name, cat_res)
                continue
            if cat_res.status == "UNCLEAR":
                evals[fs.vendor_name] = self._make_unclear_res("REQ_SLA", "SLA / Uptime", fs.vendor_name, cat_res)
                continue
            if cat_res.status == "CONFLICTING":
                evals[fs.vendor_name] = self._make_conflicting_res("REQ_SLA", "SLA / Uptime", fs.vendor_name, cat_res)
                continue

            norm = self.normalizer.normalize_sla(cat_res.raw_value)
            v_sla = norm.normalized_value

            if v_sla is None or not isinstance(v_sla, (int, float)):
                evals[fs.vendor_name] = RequirementEvaluationResult(
                    requirement_id="REQ_SLA",
                    category="SLA / Uptime",
                    vendor_name=fs.vendor_name,
                    status="UNCLEAR",
                    raw_vendor_value=cat_res.raw_value,
                    explanation="SLA detail could not be parsed into a numeric percentage.",
                    evidence_citations=cat_res.evidence_citations,
                    comparison_rule="vendor_sla >= minimum_sla",
                    normalization_status=norm.normalization_status,
                )
                continue

            if v_sla >= min_sla:
                st = "MEETS"
                exp = f"Vendor offers {v_sla}% uptime, meeting the minimum required SLA of {min_sla}%."
            else:
                st = "FAILS"
                exp = f"Vendor offers {v_sla}% uptime, failing the minimum requirement of {min_sla}%."

            evals[fs.vendor_name] = RequirementEvaluationResult(
                requirement_id="REQ_SLA",
                category="SLA / Uptime",
                vendor_name=fs.vendor_name,
                status=st,
                raw_vendor_value=cat_res.raw_value,
                normalized_vendor_value=f"{v_sla}%",
                normalized_unit="percent_uptime",
                explanation=exp,
                evidence_citations=cat_res.evidence_citations,
                comparison_rule=f"vendor_sla ({v_sla}) >= minimum_sla ({min_sla})",
                normalization_status=norm.normalization_status,
            )

        return ComparisonMatrixRow(
            category="SLA / Uptime",
            requirement_label=label,
            requirement_name="Uptime SLA",
            buyer_target_summary=f">= {min_sla}%",
            vendor_evaluations=evals,
        )

    def _evaluate_payment_requirement(self, reqs: ProcurementRequirements, fact_sheets: List[VendorFactSheet]) -> ComparisonMatrixRow:
        evals: Dict[str, RequirementEvaluationResult] = {}
        req_text = reqs.payment_terms
        norm_req = self.normalizer.normalize_payment_terms(req_text)
        req_due = norm_req.normalized_value.get("due_days", 30) if (norm_req.normalized_value and isinstance(norm_req.normalized_value, dict)) else 30
        label = f"Payment Terms: {req_text}"

        for fs in fact_sheets:
            cat_res = self._get_category_result(fs, "Payment Terms")
            if not cat_res or cat_res.status == "NOT_FOUND":
                evals[fs.vendor_name] = self._make_missing_res("REQ_PAYMENT", "Payment Terms", fs.vendor_name, cat_res)
                continue
            if cat_res.status == "UNCLEAR":
                evals[fs.vendor_name] = self._make_unclear_res("REQ_PAYMENT", "Payment Terms", fs.vendor_name, cat_res)
                continue
            if cat_res.status == "CONFLICTING":
                evals[fs.vendor_name] = self._make_conflicting_res("REQ_PAYMENT", "Payment Terms", fs.vendor_name, cat_res)
                continue

            norm = self.normalizer.normalize_payment_terms(cat_res.raw_value)
            if not norm.normalized_value or not isinstance(norm.normalized_value, dict):
                evals[fs.vendor_name] = RequirementEvaluationResult(
                    requirement_id="REQ_PAYMENT",
                    category="Payment Terms",
                    vendor_name=fs.vendor_name,
                    status="UNCLEAR",
                    raw_vendor_value=cat_res.raw_value,
                    explanation="Payment terms wording is unstructured.",
                    evidence_citations=cat_res.evidence_citations,
                    comparison_rule="vendor_due_days >= required_due_days",
                    normalization_status=norm.normalization_status,
                )
                continue

            v_due = norm.normalized_value.get("due_days", 0)
            v_uf = norm.normalized_value.get("upfront_percentage", 0.0)

            # Buyer Perspective Rule: Upfront payments violate Net due terms; longer payment terms (higher due days) favor buyer cash flow!
            if v_uf > 0:
                st = "FAILS"
                exp = f"Vendor requires {v_uf}% upfront payment, violating required {req_text} terms."
            elif v_due > 0 and v_due >= req_due:
                st = "MEETS"
                exp = f"Vendor Net {v_due} terms meet or exceed required Net {req_due} terms."
            elif v_due > 0:
                st = "FAILS"
                exp = f"Vendor Net {v_due} terms provide shorter payment window than required Net {req_due}."
            else:
                st = "UNCLEAR"
                exp = f"Vendor specifies payment arrangement ('{cat_res.raw_value}'), but explicit Net payment due days are not specified in evidence."

            evals[fs.vendor_name] = RequirementEvaluationResult(
                requirement_id="REQ_PAYMENT",
                category="Payment Terms",
                vendor_name=fs.vendor_name,
                status=st,
                raw_vendor_value=cat_res.raw_value,
                normalized_vendor_value=f"Net {v_due}" if v_due > 0 else f"{v_uf}% upfront" if v_uf > 0 else cat_res.raw_value,
                normalized_unit="days",
                explanation=exp,
                evidence_citations=cat_res.evidence_citations,
                comparison_rule=f"vendor_due_days ({v_due}) >= required_due_days ({req_due})",
                normalization_status=norm.normalization_status,
            )

        return ComparisonMatrixRow(
            category="Payment Terms",
            requirement_label=label,
            requirement_name="Payment Terms",
            buyer_target_summary=reqs.payment_terms,
            vendor_evaluations=evals,
        )

    def _evaluate_certifications_requirement(self, reqs: ProcurementRequirements, fact_sheets: List[VendorFactSheet]) -> ComparisonMatrixRow:
        evals: Dict[str, RequirementEvaluationResult] = {}
        req_certs = [c.strip() for c in reqs.certifications if c.strip()]
        norm_req_set = set(self.normalizer.normalize_certifications(", ".join(req_certs)).normalized_value or [])
        label = f"Certifications: {', '.join(req_certs)}"

        for fs in fact_sheets:
            cat_res = self._get_category_result(fs, "Certifications")
            if not cat_res or cat_res.status == "NOT_FOUND":
                evals[fs.vendor_name] = self._make_missing_res("REQ_CERTS", "Certifications", fs.vendor_name, cat_res)
                continue
            if cat_res.status == "UNCLEAR":
                evals[fs.vendor_name] = self._make_unclear_res("REQ_CERTS", "Certifications", fs.vendor_name, cat_res)
                continue
            if cat_res.status == "CONFLICTING":
                evals[fs.vendor_name] = self._make_conflicting_res("REQ_CERTS", "Certifications", fs.vendor_name, cat_res)
                continue

            norm = self.normalizer.normalize_certifications(cat_res.raw_value)
            v_certs = set(norm.normalized_value or [])

            # Deterministic certification state decision matrix:
            # - all required certifications confirmed -> MEETS
            # - at least one confirmed and remaining required unstated/planned/absent -> PARTIAL
            # - none confirmed and one or more explicitly absent -> FAILS
            # - none mentioned -> MISSING (handled above by NOT_FOUND)
            if norm_req_set.issubset(v_certs):
                st = "MEETS"
                exp = f"All required certifications confirmed ({', '.join(sorted(list(norm_req_set)))})."
            elif norm_req_set.intersection(v_certs):
                st = "PARTIAL"
                matched = ", ".join(sorted(list(norm_req_set.intersection(v_certs))))
                missing = ", ".join(sorted(list(norm_req_set - v_certs)))
                exp = f"Vendor confirms {matched}, but required {missing} are unstated or unconfirmed."
            elif v_certs:
                # Vendor holds other certifications (e.g. ISO 9001), but none of the required ones (SOC 2, ISO 27001)
                st = "FAILS"
                exp = f"Vendor possesses certifications ({', '.join(sorted(list(v_certs)))}), but none of the required certifications ({', '.join(req_certs)})."
            else:
                st = "FAILS"
                exp = f"Vendor does not possess required certifications ({', '.join(req_certs)})."

            evals[fs.vendor_name] = RequirementEvaluationResult(
                requirement_id="REQ_CERTS",
                category="Certifications",
                vendor_name=fs.vendor_name,
                status=st,
                raw_vendor_value=cat_res.raw_value,
                normalized_vendor_value=", ".join(sorted(list(v_certs))) if v_certs else "None",
                normalized_unit="certifications",
                explanation=exp,
                evidence_citations=cat_res.evidence_citations,
                comparison_rule="required_certs.issubset(vendor_certs)",
                normalization_status=norm.normalization_status,
            )

        return ComparisonMatrixRow(
            category="Certifications",
            requirement_label=label,
            requirement_name="Security Certifications",
            buyer_target_summary=", ".join(req_certs),
            vendor_evaluations=evals,
        )

    def _evaluate_warranty_requirement(self, reqs: ProcurementRequirements, fact_sheets: List[VendorFactSheet]) -> ComparisonMatrixRow:
        evals: Dict[str, RequirementEvaluationResult] = {}
        target_val = reqs.warranty_value
        target_unit = reqs.warranty_unit or "months"
        min_months = target_val * (12.0 if target_unit == "years" else 1.0)
        label = f"Minimum Warranty >= {target_val} {target_unit}"

        for fs in fact_sheets:
            cat_res = self._get_category_result(fs, "Warranty")
            if not cat_res or cat_res.status == "NOT_FOUND":
                evals[fs.vendor_name] = self._make_missing_res("REQ_WARRANTY", "Warranty", fs.vendor_name, cat_res)
                continue
            if cat_res.status == "UNCLEAR":
                evals[fs.vendor_name] = self._make_unclear_res("REQ_WARRANTY", "Warranty", fs.vendor_name, cat_res)
                continue
            if cat_res.status == "CONFLICTING":
                evals[fs.vendor_name] = self._make_conflicting_res("REQ_WARRANTY", "Warranty", fs.vendor_name, cat_res)
                continue

            norm = self.normalizer.normalize_warranty(cat_res.raw_value)
            v_val = norm.normalized_value

            if v_val is None or not isinstance(v_val, (int, float)):
                evals[fs.vendor_name] = RequirementEvaluationResult(
                    requirement_id="REQ_WARRANTY",
                    category="Warranty",
                    vendor_name=fs.vendor_name,
                    status="UNCLEAR",
                    raw_vendor_value=cat_res.raw_value,
                    explanation="Warranty wording does not specify a clear numeric duration.",
                    evidence_citations=cat_res.evidence_citations,
                    comparison_rule="vendor_months >= min_months",
                    normalization_status=norm.normalization_status,
                )
                continue

            v_months = v_val * (12.0 if norm.normalized_unit == "years" else 1.0)

            if v_months >= min_months:
                st = "MEETS"
                exp = f"Vendor warranty of {v_val} {norm.normalized_unit} meets the minimum required warranty of {target_val} {target_unit}."
            else:
                st = "FAILS"
                exp = f"Vendor warranty of {v_val} {norm.normalized_unit} fails the minimum required warranty of {target_val} {target_unit}."

            evals[fs.vendor_name] = RequirementEvaluationResult(
                requirement_id="REQ_WARRANTY",
                category="Warranty",
                vendor_name=fs.vendor_name,
                status=st,
                raw_vendor_value=cat_res.raw_value,
                normalized_vendor_value=f"{v_val} {norm.normalized_unit}",
                normalized_unit=norm.normalized_unit,
                explanation=exp,
                evidence_citations=cat_res.evidence_citations,
                comparison_rule=f"vendor_months ({v_months}) >= min_months ({min_months})",
                normalization_status=norm.normalization_status,
            )

        return ComparisonMatrixRow(
            category="Warranty",
            requirement_label=label,
            requirement_name="Warranty Period",
            buyer_target_summary=f">= {target_val} {target_unit}",
            vendor_evaluations=evals,
        )

    def _evaluate_liability_requirement(self, reqs: ProcurementRequirements, fact_sheets: List[VendorFactSheet]) -> ComparisonMatrixRow:
        return self._evaluate_textual_requirement("REQ_LIABILITY", "Liability", reqs.liability_requirement, fact_sheets)

    def _evaluate_renewal_requirement(self, reqs: ProcurementRequirements, fact_sheets: List[VendorFactSheet]) -> ComparisonMatrixRow:
        evals: Dict[str, RequirementEvaluationResult] = {}
        pref = reqs.renewal_preference
        no_auto = "no auto" in pref.lower() or "manual" in pref.lower()
        label = f"Renewal Preference: {pref}"

        for fs in fact_sheets:
            cat_res = self._get_category_result(fs, "Renewal")
            if not cat_res or cat_res.status == "NOT_FOUND":
                evals[fs.vendor_name] = self._make_missing_res("REQ_RENEWAL", "Renewal", fs.vendor_name, cat_res)
                continue
            if cat_res.status == "UNCLEAR":
                evals[fs.vendor_name] = self._make_unclear_res("REQ_RENEWAL", "Renewal", fs.vendor_name, cat_res)
                continue
            if cat_res.status == "CONFLICTING":
                evals[fs.vendor_name] = self._make_conflicting_res("REQ_RENEWAL", "Renewal", fs.vendor_name, cat_res)
                continue

            norm = self.normalizer.normalize_renewal(cat_res.raw_value)
            ren_type = norm.normalized_value.get("renewal_type") if (norm.normalized_value and isinstance(norm.normalized_value, dict)) else "unclear"

            if no_auto:
                if ren_type == "manual":
                    st = "MEETS"
                    exp = "Vendor specifies manual renewal, matching no auto-renewal preference."
                elif ren_type == "automatic":
                    st = "FAILS"
                    exp = "Vendor specifies automatic annual renewal, violating no auto-renewal preference."
                else:
                    st = "UNCLEAR"
                    exp = "Vendor renewal terms are subject to agreement."
            else:
                st = "MEETS"
                exp = f"Vendor renewal clause: {cat_res.raw_value}"

            evals[fs.vendor_name] = RequirementEvaluationResult(
                requirement_id="REQ_RENEWAL",
                category="Renewal",
                vendor_name=fs.vendor_name,
                status=st,
                raw_vendor_value=cat_res.raw_value,
                normalized_vendor_value=ren_type.capitalize(),
                normalized_unit="renewal_type",
                explanation=exp,
                evidence_citations=cat_res.evidence_citations,
                comparison_rule="vendor_renewal_type == required_renewal_type",
                normalization_status=norm.normalization_status,
            )

        return ComparisonMatrixRow(
            category="Renewal",
            requirement_label=label,
            requirement_name="Renewal Terms",
            buyer_target_summary=pref,
            vendor_evaluations=evals,
        )

    def _evaluate_termination_requirement(self, reqs: ProcurementRequirements, fact_sheets: List[VendorFactSheet]) -> ComparisonMatrixRow:
        evals: Dict[str, RequirementEvaluationResult] = {}
        req_text = reqs.termination_requirement
        for_convenience_req = "convenience" in req_text.lower()
        label = f"Termination: {req_text}"

        for fs in fact_sheets:
            cat_res = self._get_category_result(fs, "Termination / Exit")
            if not cat_res or cat_res.status == "NOT_FOUND":
                evals[fs.vendor_name] = self._make_missing_res("REQ_TERMINATION", "Termination / Exit", fs.vendor_name, cat_res)
                continue
            if cat_res.status == "UNCLEAR":
                evals[fs.vendor_name] = self._make_unclear_res("REQ_TERMINATION", "Termination / Exit", fs.vendor_name, cat_res)
                continue
            if cat_res.status == "CONFLICTING":
                evals[fs.vendor_name] = self._make_conflicting_res("REQ_TERMINATION", "Termination / Exit", fs.vendor_name, cat_res)
                continue

            norm = self.normalizer.normalize_termination(cat_res.raw_value)
            conv_perm = norm.normalized_value.get("termination_for_convenience", False) if (norm.normalized_value and isinstance(norm.normalized_value, dict)) else False

            if for_convenience_req:
                if conv_perm:
                    st = "MEETS"
                    exp = "Vendor permits termination for convenience."
                else:
                    st = "FAILS"
                    exp = "Vendor permits termination for material breach only, failing convenience requirement."
            else:
                st = "MEETS"
                exp = f"Vendor termination clause: {cat_res.raw_value}"

            evals[fs.vendor_name] = RequirementEvaluationResult(
                requirement_id="REQ_TERMINATION",
                category="Termination / Exit",
                vendor_name=fs.vendor_name,
                status=st,
                raw_vendor_value=cat_res.raw_value,
                normalized_vendor_value="Convenience Permitted" if conv_perm else "Cause Only",
                normalized_unit="termination_right",
                explanation=exp,
                evidence_citations=cat_res.evidence_citations,
                comparison_rule="vendor_convenience == True",
                normalization_status=norm.normalization_status,
            )

        return ComparisonMatrixRow(
            category="Termination / Exit",
            requirement_label=label,
            requirement_name="Termination Clause",
            buyer_target_summary=req_text,
            vendor_evaluations=evals,
        )

    def _evaluate_support_requirement(self, reqs: ProcurementRequirements, fact_sheets: List[VendorFactSheet]) -> ComparisonMatrixRow:
        evals: Dict[str, RequirementEvaluationResult] = {}
        req_text = reqs.support_requirement
        is_24_7_req = "24/7" in req_text or "24x7" in req_text or "critical" in req_text.lower()
        label = f"Support Window: {req_text}"

        for fs in fact_sheets:
            cat_res = self._get_category_result(fs, "Support")
            if not cat_res or cat_res.status == "NOT_FOUND":
                evals[fs.vendor_name] = self._make_missing_res("REQ_SUPPORT", "Support", fs.vendor_name, cat_res)
                continue
            if cat_res.status == "UNCLEAR":
                evals[fs.vendor_name] = self._make_unclear_res("REQ_SUPPORT", "Support", fs.vendor_name, cat_res)
                continue
            if cat_res.status == "CONFLICTING":
                evals[fs.vendor_name] = self._make_conflicting_res("REQ_SUPPORT", "Support", fs.vendor_name, cat_res)
                continue

            norm = self.normalizer.normalize_support(cat_res.raw_value)
            win = norm.normalized_value.get("window") if (norm.normalized_value and isinstance(norm.normalized_value, dict)) else "unspecified"
            is_addon = norm.normalized_value.get("is_paid_addon", False) if (norm.normalized_value and isinstance(norm.normalized_value, dict)) else False

            # Evaluate compound support subconditions (availability window & incident response time)
            has_response_req = any(kw in req_text.lower() for kw in ["response", "hour", "minute", "critical", "severity", "sla"])

            if is_24_7_req:
                if win == "24_7" and not is_addon:
                    if has_response_req:
                        # Check if vendor evidence explicitly specifies response time
                        v_text_lower = (cat_res.raw_value or "").lower()
                        has_v_response = any(kw in v_text_lower for kw in ["response", "hour", "minute", "min", "hr", "severity"])
                        if has_v_response:
                            st = "MEETS"
                            exp = f"Vendor includes 24/7 technical support and specifies incident response time ('{cat_res.raw_value}')."
                        else:
                            st = "PARTIAL"
                            exp = "Vendor includes 24/7 technical support, but critical incident response time is not specified in proposal evidence."
                    else:
                        st = "MEETS"
                        exp = "Vendor includes 24/7 technical support."
                elif win == "24_7" and is_addon:
                    st = "PARTIAL"
                    exp = "24/7 support is available as a paid premium add-on."
                elif win == "business_hours":
                    st = "FAILS"
                    exp = "Vendor offers business-hours support only, failing 24/7 requirement."
                else:
                    st = "UNCLEAR"
                    exp = f"Support detail: {cat_res.raw_value}"
            else:
                st = "MEETS"
                exp = f"Vendor support coverage: {cat_res.raw_value}"

            evals[fs.vendor_name] = RequirementEvaluationResult(
                requirement_id="REQ_SUPPORT",
                category="Support",
                vendor_name=fs.vendor_name,
                status=st,
                raw_vendor_value=cat_res.raw_value,
                normalized_vendor_value="24/7 Included" if (win == "24_7" and not is_addon) else "24/7 Add-on" if is_addon else "Business Hours",
                normalized_unit="support_window",
                explanation=exp,
                evidence_citations=cat_res.evidence_citations,
                comparison_rule="vendor_support == 24_7",
                normalization_status=norm.normalization_status,
            )

        return ComparisonMatrixRow(
            category="Support",
            requirement_label=label,
            requirement_name="Support SLA",
            buyer_target_summary=req_text,
            vendor_evaluations=evals,
        )

    def _evaluate_custom_requirement(self, custom_text: str, req_idx: int, fact_sheets: List[VendorFactSheet]) -> ComparisonMatrixRow:
        evals: Dict[str, RequirementEvaluationResult] = {}
        cat_name = f"Custom: {custom_text}"
        req_id = f"REQ_CUSTOM_{req_idx}"

        for fs in fact_sheets:
            cat_res = self._get_category_result(fs, cat_name)
            if not cat_res or cat_res.status == "NOT_FOUND":
                evals[fs.vendor_name] = self._make_missing_res(req_id, cat_name, fs.vendor_name, cat_res)
                continue
            if cat_res.status == "UNCLEAR":
                evals[fs.vendor_name] = self._make_unclear_res(req_id, cat_name, fs.vendor_name, cat_res)
                continue
            if cat_res.status == "CONFLICTING":
                evals[fs.vendor_name] = self._make_conflicting_res(req_id, cat_name, fs.vendor_name, cat_res)
                continue

            # Evaluate custom requirement based on extracted evidence
            val_text = cat_res.raw_value or cat_res.summary
            evals[fs.vendor_name] = RequirementEvaluationResult(
                requirement_id=req_id,
                category=cat_name,
                vendor_name=fs.vendor_name,
                status="MEETS" if val_text else "UNCLEAR",
                raw_vendor_value=cat_res.raw_value,
                normalized_vendor_value=val_text,
                explanation=cat_res.summary or f"Vendor addresses requirement: {val_text}",
                evidence_citations=cat_res.evidence_citations,
                comparison_rule="vendor_custom_evidence_found",
                normalization_status="NORMALIZED" if val_text else "UNSUPPORTED",
            )

        return ComparisonMatrixRow(
            category=cat_name,
            requirement_label=f"Custom: {custom_text}",
            requirement_name=custom_text,
            buyer_target_summary=custom_text,
            vendor_evaluations=evals,
        )

    def _evaluate_textual_requirement(self, req_id: str, category: str, req_text: str, fact_sheets: List[VendorFactSheet]) -> ComparisonMatrixRow:
        evals: Dict[str, RequirementEvaluationResult] = {}
        label = f"{category}: {req_text}"

        for fs in fact_sheets:
            cat_res = self._get_category_result(fs, category)
            if not cat_res or cat_res.status == "NOT_FOUND":
                evals[fs.vendor_name] = self._make_missing_res(req_id, category, fs.vendor_name, cat_res)
                continue
            if cat_res.status == "UNCLEAR":
                evals[fs.vendor_name] = self._make_unclear_res(req_id, category, fs.vendor_name, cat_res)
                continue
            if cat_res.status == "CONFLICTING":
                evals[fs.vendor_name] = self._make_conflicting_res(req_id, category, fs.vendor_name, cat_res)
                continue

            val_text = cat_res.raw_value or cat_res.summary
            evals[fs.vendor_name] = RequirementEvaluationResult(
                requirement_id=req_id,
                category=category,
                vendor_name=fs.vendor_name,
                status="MEETS" if val_text else "UNCLEAR",
                raw_vendor_value=cat_res.raw_value,
                normalized_vendor_value=val_text,
                explanation=cat_res.summary or f"Vendor term: {val_text}",
                evidence_citations=cat_res.evidence_citations,
                comparison_rule="vendor_textual_evidence_found",
                normalization_status="NORMALIZED" if val_text else "UNSUPPORTED",
            )

        return ComparisonMatrixRow(
            category=category,
            requirement_label=label,
            requirement_name=category,
            buyer_target_summary=req_text,
            vendor_evaluations=evals,
        )

    # --- Phase 3 Status Propagation Helpers ---

    def _make_missing_res(self, req_id: str, category: str, vendor_name: str, cat_res: Optional[CategoryExtractionResult]) -> RequirementEvaluationResult:
        cits = cat_res.evidence_citations if cat_res else []
        return RequirementEvaluationResult(
            requirement_id=req_id,
            category=category,
            vendor_name=vendor_name,
            status="MISSING",
            raw_vendor_value=None,
            normalized_vendor_value=None,
            explanation="No supported fact found in proposal evidence.",
            evidence_citations=cits,
            comparison_rule="phase3_status == NOT_FOUND",
            normalization_status="NOT_APPLICABLE",
        )

    def _make_unclear_res(self, req_id: str, category: str, vendor_name: str, cat_res: CategoryExtractionResult) -> RequirementEvaluationResult:
        return RequirementEvaluationResult(
            requirement_id=req_id,
            category=category,
            vendor_name=vendor_name,
            status="UNCLEAR",
            raw_vendor_value=cat_res.raw_value,
            normalized_vendor_value=None,
            explanation=cat_res.summary or "Extracted proposal detail is ambiguous or incomplete.",
            evidence_citations=cat_res.evidence_citations,
            comparison_rule="phase3_status == UNCLEAR",
            normalization_status="AMBIGUOUS",
        )

    def _make_conflicting_res(self, req_id: str, category: str, vendor_name: str, cat_res: CategoryExtractionResult) -> RequirementEvaluationResult:
        return RequirementEvaluationResult(
            requirement_id=req_id,
            category=category,
            vendor_name=vendor_name,
            status="CONFLICTING",
            raw_vendor_value=cat_res.raw_value,
            normalized_vendor_value=None,
            explanation=cat_res.summary or "Proposal contains conflicting extracted values in different sections.",
            evidence_citations=cat_res.evidence_citations,
            comparison_rule="phase3_status == CONFLICTING",
            normalization_status="CONFLICTING",
        )
