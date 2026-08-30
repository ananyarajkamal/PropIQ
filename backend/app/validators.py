"""Validation and sanitization helpers for PropIQ FastAPI Backend.

Enforces input validation, filename sanitization, PDF magic header checks,
cryptographically secure high-entropy session ID generation and validation,
and path traversal defense.
"""

import os
import re
import secrets


def generate_secure_session_id() -> str:
    """Generate a cryptographically strong high-entropy session identifier (256 bits entropy).

    Uses secrets.token_urlsafe(32) providing 32 bytes (256 bits) of cryptographically
    random data formatted as URL-safe Base64 string.
    """
    return f"sess_{secrets.token_urlsafe(32)}"


def validate_non_empty_string(value: str, field_name: str = "field") -> str:
    """Validate that a string input is non-empty after stripping whitespace.

    Args:
        value: Input string to validate.
        field_name: Name of the field for error reporting.

    Returns:
        Stripped string.

    Raises:
        ValueError: If value is not a string or is empty/whitespace.
    """
    if not isinstance(value, str):
        raise ValueError(f"Value for '{field_name}' must be a string.")

    stripped = value.strip()
    if not stripped:
        raise ValueError(f"Field '{field_name}' cannot be empty or whitespace only.")

    return stripped


def validate_vendor_name(name: str) -> str:
    """Validate a vendor name string.

    Args:
        name: Vendor name candidate.

    Returns:
        Validated vendor name string.

    Raises:
        ValueError: If vendor name is invalid or exceeds maximum length.
    """
    clean_name = validate_non_empty_string(name, field_name="vendor_name")

    if len(clean_name) > 150:
        raise ValueError("Vendor name must not exceed 150 characters.")

    return clean_name


def sanitize_filename(filename: str) -> str:
    """Sanitize a filename to prevent path traversal and invalid characters.

    Args:
        filename: Proposed filename or file path.

    Returns:
        Sanitized filename safe for local storage operations.

    Raises:
        ValueError: If resulting filename is empty or invalid.
    """
    if not isinstance(filename, str):
        raise ValueError("Filename must be a string.")

    # Remove URL encoding, null bytes, and path traversal markers
    clean = filename.replace("\x00", "").replace("%00", "")

    # Extract basename only to prevent directory traversal
    base_name = os.path.basename(clean.replace("\\", "/"))

    # Remove null bytes and dangerous control characters
    sanitized = re.sub(r"[\x00-\x1f\x7f]", "", base_name)

    # Remove script tags or HTML injection
    sanitized = re.sub(r"<[^>]*>", "", sanitized)

    # Keep alphanumeric, dots, dashes, underscores, and spaces
    sanitized = re.sub(r"[^a-zA-Z0-9._\- ]", "_", sanitized).strip()

    # Remove leading dots or spaces
    sanitized = sanitized.lstrip(". ")

    # Handle reserved Windows filenames (CON, PRN, AUX, NUL, COM1-9, LPT1-9)
    stem = os.path.splitext(sanitized)[0].upper()
    if stem in {"CON", "PRN", "AUX", "NUL", "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9", "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9"}:
        sanitized = f"file_{sanitized}"

    if not sanitized:
        raise ValueError("Sanitized filename resulted in an empty string.")

    return sanitized


def validate_pdf_magic_header(file_bytes: bytes) -> bool:
    """Validate that file content begins with standard PDF magic bytes (%PDF-).

    Args:
        file_bytes: First few bytes or full content of the file.

    Returns:
        True if valid PDF magic header, False otherwise.
    """
    if not file_bytes or len(file_bytes) < 5:
        return False
    return file_bytes.startswith(b"%PDF-") or b"%PDF-" in file_bytes[:1024]


def validate_session_id(session_id: str) -> str:
    """Validate that session_id is a safe, non-empty cryptographically strong session token.

    Args:
        session_id: Session ID input.

    Returns:
        Validated session_id.

    Raises:
        ValueError: If session_id is invalid, malformed, or injection-like.
    """
    if not isinstance(session_id, str):
        raise ValueError("Session ID must be a string.")

    sid = session_id.strip()
    if not sid or len(sid) > 128:
        raise ValueError("Session ID must be non-empty and 128 characters or fewer.")

    # Check for path traversal or script injection in session ID
    if ".." in sid or "/" in sid or "\\" in sid or "<" in sid or ">" in sid or "%" in sid:
        raise ValueError("Invalid session ID format.")

    # Allow alphanumeric, dashes, underscores, and tildes (standard URL-safe Base64)
    if not re.match(r"^[a-zA-Z0-9_\-~]+$", sid):
        raise ValueError("Session ID contains disallowed characters.")

    return sid
