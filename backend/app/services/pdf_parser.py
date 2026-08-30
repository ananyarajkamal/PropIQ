"""PyMuPDF PDF parsing service for PropIQ.

Extracts text page-by-page from vendor proposal PDFs while preserving page-level
evidence traceability metadata.
"""

import re
from typing import List, Tuple
import fitz  # PyMuPDF
from app.config import Config
from app.models import PageExtractedText


class PDFParsingError(Exception):
    """Base exception class for PDF validation and parsing failures."""
    pass


class PasswordProtectedPDFError(PDFParsingError):
    """Exception raised when a PDF is encrypted or password-protected."""
    pass


class CorruptedPDFError(PDFParsingError):
    """Exception raised when a PDF file structure is corrupted or unreadable."""
    pass


class ScannedPDFError(PDFParsingError):
    """Exception raised when a PDF contains no extractable text (image/scanned)."""
    pass


class PageLimitExceededError(PDFParsingError):
    """Exception raised when a PDF exceeds the maximum page limit."""
    pass


class TextLimitExceededError(PDFParsingError):
    """Exception raised when a document exceeds the maximum extracted characters limit."""
    pass


def normalize_page_text(raw_text: str) -> str:
    """Conservatively normalize extracted page text without altering contract meaning.

    Collapses excessive blank lines while preserving numbers, currency, SLAs,
    percentages, dates, and punctuation.

    Args:
        raw_text: Raw string extracted from a PDF page.

    Returns:
        Conservatively normalized string.
    """
    if not raw_text:
        return ""

    # Replace carriage returns with standard newlines
    text = raw_text.replace("\r\n", "\n").replace("\r", "\n")

    # Collapse 3 or more consecutive newlines into 2 (paragraph break)
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Strip leading/trailing blank spaces per line while keeping line structure
    lines = [line.strip() for line in text.split("\n")]
    text = "\n".join(lines).strip()

    return text


def parse_pdf_bytes(pdf_bytes: bytes, filename: str) -> Tuple[List[PageExtractedText], int, int]:
    """Parse PDF file bytes into page-level extracted text models.

    Args:
        pdf_bytes: Raw bytes of the uploaded PDF file.
        filename: Original filename for logging and diagnostic context.

    Returns:
        Tuple of (list of PageExtractedText, total character count, total page count).

    Raises:
        CorruptedPDFError: If file header signature is invalid or PyMuPDF fails to open document.
        PasswordProtectedPDFError: If PDF is encrypted or password-protected.
        ScannedPDFError: If PDF contains pages but zero extractable text (scanned PDF).
        PageLimitExceededError: If page count exceeds MAX_PAGES_PER_PDF (250).
        TextLimitExceededError: If extracted text exceeds MAX_EXTRACTED_CHARS_PER_DOC (500k).
    """
    if not pdf_bytes or len(pdf_bytes) < 5:
        raise CorruptedPDFError("The uploaded file is empty or too small to be a valid PDF.")

    # Validate PDF signature magic bytes (%PDF-)
    if not pdf_bytes.startswith(b"%PDF-"):
        raise CorruptedPDFError("File content signature does not match standard PDF format.")

    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    except Exception as exc:
        raise CorruptedPDFError("This PDF could not be read. Please upload a valid PDF file.") from exc

    try:
        # Check password protection
        if doc.is_encrypted:
            # Attempt blank password authentication
            if not doc.authenticate(""):
                raise PasswordProtectedPDFError(
                    "This PDF is password protected. Please upload an unlocked version."
                )

        page_count = len(doc)
        if page_count == 0:
            raise CorruptedPDFError("The PDF contains 0 pages.")

        if page_count > Config.MAX_PAGES_PER_PDF:
            raise PageLimitExceededError(
                f"Document exceeds maximum page limit ({page_count} pages uploaded, max allowed is {Config.MAX_PAGES_PER_PDF})."
            )

        pages_extracted: List[PageExtractedText] = []
        total_character_count = 0

        for page_index in range(page_count):
            page_num = page_index + 1
            page = doc[page_index]

            raw_text = page.get_text("text")
            clean_text = normalize_page_text(raw_text)
            char_count = len(clean_text)

            total_character_count += char_count
            if total_character_count > Config.MAX_EXTRACTED_CHARS_PER_DOC:
                raise TextLimitExceededError(
                    f"Document exceeds maximum extracted character limit ({total_character_count} chars, max allowed is {Config.MAX_EXTRACTED_CHARS_PER_DOC})."
                )

            pages_extracted.append(
                PageExtractedText(
                    page_number=page_num,
                    text=clean_text,
                    character_count=char_count,
                )
            )

        if total_character_count == 0:
            raise ScannedPDFError(
                "Scanned or image-based PDF detected. OCR is not currently supported."
            )

        return pages_extracted, total_character_count, page_count

    finally:
        doc.close()
