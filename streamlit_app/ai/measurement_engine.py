"""Professional Damage Measurement & Annotation Engine for InspectAI.

Analyses every detected contour and calculates measurable inspection
statistics for each damage region.

Public API
----------
measure_damage_regions()  — analyse contours → MeasurementReport
annotate_damage()         — generate annotated image, mask, overlay, legend

Design
------
All functions are pure numpy/OpenCV operations — no Streamlit imports.
They consume the outputs of the OpenCV pipeline (mask + contours + bboxes)
and produce measurement data plus annotated images.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import cv2
import numpy as np

from streamlit_app.utils.logger import get_logger

# ── Logging ──────────────────────────────────────────────────────────────────

_logger = get_logger(__name__)

# ── Data Types ────────────────────────────────────────────────────────────────


@dataclass(frozen=False)
class DamageRegion:
    """Measurable properties of a single detected damage region.

    Attributes:
        region_id:             1-based index of this region in the image.
        contour_area_px:       Contour area in pixels.
        bounding_box:          (x, y, width, height) in pixels.
        area_px:               Contour area in pixels.
        area_pct:              Area as percentage of total image area (0-100).
        relative_width:        Bounding-box width as % of image width (0-100).
        relative_height:       Bounding-box height as % of image height (0-100).
        center_x:              Centroid x-coordinate in pixels.
        center_y:              Centroid y-coordinate in pixels.
        perimeter:             Contour perimeter in pixels.
        shape_complexity:      0.0 (simple/rectangular) to 1.0 (highly irregular).
        aspect_ratio:          bbox width / bbox height (>= 1.0).
        approx_crack_length:   Estimated crack length in pixels (perimeter-based).
        approx_crack_width:    Estimated average crack width in pixels.
        damage_coverage:       % of bbox area that is actual damage (0-100).
        estimated_repair_area_px: Estimated repair area in pixels.
    """
    region_id: int = 0
    bounding_box: tuple[int, int, int, int] = (0, 0, 0, 0)
    area_px: int = 0
    area_pct: float = 0.0
    relative_width: float = 0.0
    relative_height: float = 0.0
    center_x: float = 0.0
    center_y: float = 0.0
    perimeter: float = 0.0
    shape_complexity: float = 0.0
    aspect_ratio: float = 1.0
    approx_crack_length: float = 0.0
    approx_crack_width: float = 0.0
    damage_coverage: float = 0.0
    estimated_repair_area_px: int = 0


@dataclass(frozen=True)
class MeasurementReport:
    """Complete measurement analysis for one inspected image.

    Attributes:
        regions:                 Per-region measurements.
        total_repair_area_px:    Sum of estimated repair areas across all regions.
        avg_crack_width:         Mean crack width across all linear regions.
        largest_region:          The DamageRegion with the largest area.
        most_affected_wall:      Quadrant with the most damage ("Top-Left", etc.).
        avg_contour_complexity:  Mean shape complexity (0-1).
        total_damage_px:         Total damage pixels (from mask).
        total_damage_pct:        Total damage as % of image area.
        image_width:             Image width in pixels.
        image_height:            Image height in pixels.
        region_count:            Number of detected regions.
        contours:                Raw contour arrays (for annotation rendering).
    """
    regions: list[DamageRegion] = field(default_factory=list)
    total_repair_area_px: int = 0
    avg_crack_width: float = 0.0
    largest_region: Optional[DamageRegion] = None
    most_affected_wall: str = "Center"
    avg_contour_complexity: float = 0.0
    total_damage_px: int = 0
    total_damage_pct: float = 0.0
    image_width: int = 0
    image_height: int = 0
    region_count: int = 0
    contours: list = field(default_factory=list)


# ── Private measurement helpers ────────────────────────────────────────────────

def _contour_area(contour: np.ndarray) -> int:
    """Return contour area in pixels."""
    return int(cv2.contourArea(contour))


def _contour_perimeter(contour: np.ndarray) -> float:
    """Return contour perimeter in pixels."""
    return float(cv2.arcLength(contour, closed=True))


def _centroid(contour: np.ndarray) -> tuple[float, float]:
    """Compute centroid (moment-based) of a contour."""
    m = cv2.moments(contour)
    if m["m00"] != 0:
        return float(m["m10"] / m["m00"]), float(m["m01"] / m["m00"])
    # Fallback: bounding box center
    x, y, w, h = cv2.boundingRect(contour)
    return x + w / 2.0, y + h / 2.0


def _shape_complexity(contour: np.ndarray, bbox_area: float) -> float:
    """Compute shape complexity as (perimeter² / area) normalised to 0-1.

    A perfect circle has complexity ~0.11 (minimum for any shape).
    A very jagged shape can reach 1.0+.
    We normalise to 0-1 using a sigmoid-like mapping.
    """
    area = cv2.contourArea(contour)
    perimeter = cv2.arcLength(contour, closed=True)
    if area < 1.0 or bbox_area < 1.0:
        return 0.0
    # Circularity ratio: 4*pi*area / perimeter²
    # Circle = 1.0, irregular = lower
    circularity = (4.0 * np.pi * area) / (perimeter * perimeter) if perimeter > 0 else 0.0
    # Invert: high complexity = low circularity
    complexity = max(0.0, 1.0 - circularity)
    return min(1.0, round(complexity, 3))


def _aspect_ratio(bbox: tuple[int, int, int, int]) -> float:
    """Return width/height ratio of a bounding box (>= 1.0)."""
    _, _, w, h = bbox
    if h == 0:
        return 1.0
    return max(w, h) / max(min(w, h), 1)


def _estimate_crack_length(contour: np.ndarray, bbox: tuple[int, int, int, int]) -> float:
    """Estimate crack length from contour perimeter.

    For thin elongated damage (cracks), the perimeter is roughly 2× length + 2× width.
    Solving for length: length ≈ (perimeter - 2×width) / 2
    """
    perimeter = cv2.arcLength(contour, closed=True)
    _, _, w, h = bbox
    # Approximate: thin regions have perimeter ≈ 2×length + small end caps
    # Use the longer dimension of the bbox as a proxy
    longer = max(w, h)
    # Empirical: length ≈ perimeter × 0.4 for elongated shapes
    estimated = perimeter * 0.4
    return round(max(estimated, longer * 0.6), 1)


def _estimate_crack_width(contour: np.ndarray, bbox: tuple[int, int, int, int]) -> float:
    """Estimate average crack width from area and length.

    width ≈ area / length
    """
    area = cv2.contourArea(contour)
    length = _estimate_crack_length(contour, bbox)
    if length > 0:
        return round(area / length, 1)
    return 0.0


def _damage_coverage(contour: np.ndarray, bbox: tuple[int, int, int, int]) -> float:
    """Return what % of the bounding box area is covered by the contour."""
    x, y, w, h = bbox
    bbox_area = w * h
    contour_area = cv2.contourArea(contour)
    if bbox_area > 0:
        return round(min(100.0, (contour_area / bbox_area) * 100.0), 1)
    return 0.0


def _estimated_repair_area(contour: np.ndarray, bbox: tuple[int, int, int, int]) -> int:
    """Estimate the repair area in pixels.

    Expands the contour by ~10% to account for damaged surrounding material
    that must also be repaired (e.g., paint around a crack).
    """
    area = cv2.contourArea(contour)
    # Add ~15% buffer for surrounding damage / material removal
    return int(area * 1.15)


def _wall_quadrant(cx: float, cy: float, w: int, h: int) -> str:
    """Map a centroid to a human-readable wall quadrant."""
    mid_x = w / 2.0
    mid_y = h / 2.0
    h_part = "Top" if cy < mid_y else "Bottom"
    v_part = "Left" if cx < mid_x else "Right"
    if abs(cx - mid_x) < w * 0.15 and abs(cy - mid_y) < h * 0.15:
        return "Center"
    return f"{h_part}-{v_part}"


# ── Core measurement function ──────────────────────────────────────────────────

def measure_damage_regions(
    image: np.ndarray,
    mask: np.ndarray,
    contours: list[np.ndarray],
    bounding_boxes: list[tuple[int, int, int, int]],
    min_area: int = 100,
) -> MeasurementReport:
    """Analyse every detected contour and calculate measurable statistics.

    Args:
        image:           Original BGR image (for dimensions).
        mask:            Binary damage mask (uint8, 0/255).
        contours:        List of contour arrays from cv2.findContours.
        bounding_boxes:  List of (x, y, w, h) tuples from cv2.boundingRect.
        min_area:        Minimum contour area to include (pixels).

    Returns:
        MeasurementReport with per-region measurements and aggregates.
    """
    img_h, img_w = image.shape[:2]
    img_area = img_w * img_h

    # Total damage pixels from mask
    total_damage_px = int(np.count_nonzero(mask))
    total_damage_pct = round((total_damage_px / img_area) * 100, 2) if img_area > 0 else 0.0

    # Filter and measure each region
    regions: list[DamageRegion] = []
    total_repair_area = 0
    crack_widths: list[float] = []
    complexities: list[float] = []
    largest_region: Optional[DamageRegion] = None
    largest_area = 0

    # Wall quadrant damage counters
    quadrant_damage: dict[str, int] = {}

    for idx, (contour, bbox) in enumerate(zip(contours, bounding_boxes), start=1):
        area = _contour_area(contour)
        if area < min_area:
            continue

        x, y, w, h = bbox
        bbox_area = w * h
        perimeter = _contour_perimeter(contour)
        cx, cy = _centroid(contour)
        complexity = _shape_complexity(contour, float(bbox_area))
        ar = _aspect_ratio(bbox)
        crack_len = _estimate_crack_length(contour, bbox)
        crack_w = _estimate_crack_width(contour, bbox)
        coverage = _damage_coverage(contour, bbox)
        repair_area = _estimated_repair_area(contour, bbox)
        rel_w = round((w / img_w) * 100, 2) if img_w > 0 else 0.0
        rel_h = round((h / img_h) * 100, 2) if img_h > 0 else 0.0
        area_pct = round((area / img_area) * 100, 2) if img_area > 0 else 0.0

        region = DamageRegion(
            region_id=idx,
            bounding_box=bbox,
            area_px=area,
            area_pct=area_pct,
            relative_width=rel_w,
            relative_height=rel_h,
            center_x=round(cx, 1),
            center_y=round(cy, 1),
            perimeter=round(perimeter, 1),
            shape_complexity=complexity,
            aspect_ratio=round(ar, 2),
            approx_crack_length=crack_len,
            approx_crack_width=crack_w,
            damage_coverage=coverage,
            estimated_repair_area_px=repair_area,
        )
        regions.append(region)

        total_repair_area += repair_area
        if crack_w > 0:
            crack_widths.append(crack_w)
        complexities.append(complexity)

        # Track largest region
        if area > largest_area:
            largest_area = area
            largest_region = region

        # Track wall quadrant
        quadrant = _wall_quadrant(cx, cy, img_w, img_h)
        quadrant_damage[quadrant] = quadrant_damage.get(quadrant, 0) + area

    # Most affected wall
    most_affected = max(quadrant_damage, key=quadrant_damage.get) if quadrant_damage else "Center"

    # Average crack width (only for linear/elongated regions)
    avg_crack_w = round(sum(crack_widths) / len(crack_widths), 1) if crack_widths else 0.0

    # Average complexity
    avg_complexity = round(sum(complexities) / len(complexities), 3) if complexities else 0.0

    return MeasurementReport(
        regions=regions,
        total_repair_area_px=total_repair_area,
        avg_crack_width=avg_crack_w,
        largest_region=largest_region,
        most_affected_wall=most_affected,
        avg_contour_complexity=avg_complexity,
        total_damage_px=total_damage_px,
        total_damage_pct=total_damage_pct,
        image_width=img_w,
        image_height=img_h,
        region_count=len(regions),
        contours=contours[:len(regions)],
    )


# ── Annotation functions ───────────────────────────────────────────────────────

# Colour palette for annotations (BGR for OpenCV)
_REGION_COLORS = [
    (0, 0, 255),      # Red
    (0, 165, 255),    # Orange
    (0, 255, 255),    # Yellow
    (0, 200, 0),      # Green
    (255, 0, 0),      # Blue
    (255, 0, 255),    # Magenta
    (255, 200, 0),    # Cyan-ish
    (128, 0, 255),    # Purple
]

# Severity → colour mapping (BGR)
_SEVERITY_COLORS_BGR = {
    "Critical": (0, 0, 255),      # Red
    "High": (0, 100, 255),        # Orange-Red
    "Medium": (0, 200, 255),      # Yellow-Orange
    "Low": (0, 220, 0),           # Green
    "N/A": (200, 200, 200),       # Gray
}


def annotate_damage(
    image: np.ndarray,
    report: MeasurementReport,
    contours: Optional[list[np.ndarray]] = None,
    severity_list: Optional[list[str]] = None,
    show_labels: bool = True,
    show_bbox: bool = True,
    show_contour: bool = True,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Generate professional annotations for damage regions.

    Args:
        image:           Original BGR image.
        report:          MeasurementReport from measure_damage_regions().
        contours:        Optional list of contour arrays (matched to report.regions by index).
        severity_list:   Optional list of severity strings matching regions.
        show_labels:     Whether to draw region labels.
        show_bbox:       Whether to draw bounding boxes.
        show_contour:    Whether to draw contour outlines.

    Returns:
        (annotated_image, contour_mask, measurement_overlay)

        annotated_image:    Original + bounding boxes + labels + legend.
        contour_mask:       Binary mask with each region filled in a unique colour.
        measurement_overlay: Semi-transparent overlay showing region measurements.
    """
    h, w = image.shape[:2]
    annotated = image.copy()
    contour_mask = np.zeros((h, w, 3), dtype=np.uint8)
    overlay = image.copy()

    severity_list = severity_list or []
    contours = contours or []

    for i, region in enumerate(report.regions):
        color = _REGION_COLORS[i % len(_REGION_COLORS)]
        sev_color = _SEVERITY_COLORS_BGR.get(
            severity_list[i] if i < len(severity_list) else "N/A",
            (200, 200, 200),
        )
        x, y, bw, bh = region.bounding_box
        label = f"R{region.region_id}"
        pct_label = f"{region.area_pct:.1f}%"

        # Get contour if available, otherwise draw bbox only
        contour = contours[i] if i < len(contours) else None

        # Contour mask — fill with colour
        if contour is not None:
            cv2.drawContours(contour_mask, [contour], -1, color, thickness=cv2.FILLED)

        # Annotated image
        if show_contour and contour is not None:
            cv2.drawContours(annotated, [contour], -1, color, thickness=2)
        if show_bbox:
            cv2.rectangle(annotated, (x, y), (x + bw, y + bh), sev_color, thickness=2)
        if show_labels:
            # Label background
            label_text = f"{label} ({pct_label})"
            (tw, th), _ = cv2.getTextSize(label_text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            label_y = max(y - 8, th + 4)
            cv2.rectangle(
                annotated,
                (x, label_y - th - 4),
                (x + tw + 8, label_y + 4),
                color,
                thickness=cv2.FILLED,
            )
            cv2.putText(
                annotated, label_text,
                (x + 4, label_y),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                (255, 255, 255), 1, cv2.LINE_AA,
            )

        # Measurement overlay — semi-transparent highlight
        if contour is not None:
            cv2.drawContours(overlay, [contour], -1, color, thickness=cv2.FILLED)
            overlay = cv2.addWeighted(overlay, 0.2, image, 0.8, 0)

    # Legend
    annotated = _draw_legend(annotated, report, severity_list)

    return annotated, contour_mask, overlay


def _draw_legend(
    image: np.ndarray,
    report: MeasurementReport,
    severity_list: list[str],
) -> np.ndarray:
    """Draw a professional measurement legend in the bottom-right corner."""
    if not report.regions:
        return image

    h, w = image.shape[:2]
    legend_x = w - 220
    legend_y = h - 10
    line_height = 20
    padding = 10

    entries = []
    for i, region in enumerate(report.regions):
        color = _REGION_COLORS[i % len(_REGION_COLORS)]
        sev = severity_list[i] if i < len(severity_list) else "N/A"
        entries.append((color, f"R{region.region_id}: {region.area_pct:.1f}% | {sev}"))

    # Summary line
    entries.append(((200, 200, 200), f"Total: {report.total_damage_pct:.1f}% | {report.region_count} regions"))

    box_h = len(entries) * line_height + padding * 2
    box_w = 210

    # Background
    cv2.rectangle(image, (legend_x - padding, legend_y - box_h), (legend_x + box_w, legend_y), (30, 30, 30), thickness=cv2.FILLED)
    cv2.rectangle(image, (legend_x - padding, legend_y - box_h), (legend_x + box_w, legend_y), (100, 100, 100), thickness=1)

    for i, (color, text) in enumerate(entries):
        y = legend_y - box_h + padding + (i + 1) * line_height - 4
        cv2.rectangle(image, (legend_x, y - 10), (legend_x + 12, y + 2), color, thickness=cv2.FILLED)
        cv2.putText(image, text, (legend_x + 16, y), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (220, 220, 220), 1, cv2.LINE_AA)

    return image


def draw_measurement_overlay(
    image: np.ndarray,
    report: MeasurementReport,
) -> np.ndarray:
    """Draw measurement callouts (dimensions) on each damage region.

    Draws width and height labels next to each bounding box.
    """
    annotated = image.copy()
    for region in report.regions:
        x, y, w, h = region.bounding_box
        # Dimension labels
        cv2.putText(
            annotated, f"{w}px",
            (x + w + 4, y + h // 2),
            cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1, cv2.LINE_AA,
        )
        cv2.putText(
            annotated, f"{h}px",
            (x + w // 2, y - 4),
            cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1, cv2.LINE_AA,
        )
    return annotated
