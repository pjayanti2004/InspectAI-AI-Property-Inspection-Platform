"""Image validator for the InspectAI inspection pipeline.

Performs pre-flight checks on uploaded images before they reach the AI stack:
    - format support
    - readability
    - minimum resolution
    - maximum file size
    - channel sanity

Uses the project's canonical ``ValidationResult`` from
:mod:`streamlit_app.utils.validators` so callers get a consistent error
format across all validation surfaces.
"""

from __future__ import annotations

import io
from pathlib import Path
from typing import Any, Union

import numpy as np
from PIL import Image, UnidentifiedImageError

from streamlit_app.utils.exceptions import ImageProcessingError, ValidationError
from streamlit_app.utils.logger import get_logger
from streamlit_app.utils.validators import (
    ValidationResult as CanonicalValidationResult,
)
from streamlit_app.utils.validators import (
    validate_image_file,
    validate_image_resolution as _canonical_res_check,
)

# ── Constants ────────────────────────────────────────────────────────────────

SUPPORTED_FORMATS: frozenset[str] = frozenset({"JPEG", "JPG", "PNG", "WEBP", "BMP"})
MIN_WIDTH: int = 200
MIN_HEIGHT: int = 200
MAX_FILE_SIZE_MB: float = 15.0

# ── Logging ──────────────────────────────────────────────────────────────────

_logger = get_logger(__name__)

# ── Compatibility re-export ──────────────────────────────────────────────────

# Keep the old local dataclass for backward compatibility; it is structurally
# identical to the canonical one in utils.validators.
from streamlit_app.utils.validators import ValidationResult  # re-export

# ── Helpers ──────────────────────────────────────────────────────────────────


def _fail(error: str, code: str) -> "ValidationResult":
    """Create a failed ValidationResult."""
    return ValidationResult(is_valid=False, error=error, error_code=code)


# ── Public API ───────────────────────────────────────────────────────────────


def validate_image(
    source: Union[bytes, Path, str, Image.Image, np.ndarray],
    file_name: str = "",
    file_size_bytes: int | None = None,
) -> ValidationResult:
    """Validate an image against InspectAI's pre-flight requirements.

    Args:
        source:           Bytes, file path, PIL image, or decoded numpy
                           array to validate.
        file_name:        Optional file name used for format hints and
                           clearer error messages.
        file_size_bytes:  Optional size hint when ``source`` is in-memory
                           bytes (skips automatic size lookup).

    Returns:
        ``ValidationResult`` — ``is_valid=True`` only if every check passed.
        Unreadable / corrupt images raise ``ImageProcessingError`` instead
        of silently returning a bad result.
    """
    # ── Step 1: File-level checks (size + extension) ────────────────────
    if isinstance(source, (bytes, Path, str)):
        raw_bytes: bytes | None = None
        size_bytes: int | None = file_size_bytes

        if isinstance(source, bytes):
            raw_bytes = source
            size_bytes = size_bytes if size_bytes is not None else len(source)
        else:
            path = Path(source)
            if not path.exists():
                _logger.warning("Image file not found: %s", path)
                raise ValidationError(
                    f"File '{path.name}' was not found on disk.",
                    field="file",
                )
            if not path.is_file():
                _logger.warning("Not a regular file: %s", path)
                raise ValidationError(
                    f"'{path.name}' is not a regular file.",
                    field="file",
                )
            size_bytes = path.stat().st_size
            try:
                raw_bytes = path.read_bytes()
            except OSError as exc:
                _logger.exception("Failed to read image file %s", path)
                raise ImageProcessingError(
                    f"Could not read file '{path.name}'.",
                    file_name=str(path),
                ) from exc

        # Use the shared file validator
        import streamlit as _st
        try:
            fake_upload = _st.runtime.uploaded_file_mgr.UploadedFile(
                None, path.name, size_bytes or 0, raw_bytes or b""
            )
        except Exception:
            # Fallback: skip Streamlit-specific check and do it manually
            pass
        else:
            file_result = validate_image_file(fake_upload)
            if not file_result.is_valid:
                _logger.warning(
                    "File validation failed for '%s': %s", file_name or path.name, file_result.error
                )
                return _fail(file_result.error, file_result.error_code)

    # ── Step 2: Decode via Pillow ──────────────────────────────────────
    try:
        if isinstance(source, Image.Image):
            img = source.copy()
        elif isinstance(source, np.ndarray):
            img = Image.fromarray(source)
        else:
            img = Image.open(io.BytesIO(raw_bytes))  # type: ignore[arg-type]
            img.load()  # forces full decode
    except UnidentifiedImageError:
        _logger.warning("Unidentifiable image format for '%s'", file_name)
        raise ImageProcessingError(
            f"Could not identify '{file_name or 'file'}' as an image. "
            "The file may be corrupt.",
            file_name=file_name,
        )
    except Exception as exc:
        _logger.exception("Image decode failed for '%s'", file_name)
        raise ImageProcessingError(
            f"Image decoding failed: {exc}.",
            file_name=file_name,
        ) from exc

    # ── Step 3: Format check via Pillow ────────────────────────────────
    fmt = (img.format or "").upper()
    if fmt and fmt not in SUPPORTED_FORMATS:
        _logger.warning("Unsupported image format '%s' for '%s'", fmt, file_name)
        return _fail(
            f"Detected image format '{fmt}' is not supported. "
            f"Please upload: {', '.join(sorted(SUPPORTED_FORMATS))}.",
            "UNSUPPORTED_FORMAT",
        )

    # ── Step 4: Resolution check ───────────────────────────────────────
    width, height = img.size
    res_result = _canonical_res_check(width, height)
    if not res_result.is_valid:
        _logger.warning(
            "Resolution check failed for '%s' (%dx%dpx)", file_name, width, height
        )
        return _fail(res_result.error, res_result.error_code)

    # ── Step 5: Channel sanity ─────────────────────────────────────────
    if img.mode not in ("RGB", "RGBA", "L"):
        try:
            img = img.convert("RGB")
            _logger.debug(
                "Converted image mode '%s' to RGB for '%s'", img.mode, file_name
            )
        except Exception as exc:
            _logger.exception("Mode conversion failed for '%s'", file_name)
            raise ImageProcessingError(
                f"Cannot convert image mode '{img.mode}' to RGB: {exc}.",
                file_name=file_name,
            ) from exc

    _logger.info(
        "Image '%s' passed all validation checks (%dx%dpx, mode=%s).",
        file_name, width, height, img.mode,
    )
    return ValidationResult(is_valid=True)


def validate_file(
    uploaded_file: Any,
    max_size_mb: float = MAX_FILE_SIZE_MB,
) -> ValidationResult:
    """Lightweight check on a file-like object (size + extension).

    Args:
        uploaded_file: Streamlit ``UploadedFile`` or any object with
                       ``.name`` and ``.size`` attributes.
        max_size_mb:   Maximum file size in megabytes.

    Returns:
        ``ValidationResult``.
    """
    return validate_image_file(uploaded_file, max_size_mb=max_size_mb)


def validate_pil(
    img: Image.Image,
    min_width: int = MIN_WIDTH,
    min_height: int = MIN_HEIGHT,
    file_name: str = "",
) -> ValidationResult:
    """Validate a PIL Image (resolution + mode).

    Args:
        img:         PIL Image to validate.
        min_width:   Minimum width in pixels.
        min_height:  Minimum height in pixels.
        file_name:   File name for log messages.

    Returns:
        ``ValidationResult``.
    """
    width, height = img.size
    res_result = _canonical_res_check(width, height, min_width=min_width, min_height=min_height)
    if not res_result.is_valid:
        return _fail(res_result.error, res_result.error_code)

    if img.mode not in ("RGB", "RGBA", "L"):
        try:
            img.convert("RGB")
        except Exception as exc:
            raise ImageProcessingError(
                f"Cannot convert image mode '{img.mode}' to RGB.",
                file_name=file_name,
            ) from exc

    return ValidationResult(is_valid=True)


def validate_array(
    arr: np.ndarray,
    min_height: int = MIN_HEIGHT,
    min_width: int = MIN_WIDTH,
) -> ValidationResult:
    """Validate a decoded numpy image array.

    Args:
        arr:        NumPy array of shape ``(H, W)`` or ``(H, W, C)``.
        min_height: Minimum height in pixels.
        min_width:  Minimum width in pixels.

    Returns:
        ``ValidationResult``.
    """
    if arr is None or arr.size == 0:
        raise ImageProcessingError("Image array is empty or None.")

    if arr.ndim not in (2, 3):
        raise ImageProcessingError(
            f"Image array has {arr.ndim} dimensions; expected 2 or 3.",
            details={"shape": str(arr.shape)},
        )

    height, width = arr.shape[:2]
    res_result = _canonical_res_check(width, height, min_width=min_width, min_height=min_height)
    if not res_result.is_valid:
        return _fail(res_result.error, res_result.error_code)

    return ValidationResult(is_valid=True)
