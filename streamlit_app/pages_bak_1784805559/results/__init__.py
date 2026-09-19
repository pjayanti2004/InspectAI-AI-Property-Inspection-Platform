"""Step 5 — Results page for the InspectAI inspection wizard.

Package: ``streamlit_app.pages.results``
Public API: ``render_results()``

Submodules
----------
helpers          Image conversion, list rendering, grade utilities, serialisation.
renderers        Fused finding cards, legacy per-image results, comparison dashboard.
fused            Full fused inspection results view (sections 1-11).
reconstruction   Rebuild dataclass instances from session-state dicts.

All top-level names are re-exported here for backward compatibility with
``from streamlit_app.pages.results import render_results``.
"""
from __future__ import annotations

import streamlit as st

from streamlit_app.ai.fusion_engine import FusedInspection
from streamlit_app.ai.health_engine import PropertyHealthReport
from streamlit_app.ai.inspection_engine import InspectionReport
from streamlit_app.components.ui_components import (
    inject_custom_css,
    init_page_config,
    render_header,
    render_info_box,
    render_result_summary_card,
    render_wizard_stepper,
)
from streamlit_app.report.risk_engine import RiskAssessment
from streamlit_app.report.summary_engine import TimelineEntry
from streamlit_app.utils.constants import WIZARD_STEPS
from streamlit_app.utils.session_manager import (
    SessionKeys,
    get_inspection_data,
    get_inspection_step,
    reset_inspection_flow,
)

# ── Re-export from submodules for backward compatibility ─────────────────────

# helpers
from streamlit_app.pages.results.helpers import (
    _bgr_to_rgb,
    _dict_to_report,
    _get_grade_bg,
    _get_grade_color,
    _render_list,
)
# renderers
from streamlit_app.pages.results.renderers import (
    render_comparison_dashboard,
    render_fused_finding_card,
    render_legacy_results,
)
# fused
from streamlit_app.pages.results.fused import render_fused_results
# reconstruction
from streamlit_app.pages.results.reconstruction import (
    rebuild_fused_inspection,
    rebuild_health_report,
)


# ── Main entry point ────────────────────────────────────────────────────────────


def render_results() -> None:
    """Render the results step with fused or per-image analysis data."""
    inject_custom_css()
    init_page_config()

    inspection_data = get_inspection_data()
    current_step = get_inspection_step()

    if not inspection_data:
        render_info_box(
            "No inspection results found. Please run an inspection first.",
            box_type="warning",
        )
        if st.button("Start New Inspection", use_container_width=True):
            reset_inspection_flow()
            st.session_state["current_page"] = "dashboard"
            st.rerun()
        return

    gemini_error = inspection_data.get("gemini_key_error", "")
    fusion_applied = inspection_data.get("fusion_applied", False)

    if gemini_error:
        render_info_box(
            "Gemini Vision API key not configured. Results shown are from classical CV only. "
            "Add your key to a .env file for AI-powered semantic analysis.",
            box_type="warning",
        )

    # ── Fused mode: display unified property-level results ────────────
    if fusion_applied and inspection_data.get("fused_inspection"):
        fused_dict = inspection_data["fused_inspection"]
        fused = rebuild_fused_inspection(fused_dict)
        render_fused_results(fused, inspection_data)
        return

    # ── Legacy mode: reconstruct reports and display per-image ─────────
    raw_results = inspection_data.get("results", [])
    reports: list[InspectionReport] = []
    for r in raw_results:
        if isinstance(r, dict):
            reports.append(_dict_to_report(r))
        else:
            reports.append(r)

    if not reports:
        render_info_box(
            "No inspection results found. Please run an inspection first.",
            box_type="warning",
        )
        if st.button("Start New Inspection", use_container_width=True):
            reset_inspection_flow()
            st.session_state["current_page"] = "dashboard"
            st.rerun()
        return

    render_legacy_results(reports, inspection_data)
