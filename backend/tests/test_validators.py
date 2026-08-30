"""Unit tests for PropIQ Backend validation and sanitization helpers."""

import pytest
from app.validators import (
    validate_non_empty_string,
    validate_vendor_name,
    sanitize_filename,
)


def test_validate_non_empty_string_valid():
    """Verify valid string passes validation."""
    assert validate_non_empty_string("  Acme Corp  ") == "Acme Corp"


def test_validate_non_empty_string_invalid():
    """Verify empty or whitespace-only string raises ValueError."""
    with pytest.raises(ValueError, match="cannot be empty"):
        validate_non_empty_string("   ")
        
    with pytest.raises(ValueError, match="must be a string"):
        validate_non_empty_string(123)  # type: ignore


def test_validate_vendor_name_valid():
    """Verify valid vendor name passes."""
    assert validate_vendor_name("  Global Logistics Solutions  ") == "Global Logistics Solutions"


def test_validate_vendor_name_empty():
    """Verify empty vendor name raises ValueError."""
    with pytest.raises(ValueError):
        validate_vendor_name("")


def test_validate_vendor_name_too_long():
    """Verify excessively long vendor name raises ValueError."""
    long_name = "A" * 151
    with pytest.raises(ValueError, match="exceed 150 characters"):
        validate_vendor_name(long_name)


def test_sanitize_filename_standard():
    """Verify normal filename sanitization."""
    assert sanitize_filename("vendor_proposal_2026.pdf") == "vendor_proposal_2026.pdf"


def test_sanitize_filename_path_traversal():
    """Verify path traversal characters are stripped safely."""
    assert sanitize_filename("../../secret_folder/proposal.pdf") == "proposal.pdf"
    assert sanitize_filename("C:\\Windows\\System32\\proposal.pdf") == "proposal.pdf"


def test_sanitize_filename_suspicious_characters():
    """Verify dangerous shell/path characters are sanitized."""
    result = sanitize_filename("proposal<1>?*|:;.pdf")
    assert "<" not in result
    assert ">" not in result
    assert "?" not in result
    assert "*" not in result
    assert ":" not in result


def test_sanitize_filename_empty_result():
    """Verify sanitization resulting in empty string raises ValueError."""
    with pytest.raises(ValueError, match="empty string"):
        sanitize_filename("../../../")
