"""Data models module for PropIQ FastAPI Backend.

Establishes Pydantic data schemas for Phase 0, Phase 1, Phase 2, Phase 3, Phase 4, Phase 5, Phase 6, Phase 7, and Phase 8.
"""

from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class HealthResponseModel(BaseModel):
    """Data model representing the /api/health endpoint response."""

    status: str = Field(default="ok", description="Service status indicator")
    service: str = Field(default="PropIQ API", description="Service identifier name")
    phase: str = Field(default="phase9", description="Current development phase identifier")
    groq_configured: bool = Field(default=False, description="Flag indicating if Groq API key is present")


class ApplicationConfigModel(BaseModel):
    """Data model representing application status configuration."""

    app_name: str = Field(default="PropIQ API", description="Application name")
    app_version: str = Field(default="1.0.0-phase9", description="Application version")
    groq_configured: bool = Field(default=False, description="Flag indicating if Groq API key is present")
    environment: str = Field(default="development", description="Execution environment")


class APIErrorModel(BaseModel):
    """Standardized safe user-facing API error response schema (Rule 28 & 29)."""

    error_code: str = Field(..., description="Controlled machine-readable error code")
    message: str = Field(..., description="Clean, human-readable non-technical error description")
    retryable: bool = Field(default=False, description="Flag indicating if user or system can safely retry")
    details: Optional[Any] = Field(default=None, description="Optional safe non-sensitive diagnostic details")



class VendorBasicInfo(BaseModel):
    """Data model representing basic vendor information."""

    vendor_name: str = Field(..., min_length=1, max_length=150, description="Name of the vendor")
    proposal_id: Optional[str] = Field(default=None, description="Optional proposal identifier")


class SystemStatusModel(BaseModel):
    """Data model representing system operational status."""

    status_code: str = Field(..., description="Short status identifier")
    message: str = Field(..., description="Human-readable status description")
    is_ready: bool = Field(default=True, description="Flag indicating system readiness")


class PageExtractedText(BaseModel):
    """Data model for page-level extracted PDF text preserving evidence traceability."""

    page_number: int = Field(..., description="1-indexed page number within the PDF document")
    text: str = Field(..., description="Normalized text content extracted from the page")
    character_count: int = Field(..., description="Number of characters on this page")


class ChunkMetadata(BaseModel):
    """Data model representing a text chunk with complete evidence traceability metadata."""

    chunk_id: str = Field(..., description="Deterministic chunk identifier e.g. v01_p003_c002")
    vendor_name: str = Field(..., description="Associated vendor name")
    source_filename: str = Field(..., description="Original filename of the proposal PDF")
    start_page: int = Field(..., description="Starting 1-indexed page number of the chunk")
    end_page: int = Field(..., description="Ending 1-indexed page number of the chunk")
    character_count: int = Field(..., description="Total character length of the chunk text")
    text: str = Field(..., description="Chunk text snippet")


class ProposalProcessSummary(BaseModel):
    """Summary metadata for a single processed vendor proposal PDF."""

    vendor_name: str = Field(..., description="Vendor name")
    filename: str = Field(..., description="Original filename")
    file_size_bytes: int = Field(..., description="File size in bytes")
    page_count: int = Field(..., description="Total page count")
    character_count: int = Field(..., description="Total character count extracted")
    chunk_count: int = Field(..., description="Total chunks created")
    status: str = Field(default="Ready for Analysis", description="Processing status label")
    warnings: List[str] = Field(default_factory=list, description="List of non-fatal warnings")


class ProposalProcessingResponse(BaseModel):
    """API response model for POST /api/proposals/process."""

    status: str = Field(default="success", description="Overall API request status")
    session_id: str = Field(..., description="Unique analysis session identifier")
    message: str = Field(..., description="Human-readable processing summary message")
    proposals: List[ProposalProcessSummary] = Field(..., description="Processed proposal summaries")
    total_proposals: int = Field(..., description="Total proposals processed")
    total_chunks: int = Field(..., description="Total chunks generated across all proposals")


class RetrievalRequestModel(BaseModel):
    """API request model for POST /api/retrieval/search."""

    session_id: str = Field(..., description="Active analysis session identifier")
    query: str = Field(..., min_length=1, max_length=500, description="Procurement search query string")
    vendor_name: Optional[str] = Field(default=None, description="Optional vendor name filter")
    top_k: int = Field(default=5, ge=1, le=20, description="Number of top evidence chunks to retrieve")


class RetrievalResultModel(BaseModel):
    """Individual evidence match model preserving complete citation traceability."""

    rank: int = Field(..., description="1-indexed relevance rank")
    vendor_name: str = Field(..., description="Source vendor name")
    source_filename: str = Field(..., description="Source document filename")
    start_page: int = Field(..., description="Starting page number")
    end_page: int = Field(..., description="Ending page number")
    chunk_id: str = Field(..., description="Deterministic chunk ID")
    text: str = Field(..., description="Evidence text excerpt")
    similarity_score: float = Field(..., description="Cosine similarity score (0.0 to 1.0)")


class RetrievalResponseModel(BaseModel):
    """API response model for POST /api/retrieval/search."""

    status: str = Field(default="success", description="Overall request status")
    query: str = Field(..., description="Cleaned search query string")
    session_id: str = Field(..., description="Target session identifier")
    vendor_filter: Optional[str] = Field(default=None, description="Applied vendor filter if any")
    total_results: int = Field(..., description="Total matched evidence items returned")
    results: List[RetrievalResultModel] = Field(..., description="List of ranked evidence results")


# --- Phase 7 Requirement Priority Enum ---

class RequirementPriority(str, Enum):
    """Controlled importance level priority for procurement requirements."""

    MUST_HAVE = "MUST_HAVE"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


# --- Phase 3 Procurement Requirements & Extraction Schemas ---

class ProcurementRequirements(BaseModel):
    """Data model representing user-specified procurement evaluation requirements and priorities."""

    budget_ceiling: Optional[float] = Field(default=None, ge=0, description="Optional maximum acceptable budget ceiling")
    budget_currency: Optional[str] = Field(default="USD", description="Currency symbol/code e.g. USD, INR, EUR, GBP")
    budget_priority: RequirementPriority = Field(default=RequirementPriority.MEDIUM, description="Priority weight for budget requirement")

    timeline_value: Optional[float] = Field(default=None, ge=0, description="Optional maximum deployment timeline value")
    timeline_unit: Optional[str] = Field(default="days", description="Timeline unit: days, weeks, months")
    timeline_priority: RequirementPriority = Field(default=RequirementPriority.MEDIUM, description="Priority weight for timeline requirement")

    minimum_sla: Optional[float] = Field(default=None, gt=0, le=100, description="Optional minimum uptime SLA percentage")
    sla_priority: RequirementPriority = Field(default=RequirementPriority.MEDIUM, description="Priority weight for SLA requirement")

    payment_terms: Optional[str] = Field(default=None, max_length=250, description="Optional payment terms requirement e.g. Net 30")
    payment_priority: RequirementPriority = Field(default=RequirementPriority.MEDIUM, description="Priority weight for payment requirement")

    certifications: List[str] = Field(default_factory=list, description="List of required security/quality certifications")
    certifications_priority: RequirementPriority = Field(default=RequirementPriority.MEDIUM, description="Priority weight for certifications requirement")

    warranty_value: Optional[float] = Field(default=None, ge=0, description="Optional minimum warranty value")
    warranty_unit: Optional[str] = Field(default="months", description="Warranty unit: months, years")
    warranty_priority: RequirementPriority = Field(default=RequirementPriority.MEDIUM, description="Priority weight for warranty requirement")

    liability_requirement: Optional[str] = Field(default=None, max_length=250, description="Optional liability cap requirement")
    liability_priority: RequirementPriority = Field(default=RequirementPriority.MEDIUM, description="Priority weight for liability requirement")

    renewal_preference: Optional[str] = Field(default=None, max_length=250, description="Optional contract renewal preference")
    renewal_priority: RequirementPriority = Field(default=RequirementPriority.MEDIUM, description="Priority weight for renewal requirement")

    termination_requirement: Optional[str] = Field(default=None, max_length=250, description="Optional exit/termination requirement")
    termination_priority: RequirementPriority = Field(default=RequirementPriority.MEDIUM, description="Priority weight for termination requirement")

    support_requirement: Optional[str] = Field(default=None, max_length=250, description="Optional support availability requirement")
    support_priority: RequirementPriority = Field(default=RequirementPriority.MEDIUM, description="Priority weight for support requirement")

    custom_requirements: List[str] = Field(default_factory=list, description="Up to 3 optional custom procurement requirement strings")
    custom_priorities: List[RequirementPriority] = Field(default_factory=list, description="Optional priorities for custom requirements")


class EvidenceCitationModel(BaseModel):
    """Data model for backend-verified evidence citation preserving page-level traceability."""

    evidence_id: str = Field(..., description="Deterministic evidence ID e.g. E1, E2")
    vendor_name: str = Field(..., description="Backend-verified vendor name")
    source_filename: str = Field(..., description="Backend-verified source PDF filename")
    start_page: int = Field(..., description="Backend-verified 1-indexed start page")
    end_page: int = Field(..., description="Backend-verified 1-indexed end page")
    chunk_id: str = Field(..., description="Backend-verified deterministic chunk ID")
    excerpt_text: str = Field(..., description="Actual chunk excerpt text stored by backend")


class CategoryExtractionResult(BaseModel):
    """Extraction result for a single procurement category or custom requirement."""

    category: str = Field(..., description="Category identifier or custom requirement name")
    status: str = Field(..., description="Extraction status: FOUND, NOT_FOUND, UNCLEAR, or CONFLICTING")
    raw_value: Optional[str] = Field(default=None, description="Extracted raw vendor text value")
    summary: str = Field(..., description="Concise plain-language interpretation summary")
    evidence_citations: List[EvidenceCitationModel] = Field(default_factory=list, description="Backend-verified evidence citations")
    notes: Optional[str] = Field(default=None, description="Additional notes or ambiguity explanations")


class VendorFactSheet(BaseModel):
    """Structured evidence-grounded fact sheet for a single vendor."""

    vendor_name: str = Field(..., description="Vendor name")
    categories: List[CategoryExtractionResult] = Field(..., description="List of category extraction results")


class ExtractionRequest(BaseModel):
    """API request model for POST /api/analysis/extract."""

    session_id: str = Field(..., description="Active analysis session identifier")
    requirements: ProcurementRequirements = Field(..., description="Procurement requirements object")
    vendor_name: Optional[str] = Field(default=None, description="Optional vendor name filter")


class ExtractionResponse(BaseModel):
    """API response model for POST /api/analysis/extract."""

    status: str = Field(default="success", description="Overall extraction status")
    session_id: str = Field(..., description="Session identifier")
    privacy_notice: str = Field(..., description="User-facing privacy notice")
    vendor_fact_sheets: List[VendorFactSheet] = Field(..., description="Structured vendor fact sheets")
    total_vendors: int = Field(..., description="Total vendors extracted")


# --- Phase 4 Terminology Normalization & Deterministic Comparison Schemas ---

class NormalizedValueModel(BaseModel):
    """Data model representing a deterministically normalized vendor fact value."""

    raw_value: Optional[str] = Field(default=None, description="Original raw vendor wording preserved intact")
    normalized_value: Optional[Any] = Field(default=None, description="Canonical normalized numeric or structured value")
    normalized_unit: Optional[str] = Field(default=None, description="Canonical unit indicator e.g. days, percent_uptime, USD")
    normalization_status: str = Field(
        default="NORMALIZED",
        description="Controlled normalization status: NORMALIZED, ALREADY_STANDARD, NOT_APPLICABLE, UNSUPPORTED, AMBIGUOUS, or CONFLICTING",
    )
    approximate_conversion: bool = Field(default=False, description="Flag indicating if duration/unit conversion involves calendar approximation")
    notes: Optional[str] = Field(default=None, description="Normalization explanation notes")


class RequirementEvaluationResult(BaseModel):
    """Deterministic evaluation result for a single vendor against a single requirement."""

    requirement_id: str = Field(..., description="Deterministic requirement ID e.g. REQ_PRICING, REQ_SLA")
    category: str = Field(..., description="Category label")
    vendor_name: str = Field(..., description="Vendor name")
    status: str = Field(
        ...,
        description="Controlled evaluation status: MEETS, PARTIAL, FAILS, MISSING, UNCLEAR, or CONFLICTING",
    )
    raw_vendor_value: Optional[str] = Field(default=None, description="Original vendor raw wording")
    normalized_vendor_value: Optional[str] = Field(default=None, description="Formatted normalized vendor value")
    normalized_unit: Optional[str] = Field(default=None, description="Normalized unit")
    explanation: str = Field(..., description="Deterministic natural-language rule explanation")
    evidence_citations: List[EvidenceCitationModel] = Field(default_factory=list, description="Associated backend evidence citations")
    comparison_rule: str = Field(..., description="Deterministic rule comparison trace e.g. 'vendor_sla >= minimum_sla'")
    normalization_status: str = Field(default="NORMALIZED", description="Status of the value normalization step")


class ComparisonMatrixRow(BaseModel):
    """Data model representing one row of the requirement comparison matrix (one requirement across all vendors)."""

    category: str = Field(..., description="Category label")
    requirement_label: str = Field(..., description="Human-readable requirement rule label")
    requirement_name: Optional[str] = Field(default=None, description="Human-readable requirement name")
    buyer_target_summary: Optional[str] = Field(default=None, description="Buyer target summary text")
    vendor_evaluations: Dict[str, RequirementEvaluationResult] = Field(
        ..., description="Map of vendor_name -> RequirementEvaluationResult"
    )


class ComparisonResponse(BaseModel):
    """API response model for POST /api/comparison/evaluate."""

    status: str = Field(default="success", description="Overall comparison response status")
    session_id: str = Field(..., description="Target session identifier")
    requirements: ProcurementRequirements = Field(..., description="Procurement requirements evaluated")
    matrix_rows: List[ComparisonMatrixRow] = Field(..., description="List of requirement comparison matrix rows")
    vendor_summary_counts: Dict[str, Dict[str, int]] = Field(
        ..., description="Map of vendor_name -> factual status counts (Meets, Partial, Fails, Missing, Unclear, Conflicting)"
    )
    privacy_notice: str = Field(..., description="User-facing privacy notice")


# --- Phase 5 Contradiction Detection & Contract Risk Intelligence Schemas ---

class RiskCategory(str, Enum):
    """Controlled enum of supported procurement contract risk categories."""

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


class RiskSeverity(str, Enum):
    """Controlled enum for procurement risk severity review priority."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RiskStatus(str, Enum):
    """Controlled enum for risk detection operational status."""

    DETECTED = "DETECTED"
    POTENTIAL = "POTENTIAL"
    NEEDS_CLARIFICATION = "NEEDS_CLARIFICATION"
    NOT_DETECTED = "NOT_DETECTED"


class RiskFindingModel(BaseModel):
    """Evidence-grounded contract risk finding data model."""

    risk_id: str = Field(..., description="Deterministic risk identifier e.g. rsk_vendorA_auto_renewal")
    vendor_name: str = Field(..., description="Associated vendor name")
    category: RiskCategory = Field(..., description="Controlled risk category enum")
    severity: RiskSeverity = Field(..., description="Controlled severity classification")
    title: str = Field(..., description="Concise editorial title e.g. Automatic Renewal With 90-Day Notice")
    summary: str = Field(..., description="Concise summary of the identified clause")
    procurement_impact: str = Field(..., description="Commercial/procurement operational impact description")
    review_reason: str = Field(..., description="Human review guidance reason")
    evidence_citations: List[EvidenceCitationModel] = Field(..., min_length=1, description="Backend-validated evidence citations (min 1)")
    related_requirement_ids: List[str] = Field(default_factory=list, description="Associated procurement requirement IDs if any")
    status: RiskStatus = Field(default=RiskStatus.DETECTED, description="Controlled risk status")


class ContradictionStatus(str, Enum):
    """Controlled enum for contradiction findings."""

    CONFIRMED_CONTRADICTION = "CONFIRMED_CONTRADICTION"
    POTENTIAL_CONTRADICTION = "POTENTIAL_CONTRADICTION"
    CONTEXT_DEPENDENT = "CONTEXT_DEPENDENT"
    DISMISSED = "DISMISSED"


class ContradictionFindingModel(BaseModel):
    """Evidence-grounded intra-vendor contradiction finding data model."""

    contradiction_id: str = Field(..., description="Deterministic contradiction identifier e.g. ctr_vendorA_commitment")
    vendor_name: str = Field(..., description="Source vendor name (Same-vendor enforcement)")
    category: str = Field(..., description="High-value contradiction category e.g. Payment, Term, Support, SLA")
    severity: RiskSeverity = Field(..., description="Controlled severity classification")
    statement_a: str = Field(..., description="First extracted statement wording")
    statement_b: str = Field(..., description="Second extracted statement wording")
    context_a: Optional[str] = Field(default=None, description="Document location/context for Statement A")
    context_b: Optional[str] = Field(default=None, description="Document location/context for Statement B")
    evidence_a: List[EvidenceCitationModel] = Field(..., min_length=1, description="Backend-validated citations for Statement A")
    evidence_b: List[EvidenceCitationModel] = Field(..., min_length=1, description="Backend-validated citations for Statement B")
    reason: str = Field(..., description="Explanation of potential statement incompatibility")
    status: ContradictionStatus = Field(default=ContradictionStatus.POTENTIAL_CONTRADICTION, description="Controlled contradiction status")


class RiskAnalysisRequest(BaseModel):
    """API request model for POST /api/risks/analyze."""

    session_id: str = Field(..., description="Active analysis session identifier")
    requirements: Optional[ProcurementRequirements] = Field(default=None, description="Optional procurement requirements for requirement impact linking")
    vendor_name: Optional[str] = Field(default=None, description="Optional vendor name filter for targeted re-analysis")


class RiskAnalysisResponse(BaseModel):
    """API response model for POST /api/risks/analyze."""

    status: str = Field(default="success", description="Overall risk analysis status")
    session_id: str = Field(..., description="Target session identifier")
    risk_findings: List[RiskFindingModel] = Field(..., description="List of evidence-grounded risk findings")
    contradiction_findings: List[ContradictionFindingModel] = Field(..., description="List of intra-vendor contradiction findings")
    high_priority_count: int = Field(..., description="Count of High and Critical priority findings")
    medium_priority_count: int = Field(..., description="Count of Medium priority findings")
    needs_clarification_count: int = Field(..., description="Count of findings needing clarification")
    contradictions_count: int = Field(..., description="Total contradiction findings count")
    privacy_notice: str = Field(..., description="User-facing privacy notice")


# --- Phase 6 Missing Information & Vendor Clarification Schemas ---

class ClarificationReason(str, Enum):
    """Controlled enum of vendor clarification gap reasons."""

    MISSING_REQUIREMENT = "MISSING_REQUIREMENT"
    UNCLEAR_INFORMATION = "UNCLEAR_INFORMATION"
    CONFLICTING_INFORMATION = "CONFLICTING_INFORMATION"
    PARTIAL_COMPLIANCE = "PARTIAL_COMPLIANCE"
    PRICING_AMBIGUITY = "PRICING_AMBIGUITY"
    CONDITIONAL_FEATURE = "CONDITIONAL_FEATURE"
    RISK_CLARIFICATION = "RISK_CLARIFICATION"
    SLA_CLARIFICATION = "SLA_CLARIFICATION"
    PAYMENT_CLARIFICATION = "PAYMENT_CLARIFICATION"
    RENEWAL_CLARIFICATION = "RENEWAL_CLARIFICATION"
    TERMINATION_CLARIFICATION = "TERMINATION_CLARIFICATION"
    SUPPORT_CLARIFICATION = "SUPPORT_CLARIFICATION"
    CERTIFICATION_CLARIFICATION = "CERTIFICATION_CLARIFICATION"
    DATA_CLARIFICATION = "DATA_CLARIFICATION"
    OTHER_REVIEW_REQUIRED = "OTHER_REVIEW_REQUIRED"


class QuestionPriority(str, Enum):
    """Controlled priority for vendor clarification questions."""

    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class ClarificationGenerationMethod(str, Enum):
    """Method used to generate question wording."""

    TEMPLATE = "TEMPLATE"
    GROQ_ASSISTED = "GROQ_ASSISTED"


class GapModel(BaseModel):
    """Typed Pydantic schema representing an identified clarification gap between GapService and ClarificationService."""

    gap_id: str = Field(..., description="Deterministic canonical gap ID e.g. gap_sess1_vendorA_req_warranty")
    vendor_name: str = Field(..., description="Target vendor name")
    reason: ClarificationReason = Field(..., description="Controlled clarification gap reason enum")
    priority: QuestionPriority = Field(..., description="Controlled question priority enum")
    source_status: str = Field(..., description="Status indicator: MISSING, NOT_FOUND, UNCLEAR, CONFLICTING, PARTIAL, or RISK_LINKED")
    requirement_id: Optional[str] = Field(default=None, description="Associated procurement requirement ID if applicable")
    requirement_label: Optional[str] = Field(default=None, description="Associated requirement label if applicable")
    raw_values: Optional[str] = Field(default=None, description="Original raw vendor text values")
    related_risk_id: Optional[str] = Field(default=None, description="Associated contract risk ID if applicable")
    related_contradiction_id: Optional[str] = Field(default=None, description="Associated contradiction ID if applicable")
    evidence_ids: List[str] = Field(default_factory=list, description="List of authoritative backend evidence chunk IDs")
    evidence_citations: List[EvidenceCitationModel] = Field(default_factory=list, description="Full backend evidence citations")
    gap_summary: str = Field(..., description="Human-readable summary of the identified clarification gap")


class ClarificationQuestionModel(BaseModel):
    """Data model representing a single evidence/requirement-linked vendor clarification question."""

    clarification_id: str = Field(..., description="Deterministic clarification ID generated from canonical gap identity")
    vendor_name: str = Field(..., description="Target vendor name")
    reason: ClarificationReason = Field(..., description="Controlled clarification gap reason enum")
    priority: QuestionPriority = Field(..., description="Controlled question priority enum (HIGH, MEDIUM, LOW)")
    question: str = Field(..., description="Concise, professional, procurement-oriented question wording")
    context: Optional[str] = Field(default=None, description="Brief background context explaining why the question is asked")
    requirement_id: Optional[str] = Field(default=None, description="Associated procurement requirement ID if applicable")
    requirement_label: Optional[str] = Field(default=None, description="Associated requirement label if applicable")
    related_risk_id: Optional[str] = Field(default=None, description="Associated contract risk ID if applicable")
    related_contradiction_id: Optional[str] = Field(default=None, description="Associated contradiction ID if applicable")
    evidence_citations: List[EvidenceCitationModel] = Field(default_factory=list, description="Backend-verified evidence citations")
    source_status: str = Field(default="MISSING", description="Status indicator: MISSING, UNCLEAR, CONFLICTING, PARTIAL, or RISK_LINKED")
    generation_method: ClarificationGenerationMethod = Field(default=ClarificationGenerationMethod.TEMPLATE, description="Generation method: TEMPLATE or GROQ_ASSISTED")


class ClarificationRequestModel(BaseModel):
    """API request model for POST /api/clarifications/generate."""

    session_id: str = Field(..., description="Active analysis session identifier")
    requirements: Optional[ProcurementRequirements] = Field(default=None, description="Optional procurement requirements override for requirement recomputations")
    vendor_name: Optional[str] = Field(default=None, description="Optional vendor name filter for targeted generation")


class ClarificationResponseModel(BaseModel):
    """API response model for POST /api/clarifications/generate."""

    status: str = Field(default="success", description="Overall API response status")
    session_id: str = Field(..., description="Target session identifier")
    questions: List[ClarificationQuestionModel] = Field(..., description="List of vendor clarification questions")
    total_questions: int = Field(..., description="Total questions generated across all vendors")
    high_priority_count: int = Field(..., description="Count of High priority questions")
    medium_priority_count: int = Field(..., description="Count of Medium priority questions")
    low_priority_count: int = Field(..., description="Count of Low priority questions")
    conflicting_details_count: int = Field(..., description="Count of questions addressing conflicting information")
    vendor_question_counts: Dict[str, int] = Field(..., description="Map of vendor_name -> total question count")
    privacy_notice: str = Field(..., description="User-facing privacy notice")


# --- Phase 7 Deterministic Scoring & Ranking Schemas ---

class RankStatus(str, Enum):
    """Controlled ranking position status enum (Rule 33: NO WINNER or LOSER!)."""

    LEADING = "LEADING"
    COMPETITIVE = "COMPETITIVE"
    BEHIND = "BEHIND"
    TIED = "TIED"


class RequirementScoreComponentModel(BaseModel):
    """Score component breakdowns for a single requirement rule for a vendor."""

    requirement_id: str = Field(..., description="Requirement identifier e.g. REQ_PRICING")
    requirement_label: str = Field(..., description="Human-readable requirement rule label")
    priority: RequirementPriority = Field(..., description="User-assigned priority weight enum")
    weight: float = Field(..., description="Numeric priority weight e.g. 5.0, 4.0, 3.0, 1.0")
    comparison_status: str = Field(..., description="Phase 4 evaluation status: MEETS, PARTIAL, UNCLEAR, CONFLICTING, MISSING, FAILS")
    status_score: float = Field(..., description="Numeric comparison state score (1.00, 0.60, 0.40, 0.25, 0.20, 0.00)")
    weighted_points: float = Field(..., description="Calculated points (status_score * weight)")
    max_points: float = Field(..., description="Maximum possible points (weight)")
    raw_vendor_value: Optional[str] = Field(default=None, description="Original vendor raw wording")
    normalized_vendor_value: Optional[str] = Field(default=None, description="Formatted normalized vendor value")
    evidence_citations: List[EvidenceCitationModel] = Field(default_factory=list, description="Backend evidence citations")


class ScoreDeductionModel(BaseModel):
    """Data model representing a score deduction item (risk penalty, contradiction penalty, or clarification penalty)."""

    deduction_id: str = Field(..., description="Deterministic deduction identifier")
    category: str = Field(..., description="Category label")
    type: str = Field(..., description="Deduction type: RISK, CONTRADICTION, or CLARIFICATION")
    label: str = Field(..., description="Human-readable deduction label")
    severity_or_priority: str = Field(..., description="Severity or priority classification")
    raw_penalty: float = Field(..., description="Uncapped raw penalty points")
    final_deduction: float = Field(..., description="Final applied deduction points after caps and linked-risk reductions")
    is_linked_risk: bool = Field(default=False, description="Flag indicating if deduction is a reduced linked-risk penalty")
    linked_requirement_id: Optional[str] = Field(default=None, description="Associated requirement ID if linked")
    explanation: str = Field(..., description="Transparent deduction explanation")
    evidence_citations: List[EvidenceCitationModel] = Field(default_factory=list, description="Backend evidence citations")


class VendorScoreBreakdownModel(BaseModel):
    """Complete transparent score breakdown and ranking model for a single vendor."""

    vendor_name: str = Field(..., description="Vendor name")
    rank: int = Field(..., description="1-indexed rank position (1 = Highest Alignment)")
    rank_status: RankStatus = Field(..., description="Controlled rank status: LEADING, COMPETITIVE, BEHIND, or TIED")
    alignment_score: float = Field(..., description="Final Alignment Score (0.0 to 100.0, rounded to 1 decimal place)")
    base_alignment_score: float = Field(..., description="Base requirement alignment score (0.0 to 100.0) before deductions")
    total_risk_penalty: float = Field(..., description="Total risk deduction points applied (capped at 15.0)")
    total_contradiction_penalty: float = Field(..., description="Total contradiction deduction points applied (capped at 10.0)")
    total_clarification_penalty: float = Field(..., description="Total clarification deduction points applied (capped at 8.0)")
    risk_analysis_status: str = Field(default="COMPLETED", description="Risk analysis status: COMPLETED, COMPLETED_NO_FINDINGS, NOT_ANALYZED, FAILED")
    contradiction_analysis_status: str = Field(default="COMPLETED", description="Contradiction analysis status: COMPLETED, COMPLETED_NO_FINDINGS, NOT_ANALYZED, FAILED")
    clarification_analysis_status: str = Field(default="COMPLETED", description="Clarification analysis status: COMPLETED, COMPLETED_NO_FINDINGS, NOT_ANALYZED, FAILED")
    must_have_failures_count: int = Field(..., description="Count of MUST_HAVE requirements not met (FAILS, MISSING, or UNCLEAR)")
    must_have_failed_labels: List[str] = Field(default_factory=list, description="Labels of failed MUST_HAVE requirements")
    requirements_met_count: int = Field(..., description="Count of requirements MEETS")
    total_requirements_count: int = Field(..., description="Total active requirements evaluated")
    requirement_components: List[RequirementScoreComponentModel] = Field(..., description="Detailed per-requirement score components")
    deductions: List[ScoreDeductionModel] = Field(default_factory=list, description="List of transparent score deduction items")
    ranking_explanation: str = Field(..., description="Deterministic evidence-backed summary explanation of vendor score and rank")


class ScoringRequestModel(BaseModel):
    """API request model for POST /api/scoring/evaluate."""

    session_id: str = Field(..., description="Active analysis session identifier")
    requirements: Optional[ProcurementRequirements] = Field(default=None, description="Optional procurement requirements override")
    vendor_name: Optional[str] = Field(default=None, description="Optional vendor name filter for targeted scoring")


class ScoringResponseModel(BaseModel):
    """API response model for POST /api/scoring/evaluate."""

    status: str = Field(default="success", description="Overall API request status")
    session_id: str = Field(..., description="Target session identifier")
    scoring_version: str = Field(default="1.0", description="Scoring algorithm version")
    evaluated_at: str = Field(..., description="ISO timestamp of scoring evaluation")
    vendor_scores: List[VendorScoreBreakdownModel] = Field(..., description="List of transparent vendor score breakdowns sorted by rank")
    total_vendors: int = Field(..., description="Total vendors evaluated")
    scoring_config_summary: Dict[str, Any] = Field(..., description="Summary of central scoring parameters used")
    privacy_notice: str = Field(..., description="User-facing privacy notice")


# --- Phase 8 Evidence-Backed Recommendation & Executive Brief Schemas ---

class RecommendationState(str, Enum):
    """Controlled recommendation decision state enum (Rule 4: NO WINNER, PERFECT_VENDOR, or GUARANTEED_BEST)."""

    RECOMMENDED = "RECOMMENDED"
    RECOMMENDED_WITH_CONDITIONS = "RECOMMENDED_WITH_CONDITIONS"
    FURTHER_REVIEW_REQUIRED = "FURTHER_REVIEW_REQUIRED"
    NO_CLEAR_RECOMMENDATION = "NO_CLEAR_RECOMMENDATION"


class RecommendationStrengthModel(BaseModel):
    """Evidence-backed vendor strength item model."""

    title: str = Field(..., description="Short strength title e.g. Highest SLA Alignment")
    description: str = Field(..., description="Evidence-backed description summary")
    category: str = Field(..., description="Requirement or commercial category")
    evidence_citations: List[EvidenceCitationModel] = Field(default_factory=list, description="Supporting evidence citations")


class RecommendationTradeoffModel(BaseModel):
    """Evidence-backed vendor trade-off / consideration item model."""

    title: str = Field(..., description="Short trade-off title e.g. Premium Tier Required for 24/7 Support")
    description: str = Field(..., description="Evidence-backed trade-off description summary")
    category: str = Field(..., description="Category label")
    severity_or_impact: str = Field(..., description="Impact level: LOW, MEDIUM, HIGH, CRITICAL, or COMMERCIAL")
    evidence_citations: List[EvidenceCitationModel] = Field(default_factory=list, description="Supporting evidence citations")


class RecommendationConditionModel(BaseModel):
    """Before proceeding item requiring procurement confirmation."""

    condition_id: str = Field(..., description="Deterministic condition identifier")
    item_type: str = Field(..., description="Item type: CLARIFICATION, RISK, CONTRADICTION, or MUST_HAVE_GAP")
    title: str = Field(..., description="Concise condition title")
    action_required: str = Field(..., description="Specific action or confirmation required before contract award")
    priority_or_severity: str = Field(..., description="Priority or severity classification (HIGH, CRITICAL, MEDIUM)")
    evidence_citations: List[EvidenceCitationModel] = Field(default_factory=list, description="Supporting evidence citations")


class RunnerUpVendorModel(BaseModel):
    """Runner-up alternative vendor comparative model."""

    vendor_name: str = Field(..., description="Runner-up vendor name")
    alignment_score: float = Field(..., description="Runner-up alignment score")
    score_gap: float = Field(..., description="Points score gap relative to leading candidate")
    rank: int = Field(..., description="1-indexed rank position (e.g. 2)")
    key_advantage: str = Field(..., description="Primary strength of runner-up compared to candidate")
    key_tradeoff: str = Field(..., description="Primary weakness or gap of runner-up")


class RecommendationDecisionModel(BaseModel):
    """Typed model for deterministic recommendation policy outcome (Rule 17 & Phase 8 Hardening)."""

    recommendation_state: RecommendationState = Field(..., description="Controlled recommendation decision state enum")
    recommended_vendor: Optional[str] = Field(default=None, description="Recommended/leading candidate name if eligible, None if tied/no clear choice")
    leading_vendor: str = Field(..., description="Phase 7 Rank 1 vendor name")
    runner_up_vendors: List[RunnerUpVendorModel] = Field(default_factory=list, description="Runner-up alternative vendors")
    alignment_score: float = Field(..., description="Alignment score of Phase 7 Rank 1 vendor")
    score_gap: float = Field(..., description="Score gap to 2nd rank vendor (0.0 if tied or single vendor)")
    is_close_leader: bool = Field(default=False, description="Flag indicating if score gap to 2nd rank vendor is narrow (0.5 <= score_gap < 2.0)")
    is_clear_leader: bool = Field(default=False, description="Flag indicating if score gap to 2nd rank vendor is wide (score_gap >= 2.0)")
    has_core_commercial_contradiction: bool = Field(default=False, description="Flag indicating if leading vendor has confirmed core commercial contradiction")
    must_have_failures: int = Field(..., description="Must Have requirement failure count of leading vendor")
    critical_risk_count: int = Field(..., description="Critical risk count of leading vendor")
    high_risk_count: int = Field(..., description="High risk count of leading vendor")
    confirmed_contradictions: int = Field(..., description="Confirmed contradiction count of leading vendor")
    high_priority_clarifications: int = Field(..., description="High-priority clarification question count of leading vendor")
    key_strengths: List[RecommendationStrengthModel] = Field(default_factory=list, description="Structured key strengths")
    key_tradeoffs: List[RecommendationTradeoffModel] = Field(default_factory=list, description="Structured key trade-offs")
    conditions_to_confirm: List[RecommendationConditionModel] = Field(default_factory=list, description="Structured items to confirm before proceeding")
    scoring_version: str = Field(default="1.0", description="Phase 7 scoring version")
    recommendation_policy_version: str = Field(default="1.0", description="Phase 8 recommendation policy version")


class RecommendationNarrativeModel(BaseModel):
    """Executive decision brief narrative model generated by Groq or template fallback."""

    executive_summary: str = Field(..., description="2 to 4 concise sentences summarizing recommendation state, candidate alignment, score, and core trade-offs.")
    why_this_vendor: str = Field(..., description="Summary paragraph detailing key strengths.")
    key_strengths_summary: List[str] = Field(default_factory=list, description="Plain language list of key strengths")
    key_tradeoffs_summary: List[str] = Field(default_factory=list, description="Plain language list of key trade-offs")
    before_proceeding_summary: List[str] = Field(default_factory=list, description="Plain language list of items to confirm before award")
    alternative_vendor_summary: Optional[str] = Field(default=None, description="Concise alternative vendor comparison summary")
    decision_rationale: str = Field(..., description="Overall decision rationale")
    is_fallback: bool = Field(default=False, description="Flag indicating if deterministic template fallback was used")


class RecommendationRequestModel(BaseModel):
    """API request model for POST /api/recommendation/generate."""

    session_id: str = Field(..., description="Active analysis session identifier")
    requirements: Optional[ProcurementRequirements] = Field(default=None, description="Optional procurement requirements override")


class RecommendationResponseModel(BaseModel):
    """API response model for POST /api/recommendation/generate."""

    status: str = Field(default="success", description="Overall request status")
    session_id: str = Field(..., description="Target session identifier")
    recommendation_policy_version: str = Field(default="1.0", description="Recommendation policy version")
    generated_at: str = Field(..., description="ISO timestamp of recommendation generation")
    decision: RecommendationDecisionModel = Field(..., description="Deterministic recommendation decision object")
    narrative: RecommendationNarrativeModel = Field(..., description="Executive decision brief narrative object")
    privacy_notice: str = Field(..., description="User-facing privacy notice")


class ModuleStatus(str, Enum):
    """Controlled execution status for workflow analysis modules."""

    NOT_STARTED = "NOT_STARTED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    STALE = "STALE"


class PrerequisiteBlockedModel(BaseModel):
    """Structured response model returned when an operation is blocked by prerequisite workflow states."""

    ranking_status: str = Field(default="BLOCKED", description="Blocked status indicator")
    prerequisites: Dict[str, ModuleStatus] = Field(..., description="Map of module names to their current execution status")
    blocking_prerequisites: List[str] = Field(..., description="List of module names currently blocking calculation")
    detail: str = Field(..., description="Human-readable explanation of why the operation is blocked")

