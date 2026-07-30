"""InspectAI — Main Application Entry Point.

Single entry point for the InspectAI Streamlit application.
Handles page config, CSS injection, session state init, sidebar navigation,
and routing for the 5-step inspection wizard.

Navigation flow:
    Dashboard
    └─ New Inspection wizard
       ├─ Step 1: Property Details
       ├─ Step 2: Upload Images
       ├─ Step 3: Review
       ├─ Step 4: Processing
       └─ Step 5: Results

    Sidebar pages: Dashboard | History | Reports | Settings | About
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from datetime import datetime
from pathlib import Path

# Ensure the project root is on sys.path so absolute imports resolve.
# When ``streamlit run streamlit_app/app.py`` is invoked, Streamlit prepends
# the script directory (streamlit_app/) to sys.path. That breaks
# ``from streamlit_app.X import ...`` because Python would then look for
# ``streamlit_app/streamlit_app/X.py``. Inserting the project root here
# restores the expected import layout.
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_SCRIPT_DIR)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

# Load .env BEFORE any module that reads environment variables.
# Without this, os.getenv("GEMINI_API_KEY") returns "" because the .env
# file was never loaded into the process environment.
from dotenv import load_dotenv
load_dotenv()

import streamlit as st

from streamlit_app.components.ui_components import (
    inject_custom_css,
    init_page_config,
    render_sidebar,
)
from streamlit_app.views.dashboard import render_dashboard
from streamlit_app.views.new_inspection import render_property_details
from streamlit_app.views.upload import render_image_upload
from streamlit_app.views.review import render_review
from streamlit_app.views.processing import render_processing
from streamlit_app.views.results import render_results
from streamlit_app.views.history import render_history
from streamlit_app.views.reports import render_reports
from streamlit_app.views.report import render_report_page
from streamlit_app.views.analytics import render_analytics_dashboard
from streamlit_app.views.settings import render_settings
from streamlit_app.views.about import render_about
from streamlit_app.utils.config import validate_config
from streamlit_app.utils.exceptions import InspectAIError
from streamlit_app.utils.logger import configure_app_logging
from streamlit_app.utils.settings import (
    get_config_summary,
    IS_PRODUCTION,
    LOG_LEVEL,
    validate_production_config,
)
from streamlit_app.utils.session_manager import (
    init_session,
    navigate_to,
    handle_navigation,
    get_page_from_step,
    reset_inspection_flow,
)


# ── Logging ──────────────────────────────────────────────────────────────────

logger = configure_app_logging("inspectai.app")


# ── Global Error Handler ─────────────────────────────────────────────────────

def _handle_page_error(exc: Exception) -> None:
    """Display a user-friendly error message for unhandled page exceptions."""
    logger.error("Unhandled page error: %s", exc, exc_info=True)
    if isinstance(exc, InspectAIError):
        st.error(f"**{exc.__class__.__name__}**: {exc}")
    else:
        st.error(
            "An unexpected error occurred while rendering this page. "
            "Please try again or contact support if the problem persists."
        )
        if st.checkbox("Show technical details", key="show_error_details"):
            st.exception(exc)


def _safe_render(page_key: str, renderer) -> None:
    """Wrap a page renderer with a global error handler."""
    try:
        renderer()
    except SystemExit:
        raise
    except Exception as exc:
        _handle_page_error(exc)


_TRACE_DIR = Path(tempfile.gettempdir()) / "inspectai_trace"
_TRACE_DIR.mkdir(exist_ok=True)


def _dump_trace_app(label: str) -> None:
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


# ── Page Registry ────────────────────────────────────────────────────────────
# Maps page keys to render functions.
PAGE_REGISTRY = {
    "dashboard": render_dashboard,
    "analytics": render_analytics_dashboard,
    "new_inspection": render_property_details,
    "upload": render_image_upload,
    "review": render_review,
    "processing": render_processing,
    "results": render_results,
    "history": render_history,
    "reports": render_reports,
    "settings": render_settings,
    "about": render_about,
}

# Pages that should NOT show the sidebar (full-screen loading)
NO_SIDEBAR_PAGES = {"processing"}


# ── Inspection Step → Page Map ───────────────────────────────────────────────
WIZARD_STEP_MAP = {
    1: "new_inspection",
    2: "upload",
    3: "review",
    4: "processing",
    5: "results",
}


def get_active_page() -> str:
    """Get the active page from session state.

    Returns:
        Page key string.
    """
    return st.session_state.get("current_page", "dashboard")


def route_to_page(page_key: str):
    """Set the active page and rerun.

    Args:
        page_key: Target page key from PAGE_REGISTRY.
    """
    if page_key in PAGE_REGISTRY:
        st.session_state["current_page"] = page_key
        # Clear inspection step if navigating to a non-wizard page
        if page_key not in WIZARD_STEP_MAP.values():
            st.session_state["inspection_step"] = 0
        st.rerun()


def start_new_inspection():
    """Reset everything and start a fresh inspection."""
    reset_inspection_flow()
    st.session_state["current_page"] = "new_inspection"
    st.rerun()


# ── Main Application ─────────────────────────────────────────────────────────
def main():
    """Main application entry point."""
    # Validate configuration before anything else
    config_errors = validate_config()
    if config_errors:
        st.error("**Configuration Error** — please fix the following issues:")
        for err in config_errors:
            st.markdown(f"- {err}")
        st.stop()

    # In production, run stricter validation
    if IS_PRODUCTION:
        prod_errors = validate_production_config()
        if prod_errors:
            for err in prod_errors:
                logger.warning("Production config warning: %s", err)

    # Initialize logging
    configure_app_logging("inspectai")

    # Log startup info (production mode only)
    if IS_PRODUCTION:
        logger.info("InspectAI starting in PRODUCTION mode")
        logger.info("Config summary: %s", get_config_summary())

    # Initialize everything
    init_page_config()
    inject_custom_css()
    init_session()
    handle_navigation()

    # If viewing a specific report (set by reports page card click),
    # set current_page so the sidebar shows "Reports" as active.
    if st.session_state.get("view_report_id"):
        st.session_state["current_page"] = "reports"

    # Determine the active page
    active_page = get_active_page()

    # If navigating away from wizard, reset step tracking
    if active_page not in WIZARD_STEP_MAP.values():
        if st.session_state.get("current_page") not in WIZARD_STEP_MAP.values():
            # Already on a non-wizard page, nothing to do
            pass

    # Sidebar (hidden on processing page)
    if active_page not in NO_SIDEBAR_PAGES:
        st.session_state["current_page"] = active_page
        selected_page = render_sidebar(current_page=active_page)
        if selected_page != active_page:
            route_to_page(selected_page)
            return
        active_page = selected_page
    else:
        # Processing page — set current_page so sidebar shows it as active
        st.session_state["current_page"] = active_page

    # Route to the appropriate page renderer with error handling
    _dump_trace_app("05_before_page_renderer")
    page_renderer = PAGE_REGISTRY.get(active_page, render_dashboard)
    _safe_render(active_page, page_renderer)


if __name__ == "__main__":
    main()
