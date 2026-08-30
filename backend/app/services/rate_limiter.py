"""In-memory rate limiter and operation locking service for PropIQ.

Provides lightweight sliding-window rate limiting per session/endpoint and per-session
in-progress operation guards to prevent duplicate expensive tasks and API abuse (Rules 45, 53, 56, 57).
"""

import time
import logging
from typing import Dict, List, Set, Optional
from app.config import Config

logger = logging.getLogger("propiq_backend")


class RateLimitExceededError(Exception):
    """Exception raised when per-session rate limit is exceeded."""
    pass


class OperationInProgressError(Exception):
    """Exception raised when an expensive analysis operation is already running for a session."""
    pass


class SessionRateLimiter:
    """Sliding-window in-memory rate limiter tracking request timestamps per session and endpoint."""

    def __init__(self, limit_per_minute: int = Config.RATE_LIMIT_REQUESTS_PER_MINUTE):
        self.limit_per_minute = limit_per_minute
        self._history: Dict[str, List[float]] = {}

    def check_rate_limit(self, session_id: str, endpoint_key: str = "default") -> None:
        """Check if request is allowed under rate limit.

        Args:
            session_id: Active session identifier string.
            endpoint_key: Endpoint string identifier.

        Raises:
            RateLimitExceededError: If rate limit (20 req/min) is exceeded.
        """
        now = time.time()
        window_start = now - 60.0
        bucket_key = f"{session_id}:{endpoint_key}"

        timestamps = self._history.get(bucket_key, [])
        valid_timestamps = [t for t in timestamps if t > window_start]

        if len(valid_timestamps) >= self.limit_per_minute:
            logger.warning("Rate limit exceeded for session '%s' on endpoint '%s'.", session_id, endpoint_key)
            raise RateLimitExceededError("Rate limit exceeded. Please wait a moment before sending another request.")

        valid_timestamps.append(now)
        self._history[bucket_key] = valid_timestamps

    def prune_old_buckets(self) -> None:
        """Clean up old history buckets older than 10 minutes."""
        now = time.time()
        cutoff = now - 600.0
        expired_keys = []
        for key, timestamps in self._history.items():
            valid = [t for t in timestamps if t > cutoff]
            if not valid:
                expired_keys.append(key)
            else:
                self._history[key] = valid
        for key in expired_keys:
            del self._history[key]


class SessionOperationLock:
    """In-memory lock manager guarding against duplicate concurrent expensive backend jobs per session."""

    def __init__(self):
        self._running_ops: Set[str] = set()

    def acquire_lock(self, session_id: str, operation_key: str) -> str:
        """Acquire lock for a session operation.

        Args:
            session_id: Active session identifier string.
            operation_key: Operation name identifier (e.g. 'extract', 'risks', 'recommendation').

        Returns:
            Lock key string.

        Raises:
            OperationInProgressError: If operation is already running for session.
        """
        lock_key = f"{session_id}:{operation_key}"
        if lock_key in self._running_ops:
            logger.warning("Operation '%s' is already running for session '%s'. Duplicate request blocked.", operation_key, session_id)
            raise OperationInProgressError("An analysis operation is already in progress for this session. Please wait.")
        self._running_ops.add(lock_key)
        return lock_key

    def release_lock(self, lock_key: str) -> None:
        """Release operation lock."""
        self._running_ops.discard(lock_key)

    def is_locked(self, session_id: str, operation_key: str) -> bool:
        """Check if operation is currently locked."""
        return f"{session_id}:{operation_key}" in self._running_ops


# Global singleton instances
_GLOBAL_RATE_LIMITER = SessionRateLimiter()
_GLOBAL_OPERATION_LOCK = SessionOperationLock()


def get_rate_limiter() -> SessionRateLimiter:
    """Retrieve global rate limiter singleton."""
    return _GLOBAL_RATE_LIMITER


def get_operation_lock() -> SessionOperationLock:
    """Retrieve global operation lock singleton."""
    return _GLOBAL_OPERATION_LOCK
