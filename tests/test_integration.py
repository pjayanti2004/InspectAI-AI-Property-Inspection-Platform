"""End-to-end integration tests for the InspectAI inspection pipeline.

Covers the full flow:
  1. Image validation (image_validator)
  2. Classical CV analysis (opencv_engine)
  3. Report merging (summary_engine)
  4. Health & risk assessment
  5. Full report building

Uses small synthetic images (numpy arrays) and mocks for external services.
"""
from __future__ import annotations

import os
from unittest.mock import patch, MagicMock

import numpy as np
from PIL import Image

from streamlit_app.ai.image_validator import validate_array
from streamlit_app.ai.opencv_engine import run_full_analysis
from streamlit_app.report.summary_engine import (
    build_executive_summary,
    build_findings,
    build_timeline,
    build_recommendations,
    build_checklist,
    ExecutiveSummary,
)
from streamlit_app.report.risk_engine import assess_risk, RiskAssessment
from streamlit_app.ai.inspection_engine import InspectionReport


# ── helpers ─────────────────────────────────────────────────────────────────────

def _make_test_image(width=640, height=480, noise=50) -> np.ndarray:
    """Create a small test image with some noise (simulating potential damage)."""
    rng = np.random.default_rng(42)
    img = rng.integers(100 - noise, 100 + noise, (height, width, 3), dtype=np.uint8)
    # Add a dark rectangular "defect" region
    img[100:200, 100:200] = 30
    return img


# ── integration tests ───────────────────────────────────────────────────────────

class TestValidationToCVPipeline:
    """Test the validation → CV analysis path directly."""

    def test_valid_large_image_analyzes(self):
        """A large valid image should pass validation and CV analysis."""
        arr = _make_test_image(width=1920, height=1080)
        result = validate_array(arr)
        assert result.is_valid is True

        # run_full_analysis returns (processed, mask, heatmap, metrics, overlay)
        _, _, _, metrics, _ = run_full_analysis(arr, min_contour_area=100)
        assert hasattr(metrics, 'contour_count')
        assert hasattr(metrics, 'damage_percentage')

    def test_invalid_small_image_rejected_before_cv(self):
        """A too-small image should fail validation (no CV needed)."""
        arr = np.zeros((50, 50, 3), dtype=np.uint8)
        result = validate_array(arr)
        assert result.is_valid is False

    def test_grayscale_image_accepted_by_validator(self):
        """Grayscale (2D) images pass validation but may fail CV."""
        arr = np.random.randint(0, 255, (480, 640), dtype=np.uint8)
        result = validate_array(arr)
        assert result.is_valid is True

    def test_different_contour_thresholds(self):
        """Different min_contour_area values should produce different results."""
        arr = _make_test_image()
        _, _, _, metrics_low, _ = run_full_analysis(arr, min_contour_area=5)
        _, _, _, metrics_high, _ = run_full_analysis(arr, min_contour_area=500)
        # Lower threshold should find at least as many contours
        assert metrics_low.contour_count >= metrics_high.contour_count


class TestInspectionPipeline:
    """Test the full pipeline from raw image to structured report data."""

    def test_validate_then_analyze_cv(self):
        """Validate array → run CV analysis → get damage metrics."""
        arr = _make_test_image()
        result = validate_array(arr)
        assert result.is_valid is True

        _, _, _, metrics, _ = run_full_analysis(arr, min_contour_area=10)
        assert hasattr(metrics, 'contour_count')
        assert metrics.contour_count >= 0

    def test_cv_finds_damage_in_synthetic_image(self):
        """CV should detect the dark rectangle as a contour in our synthetic image."""
        arr = _make_test_image()
        _, _, _, metrics, _ = run_full_analysis(arr, min_contour_area=10)
        # The dark rectangle should be detected as damage
        assert metrics.contour_count > 0
        assert metrics.damage_percentage > 0

    def test_full_pipeline_to_executive_summary(self):
        """Run CV → build report → get executive summary."""
        arr = _make_test_image()
        validation = validate_array(arr)
        assert validation.is_valid

        _, _, _, metrics, _ = run_full_analysis(arr, min_contour_area=10)

        report = InspectionReport(
            file_name="test_image.jpg",
            image_width=arr.shape[1],
            image_height=arr.shape[0],
            validation_passed=True,
            damage_percentage=metrics.damage_percentage,
            damage_area_px=metrics.damage_area_px,
            contour_count=metrics.contour_count,
            severity="High",
            confidence=85,
            damage_type="Crack",
            estimated_cost_range="$5000–$15000",
            repair_steps=["Seal crack", "Monitor"],
            possible_causes=["Settlement"],
            recommended_professional="Structural Engineer",
            urgency="Urgent",
            prevention_tips=["Annual inspection"],
            total_processing_time_sec=2.0,
        )

        property_data = {
            "property_name": "Test Property",
            "property_type": "House",
            "property_address": "123 Test St",
        }

        summary = build_executive_summary([report], property_data)
        assert isinstance(summary, ExecutiveSummary)
        assert summary.property_name == "Test Property"
        assert summary.total_findings >= 0

    def test_full_pipeline_to_findings(self):
        """Verify findings are produced from CV + Gemini combined data."""
        arr = _make_test_image()
        validation = validate_array(arr)
        assert validation.is_valid

        _, _, _, metrics, _ = run_full_analysis(arr, min_contour_area=10)

        report = InspectionReport(
            file_name="synthetic.jpg",
            validation_passed=True,
            damage_percentage=metrics.damage_percentage,
            contour_count=metrics.contour_count,
            severity="High",
            confidence=85,
            damage_type="Crack",
            estimated_cost_range="$5000–$15000",
            repair_steps=["Seal crack", "Monitor"],
            possible_causes=["Settlement"],
            recommended_professional="Structural Engineer",
            urgency="Urgent",
            prevention_tips=["Annual inspection"],
        )

        findings = build_findings([report])
        # Should have findings if damage was detected
        if metrics.damage_percentage >= 0.1 or metrics.contour_count > 0:
            assert len(findings) >= 1

    def test_full_pipeline_to_timeline(self):
        """Verify findings are bucketed into timeline correctly."""
        report = InspectionReport(
            file_name="test.jpg",
            validation_passed=True,
            damage_percentage=5.0,
            contour_count=2,
            severity="Critical",
            confidence=95,
            damage_type="Foundation",
            repair_steps=["Emergency repair"],
            possible_causes=["Structural failure"],
            recommended_professional="Licensed engineer",
            urgency="Immediate",
            prevention_tips=["Regular inspection"],
        )

        findings = build_findings([report])
        timeline = build_timeline(findings)

        assert len(timeline) == 4
        # Critical should be in "Immediate" bucket
        immediate = next((e for e in timeline if "Immediate" in e.bucket), None)
        assert immediate is not None
        assert len(immediate.findings) == 1

    def test_full_pipeline_to_recommendations(self):
        """Verify recommendations are generated from findings."""
        report = InspectionReport(
            file_name="test.jpg",
            validation_passed=True,
            severity="High",
            repair_steps=["Fix roof flashing"],
            possible_causes=["Weather damage"],
            recommended_professional="Roofer",
            urgency="Urgent",
            prevention_tips=["Annual roof check"],
        )

        recommendations = build_recommendations([report])
        assert isinstance(recommendations, dict)
        assert "immediate_actions" in recommendations
        assert len(recommendations["immediate_actions"]) == 1
        assert "Fix roof flashing" in recommendations["immediate_actions"][0]

    def test_full_pipeline_to_checklist(self):
        """Verify checklist is generated with damage categories marked."""
        report = InspectionReport(
            file_name="test.jpg",
            validation_passed=True,
            damage_type="Crack",
        )

        checklist = build_checklist([report])
        assert len(checklist) > 0
        # "Crack" maps to "Structural Cracks" → should be checked
        structural = [i for i in checklist if "Crack" in i.get("category", "")]
        if structural:
            assert structural[0]["status"] == "checked"

    def test_multiple_images_merged_in_batch(self):
        """Test that batch processing merges results from multiple images."""
        reports = [
            InspectionReport(
                file_name="img1.jpg",
                validation_passed=True,
                damage_percentage=10.0,
                contour_count=3,
                severity="High",
                confidence=80,
                damage_type="Water Damage",
                estimated_cost_range="$8000–$20000",
                repair_steps=["Fix leak"],
                possible_causes=["Old plumbing"],
                recommended_professional="Plumber",
                urgency="Urgent",
                prevention_tips=["Check pipes annually"],
            ),
            InspectionReport(
                file_name="img2.jpg",
                validation_passed=True,
                damage_percentage=5.0,
                contour_count=1,
                severity="Medium",
                confidence=75,
                damage_type="Crack",
                estimated_cost_range="$3000–$10000",
                repair_steps=["Fill crack"],
                possible_causes=["Settlement"],
                recommended_professional="Contractor",
                urgency="Moderate",
                prevention_tips=["Monitor quarterly"],
            ),
        ]

        summary = build_executive_summary(reports, property_data={})
        findings = build_findings(reports)
        timeline = build_timeline(findings)
        recommendations = build_recommendations(reports)
        checklist = build_checklist(reports)

        assert summary.image_count == 2
        assert len(findings) >= 2
        assert len(timeline) == 4
        assert "immediate_actions" in recommendations
        assert len(checklist) > 0


class TestRiskAssessment:
    """Test risk assessment from inspection reports."""

    def test_risk_from_single_high_severity_report(self):
        # contour_count > 0 is required for assess_risk to process the report
        report = InspectionReport(
            file_name="test.jpg",
            validation_passed=True,
            contour_count=3,
            severity="Critical",
            confidence=95,
            damage_type="Foundation",
            damage_percentage=20.0,
            estimated_cost_range="$50000–$100000",
            repair_steps=["Emergency"],
            possible_causes=["Structural"],
            recommended_professional="Engineer",
            urgency="Immediate",
            prevention_tips=["Inspect"],
        )
        risk = assess_risk([report])
        assert isinstance(risk, RiskAssessment)
        # Critical severity with high damage → High/Critical risk
        assert risk.risk_level in ("High", "Critical")

    def test_risk_from_low_severity_report(self):
        report = InspectionReport(
            file_name="test.jpg",
            validation_passed=True,
            contour_count=1,
            severity="Low",
            confidence=60,
            damage_type="Paint Peeling",
            damage_percentage=2.0,
            estimated_cost_range="$500–$3000",
            repair_steps=["Repaint"],
            possible_causes=["Weather"],
            recommended_professional="Painter",
            urgency="Schedule within 30 days",
            prevention_tips=["Repaint every 5 years"],
        )
        risk = assess_risk([report])
        assert risk.risk_level in ("Low", "Medium")

    def test_risk_from_failed_validation(self):
        report = InspectionReport(
            file_name="test.jpg",
            validation_passed=False,
            validation_error="Image too blurry",
        )
        risk = assess_risk([report])
        # Failed validation (contour_count=0 default) returns empty RiskAssessment
        assert isinstance(risk, RiskAssessment)

    def test_risk_has_required_fields(self):
        report = InspectionReport(
            file_name="test.jpg",
            validation_passed=True,
            contour_count=2,
            severity="High",
            confidence=80,
            damage_type="Crack",
            damage_percentage=8.0,
        )
        risk = assess_risk([report])
        assert hasattr(risk, "health_score")
        assert hasattr(risk, "risk_level")
        assert hasattr(risk, "risk_color")
        assert hasattr(risk, "estimated_cost_min")
        assert hasattr(risk, "estimated_cost_max")
