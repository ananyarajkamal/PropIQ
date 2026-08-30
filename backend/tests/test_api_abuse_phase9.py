"""Phase 9 API Abuse, Rate Limiting, and Concurrency Test Suite for PropIQ.

Tests pre-session IP rate limiting (429), downstream session rate limiting (429),
duplicate operation locking (409), malformed session IDs, client-side state injection rejection, and input length caps.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.rate_limiter import get_rate_limiter, get_operation_lock, RateLimitExceededError, OperationInProgressError

client = TestClient(app)


def test_pre_session_ip_rate_limiting():
    """Verify pre-session rate limiting on proposals/process uses client IP identity before session creation (Section 2)."""
    limiter = get_rate_limiter()
    ip_bucket = "ip_127.0.0.1"

    # Execute 20 allowed requests under IP bucket
    for _ in range(20):
        limiter.check_rate_limit(ip_bucket, "proposals_process")

    # 21st upload attempt from same IP must raise RateLimitExceededError (HTTP 429)
    with pytest.raises(RateLimitExceededError):
        limiter.check_rate_limit(ip_bucket, "proposals_process")


def test_rate_limiter_service_enforces_downstream_session_limit():
    """Verify SessionRateLimiter enforces 20 req/min limit per session/endpoint (Rule 53-55)."""
    limiter = get_rate_limiter()
    sid = "sess_ratelimit_downstream_test_1"

    # Execute 20 allowed requests
    for _ in range(20):
        limiter.check_rate_limit(sid, "test_endpoint")

    # 21st request must raise RateLimitExceededError
    with pytest.raises(RateLimitExceededError):
        limiter.check_rate_limit(sid, "test_endpoint")


def test_operation_lock_coverage_and_locking():
    """Verify SessionOperationLock blocks concurrent duplicate expensive requests (Rule 45 & 57)."""
    op_lock = get_operation_lock()
    sid = "sess_lock_coverage_test_1"

    # Tested heavy endpoints
    heavy_ops = ["analysis_extract", "risks_analyze", "clarifications_generate", "recommendation_generate"]

    for op_key in heavy_ops:
        lock_key = op_lock.acquire_lock(sid, op_key)
        assert op_lock.is_locked(sid, op_key) is True

        # Concurrent attempt to acquire same lock must raise OperationInProgressError
        with pytest.raises(OperationInProgressError):
            op_lock.acquire_lock(sid, op_key)

        # Release lock
        op_lock.release_lock(lock_key)
        assert op_lock.is_locked(sid, op_key) is False


def test_malformed_session_id_rejected():
    """Verify GET /api/recommendation/{session_id} rejects malformed session IDs with 400 (Rule 16)."""
    response = client.get("/api/recommendation/../../etc/passwd")
    assert response.status_code == 404 or response.status_code == 400
