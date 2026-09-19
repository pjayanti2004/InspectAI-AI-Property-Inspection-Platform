"""Repair timeline and checklist renderers for the report module."""
from __future__ import annotations

import streamlit as st

from streamlit_app.components.ui_components import render_html


def render_timeline_section(timeline: list) -> None:
    """Render the repair timeline in 4 columns."""
    render_html(
        """
        <div class="section-title">📅 Repair Timeline</div>
        """,
    )

    cols = st.columns(4, gap="medium")
    for col, entry in zip(cols, timeline):
        with col:
            render_html(
                f"""
                <div style="
                    background: #1E293B; border: 1px solid #334155; border-radius: 10px;
                    padding: 1.25rem; text-align: center; height: 100%;
                ">
                    <div style="font-size: 1.75rem; margin-bottom: 0.5rem;">{entry.icon}</div>
                    <div style="font-size: 0.7rem; color: #64748B; text-transform: uppercase;
                                letter-spacing: 0.08em; margin-bottom: 0.75rem;">{entry.bucket}</div>
                    <div style="font-size: 1.75rem; font-weight: 800; color: {entry.color};">
                        {len(entry.findings)}
                    </div>
                    <div style="font-size: 0.75rem; color: #64748B;">finding{'s' if len(entry.findings) != 1 else ''}</div>
                </div>
                """,
            )

            # List findings in this bucket
            if entry.findings:
                for f in entry.findings:
                    sev_color = {
                        "Critical": "#EF4444", "High": "#F97316",
                        "Medium": "#F59E0B", "Low": "#10B981",
                    }.get(f.severity, "#64748B")
                    render_html(
                        f"""
                        <div style="
                            padding: 0.4rem 0.6rem; margin: 0.35rem 0;
                            background: #0F172A; border-left: 3px solid {sev_color};
                            border-radius: 0 6px 6px 0; font-size: 0.75rem; color: #94A3B8;
                        ">{f.damage_type}</div>
                        """,
                    )


def render_checklist_section(checklist: list) -> None:
    """Render the completed inspection checklist."""
    render_html(
        """
        <div class="section-title">✅ Inspection Checklist</div>
        """,
    )

    for item in checklist:
        checked = item.get("checked", False)
        icon = "✅" if checked else "⬜"
        color = "#10B981" if checked else "#64748B"
        render_html(
            f"""
            <div style="
                display: flex; align-items: center; gap: 0.75rem;
                padding: 0.75rem 1rem; margin-bottom: 0.5rem;
                background: #1E293B; border: 1px solid #334155; border-radius: 8px;
            ">
                <span style="font-size: 1.1rem;">{icon}</span>
                <span style="color: {color}; font-size: 0.9rem; font-weight: 500;">{item['category']}</span>
                <span style="margin-left: auto; font-size: 0.8rem; color: #64748B;">{item.get('status', '—')}</span>
            </div>
            """,
        )