"""Unit tests for PyMuPDF PDF parser service."""

import pytest
import fitz  # PyMuPDF
from app.services.pdf_parser import (
    parse_pdf_bytes,
    normalize_page_text,
    CorruptedPDFError,
    PasswordProtectedPDFError,
    ScannedPDFError,
)


def create_synthetic_pdf_bytes(pages_text: list[str]) -> bytes:
    """Helper creating in-memory valid PDF bytes for testing."""
    doc = fitz.open()
    for text in pages_text:
        page = doc.new_page()
        page.insert_text((50, 50), text)
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def create_encrypted_pdf_bytes(text: str, password: str = "secret") -> bytes:
    """Helper creating encrypted PDF bytes for testing."""
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), text)
    # Encrypt document
    perm = int(
        fitz.PDF_PERM_ACCESSIBILITY
        | fitz.PDF_PERM_PRINT
        | fitz.PDF_PERM_COPY
    )
    pdf_bytes = doc.tobytes(
        encryption=fitz.PDF_ENCRYPT_AES_256,
        user_pw=password,
        owner_pw="owner",
        permissions=perm,
    )
    doc.close()
    return pdf_bytes


def test_normalize_page_text():
    """Verify conservative text normalization."""
    raw = "Line 1\r\n\r\n\r\nLine 2\n\n\n\nLine 3  "
    clean = normalize_page_text(raw)
    assert "Line 1\n\nLine 2\n\nLine 3" in clean


def test_parse_valid_multi_page_pdf():
    """Verify parsing a valid 2-page PDF."""
    pdf_bytes = create_synthetic_pdf_bytes([
        "Page 1: Proposal for Enterprise Software. Price: $50,000.",
        "Page 2: SLA Guarantee: 99.9% Uptime. Payment terms: Net 30."
    ])
    
    pages, total_chars, page_count = parse_pdf_bytes(pdf_bytes, "proposal.pdf")
    
    assert page_count == 2
    assert len(pages) == 2
    assert pages[0].page_number == 1
    assert "Enterprise Software" in pages[0].text
    assert pages[1].page_number == 2
    assert "99.9% Uptime" in pages[1].text
    assert total_chars > 0


def test_parse_corrupted_pdf():
    """Verify corrupted file raises CorruptedPDFError."""
    bad_bytes = b"NOT_A_REAL_PDF_DATA_CONTENT"
    with pytest.raises(CorruptedPDFError):
        parse_pdf_bytes(bad_bytes, "bad.pdf")


def test_parse_encrypted_pdf():
    """Verify encrypted PDF raises PasswordProtectedPDFError."""
    encrypted_bytes = create_encrypted_pdf_bytes("Secret terms", password="mypassword")
    with pytest.raises(PasswordProtectedPDFError):
        parse_pdf_bytes(encrypted_bytes, "locked.pdf")


def test_parse_empty_text_pdf():
    """Verify PDF with 0 extractable characters raises ScannedPDFError."""
    # Create empty page without text
    doc = fitz.open()
    doc.new_page()
    empty_bytes = doc.tobytes()
    doc.close()
    
    with pytest.raises(ScannedPDFError):
        parse_pdf_bytes(empty_bytes, "scanned.pdf")
