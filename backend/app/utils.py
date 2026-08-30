"""Utility functions for PropIQ FastAPI Backend."""

import sys
import platform
from typing import Dict, Any


def get_system_info() -> Dict[str, Any]:
    """Retrieve safe non-sensitive system environment metadata.

    Returns:
        Dictionary containing python version and OS platform info.
    """
    return {
        "python_version": sys.version.split()[0],
        "platform": platform.platform(),
        "system": platform.system(),
    }


def format_status_label(is_active: bool) -> str:
    """Format boolean state into a clean text label.

    Args:
        is_active: Boolean flag.

    Returns:
        Formatted status label string without prohibited styling or punctuation.
    """
    return "Configured" if is_active else "Not Configured"
