"""Measurements and measurement detail renderer for the report page.

Renders the Measurements section using raw measurement_report data from
inspection results, with a summary fallback when detailed data is absent.
"""
from __future__ import annotations

import streamlit as st

from streamlit_app.utils.constants import (
    BORDER_COLOR, TEXT_MUTED, TEXT_PRIMARY,
)


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
                render_measurement_data(mr)

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


def render_measurement_data(mr: dict) -> None:
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
