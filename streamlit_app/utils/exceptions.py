"""Custom exception hierarchy for InspectAI.

All InspectAI code raises exceptions from this module rather than raw
built-in types so that callers can distinguish, for example, a missing
API key from a database deadlock from an unreadable image file.

Hierarchy
---------
InspectAIError (base)
├── ConfigurationError     — bad / missing config or environment variables
├── ValidationError        — input fails a pre-flight check
├── ImageProcessingError   — OpenCV or PIL failure on a specific image
├── AIServiceError         — Gemini (or future provider) call failed
├── DatabaseError          — SQLite constraint, connection, or query failure
├── ReportGenerationError  — PDF or report rendering failure
└── SessionError           — Streamlit session-state inconsistency
"""

from __future__ import annotations

from typing import Optional


# ── Base ───────────────────────────────────────────────────────────────────────


class InspectAIError(Exception):
    """Base exception for all InspectAI errors.

    Args:
        message:   Human-readable description.
        error_code: Optional machine-readable code for i18n / programmatic handling.
        details:   Optional dict with extra context (field names, file names, etc.).
    """

    def __init__(
        self,
        message: str = "An unexpected error occurred.",
        error_code: Optional[str] = None,
        details: Optional[dict] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__.upper()
        self.details = details or {}

    def __str__(self) -> str:
        if self.details:
            detail_str = ", ".join(f"{k}={v!r}" for k, v in self.details.items())
            return f"{self.message} [{detail_str}]"
        return self.message


# ── Configuration ──────────────────────────────────────────────────────────────


class ConfigurationError(InspectAIError):
    """Raised when required configuration is missing or invalid.

    Examples:
        - GEMINI_API_KEY not set in environment.
        - Database path is not writable.
        - An unsupported property type was configured.
    """

    def __init__(self, message: str, **kwargs: object) -> None:
        super().__init__(message, error_code="CONFIG_ERROR", details=kwargs)


# ── Validation ─────────────────────────────────────────────────────────────────


class ValidationError(InspectAIError):
    """Raised when input validation fails.

    Examples:
        - Image file exceeds maximum size.
        - Image resolution is below minimum threshold.
        - Required form fields are empty.
        - Unsupported image format.
    """

    def __init__(self, message: str, field: str = "", **kwargs: object) -> None:
        details = {"field": field, **kwargs}
        super().__init__(message, error_code="VALIDATION_ERROR", details=details)


# ── Image Processing ───────────────────────────────────────────────────────────


class ImageProcessingError(InspectAIError):
    """Raised when OpenCV or PIL operations fail on an image.

    Examples:
        - Image cannot be decoded.
        - Image is corrupt or truncated.
        - Unsupported number of channels.
    """

    def __init__(self, message: str, file_name: str = "", **kwargs: object) -> None:
        details = {"file_name": file_name, **kwargs}
        super().__init__(message, error_code="IMAGE_PROCESSING_ERROR", details=details)


# ── AI Service ─────────────────────────────────────────────────────────────────


class AIServiceError(InspectAIError):
    """Raised when the AI provider (Gemini) call fails.

    Examples:
        - API key is missing or invalid.
        - Rate limit exceeded.
        - Network timeout.
        - Gemini returned an unexpected response format.
    """

    def __init__(
        self,
        message: str,
        provider: str = "gemini",
        retryable: bool = False,
        error_category: str = "api_error",
        **kwargs: object,
    ) -> None:
        details = {"provider": provider, "retryable": retryable, "error_category": error_category, **kwargs}
        super().__init__(message, error_code="AI_SERVICE_ERROR", details=details)


class GeminiParseError(AIServiceError):
    """Raised when the Gemini response cannot be parsed.

    Sub-class of AIServiceError so callers can handle all AI errors
    uniformly, but can also catch parsing failures specifically.

    Examples:
        - Gemini returned text instead of JSON.
        - JSON was malformed.
        - Response was empty.
    """

    def __init__(self, message: str, raw_response: str = "", **kwargs: object) -> None:
        details = {"error_category": "parse_error", "raw_response_snippet": raw_response[:500], **kwargs}
        super().__init__(message, provider="gemini", retryable=False, **details, **kwargs)


# ── Database ───────────────────────────────────────────────────────────────────


class DatabaseError(InspectAIError):
    """Raised when a database operation fails.

    Examples:
        - Connection cannot be opened.
        - Unique constraint violation.
        - Foreign key violation.
        - Query syntax error.
    """

    def __init__(self, message: str, operation: str = "", **kwargs: object) -> None:
        details = {"operation": operation, **kwargs}
        super().__init__(message, error_code="DATABASE_ERROR", details=details)


# ── Report Generation ──────────────────────────────────────────────────────────


class ReportGenerationError(InspectAIError):
    """Raised when a report cannot be generated.

    Examples:
        - ReportLab fails to render a page.
        - Required data for a report section is missing.
        - PDF output cannot be written to disk.
    """

    def __init__(self, message: str, report_type: str = "", **kwargs: object) -> None:
        details = {"report_type": report_type, **kwargs}
        super().__init__(message, error_code="REPORT_GENERATION_ERROR", details=details)


# ── Session ────────────────────────────────────────────────────────────────────


class SessionError(InspectAIError):
    """Raised when Streamlit session state is inconsistent or missing.

    Examples:
        - Navigating to a wizard step without property data.
        - Upload step reached without completing Step 1.
        - Session state key missing or of the wrong type.
    """

    def __init__(self, message: str, key: str = "", **kwargs: object) -> None:
        details = {"session_key": key, **kwargs}
        super().__init__(message, error_code="SESSION_ERROR", details=details)
