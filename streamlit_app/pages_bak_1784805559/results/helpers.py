"""Results page helpers — image conversion, list rendering, grade utilities, serialisation."""
from __future__ import annotations

import math

import numpy as np

from streamlit_app.ai.inspection_engine import InspectionReport


# ── Image helpers ──────────────────────────────────────────────────────────────


def _bgr_to_rgb(image: np.ndarray) -> np.ndarray:
    """Convert BGR (OpenCV) image to RGB for Streamlit display."""
    if image is None:
        return np.zeros((10, 10, 3), dtype=np.uint8)
    if len(image.shape) == 2:
        return image
    return image[:, :, ::-1]


# ── Render helpers ─────────────────────────────────────────────────────────────


def _render_list(title: str, items: list[str], icon: str = "•") -> None:
    """Render a bullet list with a section title."""
    import streamlit as st

    if not items:
        return
    st.markdown(
        f"<div style='font-size: 0.75rem; color: #64748B; text-transform: uppercase; "
        f"letter-spacing: 0.05em; margin-bottom: 0.4rem;'>{title}</div>",
        unsafe_allow_html=True,
    )
    for item in items:
        st.markdown(
            f"<div style='color: #94A3B8; font-size: 0.85rem; "
            f"padding: 0.15rem 0; line-height: 1.6;'>"
            f"{icon} {item}</div>",
            unsafe_allow_html=True,
        )


# ── Grade utilities ────────────────────────────────────────────────────────────


def _get_grade_color(grade: str) -> str:
    """Get hex color for a letter grade."""
    colors = {
        "A+": "#10B981", "A": "#34D399", "B+": "#6EE7B7",
        "B": "#FBBF24", "C": "#F97316", "D": "#EF4444",
    }
    return colors.get(grade, "#64748B")


def _get_grade_bg(grade: str) -> str:
    """Get background color for a letter grade."""
    bgs = {
        "A+": "rgba(16, 185, 129, 0.15)", "A": "rgba(52, 211, 153, 0.15)",
        "B+": "rgba(110, 231, 183, 0.15)", "B": "rgba(251, 191, 36, 0.15)",
        "C": "rgba(249, 115, 22, 0.15)", "D": "rgba(239, 68, 68, 0.15)",
    }
    return bgs.get(grade, "rgba(100, 116, 139, 0.15)")


# ── Serialisation ──────────────────────────────────────────────────────────────


def _dict_to_report(data: dict) -> InspectionReport:
    """Reconstruct an InspectionReport from a serialised dict.

    Numpy arrays are not serialisable in JSON so they come back as None.
    """
    return InspectionReport(
        file_name=data.get("file_name", ""),
        image_width=data.get("image_width", 0),
        image_height=data.get("image_height", 0),
        file_size_mb=data.get("file_size_mb", 0.0),
        validation_passed=data.get("validation_passed", True),
        validation_error=data.get("validation_error", ""),
        damage_percentage=data.get("damage_percentage", 0.0),
        damage_area_px=data.get("damage_area_px", 0),
        image_area_px=data.get("image_area_px", 0),
        contour_count=data.get("contour_count", 0),
        largest_damage_area_px=data.get("largest_damage_area_px", 0),
        damage_type=data.get("damage_type", "N/A"),
        severity=data.get("severity", "N/A"),
        confidence=data.get("confidence", 0),
        possible_causes=data.get("possible_causes", []) or [],
        repair_steps=data.get("repair_steps", []) or [],
        recommended_professional=data.get("recommended_professional", "N/A"),
        estimated_cost_range=data.get("estimated_cost_range", "N/A"),
        urgency=data.get("urgency", "N/A"),
        prevention_tips=data.get("prevention_tips", []) or [],
        cv_processing_time_sec=data.get("cv_processing_time_sec", 0.0),
        gemini_processing_time_sec=data.get("gemini_processing_time_sec", 0.0),
        total_processing_time_sec=data.get("total_processing_time_sec", 0.0),
        gemini_skipped=data.get("gemini_skipped", False),
        gemini_error=data.get("gemini_error", ""),
        processed_image=None,
        damage_mask=None,
        heatmap=None,
        overlay_image=None,
    )
