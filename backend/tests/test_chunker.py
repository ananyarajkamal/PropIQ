"""Unit tests for modular text chunking service."""

import pytest
from app.models import PageExtractedText
from app.services.chunker import chunk_document_pages


def test_chunk_document_pages_basic():
    """Verify chunking document with multiple pages preserves page attribution."""
    pages = [
        PageExtractedText(page_number=1, text="Paragraph 1 on Page 1.\n\nParagraph 2 on Page 1.", character_count=45),
        PageExtractedText(page_number=2, text="Paragraph 1 on Page 2.\n\nParagraph 2 on Page 2.", character_count=45),
    ]

    chunks = chunk_document_pages(
        vendor_name="Acme Corp",
        source_filename="acme_proposal.pdf",
        vendor_index=1,
        pages=pages,
        target_chunk_size=1000,
    )

    assert len(chunks) == 2
    chunk1 = chunks[0]
    assert chunk1.vendor_name == "Acme Corp"
    assert chunk1.source_filename == "acme_proposal.pdf"
    assert chunk1.chunk_id.startswith("v01_")
    assert chunk1.start_page == 1
    assert chunk1.end_page == 1

    chunk2 = chunks[1]
    assert chunk2.start_page == 2
    assert chunk2.end_page == 2


def test_chunk_deterministic_ids():
    """Verify chunk IDs are generated deterministically."""
    pages = [PageExtractedText(page_number=1, text="Sample text content for chunking.", character_count=32)]
    
    chunks = chunk_document_pages(
        vendor_name="Beta Inc",
        source_filename="beta_proposal.pdf",
        vendor_index=2,
        pages=pages,
    )

    assert len(chunks) == 1
    assert chunks[0].chunk_id == "v02_p001_c001"
