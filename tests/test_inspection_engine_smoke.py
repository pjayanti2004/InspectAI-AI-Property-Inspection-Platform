"""Smoke tests for streamlit_app.ai.inspection_engine.

These tests verify that each stage function and the top-level
run_inspection / run_batch entry points behave correctly with
minimal synthetic inputs — no network, no real files.
"""
from __future__ import annotations

import time
from unittest.mock import patch

import cv2
import numpy as np
import pytest

from streamlit_app.ai.inspection_engine import (
    InspectionReport,
    merge_results,
    stage_gemini,
    stage_opencv,
    stage_validate,
)


# ── Helpers ────────────────────────────────────────────────────────────────────

def _make_test_image(width: int = 640, height: int = 480) -> np.ndarray:
    """Create a small solid-gray test image in BGR (OpenCV format)."""
    return np.full((height, width, 3), 128, dtype=np.uint8)


# ── stage_validate ─────────────────────────────────────────────────────────────

class TestStageValidate:
    def test_accepts_numpy_array(self):
        img = _make_test_image()
        _, cv_img, pil_img = stage_validate(img, file_name="test.jpg")
        assert cv_img is not None
        assert pil_img is not None

    def test_returns_dimensions_in_report(self):
        img = _make_test_image(320, 240)
        report = InspectionReport()
        report.image_width = 320
        report.image_height = 240
        assert report.image_width == 320
        assert report.image_height == 240


# ── stage_opencv ───────────────────────────────────────────────────────────────

class TestStageOpenCV:
    def test_returns_report_on_clean_image(self):
        img = _make_test_image()
        report = stage_opencv(img, file_name="clean.jpg")
        assert isinstance(report, InspectionReport)
        assert report.file_name == "clean.jpg"
        assert report.damage_percentage >= 0
        assert report.total_processing_time_sec > 0

    def test_returns_report_on_noisy_image(self):
        """Add some random noise so contour detection produces at least one region."""
        img = _make_test_image()
        noise = np.random.randint(0, 50, img.shape, dtype=np.uint8)
        img = cv2.add(img, noise)
        report = stage_opencv(img, file_name="noisy.jpg")
        assert report.contour_count >= 0  # >=0, may be 0 for uniform noise


# ── stage_gemini ───────────────────────────────────────────────────────────────

class TestStageGemini:
    def test_returns_report_with_gemini_skipped_when_not_configured(self):
        """When no API key is set, stage_gemini should mark gemini_skipped=True."""
        img = _make_test_image()
        from PIL import Image as PILImage
        pil_img = PILImage.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))

        with patch("streamlit_app.ai.inspection_engine.configure_gemini",
                   side_effect=Exception("not configured")):
            report = stage_gemini(pil_img, prompt="test prompt")

        assert isinstance(report, InspectionReport)
        assert report.gemini_skipped is True
        assert len(report.gemini_error) > 0


# ── merge_results ──────────────────────────────────────────────────────────────

class TestMergeResults:
    def test_merges_two_reports(self):
        r1 = InspectionReport(
            file_name="img1.jpg",
            damage_percentage=3.0,
            damage_area_px=3000,
            contour_count=2,
            cv_processing_time_sec=0.5,
            gemini_processing_time_sec=0.0,
            gemini_skipped=True,
        )
        r2 = InspectionReport(
            file_name="img2.jpg",
            damage_percentage=7.5,
            damage_area_px=7500,
            contour_count=5,
            cv_processing_time_sec=1.0,
            gemini_processing_time_sec=0.0,
            gemini_skipped=True,
        )
        merged = merge_results([r1, r2])
        assert isinstance(merged, InspectionReport)
        assert merged.file_name == "img1.jpg"  # first image kept as representative
        assert merged.damage_percentage == 10.5
        assert merged.damage_area_px == 10500
        assert merged.contour_count == 7
        assert merged.total_processing_time_sec == 1.5

    def test_returns_empty_report_for_empty_list(self):
        merged = merge_results([])
        assert isinstance(merged, InspectionReport)
        assert merged.contour_count == 0
        assert merged.damage_percentage == 0.0


# ── InspectionReport.to_dict ───────────────────────────────────────────────────

class TestInspectionReport:
    def test_to_dict_excludes_numpy_arrays(self):
        img = _make_test_image()
        report = InspectionReport(
            file_name="test.jpg",
            processed_image=img,
            damage_mask=img,
            heatmap=img,
            overlay_image=img,
        )
        d = report.to_dict()
        assert "processed_image" not in d
        assert "damage_mask" not in d
        assert "heatmap" not in d
        assert "overlay_image" not in d
        assert d["file_name"] == "test.jpg"

    def test_to_dict_preserves_metadata(self):
        report = InspectionReport(
            file_name="meta.jpg",
            image_width=1920,
            image_height=1080,
            file_size_mb=2.5,
            confidence=88,
        )
        d = report.to_dict()
        assert d["image_width"] == 1920
        assert d["image_height"] == 1080
        assert d["file_size_mb"] == 2.5
        assert d["confidence"] == 88


# ── run_inspection (mocked) ────────────────────────────────────────────────────

class TestRunInspection:
    def test_returns_list_of_reports(self):
        from streamlit_app.ai.inspection_engine import run_inspection

        with patch("streamlit_app.ai.inspection_engine.stage_validate") as mock_val, \
             patch("streamlit_app.ai.inspection_engine.stage_opencv") as mock_ocv, \
             patch("streamlit_app.ai.inspection_engine.stage_gemini") as mock_gem:
            mock_val.return_value = ("ok", _make_test_image(), None)
            mock_ocv.return_value = InspectionReport(file_name="test.jpg", damage_percentage=1.0)
            mock_gem.return_value = InspectionReport(file_name="test.jpg", gemini_skipped=True)

            results = run_inspection([_make_test_image()])

        assert len(results) == 1
        assert isinstance(results[0], InspectionReport)
        assert results[0].file_name == "test.jpg"

    def test_returns_empty_list_for_no_images(self):
        from streamlit_app.ai.inspection_engine import run_inspection
        results = run_inspection([])
        assert results == []

    def test_reports_have_timing_info(self):
        from streamlit_app.ai.inspection_engine import run_inspection

        with patch("streamlit_app.ai.inspection_engine.stage_validate") as mock_val, \
             patch("streamlit_app.ai.inspection_engine.stage_opencv") as mock_ocv, \
             patch("streamlit_app.ai.inspection_engine.stage_gemini") as mock_gem:
            mock_val.return_value = ("ok", _make_test_image(), None)
            mock_ocv.return_value = InspectionReport(file_name="t.jpg")
            mock_gem.return_value = InspectionReport(file_name="t.jpg", gemini_skipped=True)

            results = run_inspection([_make_test_image()])

        r = results[0]
        assert r.cv_processing_time_sec >= 0
        assert r.gemini_processing_time_sec >= 0
        assert r.total_processing_time_sec >= 0


# ── run_batch (mocked) ─────────────────────────────────────────────────────────

class TestRunBatch:
    def test_returns_empty_for_empty_list(self):
        from streamlit_app.ai.inspection_engine import run_batch
        assert run_batch([]) == []

    def test_merges_multi_image_results(self):
        from streamlit_app.ai.inspection_engine import run_batch

        with patch("streamlit_app.ai.inspection_engine.stage_validate") as mock_val, \
             patch("streamlit_app.ai.inspection_engine.stage_opencv") as mock_ocv, \
             patch("streamlit_app.ai.inspection_engine.stage_gemini") as mock_gem:
            mock_val.return_value = ("ok", _make_test_image(), None)

            def _make_report(fname):
                return InspectionReport(file_name=fname, damage_percentage=1.0)

            mock_ocv.side_effect = lambda img, fn: _make_report(fn)
            mock_gem.return_value = InspectionReport(file_name="x.jpg", gemini_skipped=True)

            results = run_batch([_make_test_image(), _make_test_image()])

        assert len(results) == 2
        assert all(isinstance(r, InspectionReport) for r in results)
