"""Renderers for fused inspection results (property-level unified view)."""
from __future__ import annotations

import math
import re

import streamlit as st

from streamlit_app.ai.fusion_engine import FusedInspection
from streamlit_app.ai.health_engine import PropertyHealthReport
from streamlit_app.components.ui_components import render_header, render_html, render_result_summary_card
from streamlit_app.report.health import render_health_score_ring, render_risk_badge
from streamlit_app.utils.constants import (
    BORDER_COLOR, TEXT_MUTED, TEXT_PRIMARY, TEXT_SECONDARY,
)
from streamlit_app.views.results.renderers import render_fused_finding_card, render_comparison_dashboard
from streamlit_app.views.results.helpers import _get_grade_color, _get_grade_bg


def render_fused_results(fused: FusedInspection, inspection_data: dict) -> None:
    """Render the full fused inspection results view."""

    # ── Section 1: Overall Property Score ──────────────────────────────────
    render_html(f"""
        <div style="margin-bottom: 1.5rem;">
            <h2 style="margin: 0; display: flex; align-items: center; gap: 0.5rem;">
                Inspection Results
            </h2>
            <p style="color: #64748B; margin: 0.25rem 0 0; font-size: 0.9rem;">
                Unified analysis across {fused.total_images} images — {fused.total_findings} distinct findings
            </p>
        </div>
        """,
    )

    col_score, col_risk = st.columns([2, 1], gap="large")

    with col_score:
        result_summary = {
            "health_score": fused.overall_health_score,
            "issues_found": fused.total_findings,
            "severity": fused.overall_severity,
            "estimated_cost_min": fused.overall_estimated_cost_min,
            "estimated_cost_max": fused.overall_estimated_cost_max,
            "status": "Completed",
            "inspection_id": inspection_data.get("id", "INS-0000"),
        }
        render_result_summary_card(result_summary)

    with col_risk:
        risk = fused.risk_assessment
        if risk:
            render_health_score_ring(fused.overall_health_score, risk.risk_level, risk.risk_color)
            render_html("<div style='height: 1rem;'></div>")
            render_risk_badge(risk)

    # ── Section 2: Image Priority Ranking ──────────────────────────────────
    render_html("<div style='height: 2rem;'></div>")
    render_header(title="Image Priority Ranking", subtitle="Images ranked by damage severity", icon="📊")

    rankings = fused.image_rankings
    if rankings:
        rank_cols = st.columns(min(len(rankings), 3), gap="medium")
        for i, rank in enumerate(rankings):
            col = rank_cols[i % 3]
            with col:
                medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(rank.rank, f"#{rank.rank}")
                from streamlit_app.utils.constants import SEVERITY_COLORS
                sev_color = SEVERITY_COLORS.get(rank.severity, "#64748B")
                render_html(f"""
                    <div style="
                        background: #1E293B; border: 1px solid #334155; border-radius: 10px;
                        padding: 1rem; text-align: center;
                    ">
                        <div style="font-size: 2rem; margin-bottom: 0.5rem;">{medal}</div>
                        <div style="font-size: 0.85rem; font-weight: 600; color: #F1F5F9;
                                    word-break: break-all;">{rank.file_name}</div>
                        <div style="font-size: 0.75rem; color: {sev_color}; margin-top: 0.5rem;
                                    font-weight: 600;">{rank.severity}</div>
                        <div style="font-size: 0.8rem; color: #64748B; margin-top: 0.25rem;">
                            {rank.damage_pct:.1f}% damage
                        </div>
                    </div>
                    """,
                )

    # ── Section 3: Executive Summary ────────────────────────────────────
    render_html("<div style='height: 2rem;'></div>")
    render_header(title="Executive Summary", subtitle="AI-generated inspection overview", icon="📝")

    if fused.executive_summary:
        paragraphs = fused.executive_summary.split(". ")
        for para in paragraphs:
            para = para.strip()
            if para:
                if not para.endswith("."):
                    para += "."
                render_html(f"<p style='color: #94A3B8; font-size: 0.95rem; line-height: 1.8; margin: 0.5rem 0;'>{para}</p>")

    # ── Section 4: Property Summary + Conclusion ────────────────────────
    if fused.property_summary or fused.inspection_conclusion:
        render_html("<div style='height: 1.5rem;'></div>")
        col_a, col_b = st.columns(2, gap="medium")

        with col_a:
            if fused.property_summary:
                render_html(f"""
                    <div style="
                        background: rgba(79, 70, 229, 0.05); border: 1px solid rgba(79, 70, 229, 0.15);
                        border-radius: 10px; padding: 1.25rem;
                    ">
                        <div style="font-size: 0.75rem; color: #64748B; text-transform: uppercase;
                                    letter-spacing: 0.08em; margin-bottom: 0.5rem;">Property Summary</div>
                        <p style="color: #94A3B8; font-size: 0.9rem; line-height: 1.7; margin: 0;">
                            {fused.property_summary}
                        </p>
                    </div>
                    """,
                )

        with col_b:
            if fused.inspection_conclusion:
                sev_color = {
                    "Critical": "#EF4444", "High": "#F97316",
                    "Medium": "#F59E0B", "Low": "#10B981",
                }.get(fused.overall_severity, "#64748B")
                render_html(
                    f"""
                    <div style="
                        background: {sev_color}10; border: 1px solid {sev_color}30;
                        border-radius: 10px; padding: 1.25rem;
                    ">
                        <div style="font-size: 0.75rem; color: {sev_color}; text-transform: uppercase;
                                    letter-spacing: 0.08em; margin-bottom: 0.5rem; font-weight: 700;">
                            Inspection Conclusion
                        </div>
                        <p style="color: #94A3B8; font-size: 0.9rem; line-height: 1.7; margin: 0;">
                            {fused.inspection_conclusion}
                        </p>
                    </div>
                    """,
                )

    # ── Section 5: Merged Findings ─────────────────────────────────────
    render_html("<div style='height: 2rem;'></div>")
    render_header(
        title=f"Merged Findings ({fused.total_findings} distinct damage types)",
        subtitle="Findings deduplicated across all inspected images",
        icon="🔍",
    )

    for i, finding in enumerate(fused.findings):
        with st.container():
            render_html(f"<div style='font-size: 0.8rem; color: #64748B; margin-bottom: 0.25rem;'>Finding {i+1} of {fused.total_findings}</div>")
            render_fused_finding_card(finding, index=i)
            if i < len(fused.findings) - 1:
                render_html("<div style='height: 0.75rem;'></div>")

    # ── Section 6: Combined Cost Estimate ──────────────────────────────
    render_html("<div style='height: 2rem;'></div>")
    cost_min = fused.overall_estimated_cost_min
    cost_max = fused.overall_estimated_cost_max
    render_html(f"""
        <div class="card-glass" style="padding: 1.5rem 2rem; border: 1px solid {BORDER_COLOR};">
            <div style="font-size: 0.7rem; color: {TEXT_MUTED}; text-transform: uppercase;
                        letter-spacing: 0.1em; margin-bottom: 0.5rem;">
                Combined Estimated Repair Cost
            </div>
            <div style="font-size: 2rem; font-weight: 800; color: #4F46E5; line-height: 1;">
                ₹{cost_min:,} — ₹{cost_max:,}
            </div>
            <div style="font-size: 0.8rem; color: {TEXT_MUTED}; margin-top: 0.5rem;">
                Based on {fused.total_findings} finding{'s' if fused.total_findings != 1 else ''} across {fused.total_images} images
            </div>
        </div>
        """,
    )

    # ── Section 7: Overall Repair Timeline ────────────────────────────
    render_html("<div style='height: 2rem;'></div>")
    render_header(title="Repair Timeline", subtitle="Prioritised action plan for all findings", icon="📋")

    if fused.timeline:
        timeline_cols = st.columns(4, gap="medium")
        for entry in fused.timeline:
            count = len(entry.findings)
            bucket = entry.bucket
            color = entry.color
            col = timeline_cols[fused.timeline.index(entry)]
            with col:
                render_html(f"""
                    <div style="
                        background: #1E293B; border: 1px solid #334155; border-radius: 10px;
                        padding: 1.25rem; text-align: center; height: 100%;
                    ">
                        <div style="font-size: 1.5rem; margin-bottom: 0.5rem;">{bucket.split()[0]}</div>
                        <div style="font-size: 0.7rem; color: #64748B; text-transform: uppercase;
                                    letter-spacing: 0.08em; margin-bottom: 0.75rem;">{bucket}</div>
                        <div style="font-size: 1.75rem; font-weight: 800; color: {color};">
                            {count}
                        </div>
                        <div style="font-size: 0.75rem; color: #64748B;">finding{'s' if count != 1 else ''}</div>
                    </div>
                    """,
                )

    # ── Section 8: Maintenance Tips ───────────────────────────────────
    if fused.maintenance_tips:
        render_html("<div style='height: 2rem;'></div>")
        render_header(title="Maintenance Tips", subtitle="Preventive measures based on all detected issues", icon="💡")

        tip_cols = st.columns(2, gap="medium")
        for i, tip in enumerate(fused.maintenance_tips):
            col = tip_cols[i % 2]
            with col:
                render_html(f"""
                    <div style="
                        display: flex; align-items: flex-start; gap: 0.75rem;
                        padding: 0.75rem 1rem; margin-bottom: 0.5rem;
                        background: rgba(16, 185, 129, 0.05);
                        border: 1px solid rgba(16, 185, 129, 0.15);
                        border-radius: 8px;
                    ">
                        <span style="color: #10B981; font-size: 1rem; flex-shrink: 0;">✓</span>
                        <span style="color: #94A3B8; font-size: 0.85rem; line-height: 1.5;">{tip}</span>
                    </div>
                    """,
                )

    # ── Section 9: Professional Measurements ──────────────────────────
    render_html("<div style='height: 2rem;'></div>")
    render_header(title="Professional Measurements", subtitle="Detailed measurement analysis of all damage regions", icon="📏")

    col_m1, col_m2, col_m3 = st.columns(3, gap="medium")

    with col_m1:
        render_html(f"""
            <div class="card-glass" style="padding: 1rem; text-align: center;">
                <div style="font-size: 0.7rem; color: #64748B; text-transform: uppercase;
                            letter-spacing: 0.08em; margin-bottom: 0.5rem;">Total Repair Area</div>
                <div style="font-size: 1.5rem; font-weight: 800; color: #F97316;">
                    {fused.total_repair_area_px:,} <span style="font-size: 0.8rem; font-weight: 400;">px</span>
                </div>
            </div>
        """)

    with col_m2:
        render_html(f"""
            <div class="card-glass" style="padding: 1rem; text-align: center;">
                <div style="font-size: 0.7rem; color: #64748B; text-transform: uppercase;
                            letter-spacing: 0.08em; margin-bottom: 0.5rem;">Average Crack Width</div>
                <div style="font-size: 1.5rem; font-weight: 800; color: #EF4444;">
                    {fused.avg_crack_width_px:.1f} <span style="font-size: 0.8rem; font-weight: 400;">px</span>
                </div>
            </div>
        """)

    with col_m3:
        repair_area = fused.total_repair_area_px
        damage_pct = fused.overall_damage_pct
        render_html(f"""
            <div class="card-glass" style="padding: 1rem; text-align: center;">
                <div style="font-size: 0.7rem; color: #64748B; text-transform: uppercase;
                            letter-spacing: 0.08em; margin-bottom: 0.5rem;">Damage Coverage</div>
                <div style="font-size: 1.5rem; font-weight: 800; color: #F59E0B;">
                    {damage_pct:.1f}%
                </div>
            </div>
        """)

    # ── Section 10: Property Health Dashboard ──────────────────────────
    health = fused.health_report if hasattr(fused, 'health_report') and fused.health_report else None
    if health:
        _render_health_dashboard(health)

    # ── Action buttons ──────────────────────────────────────────────────
    from streamlit_app.components.ui_components import render_info_box
    from streamlit_app.database.repository import persist_full_inspection
    from streamlit_app.utils.session_manager import (
        SessionKeys,
        get_property_data,
        reset_inspection_flow,
    )
    render_html("<div style='height: 2rem;'></div>")
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("Save Inspection", type="primary", use_container_width=True):
            try:
                prop_data = get_property_data() or {}
                image_rankings = [
                    {
                        "file_name": r.file_name if hasattr(r, 'file_name') else r.get("file_name", ""),
                        "damage_pct": r.damage_pct if hasattr(r, 'damage_pct') else r.get("damage_pct", 0.0),
                        "severity": r.severity if hasattr(r, 'severity') else r.get("severity", ""),
                        "damage_type": r.damage_type if hasattr(r, 'damage_type') else r.get("damage_type", ""),
                        "confidence": r.confidence if hasattr(r, 'confidence') else r.get("confidence", 0.0),
                    }
                    for r in fused.image_rankings
                ]
                persist_full_inspection(
                    inspection_data=inspection_data,
                    property_data=prop_data,
                    image_rankings=image_rankings,
                )
                render_info_box(
                    f"Inspection saved successfully! (ID: {inspection_data.get('id', 'N/A')})",
                    box_type="success",
                )
                st.session_state[SessionKeys.INSPECTION_DATA]["status"] = "Completed"
            except Exception as exc:
                render_info_box(f"Save failed: {exc}", box_type="error")

    with col2:
        if st.button("Generate Report", type="secondary", use_container_width=True):
            st.session_state[SessionKeys.VIEW_INSPECTION_ID] = inspection_data.get("id", "")
            st.session_state[SessionKeys.CURRENT_PAGE] = "reports"
            st.rerun()

    with col3:
        if st.button("New Inspection", type="secondary", use_container_width=True):
            reset_inspection_flow()
            st.rerun()

    # ── Section 11: Inspection Comparison Dashboard ─────────────────────
    comparison = getattr(fused, 'comparison_report', None)
    if comparison:
        render_html("<div style='height: 2rem;'></div>")
        render_comparison_dashboard(comparison)


def _render_radar_chart(categories: list) -> None:
    """Render a CSS-based radar/spider chart for category health scores."""
    if not categories:
        return

    # Build radar chart HTML using SVG polygon
    n = len(categories)
    cx, cy = 150, 150
    radius = 100
    angle_step = 360 / n
    start_angle = -90

    # Build polygon points for the filled area
    points = []
    for i, cat in enumerate(categories):
        angle = start_angle + (i * angle_step)
        rad = math.radians(angle)
        score_radius = radius * (cat.score / 100.0)
        x = cx + score_radius * math.cos(rad)
        y = cy + score_radius * math.sin(rad)
        points.append(f"{x:.1f},{y:.1f}")

    # Build outer polygon points (100%)
    outer_points = []
    for i in range(n):
        angle = start_angle + (i * angle_step)
        rad = math.radians(angle)
        x = cx + radius * math.cos(rad)
        y = cy + radius * math.sin(rad)
        outer_points.append(f"{x:.1f},{y:.1f}")

    # Build axis lines and labels
    axes = []
    labels = []
    for i, cat in enumerate(categories):
        angle = start_angle + (i * angle_step)
        rad = math.radians(angle)
        x = cx + radius * math.cos(rad)
        y = cy + radius * math.sin(rad)
        axes.append(f"<line x1='{cx}' y1='{cy}' x2='{x:.1f}' y2='{y:.1f}' stroke='#334155' stroke-width='1'/>")
        # Label position
        lx = cx + (radius + 25) * math.cos(rad)
        ly = cy + (radius + 25) * math.sin(rad)
        label_text = cat.category
        color = cat.grade.color
        labels.append(
            f"<text x='{lx:.1f}' y='{ly:.1f}' text-anchor='middle' "
            f"dominant-baseline='middle' fill='{color}' font-size='9' font-weight='600'>{label_text}</text>"
        )

    # Concentric circles (grid)
    grid_circles = []
    for r in [25, 50, 75, 100]:
        grid_circles.append(f"<circle cx='{cx}' cy='{cy}' r='{r}' fill='none' stroke='#334155' stroke-width='0.5' opacity='0.5'/>")

    score_color = "#4F46E5" if sum(c.score for c in categories) / len(categories) >= 70 else "#F59E0B"
    points_str = " ".join(points)
    outer_str = " ".join(outer_points)

    svg = f"""
    <div style="display: flex; justify-content: center; margin: 0.5rem 0;">
        <svg width="300" height="300" viewBox="0 0 300 300">
            <!-- Grid circles -->
            {''.join(grid_circles)}
            <!-- Outer polygon -->
            <polygon points="{outer_str}" fill="none" stroke="#334155" stroke-width="1" opacity="0.5"/>
            <!-- Data polygon -->
            <polygon points="{points_str}" fill="{score_color}30" stroke="{score_color}" stroke-width="2"/>
            <!-- Center dot -->
            <circle cx="{cx}" cy="{cy}" r="3" fill="{score_color}"/>
            <!-- Axes -->
            {''.join(axes)}
            <!-- Labels -->
            {''.join(labels)}
        </svg>
    </div>
    """

    render_html(svg)


def _render_health_dashboard(health: PropertyHealthReport) -> None:
    """Render the full property health dashboard section."""
    render_html("<div style='height: 2rem;'></div>")
    render_header(
        title="Property Health Dashboard",
        subtitle="Comprehensive property health assessment",
        icon="🏥"
    )

    # Row 1: Overall Health Ring + Grade + Key Metrics
    col_health1, col_health2, col_health3 = st.columns([1, 1, 2], gap="medium")

    with col_health1:
        # Health Score Ring
        render_health_score_ring(int(health.overall_score), health.overall_grade.value, health.overall_grade.color)

    with col_health2:
        # Grade Badge
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

        # Immediate Risk
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

    with col_health3:
        # Key Metrics Grid
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

    # Row 2: Category Cards with Progress Bars
    render_html("<div style='height: 1.5rem;'></div>")
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

    # Row 3: Radar Chart (HTML/CSS based)
    render_html("<div style='height: 1.5rem;'></div>")
    _render_radar_chart(health.categories)

    # Row 4: Timeline Predictions
    render_html("<div style='height: 1.5rem;'></div>")
    render_html("<div style='font-size: 0.85rem; font-weight: 600; color: #94A3B8; margin-bottom: 0.75rem;'>📈 Damage Progression Forecast</div>")

    if health.future_predictions:
        pred_cols = st.columns(3, gap="medium")
        for col, (period, prediction) in zip(pred_cols, health.future_predictions.items()):
            with col:
                period_label = {"3mo": "3 Months", "6mo": "6 Months", "12mo": "12 Months"}.get(period, period)
                # Extract score from prediction text
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
                            {score_val}/100
                        </div>
                        <div style="font-size: 0.75rem; color: #64748B; margin-top: 0.4rem; line-height: 1.4;">
                            {prediction.split('—')[-1].strip() if '—' in prediction else prediction}
                        </div>
                    </div>
                """)

    # Row 5: Health Summary
    if health.health_summary:
        render_html("<div style='height: 1.5rem;'></div>")
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

    # Row 6: Strengths, Weaknesses, Priority Actions (3 columns)
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
