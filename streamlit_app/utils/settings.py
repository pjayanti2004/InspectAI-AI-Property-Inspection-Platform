"""InspectAI — Production Settings Module.

Centralizes all production configuration in one place.
Reads from environment variables with sensible defaults.
"""
from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Optional

# ── Environment ────────────────────────────────────────────────────────────────

APP_ENV: str = os.getenv("APP_ENV", "development").lower()
IS_PRODUCTION: bool = APP_ENV == "production"
IS_STAGING: bool = APP_ENV == "staging"
IS_DEVELOPMENT: bool = APP_ENV not in ("production", "staging")

# ── Logging ───────────────────────────────────────────────────────────────────

LOG_LEVEL_STR: str = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_LEVEL: int = getattr(logging, LOG_LEVEL_STR, logging.INFO)

# ── Database ──────────────────────────────────────────────────────────────────

_DB_PATH_RAW: str = os.getenv("DATABASE_PATH", "data/inspectai.db")
DATABASE_PATH: Path = Path(_DB_PATH_RAW)
# Ensure parent directory exists
DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

# ── Upload Limits ─────────────────────────────────────────────────────────────

MAX_UPLOAD_MB: int = int(os.getenv("MAX_UPLOAD_MB", "15"))
MAX_UPLOAD_BYTES: int = MAX_UPLOAD_MB * 1024 * 1024

# ── Performance ───────────────────────────────────────────────────────────────

# Image optimization max dimension (pixels)
MAX_IMAGE_DIMENSION: int = 1024

# OpenCV minimum contour area for damage detection
MIN_CONTOUR_AREA: int = 100

# Gemini retry configuration
GEMINI_MAX_RETRIES: int = 3
GEMINI_RETRY_BASE_DELAY: float = 1.0  # seconds
GEMINI_TIMEOUT_SECONDS: int = 30

# Batch processing limits
MAX_BATCH_SIZE: int = 20
MAX_CONCURRENT_ANALYSES: int = 4

# ── Caching ───────────────────────────────────────────────────────────────────

# Session state cache TTL (not used directly — Streamlit manages session state)
# Analysis result cache key prefix
CACHE_KEY_PREFIX: str = "inspectai_"

# ── Resource Limits ───────────────────────────────────────────────────────────

# Memory warning threshold (MB) — used for monitoring
MEMORY_WARNING_MB: int = 2048

# Request timeout (seconds) for Gemini API calls
REQUEST_TIMEOUT_SECONDS: int = 30

# ── Paths ─────────────────────────────────────────────────────────────────────

APP_ROOT: Path = Path(__file__).resolve().parent.parent
DATA_DIR: Path = APP_ROOT / "data"
LOGS_DIR: Path = APP_ROOT / "logs"
UPLOADS_DIR: Path = APP_ROOT / "streamlit_app" / "uploads"

# Ensure directories exist
for _dir in (DATA_DIR, LOGS_DIR, UPLOADS_DIR):
    _dir.mkdir(parents=True, exist_ok=True)


# ── Configuration Summary ─────────────────────────────────────────────────────

def get_config_summary() -> dict:
    """Return a sanitized summary of the current configuration.

    Never includes API keys or secrets.
    """
    return {
        "app_env": APP_ENV,
        "is_production": IS_PRODUCTION,
        "log_level": LOG_LEVEL_STR,
        "database_path": str(DATABASE_PATH),
        "max_upload_mb": MAX_UPLOAD_MB,
        "max_image_dimension": MAX_IMAGE_DIMENSION,
        "max_batch_size": MAX_BATCH_SIZE,
        "gemini_max_retries": GEMINI_MAX_RETRIES,
        "gemini_timeout_seconds": GEMINI_TIMEOUT_SECONDS,
    }


# ── Validation ────────────────────────────────────────────────────────────────

def validate_production_config() -> list[str]:
    """Validate that all required production configuration is present.

    Returns:
        List of error messages. Empty list means all checks passed.
    """
    errors: list[str] = []

    # Always require Gemini API key
    gemini_key: Optional[str] = os.getenv("GEMINI_API_KEY", "").strip() or None
    if not gemini_key:
        errors.append("GEMINI_API_KEY is not set. AI analysis will be unavailable.")

    # Production-specific checks
    if IS_PRODUCTION:
        if APP_ENV == "development":
            errors.append("APP_ENV is 'development' but running in production.")
        if LOG_LEVEL_STR == "DEBUG":
            errors.append("LOG_LEVEL is DEBUG in production — this generates excessive logs.")
        if not DATABASE_PATH.parent.exists():
            errors.append(f"Database directory does not exist: {DATABASE_PATH.parent}")

    return errors
