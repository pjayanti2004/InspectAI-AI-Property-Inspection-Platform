"""Reusable Streamlit UI components for InspectAI.

Package: ``streamlit_app.components.ui_components``
Public API: re-exports from submodules.

Submodules
----------
page_setup    Page config, CSS injection, sidebar navigation.
headers       Page headers and section titles.
cards         Stat cards, action buttons, inspection cards, result summaries, detail rows, empty states.
wizard        Wizard stepper and navigation buttons.
dialogs       History cards, confirm dialogs, skeleton loaders, database error, empty history.
info_box      Info/warning/error/success boxes (direct import from this module).

All top-level names are re-exported here for backward compatibility.
"""
from __future__ import annotations

import streamlit as st


def render_html(html: str) -> None:
    """Render an HTML fragment safely in Streamlit."""
    import streamlit as st

    st.markdown(html, unsafe_allow_html=True)


# ── Submodule re-exports ───────────────────────────────────────────────────────

from streamlit_app.components.page_setup import (
    inject_custom_css,
    init_page_config,
    render_sidebar,
)
from streamlit_app.components.headers import (
    render_header,
    render_section_title,
)
from streamlit_app.components.cards import (
    render_action_button,
    render_action_buttons,
    render_detail_row,
    render_empty_state,
    render_health_score,
    render_inspection_card,
    render_inspection_grid,
    render_result_summary_card,
    render_severity_badge,
    render_stat_cards,
    render_welcome_banner,
)
from streamlit_app.components.wizard import (
    render_wizard_nav,
    render_wizard_stepper,
)
from streamlit_app.components.dialogs import (
    _derive_risk_level,
    _render_stat_cards_inner,
    _score_to_grade,
    render_confirm_dialog,
    render_database_error,
    render_empty_history,
    render_history_card,
    render_history_stat_cards,
    render_skeleton_loader,
)

# ── Info box (inline) ─────────────────────────────────────────────────────────


def render_info_box(message: str, box_type: str = "info") -> None:
    """Render a styled info/warning/error/success box."""
    from streamlit_app.utils.constants import (
        PRIMARY, ACCENT, SUCCESS, WARNING, DANGER,
        TEXT_SECONDARY,
    )

    colors = {
        "info": (PRIMARY, "rgba(79, 70, 229, 0.1)", "ℹ️"),
        "warning": (WARNING, "rgba(245, 158, 11, 0.1)", "⚠️"),
        "error": (DANGER, "rgba(239, 68, 68, 0.1)", "❌"),
        "success": (SUCCESS, "rgba(16, 185, 129, 0.1)", "✅"),
    }

    color, bg, icon = colors.get(box_type, colors["info"])

    render_html(
        f"""
        <div style="
            background: {bg};
            border: 1px solid {color};
            border-left: 4px solid {color};
            border-radius: 8px;
            padding: 1rem 1.25rem;
            margin: 0.75rem 0;
            display: flex;
            align-items: center;
            gap: 0.75rem;
        ">
            <span style="font-size: 1.2rem;">{icon}</span>
            <span style="color: {TEXT_SECONDARY}; font-size: 0.9rem;">{message}</span>
        </div>
        """,
    )