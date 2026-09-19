"""Executive summary and stat row renderers."""
from __future__ import annotations

import streamlit as st

from streamlit_app.components.ui_components import render_html


def render_executive_summary(summary) -> None:
    """Render the executive summary card."""
    from streamlit_app.utils.constants import BORDER_COLOR, TEXT_PRIMARY, TEXT_MUTED

    render_html(
        f"""
        <div class="card-glass" style="
            padding: 1.75rem 2rem;
            margin: 1rem 0;
            border: 1px solid {BORDER_COLOR};
        ">
            <div style="display: flex; justify-content: space-between; align-items: flex-start;
                        margin-bottom: 1.25rem; padding-bottom: 1rem; border-bottom: 1px solid {BORDER_COLOR};">
                <div>
                    <div style="font-size: 0.7rem; color: #64748B; text-transform: uppercase;
                                letter-spacing: 0.1em; margin-bottom: 0.25rem;">Inspection ID</div>
                    <div style="font-size: 1.1rem; font-weight: 700; color: {TEXT_PRIMARY};">
                        {summary.inspection_id}
                    </div>
                </div>
                <div style="text-align: right;">
                    <div style="font-size: 0.7rem; color: {TEXT_MUTED};">Date</div>
                    <div style="font-size: 0.9rem; font-weight: 600; color: {TEXT_PRIMARY};">
                        {summary.inspection_date}
                    </div>
                </div>
            </div>

            <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 1rem 2rem;">
                <div>
                    <div style="font-size: 0.7rem; color: #64748B; text-transform: uppercase;
                                letter-spacing: 0.08em;">Property</div>
                    <div style="font-size: 0.95rem; font-weight: 600; color: {TEXT_PRIMARY}; margin-top: 0.2rem;">
                        {summary.property_name}
                    </div>
                    <div style="font-size: 0.8rem; color: {TEXT_MUTED};">{summary.property_type}</div>
                </div>
                <div>
                    <div style="font-size: 0.7rem; color: #64748B; text-transform: uppercase;
                                letter-spacing: 0.08em;">Inspector</div>
                    <div style="font-size: 0.95rem; font-weight: 600; color: {TEXT_PRIMARY}; margin-top: 0.2rem;">
                        {summary.inspector_name}
                    </div>
                </div>
                <div>
                    <div style="font-size: 0.7rem; color: #64748B; text-transform: uppercase;
                                letter-spacing: 0.08em;">Images Analysed</div>
                    <div style="font-size: 0.95rem; font-weight: 600; color: {TEXT_PRIMARY}; margin-top: 0.2rem;">
                        {summary.image_count}
                    </div>
                </div>
                <div>
                    <div style="font-size: 0.7rem; color: #64748B; text-transform: uppercase;
                                letter-spacing: 0.08em;">Processing Time</div>
                    <div style="font-size: 0.95rem; font-weight: 600; color: {TEXT_PRIMARY}; margin-top: 0.2rem;">
                        {summary.processing_time_sec:.1f}s
                    </div>
                </div>
            </div>
        </div>
        """,
    )


def render_stat_row(summary, risk) -> None:
    """Render a row of 4 stat cards below the executive summary."""
    from streamlit_app.utils.constants import PRIMARY, SUCCESS, WARNING, DANGER, TEXT_MUTED

    stats = [
        {
            "label": "Total Findings",
            "value": str(summary.total_findings),
            "icon": "🔍",
            "color": PRIMARY,
            "trend": f"{risk.critical_count + risk.high_count} urgent",
            "trend_up": risk.critical_count > 0,
        },
        {
            "label": "Avg Confidence",
            "value": f"{summary.avg_confidence:.0f}%",
            "icon": "🤖",
            "color": SUCCESS,
            "trend": "AI-powered",
            "trend_up": True,
        },
        {
            "label": "Est. Repair Cost",
            "value": f"₹{summary.estimated_cost_min:,}",
            "icon": "💰",
            "color": WARNING,
            "trend": f"up to ₹{summary.estimated_cost_max:,}",
            "trend_up": True,
        },
        {
            "label": "Damage Coverage",
            "value": f"{risk.avg_damage_pct:.1f}%",
            "icon": "📐",
            "color": DANGER if risk.avg_damage_pct > 5 else WARNING,
            "trend": f"max {risk.max_damage_pct:.1f}%",
            "trend_up": risk.max_damage_pct > 10,
        },
    ]

    cols = st.columns(4, gap="medium")
    for col, stat in zip(cols, stats):
        with col:
            trend_arrow = "↗" if stat.get("trend_up", True) else "↘"
            trend_col = SUCCESS if stat.get("trend_up", True) else WARNING
            render_html(
                f"""
                <div style="
                    background: {stat['color']}15;
                    border: 1px solid {stat['color']}40;
                    border-radius: 10px;
                    padding: 1.1rem 1rem;
                    text-align: center;
                ">
                    <div style="font-size: 1.5rem; margin-bottom: 0.4rem;">{stat['icon']}</div>
                    <div style="font-size: 1.5rem; font-weight: 800; color: #F1F5F9;">{stat['value']}</div>
                    <div style="font-size: 0.7rem; color: {TEXT_MUTED}; text-transform: uppercase;
                                letter-spacing: 0.05em; margin-top: 0.2rem;">{stat['label']}</div>
                    <div style="font-size: 0.75rem; color: {trend_col}; margin-top: 0.3rem;">
                        {trend_arrow} {stat.get('trend', '')}
                    </div>
                </div>
                """,
    
            )