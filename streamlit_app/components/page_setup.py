"""Page setup: page config, CSS injection, and sidebar navigation."""
from __future__ import annotations

import streamlit as st

from streamlit_app.components.ui_components import render_html


def init_page_config() -> None:
    """Initialize Streamlit page config. Call once at the top of app.py."""
    st.set_page_config(
        page_title="InspectAI",
        page_icon="🔍",
        layout="wide",
        initial_sidebar_state="expanded",
    )


def inject_custom_css() -> None:
    """Inject the custom CSS stylesheet. Call once at the top of app.py."""
    from pathlib import Path
    st.html(Path("streamlit_app/styles/custom.css"))


def render_sidebar(current_page: str) -> str:
    """Render the sidebar navigation and return the selected page.

    Args:
        current_page: The currently active page key.

    Returns:
        The selected page key.
    """
    from streamlit_app.utils.constants import NAV_ITEMS, PRIMARY

    with st.sidebar:
        # Logo / Brand
        render_html("""
            <div style="padding: 1.25rem 1rem 1rem; text-align: center;">
                <div style="font-size: 2.5rem; margin-bottom: 0.25rem;">🔍</div>
                <h1 style="font-size: 1.4rem; font-weight: 800; color: #F1F5F9; margin: 0; letter-spacing: -0.02em;">
                    InspectAI
                </h1>
                <p style="font-size: 0.7rem; color: #64748B; margin: 0.25rem 0 0; letter-spacing: 0.1em; text-transform: uppercase;">
                    Inspect Smarter. Repair Faster.
                </p>
            </div>
            """,
        )

        render_html(f"<div style='border-top: 1px solid #334155; margin: 0.5rem 0 1rem;'></div>")

        # Navigation label
        render_html(
            "<p style='font-size: 0.7rem; color: #64748B; text-transform: uppercase; "
            "letter-spacing: 0.1em; padding: 0 0.75rem; margin-bottom: 0.5rem;'>Navigation</p>",
        )

        selected = current_page

        # Navigation buttons — styled via CSS
        for icon, label, page_key in NAV_ITEMS:
            is_active = page_key == current_page

            btn_type = "primary" if is_active else "secondary"
            if st.button(
                f"{icon}  {label}",
                key=f"nav_{page_key}",
                type=btn_type,
                use_container_width=True,
            ):
                if page_key == "new_inspection":
                    st.session_state["inspection_step"] = 1
                st.session_state["current_page"] = page_key
                st.rerun()

        # Sidebar footer
        render_html(
            f"<div style='border-top: 1px solid #334155; margin: 2rem 0 1rem;'></div>",
        )
        render_html(
            """
            <div style="padding: 0 1rem; text-align: center;">
                <p style="font-size: 0.7rem; color: #64748B;">
                    InspectAI v0.1.0<br>
                    <span style="opacity: 0.6;">UI Foundation Phase</span>
                </p>
            </div>
            """,
        )

        return selected