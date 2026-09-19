"""Smoke tests for streamlit_app.ai.inspection_engine, fusion_engine, and health_engine.

These tests verify end-to-end behaviour of each pipeline with minimal synthetic
inputs and mocked external dependencies.  No network calls, no real files.
"""
from __future__ import annotations

import cv2
import numpy as np
import pytest
from unittest.mock import patch, MagicMock

from streamlit_app.ai.inspection_engine import (
    InspectionReport,
    stage_validate,
    stage_opencv,
)
from streamlit_app.ai.health_engine import (
    Grade,
    PropertyHealthReport,
    assess_health,
)
from streamlit_app.ai.fusion_engine import (
    FusedInspection,
    fuse_reports,
)


# ── Helpers ────────────────────────────────────────────────────────────────────

def _make_test_image(width: int = 320, height: int = 240) -> np.ndarray:
    """Solid-gray BGR image (uint8)."""
    return np.full((height, width, 3), 128, dtype=np.uint8)


def _make_report(
    file_name: str = "img_01.jpg",
    damage_type: str = "Crack",
    severity: str = "Medium",
    confidence: int = 85,
    damage_percentage: float = 5.0,
    damage_area_px: int = 3000,
    image_area_px: int = 76800,
    contour_count: int = 2,
    largest_damage_area_px: int = 2000,
    validation_passed: bool = True,
    repair_steps: list[str] | None = None,
    prevention_tips: list[str] | None = None,
    possible_causes: list[str] | None = None,
    urgency: str = "Schedule within 30 days",
    recommended_professional: str = "Structural Engineer",
    estimated_cost_range: str = "3,000 - 10,000",
) -> InspectionReport:
    return InspectionReport(
        file_name=file_name,
        damage_type=damage_type,
        severity=severity,
        confidence=confidence,
        damage_percentage=damage_percentage,
        damage_area_px=damage_area_px,
        image_area_px=image_area_px,
        contour_count=contour_count,
        largest_damage_area_px=largest_damage_area_px,
        validation_passed=validation_passed,
        repair_steps=repair_steps or ["Contact certified inspector"],
        prevention_tips=prevention_tips or ["Schedule regular inspections"],
        possible_causes=possible_causes or ["Aging materials"],
        urgency=urgency,
        recommended_professional=recommended_professional,
        estimated_cost_range=estimated_cost_range,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# inspection_engine — stage functions and run_inspection
# ═══════════════════════════════════════════════════════════════════════════════

class TestInspectionEngineSmoke:

    def test_stage_validate_returns_tuple(self):
        img = _make_test_image()
        result, cv_img, pil_img = stage_validate(img, file_name="t.jpg")
        assert result is not None
        assert cv_img is not None
        assert pil_img is not None
        assert isinstance(cv_img, np.ndarray)

    def test_stage_opencv_returns_metrics(self):
        """stage_opencv returns an InspectionReport with CV metrics."""
        img = _make_test_image()
        result = stage_opencv(img)
        assert isinstance(result, InspectionReport)
        assert result.processed_image is not None
        assert result.damage_mask is not None
        assert result.cv_processing_time_sec >= 0

    def test_stage_opencv_returns_numpy_arrays(self):
        img = _make_test_image()
        result = stage_opencv(img)
        assert isinstance(result.processed_image, np.ndarray)
        assert isinstance(result.damage_mask, np.ndarray)
        assert isinstance(result.overlay_image, np.ndarray)
        assert isinstance(result.cv_processing_time_sec, float)
        assert result.cv_processing_time_sec >= 0

    def test_empty_input_returns_empty_list(self):
        from streamlit_app.ai.inspection_engine import run_inspection
        assert run_inspection([]) == []

    def test_single_image_returns_report(self):
        from streamlit_app.ai.inspection_engine import run_inspection
        img = _make_test_image()

        with patch("streamlit_app.ai.inspection_engine.stage_validate") as mock_val, \
             patch("streamlit_app.ai.inspection_engine.stage_opencv") as mock_ocv, \
             patch("streamlit_app.ai.inspection_engine.stage_gemini") as mock_gem:
            mock_val.return_value = (MagicMock(is_valid=True), img, MagicMock())
            mock_ocv.return_value = InspectionReport(
                file_name="test.jpg", processed_image=img, damage_mask=img,
                overlay_image=img, cv_processing_time_sec=0.1,
            )
            mock_gem.return_value = InspectionReport(
                gemini_skipped=True, damage_type="N/A", severity="Low", confidence=0,
                gemini_processing_time_sec=0.05,
            )

            results = run_inspection([img])

        assert len(results) == 1
        assert isinstance(results[0], InspectionReport)

    def test_reports_have_non_negative_timing(self):
        from streamlit_app.ai.inspection_engine import run_inspection
        img = _make_test_image()

        with patch("streamlit_app.ai.inspection_engine.stage_validate") as mock_val, \
             patch("streamlit_app.ai.inspection_engine.stage_opencv") as mock_ocv, \
             patch("streamlit_app.ai.inspection_engine.stage_gemini") as mock_gem:
            mock_val.return_value = (MagicMock(is_valid=True), img, MagicMock())
            mock_ocv.return_value = InspectionReport(
                file_name="test.jpg", processed_image=img, damage_mask=img,
                overlay_image=img, cv_processing_time_sec=0.1,
            )
            mock_gem.return_value = InspectionReport(
                gemini_skipped=True, damage_type="N/A", severity="Low", confidence=0,
                gemini_processing_time_sec=0.05,
            )

            results = run_inspection([img])

        r = results[0]
        assert r.cv_processing_time_sec >= 0
        assert r.gemini_processing_time_sec >= 0
        assert r.total_processing_time_sec >= 0

    def test_multi_image_returns_list(self):
        from streamlit_app.ai.inspection_engine import run_inspection
        imgs = [_make_test_image(), _make_test_image()]

        with patch("streamlit_app.ai.inspection_engine.stage_validate") as mock_val, \
             patch("streamlit_app.ai.inspection_engine.stage_opencv") as mock_ocv, \
             patch("streamlit_app.ai.inspection_engine.stage_gemini") as mock_gem:
            mock_val.return_value = (MagicMock(is_valid=True), _make_test_image(), MagicMock())
            mock_ocv.return_value = InspectionReport(
                file_name="test.jpg", processed_image=imgs[0], damage_mask=imgs[0],
                overlay_image=imgs[0], cv_processing_time_sec=0.1,
            )
            mock_gem.return_value = InspectionReport(
                gemini_skipped=True, damage_type="N/A", severity="Low", confidence=0,
                gemini_processing_time_sec=0.05,
            )

            results = run_inspection(imgs)

        assert len(results) == 2


# ═══════════════════════════════════════════════════════════════════════════════
# fusion_engine — end-to-end with synthetic reports
# ═══════════════════════════════════════════════════════════════════════════════

class TestFusionEngineSmoke:

    def test_empty_reports_returns_default_fused(self):
        result = fuse_reports([])
        assert isinstance(result, FusedInspection)
        assert result.overall_health_score == 100
        assert result.findings == []

    def test_single_report_propagates_to_composite(self):
        r = _make_report(damage_type="Crack", severity="High", confidence=90)
        result = fuse_reports([r])
        assert isinstance(result, FusedInspection)
        assert result.overall_health_score < 100
        assert len(result.findings) == 1
        assert result.findings[0].damage_type == "Crack"

    def test_worst_severity_selected(self):
        low = _make_report(damage_type="Stain", severity="Low", confidence=80)
        critical = _make_report(damage_type="Crack", severity="Critical", confidence=95)
        result = fuse_reports([low, critical])
        assert isinstance(result, FusedInspection)
        assert result.overall_severity == "Critical"

    def test_total_images_set_correctly(self):
        reports = [_make_report(file_name=f"img_{i}.jpg") for i in range(5)]
        result = fuse_reports(reports)
        assert isinstance(result, FusedInspection)
        assert result.total_images == 5

    def test_health_score_reflects_damage(self):
        clean = _make_report(damage_type="N/A", severity="Low", confidence=0, damage_percentage=0.0)
        damaged = _make_report(damage_type="Crack", severity="High", confidence=90, damage_percentage=20.0)
        result = fuse_reports([clean, damaged])
        assert isinstance(result, FusedInspection)
        assert result.overall_health_score < 100

    def test_repair_steps_collected(self):
        r = _make_report(
            damage_type="Crack",
            repair_steps=["Clean crack", "Apply epoxy", "Sand smooth"],
        )
        result = fuse_reports([r])
        assert isinstance(result, FusedInspection)
        assert len(result.findings[0].repair_steps) >= 1

    def test_clean_inspection_has_perfect_health(self):
        clean = _make_report(damage_type="N/A", severity="Low", confidence=0, damage_percentage=0.0)
        result = fuse_reports([clean])
        assert isinstance(result, FusedInspection)
        assert result.overall_health_score == 100

    def test_damage_type_grouping(self):
        """Two reports with the same damage type are grouped into one FusedFinding."""
        r1 = _make_report(file_name="a.jpg", damage_type="Crack", severity="High", confidence=85)
        r2 = _make_report(file_name="b.jpg", damage_type="Crack", severity="Medium", confidence=75)
        result = fuse_reports([r1, r2])
        assert isinstance(result, FusedInspection)
        damage_types = [f.damage_type for f in result.findings]
        assert "Crack" in damage_types

    def test_fused_has_summary_fields(self):
        r = _make_report(damage_type="Crack", severity="High")
        result = fuse_reports([r])
        assert isinstance(result, FusedInspection)
        assert isinstance(result.property_summary, str)
        assert isinstance(result.inspection_conclusion, str)

    def test_max_confidence_propagated(self):
        r1 = _make_report(damage_type="Crack", severity="High", confidence=60)
        r2 = _make_report(damage_type="Crack", severity="Medium", confidence=95)
        result = fuse_reports([r1, r2])
        assert isinstance(result, FusedInspection)
        assert result.findings[0].confidence == 95


# ═══════════════════════════════════════════════════════════════════════════════
# health_engine — grading and assess_health
# ═══════════════════════════════════════════════════════════════════════════════

class TestHealthEngineSmoke:

    def test_perfect_score_grade_is_A_plus(self):
        assert Grade.from_score(100) == Grade.A_PLUS

    def test_zero_score_grade_is_D(self):
        assert Grade.from_score(0) == Grade.D

    def test_score_95_is_A_plus(self):
        assert Grade.from_score(95) == Grade.A_PLUS

    def test_score_85_is_A(self):
        assert Grade.from_score(85) == Grade.A

    def test_score_79_is_B_plus(self):
        assert Grade.from_score(79) == Grade.B_PLUS

    def test_score_70_is_B_plus(self):
        assert Grade.from_score(70) == Grade.B_PLUS

    def test_score_60_is_B(self):
        assert Grade.from_score(60) == Grade.B

    def test_assess_health_no_damage_returns_perfect_score(self):
        reports = [InspectionReport(
            file_name="clean.jpg",
            damage_type="N/A",
            severity="Low",
            confidence=0,
        )]
        result = assess_health(reports)
        assert isinstance(result, PropertyHealthReport)
        assert result.overall_score >= 90

    def test_assess_health_with_critical_damage_lowers_score(self):
        reports = [InspectionReport(
            file_name="bad.jpg",
            damage_type="Structural Crack",
            severity="Critical",
            confidence=95,
        )]
        result = assess_health(reports)
        assert isinstance(result, PropertyHealthReport)
        assert result.overall_score < 85
        assert result.overall_grade in (Grade.B_PLUS, Grade.B)

    def test_assess_health_multiple_reports(self):
        r1 = InspectionReport(file_name="a.jpg", damage_type="Crack", severity="Medium", confidence=80)
        r2 = InspectionReport(file_name="b.jpg", damage_type="Water Damage", severity="High", confidence=90)
        result = assess_health([r1, r2])
        assert isinstance(result, PropertyHealthReport)
        assert result.overall_score > 0

    def test_assess_health_report_has_all_fields(self):
        r = InspectionReport(file_name="test.jpg", damage_type="Crack", severity="High", confidence=85)
        result = assess_health([r])
        assert isinstance(result, PropertyHealthReport)
        assert hasattr(result, "overall_score")
        assert hasattr(result, "overall_grade")
        assert hasattr(result, "categories")
        assert hasattr(result, "weaknesses")
        assert hasattr(result, "priority_actions")
        assert isinstance(result.health_summary, str)
        assert len(result.health_summary) > 0

    def test_grade_color_hex_values(self):
        a_plus = Grade.A_PLUS
        assert a_plus.color.startswith("#")
        assert len(a_plus.color) == 7

    def test_grade_enum_values(self):
        assert Grade.A_PLUS.value == "A+"
        assert Grade.A.value == "A"
        assert Grade.B.value == "B"
        assert Grade.D.value == "D"
