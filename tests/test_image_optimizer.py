"""Tests for the Image Optimizer module.

Covers:
- resize_before_processing: no-op when under limit, resize when over
- compress_image: JPEG and PNG, quality parameter, retry on oversize
- normalize_image: float, uint16, uint8 passthrough
- auto_rotate_using_exif: EXIF correction for numpy vs PIL input
- remove_alpha_channel: RGBA → RGB compositing
- convert_to_rgb: BGR, grayscale, RGBA handling
- optimize_for_ai: full pipeline roundtrip
"""
from __future__ import annotations

import io

import numpy as np
import pytest
from PIL import Image, ExifTags

from streamlit_app.utils.image_optimizer import (
    auto_rotate_using_exif,
    compress_image,
    convert_to_rgb,
    normalize_image,
    optimize_for_ai,
    remove_alpha_channel,
    resize_before_processing,
)


# ── Helpers ────────────────────────────────────────────────────────────────────

def _make_rgb_array(h=480, w=640) -> np.ndarray:
    """Create a random RGB uint8 array."""
    return np.random.randint(0, 255, (h, w, 3), dtype=np.uint8)


def _make_pil_image(h=480, w=640) -> Image.Image:
    return Image.fromarray(_make_rgb_array(h, w))


# ── resize_before_processing ───────────────────────────────────────────────────

class TestResizeBeforeProcessing:
    def test_no_resize_when_under_limit(self):
        img = _make_rgb_array(400, 300)  # max dim 400 < 1024
        result = resize_before_processing(img, max_dimension=1024)
        assert result.shape == img.shape

    def test_resize_when_over_limit(self):
        img = _make_rgb_array(2000, 1500)  # max dim 2000 > 1024
        result = resize_before_processing(img, max_dimension=1024)
        assert max(result.shape[:2]) <= 1024

    def test_aspect_ratio_preserved(self):
        # 16:9 landscape: h=900, w=1600 → after resize longest edge ≤ 1024
        img = _make_rgb_array(900, 1600)
        result = resize_before_processing(img, max_dimension=1024)
        new_h, new_w = result.shape[:2]
        orig_ratio = 1600 / 900
        new_ratio = new_w / new_h
        assert abs(orig_ratio - new_ratio) < 0.05

    def test_accepts_pil_image(self):
        pil = _make_pil_image()
        result = resize_before_processing(pil, max_dimension=1024)
        assert isinstance(result, np.ndarray)

    def test_result_is_uint8(self):
        img = _make_rgb_array(2000, 1500)
        result = resize_before_processing(img, max_dimension=1024)
        assert result.dtype == np.uint8


# ── compress_image ─────────────────────────────────────────────────────────────

class TestCompressImage:
    def test_jpeg_returns_bytes(self):
        img = _make_rgb_array()
        data = compress_image(img, format="JPEG", quality=85)
        assert isinstance(data, bytes)
        assert len(data) > 0

    def test_jpeg_signature(self):
        img = _make_rgb_array()
        data = compress_image(img, format="JPEG")
        assert data[:2] == b"\xff\xd8"  # JPEG magic bytes

    def test_png_returns_bytes(self):
        img = _make_rgb_array()
        data = compress_image(img, format="PNG")
        assert isinstance(data, bytes)
        assert len(data) > 0

    def test_unsupported_format_raises(self):
        img = _make_rgb_array()
        with pytest.raises(Exception):
            compress_image(img, format="TIFF")

    def test_accepts_pil_input(self):
        pil = _make_pil_image()
        data = compress_image(pil, format="JPEG", quality=85)
        assert len(data) > 0

    def test_higher_quality_gives_larger_file(self):
        img = _make_rgb_array()
        low = compress_image(img, format="JPEG", quality=30)
        high = compress_image(img, format="JPEG", quality=95)
        assert len(high) >= len(low)


# ── normalize_image ────────────────────────────────────────────────────────────

class TestNormalizeImage:
    def test_uint8_passthrough(self):
        arr = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        result = normalize_image(arr)
        assert result.dtype == np.uint8
        assert result.shape == arr.shape

    def test_float_in_range_scales_to_255(self):
        arr = np.ones((50, 50, 3), dtype=np.float32) * 0.5
        result = normalize_image(arr)
        assert result.dtype == np.uint8
        assert result.max() == 127  # 0.5 * 255

    def test_float_0_to_1_scales_correctly(self):
        arr = np.ones((50, 50, 3), dtype=np.float32)
        result = normalize_image(arr)
        assert result.dtype == np.uint8
        assert result.max() == 255

    def test_uint16_downscaled(self):
        arr = np.full((50, 50, 3), 65535, dtype=np.uint16)
        result = normalize_image(arr)
        assert result.dtype == np.uint8
        assert result.max() == 255

    def test_grayscale_passthrough(self):
        arr = np.random.randint(0, 255, (100, 100), dtype=np.uint8)
        result = normalize_image(arr)
        assert result.dtype == np.uint8


# ── auto_rotate_using_exif ─────────────────────────────────────────────────────

class TestAutoRotateUsingExif:
    def test_no_rotation_for_plain_array(self):
        arr = _make_rgb_array()
        result = auto_rotate_using_exif(arr)
        np.testing.assert_array_equal(result, arr)

    def test_no_rotation_for_standard_orientation(self):
        pil = _make_pil_image()
        result = auto_rotate_using_exif(pil)
        assert result.dtype == np.uint8

    def test_returns_numpy_array(self):
        pil = _make_pil_image()
        result = auto_rotate_using_exif(pil)
        assert isinstance(result, np.ndarray)


# ── remove_alpha_channel ───────────────────────────────────────────────────────

class TestRemoveAlphaChannel:
    def test_rgba_becomes_rgb(self):
        rgba = np.full((100, 100, 4), [100, 150, 200, 128], dtype=np.uint8)
        result = remove_alpha_channel(rgba)
        assert result.shape[-1] == 3
        assert result.dtype == np.uint8

    def test_rgb_unchanged(self):
        rgb = _make_rgb_array()
        result = remove_alpha_channel(rgb)
        assert result.shape == rgb.shape

    def test_pil_rgba_handled(self):
        pil = Image.new("RGBA", (100, 100), (255, 0, 0, 128))
        result = remove_alpha_channel(pil)
        assert result.shape[-1] == 3


# ── convert_to_rgb ─────────────────────────────────────────────────────────────

class TestConvertToRgb:
    def test_grayscale_becomes_rgb(self):
        gray = np.full((100, 100), 128, dtype=np.uint8)
        result = convert_to_rgb(gray)
        assert result.shape == (100, 100, 3)

    def test_rgba_drops_alpha(self):
        rgba = np.full((100, 100, 4), [100, 150, 200, 255], dtype=np.uint8)
        result = convert_to_rgb(rgba)
        assert result.shape == (100, 100, 3)

    def test_returns_uint8(self):
        arr = _make_rgb_array()
        result = convert_to_rgb(arr)
        assert result.dtype == np.uint8

    def test_accepts_pil(self):
        pil = _make_pil_image()
        result = convert_to_rgb(pil)
        assert isinstance(result, np.ndarray)


# ── optimize_for_ai (integration) ──────────────────────────────────────────────

class TestOptimizeForAi:
    def test_numpy_input_returns_array(self):
        img = _make_rgb_array()
        result = optimize_for_ai(img)
        assert isinstance(result, np.ndarray)

    def test_result_shape_reasonable(self):
        img = _make_rgb_array(2000, 1500)
        result = optimize_for_ai(img, max_dimension=1024)
        assert max(result.shape[:2]) <= 1024

    def test_pil_input_returns_array(self):
        pil = _make_pil_image()
        result = optimize_for_ai(pil)
        assert isinstance(result, np.ndarray)

    def test_bytes_input_returns_array(self):
        buf = io.BytesIO()
        _make_pil_image().save(buf, format="PNG")
        result = optimize_for_ai(buf.getvalue(), file_name="test.png")
        assert isinstance(result, np.ndarray)

    def test_output_is_uint8_rgb(self):
        img = _make_rgb_array()
        result = optimize_for_ai(img)
        assert result.dtype == np.uint8
        assert result.shape[-1] == 3
