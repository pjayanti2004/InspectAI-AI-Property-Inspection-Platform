"""Inspection Comparison renderer for the report page.

Renders a comparison dashboard between previous and current inspections,
and the Measurements section.
"""
from __future__ import annotations

import streamlit as st

from streamlit_app.report.report_builder import _render_comparison_section
from streamlit_app.utils.constants import (
    BORDER_COLOR, TEXT_MUTED, TEXT_PRIMARY,
)


# Change type icons and colors used by the detailed comparison view.
_CHANGE_ICONS = {
    "new": "🆕", "resolved": "✅", "increased": "📈",
    "reduced": "📉", "unchanged": "➡", "grade_changed": "🏆",
}
_CHANGE_COLORS = {
    "new": "#EF4444", "resolved": "#10B981", "increased": "#F97316",
    "reduced": "#3B82F6", "unchanged": "#64748B", "grade_changed": "#8B5CF6",
}


def render_comparison(data: dict, comparison_report=None) -> None:
    """Render the Inspection Comparison section."""
    st.markdown(
        """
        <div class="section-title">📊 Inspection Comparison</div>
        """,
        unsafe_allow_html=True,
    )

    comparison_dict = data.get("comparison_report", {})

    if comparison_report:
        _render_comparison_section(comparison_report)
        return

    if not comparison_dict:
        st.info(
            "No previous inspection available for comparison. "
            "Run a second inspection on this property to enable comparison."
        )
        return

    current  = comparison_dict.get("current", {})
    previous = comparison_dict.get("previous", {})
    findings = comparison_dict.get("findings", [])
    summary  = comparison_dict.get("comparison_summary", "")

    if current and previous:
        _render_delta_cards(current, previous, comparison_dict)
    if findings:
        _render_findings_list(findings)
    if summary:
        _render_summary(summary)


def _render_delta_cards(current: dict, previous: dict, comparison_dict: dict) -> None:
    """Render the three delta cards: Score, Grade, Time."""
    curr_score = current.get("health_score", 0)
    prev_score = previous.get("health_score", 0)
    delta = curr_score - prev_score
    delta_color = "#10B981" if delta > 0 else "#EF4444" if delta < 0 else "#64748B"

    col1, col2, col3 = st.columns(3, gap="medium")
    with col1:
        st.markdown(
            f"""
            <div style="padding: 1rem; text-align: center; background: {delta_color}12;
                        border: 1px solid {delta_color}35; border-radius: 10px;">
                <div style="font-size: 0.7rem; color: #64748B; text-transform: uppercase;
                            letter-spacing: 0.06em; margin-bottom: 0.4rem;">Score Change</div>
                <div style="font-size: 1.75rem; font-weight: 800; color: {delta_color};">
                    {"+" if delta > 0 else ""}{delta:.0f}
                </div>
                <div style="font-size: 0.75rem; color: #64748B;">{prev_score:.0f} → {curr_score:.0f}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            f"""
            <div style="padding: 1rem; text-align: center; background: #1E293B;
                        border: 1px solid {BORDER_COLOR}; border-radius: 10px;">
                <div style="font-size: 0.7rem; color: #64748B; text-transform: uppercase;
                            letter-spacing: 0.06em; margin-bottom: 0.4rem;">Grade Change</div>
                <div style="font-size: 1.75rem; font-weight: 800; color: #3B82F6;">
                    {previous.get('grade', '—')} → {current.get('grade', '—')}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col3:
        days = comparison_dict.get("days_between_inspections", 0)
        st.markdown(
            f"""
            <div style="padding: 1rem; text-align: center; background: #1E293B;
                        border: 1px solid {BORDER_COLOR}; border-radius: 10px;">
                <div style="font-size: 0.7rem; color: #64748B; text-transform: uppercase;
                            letter-spacing: 0.06em; margin-bottom: 0.4rem;">Time Since Last</div>
                <div style="font-size: 1.75rem; font-weight: 800; color: #3B82F6;">{days} days</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def _render_findings_list(findings: list) -> None:
    """Render the detailed changes list."""
    st.markdown(
        f"<div style='font-size: 0.85rem; font-weight: 600; color: #334155; margin: 1rem 0 0.5rem;'>"
        f"Detailed Changes ({len(findings)})</div>",
        unsafe_allow_html=True,
    )
    for f in findings:
        if not isinstance(f, dict):
            continue
        change_type = f.get("change_type", "unchanged")
        category    = f.get("category", "")
        prev        = f.get("previous_status", "—")
        curr        = f.get("current_status", "—")
        icon  = _CHANGE_ICONS.get(change_type, "•")
        color = _CHANGE_COLORS.get(change_type, "#64748B")
        st.markdown(
            f"""
            <div style="padding: 0.6rem 1rem; margin-bottom: 0.4rem; background: {color}08;
                        border-left: 3px solid {color}; border-radius: 0 8px 8px 0;
                        display: flex; align-items: center; gap: 0.6rem;">
                <span>{icon}</span>
                <div>
                    <span style="font-weight: 600; color: #1E293B; font-size: 0.85rem;">
                        {category} — <span style="color: {color};">{change_type}</span>
                    </span>
                    <span style="font-size: 0.8rem; color: #64748B; margin-left: 0.5rem;">
                        {prev} → {curr}
                    </span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def _render_summary(summary: str) -> None:
    """Render the comparison summary block."""
    st.markdown(
        f"""
        <div style="padding: 0.75rem; background: #F8FAFC; border-radius: 8px;
                    border: 1px solid {BORDER_COLOR}; font-size: 0.85rem;
                    color: #64748B; font-style: italic; margin-top: 0.5rem;">
            {summary}
        </div>
        """,
        unsafe_allow_html=True,
    )


# ──────────────────────────────────────────────────────────────────────────────
# Measurements
# ──────────────────────────────────────────────────────────────────────────────

def render_measurements(data: dict) -> None:
    """Render the Measurements overview section."""
    st.markdown(
        """
        <div class="section-title">📐 Measurements</div>
        """,
        unsafe_allow_html=True,
    )

    raw_reports = data.get("raw_reports", [])
    found = False
    for report in raw_reports:
        if isinstance(report, dict):
            mr = report.get("measurement_report")
            if mr and isinstance(mr, dict):
                found = True
                _render_measurement_data(mr)

    if not found:
        damage_pct  = data.get("overall_damage_pct", 0)
        damage_area = data.get("total_repair_area_px", 0)
        crack_w     = data.get("avg_crack_width_px", 0)

        if damage_pct or damage_area or crack_w:
            st.markdown(
                f"""
                <div class="card-glass" style="padding: 1.25rem 1.5rem; border: 1px solid {BORDER_COLOR};">
                    <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem;">
                        <div style="text-align: center;">
                            <div style="font-size: 0.7rem; color: #64748B; text-transform: uppercase;
                                        letter-spacing: 0.05em; margin-bottom: 0.3rem;">Damage Coverage</div>
                            <div style="font-size: 1.5rem; font-weight: 700; color: #F97316;">{damage_pct:.1f}%</div>
                        </div>
                        <div style="text-align: center;">
                            <div style="font-size: 0.7rem; color: #64748B; text-transform: uppercase;
                                        letter-spacing: 0.05em; margin-bottom: 0.3rem;">Damage Area</div>
                            <div style="font-size: 1.5rem; font-weight: 700; color: #EF4444;">{damage_area:,} px</div>
                        </div>
                        <div style="text-align: center;">
                            <div style="font-size: 0.7rem; color: #64748B; text-transform: uppercase;
                                        letter-spacing: 0.05em; margin-bottom: 0.3rem;">Avg Crack Width</div>
                            <div style="font-size: 1.5rem; font-weight: 700; color: #F59E0B;">{crack_w:.1f} px</div>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.info("No detailed measurements available for this report.")


def _render_measurement_data(mr: dict) -> None:
    """Render individual measurement entries."""
    measurements = mr.get("measurements", [])
    if not measurements:
        st.info("No specific measurements recorded.")
        return

    for m in measurements[:8]:
        if not isinstance(m, dict):
            continue
        name  = m.get("measurement_type", m.get("name", "—"))
        value = m.get("value", m.get("measured_value", "—"))
        unit  = m.get("unit", "")
        conf  = m.get("confidence", 0)

        st.markdown(
            f"""
            <div style="
                display: flex; justify-content: space-between; align-items: center;
                padding: 0.6rem 1rem; margin-bottom: 0.4rem;
                background: #1E293B; border: 1px solid {BORDER_COLOR}; border-radius: 8px;
            ">
                <div>
                    <div style="font-size: 0.85rem; font-weight: 600; color: {TEXT_PRIMARY};">{name}</div>
                    <div style="font-size: 0.75rem; color: {TEXT_MUTED};">Confidence: {conf}%</div>
                </div>
                <div style="font-size: 1.1rem; font-weight: 700; color: #3B82F6;">{value} {unit}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


__all__ = [
    "render_comparison",
    "render_measurements",
]
