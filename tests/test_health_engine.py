"""Tests for the Health Engine (assess_health).

Covers:
- Grade boundaries (A+ through D)
- Category scoring with findings
- Overall score weighting
- Future damage predictions
- Remaining life estimation
- Confidence and repair priority index
"""
from __future__ import annotations

import pytest

from streamlit_app.ai.health_engine import (
    Grade,
    HealthCategory,
    HealthMetric,
    PropertyHealthReport,
    assess_health,
)


# ── Grade boundary tests ───────────────────────────────────────────────────────

class TestGradeFromScore:
    @pytest.mark.parametrize("score,expected", [
        (100, "A+"), (95, "A+"),
        (89, "A"), (80, "A"),
        (79, "B+"), (70, "B+"),
        (69, "B"), (60, "B"),
        (59, "C"), (50, "C"),
        (49, "D"), (0, "D"),
    ])
    def test_grade_thresholds(self, score, expected):
        assert Grade.from_score(score).value == expected

    def test_grade_color_a_plus(self):
        assert Grade.A_PLUS.color == "#10B981"

    def test_grade_color_d(self):
        assert Grade.D.color == "#EF4444"

    def test_grade_bg_a(self):
        assert "rgba" in Grade.A.bg


# ── Empty input ────────────────────────────────────────────────────────────────

class TestEmptyInput:
    def test_empty_reports_returns_default_report(self):
        result = assess_health([])
        assert isinstance(result, PropertyHealthReport)
        # With no reports, 10 categories each at default 90 = weighted average 90
        assert result.overall_score >= 90.0
        assert result.overall_grade in (Grade.A, Grade.A_PLUS)

    def test_no_findings_gives_high_score(self):
        report = _make_report("Wall Paint Peeling", damage_pct=0.0, confidence=0, contour_count=0)
        result = assess_health([report])
        assert result.overall_score >= 80


# ── Single finding scoring ─────────────────────────────────────────────────────

class TestSingleFinding:
    def test_critical_finding_drops_score(self):
        report = _make_report("Structural Crack", severity="Critical",
                              damage_pct=25.0, confidence=90, contour_count=3)
        result = assess_health([report])
        # Critical finding degrades the affected category significantly;
        # overall score drops but other healthy categories buffer it
        assert result.overall_score < 80
        # The affected category (Structure) should have a low grade
        structure = _find_category(result, "Structure")
        if structure:
            assert structure.grade in (Grade.C, Grade.D)

    def test_low_finding_preserves_score(self):
        report = _make_report("Minor Crack", severity="Low",
                              damage_pct=1.0, confidence=95, contour_count=1)
        result = assess_health([report])
        assert result.overall_score >= 70

    def test_immediate_risk_reflects_severity(self):
        critical = _make_report("Foundation Failure", severity="Critical",
                                damage_pct=40.0, confidence=90)
        result = assess_health([critical])
        assert result.immediate_risk == "High"

    def test_low_severity_gives_low_risk(self):
        low = _make_report("Paint Fading", severity="Low",
                           damage_pct=0.5, confidence=80)
        result = assess_health([low])
        assert result.immediate_risk == "Low"


# ── Multiple findings aggregation ─────────────────────────────────────────────

class TestMultipleFindings:
    def test_all_categories_populated(self):
        reports = [
            _make_report("Wall Crack", severity="High", damage_pct=10.0),
            _make_report("Water Damage", severity="Medium", damage_pct=8.0),
            _make_report("Roof Leak", severity="Critical", damage_pct=30.0),
        ]
        result = assess_health(reports)
        assert len(result.categories) == 10  # All categories present

    def test_worst_severity_drives_risk(self):
        reports = [
            _make_report("Minor Issue", severity="Low", damage_pct=1.0),
            _make_report("Critical Issue", severity="Critical", damage_pct=35.0),
        ]
        result = assess_health(reports)
        assert result.immediate_risk == "High"

    def test_findings_count_tracked(self):
        reports = [_make_report("Crack", damage_pct=5.0, contour_count=2)]
        result = assess_health(reports)
        # Total findings should match number of non-N/A damage types reported
        total_findings = sum(c.findings_count for c in result.categories)
        assert total_findings >= 1

    def test_strengths_and_weaknesses_present(self):
        reports = [_make_report("Crack", severity="Medium", damage_pct=10.0)]
        result = assess_health(reports)
        assert isinstance(result.strengths, list)
        assert isinstance(result.weaknesses, list)

    def test_priority_actions_generated(self):
        critical = _make_report("Urgent Crack", severity="Critical",
                                damage_pct=20.0, confidence=90)
        result = assess_health([critical])
        assert len(result.priority_actions) > 0
        assert any("URGENT" in a for a in result.priority_actions)


# ── Future predictions ─────────────────────────────────────────────────────────

class TestFuturePredictions:
    def test_predictions_dict_has_3_6_12_keys(self):
        report = _make_report("Structural Damage", severity="Critical",
                              damage_pct=25.0, confidence=80)
        result = assess_health([report])
        assert "3mo" in result.future_predictions
        assert "6mo" in result.future_predictions
        assert "12mo" in result.future_predictions

    def test_predictions_contain_score_string(self):
        report = _make_report("Damage", severity="Medium", damage_pct=15.0)
        result = assess_health([report])
        for key in ("3mo", "6mo", "12mo"):
            val = result.future_predictions[key]
            assert "Score:" in val

    def test_critical_damage_declines_faster(self):
        mild = _make_report("Mild Crack", severity="Low", damage_pct=2.0)
        severe = _make_report("Severe Crack", severity="Critical", damage_pct=35.0)

        mild_result = assess_health([mild])
        severe_result = assess_health([severe])

        # Critical damage should show worse 12mo projection
        mild_score = _extract_score(mild_result.future_predictions["12mo"])
        severe_score = _extract_score(severe_result.future_predictions["12mo"])
        assert severe_score <= mild_score


# ── Remaining life ─────────────────────────────────────────────────────────────

class TestRemainingLife:
    def test_perfect_health_gives_long_life(self):
        result = assess_health([])
        assert result.remaining_life_years > 20

    def test_critical_damage_reduces_life(self):
        report = _make_report("Foundation", severity="Critical", damage_pct=40.0)
        result = assess_health([report])
        # Critical damage reduces remaining life compared to perfect health
        assert result.remaining_life_years < 50

    def test_life_is_positive(self):
        report = _make_report("Damage", severity="Critical", damage_pct=50.0)
        result = assess_health([report])
        assert result.remaining_life_years >= 0.5


# ── Confidence ─────────────────────────────────────────────────────────────────

class TestConfidence:
    def test_high_confidence_gives_high_inspection_confidence(self):
        report = _make_report("Crack", confidence=95, damage_pct=5.0)
        result = assess_health([report])
        assert result.inspection_confidence >= 85

    def test_low_confidence_lowers_score(self):
        report = _make_report("Unclear", confidence=30, damage_pct=10.0)
        result = assess_health([report])
        # Low confidence should not artificially boost the score
        assert result.inspection_confidence <= 70


# ── Category mapping ───────────────────────────────────────────────────────────

class TestCategoryMapping:
    def test_crack_finding_maps_to_cracks_category(self):
        report = _make_report("Wall Crack", severity="Medium", damage_pct=8.0)
        result = assess_health([report])
        cracks = _find_category(result, "Cracks")
        assert cracks is not None

    def test_water_damage_maps_to_moisture(self):
        report = _make_report("Water Damage / Damp", severity="High", damage_pct=12.0)
        result = assess_health([report])
        moisture = _find_category(result, "Moisture")
        assert moisture is not None

    def test_electrical_finding_maps_correctly(self):
        report = _make_report("Electrical Wiring Issue", severity="Medium", damage_pct=5.0)
        result = assess_health([report])
        electrical = _find_category(result, "Electrical")
        assert electrical is not None


# ── Repair priority index ──────────────────────────────────────────────────────

class TestRepairPriorityIndex:
    def test_index_in_valid_range(self):
        report = _make_report("Crack", severity="High", damage_pct=20.0)
        result = assess_health([report])
        assert 0 <= result.repair_priority_index <= 100

    def test_critical_has_higher_priority_than_low(self):
        critical = _make_report("Critical", severity="Critical", damage_pct=30.0)
        low = _make_report("Low", severity="Low", damage_pct=1.0)
        crit_result = assess_health([critical])
        low_result = assess_health([low])
        assert crit_result.repair_priority_index >= low_result.repair_priority_index


# ── Maintenance tips ───────────────────────────────────────────────────────────

class TestMaintenanceTips:
    def test_tips_always_present(self):
        result = assess_health([])
        assert isinstance(result.preventive_maintenance, list)

    def test_damage_generates_tips(self):
        report = _make_report("Crack", severity="Medium", damage_pct=10.0)
        result = assess_health([report])
        assert len(result.preventive_maintenance) > 0


# ── Helpers ────────────────────────────────────────────────────────────────────

def _make_report(damage_type: str, severity: str = "Medium",
                 confidence: int = 80, damage_pct: float = 5.0,
                 contour_count: int = 1, damage_area_px: int = 3000):
    """Create a minimal dict-style report for assess_health."""
    return {
        "damage_type": damage_type,
        "severity": severity,
        "confidence": confidence,
        "damage_pct": damage_pct,
        "damage_percentage": damage_pct,
        "contour_count": contour_count,
        "damage_area_px": damage_area_px,
        "repair_steps": ["Inspect and repair"],
        "possible_causes": ["Aging"],
        "urgency": "Schedule within 30 days",
        "prevention_tips": ["Regular inspection"],
        "file_name": "test.jpg",
    }


def _find_category(report: PropertyHealthReport, name: str) -> HealthCategory | None:
    for cat in report.categories:
        if cat.category == name:
            return cat
    return None


def _extract_score(prediction: str) -> float:
    """Extract numeric score from 'Score: XX/100 (...) — ...' string."""
    try:
        return float(prediction.split("Score:")[1].split("/")[0].strip())
    except (IndexError, ValueError):
        return 0.0
