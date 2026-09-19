"""Reusable UI components for InspectAI.

Submodules
----------
page_setup       — Page config, CSS injection, sidebar.
headers          — Page headers and section titles.
cards            — Stat cards, action buttons, inspection cards, result summaries.
wizard           — Wizard stepper and navigation buttons.
dialogs          — History cards, confirm dialogs, skeleton loaders, error states.
ui_components    — Backward-compatible facade re-exporting all submodules.
"""
from __future__ import annotations

from streamlit_app.components.ui_components import (
    _derive_risk_level,
    _render_stat_cards_inner,
    _score_to_grade,
    inject_custom_css,
    init_page_config,
    render_action_button,
    render_action_buttons,
    render_confirm_dialog,
    render_database_error,
    render_detail_row,
    render_empty_history,
    render_empty_state,
    render_header,
    render_health_score,
    render_history_card,
    render_history_stat_cards,
    render_html,
    render_inspection_card,
    render_inspection_grid,
    render_info_box,
    render_result_summary_card,
    render_section_title,
    render_severity_badge,
    render_skeleton_loader,
    render_sidebar,
    render_stat_cards,
    render_welcome_banner,
    render_wizard_nav,
    render_wizard_stepper,
)

__all__ = [
    "inject_custom_css",
    "init_page_config",
    "render_html",
    "render_sidebar",
    "render_header",
    "render_section_title",
    "render_action_button",
    "render_action_buttons",
    "render_detail_row",
    "render_empty_state",
    "render_health_score",
    "render_inspection_card",
    "render_inspection_grid",
    "render_result_summary_card",
    "render_severity_badge",
    "render_stat_cards",
    "render_welcome_banner",
    "render_wizard_nav",
    "render_wizard_stepper",
    "render_confirm_dialog",
    "render_database_error",
    "render_empty_history",
    "render_history_card",
    "render_history_stat_cards",
    "render_skeleton_loader",
    "render_info_box",
    "_derive_risk_level",
    "_render_stat_cards_inner",
    "_score_to_grade",
]
