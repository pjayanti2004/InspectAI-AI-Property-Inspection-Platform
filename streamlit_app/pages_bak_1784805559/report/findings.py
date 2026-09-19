"""Damage Findings renderer for the report page.

Includes the damage findings list, repair plan, recommendations,
and repair timeline — all related to the inspection findings.
"""
from __future__ import annotations

import streamlit as st

from streamlit_app.report.report_builder import _render_findings_section
from streamlit_app.utils.constants import (
    BORDER_COLOR, TEXT_MUTED, TEXT_PRIMARY, SEVERITY_COLORS,
)
from streamlit_app.pages.report.helpers import (
    avg_cost, sev_color, sev_bg, dicts_to_finding_records,
)
from streamlit_app.pages.report.page import (
    CLR_LIGHT_BG,
)


# ── Findings ─────────────────────────────────────────────────────────────────

def render_findings(data: dict) -> None:
    """Render the Damage Findings section."""
    st.markdown(
        """
        <div class="section-title">🔍 Damage Findings</div>
        """,
        unsafe_allow_html=True,
    )

    findings = data.get("findings", [])
    if not findings:
        st.info("No damage findings recorded for this inspection.")
        return

    # Severity count badges
    sev_counts: dict[str, int] = {}
    for f in findings:
        sev = f.get("severity", "Medium") if isinstance(f, dict) else getattr(f, "severity", "Medium")
        sev_counts[sev] = sev_counts.get(sev, 0) + 1

    badge_html = "".join(
        f"""<span style="background: {sev_color(s)}; color: white; padding: 0.2rem 0.6rem;
            border-radius: 4px; font-size: 0.75rem; font-weight: 600; margin-right: 0.4rem;">
            {s}: {sev_counts.get(s, 0)}</span>"""
        for s in ["Critical", "High", "Medium", "Low"] if sev_counts.get(s, 0) > 0
    )
    st.markdown(f"<div style='display: flex; gap: 0.3rem; margin-bottom: 1rem;'>{badge_html}</div>",
                unsafe_allow_html=True)

    # Use the report_builder's finding renderer via FindingRecord conversion
    finding_records = dicts_to_finding_records(findings)
    if finding_records:
        _render_findings_section(finding_records)
    else:
        _render_findings_html(findings)


def _render_findings_html(findings: list) -> None:
    """Pure-HTML fallback findings display."""
    rows = []
    for f in findings:
        if not isinstance(f, dict):
            continue
        sev         = f.get("severity", "Medium")
        sev_color_v = sev_color(sev)
        damage_type = f.get("damage_type", "N/A").replace("_", " ").title()
        source      = f.get("file_name", "—")[:22]
        confidence  = f"{f.get('confidence', 0)}%"
        steps       = "; ".join(f.get("repair_steps", [])[:2]) or "—"

        rows.append(
            f"""
            <div style="
                display: flex; align-items: center; gap: 0.75rem;
                padding: 0.65rem 1rem; margin-bottom: 0.35rem;
                background: #1E293B; border: 1px solid {BORDER_COLOR}; border-radius: 8px;
            ">
                <div style="flex: 0 0 15%; font-weight: 600; color: {TEXT_PRIMARY}; font-size: 0.85rem;">
                    {damage_type}
                </div>
                <div style="flex: 0 0 15%; color: {TEXT_MUTED}; font-size: 0.8rem;">{source}</div>
                <div style="flex: 0 0 10%;">
                    <span style="background: {sev_color_v}; color: white; padding: 0.15rem 0.5rem;
                                 border-radius: 4px; font-size: 0.7rem; font-weight: 600;">
                        {sev.upper()}
                    </span>
                </div>
                <div style="flex: 0 0 10%; color: {TEXT_PRIMARY}; font-size: 0.85rem;">{confidence}</div>
                <div style="flex: 1; color: {TEXT_MUTED}; font-size: 0.8rem;">{steps}</div>
            </div>
            """
        )

    header = """
        <div style="display: flex; gap: 0.75rem; padding: 0.5rem 1rem; margin-bottom: 0.25rem;
                    font-size: 0.7rem; color: #64748B; text-transform: uppercase; letter-spacing: 0.05em;">
            <div style="flex: 0 0 15%;">Type</div>
            <div style="flex: 0 0 15%;">Source</div>
            <div style="flex: 0 0 10%;">Severity</div>
            <div style="flex: 0 0 10%;">Confidence</div>
            <div style="flex: 1;">Repair Steps</div>
        </div>
        <hr style="border: none; border-top: 1px solid {border}; margin: 0 0 0.5rem;">
    """.format(border=BORDER_COLOR)

    st.markdown(header, unsafe_allow_html=True)
    st.markdown("".join(rows), unsafe_allow_html=True)


# ── Repair Plan ───────────────────────────────────────────────────────────────

def render_repair_plan(data: dict) -> None:
    """Repair plan with cost estimate and per-finding repair steps."""
    st.markdown(
        """
        <div class="section-title">🔧 Repair Plan & Recommendations</div>
        """,
        unsafe_allow_html=True,
    )

    findings = data.get("findings", [])
    if not findings:
        st.info("No repair recommendations available.")
        return

    est_min = data.get("overall_estimated_cost_min", 0)
    est_max = data.get("overall_estimated_cost_max", 0)
    avg     = avg_cost(est_min, est_max)

    st.markdown(
        f"""
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-bottom: 1rem;">
            <div style="padding: 0.75rem; text-align: center; background: {CLR_LIGHT_BG};
                        border: 1px solid {BORDER_COLOR}; border-radius: 8px;">
                <div style="font-size: 0.7rem; color: #64748B; text-transform: uppercase;
                            letter-spacing: 0.06em; margin-bottom: 0.3rem;">Estimated Cost Range</div>
                <div style="font-size: 1.1rem; font-weight: 700; color: {TEXT_PRIMARY};">
                    ₹{est_min:,} – ₹{est_max:,}
                </div>
            </div>
            <div style="padding: 0.75rem; text-align: center; background: {CLR_LIGHT_BG};
                        border: 1px solid {BORDER_COLOR}; border-radius: 8px;">
                <div style="font-size: 0.7rem; color: #64748B; text-transform: uppercase;
                            letter-spacing: 0.06em; margin-bottom: 0.3rem;">Average Estimate</div>
                <div style="font-size: 1.1rem; font-weight: 700; color: {TEXT_PRIMARY};">
                    ₹{avg:,}
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    for i, f in enumerate(findings, 1):
        if not isinstance(f, dict):
            continue
        severity    = f.get("severity", "Medium")
        damage_type = f.get("damage_type", "N/A").replace("_", " ").title()
        sev_color_v = sev_color(severity)
        steps       = f.get("repair_steps", [])
        causes      = f.get("possible_causes", [])
        professional = f.get("recommended_professional", "N/A")
        prevention  = f.get("prevention_tips", [])

        st.markdown(
            f"""
            <div style="margin-bottom: 0.75rem;">
                <div style="display: flex; align-items: center; gap: 0.75rem; margin-bottom: 0.5rem;">
                    <span style="font-size: 1rem; font-weight: 700; color: {TEXT_PRIMARY};">
                        {i}. {damage_type}
                    </span>
                    <span style="background: {sev_color_v}; color: white; padding: 0.15rem 0.5rem;
                                 border-radius: 4px; font-size: 0.7rem; font-weight: 600;">
                        {severity.upper()}
                    </span>
                </div>
            """,
            unsafe_allow_html=True,
        )

        if causes:
            st.markdown(
                f"<div style='font-size: 0.8rem; color: {TEXT_MUTED}; margin-bottom: 0.25rem;'>"
                f"<b>Possible Causes:</b> {', '.join(causes)}</div>",
                unsafe_allow_html=True,
            )
        if steps:
            step_html = "".join(
                f"<div style='font-size: 0.85rem; color: #94A3B8; padding: 0.15rem 0;'>• {s}</div>"
                for s in steps[:4]
            )
            st.markdown(
                f"<div style='font-size: 0.8rem; color: {TEXT_MUTED}; margin-bottom: 0.25rem;'>"
                f"<b>Repair Steps:</b></div>{step_html}",
                unsafe_allow_html=True,
            )
        if professional and professional != "N/A":
            st.markdown(
                f"<div style='font-size: 0.8rem; color: {TEXT_MUTED}; margin-bottom: 0.25rem;'>"
                f"<b>Professional:</b> {professional}</div>",
                unsafe_allow_html=True,
            )
        if prevention:
            st.markdown(
                f"<div style='font-size: 0.8rem; color: {TEXT_MUTED}; margin-bottom: 0.25rem;'>"
                f"<b>Prevention:</b> {'; '.join(prevention[:2])}</div>",
                unsafe_allow_html=True,
            )

        st.markdown("</div>", unsafe_allow_html=True)


# ── Recommendations ───────────────────────────────────────────────────────────

def render_recommendations(data: dict) -> None:
    """Recommendations: maintenance tips, immediate actions, professionals, prevention tips."""
    st.markdown(
        """
        <div class="section-title">💡 Recommendations</div>
        """,
        unsafe_allow_html=True,
    )

    findings         = data.get("findings", [])
    maintenance_tips = data.get("maintenance_tips", [])

    col1, col2 = st.columns(2, gap="medium")

    with col1:
        if maintenance_tips:
            st.markdown(
                """
                <div style="font-size: 0.85rem; font-weight: 700; color: #10B981; margin-bottom: 0.75rem;">
                    🛡️ Maintenance Tips
                </div>
                """,
                unsafe_allow_html=True,
            )
            for tip in maintenance_tips[:6]:
                st.markdown(
                    f"<div style='font-size: 0.85rem; color: #94A3B8; padding: 0.25rem 0;'>• {tip}</div>",
                    unsafe_allow_html=True,
                )

        critical = [f for f in findings if isinstance(f, dict) and f.get("severity") == "Critical"]
        if critical:
            st.markdown(
                """
                <div style="font-size: 0.85rem; font-weight: 700; color: #EF4444; margin: 1.25rem 0 0.75rem;">
                    🚨 Immediate Actions Required
                </div>
                """,
                unsafe_allow_html=True,
            )
            for f in critical[:3]:
                for step in f.get("repair_steps", [])[:2]:
                    st.markdown(
                        f"<div style='font-size: 0.85rem; color: #94A3B8; padding: 0.25rem 0;'>• {step}</div>",
                        unsafe_allow_html=True,
                    )

    with col2:
        professionals = set()
        for f in findings:
            if isinstance(f, dict):
                prof = f.get("recommended_professional", "")
                if prof and prof != "N/A":
                    professionals.add(prof)

        if professionals:
            st.markdown(
                """
                <div style="font-size: 0.85rem; font-weight: 700; color: #F59E0B; margin-bottom: 0.75rem;">
                    👷 Recommended Professionals
                </div>
                """,
                unsafe_allow_html=True,
            )
            for prof in professionals:
                st.markdown(
                    f"<div style='font-size: 0.85rem; color: #94A3B8; padding: 0.25rem 0;'>• {prof}</div>",
                    unsafe_allow_html=True,
                )

        all_prevention = []
        for f in findings:
            if isinstance(f, dict):
                all_prevention.extend(f.get("prevention_tips", []))
        if all_prevention:
            st.markdown(
                """
                <div style="font-size: 0.85rem; font-weight: 700; color: #06B6D4; margin: 1.25rem 0 0.75rem;">
                    🛡️ Prevention Tips
                </div>
                """,
                unsafe_allow_html=True,
            )
            for tip in list(set(all_prevention))[:5]:
                st.markdown(
                    f"<div style='font-size: 0.85rem; color: #94A3B8; padding: 0.25rem 0;'>• {tip}</div>",
                    unsafe_allow_html=True,
                )


# ── Timeline ──────────────────────────────────────────────────────────────────

def render_timeline(data: dict) -> None:
    """Repair timeline section."""
    st.markdown(
        """
        <div class="section-title">📅 Repair Timeline</div>
        """,
        unsafe_allow_html=True,
    )

    timeline = data.get("timeline", [])
    if not timeline:
        st.info("No timeline data available for this report.")
        return

    for entry in timeline:
        if isinstance(entry, dict):
            bucket  = entry.get("bucket", entry.get("phase", ""))
            actions = entry.get("actions", [])
            desc    = entry.get("description", "")
        else:
            bucket  = getattr(entry, "bucket", getattr(entry, "phase", ""))
            actions = getattr(entry, "actions", [])
            desc    = getattr(entry, "description", "")

        action_str = "; ".join(actions[:2]) if actions else desc or "—"

        st.markdown(
            f"""
            <div style="
                display: flex; align-items: flex-start; gap: 1rem;
                padding: 0.75rem 1rem; margin-bottom: 0.5rem;
                background: #1E293B; border: 1px solid {BORDER_COLOR}; border-radius: 8px;
            ">
                <div style="
                    flex: 0 0 22%; font-weight: 700; color: #3B82F6;
                    font-size: 0.85rem; padding-top: 0.1rem;
                ">{bucket}</div>
                <div style="flex: 1; color: {TEXT_MUTED}; font-size: 0.85rem;">{action_str}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


__all__ = [
    "render_findings",
    "render_repair_plan",
    "render_recommendations",
    "render_timeline",
]
