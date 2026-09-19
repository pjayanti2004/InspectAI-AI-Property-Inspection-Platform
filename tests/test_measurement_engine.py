"""Tests for the Measurement Engine.

Covers:
- measure_damage_regions: region counting, area calculations, crack estimates
- measure_damage_regions: min_area filtering
- measure_damage_regions: largest region tracking
- measure_damage_regions: wall quadrant detection
- measure_damage_regions: aggregate stats (total repair area, avg crack width)
- annotate_damage: output shapes and types
- annotate_damage: legend drawing
"""
from __future__ import annotations

import cv2
import numpy as np
import pytest

from streamlit_app.ai.measurement_engine import (
    DamageRegion,
    MeasurementReport,
    annotate_damage,
    measure_damage_regions,
)


# ── Synthetic data helpers ─────────────────────────────────────────────────────

def _make_test_image(width=640, height=480):
    """Create a plain gray BGR image."""
    return np.full((height, width, 3), 180, dtype=np.uint8)


def _make_rect_contour(x, y, w, h):
    """Return a cv2-style rectangular contour."""
    return np.array([[[x, y]], [[x + w, y]], [[x + w, y + h]], [[x, y + h]]],
                    dtype=np.int32)


def _make_mask(width=640, height=480, regions=None):
    """Create binary mask with filled rectangles."""
    mask = np.zeros((height, width), dtype=np.uint8)
    if regions:
        for x, y, w, h in regions:
            mask[y:y + h, x:x + w] = 255
    return mask


# ── measure_damage_regions tests ───────────────────────────────────────────────

class TestMeasureDamageRegions:
    def test_empty_contours_returns_empty_report(self):
        img = _make_test_image()
        mask = np.zeros((480, 640), dtype=np.uint8)
        result = measure_damage_regions(img, mask, [], [])
        assert result.region_count == 0
        assert result.total_damage_pct == 0.0
        assert result.regions == []

    def test_single_region_counted(self):
        img = _make_test_image()
        mask = _make_mask(regions=[(100, 100, 100, 80)])
        contours = [_make_rect_contour(100, 100, 100, 80)]
        bboxes = [(100, 100, 100, 80)]
        result = measure_damage_regions(img, mask, contours, bboxes)
        assert result.region_count == 1
        assert len(result.regions) == 1

    def test_region_has_correct_id(self):
        img = _make_test_image()
        mask = _make_mask(regions=[(50, 50, 60, 40)])
        contours = [_make_rect_contour(50, 50, 60, 40)]
        bboxes = [(50, 50, 60, 40)]
        result = measure_damage_regions(img, mask, contours, bboxes)
        assert result.regions[0].region_id == 1

    def test_damage_pct_calculated(self):
        img = _make_test_image()
        mask = _make_mask(regions=[(0, 0, 320, 240)])  # 25% of image
        contours = [_make_rect_contour(0, 0, 320, 240)]
        bboxes = [(0, 0, 320, 240)]
        result = measure_damage_regions(img, mask, contours, bboxes)
        # 320*240 = 76800; total = 640*480 = 307200; pct = 25%
        assert abs(result.total_damage_pct - 25.0) < 1.0

    def test_total_repair_area_exceeds_damage_area(self):
        img = _make_test_image()
        mask = _make_mask(regions=[(100, 100, 80, 60)])
        contours = [_make_rect_contour(100, 100, 80, 60)]
        bboxes = [(100, 100, 80, 60)]
        result = measure_damage_regions(img, mask, contours, bboxes)
        # Repair area includes ~15% buffer
        assert result.total_repair_area_px >= result.regions[0].area_px

    def test_largest_region_tracked(self):
        img = _make_test_image()
        mask = _make_mask(regions=[(10, 10, 50, 50), (200, 200, 150, 150)])
        contours = [
            _make_rect_contour(10, 10, 50, 50),
            _make_rect_contour(200, 200, 150, 150),
        ]
        bboxes = [(10, 10, 50, 50), (200, 200, 150, 150)]
        result = measure_damage_regions(img, mask, contours, bboxes)
        assert result.largest_region is not None
        assert result.largest_region.area_px == 150 * 150

    def test_min_area_filters_small_regions(self):
        img = _make_test_image()
        mask = _make_mask(regions=[(10, 10, 10, 10), (200, 200, 100, 100)])
        contours = [
            _make_rect_contour(10, 10, 10, 10),
            _make_rect_contour(200, 200, 100, 100),
        ]
        bboxes = [(10, 10, 10, 10), (200, 200, 100, 100)]
        result = measure_damage_regions(img, mask, contours, bboxes, min_area=500)
        assert result.region_count == 1
        assert result.regions[0].area_px == 100 * 100

    def test_center_quadrant_for_centered_region(self):
        img = _make_test_image()
        mask = _make_mask(regions=[(280, 200, 80, 80)])
        contours = [_make_rect_contour(280, 200, 80, 80)]
        bboxes = [(280, 200, 80, 80)]
        result = measure_damage_regions(img, mask, contours, bboxes)
        assert result.most_affected_wall == "Center"

    def test_top_left_quadrant(self):
        img = _make_test_image()
        mask = _make_mask(regions=[(50, 50, 100, 100)])
        contours = [_make_rect_contour(50, 50, 100, 100)]
        bboxes = [(50, 50, 100, 100)]
        result = measure_damage_regions(img, mask, contours, bboxes)
        assert result.most_affected_wall == "Top-Left"

    def test_bottom_right_quadrant(self):
        img = _make_test_image()
        mask = _make_mask(regions=[(450, 350, 100, 100)])
        contours = [_make_rect_contour(450, 350, 100, 100)]
        bboxes = [(450, 350, 100, 100)]
        result = measure_damage_regions(img, mask, contours, bboxes)
        assert result.most_affected_wall == "Bottom-Right"

    def test_image_dimensions_recorded(self):
        img = _make_test_image(width=800, height=600)
        mask = np.zeros((600, 800), dtype=np.uint8)
        result = measure_damage_regions(img, mask, [], [])
        assert result.image_width == 800
        assert result.image_height == 600

    def test_avg_crack_width_zero_when_no_regions(self):
        img = _make_test_image()
        mask = np.zeros((480, 640), dtype=np.uint8)
        result = measure_damage_regions(img, mask, [], [])
        assert result.avg_crack_width == 0.0

    def test_avg_crack_width_positive_with_regions(self):
        img = _make_test_image()
        mask = _make_mask(regions=[(100, 100, 100, 80)])
        contours = [_make_rect_contour(100, 100, 100, 80)]
        bboxes = [(100, 100, 100, 80)]
        result = measure_damage_regions(img, mask, contours, bboxes)
        assert result.avg_crack_width > 0.0

    def test_region_bounding_box_matches_input(self):
        img = _make_test_image()
        mask = _make_mask(regions=[(50, 80, 120, 60)])
        contours = [_make_rect_contour(50, 80, 120, 60)]
        bboxes = [(50, 80, 120, 60)]
        result = measure_damage_regions(img, mask, contours, bboxes)
        region = result.regions[0]
        assert region.bounding_box == (50, 80, 120, 60)

    def test_center_coordinates_within_bbox(self):
        img = _make_test_image()
        mask = _make_mask(regions=[(100, 100, 80, 60)])
        contours = [_make_rect_contour(100, 100, 80, 60)]
        bboxes = [(100, 100, 80, 60)]
        result = measure_damage_regions(img, mask, contours, bboxes)
        cx, cy = result.regions[0].center_x, result.regions[0].center_y
        assert 100 <= cx <= 180
        assert 100 <= cy <= 160

    def test_contours_saved_in_report(self):
        img = _make_test_image()
        mask = _make_mask(regions=[(50, 50, 60, 40)])
        contours = [_make_rect_contour(50, 50, 60, 40)]
        bboxes = [(50, 50, 60, 40)]
        result = measure_damage_regions(img, mask, contours, bboxes)
        assert len(result.contours) == 1


# ── annotate_damage tests ──────────────────────────────────────────────────────

class TestAnnotateDamage:
    def test_returns_three_images(self):
        img = _make_test_image()
        report = MeasurementReport(regions=[])
        annotated, mask_out, overlay = annotate_damage(img, report)
        assert annotated.shape == img.shape
        assert mask_out.shape[:2] == img.shape[:2]
        assert overlay.shape == img.shape

    def test_output_dtypes_uint8(self):
        img = _make_test_image()
        report = MeasurementReport(regions=[])
        annotated, mask_out, overlay = annotate_damage(img, report)
        assert annotated.dtype == np.uint8
        assert mask_out.dtype == np.uint8
        assert overlay.dtype == np.uint8

    def test_contour_mask_is_3_channel(self):
        img = _make_test_image()
        report = MeasurementReport(regions=[])
        _, mask_out, _ = annotate_damage(img, report)
        assert mask_out.ndim == 3
        assert mask_out.shape[2] == 3

    def test_legend_added_when_regions_present(self):
        img = _make_test_image()
        mask = _make_mask(regions=[(100, 100, 80, 60)])
        contours = [_make_rect_contour(100, 100, 80, 60)]
        bboxes = [(100, 100, 80, 60)]
        report = measure_damage_regions(img, mask, contours, bboxes)
        annotated, _, _ = annotate_damage(img, report, contours,
                                          severity_list=["High"])
        # Legend should change the bottom-right corner — image still valid
        assert annotated.shape == img.shape

    def test_show_options_respected(self):
        img = _make_test_image()
        report = MeasurementReport(regions=[])
        annotated, _, _ = annotate_damage(img, report, show_labels=False,
                                          show_bbox=False, show_contour=False)
        assert annotated.shape == img.shape
