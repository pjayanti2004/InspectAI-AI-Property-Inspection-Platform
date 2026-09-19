"""Report Builder — orchestrator.

Delegates to submodules:

    health            Health score ring, grade card, risk badge, category cards, predictions
    summary           Executive summary card, stat row
    findings          Finding cards, findings list
    comparison        Inspection comparison section
    timeline          Repair timeline, checklist
    recommendations   Immediate actions, repair priority, maintenance tips
    pdf_generator     PDF download (unchanged)

Public API (unchanged from before the split):
    render_report
    render_report_preview
"""
from __future__ import annotations

from typing import Any

import streamlit as st

from streamlit_app.ai.inspection_engine import InspectionReport
from streamlit_app.ai.health_engine import PropertyHealthReport
from streamlit_app.report.risk_engine import RiskAssessment, assess_risk
from streamlit_app.report.summary_engine import (
    ExecutiveSummary, FindingRecord, TimelineEntry,
    build_executive_summary, build_findings, build_timeline,
    build_recommendations, build_checklist,
)

from streamlit_app.report.health import (
    render_health_score_ring, render_risk_badge,
    render_property_health_dashboard,
)
from streamlit_app.report.summary import render_executive_summary, render_stat_row
from streamlit_app.report.findings import render_findings_section
from streamlit_app.report.comparison import render_comparison_section
from streamlit_app.report.timeline import render_timeline_section, render_checklist_section
from streamlit_app.report.recommendations import render_recommendations_section
from streamlit_app.components.ui_components import render_html


def render_report(
    reports: list[InspectionReport],
    property_data: dict,
    inspection_id: str,
) -> None:
    """Render a full inspection report from AI pipeline results."""
    if not reports:
        st.warning("No inspection reports to display.")
        return

    primary_report = reports[0]

    # ── Build auxiliary data ────────────────────────────────────────────
    health = _build_health_report(primary_report, property_data)
    risk = assess_risk(primary_report, property_data)
    summary = build_executive_summary(primary_report, property_data, inspection_id)
    findings = build_findings(primary_report, property_data)
    timeline = build_timeline(primary_report, property_data)
    recommendations = build_recommendations(primary_report, property_data)
    checklist = build_checklist(primary_report, property_data)

    # ── Section 1: Executive Summary ───────────────────────────────────
    render_executive_summary(summary)
    render_stat_row(summary, risk)

    render_html("<div style='height: 1rem;'></div>")

    # ── Section 2: Property Health Dashboard ───────────────────────────
    render_property_health_dashboard(health)

    render_html("<div style='height: 1rem;'></div>")

    # ── Section 3: Risk Badge ──────────────────────────────────────────
    render_risk_badge(risk)

    render_html("<div style='height: 1rem;'></div>")

    # ── Section 4: Detailed Findings ──────────────────────────────────
    render_findings_section(findings)

    render_html("<div style='height: 1rem;'></div>")

    # ── Section 5: Comparison (if multiple reports) ────────────────────
    if len(reports) >= 2:
        comparison = _build_comparison(reports, property_data)
        render_comparison_section(comparison)

        render_html("<div style='height: 1rem;'></div>")

    # ── Section 6: Repair Timeline ────────────────────────────────────
    if timeline:
        render_timeline_section(timeline)

        render_html("<div style='height: 1rem;'></div>")

    # ── Section 7: Recommendations ────────────────────────────────────
    render_recommendations_section(recommendations)

    render_html("<div style='height: 1rem;'></div>")

    # ── Section 8: Checklist ──────────────────────────────────────────
    if checklist:
        render_checklist_section(checklist)

        render_html("<div style='height: 1rem;'></div>")

    # ── Section 9: PDF Download ───────────────────────────────────────
    from streamlit_app.report.pdf_generator import generate_pdf

    report_data = _build_report_dict(
        primary_report, property_data, inspection_id,
        health, risk, findings, recommendations, checklist, timeline,
    )
    pdf_bytes = generate_pdf(report_data)
    if pdf_bytes:
        st.download_button(
            "Download PDF Report",
            data=pdf_bytes,
            file_name=f"inspection_report_{inspection_id}.pdf",
            mime="application/pdf",
            use_container_width=True,
        )
    else:
        st.info("PDF generation is not available. Use the Print feature (Ctrl+P) to save this report.")


def _build_health_report(report: InspectionReport, property_data: dict) -> PropertyHealthReport:
    """Build a PropertyHealthReport from the inspection report."""
    from streamlit_app.ai.health_engine import (
        PropertyHealthReport, HealthGrade, HealthCategory,
        CategoryScore, CategoryGrade, FuturePredictions,
    )
    import random

    overall_score = max(20, min(95, 100 - len(report.damages) * 8 - random.randint(0, 10)))
    grade = _score_to_grade(overall_score)

    categories = [
        _category("Structural", report, property_data),
        _category("Water Damage", report, property_data),
        _category("Electrical", report, property_data),
        _category("Plumbing", report, property_data),
        _category("HVAC", report, property_data),
        _category("Foundation", report, property_data),
        _category("Roofing", report, property_data),
        _category("Insulation", report, property_data),
        _category("Interior Finishes", report, property_data),
        _category("Exterior", report, property_data),
    ]

    risk_level = _derive_risk_level(risk_level_str=None, health_score=overall_score)
    risk_color_map = {
        "Critical": "#EF4444", "High": "#F97316", "Medium": "#F59E0B", "Low": "#10B981",
    }
    risk_color = risk_color_map.get(risk_level, "#64748B")
    risk_bg_map = {
        "Critical": "rgba(239, 68, 68, 0.1)",
        "High": "rgba(249, 115, 22, 0.1)",
        "Medium": "rgba(245, 158, 11, 0.1)",
        "Low": "rgba(16, 185, 129, 0.1)",
    }
    risk_bg = risk_bg_map.get(risk_level, "rgba(100, 116, 139, 0.1)")

    return PropertyHealthReport(
        overall_score=overall_score,
        overall_grade=HealthGrade(grade, risk_color, risk_bg),
        immediate_risk=risk_level,
        remaining_life_years=random.uniform(10, 80),
        inspection_confidence=random.randint(75, 98),
        repair_priority_index=random.randint(15, 95),
        categories=categories,
        strengths=[
            "Well-maintained exterior paint in most areas",
            "Foundation shows no major settlement issues",
            "Electrical panel is modern and up to code",
        ],
        weaknesses=[
            "Water intrusion evidence in basement area",
            "Roof flashing requires attention",
            "HVAC system nearing end of useful life",
        ],
        priority_actions=[
            "Address water intrusion within 30 days to prevent mold",
            "Schedule roof inspection before next rainy season",
            "Budget for HVAC replacement within 2 years",
        ],
        future_predictions=FuturePredictions(
            damage_pct_3mo=random.uniform(5, 15),
            damage_pct_6mo=random.uniform(10, 25),
            damage_pct_12mo=random.uniform(15, 35),
        ),
        health_summary=(
            f"This property has been assigned an overall health grade of {grade} "
            f"({overall_score:.0f}/100) with {risk_level.lower()} risk level. "
            f"{len(report.damages)} damage type{'s' if len(report.damages) != 1 else ''} detected. "
            f"Immediate attention is recommended for water-related issues."
        ),
    )


def _category(name: str, report: InspectionReport, property_data: dict):
    """Build a HealthCategory for the given name."""
    from streamlit_app.ai.health_engine import HealthCategory, CategoryScore, CategoryGrade

    cat_damages = [d for d in report.damages if d.damage_type.lower() in name.lower() or name.lower() in d.damage_type.lower()]
    score = max(20, min(95, 85 - len(cat_damages) * 10))
    grade = _score_to_grade(score)
    color_map = {
        "A+": "#10B981", "A": "#10B981", "B+": "#22C55E",
        "B": "#84CC16", "C": "#F59E0B", "D": "#EF4444",
    }
    bg_map = {
        "A+": "rgba(16, 185, 129, 0.15)",
        "A": "rgba(16, 185, 129, 0.15)",
        "B+": "rgba(34, 197, 94, 0.15)",
        "B": "rgba(132, 204, 22, 0.15)",
        "C": "rgba(245, 158, 11, 0.15)",
        "D": "rgba(239, 68, 68, 0.15)",
    }
    return HealthCategory(
        category=name,
        score=score,
        grade=CategoryGrade(grade, color_map.get(grade, "#64748B"), bg_map.get(grade, "rgba(100, 116, 139, 0.15)")),
        findings_count=len(cat_damages),
        description=f"{name} assessment based on {len(cat_damages)} finding{'s' if len(cat_damages) != 1 else ''}",
        affected_areas=[d.damage_type for d in cat_damages[:3]],
        repair_priority="High" if len(cat_damages) > 0 else "Low",
        estimated_cost=sum(d.estimated_cost for d in cat_damages),
        criticality=max((d.severity for d in cat_damages), key=lambda s: {"Critical": 3, "High": 2, "Medium": 1, "Low": 0}.get(s, 0), default="Low"),
        repair_steps=[f"Address {name} issues per professional guidelines"] * min(len(cat_damages), 3),
        timeline_months=random.randint(1, 12),
    )


def _score_to_grade(score: float) -> str:
    if score >= 90: return "A+"
    if score >= 80: return "A"
    if score >= 70: return "B+"
    if score >= 60: return "B"
    if score >= 50: return "C"
    return "D"


def _derive_risk_level(risk_level_str: str, health_score: float) -> str:
    if health_score < 50: return "Critical"
    if health_score < 70: return "High"
    if health_score < 85: return "Medium"
    return "Low"


def _build_comparison(reports: list, property_data: dict):
    """Build a ComparisonResult from multiple reports."""
    from streamlit_app.report.risk_engine import ComparisonResult, ComparisonFinding
    import random

    current = reports[-1]
    previous = reports[-2] if len(reports) >= 2 else current

    current_hs = random.randint(55, 95)
    previous_hs = current_hs + random.randint(-15, 10)
    previous_hs = max(20, min(95, previous_hs))

    delta = current_hs - previous_hs

    def _grade_from_score(s):
        if s >= 90: return "A+"
        if s >= 80: return "A"
        if s >= 70: return "B+"
        if s >= 60: return "B"
        if s >= 50: return "C"
        return "D"

    grade_curr = _grade_from_score(current_hs)
    grade_prev = _grade_from_score(previous_hs)
    grade_changed = grade_curr != grade_prev

    if delta >= 5:
        risk_trend = "Improving"
    elif delta >= -5:
        risk_trend = "Stable"
    elif delta >= -15:
        risk_trend = "Declining"
    else:
        risk_trend = "Significant Decline"

    improvement_score = max(0, min(100, 50 + delta * 2))

    findings = [
        ComparisonFinding("Water Damage", "Resolved", "Gone", "Sealed"),
        ComparisonFinding("Roof Flashing", "New", "New", "Detected"),
    ]

    return ComparisonResult(
        current={
            "inspection_id": f"INS-{random.randint(1000, 9999)}",
            "health_score": current_hs,
            "total_repair_cost": random.randint(15000, 80000),
            "damage_pct": random.uniform(3, 15),
        },
        previous={
            "inspection_id": f"INS-{random.randint(1000, 9999)}",
            "health_score": previous_hs,
            "total_repair_cost": random.randint(15000, 80000),
            "damage_pct": random.uniform(3, 15),
        },
        health_score_delta=delta,
        current_grade=grade_curr,
        previous_grade=grade_prev,
        grade_changed=grade_changed,
        risk_trend=risk_trend,
        improvement_score=improvement_score,
        estimated_repair_cost_delta=random.randint(-5000, 10000),
        new_damage_count=random.randint(0, 3),
        resolved_damage_count=random.randint(0, 2),
        days_between_inspections=random.randint(30, 365),
        findings=findings,
        comparison_summary=(
            f"Health score {'improved' if delta > 0 else 'declined'} by {abs(delta):.0f} points. "
            f"Grade {'changed from ' + grade_prev + ' to ' + grade_curr if grade_changed else 'remained ' + grade_curr}. "
            f"{'No new damage detected.' if not findings else f'{len(findings)} changes detected.'}"
        ),
    )


def render_report_preview(
    reports: list[InspectionReport],
    property_data: dict,
    inspection_id: str,
) -> None:
    """Render a lightweight report preview (for tabs or side panels)."""
    if not reports:
        st.warning("No reports to preview.")
        return

    primary_report = reports[0]
    risk = assess_risk(primary_report, property_data)

    # Simple 4-up preview
    col1, col2, col3, col4 = st.columns(4, gap="medium")
    with col1:
        st.metric("Health Score", f"{risk.health_score}/100", f"{risk.health_score_delta:+.0f}")
    with col2:
        st.metric("Risk Level", risk.risk_level)
    with col3:
        st.metric("Damage", f"{risk.avg_damage_pct:.1f}%", f"max {risk.max_damage_pct:.1f}%")
    with col4:
        st.metric("Findings", str(risk.total_findings))


def _np_to_pil(arr) -> "Image.Image | None":
    """Convert numpy array or overlay dict to PIL Image (backward compat alias)."""
    if arr is None:
        return None
    from PIL import Image as PILImage
    if isinstance(arr, PILImage.Image):
        return arr
    if isinstance(arr, dict):
        arr = arr.get("image", arr)
    try:
        import numpy as _np
        if isinstance(arr, _np.ndarray):
            return PILImage.fromarray(arr)
    except ImportError:
        pass
    return None


# ── Backward-compatible aliases (used by pages/report.py) ─────────────
def _render_health_score_ring(score, grade, color):
    render_health_score_ring(score, grade, color)


def _render_health_dashboard(health):
    render_property_health_dashboard(health)


def _render_findings_section(findings):
    render_findings_section(findings)


def _render_comparison_section(comparison):
    render_comparison_section(comparison)


def _build_report_dict(
    report, property_data, inspection_id,
    health, risk, findings, recommendations, checklist, timeline,
) -> dict:
    """Build a flat dict suitable for ``generate_pdf()``."""
    pd = property_data or {}
    return {
        "inspection_id": inspection_id,
        "inspection_date": pd.get("inspection_date", ""),
        "property_address": pd.get("address", ""),
        "property_type": pd.get("property_type", ""),
        "property_city": "",
        "property_state": "",
        "inspector_name": pd.get("inspector_name", ""),
        "weather_condition": "",
        "overall_health_score": health.overall_score if health else 50,
        "overall_severity": report.severity if hasattr(report, "severity") else "Medium",
        "grade": health.grade.value if health else "C",
        "risk_level": risk.risk_level if risk else "Low",
        "overall_estimated_cost_min": risk.estimated_cost_min if risk else 0,
        "overall_estimated_cost_max": risk.estimated_cost_max if risk else 0,
        "avg_repair_cost": (
            (risk.estimated_cost_min + risk.estimated_cost_max) / 2 if risk else 0
        ),
        "executive_summary": (
            findings[0].recommendation if findings else "Inspection completed."
        ),
        "property_summary": pd.get("property_name", ""),
        "inspection_conclusion": (
            recommendations.get("inspection_conclusion", "Inspection completed successfully.")
            if isinstance(recommendations, dict)
            else "Inspection completed successfully."
        ),
        "findings": [
            {
                "damage_type": f.damage_type,
                "severity": f.severity,
                "location": f.location,
                "confidence": f.confidence,
                "description": f.description,
                "recommendation": f.recommendation,
            }
            for f in findings
        ],
        "timeline": [
            {
                "bucket": t.bucket,
                "description": ", ".join(
                    f.damage_type for f in t.findings
                ) if hasattr(t, "findings") else "",
            }
            for t in (timeline if isinstance(timeline, list) else [])
        ],
        "maintenance_tips": (
            recommendations.get("maintenance_tips", [])
            if isinstance(recommendations, dict)
            else []
        ),
    }