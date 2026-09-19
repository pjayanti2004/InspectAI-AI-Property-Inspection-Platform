"""OpenCV-based classical image analysis for InspectAI.

Pre-processes uploaded images (resize, denoise, gray-scale) and detects
potential wall defects via Canny edge detection + contour analysis.

Public API
----------
- ``process_images``            — full pipeline over a list of file-like objects.
- ``preprocess_image``          — resize → denoise → grayscale.
- ``detect_edges``              — Canny edge detection.
- ``detect_contours``           — find and filter contours by area.
- ``analyze_defects``           — score each contour as a potential defect.
- ``generate_severity_report``  — summarise findings by severity level.
- ``DamageMetrics``             — dataclass holding CV damage metrics.
"""

from __future__ import annotations

import cv2
import numpy as np
from dataclasses import dataclass
from pathlib import Path
from PIL import Image
from typing import Any, Sequence

from streamlit_app.utils.exceptions import (
    ImageProcessingError,
    ValidationError,
)
from streamlit_app.utils.logger import get_logger
from streamlit_app.ai.measurement_engine import measure_damage_regions
from streamlit_app.utils.validators import validate_processing_params

# ── Logging ──────────────────────────────────────────────────────────────────

_logger = get_logger(__name__)

# ── Defaults ─────────────────────────────────────────────────────────────────

DEFAULT_MIN_CONTOUR_AREA: int = 100
MIN_CONTOUR_AREA: int = DEFAULT_MIN_CONTOUR_AREA  # alias
DEFAULT_CANNY_LOW: int = 50
DEFAULT_CANNY_HIGH: int = 150
DEFAULT_BLUR_KERNEL: tuple[int, int] = (5, 5)
DEFAULT_RESIZE_MAX: int = 1024


@dataclass
class DamageMetrics:
    """Quantitative damage metrics from CV analysis."""
    damage_percentage: float = 0.0
    damage_area_px: int = 0
    image_area_px: int = 0
    contour_count: int = 0
    largest_damage_area_px: int = 0


# ── Pre-processing ───────────────────────────────────────────────────────────


def preprocess_image(
    source: Any,
    max_dimension: int = DEFAULT_RESIZE_MAX,
    blur_kernel: tuple[int, int] = DEFAULT_BLUR_KERNEL,
) -> np.ndarray:
    """Resize, denoise, and convert an image to grayscale.

    Args:
        source:       File path (``str`` / ``Path``), file-like object,
                      ``PIL.Image``, or numpy ``ndarray``.
        max_dimension: Longest edge is capped at this value.
        blur_kernel:   Gaussian blur kernel size (odd integers).

    Returns:
        Grayscale ``np.ndarray`` ready for edge detection.

    Raises:
        ImageProcessingError: Image cannot be loaded or decoded.
    """
    _logger.debug("Pre-processing image (max_dimension=%d).", max_dimension)

    # Load
    if isinstance(source, np.ndarray):
        img_bgr = source
    elif isinstance(source, Image.Image):
        img_bgr = cv2.cvtColor(np.array(source), cv2.COLOR_RGB2BGR)
    elif isinstance(source, (str, Path)):
        img_bgr = cv2.imread(str(source))
        if img_bgr is None:
            raise ImageProcessingError(
                f"cv2.imread returned None for '{source}'.",
                details={"path": str(source)},
            )
    else:
        # file-like
        raw = source.read()
        arr = np.frombuffer(raw, np.uint8)
        img_bgr = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if img_bgr is None:
            raise ImageProcessingError(
                "cv2.imdecode failed on uploaded file.",
            )

    h, w = img_bgr.shape[:2]
    _logger.debug("Original size: %dx%dpx.", w, h)

    # Resize
    if max(h, w) > max_dimension:
        scale = max_dimension / max(h, w)
        new_w, new_h = int(w * scale), int(h * scale)
        img_bgr = cv2.resize(img_bgr, (new_w, new_h), interpolation=cv2.INTER_AREA)
        _logger.debug("Resized to %dx%dpx.", new_w, new_h)

    # Denoise + grayscale
    blurred = cv2.GaussianBlur(img_bgr, blur_kernel, 0)
    gray = cv2.cvtColor(blurred, cv2.COLOR_BGR2GRAY)

    _logger.debug("Pre-processing complete (output: %dx%d grayscale).", *gray.shape[::-1])
    return gray


# ── Edge Detection ────────────────────────────────────────────────────────────


def detect_edges(
    gray: np.ndarray,
    low: int = DEFAULT_CANNY_LOW,
    high: int = DEFAULT_CANNY_HIGH,
) -> np.ndarray:
    """Apply Canny edge detection to a grayscale image.

    Args:
        gray: Grayscale image array.
        low:  Lower Canny threshold.
        high: Upper Canny threshold.

    Returns:
        Binary edge map as ``np.ndarray`` (dtype uint8, values 0/255).
    """
    _logger.debug("Running Canny edge detection (low=%d, high=%d).", low, high)
    edges = cv2.Canny(gray, low, high)
    edge_count = int(np.count_nonzero(edges))
    _logger.debug("Edge detection complete — %d edge pixels.", edge_count)
    return edges


# ── Contour Detection ────────────────────────────────────────────────────────


def detect_contours(
    edges: np.ndarray,
    min_area: int = DEFAULT_MIN_CONTOUR_AREA,
) -> list[np.ndarray]:
    """Find and filter contours from an edge map.

    Applies morphological closing to fill hollow Canny contours (which
    are the outline of a line/shape, not a solid region) so that
    downstream solidity/fill scoring distinguishes cracks (hollow) from
    blobs (filled).

    Args:
        edges:     Binary edge map from :func:`detect_edges`.
        min_area:  Contours below this pixel area are discarded as noise.

    Returns:
        List of contour arrays (each ``(N, 1, 2)`` int32).

    Raises:
        ValidationError: ``min_area`` is below the safe threshold of 10.
    """
    validate_processing_params(min_contour_area=min_area)

    _logger.debug("Finding contours (min_area=%d).", min_area)
    # Morphological close: connect nearby edges so a thin crack becomes
    # a solid contour, not just two parallel edges of a hollow tube.
    closed = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    filtered = [c for c in contours if cv2.contourArea(c) >= min_area]
    _logger.debug(
        "Found %d total contours, %d after filtering (min_area=%d).",
        len(contours), len(filtered), min_area,
    )
    return filtered


# ── Defect Analysis ───────────────────────────────────────────────────────────


def _classify_damage(
    contour: np.ndarray,
    aspect_ratio: float,
    solidity: float,
    extent_ratio: float,
    fill_ratio: float,
    shape_complexity: float,
    area_px: int,
    cv_image: Optional[np.ndarray] = None,
    bbox: Optional[tuple[int, int, int, int]] = None,
) -> str:
    """Classify a contour into a semantic damage type using multi-feature analysis.

    Classification rules (ordered, first match wins):
      - Crack:               high AR + low solidity (thin elongated break)
      - Surface Crack:       moderate AR + low solidity (shallow linear defect)
      - Water Damage:        low AR + high solidity + large area (active water stain)
      - Moisture Damage:     low AR + high solidity + small/medium area
      - Paint Peeling:       low AR + moderate solidity (flaking surface layer)
      - Spalling:            moderate AR + high solidity + high complexity
      - Mold / Fungus:       very small + near-circular
      - Rust:                reddish-brown dominant color in bbox region
      - Surface Stain:       low AR + moderate extent (general discoloration)
      - Unknown Surface Defect: fallback
    """
    # --- Rust: check BGR color before shape-based rules ---
    if cv_image is not None and bbox is not None:
        x, y, w, h = bbox
        ih, iw = cv_image.shape[:2]
        x0, x1 = max(0, x), min(iw, x + w)
        y0, y1 = max(0, y), min(ih, y + h)
        if x1 > x0 and y1 > y0:
            region = cv_image[y0:y1, x0:x1]
            # Rust is reddish-brown: high R, moderate G, low B in BGR → (low B, med G, high R)
            b_ch, g_ch, r_ch = cv2.split(region)
            mean_b = float(np.mean(b_ch))
            mean_g = float(np.mean(g_ch))
            mean_r = float(np.mean(r_ch))
            # Rust: R > G > B, with R significantly higher than B
            if mean_r > mean_g > mean_b and (mean_r - mean_b) > 30 and mean_r > 80:
                return "Rust"

    # --- Shape-based classification ---
    if aspect_ratio >= 3.0 and solidity < 0.5:
        return "Crack"

    if aspect_ratio >= 1.5 and solidity < 0.5:
        return "Surface Crack"

    if aspect_ratio < 1.5 and solidity > 0.7:
        if area_px > 2000:
            return "Water Damage"
        return "Moisture Damage"

    if aspect_ratio < 1.5 and 0.4 <= solidity <= 0.7:
        return "Paint Peeling"

    if aspect_ratio >= 1.5 and solidity > 0.7 and shape_complexity > 0.4:
        return "Spalling"

    if area_px < 500 and aspect_ratio < 1.3:
        return "Mold / Fungus"

    if aspect_ratio < 1.5 and extent_ratio < 3.0:
        return "Surface Stain"

    return "Unknown Surface Defect"


# ── Defect Analysis ───────────────────────────────────────────────────────────


def analyze_defects(
    contours: list[np.ndarray],
    image_shape: tuple[int, ...],
    cv_image: Optional[np.ndarray] = None,
) -> list[dict[str, Any]]:
    """Score each contour as a potential wall defect and classify its damage type.

    Uses multi-feature analysis: aspect ratio, solidity, extent, fill ratio,
    shape complexity, contour area, and (optionally) dominant color.

    Args:
        contours:    List of contour arrays.
        image_shape: Shape of the source image ``(H, W)`` or ``(H, W, C)``.
        cv_image:    Optional original BGR image for color-based classification (rust).

    Returns:
        Sorted list of defect dicts, highest confidence first.
    """
    img_h, img_w = image_shape[:2]
    img_area = img_h * img_w
    defects: list[dict[str, Any]] = []

    _logger.debug("Analyzing %d contours for defects.", len(contours))

    for idx, contour in enumerate(contours):
        area = float(cv2.contourArea(contour))
        if area <= 0:
            continue

        x, y, w, h = cv2.boundingRect(contour)
        aspect_ratio = w / h if h > 0 else 0

        # ── Feature computation ─────────────────────────────────────────
        hull = cv2.convexHull(contour)
        hull_w = float(hull[:, 0, 0].max() - hull[:, 0, 0].min() + 1)
        hull_h = float(hull[:, 0, 1].max() - hull[:, 0, 1].min() + 1)
        hull_area = float(cv2.contourArea(hull))

        # Extent ratio: how lopsided is the shape across image axes
        extent_x = hull_w / img_w
        extent_y = hull_h / img_h
        if extent_y > 0.001:
            extent_ratio = max(extent_x, extent_y) / min(extent_x, extent_y)
        else:
            extent_ratio = 100.0

        # Solidity: how filled is the convex hull
        solidity = area / hull_area if hull_area > 0 else 0.0

        # Fill ratio: how filled is the bounding box
        bbox_area = float(w * h)
        fill_ratio = area / bbox_area if bbox_area > 0 else 0.0

        # Shape complexity: inverse of circularity (0=smooth circle, 1=very irregular)
        perimeter = cv2.arcLength(contour, closed=True)
        if perimeter > 0 and area > 0:
            circularity = (4.0 * np.pi * area) / (perimeter * perimeter)
            shape_complexity = max(0.0, 1.0 - circularity)
        else:
            shape_complexity = 0.0

        # ── Confidence scoring (0–100) ─────────────────────────────────
        extent_score = min(extent_ratio / 5.0, 1.0) * 35
        solidity_score = (1.0 - solidity) * 35
        fill_score = (1.0 - fill_ratio) * 30

        confidence = int(round(extent_score + solidity_score + fill_score))
        confidence = max(0, min(100, confidence))

        # ── Severity from confidence ───────────────────────────────────
        if confidence >= 60:
            severity = "High"
        elif confidence >= 40:
            severity = "Medium"
        elif confidence >= 20:
            severity = "Low"
        else:
            severity = "Minimal"

        # ── Semantic damage classification ─────────────────────────────
        damage_type = _classify_damage(
            contour=contour,
            aspect_ratio=aspect_ratio,
            solidity=solidity,
            extent_ratio=extent_ratio,
            fill_ratio=fill_ratio,
            shape_complexity=shape_complexity,
            area_px=int(area),
            cv_image=cv_image,
            bbox=(x, y, w, h),
        )

        defect = {
            "id": idx + 1,
            "area_px": int(area),
            "bbox": [int(x), int(y), int(w), int(h)],
            "aspect_ratio": round(aspect_ratio, 2),
            "solidity": round(solidity, 3),
            "extent_ratio": round(extent_ratio, 3),
            "fill_ratio": round(fill_ratio, 3),
            "shape_complexity": round(shape_complexity, 3),
            "confidence": confidence,
            "severity": severity,
            "damage_type": damage_type,
        }
        defects.append(defect)

    defects.sort(key=lambda d: d["confidence"], reverse=True)
    _logger.debug("Identified %d potential defects.", len(defects))
    return defects


# ── Report Generation ─────────────────────────────────────────────────────────


def generate_severity_report(defects: list[dict[str, Any]]) -> dict[str, Any]:
    """Summarise defects by severity level.

    Args:
        defects: List of defect dicts from :func:`analyze_defects`.

    Returns:
        Summary dict with counts, average confidence, and cost estimates.
    """
    severities: dict[str, list[dict[str, Any]]] = {"High": [], "Medium": [], "Low": [], "Minimal": []}

    for d in defects:
        sev = d.get("severity", "Low")
        if sev in severities:
            severities[sev].append(d)

    total = len(defects)
    avg_conf = int(sum(d["confidence"] for d in defects) / total) if total else 0

    cost_map = {"High": 5000, "Medium": 2000, "Low": 500, "Minimal": 100}
    total_cost_min = sum(cost_map.get(d["severity"], 500) for d in defects)
    total_cost_max = int(total_cost_min * 2.5)

    report = {
        "total_defects": total,
        "by_severity": {k: len(v) for k, v in severities.items()},
        "average_confidence": avg_conf,
        "estimated_cost_min": total_cost_min,
        "estimated_cost_max": total_cost_max,
        "defects": defects,
        "status": "Completed",
    }

    _logger.info(
        "Severity report: %d defects (avg confidence %d%%), "
        "cost estimate $%d–$%d.",
        total, avg_conf, total_cost_min, total_cost_max,
    )
    return report


# ── Full Pipeline ─────────────────────────────────────────────────────────────


def process_images(
    sources: list[Any],
    min_contour_area: int = DEFAULT_MIN_CONTOUR_AREA,
    max_dimension: int = DEFAULT_RESIZE_MAX,
) -> dict[str, Any]:
    """Run the full CV pipeline over a list of images.

    Args:
        sources:           List of file paths, file-like objects, PIL
                            Images, or numpy arrays.
        min_contour_area:  Minimum contour area in pixels.
        max_dimension:     Maximum image dimension for resizing.

    Returns:
        Merged severity report dict.

    Raises:
        ValidationError:  ``sources`` is empty or ``min_contour_area`` is invalid.
        ImageProcessingError: Any image fails to load or decode.
    """
    validate_processing_params(min_contour_area=min_contour_area)

    if not sources:
        raise ValidationError("No image sources provided for processing.", field="sources")

    _logger.info("Starting CV pipeline for %d images.", len(sources))

    all_defects: list[dict[str, Any]] = []

    for idx, source in enumerate(sources):
        _logger.debug("Processing image %d/%d.", idx + 1, len(sources))
        try:
            gray = preprocess_image(source, max_dimension=max_dimension)
        except ImageProcessingError:
            _logger.exception("Pre-processing failed for image %d.", idx + 1)
            raise

        edges = detect_edges(gray)
        contours = detect_contours(edges, min_area=min_contour_area)
        defects = analyze_defects(contours, gray.shape, cv_image=source)
        all_defects.extend(defects)

    report = generate_severity_report(all_defects)
    report["images_processed"] = len(sources)
    _logger.info("CV pipeline complete — %d total defects across %d images.", len(all_defects), len(sources))
    return report


def run_full_analysis(
    cv_image: np.ndarray,
    min_contour_area: int = DEFAULT_MIN_CONTOUR_AREA,
    max_dimension: int = DEFAULT_RESIZE_MAX,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, DamageMetrics, Any, list[dict[str, Any]], dict[str, Any]]:
    """Run the full CV pipeline on a single BGR image.

    Args:
        cv_image:        OpenCV BGR image array.
        min_contour_area: Minimum contour area in pixels.
        max_dimension:   Maximum image dimension for resizing.

    Returns:
        (processed_bgr, damage_mask, overlay_bgr, DamageMetrics,
         measurement_report, defects, severity_report)
    """
    _logger.info("Running full CV analysis (shape=%s).", cv_image.shape)

    # Pre-process
    gray = preprocess_image(cv_image, max_dimension=max_dimension)
    h, w = gray.shape

    # Detect edges + contours
    edges = detect_edges(gray)
    contours = detect_contours(edges, min_area=min_contour_area)

    # Analyze defects
    defects = analyze_defects(contours, gray.shape, cv_image=source)
    severity_report = generate_severity_report(defects)

    # Compute metrics
    total_defect_area = sum(d["area_px"] for d in defects)
    image_area = h * w
    damage_pct = (total_defect_area / image_area * 100) if image_area > 0 else 0.0
    largest_defect = max((d["area_px"] for d in defects), default=0)

    metrics = DamageMetrics(
        damage_percentage=round(damage_pct, 2),
        damage_area_px=total_defect_area,
        image_area_px=image_area,
        contour_count=len(contours),
        largest_damage_area_px=largest_defect,
    )

    # Create processed BGR (colorized edges)
    processed_bgr = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)

    # Create damage mask
    mask = np.zeros(gray.shape, dtype=np.uint8)
    for contour in contours:
        cv2.drawContours(mask, [contour], -1, 255, -1)

    # Create overlay
    overlay = processed_bgr.copy()
    mask_region = overlay[mask > 0]
    if mask_region.size > 0:
        blended = cv2.addWeighted(mask_region, 0.7,
                                   np.full_like(mask_region, (0, 100, 255)), 0.3, 0)
        if blended is not None:
            overlay[mask > 0] = blended

    # Placeholder measurement report (filled by measurement_engine)
    bounding_boxes = [cv2.boundingRect(c) for c in contours]
    measurement_report = measure_damage_regions(
        image=cv_image,
        mask=mask,
        contours=contours,
        bounding_boxes=bounding_boxes,
    )

    _logger.info(
        "Full analysis complete -- %d contours, %.1f%% damage, %d defects.",
        len(contours), damage_pct, len(defects),
    )
    return processed_bgr, mask, overlay, metrics, measurement_report, defects, severity_report
