"""Renderers for fused findings, legacy per-image results, and comparison dashboard."""
from __future__ import annotations

from typing import Optional

import streamlit as st

from streamlit_app.ai.comparison_engine import ComparisonReport
from streamlit_app.ai.fusion_engine import FusedInspection
from streamlit_app.ai.health_engine import PropertyHealthReport
from streamlit_app.ai.inspection_engine import InspectionReport
from streamlit_app.report.risk_engine import RiskAssessment
from streamlit_app.utils.constants import (
    BORDER_COLOR, SEVERITY_BG, SEVERITY_COLORS, TEXT_MUTED, TEXT_PRIMARY, TEXT_SECONDARY, WIZARD_STEPS,
)
from streamlit_app.utils.session_manager import (
    SessionKeys, get_inspection_data, get_inspection_step, reset_inspection_flow,
)
from streamlit_app.components.ui_components import (
    inject_custom_css, init_page_config, render_header, render_info_box, render_result_summary_card, render_wizard_stepper,
)


# ── Fused finding card ────────────────────────────────────────────────────────


def render_fused_finding_card(finding, index: int) -> None:
    """Render a single merged finding card.

    Accepts either a FusedFinding dataclass or a plain dict.
    """
    # Normalise: support both FusedFinding objects and plain dicts
    if hasattr(finding, "severity"):
        sev = finding.severity
        sev_color = SEVERITY_COLORS.get(sev, "#64748B")
        sev_bg = SEVERITY_BG.get(sev, "rgba(100, 116, 139, 0.15)")
        confidence = finding.confidence
        damage_pct = finding.damage_pct
        affected = finding.affected_images
        causes = finding.possible_causes
        steps = finding.repair_steps
        professional = finding.recommended_professional
        cost = finding.estimated_cost_range
        urgency = finding.urgency
        tips = finding.prevention_tips
        damage_type = finding.damage_type
    else:
        sev = finding.get("severity", "Medium")
        sev_color = SEVERITY_COLORS.get(sev, "#64748B")
        sev_bg = SEVERITY_BG.get(sev, "rgba(100, 116, 139, 0.15)")
        confidence = finding.get("confidence", 0)
        damage_pct = finding.get("damage_pct", 0.0)
        affected = finding.get("affected_images", [])
        causes = finding.get("possible_causes", [])
        steps = finding.get("repair_steps", [])
        professional = finding.get("recommended_professional", "N/A")
        cost = finding.get("estimated_cost_range", "N/A")
        urgency = finding.get("urgency", "N/A")
        tips = finding.get("prevention_tips", [])
        damage_type = finding.get("damage_type", "Unknown")

    st.markdown(
        f"""
        <div style="
            background: #1E293B; border: 1px solid {BORDER_COLOR}; border-radius: 10px;
            padding: 1.25rem; margin-bottom: 0.75rem;
        ">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.75rem;">
                <span style="font-size: 1.05rem; font-weight: 700; color: {TEXT_PRIMARY};">
                    {damage_type}
                </span>
                <span style="
                    padding: 0.3rem 0.8rem; background: {sev_bg}; color: {sev_color};
                    border-radius: 6px; font-size: 0.75rem; font-weight: 700;
                    text-transform: uppercase; letter-spacing: 0.05em;
                ">{sev}</span>
            </div>

            <div style="display: flex; gap: 1.5rem; margin-bottom: 0.75rem; font-size: 0.8rem; color: {TEXT_MUTED};">
                <span>Confidence: <strong style="color: {TEXT_SECONDARY};">{confidence}%</strong></span>
                <span>Damage: <strong style="color: {TEXT_SECONDARY};">{damage_pct:.1f}%</strong></span>
                <span>In: <strong style="color: {TEXT_SECONDARY};">{', '.join(affected[:3])}</strong></span>
            </div>

            <div style="margin-bottom: 0.5rem;">
                <div style="font-size: 0.75rem; color: {TEXT_MUTED}; text-transform: uppercase;
                            letter-spacing: 0.08em; margin-bottom: 0.25rem;">Possible Causes</div>
                <div style="font-size: 0.85rem; color: {TEXT_SECONDARY};">
                    {', '.join(causes[:3])}
                </div>
            </div>

            <div style="margin-bottom: 0.5rem;">
                <div style="font-size: 0.75rem; color: {TEXT_MUTED}; text-transform: uppercase;
                            letter-spacing: 0.08em; margin-bottom: 0.25rem;">Repair Steps</div>
                <ul style="margin: 0; padding-left: 1.2rem; font-size: 0.85rem; color: {TEXT_SECONDARY};">
                    {"".join(f"<li style='margin-bottom: 0.2rem;'>{s}</li>" for s in steps[:4])}
                </ul>
            </div>

            <div style="display: flex; justify-content: space-between; align-items: center;
                        margin-top: 0.75rem; padding-top: 0.75rem; border-top: 1px solid {BORDER_COLOR};">
                <span style="font-size: 0.8rem; color: {TEXT_MUTED};">{professional}</span>
                <span style="font-size: 0.9rem; font-weight: 700; color: #4F46E5;">{cost}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ── Legacy per-image results ──────────────────────────────────────────────────


def render_legacy_results(reports: list[InspectionReport], inspection_data: dict) -> None:
    """Render per-image results (fallback when fusion is not applied)."""
    # This is the original per-image display — kept as fallback
    render_header(
        title="Inspection Results",
        subtitle="Review your AI-powered inspection findings",
        icon="📊",
    )
    render_wizard_stepper(
        current_step=get_inspection_step(),
        steps=WIZARD_STEPS,
    )
    st.markdown("<div class='mt-4'></div>", unsafe_allow_html=True)

    total_images = len(reports)
    images_with_damage = sum(1 for r in reports if r.damage_percentage > 0.5)
    avg_damage_pct = (
        sum(r.damage_percentage for r in reports) / total_images if total_images > 0 else 0.0
    )
    total_contours = sum(r.contour_count for r in reports)

    health_score = max(0, min(100, round(100 - avg_damage_pct * 10)))

    result_summary = {
        "health_score": health_score,
        "issues_found": images_with_damage,
        "severity": "Medium",
        "estimated_cost_range": "N/A",
        "status": "Completed",
        "inspection_id": inspection_data.get("id", "INS-0000"),
    }
    render_result_summary_card(result_summary)
    st.markdown("<div class='mt-4'></div>", unsafe_allow_html=True)

    # Per-image analysis
    if total_images > 1:
        render_header(
            title=f"Per-Image Analysis ({total_images} images)",
            subtitle=f"{images_with_damage} image{'s' if images_with_damage != 1 else ''} with detected damage",
            icon="Image",
        )

    for idx, report in enumerate(reports):
        render_header(
            title=f"Image {idx + 1}: {report.file_name or f'Image {idx+1}'}",
            subtitle=f"Damage: {report.damage_percentage:.2f}%  |  Regions: {report.contour_count}",
            icon="Image",
            level=2,
        )

        # Image comparison
        st.markdown("Visual Analysis")
        col1, col2 = st.columns(2)
        with col1:
            if report.processed_image is not None:
                st.image(_bgr_to_rgb(report.processed_image), caption="Processed", use_container_width=True)
        with col2:
            if report.overlay_image is not None:
                st.image(_bgr_to_rgb(report.overlay_image), caption="Overlay", use_container_width=True)

        # Metrics
        metric_cols = st.columns(4)
        metrics_data = [
            ("Damage %", f"{report.damage_percentage:.2f}%"),
            ("Damage Area", f"{report.damage_area_px:,} px"),
            ("Regions", str(report.contour_count)),
            ("Largest", f"{report.largest_damage_area_px:,} px"),
        ]
        for col, (label, value) in zip(metric_cols, metrics_data):
            with col:
                st.markdown(
                    f"""
                    <div style="background: rgba(30, 41, 59, 0.5); border-radius: 8px; padding: 0.75rem; text-align: center;">
                        <div style="font-size: 0.7rem; color: #64748B; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.25rem;">{label}</div>
                        <div style="color: #F1F5F9; font-size: 1rem; font-weight: 700;">{value}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        # AI details
        if report.damage_type and report.damage_type != "N/A":
            st.markdown(
                f"""
                <div style="
                    background: #1E293B; border: 1px solid #334155; border-radius: 10px;
                    padding: 1.25rem; margin-top: 1rem;
                ">
                    <div style="font-weight: 700; color: #F1F5F9; margin-bottom: 0.5rem;">
                        {report.damage_type} — {report.severity}
                    </div>
                    <div style="color: #94A3B8; font-size: 0.85rem;">
                        Confidence: {report.confidence}% | Urgency: {report.urgency or 'N/A'}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("<div class='mt-4'></div>", unsafe_allow_html=True)

    # Action buttons
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Save Inspection", type="primary", use_container_width=True):
            render_info_box("Inspection saved!", box_type="success")
    with col2:
        if st.button("Generate Report", type="secondary", use_container_width=True):
            st.session_state.navigate_to = "report_detail"
            st.rerun()
    with col3:
        if st.button("New Inspection", type="secondary", use_container_width=True):
            reset_inspection_flow()
            st.rerun()


# ── Comparison dashboard ───────────────────────────────────────────────────────


def _get_grade_color(grade: str) -> str:
    """Get hex color for a letter grade."""
    colors = {
        "A+": "#10B981", "A": "#34D399", "B+": "#6EE7B7",
        "B": "#FBBF24", "C": "#F97316", "D": "#EF4444",
    }
    return colors.get(grade, "#64748B")


def _get_grade_bg(grade: str) -> str:
    """Get background color for a letter grade."""
    bgs = {
        "A+": "rgba(16, 185, 129, 0.15)", "A": "rgba(52, 211, 153, 0.15)",
        "B+": "rgba(110, 231, 183, 0.15)", "B": "rgba(251, 191, 36, 0.15)",
        "C": "rgba(249, 115, 22, 0.15)", "D": "rgba(239, 68, 68, 0.15)",
    }
    return bgs.get(grade, "rgba(100, 116, 139, 0.15)")


def render_comparison_dashboard(comparison: ComparisonReport) -> None:
    """Render the Inspection Comparison Dashboard."""
    from streamlit_app.ai.comparison_engine import comparison_report_to_dict, rebuild_comparison_report

    st.markdown(
        """
        <div class="section-title">🔄 Inspection Comparison Dashboard</div>
        """,
        unsafe_allow_html=True,
    )

    prev = comparison.previous
    curr = comparison.current

    # ── Row 1: Before vs After Cards ────────────────────────────────────────
    col_prev, col_delta, col_curr = st.columns([1, 1, 1], gap="medium")

    with col_prev:
        st.markdown("<div style='font-size: 0.75rem; font-weight: 600; color: #64748B; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 0.75rem;'>Previous Inspection</div>", unsafe_allow_html=True)
        st.markdown(f"""
            <div class="card-glass" style="padding: 1.25rem; border: 1px solid #334155;">
                <div style="font-size: 0.8rem; color: #94A3B8; margin-bottom: 0.75rem;">
                    📅 {prev.inspection_date or 'Unknown Date'}
                </div>
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                    <div>
                        <div style="font-size: 0.7rem; color: #64748B; text-transform: uppercase; letter-spacing: 0.08em;">Health Score</div>
                        <div style="font-size: 2rem; font-weight: 800; color: #F1F5F9;">{prev.health_score:.0f}</div>
                    </div>
                    <div style="
                        padding: 0.5rem 1rem; background: {_get_grade_bg(prev.grade)};
                        border: 1px solid {_get_grade_color(prev.grade)};
                        border-radius: 8px;
                    ">
                        <span style="font-size: 1.25rem; font-weight: 800; color: {_get_grade_color(prev.grade)};">{prev.grade}</span>
                    </div>
                </div>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem; font-size: 0.8rem;">
                    <div><span style="color: #64748B;">Damage:</span> <span style="color: #F1F5F9;">{prev.total_damage_pct:.1f}%</span></div>
                    <div><span style="color: #64748B;">Findings:</span> <span style="color: #F1F5F9;">{prev.total_findings}</span></div>
                    <div><span style="color: #64748B;">Cost:</span> <span style="color: #F1F5F9;">₹{prev.total_repair_cost:,}</span></div>
                    <div><span style="color: #64748B;">Moisture:</span> <span style="color: #F1F5F9;">{prev.moisture_level}</span></div>
                </div>
                <div style="margin-top: 0.75rem; padding-top: 0.75rem; border-top: 1px solid #334155;">
                    <div style="font-size: 0.7rem; color: #64748B;">Damage Types</div>
                    <div style="font-size: 0.8rem; color: #94A3B8; margin-top: 0.25rem;">
                        {', '.join(prev.damage_types[:5]) if prev.damage_types else 'None detected'}
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

    with col_delta:
        delta = comparison.health_score_delta
        delta_color = "#10B981" if delta > 0 else "#EF4444" if delta < 0 else "#64748B"
        delta_arrow = "↑" if delta > 0 else "↓" if delta < 0 else "→"
        damage_delta = comparison.damage_delta_pct
        damage_delta_color = "#10B981" if damage_delta < 0 else "#EF4444" if damage_delta > 0 else "#64748B"
        damage_delta_arrow = "↓" if damage_delta < 0 else "↑" if damage_delta > 0 else "→"

        trend_colors = {"Improving": "#10B981", "Stable": "#FBBF24", "Deteriorating": "#EF4444"}
        trend_color = trend_colors.get(comparison.risk_trend, "#64748B")

        st.markdown(f"""
            <div class="card-glass" style="padding: 1.25rem; border: 1px solid #334155; text-align: center;">
                <div style="font-size: 0.75rem; font-weight: 600; color: #64748B; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 1rem;">Change</div>

                <div style="margin-bottom: 1.25rem;">
                    <div style="font-size: 0.7rem; color: #64748B; margin-bottom: 0.25rem;">Health Score</div>
                    <div style="font-size: 2rem; font-weight: 800; color: {delta_color};">
                        {delta_arrow} {abs(delta):.0f}
                    </div>
                </div>

                <div style="margin-bottom: 1.25rem;">
                    <div style="font-size: 0.7rem; color: #64748B; margin-bottom: 0.25rem;">Damage Change</div>
                    <div style="font-size: 1.5rem; font-weight: 800; color: {damage_delta_color};">
                        {damage_delta_arrow} {abs(damage_delta):.1f}%
                    </div>
                </div>

                <div style="padding: 0.75rem; background: {trend_color}15; border: 1px solid {trend_color}40; border-radius: 8px;">
                    <div style="font-size: 0.65rem; color: #64748B; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 0.25rem;">Risk Trend</div>
                    <div style="font-size: 1.1rem; font-weight: 800; color: {trend_color};">
                        {comparison.risk_trend}
                    </div>
                </div>

                <div style="margin-top: 1rem; font-size: 0.75rem; color: #64748B;">
                    📅 {comparison.days_between} days between inspections
                </div>
            </div>
        """, unsafe_allow_html=True)

    with col_curr:
        st.markdown("<div style='font-size: 0.75rem; font-weight: 600; color: #64748B; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 0.75rem;'>Current Inspection</div>", unsafe_allow_html=True)
        st.markdown(f"""
            <div class="card-glass" style="padding: 1.25rem; border: 1px solid #4F46E5;">
                <div style="font-size: 0.8rem; color: #94A3B8; margin-bottom: 0.75rem;">
                    📅 {curr.inspection_date or 'Current'}
                </div>
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                    <div>
                        <div style="font-size: 0.7rem; color: #64748B; text-transform: uppercase; letter-spacing: 0.08em;">Health Score</div>
                        <div style="font-size: 2rem; font-weight: 800; color: #F1F5F9;">{curr.health_score:.0f}</div>
                    </div>
                    <div style="
                        padding: 0.5rem 1rem; background: {_get_grade_bg(curr.grade)};
                        border: 1px solid {_get_grade_color(curr.grade)};
                        border-radius: 8px;
                    ">
                        <span style="font-size: 1.25rem; font-weight: 800; color: {_get_grade_color(curr.grade)};">{curr.grade}</span>
                    </div>
                </div>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem; font-size: 0.8rem;">
                    <div><span style="color: #64748B;">Damage:</span> <span style="color: #F1F5F9;">{curr.total_damage_pct:.1f}%</span></div>
                    <div><span style="color: #64748B;">Findings:</span> <span style="color: #F1F5F9;">{curr.total_findings}</span></div>
                    <div><span style="color: #64748B;">Cost:</span> <span style="color: #F1F5F9;">₹{curr.total_repair_cost:,}</span></div>
                    <div><span style="color: #64748B;">Moisture:</span> <span style="color: #F1F5F9;">{curr.moisture_level}</span></div>
                </div>
                <div style="margin-top: 0.75rem; padding-top: 0.75rem; border-top: 1px solid #334155;">
                    <div style="font-size: 0.7rem; color: #64748B;">Damage Types</div>
                    <div style="font-size: 0.8rem; color: #94A3B8; margin-top: 0.25rem;">
                        {', '.join(curr.damage_types[:5]) if curr.damage_types else 'None detected'}
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

    # ── Row 2: Key Metrics Bar ───────────────────────────────────────────────
    st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
    col_m1, col_m2, col_m3, col_m4 = st.columns(4, gap="medium")

    with col_m1:
        imp_color = "#10B981" if comparison.improvement_score >= 70 else "#F59E0B" if comparison.improvement_score >= 40 else "#EF4444"
        st.markdown(f"""
            <div class="card-glass" style="padding: 1rem; text-align: center;">
                <div style="font-size: 0.7rem; color: #64748B; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 0.5rem;">Improvement Score</div>
                <div style="font-size: 1.75rem; font-weight: 800; color: {imp_color};">{comparison.improvement_score:.0f}</div>
                <div style="font-size: 0.7rem; color: #64748B;">/ 100</div>
            </div>
        """, unsafe_allow_html=True)

    with col_m2:
        eff_color = "#10B981" if comparison.repair_effectiveness_pct >= 70 else "#F59E0B" if comparison.repair_effectiveness_pct >= 40 else "#EF4444"
        st.markdown(f"""
            <div class="card-glass" style="padding: 1rem; text-align: center;">
                <div style="font-size: 0.7rem; color: #64748B; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 0.5rem;">Repair Effectiveness</div>
                <div style="font-size: 1.75rem; font-weight: 800; color: {eff_color};">{comparison.repair_effectiveness_pct:.0f}%</div>
            </div>
        """, unsafe_allow_html=True)

    with col_m3:
        growth_color = "#10B981" if comparison.damage_growth_pct <= 0 else "#F59E0B" if comparison.damage_growth_pct <= 20 else "#EF4444"
        growth_arrow = "↓" if comparison.damage_growth_pct < 0 else "↑" if comparison.damage_growth_pct > 0 else "→"
        st.markdown(f"""
            <div class="card-glass" style="padding: 1rem; text-align: center;">
                <div style="font-size: 0.7rem; color: #64748B; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 0.5rem;">Damage Growth</div>
                <div style="font-size: 1.75rem; font-weight: 800; color: {growth_color};">
                    {growth_arrow} {abs(comparison.damage_growth_pct):.0f}%
                </div>
            </div>
        """, unsafe_allow_html=True)

    with col_m4:
        change_badge = f"+{comparison.new_damage_count}/-{comparison.resolved_damage_count}"
        st.markdown(f"""
            <div class="card-glass" style="padding: 1rem; text-align: center;">
                <div style="font-size: 0.7rem; color: #64748B; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 0.5rem;">New / Resolved</div>
                <div style="font-size: 1.5rem; font-weight: 800; color: #F1F5F9;">
                    {change_badge}
                </div>
                <div style="font-size: 0.7rem; color: #64748B; margin-top: 0.25rem;">
                    {comparison.increased_count} increased, {comparison.reduced_count} reduced
                </div>
            </div>
        """, unsafe_allow_html=True)

    # ── Row 3: Change Detection Summary ──────────────────────────────────────
    st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
    st.markdown("<div style='font-size: 0.85rem; font-weight: 600; color: #94A3B8; margin-bottom: 0.75rem;'>Change Detection Summary</div>", unsafe_allow_html=True)

    change_cols = st.columns(5, gap="small")
    change_data = [
        ("🆕", "New Damage", comparison.new_damage_count, "#EF4444", "New findings detected"),
        ("✅", "Resolved", comparison.resolved_damage_count, "#10B981", "Issues fixed"),
        ("⚠️", "Increased", comparison.increased_count, "#F97316", "Worsening issues"),
        ("📉", "Reduced", comparison.reduced_count, "#3B82F6", "Improving issues"),
        ("➡️", "Unchanged", comparison.unchanged_count, "#64748B", "No change"),
    ]

    for col, (icon, label, count, color, desc) in zip(change_cols, change_data):
        with col:
            st.markdown(f"""
                <div class="card-glass" style="padding: 0.9rem; text-align: center; border: 1px solid {color}40;">
                    <div style="font-size: 1.25rem; margin-bottom: 0.3rem;">{icon}</div>
                    <div style="font-size: 1.5rem; font-weight: 800; color: {color};">{count}</div>
                    <div style="font-size: 0.65rem; color: #64748B; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.25rem;">{label}</div>
                    <div style="font-size: 0.7rem; color: #64748B;">{desc}</div>
                </div>
            """, unsafe_allow_html=True)

    # ── Row 4: Comparison Table ──────────────────────────────────────────────
    if comparison.findings:
        st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
        st.markdown("<div style='font-size: 0.85rem; font-weight: 600; color: #94A3B8; margin-bottom: 0.75rem;'>Detailed Comparison</div>", unsafe_allow_html=True)

        table_data = []
        for f in comparison.findings:
            change_emoji = {
                "new": "🆕", "resolved": "✅", "increased": "⚠️",
                "reduced": "📉", "unchanged": "➡️"
            }.get(f.change_type, "➡️")

            sev_prev = f.previous_severity if f.previous_severity != "N/A" else "—"
            sev_curr = f.current_severity if f.current_severity != "N/A" else "—"

            delta_str = f"+{f.delta_pct:.1f}%" if f.delta_pct > 0 else f"{f.delta_pct:.1f}%"

            table_data.append({
                "": change_emoji,
                "Damage Type": f.damage_type,
                "Previous Sev.": sev_prev,
                "Current Sev.": sev_curr,
                "Prev. Damage": f"{f.previous_damage_pct:.1f}%",
                "Current": f"{f.current_damage_pct:.1f}%",
                "Delta": delta_str,
                "Recommendation": f.recommendation,
            })

        st.dataframe(table_data, use_container_width=True, hide_index=True)

    # ── Row 5: Comparison Summary ────────────────────────────────────────────
    if comparison.comparison_summary:
        st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
        st.markdown(
            f"""
            <div class="card-glass" style="padding: 1.5rem 2rem; border: 1px solid #334155;">
                <div style="font-size: 0.7rem; color: #64748B; text-transform: uppercase;
                            letter-spacing: 0.1em; margin-bottom: 0.75rem;">AI Comparison Summary</div>
                <p style="color: #94A3B8; font-size: 0.9rem; line-height: 1.8; margin: 0;">
                    {comparison.comparison_summary}
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
