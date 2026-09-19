"""Report page helpers — score grading, object conversion, color helpers, data reconstruction."""
from __future__ import annotations

from typing import Any

import streamlit as st

from streamlit_app.report.summary_engine import FindingRecord
from streamlit_app.utils.constants import SEVERITY_COLORS
from streamlit_app.utils.session_manager import navigate_to


# ── Score grading ──────────────────────────────────────────────────────────────

def score_to_grade(score: float) -> str:
    """Convert a numeric health score to a letter grade."""
    if score >= 90: return "A+"
    if score >= 80: return "A"
    if score >= 70: return "B+"
    if score >= 60: return "B"
    if score >= 50: return "C"
    return "D"


def avg_cost(min_c: int, max_c: int) -> int:
    """Compute average repair cost from min/max range."""
    return (min_c + max_c) // 2 if (min_c or max_c) else 0


# ── Object conversion ──────────────────────────────────────────────────────────

def obj_to_dict(obj) -> dict:
    """Convert a dataclass object to a plain dict, excluding binary fields."""
    if hasattr(obj, '__dict__'):
        return {k: v for k, v in obj.__dict__.items()
                if k not in ('image_thumbnail', 'overlay_image', 'processed_image',
                             'damage_mask', 'heatmap', 'measurement_report')}
    return obj if isinstance(obj, dict) else {}


def dicts_to_finding_records(findings: list) -> list:
    """Convert dict findings to FindingRecord objects for the report_builder."""
    try:
        result = []
        for f in findings:
            if isinstance(f, FindingRecord):
                result.append(f)
            elif isinstance(f, dict):
                result.append(FindingRecord(
                    file_name=f.get("file_name", ""),
                    damage_type=f.get("damage_type", "N/A"),
                    severity=f.get("severity", "Medium"),
                    confidence=f.get("confidence", 0),
                    damage_pct=f.get("damage_pct", 0.0),
                    contour_count=f.get("contour_count", 1),
                    possible_causes=f.get("possible_causes", []),
                    repair_steps=f.get("repair_steps", []),
                    recommended_professional=f.get("recommended_professional", "N/A"),
                    estimated_cost_range=f.get("estimated_cost_range", "N/A"),
                    urgency=f.get("urgency", "N/A"),
                    prevention_tips=f.get("prevention_tips", []),
                ))
        return result
    except Exception:
        return []


# ── Color helpers ──────────────────────────────────────────────────────────────

def sev_color(severity: str) -> str:
    """Get hex color for a severity level."""
    return SEVERITY_COLORS.get(severity, "#64748B")


def sev_bg(severity: str) -> str:
    """Get background color for a severity level."""
    mapping = {
        "Critical": "rgba(239, 68, 68, 0.15)",
        "High":     "rgba(249, 115, 22, 0.15)",
        "Medium":   "rgba(245, 158, 11, 0.15)",
        "Low":      "rgba(16, 185, 129, 0.15)",
    }
    return mapping.get(severity, "rgba(100, 116, 139, 0.15)")


def risk_color(risk: str) -> str:
    """Get hex color for a risk level."""
    mapping = {
        "Critical": "#EF4444",
        "High":     "#F97316",
        "Medium":   "#F59E0B",
        "Low":      "#10B981",
    }
    return mapping.get(risk, "#64748B")


def grade_color(grade: str) -> str:
    """Get hex color for a letter grade."""
    mapping = {
        "A+": "#10B981", "A": "#34D399",
        "B+": "#6EE7B7", "B": "#FBBF24",
        "C":  "#F97316", "D": "#EF4444",
    }
    return mapping.get(grade, "#64748B")


# ── Data reconstruction ───────────────────────────────────────────────────────

def rebuild_health_report(health_dict: dict) -> Any | None:
    """Reconstruct a PropertyHealthReport from serialized dict."""
    if not health_dict:
        return None
    try:
        from streamlit_app.ai.health_engine import (
            Grade, HealthCategory, HealthMetric, PropertyHealthReport
        )
        categories = []
        for c in health_dict.get("categories", []):
            grade_val = c.get("grade", "D")
            grade = Grade(grade_val) if grade_val in [g.value for g in Grade] else Grade.D
            metrics = [HealthMetric(**m) for m in c.get("metrics", [])]
            categories.append(HealthCategory(
                category=c.get("category", ""),
                score=c.get("score", 0.0),
                grade=grade,
                findings_count=c.get("findings_count", 0),
                issues=c.get("issues", []),
                metrics=metrics,
            ))
        grade_val = health_dict.get("overall_grade", "D")
        grade = Grade(grade_val) if grade_val in [g.value for g in Grade] else Grade.D
        return PropertyHealthReport(
            overall_score=health_dict.get("overall_score", 0.0),
            overall_grade=grade,
            categories=categories,
            remaining_life_years=health_dict.get("remaining_life_years", 0.0),
            immediate_risk=health_dict.get("immediate_risk", "Low"),
            immediate_risk_desc=health_dict.get("immediate_risk_desc", ""),
            future_predictions=health_dict.get("future_predictions", {}),
            inspection_confidence=health_dict.get("inspection_confidence", 0.0),
            repair_priority_index=health_dict.get("repair_priority_index", 0.0),
            health_summary=health_dict.get("health_summary", ""),
            strengths=health_dict.get("strengths", []),
            weaknesses=health_dict.get("weaknesses", []),
            priority_actions=health_dict.get("priority_actions", []),
            preventive_maintenance=health_dict.get("preventive_maintenance", []),
        )
    except Exception:
        return None


def rebuild_comparison_report(comparison_dict: dict) -> Any | None:
    """Reconstruct a ComparisonReport from serialized dict."""
    if not comparison_dict:
        return None
    try:
        from streamlit_app.ai.comparison_engine import rebuild_comparison_report
        return rebuild_comparison_report(comparison_dict)
    except Exception:
        return None


# ── Not-found / no-data states ─────────────────────────────────────────────────

def render_not_found(report_id: str) -> None:
    """Render the report-not-found state."""
    st.markdown(
        f"""
        <div style="text-align: center; padding: 4rem 2rem;">
            <div style="font-size: 4rem; margin-bottom: 1rem;">🔍</div>
            <h2 style="color: #F1F5F9; margin: 0 0 0.5rem;">Report Not Found</h2>
            <p style="color: #64748B; font-size: 1rem;">
                No report found for inspection ID: <b>{report_id}</b>
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("← Back to Reports", type="primary"):
        st.session_state.pop("view_report_id", None)
        navigate_to("reports")


def render_no_data() -> None:
    """Render the no-report-data state."""
    st.markdown(
        """
        <div style="text-align: center; padding: 4rem 2rem;">
            <div style="font-size: 4rem; margin-bottom: 1rem;">📭</div>
            <h2 style="color: #F1F5F9; margin: 0 0 0.5rem;">No Report Data</h2>
            <p style="color: #64748B; font-size: 1rem;">
                Complete an inspection to generate a report.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("Start New Inspection", type="primary", use_container_width=True):
            navigate_to("new_inspection")
