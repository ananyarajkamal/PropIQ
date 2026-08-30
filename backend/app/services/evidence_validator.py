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
