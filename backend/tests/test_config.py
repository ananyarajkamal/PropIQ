"""Unit tests for configuration module."""

from app.config import Config


def test_config_defaults():
    """Verify default application configuration constants."""
    assert Config.APP_NAME == "PropIQ API"
    assert Config.APP_VERSION == "1.0.0-hackathon"
    assert Config.MIN_PROPOSALS == 2
    assert Config.MAX_PROPOSALS == 5
    assert Config.MAX_FILE_SIZE_BYTES == 20 * 1024 * 1024
    assert Config.EMBEDDING_MODEL_NAME == "all-MiniLM-L6-v2"
    assert Config.EMBEDDING_DIMENSION == 384
    assert Config.DEFAULT_TOP_K == 5


def test_missing_groq_api_key(monkeypatch):
    """Verify system handles missing GROQ_API_KEY gracefully."""
    monkeypatch.setattr(Config, "GROQ_API_KEY", "")
    assert Config.is_groq_configured() is False


def test_groq_api_key_detection(monkeypatch):
    """Verify system detects valid GROQ_API_KEY string."""
    monkeypatch.setattr(Config, "GROQ_API_KEY", "gsk_mock_api_key_for_testing_12345")
    assert Config.is_groq_configured() is True


def test_api_key_not_exposed_in_repr():
    """Verify API key is not printed in string outputs."""
    config_repr = repr(Config)
    assert "gsk_" not in config_repr
