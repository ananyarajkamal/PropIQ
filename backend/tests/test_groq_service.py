"""Unit tests for Groq client service module."""

import pytest
from unittest.mock import MagicMock, patch
from app.services.groq_service import (
    GroqService,
    GroqNotConfiguredError,
)


def test_groq_service_missing_api_key():
    """Verify GroqNotConfiguredError is raised when API key is missing."""
    with patch("app.config.Config.get_groq_api_key", return_value=""):
        service = GroqService(api_key="")

        with pytest.raises(GroqNotConfiguredError):
            service.extract_category_evidence(
                vendor_name="Northstar Systems",
                category="Pricing",
                evidence_pack=[{"evidence_id": "E1", "chunk_id": "v01_p001_c001", "text": "Annual cost $180,000."}],
            )


def test_groq_service_empty_evidence_pack():
    """Verify empty evidence pack returns NOT_FOUND immediately without calling API."""
    service = GroqService(api_key="gsk_mock")
    result = service.extract_category_evidence(
        vendor_name="Northstar Systems",
        category="Warranty",
        evidence_pack=[],
    )

    assert result["status"] == "NOT_FOUND"
    assert result["raw_value"] is None
    assert result["cited_evidence_ids"] == []
