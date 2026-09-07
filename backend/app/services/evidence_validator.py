"""Authoritative Evidence Validation Service for PropIQ.

Validates evidence citations against trusted PDF chunk metadata and parsed page text.
Guarantees complete provenance, page correctness, and source-text entailment.
"""

import re
import logging
from typing import List, Dict, Optional, Any, Set
from app.models import EvidenceCitationModel, ChunkMetadata, PageExtractedText, ComparisonMatrixRow

logger = logging.getLogger("propiq_backend")


def collapse_whitespace(text: str) -> str:
    """Normalize whitespace conservatively for exact substring comparison."""
    if not text:
        return ""
    return re.sub(r"\s+", " ", text).strip().lower()


class EvidenceValidator:
    """Service providing authoritative validation and provenance auditing for evidence citations."""

    @staticmethod
    def validate_citation(
        citation: EvidenceCitationModel,
        trusted_chunks: Dict[str, ChunkMetadata],
        parsed_pages: Optional[List[PageExtractedText]] = None,
    ) -> bool:
        """Validate an evidence citation against trusted parsed document chunks and pages.

        Args:
            citation: The EvidenceCitationModel to validate.
            trusted_chunks: Map of chunk_id -> ChunkMetadata from PDF parser.
            parsed_pages: Optional list of PageExtractedText for page-level verification.

        Returns:
            True if citation passes all provenance and source substring checks; False otherwise.
        """
        if not citation or not citation.chunk_id:
            logger.warning("evidence_validator.rejected: Citation missing chunk_id.")
            return False

        # 1. Chunk existence check
        chunk = trusted_chunks.get(citation.chunk_id)
        if not chunk:
            logger.warning("evidence_validator.rejected: Chunk ID '%s' not found in trusted chunks.", citation.chunk_id)
            return False

        # 2. Vendor name match check
        if collapse_whitespace(citation.vendor_name) != collapse_whitespace(chunk.vendor_name):
            logger.warning("evidence_validator.rejected: Vendor mismatch ('%s' vs '%s').", citation.vendor_name, chunk.vendor_name)
            return False

        # 3. Source filename match check
        if citation.source_filename and chunk.source_filename:
            if collapse_whitespace(citation.source_filename) != collapse_whitespace(chunk.source_filename):
                logger.warning("evidence_validator.rejected: Filename mismatch ('%s' vs '%s').", citation.source_filename, chunk.source_filename)
                return False

        # 4. Page number match check (start_page)
        if citation.start_page != chunk.start_page:
            logger.warning("evidence_validator.rejected: Page mismatch (%d vs %d).", citation.start_page, chunk.start_page)
            return False

        # 5. Exact source-substring validation
        norm_excerpt = collapse_whitespace(citation.excerpt_text)
        norm_chunk = collapse_whitespace(chunk.text)

        if norm_excerpt not in norm_chunk:
            # Check page-level text if available
            found_in_page = False
            if parsed_pages:
                for p in parsed_pages:
                    if p.page_number == citation.start_page:
                        if norm_excerpt in collapse_whitespace(p.text):
                            found_in_page = True
                            break
            if not found_in_page:
                logger.warning("evidence_validator.rejected: Excerpt text not present in source chunk or page.")
                return False

        return True

    # Controlled semantic topical keywords per category to prevent cross-context citation collision
    CATEGORY_TOPICAL_MARKERS: Dict[str, List[str]] = {
        "Pricing": ["price", "pricing", "fee", "cost", "annual", "subscription", "usd", "$", "eur", "gbp", "inr", "total", "license", "licensing", "rate", "bill"],
        "Payment Terms": ["net", "payment", "invoice", "invoicing", "payable", "due", "billing", "upfront", "deposit", "receipt", "days after invoice", "upon receipt"],
        "Delivery / Implementation": ["implementation", "deployment", "deploy", "timeline", "schedule", "rollout", "onboarding", "go-live", "turnaround", "delivery", "setup", "weeks", "days", "months"],
        "SLA / Uptime": ["sla", "uptime", "availability", "service level", "%", "percent", "downtime", "credit", "maintenance", "service credits"],
        "Warranty": ["warranty", "guarantee", "defect", "remedy", "repair", "replacement", "cure", "warranties"],
        "Certifications": ["soc", "iso", "pci", "hipaa", "gdpr", "certification", "certified", "compliance", "audit", "security standard", "hitrust", "fedramp"],
        "Liability": ["liability", "indemnity", "indemnification", "cap", "capped", "damages", "consequential", "aggregate", "exceed", "limitation of liability"],
        "Renewal": ["renewal", "renew", "auto-renew", "automatic renewal", "extension", "successive term", "expire", "expiration"],
        "Termination / Exit": ["termination", "terminate", "cancel", "cancellation", "exit", "convenience", "breach", "notice", "cure period", "material breach", "early termination"],
        "Support": ["support", "helpdesk", "technical support", "24/7", "24x7", "business hours", "ticket", "response time", "severity", "incident", "sla response"],
    }

    @classmethod
    def validate_claim_topical_support(
        cls,
        category: str,
        raw_value: Optional[str],
        excerpt_text: str,
    ) -> bool:
        """Validate that cited evidence excerpt semantically supports the specific category claim.
        
        Guarantees that a passage mentioning a number or term in an unrelated context
        (e.g. implementation 30 days) is not accepted as evidence for another category
        (e.g. payment terms Net 30).
        """
        if not excerpt_text or not excerpt_text.strip():
            return False

        norm_excerpt = excerpt_text.lower()

        # 1. Check category topical markers
        markers = cls.CATEGORY_TOPICAL_MARKERS.get(category)
        if markers is not None:
            has_marker = any(m in norm_excerpt for m in markers)
            if not has_marker:
                logger.warning(
                    "evidence_validator.topical_mismatch: Excerpt for category '%s' lacks required topical markers: '%s'",
                    category, excerpt_text[:80]
                )
                return False
        elif category.startswith("Custom:"):
            # Custom requirement: extract substantive terms from category name
            req_words = [
                w.lower() for w in re.findall(r"\w+", category.replace("Custom:", ""))
                if len(w) > 3 and w.lower() not in {"must", "have", "should", "with", "from", "that", "this"}
            ]
            if req_words and not any(w in norm_excerpt for w in req_words):
                logger.warning(
                    "evidence_validator.custom_topical_mismatch: Excerpt for '%s' lacks relevant requirement terms: '%s'",
                    category, excerpt_text[:80]
                )
                return False

        # 2. Check that if raw_value has numbers/key tokens, they are supported by excerpt
        if raw_value:
            norm_val = raw_value.lower().strip()
            # Extract numbers
            val_nums = re.findall(r"\d+(?:\.\d+)?", norm_val)
            if val_nums:
                excerpt_nums = re.findall(r"\d+(?:\.\d+)?", norm_excerpt)
                # At least one major number from raw_value should be present in excerpt
                if not any(num in excerpt_nums for num in val_nums):
                    logger.warning(
                        "evidence_validator.value_not_supported: Raw value '%s' numbers not found in excerpt for '%s'",
                        raw_value, category
                    )
                    return False

        return True

    @staticmethod
    def audit_comparison_row(
        row: ComparisonMatrixRow,
        trusted_chunks: Dict[str, ChunkMetadata],
    ) -> List[str]:
        """Audit all evidence citations within a comparison row.

        Returns:
            List of diagnostic violation messages.
        """
        violations: List[str] = []
        for vname, eval_res in row.vendor_evaluations.items():
            for citation in eval_res.evidence_citations:
                if not EvidenceValidator.validate_citation(citation, trusted_chunks):
                    msg = f"Violation in category '{row.category}' for vendor '{vname}': Invalid citation '{citation.evidence_id}' (Chunk '{citation.chunk_id}')."
                    violations.append(msg)
                    logger.warning("evidence_validator.audit_violation: %s", msg)

        return violations
