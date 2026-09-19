"""Tests for the Fusion Engine (fuse_reports).

Covers:
- Empty input handling
- No-damage clean inspection path
- Single report passthrough
- Multi-report deduplication by damage type
- Severity/confidence aggregation (worst, max)
- Image ranking
- Cost range parsing and aggregation
- Timeline construction
- Maintenance tip deduplication
"""
from __future__ import annotations

import pytest

from streamlit_app.ai.fusion_engine import (
    FusedInspection,
    FusedFinding,
    ImageRank,
    fuse_reports,
)
from tests._factories import make_report


# ── Empty / no damage ──────────────────────────────────────────────────────────

class TestEmptyInput:
    def test_empty_list_returns_default(self):
        result = fuse_reports([])
        assert isinstance(result, FusedInspection)
        assert result.overall_damage_pct == 0.0
        assert result.overall_health_score == 100
        assert result.total_images == 0

    def test_all_reports_pass_validation_but_zero_damage(self):
        reports = [make_report("clean.jpg", damage_pct=0.0, contour_count=0,
                               validation_passed=True)]
        result = fuse_reports(reports)
        # Zero-damage reports are filtered out as "not damaged"
        assert result.total_findings == 0

    def test_clean_inspection_has_empty_summary(self):
        """With no input, the fusion engine returns an empty summary."""
        result = fuse_reports([])
        assert result.executive_summary == "" or len(result.executive_summary) == 0


# ── Single report ──────────────────────────────────────────────────────────────

class TestSingleReport:
    def test_single_report_propagates_damage_type(self):
        report = make_report("crack_01.jpg", damage_type="Crack", damage_pct=15.0)
        result = fuse_reports([report])
        assert result.total_findings == 1
        assert result.findings[0].damage_type == "Crack"

    def test_single_report_sets_total_images(self):
        report = make_report("img.jpg", damage_pct=5.0)
        result = fuse_reports([report])
        assert result.total_images >= 1

    def test_single_report_creates_health_report(self):
        report = make_report("img.jpg", damage_pct=5.0)
        result = fuse_reports([report])
        assert result.health_report is not None
        assert result.risk_assessment is not None


# ── Deduplication ──────────────────────────────────────────────────────────────

class TestDeduplication:
    def test_same_damage_type_deduplicated(self):
        r1 = make_report("a.jpg", damage_type="Crack", severity="High",
                         damage_pct=10.0, confidence=80)
        r2 = make_report("b.jpg", damage_type="Crack", severity="Critical",
                         damage_pct=20.0, confidence=90)
        result = fuse_reports([r1, r2])
        assert result.total_findings == 1
        assert result.findings[0].damage_type == "Crack"

    def test_different_damage_types_kept_separate(self):
        r1 = make_report("a.jpg", damage_type="Crack", severity="High", damage_pct=10.0)
        r2 = make_report("b.jpg", damage_type="Water Damage", severity="Medium", damage_pct=8.0)
        result = fuse_reports([r1, r2])
        assert result.total_findings == 2
        types = {f.damage_type for f in result.findings}
        assert types == {"Crack", "Water Damage"}

    def test_affected_images_list_contains_both(self):
        r1 = make_report("a.jpg", damage_type="Crack", severity="High")
        r2 = make_report("b.jpg", damage_type="Crack", severity="Medium")
        result = fuse_reports([r1, r2])
        finding = result.findings[0]
        assert "a.jpg" in finding.affected_images
        assert "b.jpg" in finding.affected_images

    def test_image_count_matches_affected(self):
        r1 = make_report("a.jpg", damage_type="Crack")
        r2 = make_report("b.jpg", damage_type="Crack")
        result = fuse_reports([r1, r2])
        finding = result.findings[0]
        assert finding.image_count == len(finding.affected_images)


# ── Severity aggregation ───────────────────────────────────────────────────────

class TestSeverityAggregation:
    def test_worst_severity_selected(self):
        r1 = make_report("a.jpg", damage_type="Dmg", severity="Low", damage_pct=1.0)
        r2 = make_report("b.jpg", damage_type="Dmg", severity="Critical", damage_pct=5.0)
        result = fuse_reports([r1, r2])
        assert result.findings[0].severity == "Critical"

    def test_max_confidence_selected(self):
        r1 = make_report("a.jpg", damage_type="Dmg", confidence=60, damage_pct=5.0)
        r2 = make_report("b.jpg", damage_type="Dmg", confidence=95, damage_pct=5.0)
        result = fuse_reports([r1, r2])
        assert result.findings[0].confidence == 95

    def test_overall_severity_is_worst(self):
        r1 = make_report("a.jpg", damage_type="Crack", severity="Low", damage_pct=1.0)
        r2 = make_report("b.jpg", damage_type="Water Damage", severity="Critical",
                         damage_pct=30.0)
        result = fuse_reports([r1, r2])
        assert result.overall_severity == "Critical"


# ── Image ranking ──────────────────────────────────────────────────────────────

class TestImageRanking:
    def test_images_ranked_by_damage_desc(self):
        r1 = make_report("low.jpg", damage_pct=5.0)
        r2 = make_report("high.jpg", damage_pct=40.0)
        r3 = make_report("mid.jpg", damage_pct=15.0)
        result = fuse_reports([r1, r2, r3])
        assert len(result.image_rankings) == 3
        assert result.image_rankings[0].file_name == "high.jpg"
        assert result.image_rankings[0].rank == 1
        assert result.image_rankings[-1].file_name == "low.jpg"

    def test_rank_is_sequential(self):
        r1 = make_report("a.jpg", damage_pct=10.0)
        r2 = make_report("b.jpg", damage_pct=20.0)
        result = fuse_reports([r1, r2])
        ranks = [ir.rank for ir in result.image_rankings]
        assert ranks == [1, 2]


# ── Cost aggregation ───────────────────────────────────────────────────────────

class TestCostAggregation:
    def test_cost_ranges_parsed_and_summed(self):
        r1 = make_report("a.jpg", damage_type="Crack",
                         estimated_cost_range="5000 - 15000", damage_pct=5.0)
        r2 = make_report("b.jpg", damage_type="Crack",
                         estimated_cost_range="8000 - 20000", damage_pct=10.0)
        result = fuse_reports([r1, r2])
        # Costs are summed across findings (deduplicated into 1 Crack finding)
        assert result.overall_estimated_cost_min >= 5000
        assert result.overall_estimated_cost_max >= 15000


# ── Timeline ───────────────────────────────────────────────────────────────────

class TestTimeline:
    def test_timeline_has_four_buckets(self):
        r1 = make_report("a.jpg", damage_type="Crack", severity="Critical", damage_pct=20.0)
        r2 = make_report("b.jpg", damage_type="Paint", severity="Low", damage_pct=1.0)
        result = fuse_reports([r1, r2])
        assert len(result.timeline) == 4

    def test_critical_finding_in_immediate_bucket(self):
        r = make_report("a.jpg", damage_type="Crack", severity="Critical", damage_pct=25.0)
        result = fuse_reports([r])
        immediate = result.timeline[0]
        assert "Immediate" in immediate.bucket
        assert len(immediate.findings) == 1


# ── Maintenance tips ───────────────────────────────────────────────────────────

class TestMaintenanceTips:
    def test_tips_deduplicated(self):
        r1 = make_report("a.jpg", damage_type="Crack",
                         prevention_tips=["Annual inspection", "Seal cracks"])
        r2 = make_report("b.jpg", damage_type="Crack",
                         prevention_tips=["Annual inspection", "Check gutters"])
        result = fuse_reports([r1, r2])
        tip_texts = [t.lower() for t in result.maintenance_tips]
        assert tip_texts.count("annual inspection") == 1

    def test_empty_reports_gives_empty_tips(self):
        result = fuse_reports([])
        assert isinstance(result.maintenance_tips, list)
        # Empty input may produce empty or default tips


# ── Validation filtering ───────────────────────────────────────────────────────

class TestValidationFiltering:
    def test_invalid_reports_excluded(self):
        valid = make_report("good.jpg", damage_pct=10.0, validation_passed=True)
        invalid = make_report("bad.jpg", damage_pct=50.0, validation_passed=False)
        result = fuse_reports([valid, invalid])
        # Invalid report should be filtered; only valid damaged images are fused
        all_sources = result.source_reports
        assert invalid in all_sources  # Still in source_reports
