"""Report Detail Page — Professional inspection report display.

Sections rendered in order:
  1. Quick Stats (health score, grade, risk level, repair cost)
  2. Executive Summary
  3. Property Health Dashboard
  4. Damage Findings
  5. Measurements
  6. Inspection Comparison
  7. Repair Plan & Recommendations
  8. Recommendations
  9. Repair Timeline

Data source priority:
  1. ``view_report_id`` in session state → load from SQLite database.
  2. ``SessionKeys.INSPECTION_DATA`` in session state → wizard flow.

PDF export is available via the pdf_generator module.

Public API: ``render_report_page()``
"""
from __future__ import annotations

import streamlit as st

from streamlit_app.components.ui_components import (
    inject_custom_css,
    init_page_config,
    render_html,
    render_header,
)
from streamlit_app.database import get_report
from streamlit_app.report.report_builder import render_report
from streamlit_app.report.risk_engine import assess_risk
from streamlit_app.report.summary_engine import (
    build_executive_summary,
    build_findings,
    build_timeline,
    build_recommendations,
)
from streamlit_app.utils.constants import (
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED, BORDER_COLOR,
    BG_CARD, SEVERITY_COLORS,
)
from streamlit_app.utils.session_manager import SessionKeys, navigate_to


SEVERITY_CLR = SEVERITY_COLORS


# ── Local helpers ──────────────────────────────────────────────────────────────

def _score_to_grade(score: float) -> str:
    if score >= 90: return "A+"
    if score >= 80: return "A"
    if score >= 70: return "B+"
    if score >= 60: return "B"
    if score >= 50: return "C"
    return "D"


def _avg_cost(min_c: int, max_c: int) -> int:
    return (min_c + max_c) // 2 if (min_c or max_c) else 0


def _obj_to_dict(obj) -> dict:
    """Convert a dataclass object to a plain dict, excluding binary fields."""
    if hasattr(obj, '__dict__'):
        return {k: v for k, v in obj.__dict__.items()
                if k not in ('image_thumbnail', 'overlay_image', 'processed_image',
                             'damage_mask', 'heatmap', 'measurement_report')}
    return obj if isinstance(obj, dict) else {}


# ── Main entry point ───────────────────────────────────────────────────────────

def render_report_page():
    """Render the full inspection report page.

    Data source priority:
      1. ``view_report_id`` → load from SQLite database.
      2. ``SessionKeys.INSPECTION_DATA`` → wizard flow.
    """
    inject_custom_css()
    init_page_config()

    view_report_id = st.session_state.get("view_report_id")
    report_data    = None
    property_data  = {}
    reports: list  = []
    health_report  = None
    comparison_report = None
    inspection_id  = ""
    inspector_name = "Inspector"

    if view_report_id:
        # ── Load from database ────────────────────────────────────────────
        db_report = get_report(view_report_id)
        if not db_report:
            from streamlit_app.views.report.helpers import render_not_found
            render_not_found(view_report_id)
            return

        report_data = db_report

        # Reconstruct InspectionReport objects from raw_reports
        raw_reports = db_report.get("raw_reports", [])
        if raw_reports:
            try:
                from streamlit_app.ai.inspection_engine import InspectionReport
                reports = [InspectionReport(**r) for r in raw_reports if isinstance(r, dict)]
            except Exception:
                reports = []

        from streamlit_app.views.report.helpers import rebuild_health_report
        health_report = rebuild_health_report(db_report.get("health_report", {}))

        from streamlit_app.views.report.helpers import rebuild_comparison_report
        comparison_report = rebuild_comparison_report(db_report.get("comparison_report", {}))

        inspection_id  = db_report.get("inspection_id", view_report_id)
        inspector_name = db_report.get("inspector_name", "Inspector")

        from streamlit_app.database import get_inspection_history
        history = get_inspection_history(search=view_report_id, limit=1)
        if history:
            h = history[0]
            property_data = {
                "property_name":    h.get("property_name", ""),
                "property_address": h.get("property_address", ""),
                "property_type":    h.get("property_type", ""),
                "property_city":    h.get("property_city", ""),
                "property_state":   h.get("property_state", ""),
            }
        else:
            property_data = {
                "property_name":    db_report.get("property_address", ""),
                "property_address": db_report.get("property_address", ""),
                "property_type":    "",
                "property_city":    "",
                "property_state":   "",
            }

    else:
        inspection_data = st.session_state.get(SessionKeys.INSPECTION_DATA)
        if not inspection_data:
            from streamlit_app.views.report.helpers import render_no_data
            render_no_data()
            return

        property_data = inspection_data.get("property_data", {}) or {}
        raw_reports   = inspection_data.get("ai_reports", [])
        if raw_reports:
            from streamlit_app.ai.inspection_engine import InspectionReport
            for r in raw_reports:
                if isinstance(r, InspectionReport):
                    reports.append(r)
                elif isinstance(r, dict):
                    try:
                        reports.append(InspectionReport(**r))
                    except Exception:
                        pass

        inspection_id  = inspection_data.get("id", "")
        inspector_name = (
            st.session_state.get(SessionKeys.USER_DATA, {}).get("full_name", "Inspector")
            if isinstance(st.session_state.get(SessionKeys.USER_DATA), dict)
            else "Inspector"
        )

        from streamlit_app.views.report.helpers import rebuild_health_report
        health_report = rebuild_health_report(
            inspection_data.get("health_report", {}) if inspection_data else {}
        )

    if not reports and not report_data:
        from streamlit_app.views.report.helpers import render_no_data
        render_no_data()
        return

    # Build unified report_data dict
    if not report_data:
        risk    = assess_risk(reports)
        summary = build_executive_summary(
            reports, property_data=property_data,
            inspection_id=inspection_id, inspector_name=inspector_name,
        )
        findings_list   = build_findings(reports)
        timeline_list   = build_timeline(findings_list)
        recs            = build_recommendations(reports)

        report_data = {
            "inspection_id":                  inspection_id,
            "inspection_date":                summary.inspection_date,
            "property_address":               property_data.get("property_name", property_data.get("property_address", "")),
            "property_type":                  property_data.get("property_type", ""),
            "property_city":                  property_data.get("property_city", ""),
            "property_state":                 property_data.get("property_state", ""),
            "inspector_name":                 inspector_name,
            "weather_condition":              "",
            "overall_health_score":           risk.health_score,
            "overall_damage_pct":             risk.avg_damage_pct,
            "overall_severity":               risk.risk_level,
            "grade":                          _score_to_grade(risk.health_score),
            "risk_level":                     risk.risk_level,
            "overall_estimated_cost_min":     risk.estimated_cost_min,
            "overall_estimated_cost_max":     risk.estimated_cost_max,
            "avg_repair_cost":                _avg_cost(risk.estimated_cost_min, risk.estimated_cost_max),
            "total_repair_area_px":           risk.total_damage_area_px,
            "avg_crack_width_px":             0.0,
            "processing_time_sec":            getattr(summary, 'processing_time_sec', 0),
            "executive_summary":              getattr(summary, 'executive_summary', ""),
            "property_summary":               getattr(summary, 'property_summary', ""),
            "inspection_conclusion":          getattr(summary, 'inspection_conclusion', ""),
            "findings":                       [_obj_to_dict(f) for f in findings_list],
            "timeline":                       [_obj_to_dict(t) for t in timeline_list],
            "maintenance_tips":               recs.get("maintenance_tips", []),
        }

    # Action bar
    col_back, col_pdf = st.columns([1, 1])
    with col_back:
        if st.button("← Back", type="secondary", use_container_width=True):
            st.session_state.pop("view_report_id", None)
            st.session_state.pop("_reports_page", None)
            navigate_to("reports")
    with col_pdf:
        from streamlit_app.views.report.pdf_actions import download_pdf
        download_pdf(report_data, inspection_id)

    render_html("<div style='height: 1.5rem;'></div>")

    # Page header
    prop_name = report_data.get("property_address", "—")
    render_header(
        title=f"Report {inspection_id}",
        subtitle=prop_name,
        icon="📑",
    )

    # Sections (delegated to sibling modules per the refactor spec)
    from streamlit_app.views.report.health import render_health_dashboard
    from streamlit_app.views.report.findings import render_findings
    from streamlit_app.views.report.comparison import (
        render_comparison,
        render_measurements,
    )
    from streamlit_app.views.report.findings import (
        render_repair_plan,
        render_recommendations,
        render_timeline,
    )

    _render_quick_stats(report_data)
    _render_exec_summary(report_data)
    render_health_dashboard(report_data, health_report)
    render_findings(report_data)
    render_measurements(report_data)
    render_comparison(report_data, comparison_report)
    render_repair_plan(report_data)
    render_recommendations(report_data)
    render_timeline(report_data)

    # Footer
    render_html("<div style='height: 2rem;'></div>")
    date_str = report_data.get("inspection_date", "—")
    render_html(
        f"""
        <div style="
            text-align: center; padding: 1.5rem; border-top: 1px solid {BORDER_COLOR};
            color: {TEXT_MUTED}; font-size: 0.8rem;
        ">
            <p style="margin: 0;">InspectAI — Automated Property Inspection Report</p>
            <p style="margin: 0.25rem 0 0;">Report ID: {inspection_id} | Generated: {date_str}</p>
        </div>
        """,

    )


# ──────────────────────────────────────────────────────────────────────────────
# Section renderers owned by page.py
# ──────────────────────────────────────────────────────────────────────────────

def _render_quick_stats(data: dict):
    """Four stat cards: health score, grade, risk level, repair cost."""
    from streamlit_app.views.report.helpers import grade_color, risk_color

    health_score = data.get("overall_health_score", 0)
    risk_level   = data.get("risk_level", "Low")
    grade        = data.get("grade", "—")
    est_min      = data.get("overall_estimated_cost_min", 0)
    est_max      = data.get("overall_estimated_cost_max", 0)

    sev_color    = risk_color(risk_level)
    grade_color_v = grade_color(grade)
    health_color = "#10B981" if health_score >= 70 else "#F59E0B" if health_score >= 50 else "#EF4444"
    cost_display = f"₹{est_min:,} – ₹{est_max:,}" if (est_min or est_max) else "—"

    stats = [
        ("Health Score", str(health_score) + "/100", health_color),
        ("Grade", grade, grade_color_v),
        ("Risk Level", risk_level, sev_color),
        ("Est. Repair", cost_display, "#F59E0B"),
    ]

    cols = st.columns(4, gap="medium")
    for col, (label, value, color) in zip(cols, stats):
        with col:
            render_html(
                f"""
                <div class="stat-card" style="
                    background: {color}12; border: 1px solid {color}35;
                ">
                    <div style="font-size: 0.7rem; color: #64748B; text-transform: uppercase;
                                letter-spacing: 0.05em; margin-bottom: 0.3rem;">{label}</div>
                    <div style="font-size: 1.5rem; font-weight: 800; color: {color};">{value}</div>
                </div>
                """,
    
            )


def _render_exec_summary(data: dict):
    """Executive summary card with property & inspection details."""
    render_html(
        """
        <div class="section-title">📋 Executive Summary</div>
        """,

    )

    inspection_id   = data.get("inspection_id", "—")
    inspection_date = data.get("inspection_date", "—")
    inspector_name  = data.get("inspector_name", "—")
    property_type   = data.get("property_type", "—").title()
    weather         = data.get("weather_condition", "—")
    processing_time = data.get("processing_time_sec", 0)

    render_html(
        f"""
        <div class="card-glass" style="padding: 1.5rem 2rem; border: 1px solid {BORDER_COLOR};">
            <div style="display: flex; justify-content: space-between; align-items: flex-start;
                        margin-bottom: 1rem; padding-bottom: 0.75rem; border-bottom: 1px solid {BORDER_COLOR};">
                <div>
                    <div style="font-size: 0.7rem; color: #64748B; text-transform: uppercase;
                                letter-spacing: 0.08em; margin-bottom: 0.2rem;">Inspection ID</div>
                    <div style="font-size: 1.1rem; font-weight: 700; color: {TEXT_PRIMARY};">{inspection_id}</div>
                </div>
                <div style="text-align: right;">
                    <div style="font-size: 0.7rem; color: {TEXT_MUTED};">Date</div>
                    <div style="font-size: 0.9rem; font-weight: 600; color: {TEXT_PRIMARY};">{inspection_date}</div>
                </div>
            </div>
            <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 0.75rem 2rem;">
                <div>
                    <div style="font-size: 0.7rem; color: #64748B; text-transform: uppercase;
                                letter-spacing: 0.06em;">Property Type</div>
                    <div style="font-size: 0.9rem; font-weight: 600; color: {TEXT_PRIMARY}; margin-top: 0.15rem;">{property_type}</div>
                </div>
                <div>
                    <div style="font-size: 0.7rem; color: #64748B; text-transform: uppercase;
                                letter-spacing: 0.06em;">Inspector</div>
                    <div style="font-size: 0.9rem; font-weight: 600; color: {TEXT_PRIMARY}; margin-top: 0.15rem;">{inspector_name}</div>
                </div>
                <div>
                    <div style="font-size: 0.7rem; color: #64748B; text-transform: uppercase;
                                letter-spacing: 0.06em;">Weather</div>
                    <div style="font-size: 0.9rem; font-weight: 600; color: {TEXT_PRIMARY}; margin-top: 0.15rem;">{weather}</div>
                </div>
            </div>
        </div>
        """,

    )

    if processing_time:
        st.metric("AI Processing Time", f"{processing_time:.1f}s")

    for label, key in [
        ("AI Analysis Summary", "executive_summary"),
        ("Property Summary", "property_summary"),
        ("Conclusion", "inspection_conclusion"),
    ]:
        text = data.get(key, "")
        if text:
            render_html(
                f"""
                <div class="card-glass" style="padding: 1.25rem 1.5rem; border: 1px solid {BORDER_COLOR}; margin-top: 0.75rem;">
                    <div style="font-size: 0.7rem; color: #64748B; text-transform: uppercase;
                                letter-spacing: 0.08em; margin-bottom: 0.5rem;">{label}</div>
                    <p style="color: #94A3B8; font-size: 0.9rem; line-height: 1.7; margin: 0;">{text}</p>
                </div>
                """,
    
            )


__all__ = ["render_report_page"]
