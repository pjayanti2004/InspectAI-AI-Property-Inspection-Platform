"""Card renderers: stat cards, action buttons, inspection cards, result summaries."""
from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

import streamlit as st

from streamlit_app.components.ui_components import render_html
from streamlit_app.utils.constants import PRIMARY, SUCCESS, WARNING, DANGER
from streamlit_app.utils.session_manager import SessionKeys

_TRACE_DIR = Path(tempfile.gettempdir()) / "inspectai_trace"
_TRACE_DIR.mkdir(exist_ok=True)


def _dump_trace(label: str) -> None:
    """Append a timestamped snapshot of key session_state values to a trace file."""
    data = {
        "timestamp": datetime.now().isoformat(timespec="milliseconds"),
        "label": label,
        "navigate_to": st.session_state.get("navigate_to"),
        "current_page": st.session_state.get("current_page"),
        "inspection_step": st.session_state.get("inspection_step"),
        "full_session_state_keys": list(st.session_state.keys()),
    }
    path = _TRACE_DIR / "cards_nav_trace.jsonl"
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(data) + "\n")


# ── Stat Cards ────────────────────────────────────────────────────────────────


def render_stat_cards(cards: list = None) -> None:
    """Render a row of stat cards.

    Args:
        cards: List of dicts with keys: label, value, icon, color, trend, trend_up.
               If None, uses default stats.
    """
    from streamlit_app.utils.constants import STAT_CARDS

    cards = cards or STAT_CARDS
    cols = st.columns(len(cards), gap="medium")
    for col, card in zip(cols, cards):
        with col:
            trend_arrow = "↗" if card.get("trend_up", True) else "↘"
            trend_color = SUCCESS if card.get("trend_up", True) else WARNING
            render_html(
                f"""
                <div class="stat-card" style="--card-color: {card['color']};">
                    <div style="position: absolute; top: 0; left: 0; right: 0; height: 3px; background: {card['color']}; border-radius: 12px 12px 0 0;"></div>
                    <div class="icon">{card['icon']}</div>
                    <div class="value">{card['value']}</div>
                    <div class="label">{card['label']}</div>
                    <div class="trend" style="color: {trend_color};">
                        {trend_arrow} {card.get('trend', '')}
                    </div>
                </div>
                """,
            )


# ── Action Buttons ────────────────────────────────────────────────────────────


def render_action_button(
    label: str,
    icon: str,
    page_key: str,
    description: str = "",
    color: str = PRIMARY,
) -> None:
    """Render a quick action card that navigates to a page."""
    r, g, b = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
    render_html(
        f"""
        <div class="action-card" style="cursor: default;">
            <div class="action-icon" style="background: rgba({r}, {g}, {b}, 0.15);">
                <span>{icon}</span>
            </div>
            <div class="action-label">{label}</div>
            <div class="action-desc">{description}</div>
        </div>
        """,
    )
    if st.button(label, key=f"action_{page_key}", type="secondary"):
        _dump_trace("01_after_click")
        st.session_state[SessionKeys.NAVIGATE_TO] = page_key
        _dump_trace("02_after_navigate_to_assign")
        st.rerun()


def render_action_buttons(actions: list = None) -> None:
    """Render a grid of quick action buttons."""
    from streamlit_app.utils.constants import QUICK_ACTIONS
    from streamlit_app.components.headers import render_section_title

    actions = actions or QUICK_ACTIONS
    render_section_title("Quick Actions", icon="⚡")

    cols = st.columns(len(actions), gap="medium")
    for col, action in zip(cols, actions):
        with col:
            render_action_button(
                label=action["label"],
                icon=action["icon"],
                page_key=action["page"],
                description=action.get("description", ""),
                color=action.get("color", PRIMARY),
            )


# ── Inspection Cards ──────────────────────────────────────────────────────────


def render_inspection_card(inspection: dict, index: int = 0) -> None:
    """Render a single inspection result card."""
    from streamlit_app.utils.constants import (
        TEXT_PRIMARY, TEXT_MUTED, TEXT_SECONDARY, BORDER_COLOR,
    )

    # Determine status color
    status = inspection.get("status", "Completed")
    if status == "Completed":
        status_color = SUCCESS
        status_bg = "rgba(16, 185, 129, 0.15)"
    elif status == "Review":
        status_color = WARNING
        status_bg = "rgba(245, 158, 11, 0.15)"
    else:
        status_color = TEXT_MUTED
        status_bg = "rgba(100, 116, 139, 0.15)"

    # Health score color
    health = inspection.get("health_score", 70)
    if health >= 80:
        health_color = SUCCESS
    elif health >= 60:
        health_color = WARNING
    else:
        health_color = DANGER

    render_html(
        f"""
        <div class="inspection-card animate-fade-in" style="animation-delay: {index * 0.1}s;">
            <div class="card-header">
                <div>
                    <div class="card-id">{inspection.get('id', 'INS-0000')}</div>
                    <div class="card-address">{inspection.get('address', 'Unknown Address')}</div>
                </div>
                <span class="card-status" style="background: {status_bg}; color: {status_color};">
                    {status}
                </span>
            </div>
            <div class="card-body">
                <div class="card-meta">
                    <span>{inspection.get('property_type', '')}</span>
                    <span>•</span>
                    <span>{inspection.get('date', '')}</span>
                    <span>•</span>
                    <span>{inspection.get('image_count', 0)} images</span>
                </div>
            </div>
            <div class="card-footer">
                <div style="display: flex; gap: 0.75rem; font-size: 0.75rem; color: {TEXT_MUTED};">
                    <span style="color: {DANGER};">● {inspection.get('critical_count', 0)} Critical</span>
                    <span style="color: #F97316;">● {inspection.get('high_count', 0)} High</span>
                    <span style="color: {WARNING};">● {inspection.get('medium_count', 0)} Med</span>
                    <span style="color: {SUCCESS};">● {inspection.get('low_count', 0)} Low</span>
                </div>
                <div style="
                    font-size: 0.85rem;
                    font-weight: 700;
                    color: {health_color};
                ">
                    {health}/100
                </div>
            </div>
        </div>
        """,
    )

    # View button below the card
    if st.button("View Report", key=f"view_{inspection.get('id', index)}_{index}", type="secondary"):
        st.session_state.view_inspection_id = inspection.get("id")
        st.session_state[SessionKeys.NAVIGATE_TO] = "reports"
        st.rerun()


def render_inspection_grid(inspections: list = None) -> None:
    """Render a grid of inspection cards."""
    from streamlit_app.utils.constants import RECENT_INSPECTIONS, TEXT_MUTED
    from streamlit_app.components.headers import render_section_title

    inspections = inspections or RECENT_INSPECTIONS
    render_section_title("Recent Activity", icon="📋")

    if not inspections:
        render_html(
            f"""
            <div style="text-align: center; padding: 3rem; color: {TEXT_MUTED};">
                <div style="font-size: 3rem; margin-bottom: 1rem;">📭</div>
                <p style="font-size: 1.1rem;">No inspections yet.</p>
                <p style="font-size: 0.9rem;">Start your first inspection to see results here.</p>
            </div>
            """,
        )
        return

    cols = st.columns(2, gap="medium")
    for i, inspection in enumerate(inspections):
        with cols[i % 2]:
            render_inspection_card(inspection, index=i)


# ── Welcome Banner ────────────────────────────────────────────────────────────


def render_welcome_banner(name: str = "User") -> None:
    """Render a welcome banner at the top of the dashboard."""
    from streamlit_app.utils.constants import PRIMARY, TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED
    from datetime import datetime

    render_html(
        f"""
        <div class="card-glass" style="
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 2rem;
            margin-bottom: 1.5rem;
            background: linear-gradient(135deg, rgba(79, 70, 229, 0.1), rgba(6, 182, 212, 0.05));
            border: 1px solid rgba(79, 70, 229, 0.2);
        ">
            <div>
                <h1 style="margin: 0; font-size: 1.75rem;">
                    Welcome back, <span style="color: {PRIMARY};">{name}</span> 👋
                </h1>
                <p style="margin: 0.5rem 0 0; color: {TEXT_SECONDARY}; font-size: 0.95rem;">
                    Here's an overview of your inspection activity.
                </p>
            </div>
            <div style="text-align: right;">
                <p style="margin: 0; font-size: 0.85rem; color: {TEXT_MUTED};">
                    {datetime.now().strftime('%A, %B %d, %Y')}
                </p>
            </div>
        </div>
        """,
    )


# ── Severity Badge ────────────────────────────────────────────────────────────


def render_severity_badge(severity: str) -> None:
    """Render a severity badge.

    Args:
        severity: One of "Critical", "High", "Medium", "Low".
    """
    severity_lower = severity.lower()
    render_html(f'<span class="badge badge-{severity_lower}">{severity}</span>')


# ── Health Score Ring ─────────────────────────────────────────────────────────


def render_health_score(score: int, size: int = 120) -> None:
    """Render a health score indicator."""
    from streamlit_app.utils.constants import SUCCESS, WARNING, DANGER, TEXT_PRIMARY, TEXT_MUTED

    if score >= 80:
        color = SUCCESS
        label = "Good"
    elif score >= 60:
        color = WARNING
        label = "Fair"
    else:
        color = DANGER
        label = "Poor"

    percentage = score / 100
    circumference = 2 * 3.14159 * 40
    offset = circumference * (1 - percentage)

    render_html(
        f"""
        <div style="display: flex; flex-direction: column; align-items: center; gap: 0.25rem;">
            <div style="position: relative; width: {size}px; height: {size}px;">
                <svg width="{size}" height="{size}" viewBox="0 0 100 100">
                    <circle cx="50" cy="50" r="40" fill="none" stroke="#334155" stroke-width="8" />
                    <circle cx="50" cy="50" r="40" fill="none" stroke="{color}" stroke-width="8"
                        stroke-dasharray="251.33" stroke-dashoffset="{offset}"
                        stroke-linecap="round"
                        transform="rotate(-90 50 50)"
                        style="transition: stroke-dashoffset 1s ease-out;" />
                </svg>
                <div style="position: absolute; inset: 0; display: flex; flex-direction: column; align-items: center; justify-content: center;">
                    <span style="font-size: 1.75rem; font-weight: 800; color: {TEXT_PRIMARY};">{score}</span>
                    <span style="font-size: 0.6rem; color: {TEXT_MUTED}; text-transform: uppercase; letter-spacing: 0.1em;">{label}</span>
                </div>
            </div>
        </div>
        """,
    )


# ── Result Summary Card ───────────────────────────────────────────────────────


def render_result_summary_card(result: dict) -> None:
    """Render a beautiful summary card for inspection results."""
    health_score = result.get("health_score", 0)
    issues_found = result.get("issues_found", 0)
    severity = result.get("severity", "Unknown")
    cost_min = result.get("estimated_cost_min", 0)
    cost_max = result.get("estimated_cost_max", 0)
    status = result.get("status", "Completed")
    inspection_id = result.get("inspection_id", "INS-0000")

    # Severity color
    severity_color_map = {
        "Critical": ("#EF4444", "rgba(239, 68, 68, 0.15)"),
        "High": ("#F97316", "rgba(249, 115, 22, 0.15)"),
        "Medium": ("#F59E0B", "rgba(245, 158, 11, 0.15)"),
        "Low": ("#10B981", "rgba(16, 185, 129, 0.15)"),
    }
    sev_color, sev_bg = severity_color_map.get(severity, ("#64748B", "rgba(100, 116, 139, 0.15)"))

    # Health score color
    if health_score >= 80:
        health_color = "#10B981"
        health_label = "Good"
    elif health_score >= 60:
        health_color = "#F59E0B"
        health_label = "Fair"
    else:
        health_color = "#EF4444"
        health_label = "Poor"

    # Health ring SVG calculation
    percentage = health_score / 100
    circumference = 2 * 3.14159 * 52
    offset = circumference * (1 - percentage)

    render_html(
        f"""
        <div class="card-glass" style="
            background: linear-gradient(135deg, rgba(79, 70, 229, 0.08), rgba(6, 182, 212, 0.04));
            border: 1px solid rgba(79, 70, 229, 0.2);
            padding: 2rem;
            margin: 1rem 0;
        ">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 1.5rem;">
                <div>
                    <div style="font-size: 0.75rem; color: #64748B; text-transform: uppercase; letter-spacing: 0.1em;">
                        Inspection ID
                    </div>
                    <div style="font-size: 1rem; color: #F1F5F9; font-weight: 600; margin-top: 0.25rem;">
                        {inspection_id}
                    </div>
                </div>
                <div style="
                    padding: 0.4rem 1rem;
                    background: rgba(16, 185, 129, 0.15);
                    color: #10B981;
                    border-radius: 20px;
                    font-size: 0.8rem;
                    font-weight: 600;
                    text-transform: uppercase;
                    letter-spacing: 0.05em;
                ">
                    ✓ {status}
                </div>
            </div>

            <div style="display: grid; grid-template-columns: auto 1fr; gap: 2.5rem; align-items: center;">
                <!-- Health Score Ring -->
                <div style="position: relative; width: 140px; height: 140px;">
                    <svg width="140" height="140" viewBox="0 0 120 120">
                        <circle cx="60" cy="60" r="52" fill="none" stroke="#334155" stroke-width="8" />
                        <circle cx="60" cy="60" r="52" fill="none" stroke="{health_color}" stroke-width="8"
                            stroke-dasharray="326.73" stroke-dashoffset="{offset}"
                            stroke-linecap="round"
                            transform="rotate(-90 60 60)"
                            style="transition: stroke-dashoffset 1.5s ease-out;" />
                    </svg>
                    <div style="position: absolute; inset: 0; display: flex; flex-direction: column; align-items: center; justify-content: center;">
                        <span style="font-size: 2.25rem; font-weight: 800; color: #F1F5F9; line-height: 1;">{health_score}<span style="font-size: 0.9rem; color: #64748B; font-weight: 500;">/100</span></span>
                        <span style="font-size: 0.65rem; color: {health_color}; text-transform: uppercase; letter-spacing: 0.1em; margin-top: 0.25rem; font-weight: 600;">{health_label}</span>
                    </div>
                </div>

                <!-- Stats Grid -->
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1.25rem;">
                    <div>
                        <div style="font-size: 0.7rem; color: #64748B; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 0.5rem;">
                            Issues Found
                        </div>
                        <div style="font-size: 1.75rem; font-weight: 700; color: #F1F5F9; line-height: 1;">
                            {issues_found}
                        </div>
                        <div style="font-size: 0.75rem; color: #64748B; margin-top: 0.25rem;">
                            detected issues
                        </div>
                    </div>
                    <div>
                        <div style="font-size: 0.7rem; color: #64748B; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 0.5rem;">
                            Severity
                        </div>
                        <div style="
                            display: inline-block;
                            padding: 0.4rem 0.85rem;
                            background: {sev_bg};
                            color: {sev_color};
                            border-radius: 8px;
                            font-size: 1.1rem;
                            font-weight: 700;
                        ">
                            {severity}
                        </div>
                    </div>
                    <div style="grid-column: 1 / -1;">
                        <div style="font-size: 0.7rem; color: #64748B; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 0.5rem;">
                            Estimated Repair Cost
                        </div>
                        <div style="font-size: 1.5rem; font-weight: 700; color: #4F46E5; line-height: 1;">
                            ₹{cost_min:,} — ₹{cost_max:,}
                        </div>
                        <div style="font-size: 0.75rem; color: #64748B; margin-top: 0.25rem;">
                            based on {issues_found} finding{'s' if issues_found != 1 else ''}
                        </div>
                    </div>
                </div>
            </div>
        </div>
        """,
    )


# ── Detail Row ────────────────────────────────────────────────────────────────


def render_detail_row(label: str, value: str, icon: str = "") -> None:
    """Render a labeled detail row, used on the review page."""
    icon_html = f"<span style='margin-right: 0.4rem;'>{icon}</span>" if icon else ""
    render_html(
        f"""
        <div style="
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0.85rem 1rem;
            background: rgba(30, 41, 59, 0.5);
            border: 1px solid rgba(51, 65, 85, 0.5);
            border-radius: 8px;
            margin-bottom: 0.5rem;
        ">
            <div style="font-size: 0.85rem; color: #64748B; font-weight: 500;">
                {icon_html}{label}
            </div>
            <div style="font-size: 0.9rem; color: #F1F5F9; font-weight: 600; text-align: right; max-width: 60%; word-wrap: break-word;">
                {value if value else '<span style="color: #64748B;">—</span>'}
            </div>
        </div>
        """,
    )


# ── Empty State ───────────────────────────────────────────────────────────────


def render_empty_state(icon: str, title: str, message: str) -> None:
    """Render an empty state with an icon and message."""
    render_html(
        f"""
        <div style="
            text-align: center;
            padding: 2rem 1rem;
            background: rgba(30, 41, 59, 0.3);
            border: 2px dashed rgba(51, 65, 85, 0.6);
            border-radius: 12px;
            margin: 1rem 0;
        ">
            <div style="font-size: 3rem; margin-bottom: 0.75rem;">{icon}</div>
            <p style="color: #F1F5F9; font-weight: 600; margin: 0 0 0.5rem; font-size: 1rem;">{title}</p>
            <p style="color: #64748B; font-size: 0.85rem; margin: 0;">{message}</p>
        </div>
        """,
    )