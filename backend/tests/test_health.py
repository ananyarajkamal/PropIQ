"""Unit tests for /api/health endpoint."""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_endpoint():
    """Verify /api/health endpoint returns 200 OK with Phase 7 status."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "ok"
    assert data["service"] == "PropIQ API"
    assert data["phase"] == "phase7"
    assert "groq_configured" in data


def test_health_endpoint_security():
    """Verify health endpoint does not leak sensitive environment details."""
    response = client.get("/api/health")
    data = response.json()

    assert "api_key" not in data
    assert "groq_api_key" not in data
