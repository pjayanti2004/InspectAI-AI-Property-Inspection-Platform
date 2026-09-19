"""Step 5 — Results page for the InspectAI inspection wizard.

Package: ``streamlit_app.views.results``
Public API: ``render_results()``

Submodules
----------
helpers          Image conversion, list rendering, grade utilities, serialisation.
renderers        Fused finding cards, legacy per-image results, comparison dashboard.
fused            Full fused inspection results view (sections 1-11).
reconstruction   Rebuild dataclass instances from session-state dicts.

All top-level names are re-exported here for backward compatibility with
``from streamlit_app.views.results import render_results``.
"""
from __future__ import annotations

import json
import os

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

_TRACE_PATH = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "trace_pipeline.jsonl")
)


def _trace(event, data):
    line = json.dumps({"stage": event, **data})
    print(f"[TRACE] {line}", flush=True)
    with open(_TRACE_PATH, "a", encoding="utf-8") as fh:
        fh.write(line + "\n")

# ── Re-export from submodules for backward compatibility ─────────────────────

# helpers
from streamlit_app.views.results.helpers import (
    _bgr_to_rgb,
    _dict_to_report,
    _get_grade_bg,
    _get_grade_color,
    _render_list,
)
# renderers
from streamlit_app.views.results.renderers import (
    render_comparison_dashboard,
    render_fused_finding_card,
    render_legacy_results,
)
# fused
from streamlit_app.views.results.fused import render_fused_results
# reconstruction
from streamlit_app.views.results.reconstruction import (
    rebuild_fused_inspection,
    rebuild_health_report,
)


# ── Main entry point ────────────────────────────────────────────────────────────


def render_results() -> None:
    """Render the results step with fused or per-image analysis data."""
    import traceback as _tb
    _trace("TP0_function_entry", {
        "session_state_keys": list(st.session_state.keys()),
        "inspection_data_present": "inspection_data" in st.session_state,
    })
    print("[TRACE][results][TP0] render_results() ENTERED", flush=True)
    _tb.print_stack(limit=3)
    inject_custom_css()
    init_page_config()

    inspection_data = get_inspection_data()
    current_step = get_inspection_step()
    print(f"[TRACE][results][TP0a] get_inspection_data() returned type={type(inspection_data).__name__}", flush=True)

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

    # ── TRACE POINT 3: type and keys of inspection_data ────────────────
    print(f"[TRACE][results] type(inspection_data)={type(inspection_data).__name__}")
    print(f"[TRACE][results] inspection_data keys={list(inspection_data.keys())}")
    print(f"[TRACE][results] inspection_data fusion_applied="
          f"{inspection_data.get('fusion_applied')}")
    print(f"[TRACE][results] inspection_data fused_inspection type="
          f"{type(inspection_data.get('fused_inspection')).__name__}")
    if isinstance(inspection_data.get("fused_inspection"), dict):
        fi = inspection_data["fused_inspection"]
        print(f"[TRACE][results] fused_inspection keys={list(fi.keys())}")
        print(f"[TRACE][results] fused_inspection total_images={fi.get('total_images')}")
        print(f"[TRACE][results] fused_inspection total_findings={fi.get('total_findings')}")

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

        # ── TRACE POINT 4: fused_dict right before rebuild ─────────────
        print(f"[TRACE][results][4] fused_dict type={type(fused_dict).__name__}")
        print(f"[TRACE][results][4] fused_dict total_images={fused_dict.get('total_images')}")
        print(f"[TRACE][results][4] fused_dict total_findings={fused_dict.get('total_findings')}")

        fused = rebuild_fused_inspection(fused_dict)

        # ── TRACE POINT 5: fused right after rebuild ────────────────────
        print(f"[TRACE][results][5] fused total_images={fused.total_images}")
        print(f"[TRACE][results][5] fused total_findings={fused.total_findings}")
        print(f"[TRACE][results][5] fused overall_health_score={fused.overall_health_score}")
        print(f"[TRACE][results][5] fused overall_estimated_cost_min="
              f"{fused.overall_estimated_cost_min}")
        print(f"[TRACE][results][5] fused overall_estimated_cost_max="
              f"{fused.overall_estimated_cost_max}")
        print(f"[TRACE][results][5] fused overall_damage_pct={fused.overall_damage_pct}")
        print(f"[TRACE][results][5] fused findings count={len(fused.findings)}")
        print(f"[TRACE][results][5] fused image_rankings count={len(fused.image_rankings)}")
        print(f"[TRACE][results][5] fused executive_summary[:120]="
              f"{fused.executive_summary[:120]}")

        render_fused_results(fused, inspection_data)

        # ── TRACE POINT 6: right before the header is rendered ──────────
        # The header is rendered inside render_fused_results → render_header()
        # We print it here as the last check before any user-facing output
        print(f"[TRACE][results][6] HEADER fused.total_images={fused.total_images}")
        print(f"[TRACE][results][6] HEADER fused.total_findings={fused.total_findings}")
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
