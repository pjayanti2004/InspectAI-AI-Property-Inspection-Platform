"""Dashboard page — Main landing dashboard for InspectAI.

Shows welcome banner, stat cards, quick actions, and recent activity.
"""
import streamlit as st

from streamlit_app.components.ui_components import (
    inject_custom_css,
    init_page_config,
    render_welcome_banner,
    render_stat_cards,
    render_action_buttons,
    render_inspection_grid,
    render_info_box,
)


def render_dashboard():
    """Render the dashboard page."""
    inject_custom_css()
    init_page_config()

    # Welcome banner
    render_welcome_banner(name="User")

    # Stat cards
    render_stat_cards()

    # Quick actions
    render_action_buttons()

    # Recent activity
    render_inspection_grid()
