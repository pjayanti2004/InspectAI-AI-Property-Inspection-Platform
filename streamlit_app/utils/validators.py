"""Input validation utilities for InspectAI.

Every validator returns a ``ValidationResult`` so callers always get:
- a boolean pass/fail,
- a human-readable message suitable for the UI,
- and a machine-readable ``error_code`` for programmatic branching.

Validators
----------
- ``validate_image_file``          — file bytes, size, format
- ``validate_image_resolution``    — width / height minimums
- ``validate_property_form``       — wizard Step 1 fields
- ``validate_session_state``       — wizard step guards
- ``validate_api_key``             — Gemini key presence and format
- ``validate_processing_params``   — min_contour_area and similar
- ``validate_inspection_id``       — database inspection IDs
- ``validate_report_data``         — fused inspection data integrity

Usage::

    from streamlit_app.utils.validators import validate_image_file, validate_property_form

    result = validate_image_file(uploaded_file)
    if not result.is_valid:
        st.error(result.error)
        return

    result = validate_property_form(name, ptype, address, inspector, date)
    if not result.is_valid:
        render_info_box(result.error, box_type="warning")
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional, Sequence

# ── Re-export ValidationResult from the AI module ──────────────────────────────
# Import here so the rest of the codebase can import from utils.validators
# instead of remembering which sub-module owns the type.
from streamlit_app.utils.exceptions import ValidationError  # noqa: E402


@dataclass(frozen=True)
class ValidationResult:
    """Outcome of a validation check.

    Attributes:
        is_valid:  ``True`` when every check passed.
        error:     Human-readable description of the failure.
        error_code: Machine-readable code for programmatic handling.
        field:     Name of the field that failed (when applicable).
    """

    is_valid: bool = True
    error: str = ""
    error_code: str = ""
    field: str = ""


# ── Internal helpers ───────────────────────────────────────────────────────────


def _fail(message: str, error_code: str = "VALIDATION_ERROR", field: str = "") -> ValidationResult:
    """Create a failed ValidationResult."""
    return ValidationResult(is_valid=False, error=message, error_code=error_code, field=field)


def _ok() -> ValidationResult:
    """Create a successful ValidationResult."""
    return ValidationResult(is_valid=True)


# ── Image file validators ──────────────────────────────────────────────────────


# Allowed extensions (uppercased for comparison)
_ALLOWED_EXTENSIONS: frozenset[str] = frozenset({"JPG", "JPEG", "PNG", "WEBP", "BMP"})
_MAX_FILE_SIZE_MB: float = 15.0
_MIN_WIDTH_PX: int = 200
_MIN_HEIGHT_PX: int = 200


def validate_image_file(
    file: Any,
    max_size_mb: float = _MAX_FILE_SIZE_MB,
) -> ValidationResult:
    """Validate an uploaded image file's size and format.

    Checks:
        - File object has a ``.name`` and ``.size`` attribute.
        - File extension is in the allowed list.
        - File size is below ``max_size_mb``.
        - File is not empty (size > 0).

    Args:
        file:      A file-like object (e.g. Streamlit UploadedFile) with
                   ``name`` and ``size`` attributes, or ``None``.
        max_size_mb: Maximum allowed file size in megabytes.

    Returns:
        ValidationResult indicating pass or a specific failure.
    """
    if file is None:
        return _fail("No file provided.", error_code="MISSING_FILE", field="file")

    file_name: str = getattr(file, "name", "")
    file_size: int = getattr(file, "size", 0)

    if not file_name:
        return _fail("File has no name.", error_code="INVALID_FILE", field="file")

    if file_size == 0:
        return _fail(
            f"'{file_name}' is empty (0 bytes).",
            error_code="EMPTY_FILE",
            field="file",
        )

    ext = Path(file_name).suffix.lstrip(".").upper()
    if ext not in _ALLOWED_EXTENSIONS:
        allowed = ", ".join(sorted(_ALLOWED_EXTENSIONS))
        return _fail(
            f"Unsupported format '.{ext.lower()}'. Allowed formats: {allowed}.",
            error_code="UNSUPPORTED_FORMAT",
            field="file",
        )

    size_mb = file_size / (1024 * 1024)
    if size_mb > max_size_mb:
        return _fail(
            f"'{file_name}' is {size_mb:.1f} MB — exceeds the {max_size_mb} MB limit.",
            error_code="FILE_TOO_LARGE",
            field="file",
        )

    return _ok()


def validate_image_resolution(
    width: int,
    height: int,
    min_width: int = _MIN_WIDTH_PX,
    min_height: int = _MIN_HEIGHT_PX,
) -> ValidationResult:
    """Validate that an image meets the minimum resolution requirements.

    Args:
        width:     Image width in pixels.
        height:    Image height in pixels.
        min_width: Minimum acceptable width.
        min_height: Minimum acceptable height.

    Returns:
        ValidationResult with specific resolution error if too small.
    """
    if width < min_width or height < min_height:
        return _fail(
            f"Image resolution {width}x{height}px is below the minimum "
            f"requirement of {min_width}x{min_height}px.",
            error_code="RESOLUTION_TOO_LOW",
            field="resolution",
        )
    return _ok()


def validate_image_file_with_resolution(
    file: Any,
    width: int,
    height: int,
    max_size_mb: float = _MAX_FILE_SIZE_MB,
) -> ValidationResult:
    """Run both file-level and resolution checks in one call.

    Returns the first failing result, or success if both pass.
    """
    result = validate_image_file(file, max_size_mb=max_size_mb)
    if not result.is_valid:
        return result
    return validate_image_resolution(width, height)


# ── Property form validator ────────────────────────────────────────────────────


def validate_property_form(
    property_name: str = "",
    property_type: str = "",
    address: str = "",
    inspector_name: str = "",
    inspection_date: Any = None,
) -> ValidationResult:
    """Validate the Step 1 property details form.

    All fields except ``notes`` are required.

    Args:
        property_name:    Name of the property.
        property_type:    One of the property type strings.
        address:          Street address.
        inspector_name:   Inspector's full name.
        inspection_date:  Date value (any type with string representation).

    Returns:
        ValidationResult.  If invalid, ``error`` names the first missing field.
    """
    if not property_name or not property_name.strip():
        return _fail("Property name is required.", error_code="MISSING_FIELD", field="property_name")

    if not property_type:
        return _fail("Property type is required.", error_code="MISSING_FIELD", field="property_type")

    if not address or not address.strip():
        return _fail("Property address is required.", error_code="MISSING_FIELD", field="address")

    if not inspector_name or not inspector_name.strip():
        return _fail("Inspector name is required.", error_code="MISSING_FIELD", field="inspector_name")

    if inspection_date is None:
        return _fail("Inspection date is required.", error_code="MISSING_FIELD", field="inspection_date")

    return _ok()


# ── Session state validator ────────────────────────────────────────────────────


def validate_session_state(keys: Sequence[str], session: Any = None) -> ValidationResult:
    """Verify that required keys exist in session state.

    Args:
        keys:    Sequence of key names that must be present and truthy.
        session: The session-state object (defaults to ``st.session_state``).

    Returns:
        ValidationResult naming the first missing key.
    """
    import streamlit as st

    state = session if session is not None else st.session_state

    missing: list[str] = []
    for key in keys:
        if not state.get(key):
            missing.append(key)

    if missing:
        return _fail(
            f"Missing required session keys: {', '.join(missing)}.",
            error_code="MISSING_SESSION_KEYS",
            field=",".join(missing),
        )

    return _ok()


# ── API key validator ──────────────────────────────────────────────────────────


def validate_api_key(api_key: Optional[str]) -> ValidationResult:
    """Verify that a Gemini API key is present and has a plausible format.

    Args:
        api_key:  The raw API key string, or ``None`` / empty.

    Returns:
        ValidationResult.  A present but obviously malformed key still passes
        the format check (we do not validate key structure beyond non-empty).
    """
    if not api_key or not api_key.strip():
        return _fail(
            "Gemini API key is not configured. "
            "Add GEMINI_API_KEY to your .env file or environment variables.",
            error_code="MISSING_API_KEY",
            field="gemini_api_key",
        )

    key = api_key.strip()
    if len(key) < 10:
        return _fail(
            "Gemini API key appears too short to be valid.",
            error_code="INVALID_API_KEY",
            field="gemini_api_key",
        )

    return _ok()


# ── Processing parameter validator ─────────────────────────────────────────────


def validate_processing_params(
    min_contour_area: int = 100,
    max_images: int = 20,
) -> ValidationResult:
    """Validate AI processing parameters.

    Args:
        min_contour_area: Minimum contour area in pixels (must be >= 10).
        max_images:       Maximum number of images to process (must be 1-200).

    Returns:
        ValidationResult with the first invalid parameter named.
    """
    if min_contour_area < 10:
        return _fail(
            f"min_contour_area ({min_contour_area}) must be at least 10.",
            error_code="INVALID_PARAM",
            field="min_contour_area",
        )

    if not (1 <= max_images <= 200):
        return _fail(
            f"max_images ({max_images}) must be between 1 and 200.",
            error_code="INVALID_PARAM",
            field="max_images",
        )

    return _ok()


# ── Inspection ID validator ────────────────────────────────────────────────────


def validate_inspection_id(inspection_id: str) -> ValidationResult:
    """Validate an inspection ID format.

    Expected format: ``INS-YYYY-NNNN`` (e.g. ``INS-2026-0043``).

    Args:
        inspection_id: The inspection ID string to validate.

    Returns:
        ValidationResult.
    """
    if not inspection_id or not inspection_id.strip():
        return _fail(
            "Inspection ID is empty.",
            error_code="MISSING_INSPECTION_ID",
            field="inspection_id",
        )

    pattern = re.compile(r"^INS-\d{4}-\d{4}$")
    if not pattern.match(inspection_id.strip()):
        return _fail(
            f"'{inspection_id}' does not match the expected format INS-YYYY-NNNN.",
            error_code="INVALID_INSPECTION_ID_FORMAT",
            field="inspection_id",
        )

    return _ok()


# ── Report data validator ──────────────────────────────────────────────────────


def validate_fused_inspection(fused: Any) -> ValidationResult:
    """Verify that a FusedInspection object has the minimum required data.

    Args:
        fused: A ``FusedInspection`` dataclass instance or a dict.

    Returns:
        ValidationResult.
    """
    if fused is None:
        return _fail(
            "Inspection data is missing. The analysis may not have completed.",
            error_code="MISSING_INSPECTION_DATA",
            field="fused_inspection",
        )

    # Support both dataclass and dict
    total_images = getattr(fused, "total_images", None)
    if total_images is None and isinstance(fused, dict):
        total_images = fused.get("total_images")

    if not total_images or total_images == 0:
        return _fail(
            "No images were analyzed during inspection.",
            error_code="NO_IMAGES_ANALYZED",
            field="total_images",
        )

    return _ok()


def validate_uploaded_files_count(
    uploaded_files: Sequence[Any],
    min_count: int = 1,
    max_count: int = 20,
) -> ValidationResult:
    """Check that the number of uploaded files is within bounds.

    Args:
        uploaded_files: Sequence of uploaded file objects.
        min_count:      Minimum required images.
        max_count:      Maximum allowed images.

    Returns:
        ValidationResult.
    """
    count = len(uploaded_files)

    if count < min_count:
        return _fail(
            f"At least {min_count} image{' is' if min_count == 1 else 's are'} required. "
            f"Currently uploaded: {count}.",
            error_code="NOT_ENOUGH_IMAGES",
            field="uploaded_files",
        )

    if count > max_count:
        return _fail(
            f"Maximum {max_count} images allowed. Currently uploaded: {count}.",
            error_code="TOO_MANY_IMAGES",
            field="uploaded_files",
        )

    return _ok()
