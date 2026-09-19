"""History page — Browse past inspection records.

Connected to the SQLite database via streamlit_app.database.repository.

Features:
  • Loads inspections joined with properties + reports (single query)
  • Search by property name / inspection ID / city
  • Filters: risk, grade, property type, date range
  • Sort: newest, oldest, highest damage, lowest damage, highest cost
  • Stat cards: total inspections, avg health, critical properties, avg cost
  • Per-card actions: View Report, Duplicate, Delete (with confirmation)
  • Empty / loading / error states
"""
from __future__ import annotations

import time
from datetime import date

import streamlit as st

from streamlit_app.components.ui_components import (
    inject_custom_css,
    init_page_config,
    render_database_error,
    render_empty_history,
    render_header,
    render_history_card,
    render_history_stat_cards,
    render_html,
    render_info_box,
    render_section_title,
    render_skeleton_loader,
)
from streamlit_app.database import (
    delete_inspection,
    get_history_stats,
    get_inspection_history,
)
from streamlit_app.utils.constants import PROPERTY_TYPES
from streamlit_app.utils.session_manager import navigate_to


# ── Constants ─────────────────────────────────────────────────────────────────
RISK_LEVELS = ["Critical", "High", "Medium", "Low"]
GRADES = ["excellent", "good", "fair", "poor"]
GRADE_LABELS = {
    "excellent": "Excellent (A+ / A)",
    "good":      "Good (B+ / B)",
    "fair":      "Fair (C)",
    "poor":      "Poor (D)",
}
SEVERITY_OPTIONS = ["critical", "high", "medium", "low"]
SORT_OPTIONS = {
    "newest":         "Newest First",
    "oldest":         "Oldest First",
    "highest_damage": "Highest Damage",
    "lowest_damage":  "Lowest Damage",
    "highest_cost":   "Highest Cost",
}
DEFAULT_SORT = list(SORT_OPTIONS.keys()).index("newest")


# ── Page renderer ────────────────────────────────────────────────────────────
def render_history():
    """Render the inspection history page."""
    inject_custom_css()
    init_page_config()

    render_header(
        title="Inspection History",
        subtitle="Browse and manage your past inspections",
        icon="📜",
    )

    # 1) Stats — show skeleton first, then real values
    if "history_loaded" not in st.session_state:
        st.session_state["history_loaded"] = False

    if not st.session_state["history_loaded"]:
        render_skeleton_loader(count=4)
        _render_filters()
        _simulate_load()
        return

    # 2) Load stats + history from DB (guarded against errors)
    try:
        stats = get_history_stats()
        inspections = get_inspection_history(
            search=st.session_state.get("hist_search", ""),
            property_type=st.session_state.get("hist_property_type", ""),
            severity=st.session_state.get("hist_severity", ""),
            grade=st.session_state.get("hist_grade", ""),
            date_from=st.session_state.get("hist_date_from", ""),
            date_to=st.session_state.get("hist_date_to", ""),
            sort_by=st.session_state.get("hist_sort", "newest"),
            limit=100,
            offset=0,
        )
    except Exception as exc:
        render_database_error(f"Failed to load inspections: {exc}")
        return

    # 3) Stat cards
    render_history_stat_cards(stats)

    render_html("<div style='margin-top: 1.5rem;'></div>")

    # 4) Filters
    _render_filters()

    # 5) Confirmation dialog (delete)
    _handle_delete_confirmation(inspections)

    # 6) Results
    render_section_title(
        f"Showing {len(inspections)} inspection{'s' if len(inspections) != 1 else ''}",
        icon="📋",
    )

    if not inspections:
        render_empty_history()
        return

    # 7) Cards grid
    cols = st.columns(2, gap="medium")
    for i, insp in enumerate(inspections):
        with cols[i % 2]:
            render_history_card(
                inspection=insp,
                index=i,
                on_open=_on_open_report,
                on_delete=_on_delete_request,
                on_duplicate=_on_duplicate,
            )


# ── Filter bar ────────────────────────────────────────────────────────────────
def _render_filters():
    """Render the search + filter controls in a responsive layout."""
    col_search, col_type, col_risk, col_grade, col_sort = st.columns([3, 1.5, 1.5, 1.5, 1.5])

    with col_search:
        search_query = st.text_input(
            "Search",
            value=st.session_state.get("hist_search", ""),
            placeholder="Search by address, inspection ID, or city...",
            label_visibility="collapsed",
            key="hist_search_input",
        )
        st.session_state["hist_search"] = search_query

    with col_type:
        type_options = ["All Types"] + [
            t.title() for t in PROPERTY_TYPES
        ]
        current_type = st.session_state.get("hist_property_type", "")
        idx = 0
        if current_type:
            try:
                idx = type_options.index(current_type.title())
            except ValueError:
                idx = 0
        selected_type = st.selectbox(
            "Property Type",
            type_options,
            index=idx,
            label_visibility="collapsed",
            key="hist_type_input",
        )
        st.session_state["hist_property_type"] = "" if selected_type == "All Types" else selected_type.lower()

    with col_risk:
        risk_options = ["All Risk Levels"] + RISK_LEVELS
        selected_risk = st.selectbox(
            "Risk",
            risk_options,
            index=0,
            label_visibility="collapsed",
            key="hist_risk_input",
        )
        st.session_state["hist_severity"] = (
            "" if selected_risk == "All Risk Levels" else selected_risk.lower()
        )

    with col_grade:
        grade_options = ["All Grades"] + [GRADE_LABELS[g] for g in GRADES]
        selected_grade = st.selectbox(
            "Grade",
            grade_options,
            index=0,
            label_visibility="collapsed",
            key="hist_grade_input",
        )
        if selected_grade == "All Grades":
            st.session_state["hist_grade"] = ""
        else:
            for g, label in GRADE_LABELS.items():
                if label == selected_grade:
                    st.session_state["hist_grade"] = g
                    break

    with col_sort:
        selected_sort_label = st.selectbox(
            "Sort",
            list(SORT_OPTIONS.values()),
            index=DEFAULT_SORT,
            label_visibility="collapsed",
            key="hist_sort_input",
        )
        for key, label in SORT_OPTIONS.items():
            if label == selected_sort_label:
                st.session_state["hist_sort"] = key
                break

    # Date range (collapsible)
    with st.expander("📅 Date Range Filter", expanded=False):
        date_col1, date_col2, date_col3 = st.columns([1, 1, 2])
        with date_col1:
            date_from = st.date_input(
                "From",
                value=None,
                key="hist_date_from_input",
            )
            if date_from:
                st.session_state["hist_date_from"] = date_from.isoformat()
            else:
                st.session_state["hist_date_from"] = ""
        with date_col2:
            date_to = st.date_input(
                "To",
                value=None,
                key="hist_date_to_input",
            )
            if date_to:
                st.session_state["hist_date_to"] = date_to.isoformat()
            else:
                st.session_state["hist_date_to"] = ""
        with date_col3:
            if st.button("🗑️ Clear All Filters", key="clear_filters", type="secondary"):
                _clear_filters()
                st.rerun()

    render_html("<div style='margin-top: 1rem;'></div>")


# ── Helpers ───────────────────────────────────────────────────────────────────
def _simulate_load():
    """Show a brief loading state, then mark as loaded."""
    progress = st.progress(0, text="Loading inspection history...")
    for pct in [20, 50, 80, 100]:
        time.sleep(0.05)
        progress.progress(pct)
    progress.empty()
    st.session_state["history_loaded"] = True
    st.rerun()


def _clear_filters():
    """Reset all filter state."""
    for key in (
        "hist_search", "hist_property_type", "hist_severity",
        "hist_grade", "hist_date_from", "hist_date_to", "hist_sort",
    ):
        st.session_state[key] = "" if key != "hist_sort" else "newest"


def _on_open_report(inspection: dict):
    """Handle View / Open button click."""
    ins_id = inspection.get("inspection_id")
    st.session_state["view_inspection_id"] = ins_id
    st.session_state["current_page"] = "reports"
    st.rerun()


def _on_delete_request(inspection: dict):
    """Handle Delete button click — opens confirmation dialog."""
    ins_id = inspection.get("inspection_id")
    st.session_state["delete_target_id"] = ins_id
    st.session_state[f"confirm_delete_{ins_id}"] = True
    st.rerun()


def _on_duplicate(inspection: dict):
    """Handle Duplicate button click.

    For now, prefills the new-inspection wizard with this property's
    address so the user can run another inspection on the same property.
    """
    st.session_state["prefill_property_address"] = inspection.get("property_address", "")
    st.session_state["prefill_property_type"]  = inspection.get("property_type", "")
    st.session_state["prefill_property_city"]   = inspection.get("property_city", "")
    st.session_state["prefill_property_state"]  = inspection.get("property_state", "")
    render_info_box(
        f"Property details prefilled from {inspection.get('inspection_id', '')}. Continue with the new inspection.",
        box_type="success",
    )
    navigate_to("new_inspection")


def _handle_delete_confirmation(inspections: list):
    """Render and process the delete confirmation dialog."""
    target_id = st.session_state.get("delete_target_id")
    if not target_id:
        return

    dialog_key = f"confirm_delete_{target_id}"
    if not st.session_state.get(dialog_key, False):
        return

    target = next((i for i in inspections if i.get("inspection_id") == target_id), None)
    if not target:
        st.session_state[dialog_key] = False
        st.session_state["delete_target_id"] = None
        return

    with st.container():
        render_html(f"""
            <div style="
                background: rgba(239, 68, 68, 0.08);
                border: 1px solid rgba(239, 68, 68, 0.3);
                border-left: 4px solid #EF4444;
                border-radius: 8px;
                padding: 1rem 1.25rem;
                margin: 1rem 0;
            ">
                <p style="color: #F1F5F9; font-weight: 600; margin: 0 0 0.25rem; font-size: 1rem;">
                    ⚠️ Confirm Deletion
                </p>
                <p style="color: #94A3B8; margin: 0; font-size: 0.9rem;">
                    Delete inspection <strong>{target_id}</strong> at
                    <strong>{target.get('property_address', 'Unknown')}</strong>?
                    This will also remove all images and the AI report.
                </p>
            </div>
            """,
        )

        col_a, col_b, col_c = st.columns([1, 1, 3])
        with col_a:
            if st.button("🗑️ Delete", key=f"confirm_yes_{target_id}", type="primary", use_container_width=True):
                try:
                    delete_inspection(target_id)
                    st.session_state["delete_target_id"] = None
                    st.session_state[dialog_key] = False
                    render_info_box(f"Deleted inspection {target_id}", box_type="success")
                    st.rerun()
                except Exception as exc:
                    render_info_box(f"Delete failed: {exc}", box_type="error")
        with col_b:
            if st.button("Cancel", key=f"confirm_no_{target_id}", type="secondary", use_container_width=True):
                st.session_state["delete_target_id"] = None
                st.session_state[dialog_key] = False
                st.rerun()
