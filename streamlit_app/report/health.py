"""Health score ring and risk badge renderers for the report module."""
from __future__ import annotations

import math

import streamlit as st

from streamlit_app.components.ui_components import render_html


def render_health_score_ring(score: int, risk_level: str, risk_color: str) -> None:
    """Render the health score SVG ring inline."""
    pct = score / 100.0
    circumference = 2 * math.pi * 52
    offset = circumference * (1 - pct)

    if score >= 80:
        label = "Good"
    elif score >= 60:
        label = "Fair"
    else:
        label = "Poor"

    render_html(f"""
        <div style="display: flex; flex-direction: column; align-items: center; gap: 0.5rem;">
            <div style="position: relative; width: 140px; height: 140px;">
                <svg width="140" height="140" viewBox="0 0 120 120">
                    <circle cx="60" cy="60" r="52" fill="none" stroke="#334155" stroke-width="8" />
                    <circle cx="60" cy="60" r="52" fill="none" stroke="{risk_color}" stroke-width="8"
                        stroke-dasharray="{circumference:.2f}" stroke-dashoffset="{offset:.2f}"
                        stroke-linecap="round" transform="rotate(-90 60 60)"
                        style="transition: stroke-dashoffset 1.5s ease-out;" />
                </svg>
                <div style="position: absolute; inset: 0; display: flex; flex-direction: column;
                            align-items: center; justify-content: center;">
                    <span style="font-size: 2.25rem; font-weight: 800; color: #F1F5F9; line-height: 1;">
                        {score}<span style="font-size: 0.9rem; color: #64748B; font-weight: 500;">/100</span>
                    </span>
                    <span style="font-size: 0.65rem; color: {risk_color}; text-transform: uppercase;
                                 letter-spacing: 0.1em; margin-top: 0.25rem; font-weight: 600;">{label}</span>
                </div>
            </div>
            <span style="font-size: 0.8rem; color: #64748B;">Health Score</span>
        </div>
        """,
    )


def render_risk_badge(risk) -> None:
    """Render a risk assessment badge.

    Args:
        risk: RiskAssessment instance with risk_level, risk_color, risk_bg, total_findings, etc.
    """
    render_html(
        f"""
        <div style="
            background: {risk.risk_bg};
            border: 1px solid {risk.risk_color};
            border-radius: 10px;
            padding: 1rem;
            text-align: center;
        ">
            <div style="font-size: 0.7rem; color: #64748B; text-transform: uppercase;
                        letter-spacing: 0.1em; margin-bottom: 0.5rem;">
                Risk Level
            </div>
            <div style="font-size: 1.75rem; font-weight: 800; color: {risk.risk_color};">
                {risk.risk_level}
            </div>
            <div style="font-size: 0.8rem; color: #64748B; margin-top: 0.5rem;">
                {risk.total_findings} findings · Score {risk.health_score}/100
            </div>
        </div>
        """,
    )


def render_property_health_dashboard(health) -> None:
    """Render the Property Health Dashboard section."""
    import re

    render_html(
        f"""
        <div class="section-title">🏥 Property Health Dashboard</div>
        """,
    )

    # Row 1: Overall Health + Grade + Key Metrics
    col_h1, col_h2, col_h3 = st.columns([1, 1, 2], gap="medium")

    with col_h1:
        render_health_score_ring(int(health.overall_score), health.overall_grade.value, health.overall_grade.color)

    with col_h2:
        render_html(f"""
            <div style="
                padding: 1.5rem; text-align: center;
                background: {health.overall_grade.bg};
                border: 2px solid {health.overall_grade.color};
                border-radius: 12px; margin-top: 1rem;
            ">
                <div style="font-size: 0.7rem; color: #64748B; text-transform: uppercase;
                            letter-spacing: 0.1em; margin-bottom: 0.75rem;">Overall Grade</div>
                <div style="font-size: 3.5rem; font-weight: 800; color: {health.overall_grade.color}; line-height: 1;">
                    {health.overall_grade.value}
                </div>
                <div style="font-size: 0.8rem; color: #64748B; margin-top: 0.5rem;">
                    {health.overall_score:.0f}/100
                </div>
            </div>
        """)

        risk_colors = {"High": "#EF4444", "Elevated": "#F97316", "Moderate": "#F59E0B", "Low": "#10B981"}
        risk_color = risk_colors.get(health.immediate_risk, "#64748B")
        render_html(f"""
            <div style="
                padding: 1rem; text-align: center; margin-top: 1rem;
                background: {risk_color}15; border: 1px solid {risk_color}40;
                border-radius: 10px;
            ">
                <div style="font-size: 0.7rem; color: #64748B; text-transform: uppercase;
                            letter-spacing: 0.08em; margin-bottom: 0.4rem;">Immediate Risk</div>
                <div style="font-size: 1.25rem; font-weight: 800; color: {risk_color};">
                    {health.immediate_risk}
                </div>
            </div>
        """)

    with col_h3:
        render_html("<div style='font-size: 0.85rem; font-weight: 600; color: #94A3B8; margin-bottom: 0.75rem;'>Key Intelligence Metrics</div>")

        metric_items = [
            ("🏠", "Remaining Healthy Life", f"{health.remaining_life_years:.1f} years", "#3B82F6"),
            ("🔮", "Inspection Confidence", f"{health.inspection_confidence:.0f}%", "#8B5CF6"),
            ("⚡", "Repair Priority Index", f"{health.repair_priority_index:.0f}/100", "#F59E0B"),
            ("📊", "Categories Assessed", f"{len(health.categories)}/10", "#10B981"),
        ]

        for icon, label, value, color in metric_items:
            render_html(f"""
                <div style="
                    display: flex; align-items: center; justify-content: space-between;
                    padding: 0.75rem 1rem; margin-bottom: 0.5rem;
                    background: #1E293B; border: 1px solid #334155; border-radius: 8px;
                ">
                    <div style="display: flex; align-items: center; gap: 0.75rem;">
                        <span style="font-size: 1.1rem;">{icon}</span>
                        <span style="font-size: 0.85rem; color: #94A3B8;">{label}</span>
                    </div>
                    <span style="font-size: 0.95rem; font-weight: 700; color: {color};">{value}</span>
                </div>
            """)

    # Row 2: Category Cards
    render_html("<div style='height: 1rem;'></div>")
    render_html("<div style='font-size: 0.85rem; font-weight: 600; color: #94A3B8; margin-bottom: 0.75rem;'>Category Health Scores</div>")

    cat_cols = st.columns(5, gap="small")
    for i, cat in enumerate(health.categories):
        col = cat_cols[i % 5]
        with col:
            bar_color = cat.grade.color
            bar_width = max(cat.score, 5)
            issues_badge = f"⚠️ {cat.findings_count}" if cat.findings_count > 0 else "✅"
            render_html(f"""
                <div style="
                    background: #1E293B; border: 1px solid #334155; border-radius: 10px;
                    padding: 0.9rem; text-align: center;
                ">
                    <div style="font-size: 0.7rem; color: #64748B; text-transform: uppercase;
                                letter-spacing: 0.05em; margin-bottom: 0.3rem;">
                        {cat.category}
                    </div>
                    <div style="font-size: 1.3rem; font-weight: 800; color: {bar_color};">
                        {cat.score:.0f}
                    </div>
                    <div style="font-size: 0.65rem; color: {bar_color}; font-weight: 600; margin-bottom: 0.5rem;">
                        {cat.grade.value}
                    </div>
                    <div style="
                        background: #0F172A; border-radius: 3px; height: 6px;
                        overflow: hidden; margin-bottom: 0.4rem;
                    ">
                        <div style="
                            background: {bar_color}; height: 100%; width: {bar_width}%;
                            border-radius: 3px; transition: width 1s ease-out;
                        "></div>
                    </div>
                    <div style="font-size: 0.75rem;">{issues_badge}</div>
                </div>
            """)

    # Row 3: Timeline Predictions
    if health.future_predictions:
        render_html("<div style='height: 1rem;'></div>")
        render_html("<div style='font-size: 0.85rem; font-weight: 600; color: #94A3B8; margin-bottom: 0.75rem;'>📈 Damage Progression Forecast</div>")

        pred_cols = st.columns(3, gap="medium")
        period_map = {"3mo": "3 Months", "6mo": "6 Months", "12mo": "12 Months"}
        predictions_data = [
            (period_map.get(period, period), prediction)
            for period, prediction in health.future_predictions.items()
        ]
        for col, (period_label, prediction) in zip(pred_cols, predictions_data):
            with col:
                score_match = re.search(r"Score: (\d+)", prediction)
                score_val = int(score_match.group(1)) if score_match else 0
                score_color = "#10B981" if score_val >= 80 else "#F59E0B" if score_val >= 60 else "#F97316" if score_val >= 40 else "#EF4444"

                render_html(f"""
                    <div style="
                        background: #1E293B; border: 1px solid #334155; border-radius: 10px;
                        padding: 1.25rem; text-align: center;
                    ">
                        <div style="font-size: 0.7rem; color: #64748B; text-transform: uppercase;
                                    letter-spacing: 0.08em; margin-bottom: 0.5rem;">{period_label}</div>
                        <div style="font-size: 1.75rem; font-weight: 800; color: {score_color};">
                            {score_val:.0f}/100
                        </div>
                        <div style="font-size: 0.75rem; color: #64748B; margin-top: 0.4rem; line-height: 1.4;">
                            Forecasted damage progression
                        </div>
                    </div>
                """)

    # Row 4: Health Summary
    if health.health_summary:
        render_html("<div style='height: 1rem;'></div>")
        render_html(f"""
            <div class="card-glass" style="padding: 1.5rem 2rem; border: 1px solid #334155;">
                <div style="font-size: 0.7rem; color: #64748B; text-transform: uppercase;
                            letter-spacing: 0.1em; margin-bottom: 0.75rem;">AI Health Assessment Summary</div>
                <p style="color: #94A3B8; font-size: 0.9rem; line-height: 1.8; margin: 0;">
                    {health.health_summary}
                </p>
            </div>
            """,
        )

    # Row 5: Strengths, Weaknesses, Priority Actions
    col_s, col_w, col_p = st.columns(3, gap="medium")

    with col_s:
        render_html("<div style='font-size: 0.8rem; font-weight: 700; color: #10B981; margin-bottom: 0.6rem;'>💪 Strengths</div>")
        for s in health.strengths[:4]:
            render_html(f"<div style='font-size: 0.8rem; color: #94A3B8; padding: 0.25rem 0;'>• {s}</div>")

    with col_w:
        render_html("<div style='font-size: 0.8rem; font-weight: 700; color: #EF4444; margin-bottom: 0.6rem;'>⚠️ Weaknesses</div>")
        for w in health.weaknesses[:4]:
            render_html(f"<div style='font-size: 0.8rem; color: #94A3B8; padding: 0.25rem 0;'>• {w}</div>")

    with col_p:
        render_html("<div style='font-size: 0.8rem; font-weight: 700; color: #F59E0B; margin-bottom: 0.6rem;'>🔧 Priority Actions</div>")
        for i, a in enumerate(health.priority_actions[:4], 1):
            render_html(f"<div style='font-size: 0.8rem; color: #94A3B8; padding: 0.25rem 0;'>{i}. {a}</div>")