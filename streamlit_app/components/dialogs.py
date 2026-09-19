"""Dialogs and overlay components: history cards, confirm dialogs, skeleton loaders, error states."""
from __future__ import annotations

import streamlit as st

from streamlit_app.components.ui_components import render_html


# ── Grade and Risk Utilities ──────────────────────────────────────────────────

_GRADE_RANGES = {
    "A+": (90, 101), "A": (80, 90), "B+": (70, 80),
    "B": (60, 70), "C": (50, 60), "D": (0, 50),
}

_GRADE_COLORS = {
    "A+": "#10B981", "A": "#10B981", "B+": "#22C55E",
    "B": "#84CC16", "C": "#F59E0B", "D": "#EF4444",
}

_RISK_COLORS = {
    "Critical": "#EF4444", "High": "#F97316",
    "Medium": "#F59E0B", "Low": "#10B981",
}


def _score_to_grade(score: float) -> str:
    if score >= 90: return "A+"
    if score >= 80: return "A"
    if score >= 70: return "B+"
    if score >= 60: return "B"
    if score >= 50: return "C"
    return "D"


def _derive_risk_level(severity: str, health_score: float) -> str:
    sev = (severity or "").lower()
    if sev == "critical" or (health_score and health_score < 50):
        return "Critical"
    if sev == "high" or (health_score and health_score < 70):
        return "High"
    if sev == "medium" or (health_score and health_score < 85):
        return "Medium"
    return "Low"


# ── History Stat Cards ────────────────────────────────────────────────────────


def render_history_stat_cards(stats: dict) -> None:
    """Render stat cards for the history page header."""
    from streamlit_app.utils.constants import (
        PRIMARY, ACCENT, SUCCESS, WARNING, DANGER,
    )

    cards = [
        {
            "label": "Total Inspections",
            "value": str(stats.get("total_inspections", 0)),
            "icon": "📋",
            "color": PRIMARY,
            "trend": "All time",
            "trend_up": True,
        },
        {
            "label": "Average Health Score",
            "value": str(stats.get("avg_health_score", 0)),
            "icon": "❤️",
            "color": SUCCESS if stats.get("avg_health_score", 0) >= 70 else WARNING,
            "trend": "Average",
            "trend_up": stats.get("avg_health_score", 0) >= 70,
        },
        {
            "label": "Critical Properties",
            "value": str(stats.get("critical_count", 0)),
            "icon": "⚠️",
            "color": DANGER,
            "trend": "Needs attention",
            "trend_up": False,
        },
        {
            "label": "Avg Repair Cost",
            "value": f"₹{stats.get('avg_repair_cost', 0):,}",
            "icon": "💰",
            "color": ACCENT,
            "trend": "Average estimate",
            "trend_up": True,
        },
    ]
    _render_stat_cards_inner(cards)


def _render_stat_cards_inner(cards: list[dict]) -> None:
    """Internal stat card renderer."""
    from streamlit_app.utils.constants import TEXT_MUTED

    cols = st.columns(len(cards), gap="medium")
    for col, card in zip(cols, cards):
        with col:
            trend_arrow = "↑" if card.get("trend_up", True) else "↓"
            trend_color = "#10B981" if card.get("trend_up", True) else "#F59E0B"
            render_html(f"""
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


# ── History Card ──────────────────────────────────────────────────────────────


def render_history_card(
    inspection: dict,
    index: int = 0,
    on_open: callable = None,
    on_delete: callable = None,
    on_duplicate: callable = None,
) -> None:
    """Render a single inspection history card."""
    from streamlit_app.utils.constants import (
        SUCCESS, WARNING, DANGER,
        TEXT_PRIMARY, TEXT_MUTED, TEXT_SECONDARY,
    )
    from streamlit_app.components.ui_components import render_info_box

    ins_id    = inspection.get("inspection_id", "")
    address   = inspection.get("property_address", "Unknown Address")
    prop_type = inspection.get("property_type", "")
    date      = inspection.get("inspection_date", "")
    img_count = inspection.get("image_count", 0)
    status    = inspection.get("inspection_status", "completed")

    health_score   = inspection.get("overall_health_score")
    damage_pct     = inspection.get("overall_damage_pct")
    repair_cost    = inspection.get("avg_repair_cost", 0)
    risk_level     = inspection.get("risk_level", "Low")
    grade          = inspection.get("grade", "D")
    findings_count = inspection.get("damages_found", 0)
    has_report     = bool(inspection.get("report_id"))

    crit = inspection.get("critical_count", 0)
    high = inspection.get("high_count", 0)
    med  = inspection.get("medium_count", 0)
    low  = inspection.get("low_count", 0)

    grade_color  = _GRADE_COLORS.get(grade, TEXT_MUTED)
    risk_color   = _RISK_COLORS.get(risk_level, TEXT_MUTED)

    status_map = {
        "completed":  (SUCCESS,     "rgba(16, 185, 129, 0.15)"),
        "processing": (WARNING,     "rgba(245, 158, 11, 0.15)"),
        "failed":     (DANGER,      "rgba(239, 68, 68, 0.15)"),
    }
    status_color, status_bg = status_map.get(status, (TEXT_MUTED, "rgba(100,116,139,0.15)"))

    health_color = SUCCESS if health_score and health_score >= 80 else (
        WARNING if health_score and health_score >= 60 else DANGER
    )

    badges = []
    if crit > 0:  badges.append(f'<span class="badge badge-critical">{crit} Critical</span>')
    if high > 0:  badges.append(f'<span class="badge badge-high">{high} High</span>')
    if med > 0:   badges.append(f'<span class="badge badge-medium">{med} Medium</span>')
    if low > 0:   badges.append(f'<span class="badge badge-low">{low} Low</span>')
    badges_html = " ".join(badges)

    damage_str = f"{damage_pct:.1f}%" if damage_pct is not None else "N/A"
    cost_str   = f"₹{repair_cost:,}" if repair_cost else "—"

    render_html(
        f"""
        <div class="inspection-card animate-fade-in" style="animation-delay: {index * 0.05}s;">
            <div class="card-header">
                <div>
                    <div class="card-id">{ins_id}</div>
                    <div class="card-address">{address}</div>
                </div>
                <span class="card-status" style="background: {status_bg}; color: {status_color};">
                    {status}
                </span>
            </div>
            <div class="card-body">
                <div class="card-meta">
                    <span>{prop_type}</span>
                    <span style="color: {TEXT_MUTED};">·</span>
                    <span>{date}</span>
                    <span style="color: {TEXT_MUTED};">·</span>
                    <span>{img_count} image{'s' if img_count != 1 else ''}</span>
                </div>
                <div style="display: flex; gap: 0.5rem; margin-top: 0.75rem; flex-wrap: wrap;">
                    {badges_html}
                </div>
                <div style="margin-top: 0.75rem; display: flex; gap: 1.5rem; font-size: 0.85rem; color: {TEXT_SECONDARY};">
                    <span style="color: {health_color}; font-weight: 600;">Health: {health_score if health_score is not None else 'N/A'}</span>
                    <span>Damage: {damage_str}</span>
                    <span>Cost: {cost_str}</span>
                </div>
            </div>
            <div class="card-footer">
                <span style="font-size: 0.8rem; color: {TEXT_MUTED};">
                    Grade: <strong style="color: {grade_color};">{grade}</strong>
                    &nbsp;·&nbsp;
                    Risk: <strong style="color: {risk_color};">{risk_level}</strong>
                </span>
                <div>
        """,
    )

    cols = st.columns([1, 1, 1] if on_duplicate else [1, 1])
    with cols[0]:
        view_label = "📄 View" if has_report else "👁️ Open"
        if st.button(view_label, key=f"history_view_{index}_{ins_id}", type="secondary", use_container_width=True):
            if on_open:
                on_open(inspection)
            else:
                st.session_state["view_inspection_id"] = ins_id
                st.session_state["navigate_to"] = "reports"
                st.rerun()
    with cols[1]:
        if st.button("📋 Copy", key=f"history_dup_{index}_{ins_id}", type="secondary", use_container_width=True):
            if on_duplicate:
                on_duplicate(inspection)
            else:
                render_info_box("Duplicate functionality — select as template for a new inspection.", box_type="info")
    if on_duplicate:
        with cols[2]:
            if st.button("🗑️ Delete", key=f"history_del_{index}_{ins_id}", type="secondary", use_container_width=True):
                if on_delete:
                    on_delete(inspection)
                else:
                    st.session_state[f"delete_confirm_{ins_id}"] = True
                    st.rerun()

    render_html("</div></div>")


# ── Confirm Dialog ────────────────────────────────────────────────────────────


def render_confirm_dialog(
    title: str,
    message: str,
    confirm_label: str = "Delete",
    cancel_label: str = "Cancel",
    dialog_key: str = "confirm",
) -> bool | None:
    """Render a confirmation dialog inside a Streamlit container.

    Returns:
        True  if user confirmed.
        False if user cancelled.
        None  if dialog is not open.
    """
    if not st.session_state.get(dialog_key, False):
        return None

    with st.expander(f"⚠️ {title}", expanded=True):
        render_html(f"<p style='color: #94A3B8; font-size: 0.9rem;'>{message}</p>")
        col_a, col_b = st.columns(2)
        with col_a:
            confirmed = st.button(confirm_label, key=f"{dialog_key}_yes", type="primary", use_container_width=True)
        with col_b:
            cancelled = st.button(cancel_label, key=f"{dialog_key}_no", type="secondary", use_container_width=True)

        if confirmed:
            st.session_state[dialog_key] = False
            return True
        if cancelled:
            st.session_state[dialog_key] = False
            return False
    return None


# ── Skeleton Loader ───────────────────────────────────────────────────────────


def render_skeleton_loader(count: int = 4) -> None:
    """Render skeleton placeholder cards while data is loading."""
    cols = st.columns(2, gap="medium")
    for i in range(count):
        with cols[i % 2]:
            render_html(
                f"""
                <div class="inspection-card" style="opacity: 0.4; pointer-events: none;">
                    <div class="card-header">
                        <div>
                            <div class="card-id" style="background: #334155; border-radius: 4px; width: 120px; height: 16px;"></div>
                            <div style="background: #1E293B; border-radius: 4px; width: 200px; height: 14px; margin-top: 6px;"></div>
                        </div>
                        <span class="card-status" style="background: #1E293B; width: 70px; height: 24px;"></span>
                    </div>
                    <div class="card-body">
                        <div style="background: #1E293B; border-radius: 4px; width: 160px; height: 12px;"></div>
                        <div style="display: flex; gap: 0.5rem; margin-top: 0.75rem;">
                            <span style="background: #1E293B; border-radius: 12px; width: 60px; height: 22px;"></span>
                            <span style="background: #1E293B; border-radius: 12px; width: 60px; height: 22px;"></span>
                        </div>
                    </div>
                </div>
                """,
            )


# ── Database Error ────────────────────────────────────────────────────────────


def render_database_error(error_msg: str = "Unable to connect to the database.") -> None:
    """Render a database error state."""
    from streamlit_app.utils.constants import DANGER, TEXT_MUTED

    render_html(
        f"""
        <div style="
            text-align: center;
            padding: 3rem 1rem;
            background: rgba(239, 68, 68, 0.05);
            border: 1px solid rgba(239, 68, 68, 0.2);
            border-radius: 12px;
        ">
            <div style="font-size: 3rem; margin-bottom: 1rem;">🚫</div>
            <p style="color: {DANGER}; font-weight: 600; margin: 0 0 0.5rem; font-size: 1.1rem;">Database Unavailable</p>
            <p style="color: {TEXT_MUTED}; font-size: 0.85rem; margin: 0;">{error_msg}</p>
            <p style="color: {TEXT_MUTED}; font-size: 0.8rem; margin: 0.75rem 0 0;">
                Please check that the database file is not corrupted and try again.
            </p>
        </div>
        """,
    )


# ── Empty History ─────────────────────────────────────────────────────────────


def render_empty_history(message: str = "No inspections found.") -> None:
    """Render an empty state for the history page."""
    from streamlit_app.utils.constants import TEXT_MUTED, PRIMARY
    from streamlit_app.utils.session_manager import navigate_to

    render_html(
        f"""
        <div style="
            text-align: center;
            padding: 4rem 1rem;
        ">
            <div style="font-size: 4rem; margin-bottom: 1rem; opacity: 0.7;">📭</div>
            <p style="color: #F1F5F9; font-weight: 600; margin: 0 0 0.5rem; font-size: 1.1rem;">{message}</p>
            <p style="color: {TEXT_MUTED}; font-size: 0.9rem; margin: 0 0 1.5rem;">
                Try adjusting your search or filters, or start a new inspection.
            </p>
        </div>
        """,
    )
    if st.button("Start New Inspection", key="empty_new_insp", type="primary", use_container_width=False):
        navigate_to("new_inspection")