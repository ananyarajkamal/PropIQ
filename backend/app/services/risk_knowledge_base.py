"""Procurement Risk Taxonomy & Knowledge Base for PropIQ.

Defines controlled 22-category risk taxonomy, deterministic rule signals,
semantic vector texts for embedding matching, target extraction fields,
and deterministic severity policy rules.
"""

import re
from enum import Enum
from typing import Dict, List, Optional, Any, Callable
from pydantic import BaseModel


class RiskCategory(str, Enum):
    """Controlled 22-category procurement risk taxonomy."""

    AUTO_RENEWAL = "AUTO_RENEWAL"
    PRICE_ESCALATION = "PRICE_ESCALATION"
    LIABILITY_CAP = "LIABILITY_CAP"
    UNCAPPED_LIABILITY = "UNCAPPED_LIABILITY"
    INDEMNITY = "INDEMNITY"
    TERMINATION_RESTRICTION = "TERMINATION_RESTRICTION"
    EARLY_TERMINATION_FEE = "EARLY_TERMINATION_FEE"
    MINIMUM_COMMITMENT = "MINIMUM_COMMITMENT"
    NON_REFUNDABLE_FEES = "NON_REFUNDABLE_FEES"
    SUSPENSION_RIGHTS = "SUSPENSION_RIGHTS"
    UNILATERAL_CHANGE_RIGHTS = "UNILATERAL_CHANGE_RIGHTS"
    DATA_OWNERSHIP = "DATA_OWNERSHIP"
    DATA_USAGE = "DATA_USAGE"
    SECURITY_OBLIGATION_GAP = "SECURITY_OBLIGATION_GAP"
    SLA_REMEDY_WEAKNESS = "SLA_REMEDY_WEAKNESS"
    AUDIT_RIGHTS = "AUDIT_RIGHTS"
    NOTICE_PERIOD = "NOTICE_PERIOD"
    SUPPORT_LIMITATION = "SUPPORT_LIMITATION"
    WARRANTY_LIMITATION = "WARRANTY_LIMITATION"
    PAYMENT_RISK = "PAYMENT_RISK"
    LOCK_IN = "LOCK_IN"
    OTHER_REVIEW_REQUIRED = "OTHER_REVIEW_REQUIRED"


class RiskDefinition(BaseModel):
    """Structured knowledge base entry for a risk category."""

    category: RiskCategory
    title: str
    description: str
    semantic_vector_text: str
    rule_patterns: List[str]
    suppression_patterns: List[str]
    target_fields: List[str]
    default_procurement_impact: str
    default_review_reason: str


TAXONOMY_KNOWLEDGE_BASE: Dict[RiskCategory, RiskDefinition] = {
    RiskCategory.AUTO_RENEWAL: RiskDefinition(
        category=RiskCategory.AUTO_RENEWAL,
        title="Automatic Contract Renewal Provision",
        description="Agreement automatically renews for successive multi-month or annual terms unless formal written cancellation notice is submitted in advance.",
        semantic_vector_text="automatically renews for successive term agreement extends auto-renewal unless written notice provided cancellation window prior to expiration",
        rule_patterns=[
            r"automatic(?:ally)?\s+renew",
            r"auto-renew(?:al)?",
            r"successive\s+(?:\d+-month|\d+-year|annual|monthly)\s+terms?",
            r"renew\s+unless\s+(?:cancelled|terminated)",
            r"evergreen\s+provision",
        ],
        suppression_patterns=[
            r"does not renew automatically",
            r"will not automatically renew",
            r"no auto-renewal",
            r"no automatic renewal",
            r"manual renewal required",
        ],
        target_fields=["renewal_duration", "notice_period", "renewal_frequency"],
        default_procurement_impact="Creates potential vendor lock-in if cancellation notice is missed prior to expiration.",
        default_review_reason="Track renewal notice deadline operationally in procurement calendar.",
    ),
    RiskCategory.PRICE_ESCALATION: RiskDefinition(
        category=RiskCategory.PRICE_ESCALATION,
        title="Price Increase & Fee Escalation Clause",
        description="Vendor retains unilateral right to increase fees annually or upon renewal by a percentage, CPI, or sole discretion.",
        semantic_vector_text="price increase annual escalation pricing adjustment fee increase CPI consumer price index sole discretion rate revision percentage uplift",
        rule_patterns=[
            r"price\s+(?:increase|escalation|adjustment|uplift)",
            r"fee\s+(?:increase|escalation|adjustment)",
            r"increase\s+by\s+(?:up\s+to\s+)?\d+%",
            r"subject\s+to\s+annual\s+increase",
            r"cpi\s+(?:increase|adjustment)",
            r"sole\s+discretion\s+pricing",
        ],
        suppression_patterns=[
            r"fees remain fixed",
            r"pricing is fixed",
            r"no price increase",
            r"will not increase during the term",
            r"fixed price for initial term",
        ],
        target_fields=["percentage_increase", "escalation_basis", "frequency"],
        default_procurement_impact="Increases total cost of ownership over multi-year contract term.",
        default_review_reason="Negotiate fixed price cap on annual renewal price increases.",
    ),
    RiskCategory.LIABILITY_CAP: RiskDefinition(
        category=RiskCategory.LIABILITY_CAP,
        title="Low or Unfavorable Liability Cap",
        description="Vendor limits maximum financial liability to a small multiple of monthly or paid fees.",
        semantic_vector_text="limitation of liability liability cap aggregate liability maximum liability total fees paid in preceding 12 months 3 months",
        rule_patterns=[
            r"limitation\s+of\s+liability",
            r"aggregate\s+liability\s+shall\s+not\s+exceed",
            r"capped\s+at\s+the\s+total\s+amount\s+paid",
            r"liability\s+limited\s+to",
        ],
        suppression_patterns=[
            r"uncapped liability",
            r"unlimited liability",
            r"no cap on liability",
        ],
        target_fields=["cap_amount", "cap_basis", "carve_outs"],
        default_procurement_impact="Caps customer financial recovery in case of vendor breach or failure.",
        default_review_reason="Review liability cap relative to contract value and operational risk exposure.",
    ),
    RiskCategory.UNCAPPED_LIABILITY: RiskDefinition(
        category=RiskCategory.UNCAPPED_LIABILITY,
        title="Uncapped or Unlimited Financial Exposure",
        description="Clause explicitly leaves liability uncapped or exposes party to unlimited consequential damages.",
        semantic_vector_text="unlimited liability uncapped liability no limitation of liability full indemnification without cap consequential damages",
        rule_patterns=[
            r"unlimited\s+liability",
            r"uncapped\s+liability",
            r"without\s+limitation\s+of\s+liability",
            r"no\s+cap\s+on\s+liability",
        ],
        suppression_patterns=[
            r"liability\s+is\s+capped",
            r"liability\s+shall\s+not\s+exceed",
        ],
        target_fields=["exposure_type", "carve_out_terms"],
        default_procurement_impact="Exposes organization to un-budgeted financial liability in disputes.",
        default_review_reason="Requires legal team review to establish reasonable contractual cap.",
    ),
    RiskCategory.MINIMUM_COMMITMENT: RiskDefinition(
        category=RiskCategory.MINIMUM_COMMITMENT,
        title="Minimum Contract Commitment & Duration",
        description="Requires customer to commit to multi-year subscription or minimum volume commitment.",
        semantic_vector_text="minimum commitment initial term 24 months 36 months committed volume minimum order spend lock-in",
        rule_patterns=[
            r"initial\s+(?:term|period)\s+of\s+\d+\s+(?:months|years)",
            r"minimum\s+(?:commitment|spend|volume|subscription)",
            r"committed\s+term\s+of\s+\d+",
            r"locked-in\s+period",
        ],
        suppression_patterns=[
            r"no minimum commitment",
            r"cancel anytime",
            r"month-to-month",
        ],
        target_fields=["commitment_period", "minimum_amount"],
        default_procurement_impact="Binds organization to fixed long-term financial obligation.",
        default_review_reason="Align commitment term with project roadmap and exit criteria.",
    ),
    RiskCategory.EARLY_TERMINATION_FEE: RiskDefinition(
        category=RiskCategory.EARLY_TERMINATION_FEE,
        title="Early Termination Fee & Buyout Penalty",
        description="Terminating prior to contract end date triggers buyout fees or remaining contract payments.",
        semantic_vector_text="early termination fee buyout charge remaining contract fees acceleration of payments liquidated damages cancellation penalty",
        rule_patterns=[
            r"early\s+termination\s+(?:fee|penalty|charge)",
            r"remaining\s+fees\s+(?:shall|will)\s+become\s+(?:due|payable)",
            r"liquidated\s+damages\s+for\s+early\s+termination",
            r"buyout\s+fee",
        ],
        suppression_patterns=[
            r"no early termination fee",
            r"without penalty",
            r"no termination fee",
        ],
        target_fields=["fee_amount", "calculation_method"],
        default_procurement_impact="Imposes financial penalty if service must be discontinued early.",
        default_review_reason="Negotiate termination for convenience without remaining fee acceleration.",
    ),
    RiskCategory.NON_REFUNDABLE_FEES: RiskDefinition(
        category=RiskCategory.NON_REFUNDABLE_FEES,
        title="Non-Refundable Upfront or Implementation Fees",
        description="Prepaid fees or implementation deposits are non-refundable upon cancellation.",
        semantic_vector_text="non-refundable fees implementation deposit prepaid fees non refundable no refunds provided under any circumstances",
        rule_patterns=[
            r"non-refundable",
            r"non\s+refundable",
            r"fees\s+will\s+not\s+be\s+refunded",
            r"no\s+refunds",
        ],
        suppression_patterns=[
            r"pro-rata refund",
            r"fully refundable",
            r"refunded in full",
        ],
        target_fields=["fee_type", "refund_conditions"],
        default_procurement_impact="Upfront payments are forfeited even if project is cancelled prior to completion.",
        default_review_reason="Structure payments against milestone deliverables rather than upfront deposits.",
    ),
    RiskCategory.TERMINATION_RESTRICTION: RiskDefinition(
        category=RiskCategory.TERMINATION_RESTRICTION,
        title="Termination Rights Restriction",
        description="Customer right to terminate for convenience is restricted or requires excessive notice.",
        semantic_vector_text="no termination for convenience restricted cancellation notice period 90 days notice 120 days notice required",
        rule_patterns=[
            r"no\s+right\s+to\s+terminate\s+for\s+convenience",
            r"termination\s+only\s+for\s+cause",
            r"notice\s+of\s+non-renewal\s+at\s+least\s+\d+\s+days",
        ],
        suppression_patterns=[
            r"may terminate for convenience",
            r"30-day notice for convenience",
        ],
        target_fields=["notice_days", "termination_type"],
        default_procurement_impact="Limits flexibility to exit underperforming vendor contracts.",
        default_review_reason="Include standard 30-day termination for convenience clause.",
    ),
    RiskCategory.SUSPENSION_RIGHTS: RiskDefinition(
        category=RiskCategory.SUSPENSION_RIGHTS,
        title="Broad Vendor Service Suspension Rights",
        description="Vendor reserves right to suspend service immediately for alleged breach or sole discretion.",
        semantic_vector_text="suspend service immediate suspension sole discretion withhold access without prior notice",
        rule_patterns=[
            r"suspend\s+(?:access|service|account)",
            r"immediate\s+suspension",
            r"sole\s+discretion\s+to\s+suspend",
        ],
        suppression_patterns=[
            r"suspension solely for non-payment",
            r"written notice required prior to suspension",
        ],
        target_fields=["suspension_trigger", "notice_required"],
        default_procurement_impact="Risk of unexpected service disruption to business operations.",
        default_review_reason="Require minimum written notice and cure period prior to suspension.",
    ),
    RiskCategory.UNILATERAL_CHANGE_RIGHTS: RiskDefinition(
        category=RiskCategory.UNILATERAL_CHANGE_RIGHTS,
        title="Unilateral Contract & Feature Modification Rights",
        description="Vendor may modify terms, features, or SLAs unilaterally by posting online updates.",
        semantic_vector_text="unilateral change modify terms update agreement online posting sole discretion continued use constitutes acceptance",
        rule_patterns=[
            r"modify\s+this\s+agreement\s+at\s+any\s+time",
            r"unilateral\s+(?:change|modification|update)",
            r"update\s+terms\s+by\s+posting",
            r"continued\s+use\s+constitutes\s+acceptance",
        ],
        suppression_patterns=[
            r"mutual written agreement",
            r"written consent of both parties",
        ],
        target_fields=["modification_scope", "notice_mechanism"],
        default_procurement_impact="Vendor can change pricing, SLAs, or core functionality without customer consent.",
        default_review_reason="Require mutual written consent for material contract amendments.",
    ),
    RiskCategory.DATA_OWNERSHIP: RiskDefinition(
        category=RiskCategory.DATA_OWNERSHIP,
        title="Ambiguous Data Ownership Rights",
        description="Terms do not explicitly grant customer full ownership of customer data or derived analytics.",
        semantic_vector_text="data ownership customer data analytics rights derived data vendor ownership intellectual property in data",
        rule_patterns=[
            r"vendor\s+retains\s+ownership\s+of\s+data",
            r"derived\s+data\s+ownership",
            r"analytics\s+data\s+ownership",
        ],
        suppression_patterns=[
            r"customer retains all right title and interest",
            r"customer owns all customer data",
            r"sole property of customer",
        ],
        target_fields=["data_type", "ownership_grant"],
        default_procurement_impact="Potential loss of control over proprietary business data.",
        default_review_reason="Explicitly define customer sole ownership of raw and derived data.",
    ),
    RiskCategory.DATA_USAGE: RiskDefinition(
        category=RiskCategory.DATA_USAGE,
        title="Broad Vendor Data Usage & AI Training Rights",
        description="Vendor claims rights to aggregate, analyze, or train machine learning models using customer data.",
        semantic_vector_text="use customer data machine learning AI model training aggregate data research partner sharing analytics",
        rule_patterns=[
            r"train\s+(?:ai|machine\s+learning|models)",
            r"aggregate\s+and\s+anonymize\s+data",
            r"use\s+customer\s+data\s+for\s+product\s+improvement",
        ],
        suppression_patterns=[
            r"solely to provide the service",
            r"will not use customer data to train",
            r"process data solely for customer",
        ],
        target_fields=["usage_scope", "opt_out_available"],
        default_procurement_impact="Data privacy exposure and unauthorized reuse of corporate knowledge.",
        default_review_reason="Restrict data processing strictly to service delivery; prohibit AI training.",
    ),
    RiskCategory.INDEMNITY: RiskDefinition(
        category=RiskCategory.INDEMNITY,
        title="Unbalanced Customer Indemnification Obligation",
        description="Requires customer to indemnify vendor broadly for third-party claims or operational use.",
        semantic_vector_text="customer shall indemnify hold harmless defend vendor third party claims broad indemnification",
        rule_patterns=[
            r"customer\s+(?:shall|agrees\s+to)\s+indemnify",
            r"defend\s+and\s+hold\s+harmless\s+vendor",
            r"broad\s+indemnification",
        ],
        suppression_patterns=[
            r"vendor shall indemnify customer",
            r"mutual indemnification",
        ],
        target_fields=["indemnitor", "scope"],
        default_procurement_impact="Shifts third-party litigation costs and damages onto customer.",
        default_review_reason="Ensure indemnification obligations are mutual and proportional.",
    ),
    RiskCategory.SECURITY_OBLIGATION_GAP: RiskDefinition(
        category=RiskCategory.SECURITY_OBLIGATION_GAP,
        title="Missing or Unconfirmed Security Commitments",
        description="Proposal lacks formal confirmation of SOC 2, ISO 27001, or encryption standards.",
        semantic_vector_text="security gap missing SOC 2 ISO 27001 unconfirmed security controls encryption at rest in transit",
        rule_patterns=[
            r"security\s+audit\s+not\s+available",
            r"working\s+towards\s+compliance",
            r"certification\s+in\s+progress",
        ],
        suppression_patterns=[
            r"soc 2 type ii certified",
            r"iso 27001 certified",
        ],
        target_fields=["missing_certifications"],
        default_procurement_impact="Heightened cybersecurity and regulatory compliance risk.",
        default_review_reason="Require current SOC 2 Type II / ISO 27001 audit report prior to execution.",
    ),
    RiskCategory.SLA_REMEDY_WEAKNESS: RiskDefinition(
        category=RiskCategory.SLA_REMEDY_WEAKNESS,
        title="Weak or Sole SLA Remedy Provision",
        description="Uptime SLA remedies are limited to tiny service credits as sole and exclusive remedy.",
        semantic_vector_text="service credit sole and exclusive remedy SLA uptime credit capped credit 5% monthly fee",
        rule_patterns=[
            r"sole\s+and\s+exclusive\s+remedy",
            r"sla\s+credit\s+capped",
            r"credit\s+not\s+exceeding\s+\d+%",
        ],
        suppression_patterns=[
            r"right to terminate for persistent outage",
            r"meaningful financial credit",
        ],
        target_fields=["remedy_cap", "credit_percentage"],
        default_procurement_impact="Inadequate compensation for business losses caused by vendor downtime.",
        default_review_reason="Add termination right for chronic downtime below SLA threshold.",
    ),
    RiskCategory.NOTICE_PERIOD: RiskDefinition(
        category=RiskCategory.NOTICE_PERIOD,
        title="Excessive Notice Period Requirement",
        description="Requires 60, 90, or 120 days advance notice for cancellation or modifications.",
        semantic_vector_text="notice period 60 days 90 days 120 days written notice advance notice requirement",
        rule_patterns=[
            r"(?:60|90|120)\s+days?\s+prior\s+written\s+notice",
            r"advance\s+notice\s+of\s+at\s+least\s+(?:60|90|120)\s+days",
        ],
        suppression_patterns=[
            r"30 days notice",
            r"14 days notice",
        ],
        target_fields=["notice_days"],
        default_procurement_impact="Increases operational burden to meet tight cancellation windows.",
        default_review_reason="Standardize notice window to 30 days.",
    ),
    RiskCategory.SUPPORT_LIMITATION: RiskDefinition(
        category=RiskCategory.SUPPORT_LIMITATION,
        title="Restricted Technical Support Availability",
        description="Support is limited to business hours or email only; 24/7 support requires extra fee.",
        semantic_vector_text="business hours support 8x5 email support only 24/7 support paid add-on extra charge response time",
        rule_patterns=[
            r"support\s+available\s+during\s+business\s+hours\s+only",
            r"8x5\s+support",
            r"24/7\s+support\s+(?:available\s+for\s+an\s+)?additional\s+fee",
        ],
        suppression_patterns=[
            r"24/7 support included",
            r"24/7/365 support provided",
        ],
        target_fields=["support_hours", "channels"],
        default_procurement_impact="Slow incident resolution during off-hours outages.",
        default_review_reason="Ensure critical incident SLA covers 24/7 emergency escalation.",
    ),
    RiskCategory.WARRANTY_LIMITATION: RiskDefinition(
        category=RiskCategory.WARRANTY_LIMITATION,
        title="Short or Disclaimed Performance Warranty",
        description="Warranty period is extremely short (e.g. 30/90 days) or disclaimed 'AS IS'.",
        semantic_vector_text="as-is warranty disclaimer performance warranty 30-day warranty short warranty period no warranty",
        rule_patterns=[
            r"provided\s+[\"']?as\s+is[\"']?",
            r"disclaims?\s+all\s+warranties",
            r"warranty\s+period\s+of\s+(?:30|60|90)\s+days",
        ],
        suppression_patterns=[
            r"12-month warranty",
            r"warrants service will perform substantially",
        ],
        target_fields=["warranty_duration"],
        default_procurement_impact="Customer bears risk of software defects after initial window.",
        default_review_reason="Require warranty coverage for initial annual contract term.",
    ),
    RiskCategory.PAYMENT_RISK: RiskDefinition(
        category=RiskCategory.PAYMENT_RISK,
        title="Aggressive Payment & Late Interest Terms",
        description="Requires immediate payment or imposes high monthly interest penalties for late payment.",
        semantic_vector_text="payment due upon receipt late payment interest 1.5% per month immediate payment due",
        rule_patterns=[
            r"due\s+upon\s+receipt",
            r"late\s+payment\s+interest\s+of\s+\d+",
            r"1\.5%\s+per\s+month",
        ],
        suppression_patterns=[
            r"net 30",
            r"net 45",
            r"net 60",
        ],
        target_fields=["payment_days", "late_interest"],
        default_procurement_impact="Adverse impact on treasury and cash flow management.",
        default_review_reason="Negotiate standard Net 30 or Net 45 payment terms.",
    ),
    RiskCategory.LOCK_IN: RiskDefinition(
        category=RiskCategory.LOCK_IN,
        title="Proprietary Technology & Data Lock-In Risk",
        description="Proprietary data formats or high migration fees create switching friction.",
        semantic_vector_text="proprietary format data export fee migration fee vendor lock-in data extraction charge",
        rule_patterns=[
            r"proprietary\s+data\s+format",
            r"data\s+export\s+fee",
            r"assisted\s+migration\s+charge",
        ],
        suppression_patterns=[
            r"standard open api export",
            r"free data export",
        ],
        target_fields=["export_format", "export_fee"],
        default_procurement_impact="High switching cost if migrating to alternative vendor.",
        default_review_reason="Require automated standard data export capability upon exit.",
    ),
    RiskCategory.AUDIT_RIGHTS: RiskDefinition(
        category=RiskCategory.AUDIT_RIGHTS,
        title="Excessive Vendor Audit Rights on Customer",
        description="Vendor retains broad right to audit customer systems and bill for overage with penalty.",
        semantic_vector_text="vendor audit right audit customer facilities inspection overage charge audit cost",
        rule_patterns=[
            r"vendor\s+may\s+audit",
            r"inspect\s+customer\s+(?:facilities|systems)",
            r"audit\s+at\s+customer\s+expense",
        ],
        suppression_patterns=[
            r"audit with 30 days notice once per year",
            r"independent third party auditor",
        ],
        target_fields=["audit_frequency", "cost_allocation"],
        default_procurement_impact="Operational disruption and unbudgeted audit fee exposure.",
        default_review_reason="Limit audit frequency to once per year with prior notice.",
    ),
    RiskCategory.OTHER_REVIEW_REQUIRED: RiskDefinition(
        category=RiskCategory.OTHER_REVIEW_REQUIRED,
        title="General Commercial Review Item",
        description="Unusual commercial clause or non-standard term requiring procurement review.",
        semantic_vector_text="unusual commercial term non-standard obligation procurement review required",
        rule_patterns=[],
        suppression_patterns=[],
        target_fields=[],
        default_procurement_impact="Potential operational or commercial risk.",
        default_review_reason="Review clause with procurement lead.",
    ),
}
