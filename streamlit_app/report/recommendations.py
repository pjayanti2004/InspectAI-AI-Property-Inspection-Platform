"""Recommendations renderers for the report module."""
from __future__ import annotations

import streamlit as st

from streamlit_app.components.ui_components import render_html


def render_recommendations_section(recommendations: dict) -> None:
    """Render recommendations: immediate actions, repair priority, maintenance tips."""
    render_html("""
        <div class="section-title">💡 Recommendations</div>
        """,
    )

    col1, col2 = st.columns(2, gap="medium")

    with col1:
        render_html(
            """
            <div style="font-size: 0.85rem; font-weight: 700; color: #EF4444; margin-bottom: 0.75rem;">
                🚨 Immediate Actions
            </div>
            """,
        )
        for action in recommendations.get("immediate_actions", []):
            render_html(f"<div style='font-size: 0.85rem; color: #94A3B8; padding: 0.3rem 0;'>• {action}</div>")

        render_html("""
            <div style="font-size: 0.85rem; font-weight: 700; color: #F59E0B; margin: 1.25rem 0 0.75rem;">
                🔧 Professional Help
            </div>
            """,
        )
        for prof in recommendations.get("professional_help", []):
            render_html(f"<div style='font-size: 0.85rem; color: #94A3B8; padding: 0.3rem 0;'>• {prof}</div>")

    with col2:
        render_html("""
            <div style="font-size: 0.85rem; font-weight: 700; color: #F59E0B; margin-bottom: 0.75rem;">
                📋 Repair Priority
            </div>
            """,
        )
        for i, step in enumerate(recommendations.get("repair_priority", [])[:8], start=1):
            render_html(
                f"<div style='font-size: 0.85rem; color: #94A3B8; padding: 0.3rem 0;'>{i}. {step}</div>",
            )

        render_html(
            """
            <div style="font-size: 0.85rem; font-weight: 700; color: #10B981; margin: 1.25rem 0 0.75rem;">
                🛡️ Maintenance Tips
            </div>
            """,
        )
        for tip in recommendations.get("maintenance_tips", []):
            render_html(f"<div style='font-size: 0.85rem; color: #94A3B8; padding: 0.3rem 0;'>• {tip}</div>")