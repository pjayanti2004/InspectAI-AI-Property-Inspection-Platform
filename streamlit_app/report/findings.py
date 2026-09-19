"""Finding card and findings list renderers for the report module."""
from __future__ import annotations

import streamlit as st

from streamlit_app.components.ui_components import render_html


def render_finding_card(finding, index: int) -> None:
    """Render a single finding card with image thumbnail, details, and actions."""
    from streamlit_app.utils.constants import (
        SEVERITY_COLORS, SEVERITY_BG, TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED, BORDER_COLOR
    )
    from streamlit_app.report.report_builder import _np_to_pil

    sev_color = SEVERITY_COLORS.get(finding.severity, "#64748B")
    sev_bg = SEVERITY_BG.get(finding.severity, "rgba(100, 116, 139, 0.15)")

    thumb = _np_to_pil(finding.overlay_image)
    col_img, col_details = st.columns([1, 2], gap="medium")

    with col_img:
        if thumb:
            st.image(thumb, use_container_width=True, caption=finding.file_name)
        else:
            render_html(f"""
                <div style="
                    background: #1E293B; border: 1px dashed #334155; border-radius: 8px;
                    height: 140px; display: flex; align-items: center; justify-content: center;
                    color: #64748B; font-size: 0.85rem;
                ">📷 {finding.file_name}</div>
                """,
            )

    with col_details:
        render_html(
            f"""
            <div style="
                background: #1E293B; border: 1px solid {BORDER_COLOR}; border-radius: 10px;
                padding: 1.25rem; margin-bottom: 0.75rem;
            ">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.75rem;">
                    <span style="font-size: 1.05rem; font-weight: 700; color: {TEXT_PRIMARY};">
                        {finding.damage_type}
                    </span>
                    <span style="
                        padding: 0.3rem 0.8rem; background: {sev_bg}; color: {sev_color};
                        border-radius: 6px; font-size: 0.75rem; font-weight: 700;
                        text-transform: uppercase; letter-spacing: 0.05em;
                    ">{finding.severity}</span>
                </div>

                <div style="display: flex; gap: 1.5rem; margin-bottom: 0.75rem; font-size: 0.8rem; color: {TEXT_MUTED};">
                    <span>🎯 <strong style="color: {TEXT_SECONDARY};">{finding.confidence}%</strong> Confidence</span>
                    <span>📏 <strong style="color: {TEXT_SECONDARY};">{finding.damage_pct:.1f}%</strong> Area</span>
                    <span>📍 <strong style="color: {TEXT_SECONDARY};">{finding.contour_count}</strong> Region{'s' if finding.contour_count != 1 else ''}</span>
                </div>

                <div style="margin-bottom: 0.5rem;">
                    <div style="font-size: 0.75rem; color: {TEXT_MUTED}; text-transform: uppercase;
                                letter-spacing: 0.08em; margin-bottom: 0.25rem;">Possible Causes</div>
                    <div style="font-size: 0.85rem; color: {TEXT_SECONDARY};">
                        {', '.join(finding.possible_causes[:3])}
                    </div>
                </div>

                <div style="margin-bottom: 0.5rem;">
                    <div style="font-size: 0.75rem; color: {TEXT_MUTED}; text-transform: uppercase;
                                letter-spacing: 0.08em; margin-bottom: 0.25rem;">Repair Steps</div>
                    <ul style="margin: 0; padding-left: 1.2rem; font-size: 0.85rem; color: {TEXT_SECONDARY};">
                        {"".join(f"<li style='margin-bottom: 0.2rem;'>{s}</li>" for s in finding.repair_steps[:4])}
                    </ul>
                </div>

                <div style="display: flex; justify-content: space-between; align-items: center;
                            margin-top: 0.75rem; padding-top: 0.75rem; border-top: 1px solid {BORDER_COLOR};">
                    <span style="font-size: 0.8rem; color: {TEXT_MUTED};">
                        👷 {finding.recommended_professional}
                    </span>
                    <span style="font-size: 0.9rem; font-weight: 700; color: #4F46E5;">
                        {finding.estimated_cost_range}
                    </span>
                </div>
            </div>
            """,
        )


def render_findings_section(findings: list) -> None:
    """Render all finding cards in a numbered list."""
    if not findings:
        st.info("No significant damage detected in the uploaded images.")
        return

    render_html(
        f"""
        <div class="section-title">🔍 Findings ({len(findings)} detected)</div>
        """,
    )

    for i, finding in enumerate(findings, start=1):
        with st.container():
            render_html(
                f"<div style='font-size: 0.8rem; color: #64748B; margin-bottom: 0.25rem;'>Finding #{i}</div>",
            )
            render_finding_card(finding, index=i)
            if i < len(findings):
                render_html("<div style='height: 0.5rem;'></div>")