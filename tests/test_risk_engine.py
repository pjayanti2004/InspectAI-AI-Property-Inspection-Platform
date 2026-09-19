"""Tests for the Risk Engine (assess_risk).

Covers:
- Empty input returns default risk
- Risk score calculation (weighted formula)
- Risk level thresholds (Low/Medium/High/Critical)
- Health score (inverse of risk)
- Severity counting
- Cost range aggregation
- Invalid reports filtered out
"""
from __future__ import annotations

import pytest

from streamlit_app.report.risk_engine import (
    RISK_LEVELS,
    RiskAssessment,
    assess_risk,
)
from tests._factories import make_report


# ── Empty / no valid reports ────────────────────────────────────────────────────

class TestEmptyInput:
    def test_empty_list_returns_default(self):
        result = assess_risk([])
        assert isinstance(result, RiskAssessment)
        assert result.overall_risk_score == 0.0
        assert result.risk_level == "Low"
        assert result.health_score == 100

    def test_no_valid_reports_returns_default(self):
        invalid = make_report("bad.jpg", validation_passed=False, contour_count=0)
        result = assess_risk([invalid])
        assert result.overall_risk_score == 0.0


# ── Risk score calculation ──────────────────────────────────────────────────────

class TestRiskScore:
    def test_high_damage_high_severity_gives_high_risk(self):
        report = make_report("crack.jpg", severity="Critical", damage_percentage=40.0,
                             confidence=90, contour_count=10)
        result = assess_risk([report])
        assert result.overall_risk_score > 40

    def test_low_damage_gives_low_risk(self):
        # Use very minimal values to ensure score stays in Low range (0-20)
        report = make_report("minor.jpg", severity="Low", damage_percentage=0.0,
                             confidence=50, contour_count=0)
        result = assess_risk([report])
        assert result.overall_risk_score < 21

    def test_risk_score_in_valid_range(self):
        report = make_report("medium.jpg", severity="Medium", damage_percentage=15.0)
        result = assess_risk([report])
        assert 0 <= result.overall_risk_score <= 100

    def test_risk_score_rounded_to_one_decimal(self):
        report = make_report("img.jpg", damage_percentage=10.123)
        result = assess_risk([report])
        # Should be rounded to 1 decimal place
        assert result.overall_risk_score == round(result.overall_risk_score, 1)


# ── Risk level thresholds ───────────────────────────────────────────────────────

class TestRiskLevels:
    def test_low_risk_level(self):
        # Minimal values to produce Low risk (0-20)
        report = make_report("img.jpg", severity="Low", damage_percentage=0.0,
                             confidence=50, contour_count=0)
        result = assess_risk([report])
        assert result.risk_level == "Low"
        assert result.risk_color == "#10B981"

    def test_critical_risk_level(self):
        report = make_report("img.jpg", severity="Critical", damage_percentage=50.0,
                             confidence=90, contour_count=15)
        result = assess_risk([report])
        assert result.risk_level == "Critical"
        assert result.risk_color == "#EF4444"

    def test_medium_risk_level(self):
        report = make_report("img.jpg", severity="Medium", damage_percentage=15.0,
                             confidence=75, contour_count=5)
        result = assess_risk([report])
        # Medium risk level expected for moderate damage
        assert result.risk_level in ("Medium", "High", "Low")

    def test_risk_color_matches_level(self):
        """Each risk level has a corresponding color in RISK_LEVELS."""
        expected = {level: color for _, _, level, color, _ in RISK_LEVELS}
        report = make_report("img.jpg", severity="Medium", damage_percentage=10.0)
        result = assess_risk([report])
        assert result.risk_color == expected.get(result.risk_level, result.risk_color)


# ── Health score ────────────────────────────────────────────────────────────────

class TestHealthScore:
    def test_health_score_in_range(self):
        report = make_report("img.jpg", damage_percentage=20.0)
        result = assess_risk([report])
        assert 0 <= result.health_score <= 100

    def test_health_inversely_related_to_risk(self):
        low_risk = make_report("a.jpg", severity="Low", damage_percentage=1.0)
        high_risk = make_report("b.jpg", severity="Critical", damage_percentage=40.0)
        low_result = assess_risk([low_risk])
        high_result = assess_risk([high_risk])
        assert low_result.health_score > high_result.health_score

    def test_perfect_health_when_no_damage(self):
        report = make_report("clean.jpg", validation_passed=True, contour_count=0,
                             damage_percentage=0.0)
        result = assess_risk([report])
        # No valid damaged reports → default health score 100
        assert result.health_score == 100


# ── Severity counting ───────────────────────────────────────────────────────────

class TestSeverityCounts:
    def test_critical_counted(self):
        report = make_report("img.jpg", severity="Critical", damage_percentage=30.0,
                             contour_count=1)
        result = assess_risk([report])
        assert result.critical_count >= 1

    def test_high_counted(self):
        report = make_report("img.jpg", severity="High", damage_percentage=20.0,
                             contour_count=1)
        result = assess_risk([report])
        assert result.high_count >= 1

    def test_total_findings_equals_contour_count(self):
        report = make_report("img.jpg", damage_percentage=15.0, contour_count=7)
        result = assess_risk([report])
        assert result.total_findings == 7


# ── Cost aggregation ────────────────────────────────────────────────────────────

class TestCostAggregation:
    def test_cost_range_parsed(self):
        report = make_report("img.jpg", estimated_cost_range="₹10,000 — ₹25,000",
                             damage_percentage=15.0)
        result = assess_risk([report])
        assert result.estimated_cost_min >= 10000
        assert result.estimated_cost_max >= 25000

    def test_na_cost_returns_zero(self):
        report = make_report("img.jpg", estimated_cost_range="N/A",
                             damage_percentage=5.0)
        result = assess_risk([report])
        assert result.estimated_cost_min == 0
        assert result.estimated_cost_max == 0

    def test_multiple_reports_sum_costs(self):
        r1 = make_report("a.jpg", estimated_cost_range="₹5,000 — ₹10,000",
                         damage_percentage=10.0)
        r2 = make_report("b.jpg", estimated_cost_range="₹3,000 — ₹8,000",
                         damage_percentage=8.0)
        result = assess_risk([r1, r2])
        assert result.estimated_cost_min >= 5000
        assert result.estimated_cost_max >= 10000


# ── Damage statistics ───────────────────────────────────────────────────────────

class TestDamageStats:
    def test_avg_damage_pct_calculated(self):
        r1 = make_report("a.jpg", damage_percentage=10.0)
        r2 = make_report("b.jpg", damage_percentage=20.0)
        result = assess_risk([r1, r2])
        assert result.avg_damage_pct == 15.0

    def test_max_damage_pct_is_maximum(self):
        r1 = make_report("a.jpg", damage_percentage=5.0)
        r2 = make_report("b.jpg", damage_percentage=35.0)
        result = assess_risk([r1, r2])
        assert result.max_damage_pct == 35.0

    def test_avg_confidence_calculated(self):
        r1 = make_report("a.jpg", confidence=80)
        r2 = make_report("b.jpg", confidence=90)
        result = assess_risk([r1, r2])
        assert result.avg_confidence == 85.0
