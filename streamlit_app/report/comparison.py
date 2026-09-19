"""Comparison section renderer for the report module."""
from __future__ import annotations

import streamlit as st

from streamlit_app.components.ui_components import render_html


def render_comparison_section(comparison) -> None:
    """Render the Inspection Comparison section."""
    from streamlit_app.utils.constants import TEXT_MUTED, BORDER_COLOR

    render_html("<div class='section-title'>📊 Inspection Comparison</div>")
    render_html(f"<p style='color: {TEXT_MUTED}; font-size: 0.85rem; margin: 0.25rem 0 1rem;'>"
                f"Comparing <strong>{comparison.current.inspection_id}</strong> (current) against "
                f"<strong>{comparison.previous.inspection_id}</strong> (previous)</p>")

    # ── Row 1: Score Delta + Grade + Risk Trend + Improvement Score
    col_a, col_b, col_c, col_d = st.columns(4, gap="medium")

    with col_a:
        delta = comparison.health_score_delta
        arrow = "↑" if delta > 0 else ("↓" if delta < 0 else "→")
        delta_color = "#10B981" if delta > 0 else ("#EF4444" if delta < 0 else "#64748B")
        delta_bg = delta_color + "15" if delta != 0 else BORDER_COLOR + "30"
        render_html(f"""
            <div style="
                padding: 1.25rem; text-align: center;
                background: {delta_bg}; border: 1px solid {delta_color}40;
                border-radius: 12px;
            ">
                <div style="font-size: 0.7rem; color: #64748B; text-transform: uppercase;
                            letter-spacing: 0.08em; margin-bottom: 0.5rem;">Health Score Change</div>
                <div style="font-size: 2rem; font-weight: 800; color: {delta_color};">
                    {arrow} {abs(delta):.0f}
                </div>
                <div style="font-size: 0.75rem; color: {TEXT_MUTED}; margin-top: 0.25rem;">
                    {comparison.previous.health_score:.0f} → {comparison.current.health_score:.0f}
                </div>
            </div>
        """)

    with col_b:
        grade_prev = comparison.previous_grade
        grade_curr = comparison.current_grade
        grade_changed = comparison.grade_changed
        render_html(f"""
            <div style="
                padding: 1.25rem; text-align: center;
                background: #F8FAFC; border: 1px solid {BORDER_COLOR};
                border-radius: 12px;
            ">
                <div style="font-size: 0.7rem; color: #64748B; text-transform: uppercase;
                            letter-spacing: 0.08em; margin-bottom: 0.5rem;">Grade Change</div>
                <div style="font-size: 2rem; font-weight: 800; color: #3B82F6;">
                    {grade_prev} → {grade_curr}
                </div>
                <div style="font-size: 0.75rem; color: {TEXT_MUTED}; margin-top: 0.25rem;">
                    {"⬆ Grade Changed" if grade_changed else "Grade Unchanged"}
                </div>
            </div>
        """)

    with col_c:
        trend = comparison.risk_trend
        trend_colors = {"Improving": "#10B981", "Stable": "#3B82F6", "Declining": "#EF4444", "Significant Decline": "#DC2626"}
        trend_color = trend_colors.get(trend, "#64748B")
        render_html(f"""
            <div style="
                padding: 1.25rem; text-align: center;
                background: {trend_color}15; border: 1px solid {trend_color}40;
                border-radius: 12px;
            ">
                <div style="font-size: 0.7rem; color: #64748B; text-transform: uppercase;
                            letter-spacing: 0.08em; margin-bottom: 0.5rem;">Risk Trend</div>
                <div style="font-size: 1.5rem; font-weight: 800; color: {trend_color};">
                    {trend}
                </div>
                <div style="font-size: 0.75rem; color: {TEXT_MUTED}; margin-top: 0.25rem;">
                    Based on score & damage changes
                </div>
            </div>
        """)

    with col_d:
        imp_score = comparison.improvement_score
        imp_color = "#10B981" if imp_score >= 80 else ("#F59E0B" if imp_score >= 50 else "#EF4444")
        render_html(f"""
            <div style="
                padding: 1.25rem; text-align: center;
                background: {imp_color}15; border: 1px solid {imp_color}40;
                border-radius: 12px;
            ">
                <div style="font-size: 0.7rem; color: #64748B; text-transform: uppercase;
                            letter-spacing: 0.08em; margin-bottom: 0.5rem;">Improvement Score</div>
                <div style="font-size: 2rem; font-weight: 800; color: {imp_color};">
                    {imp_score:.0f}%
                </div>
                <div style="font-size: 0.75rem; color: {TEXT_MUTED}; margin-top: 0.25rem;">
                    Composite of all metrics
                </div>
            </div>
        """)

    # ── Row 2: Cost Change + Time Between Inspections
    col_e, col_f, col_g = st.columns(3, gap="medium")

    with col_e:
        cost_delta = comparison.estimated_repair_cost_delta
        cost_arrow = "↓" if cost_delta < 0 else ("↑" if cost_delta > 0 else "→")
        cost_color = "#10B981" if cost_delta < 0 else ("#EF4444" if cost_delta > 0 else "#64748B")
        cost_bg = cost_color + "15" if cost_delta != 0 else BORDER_COLOR + "30"
        render_html(f"""
            <div style="
                padding: 1.25rem; text-align: center;
                background: {cost_bg}; border: 1px solid {cost_color}40;
                border-radius: 12px;
            ">
                <div style="font-size: 0.7rem; color: #64748B; text-transform: uppercase;
                            letter-spacing: 0.08em; margin-bottom: 0.5rem;">Est. Repair Cost</div>
                <div style="font-size: 1.5rem; font-weight: 800; color: {cost_color};">
                    {cost_arrow} ₹{abs(cost_delta):,.0f}
                </div>
                <div style="font-size: 0.75rem; color: {TEXT_MUTED}; margin-top: 0.25rem;">
                    {comparison.previous.total_repair_cost:,.0f} → {comparison.current.total_repair_cost:,.0f}
                </div>
            </div>
        """)

    with col_f:
        new_count = comparison.new_damage_count
        resolved_count = comparison.resolved_damage_count
        net_color = "#10B981" if resolved_count >= new_count else "#EF4444"
        render_html(f"""
            <div style="
                padding: 1.25rem; text-align: center;
                background: #F8FAFC; border: 1px solid {BORDER_COLOR};
                border-radius: 12px;
            ">
                <div style="font-size: 0.7rem; color: #64748B; text-transform: uppercase;
                            letter-spacing: 0.08em; margin-bottom: 0.5rem;">Damage Changes</div>
                <div style="font-size: 1.5rem; font-weight: 800; color: {net_color};">
                    +{new_count} / -{resolved_count}
                </div>
                <div style="font-size: 0.75rem; color: {TEXT_MUTED}; margin-top: 0.25rem;">
                    New / Resolved damage types
                </div>
            </div>
        """)

    with col_g:
        days = comparison.days_between_inspections
        render_html(f"""
            <div style="
                padding: 1.25rem; text-align: center;
                background: #F8FAFC; border: 1px solid {BORDER_COLOR};
                border-radius: 12px;
            ">
                <div style="font-size: 0.7rem; color: #64748B; text-transform: uppercase;
                            letter-spacing: 0.08em; margin-bottom: 0.5rem;">Time Between</div>
                <div style="font-size: 2rem; font-weight: 800; color: #3B82F6;">
                    {days}
                </div>
                <div style="font-size: 0.75rem; color: {TEXT_MUTED}; margin-top: 0.25rem;">
                    days since last inspection
                </div>
            </div>
        """)

    # ── Findings Breakdown
    if comparison.findings:
        render_html(f"<div style='height: 1.5rem;'></div>")
        render_html(f"<div style='font-size: 0.9rem; font-weight: 600; color: #334155; margin-bottom: 0.75rem;'>"
                    f"📋 Detailed Change Breakdown ({len(comparison.findings)} changes)</div>")

        change_icons = {
            "new": "🆕", "resolved": "✅", "increased": "📈",
            "reduced": "📉", "unchanged": "➡", "grade_changed": "🏆"
        }
        change_colors = {
            "new": "#EF4444", "resolved": "#10B981", "increased": "#F97316",
            "reduced": "#3B82F6", "unchanged": "#64748B", "grade_changed": "#8B5CF6"
        }
        change_labels = {
            "new": "New Damage", "resolved": "Resolved", "increased": "Worsened",
            "reduced": "Improved", "unchanged": "No Change", "grade_changed": "Grade Change"
        }

        for finding in comparison.findings:
            icon = change_icons.get(finding.change_type, "•")
            color = change_colors.get(finding.change_type, "#64748B")
            label = change_labels.get(finding.change_type, finding.change_type)
            render_html(f"""
                <div style="
                    padding: 0.75rem 1rem; margin-bottom: 0.5rem;
                    background: {color}08; border-left: 3px solid {color};
                    border-radius: 0 8px 8px 0; display: flex; align-items: center; gap: 0.75rem;
                ">
                    <span style="font-size: 1.1rem;">{icon}</span>
                    <div>
                        <div style="font-weight: 600; color: #1E293B; font-size: 0.9rem;">
                            {finding.category} — <span style="color: {color};">{label}</span>
                        </div>
                        <div style="font-size: 0.8rem; color: {TEXT_MUTED};">
                            {finding.previous_status} → {finding.current_status}
                            {" | Impact: " + finding.impact if finding.impact else ""}
                        </div>
                    </div>
                </div>
            """)

    # ── Summary
    if comparison.comparison_summary:
        render_html(f"<div style='height: 1rem;'></div>")
        render_html(f"<div style='font-size: 0.85rem; color: #64748B; font-style: italic; "
                    f"padding: 0.75rem; background: #F8FAFC; border-radius: 8px; border: 1px solid {BORDER_COLOR};'>"
                    f"{comparison.comparison_summary}</div>")