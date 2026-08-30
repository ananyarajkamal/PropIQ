"""Centralized logging configuration module for PropIQ FastAPI Backend."""

import logging
import sys
from typing import Optional


def setup_logging(log_level: int = logging.INFO) -> logging.Logger:
    """Configure and return the root logger for PropIQ Backend.

    Args:
        log_level: Desired logging level (default: logging.INFO).

    Returns:
        Configured Logger instance.
    """
    logger = logging.getLogger("propiq_backend")
    logger.setLevel(log_level)

    # Avoid adding duplicate handlers if setup_logging is called multiple times
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(log_level)
        formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


def log_startup_status(logger: Optional[logging.Logger] = None, groq_configured: bool = False) -> None:
    """Log application startup status safely without exposing secrets.

    Args:
        logger: Logger instance to use, or retrieves default if None.
        groq_configured: Boolean flag indicating if Groq API is configured.
    """
    if logger is None:
        logger = setup_logging()

    logger.info("PropIQ FastAPI Backend initializing...")
    logger.info("Configuration check completed. Groq API key status: %s", "Configured" if groq_configured else "Not configured")
