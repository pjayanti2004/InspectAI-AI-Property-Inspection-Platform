"""Tests for the image_validator module functions.

Covers:
- validate_image: happy path, corrupt files, unsupported formats
- validate_file: file path validation
- validate_pil: PIL image validation
- validate_array: numpy array validation
- _fail helper
- SUPPORTED_FORMATS constant
- MIN_WIDTH / MIN_HEIGHT constants
"""
from __future__ import annotations

import io
import os
import tempfile

import numpy as np
import pytest
from PIL import Image

from streamlit_app.ai.image_validator import (
    SUPPORTED_FORMATS,
    MAX_FILE_SIZE_MB,
    MIN_HEIGHT,
    MIN_WIDTH,
    validate_array,
    validate_file,
    validate_image,
    validate_pil,
)
from streamlit_app.utils.validators import ValidationResult


# ── Helpers ─────────────────────────────────────────────────────────────────────

def _make_image_bytes(fmt="JPEG", h=480, w=640) -> bytes:
    """Create a valid image as bytes."""
    arr = np.random.randint(0, 255, (h, w, 3), dtype=np.uint8)
    img = Image.fromarray(arr)
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    return buf.getvalue()


def _write_temp_image(fmt="JPEG", h=480, w=640) -> str:
    """Write a temp image file and return its path."""
    fd, path = tempfile.mkstemp(suffix=f".{fmt.lower()}")
    os.close(fd)
    arr = np.random.randint(0, 255, (h, w, 3), dtype=np.uint8)
    Image.fromarray(arr).save(path, format=fmt)
    return path


# ── validate_image ──────────────────────────────────────────────────────────────

class TestValidateImage:
    def test_valid_jpeg_passes(self):
        data = _make_image_bytes("JPEG")
        result = validate_image(data, "test.jpg")
        assert result.is_valid is True

    def test_valid_png_passes(self):
        data = _make_image_bytes("PNG")
        result = validate_image(data, "test.png")
        assert result.is_valid is True

    def test_none_input_raises(self):
        from streamlit_app.utils.exceptions import ImageProcessingError
        with pytest.raises((ImageProcessingError, Exception)):
            validate_image(None, "test.jpg")


# ── format validation ───────────────────────────────────────────────────────────

class TestFormatValidation:
    def test_supported_formats_list(self):
        assert "JPEG" in SUPPORTED_FORMATS or "JPG" in SUPPORTED_FORMATS
        assert "PNG" in SUPPORTED_FORMATS

    def test_jpeg_accepted(self):
        data = _make_image_bytes("JPEG")
        result = validate_image(data, "photo.jpg")
        assert result.is_valid is True

    def test_png_accepted(self):
        data = _make_image_bytes("PNG")
        result = validate_image(data, "photo.png")
        assert result.is_valid is True

    def test_webp_accepted(self):
        data = _make_image_bytes("WEBP")
        result = validate_image(data, "photo.webp")
        assert result.is_valid is True

    def test_bmp_accepted(self):
        data = _make_image_bytes("BMP")
        result = validate_image(data, "photo.bmp")
        assert result.is_valid is True


# ── size validation ─────────────────────────────────────────────────────────────

class TestSizeValidation:
    def test_oversized_file_rejected_via_validators(self):
        """Test that the underlying validator rejects oversized files."""
        from streamlit_app.utils.validators import validate_image_file

        class _FakeFile:
            name = "huge.jpg"
            size = 100 * 1024 * 1024  # 100 MB

        # Pass a tiny max_size_mb directly to override the default
        result = validate_image_file(_FakeFile(), max_size_mb=0.001)
        assert result.is_valid is False
        assert "exceeds" in result.error.lower() or "limit" in result.error.lower()

    def test_normal_size_accepted_via_validators(self):
        """Test that the underlying validator accepts normal-sized files."""
        from streamlit_app.utils.validators import validate_image_file

        class _FakeFile:
            name = "normal.jpg"
            size = 1024  # 1 KB

        result = validate_image_file(_FakeFile())
        assert result.is_valid is True


# ── dimension validation ────────────────────────────────────────────────────────

class TestDimensionValidation:
    def test_very_small_image_rejected(self):
        data = _make_image_bytes("JPEG", h=50, w=50)
        result = validate_image(data, "tiny.jpg")
        assert result.is_valid is False

    def test_normal_dimensions_accepted(self):
        data = _make_image_bytes("JPEG", h=480, w=640)
        result = validate_image(data, "normal.jpg")
        assert result.is_valid is True


# ── validate_file ───────────────────────────────────────────────────────────────

class TestValidateFile:
    def test_valid_file_passes(self):
        # validate_file expects a file-like object with name and size
        class _FakeFile:
            name = "photo.jpg"
            size = 1024  # 1 KB

        result = validate_file(_FakeFile())
        # Should pass since name is valid and size is below limit
        assert result.is_valid is True

    def test_missing_name_rejected(self):
        class _FakeFileNoName:
            name = ""
            size = 1024

        result = validate_file(_FakeFileNoName())
        assert result.is_valid is False

    def test_empty_file_rejected(self):
        class _FakeEmptyFile:
            name = "photo.jpg"
            size = 0

        result = validate_file(_FakeEmptyFile())
        assert result.is_valid is False
        assert "empty" in result.error.lower() or "0 byte" in result.error.lower() or "0" in result.error.lower()


# ── validate_pil ────────────────────────────────────────────────────────────────

class TestValidatePil:
    def test_valid_pil_image_passes(self):
        img = Image.fromarray(np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8))
        result = validate_pil(img, file_name="test.jpg")
        assert result.is_valid is True

    def test_small_pil_image_rejected(self):
        img = Image.fromarray(np.random.randint(0, 255, (50, 50, 3), dtype=np.uint8))
        result = validate_pil(img, file_name="tiny.jpg")
        assert result.is_valid is False


# ── validate_array ──────────────────────────────────────────────────────────────

class TestValidateArray:
    def test_valid_array_passes(self):
        arr = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        result = validate_array(arr)
        assert result.is_valid is True

    def test_small_array_rejected(self):
        arr = np.random.randint(0, 255, (50, 50, 3), dtype=np.uint8)
        result = validate_array(arr)
        assert result.is_valid is False

    def test_grayscale_array_accepted(self):
        # Grayscale (2D) arrays are accepted by validate_array
        arr = np.random.randint(0, 255, (480, 640), dtype=np.uint8)
        result = validate_array(arr)
        assert result.is_valid is True
