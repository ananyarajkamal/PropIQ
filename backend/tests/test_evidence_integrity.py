"""Evidence integrity and anti-hallucination test suite for PropIQ.

Evaluates exact source-substring validation, canonical 1-indexed page citations,
multi-page provenance traceability, and rejection of hallucinated or ungrounded evidence.
"""

import pytest
from app.models import (
    PageExtractedText,
    ChunkMetadata,
    EvidenceCitationModel,
    CategoryExtractionResult,
    VendorFactSheet,
)
from app.services.chunker import chunk_document_pages
from app.services.evidence_validator import EvidenceValidator, collapse_whitespace


def test_canonical_page_numbering_traceability():
    """Verify PDF pages produce 1-indexed page citations matching chunk metadata."""
    pages = [
        PageExtractedText(page_number=1, text="Pricing detail: $100,000 per year. Commercial terms apply.", character_count=57),
        PageExtractedText(page_number=2, text="Implementation timeline: 30 days deployment duration.", character_count=54),
        PageExtractedText(page_number=3, text="Service Level Agreement: 99.9% monthly uptime guarantee.", character_count=57),
    ]

    chunks = chunk_document_pages(
        vendor_name="Acme Corp",
        source_filename="acme_proposal.pdf",
        vendor_index=1,
        pages=pages,
    )

    assert len(chunks) == 3
    # Page 1 -> start_page=1, end_page=1
    assert chunks[0].start_page == 1
    assert "100,000" in chunks[0].text

    # Page 2 -> start_page=2, end_page=2
    assert chunks[1].start_page == 2
    assert "30 days" in chunks[1].text

    # Page 3 -> start_page=3, end_page=3
    assert chunks[2].start_page == 3
    assert "99.9%" in chunks[2].text


def test_evidence_validator_exact_source_substring_verification():
    """Verify EvidenceValidator accepts valid citations and rejects fabricated/hallucinated excerpts."""
    pages = [
        PageExtractedText(page_number=1, text="The annual cost is $150,000 USD payable Net 30 days.", character_count=53),
    ]
    chunks = chunk_document_pages(
        vendor_name="Northstar Systems",
        source_filename="northstar.pdf",
        vendor_index=1,
        pages=pages,
    )
    chunk_map = {c.chunk_id: c for c in chunks}

    valid_cit = EvidenceCitationModel(
        evidence_id="E1",
        vendor_name="Northstar Systems",
        source_filename="northstar.pdf",
        start_page=1,
        end_page=1,
        chunk_id=chunks[0].chunk_id,
        excerpt_text="The annual cost is $150,000 USD payable Net 30 days.",
    )

    # 1. Valid citation must pass
    assert EvidenceValidator.validate_citation(valid_cit, chunk_map, pages) is True

    # 2. Fabricated chunk_id must fail
    fake_chunk_cit = EvidenceCitationModel(
        evidence_id="E2",
        vendor_name="Northstar Systems",
        source_filename="northstar.pdf",
        start_page=1,
        end_page=1,
        chunk_id="nonexistent_chunk_id",
        excerpt_text="The annual cost is $150,000 USD",
    )
    assert EvidenceValidator.validate_citation(fake_chunk_cit, chunk_map, pages) is False

    # 3. Wrong vendor name must fail
    wrong_vendor_cit = EvidenceCitationModel(
        evidence_id="E1",
        vendor_name="Wrong Vendor",
        source_filename="northstar.pdf",
        start_page=1,
        end_page=1,
        chunk_id=chunks[0].chunk_id,
        excerpt_text="The annual cost is $150,000 USD",
    )
    assert EvidenceValidator.validate_citation(wrong_vendor_cit, chunk_map, pages) is False

    # 4. Fabricated text excerpt not in source must fail
    fabricated_text_cit = EvidenceCitationModel(
        evidence_id="E1",
        vendor_name="Northstar Systems",
        source_filename="northstar.pdf",
        start_page=1,
        end_page=1,
        chunk_id=chunks[0].chunk_id,
        excerpt_text="The annual cost is $999,999 USD completely fabricated quote.",
    )
    assert EvidenceValidator.validate_citation(fabricated_text_cit, chunk_map, pages) is False


def test_cross_vendor_evidence_isolation():
    """Verify Vendor A citation cannot be validated against Vendor B chunk metadata."""
    chunks_a = chunk_document_pages("Vendor A", "vendor_a.pdf", 1, [PageExtractedText(page_number=1, text="Vendor A price $100k", character_count=20)])
    chunks_b = chunk_document_pages("Vendor B", "vendor_b.pdf", 2, [PageExtractedText(page_number=1, text="Vendor B price $200k", character_count=20)])

    map_a = {c.chunk_id: c for c in chunks_a}
    map_b = {c.chunk_id: c for c in chunks_b}

    cit_a = EvidenceCitationModel(
        evidence_id="E1",
        vendor_name="Vendor A",
        source_filename="vendor_a.pdf",
        start_page=1,
        end_page=1,
        chunk_id=chunks_a[0].chunk_id,
        excerpt_text="Vendor A price $100k",
    )

    # Valid against Vendor A map
    assert EvidenceValidator.validate_citation(cit_a, map_a) is True

    # Invalid against Vendor B map (cross-vendor leakage blocked)
    assert EvidenceValidator.validate_citation(cit_a, map_b) is False
