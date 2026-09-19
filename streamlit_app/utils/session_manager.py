"""Session state management utilities for InspectAI.

Provides functions to initialize, reset, and manage Streamlit session state
for the 5-step inspection wizard.
"""
from __future__ import annotations

import datetime
import json
import os
import random
import tempfile
from pathlib import Path

import streamlit as st

_TRACE_DIR = Path(tempfile.gettempdir()) / "inspectai_trace"
_TRACE_DIR.mkdir(exist_ok=True)


def _dump_trace(label: str) -> None:
    """Append a timestamped snapshot of key session_state values to a trace file."""
    data = {
        "timestamp": datetime.datetime.now().isoformat(timespec="milliseconds"),
        "label": label,
        "navigate_to": st.session_state.get("navigate_to"),
        "current_page": st.session_state.get("current_page"),
        "inspection_step": st.session_state.get("inspection_step"),
        "full_session_state_keys": list(st.session_state.keys()),
    }
    path = _TRACE_DIR / "cards_nav_trace.jsonl"
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(data) + "\n")


# ── Session State Keys ───────────────────────────────────────────────────────
class SessionKeys:
    """Centralized session state key names."""
    CURRENT_PAGE = "current_page"
    INSPECTION_STEP = "inspection_step"
    NAVIGATE_TO = "navigate_to"
    VIEW_INSPECTION_ID = "view_inspection_id"

    # Inspection wizard data
    PROPERTY_DATA = "property_data"
    UPLOADED_FILES = "uploaded_files"
    INSPECTION_DATA = "inspection_data"  # Combined final inspection record
    PREVIOUS_INSPECTIONS = "previous_inspections"  # List of past inspections for comparison

    # User state
    USER_LOGGED_IN = "user_logged_in"
    USER_DATA = "user_data"

    # Display preferences
    DARK_MODE = "dark_mode"
    NOTIFICATIONS_ENABLED = "notifications_enabled"


# ── Initialization ───────────────────────────────────────────────────────────
def init_session():
    """Initialize all session state variables with default values."""
    defaults = {
        SessionKeys.CURRENT_PAGE: "dashboard",
        SessionKeys.INSPECTION_STEP: 1,
        SessionKeys.NAVIGATE_TO: None,
        SessionKeys.VIEW_INSPECTION_ID: None,
        SessionKeys.PROPERTY_DATA: None,
        SessionKeys.UPLOADED_FILES: None,
        SessionKeys.INSPECTION_DATA: None,
        SessionKeys.USER_LOGGED_IN: False,
        SessionKeys.USER_DATA: None,
        SessionKeys.DARK_MODE: True,
        SessionKeys.NOTIFICATIONS_ENABLED: True,
    }

    for key, default in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default


# ── Navigation ───────────────────────────────────────────────────────────────
def navigate_to(page_key: str):
    """Navigate to a specific page."""
    if page_key:
        st.session_state[SessionKeys.CURRENT_PAGE] = page_key
        st.session_state[SessionKeys.NAVIGATE_TO] = page_key
        st.rerun()


def handle_navigation():
    """Process navigation requests stored in session state.

    Reads the NAVIGATE_TO flag, switches to that page, then clears the flag.
    """
    _dump_trace("03_handle_nav_before")
    target = st.session_state.get(SessionKeys.NAVIGATE_TO)
    if target:
        st.session_state[SessionKeys.CURRENT_PAGE] = target
        st.session_state[SessionKeys.NAVIGATE_TO] = None
    _dump_trace("04_handle_nav_after")


def go_back():
    """Navigate to the previous page in the app flow."""
    current = st.session_state.get(SessionKeys.CURRENT_PAGE, "dashboard")
    back_map = {
        "new_inspection": "dashboard",
        "upload": "new_inspection",
        "review": "upload",
        "processing": "review",
        "results": "reports",
        "report_detail": "reports",
        "history": "dashboard",
        "reports": "dashboard",
        "settings": "dashboard",
        "about": "dashboard",
    }
    navigate_to(back_map.get(current, "dashboard"))


# ── Inspection Flow ──────────────────────────────────────────────────────────
def get_page_from_step(step: int) -> str:
    """Map inspection step number to page key.

    Steps:
        1 → Property Details (new_inspection)
        2 → Upload Images (upload)
        3 → Review (review)
        4 → Processing (processing)
        5 → Results (results)
    """
    step_map = {
        1: "new_inspection",
        2: "upload",
        3: "review",
        4: "processing",
        5: "results",
    }
    return step_map.get(step, "dashboard")


def reset_inspection_flow():
    """Reset the entire inspection flow to initial state."""
    st.session_state[SessionKeys.INSPECTION_STEP] = 1
    st.session_state[SessionKeys.PROPERTY_DATA] = None
    st.session_state[SessionKeys.UPLOADED_FILES] = None
    st.session_state[SessionKeys.INSPECTION_DATA] = None


def get_inspection_step() -> int:
    """Get the current inspection step (1-5).

    Returns:
        Current step number.
    """
    return st.session_state.get(SessionKeys.INSPECTION_STEP, 1)


def set_inspection_step(step: int):
    """Set the current inspection step.

    Args:
        step: Step number (1-5).
    """
    st.session_state[SessionKeys.INSPECTION_STEP] = max(1, min(5, step))


# ── Property Data ────────────────────────────────────────────────────────────
def save_property_data(data: dict):
    """Save property information and advance to upload step.

    Args:
        data: Dict containing property form fields.
    """
    st.session_state[SessionKeys.PROPERTY_DATA] = data
    st.session_state[SessionKeys.INSPECTION_STEP] = 2


def get_property_data() -> dict | None:
    """Get saved property data."""
    return st.session_state.get(SessionKeys.PROPERTY_DATA)


# ── Uploaded Files ───────────────────────────────────────────────────────────
def save_uploaded_files(files: list):
    """Save uploaded image files and advance to review step.

    Args:
        files: List of UploadedFile objects from Streamlit.
    """
    st.session_state[SessionKeys.UPLOADED_FILES] = files
    st.session_state[SessionKeys.INSPECTION_STEP] = 3


def get_uploaded_files() -> list | None:
    """Get saved uploaded files."""
    return st.session_state.get(SessionKeys.UPLOADED_FILES)


# ── Inspection Data (Combined Record) ────────────────────────────────────────
def build_inspection_id() -> str:
    """Generate a unique inspection ID.

    Returns:
        String like INS-2026-0043
    """
    today = datetime.date.today()
    year = today.year
    random_suffix = random.randint(1000, 9999)
    return f"INS-{year}-{random_suffix}"


def save_inspection_data(property_data: dict, uploaded_files: list, results: dict = None):
    """Combine property data, file info, and results into a single inspection record.

    This simulates what would be saved to a database in a real app.

    Args:
        property_data: Dict from the property form.
        uploaded_files: List of uploaded file objects.
        results: Dict from AI analysis (None for now, will be filled later).
    """
    inspection = {
        "id": build_inspection_id(),
        "property_data": property_data,
        "image_count": len(uploaded_files),
        "image_names": [f.name for f in uploaded_files],
        "created_at": datetime.datetime.now().isoformat(),
        "status": "Completed",
    }

    if results:
        inspection.update(results)

    st.session_state[SessionKeys.INSPECTION_DATA] = inspection
    st.session_state[SessionKeys.INSPECTION_STEP] = 5
    return inspection


def get_inspection_data() -> dict | None:
    """Get the combined inspection data record."""
    return st.session_state.get(SessionKeys.INSPECTION_DATA)


# ── User State ───────────────────────────────────────────────────────────────
def set_user_logged_in(user_data: dict):
    """Set user as logged in."""
    st.session_state[SessionKeys.USER_LOGGED_IN] = True
    st.session_state[SessionKeys.USER_DATA] = user_data


def set_user_logged_out():
    """Set user as logged out and clear user data."""
    st.session_state[SessionKeys.USER_LOGGED_IN] = False
    st.session_state[SessionKeys.USER_DATA] = None


def is_user_logged_in() -> bool:
    """Check if a user is currently logged in."""
    return st.session_state.get(SessionKeys.USER_LOGGED_IN, False)


def get_user_name() -> str:
    """Get the current user's display name."""
    user_data = st.session_state.get(SessionKeys.USER_DATA)
    if user_data:
        return user_data.get("full_name", "User")
    return "User"


# ── Display State ────────────────────────────────────────────────────────────
def get_dark_mode() -> bool:
    """Get dark mode preference."""
    return st.session_state.get(SessionKeys.DARK_MODE, True)


def toggle_dark_mode():
    """Toggle dark mode preference."""
    st.session_state[SessionKeys.DARK_MODE] = not get_dark_mode()


# ── Debug / Development ──────────────────────────────────────────────────────
def show_session_state():
    """Display current session state for debugging."""
    with st.expander("🔧 Session State (Dev)"):
        st.json(dict(st.session_state))


def clear_session():
    """Clear all session state."""
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    init_session()
    st.rerun()
