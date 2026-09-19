"""Page header and section title renderers."""
from __future__ import annotations

import streamlit as st

from streamlit_app.components.ui_components import render_html


def render_header(
    title: str,
    subtitle: str = "",
    icon: str = "",
    actions: list = None,
) -> None:
    """Render a consistent page header.

    Args:
        title: Main heading text.
        subtitle: Optional subtitle below the heading.
        icon: Optional emoji icon before the title.
        actions: Optional list of (label, key) tuples for header action buttons.
    """
    from streamlit_app.utils.constants import TEXT_PRIMARY, TEXT_MUTED, BORDER_COLOR

    icon_html = f"<span style='font-size: 1.5rem;'>{icon} </span>" if icon else ""

    # Build action buttons HTML outside the f-string to avoid backslash issues
    action_buttons_html = ""
    if actions:
        buttons = []
        for l, k in actions:
            btn = (
                '<button class="btn-primary" '
                'style="margin-left: 0.5rem; font-size: 0.85rem; padding: 0.5rem 1rem; border: none; border-radius: 6px; cursor: pointer;">'
                f'{l}</button>'
            )
            buttons.append(btn)
        action_buttons_html = "".join(buttons)

    subtitle_html = (
        f"<p style='color: {TEXT_MUTED}; margin: 0.25rem 0 0; font-size: 0.9rem;'>{subtitle}</p>"
        if subtitle else ""
    )

    render_html(
        f"""
        <div style="
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 2rem;
            padding-bottom: 1rem;
            border-bottom: 1px solid {BORDER_COLOR};
        ">
            <div>
                <h2 style="margin: 0; display: flex; align-items: center; gap: 0.5rem;">
                    {icon_html}{title}
                </h2>
                {subtitle_html}
            </div>
            <div>
                {action_buttons_html}
            </div>
        </div>
        """,
    )

    # Hidden buttons for action handling
    if actions:
        for label, key in actions:
            st.button(label, key=key, type="primary", use_container_width=False)


def render_section_title(title: str, icon: str = "") -> None:
    """Render a section divider title.

    Args:
        title: Section heading text.
        icon: Optional emoji icon.
    """
    from streamlit_app.utils.constants import TEXT_PRIMARY, TEXT_MUTED, BORDER_COLOR

    icon_html = f"<span>{icon} </span>" if icon else ""
    render_html(
        f"""
        <div class="section-title">
            {icon_html}{title}
        </div>
        """,
    )