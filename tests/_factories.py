"""Factory helpers for creating synthetic InspectionReport and FusedFinding objects."""
from __future__ import annotations

from streamlit_app.ai.inspection_engine import InspectionReport


def make_report(
    file_name: str = "wall_01.jpg",
    damage_type: str = "Crack",
    severity: str = "Medium",
    confidence: int = 85,
    damage_percentage: float = 5.0,
    damage_pct: float | None = None,
    contour_count: int = 1,
    damage_area_px: int = 4000,
    largest_damage_area_px: int = 4000,
    validation_passed: bool = True,
    total_processing_time_sec: float = 1.5,
    possible_causes: list[str] | None = None,
    repair_steps: list[str] | None = None,
    prevention_tips: list[str] | None = None,
    recommended_professional: str = "Structural Engineer",
    estimated_cost_range: str = "₹5,000 — ₹15,000",
    urgency: str = "Schedule within 30 days",
) -> InspectionReport:
    """Build an InspectionReport with sensible defaults.

    Tests can override any field by passing the kwarg.

    Note: ``damage_pct`` is accepted as a convenience alias for
    ``damage_percentage`` (the dataclass field name).
    """
    if damage_pct is not None:
        damage_percentage = damage_pct

    return InspectionReport(
        file_name=file_name,
        image_width=640,
        image_height=480,
        file_size_mb=0.5,
        validation_passed=validation_passed,
        validation_error="",
        damage_percentage=damage_percentage,
        damage_area_px=damage_area_px,
        image_area_px=640 * 480,
        contour_count=contour_count,
        largest_damage_area_px=largest_damage_area_px,
        damage_type=damage_type,
        severity=severity,
        confidence=confidence,
        possible_causes=possible_causes or ["Thermal expansion", "Foundation settling"],
        repair_steps=repair_steps or ["Clean surface", "Apply filler", "Repaint"],
        recommended_professional=recommended_professional,
        estimated_cost_range=estimated_cost_range,
        urgency=urgency,
        prevention_tips=prevention_tips or ["Annual inspection"],
        total_processing_time_sec=total_processing_time_sec,
    )
