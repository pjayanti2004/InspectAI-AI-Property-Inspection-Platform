"""InspectAI utility package.

Submodules
----------
config      Environment / settings validation.
constants   Application-wide constants (colors, thresholds, limits).
exceptions  Custom exception hierarchy.
image_optimizer  Image compression and resizing utilities.
logger      Centralised logging configuration.
performance Timing and performance tracking decorators.
session_manager  Streamlit session state helpers.
validators  Input validation and sanitization functions.
"""
from __future__ import annotations

from streamlit_app.utils.config import validate_config
from streamlit_app.utils.exceptions import (
    AIServiceError,
    ConfigurationError,
    DatabaseError,
    ImageProcessingError,
    InspectAIError,
    ValidationError,
)
from streamlit_app.utils.image_optimizer import optimize_for_ai
from streamlit_app.utils.logger import configure_app_logging, get_logger
from streamlit_app.utils.performance import PerformanceTracker, track_stage
from streamlit_app.utils.session_manager import SessionKeys, navigate_to
from streamlit_app.utils.validators import (
    ValidationResult,
    validate_api_key,
    validate_processing_params,
)

__all__ = [
    "validate_config",
    "AIServiceError",
    "ConfigurationError",
    "DatabaseError",
    "ImageProcessingError",
    "InspectAIError",
    "ValidationError",
    "optimize_for_ai",
    "configure_app_logging",
    "get_logger",
    "PerformanceTracker",
    "track_stage",
    "SessionKeys",
    "navigate_to",
    "ValidationResult",
    "validate_api_key",
    "validate_processing_params",
]
