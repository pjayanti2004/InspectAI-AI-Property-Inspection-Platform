"""InspectAI configuration validation utilities.

Validates that required environment variables and API keys are set.
Production mode adds stricter checks via streamlit_app.utils.settings.
"""
from __future__ import annotations

import os
from typing import Any

from streamlit_app.utils.logger import get_logger

_logger = get_logger(__name__)


def validate_config() -> list[str]:
    """Validate that required configuration values are present.

    Returns:
        List of error messages for missing/invalid configuration.
        Empty list means all checks passed.
    """
    errors: list[str] = []

    # Check for Gemini API key
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        errors.append(
            "GEMINI_API_KEY is not set. Add it to your .env file or environment variables."
        )
    elif len(api_key) < 10:
        errors.append(
            "GEMINI_API_KEY appears too short. Please check your API key."
        )

    return errors
