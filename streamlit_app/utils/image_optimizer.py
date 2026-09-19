"""Image optimization utilities for InspectAI.

Provides functions to resize, compress, normalize, auto-rotate, and
convert images before AI processing.  All operations preserve visual
quality while reducing memory usage and processing time.

Supported formats: PNG, JPEG, WEBP.
"""
from __future__ import annotations

import io
import logging
import time
from typing import Optional, Tuple

import numpy as np
from PIL import Image, ExifTags

from streamlit_app.utils.exceptions import ImageProcessingError
from streamlit_app.utils.logger import get_logger

_logger = get_logger(__name__)

# ── Defaults ──────────────────────────────────────────────────────────────────

# Maximum dimension (px) for images entering the AI pipeline.
# Images larger than this are resized before processing.
DEFAULT_MAX_DIMENSION: int = 1024

# JPEG quality (1-100) for compression.  85 preserves visual quality
# while reducing file size significantly.
DEFAULT_JPEG_QUALITY: int = 85

# PNG compression level (0-9).  6 is a good balance.
DEFAULT_PNG_COMPRESSION: int = 6

# Maximum file size (bytes) after compression.  ~2 MB keeps memory
# usage reasonable for the AI pipeline.
DEFAULT_MAX_FILE_SIZE_BYTES: int = 2 * 1024 * 1024


# ── Public API ────────────────────────────────────────────────────────────────

def resize_before_processing(
    image: np.ndarray | Image.Image,
    max_dimension: int = DEFAULT_MAX_DIMENSION,
    interpolation: int = Image.Resampling.LANCZOS,
) -> np.ndarray:
    """Resize an image so its longest edge does not exceed *max_dimension*.

    Maintains aspect ratio.  No-op if the image is already within the
    size limit.

    Args:
        image:          Input image (H×W×C numpy array in RGB/BGR, or PIL Image).
        max_dimension:  Longest edge cap in pixels.
        interpolation:  PIL resampling filter.

    Returns:
        Resized image as a numpy ndarray (RGB order preserved).
    """
    t0 = _perf_counter()

    if isinstance(image, Image.Image):
        arr = np.array(image)
    else:
        arr = np.asarray(image)

    h, w = arr.shape[:2]
    longest = max(h, w)

    if longest <= max_dimension:
        _logger.debug("resize_before_processing: %dx%d — no resize needed.", w, h)
        return arr

    scale = max_dimension / float(longest)
    new_w, new_h = int(w * scale), int(h * scale)

    pil = Image.fromarray(arr)
    resized = pil.resize((new_w, new_h), interpolation)
    result = np.array(resized)

    elapsed = _perf_counter() - t0
    _logger.debug(
        "resize_before_processing: %dx%d → %dx%d (%.1f ms).",
        w, h, new_w, new_h, elapsed * 1000,
    )
    return result


def compress_image(
    image: np.ndarray | Image.Image,
    format: str = "JPEG",
    quality: int = DEFAULT_JPEG_QUALITY,
    max_file_size_bytes: int = DEFAULT_MAX_FILE_SIZE_BYTES,
) -> bytes:
    """Compress an image to bytes with quality preservation.

    For JPEG, *quality* controls the compression level.  For PNG,
    *quality* is mapped to the compression level (inverted).

    Args:
        image:               Input image.
        format:              Output format: "JPEG", "PNG", or "WEBP".
        quality:             1-100 (JPEG/WEBP) or 0-9 (PNG via compression level).
        max_file_size_bytes: If the compressed image exceeds this, quality
                              is reduced and the function retries.

    Returns:
        Compressed image bytes.

    Raises:
        ImageProcessingError: If compression fails after retries.
    """
    t0 = _perf_counter()

    if isinstance(image, np.ndarray):
        pil = Image.fromarray(image)
    else:
        pil = image.copy()

    fmt = format.upper()
    if fmt not in ("JPEG", "PNG", "WEBP"):
        raise ImageProcessingError(
            f"Unsupported format: {format!r}. Use JPEG, PNG, or WEBP.",
        )

    # JPEG → convert to RGB (no alpha)
    if fmt == "JPEG" and pil.mode in ("RGBA", "P", "LA"):
        pil = pil.convert("RGB")

    kwargs: dict = {"format": fmt}
    if fmt == "JPEG":
        kwargs["quality"] = quality
        kwargs["optimize"] = True
    elif fmt == "PNG":
        kwargs["compress_level"] = min(9, max(0, 9 - quality // 10))
    elif fmt == "WEBP":
        kwargs["quality"] = quality

    buf = io.BytesIO()
    try:
        pil.save(buf, **kwargs)
    except Exception as exc:
        raise ImageProcessingError(
            f"Failed to compress image as {fmt}: {exc}"
        ) from exc

    data = buf.getvalue()

    # If still too large, reduce quality and retry (JPEG only)
    if len(data) > max_file_size_bytes and fmt == "JPEG" and quality > 40:
        _logger.debug(
            "Compressed image (%d bytes) exceeds limit (%d), retrying at lower quality.",
            len(data), max_file_size_bytes,
        )
        return compress_image(image, format, quality - 15, max_file_size_bytes)

    elapsed = _perf_counter() - t0
    _logger.debug(
        "compress_image: %s, %d bytes, %.1f ms.",
        fmt, len(data), elapsed * 1000,
    )
    return data


def normalize_image(image: np.ndarray) -> np.ndarray:
    """Normalize pixel values to the [0, 255] range as uint8.

    Handles float images (0.0-1.0 or 0-1 range) and uint16 images.

    Args:
        image: Input image array.

    Returns:
        Normalized uint8 numpy array.
    """
    t0 = _perf_counter()

    arr = np.asarray(image)
    if arr.dtype == np.uint8:
        result = arr
    elif arr.dtype in (np.float32, np.float64):
        mx = arr.max()
        if mx <= 1.0:
            result = (arr * 255).clip(0, 255).astype(np.uint8)
        else:
            result = arr.clip(0, 255).astype(np.uint8)
    elif arr.dtype == np.uint16:
        result = (arr / 256).astype(np.uint8)
    else:
        result = arr.astype(np.uint8)

    elapsed = _perf_counter() - t0
    _logger.debug("normalize_image: %s → uint8 (%.1f ms).", arr.dtype, elapsed * 1000)
    return result


def auto_rotate_using_exif(image: np.ndarray | Image.Image) -> np.ndarray:
    """Auto-rotate an image based on EXIF orientation metadata.

    Many mobile cameras store the orientation in EXIF rather than
    rotating the pixel data.  This function corrects that.

    Args:
        image: Input image (PIL Image preferred for EXIF access).

    Returns:
        Correctly-oriented image as a numpy array (RGB).
    """
    t0 = _perf_counter()

    if isinstance(image, Image.Image):
        pil = image
        # Pillow >= 9.1 auto-orients on open, but we handle older versions
        exif = pil.getexif()
        orientation = exif.get(0x0112)  # ExifTags.ORIENTATION
        if orientation and orientation != 1:
            _transform = _EXIF_TRANSFORMS.get(orientation)
            if _transform:
                pil = pil.transpose(_transform)
                _logger.debug("auto_rotate_using_exif: corrected orientation %d.", orientation)
        result = np.array(pil)
    else:
        # Numpy arrays don't carry EXIF — return as-is
        result = np.asarray(image)

    elapsed = _perf_counter() - t0
    _logger.debug("auto_rotate_using_exif: %.1f ms.", elapsed * 1000)
    return result


def remove_alpha_channel(image: np.ndarray | Image.Image) -> np.ndarray:
    """Remove alpha channel from RGBA images, compositing onto white.

    Args:
        image: Input image (RGB, RGBA, or other modes).

    Returns:
        RGB image as a numpy array (no alpha channel).
    """
    t0 = _perf_counter()

    if isinstance(image, Image.Image):
        if image.mode == "RGBA":
            background = Image.new("RGB", image.size, (255, 255, 255))
            background.paste(image, mask=image.split()[3])
            result = np.array(background)
        else:
            result = np.array(image.convert("RGB"))
    else:
        arr = np.asarray(image)
        if arr.shape[-1] == 4:
            rgb = arr[..., :3].astype(np.float32)
            alpha = arr[..., 3:4].astype(np.float32) / 255.0
            white = np.full_like(rgb, 255)
            result = (rgb * alpha + white * (1 - alpha)).astype(np.uint8)
        else:
            result = arr

    elapsed = _perf_counter() - t0
    _logger.debug("remove_alpha_channel: %.1f ms.", elapsed * 1000)
    return result


def convert_to_rgb(image: np.ndarray | Image.Image) -> np.ndarray:
    """Ensure an image is in RGB color space.

    Handles BGR (OpenCV default), grayscale, palette, and other modes.

    Args:
        image: Input image.

    Returns:
        RGB image as a numpy array (H×W×3, uint8).
    """
    t0 = _perf_counter()

    if isinstance(image, Image.Image):
        pil = image.convert("RGB")
        result = np.array(pil)
    else:
        arr = np.asarray(image)
        if arr.ndim == 2:
            result = np.stack([arr] * 3, axis=-1)
        elif arr.shape[-1] == 3:
            # Assume BGR (OpenCV) → convert to RGB
            result = arr[:, :, ::-1].copy()
        elif arr.shape[-1] == 4:
            result = arr[:, :, :3]
        else:
            result = arr

    elapsed = _perf_counter() - t0
    _logger.debug("convert_to_rgb: %s → RGB (%.1f ms).", type(image).__name__, elapsed * 1000)
    return result


def optimize_for_ai(
    image: np.ndarray | Image.Image | bytes,
    file_name: str = "",
    max_dimension: int = DEFAULT_MAX_DIMENSION,
) -> np.ndarray:
    """Full optimization pipeline: decode → EXIF rotate → RGBA removal → RGB → normalize → resize.

    This is the single function to call before feeding images into the
    OpenCV / Gemini pipeline.

    Args:
        image:          Input image (numpy array, PIL Image, or raw bytes).
        file_name:      File name hint (for logging).
        max_dimension:  Max longest edge after resize.

    Returns:
        Optimized RGB image as a numpy ndarray (uint8).
    """
    t0 = _perf_counter()
    label = file_name or "<input>"
    if isinstance(image, np.ndarray):
        in_shape = image.shape
    elif isinstance(image, Image.Image):
        in_shape = (image.height, image.width, len(image.getbands()))
    else:
        in_shape = "bytes"

    # Decode bytes if needed
    if isinstance(image, bytes):
        pil = Image.open(io.BytesIO(image))
        pil.load()
    elif isinstance(image, Image.Image):
        pil = image
    else:
        pil = Image.fromarray(np.asarray(image))

    pil = _auto_orient(pil)
    arr = np.array(pil)

    if arr.shape[-1] == 4:
        arr = _remove_alpha(arr)
    if arr.shape[-1] == 3:
        # Assume BGR from OpenCV pipeline → RGB
        arr = arr[:, :, ::-1].copy()

    arr = _clip_normalize(arr)

    h, w = arr.shape[:2]
    longest = max(h, w)
    resized = False
    if longest > max_dimension:
        scale = max_dimension / float(longest)
        new_w, new_h = int(w * scale), int(h * scale)
        pil_rgb = Image.fromarray(arr)
        arr = np.array(pil_rgb.resize((new_w, new_h), Image.Resampling.LANCZOS))
        resized = True

    elapsed = _perf_counter() - t0
    _logger.debug(
        "optimize_for_ai(%s): %dx%d → %dx%d, %.1f ms total.",
        label, w, h, arr.shape[1], arr.shape[0], elapsed * 1000,
    )
    return arr


# ── Internal helpers ──────────────────────────────────────────────────────────

def _auto_orient(pil: Image.Image) -> Image.Image:
    """Correct EXIF orientation."""
    try:
        exif = pil.getexif()
        orientation = exif.get(0x0112)
        if orientation and orientation != 1:
            transform = _EXIF_TRANSFORMS.get(orientation)
            if transform:
                return pil.transpose(transform)
    except Exception:
        pass
    return pil


def _remove_alpha(arr: np.ndarray) -> np.ndarray:
    """Composite RGBA onto white background."""
    rgb = arr[..., :3].astype(np.float32)
    alpha = arr[..., 3:4].astype(np.float32) / 255.0
    white = np.full_like(rgb, 255)
    return (rgb * alpha + white * (1 - alpha)).astype(np.uint8)


def _clip_normalize(arr: np.ndarray) -> np.ndarray:
    """Normalize to uint8."""
    if arr.dtype == np.uint8:
        return arr
    if arr.dtype in (np.float32, np.float64):
        mx = arr.max()
        if mx <= 1.0:
            return (arr * 255).clip(0, 255).astype(np.uint8)
        return arr.clip(0, 255).astype(np.uint8)
    return arr.astype(np.uint8)


# ── EXIF orientation table ────────────────────────────────────────────────────

_EXIF_TRANSFORMS = {
    2: Image.Transpose.FLIP_LEFT_RIGHT,
    3: Image.Transpose.ROTATE_180,
    4: Image.Transpose.FLIP_TOP_BOTTOM,
    5: Image.Transpose.TRANSPOSE,
    6: Image.Transpose.ROTATE_270,
    7: Image.Transpose.TRANSVERSE,
    8: Image.Transpose.ROTATE_90,
}


# ── Timing helper ─────────────────────────────────────────────────────────────

def _perf_counter() -> float:
    """High-resolution timer."""
    return time.perf_counter()
