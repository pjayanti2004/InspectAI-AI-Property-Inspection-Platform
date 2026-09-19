"""Step 4 — Processing page for the InspectAI inspection wizard.

Runs the real AI inspection pipeline:
    Image Validation → Per-Image Analysis (OpenCV + Gemini) → Fusion → Results

Shows a 5-stage animated loading screen while processing occurs in real time.

After all images are analysed individually, the fusion_engine merges
per-image findings into a single unified inspection with:
  - Deduplicated findings
  - Image priority ranking
  - Executive summary
  - Repair timeline
  - Maintenance tips
"""
from __future__ import annotations

import time

import streamlit as st

from streamlit_app.ai.fusion_engine import FusedInspection, fuse_reports
from streamlit_app.ai.health_engine import health_report_to_dict
from streamlit_app.ai.comparison_engine import comparison_report_to_dict
from streamlit_app.ai.inspection_engine import (
    run_inspection,
)
from streamlit_app.components.ui_components import (
    inject_custom_css,
    init_page_config,
    render_header,
    render_html,
    render_info_box,
    render_wizard_stepper,
)
from streamlit_app.utils.constants import (
    PROCESSING_STAGES,
    WIZARD_STEPS,
)
from streamlit_app.utils.session_manager import (
    get_property_data,
    get_uploaded_files,
    get_inspection_step,
    set_inspection_step,
    SessionKeys,
)

# How long to show each stage label before moving on
# (actual AI work happens in the background during each phase)
STAGE_DISPLAY_DURATIONS = [0.5, 1.0, 2.5, 2.5, 1.0]


def _streamlit_file_to_np(file) -> "np.ndarray":
    """Convert a Streamlit UploadedFile to a numpy array (RGB)."""
    import io
    import numpy as np
    from PIL import Image

    file.seek(0)
    pil_img = Image.open(io.BytesIO(file.read()))
    pil_img = pil_img.convert("RGB")
    return np.array(pil_img)


def _streamlit_file_to_bytes(file) -> bytes:
    """Get raw bytes from a Streamlit UploadedFile."""
    file.seek(0)
    return file.read()


def render_processing():
    """Render the processing screen and run the AI pipeline.

    Flow:
        1. Validate uploaded files exist.
        2. Show animated stages while running AI per-image analysis.
        3. Fuse all reports into a single unified inspection.
        4. Store results (raw reports + fused inspection) in session state.
        5. Navigate to results page.
    """
    inject_custom_css()
    init_page_config()

    # ── Guard: must have data ─────────────────────────────────────────
    property_data = get_property_data()
    uploaded_files = get_uploaded_files()

    if not property_data or not uploaded_files:
        render_info_box(
            "No inspection data found. Please complete the previous steps first.",
            box_type="warning",
        )
        if st.button("Start New Inspection", use_container_width=True):
            set_inspection_step(1)
            st.session_state["current_page"] = "new_inspection"
            st.rerun()
        return

    current_step = get_inspection_step()
    render_header(
        title="Processing Inspection",
        subtitle="Step 4 of 5 — AI is analyzing your property",
        icon="⚙️",
    )
    render_wizard_stepper(current_step=current_step, steps=WIZARD_STEPS)
    render_html("<div class='mt-4'></div>")

    # ── Animated Stages ───────────────────────────────────────────────
    col_left, col_center, col_right = st.columns([1, 2, 1])

    with col_center:
        render_html(
            """
            <div style="text-align: center; padding: 2rem 0;">
                <div style="
                    width: 90px;
                    height: 90px;
                    margin: 0 auto 1.5rem;
                    border: 4px solid rgba(51, 65, 85, 0.4);
                    border-top: 4px solid #4F46E5;
                    border-right: 4px solid #06B6D4;
                    border-radius: 50%;
                    animation: spin 1.2s linear infinite;
                "></div>
                <h3 style="margin: 0 0 0.5rem; color: #F1F5F9;">Analyzing Your Property</h3>
                <p style="color: #94A3B8; margin: 0; font-size: 0.9rem;">
                    Please wait while our AI examines your images...
                </p>
            </div>
            """,
        )

        progress_bar = st.progress(0)
        stage_text = st.empty()

        total_stages = len(PROCESSING_STAGES)

    # ── Run the AI Pipeline ───────────────────────────────────────────
    # Process each image through the full pipeline individually
    all_reports: list = []
    gemini_key_error: str | None = None
    files_list = list(uploaded_files)

    for i, stage_name in enumerate(PROCESSING_STAGES):
        progress = (i + 1) / total_stages
        progress_bar.progress(progress)

        with col_center:
            stage_text.markdown(
                f"""
                <div style="
                    text-align: center;
                    padding: 0.75rem;
                    background: rgba(79, 70, 229, 0.08);
                    border: 1px solid rgba(79, 70, 229, 0.2);
                    border-radius: 8px;
                    margin-top: 1rem;
                ">
                    <div style="
                        display: inline-flex;
                        align-items: center;
                        gap: 0.5rem;
                        color: #F1F5F9;
                        font-weight: 600;
                    ">
                        <span style="
                            display: inline-block;
                            width: 8px;
                            height: 8px;
                            background: #4F46E5;
                            border-radius: 50%;
                            animation: pulse 1.5s ease-in-out infinite;
                        "></span>
                        {stage_name}
                    </div>
                </div>
                """,
            )

        # ── Actual AI work ─────────────────────────────────────────────
        if i == 0:
            # Stage 1: Image Validation — quick pass through validator
            for f in files_list:
                try:
                    from streamlit_app.ai.image_validator import validate_image
                    _raw = _streamlit_file_to_bytes(f)
                    result = validate_image(_raw, file_name=f.name, file_size_bytes=len(_raw))
                    if not result.is_valid:
                        render_info_box(
                            f"Image '{f.name}' failed validation: {result.error}",
                            box_type="error",
                        )
                except Exception:
                    pass  # Will be caught during full pipeline

        elif i == 1:
            # Stage 2: Per-image AI analysis (OpenCV + Gemini)
            for f in files_list:
                try:
                    _np = _streamlit_file_to_np(f)
                    _raw = _streamlit_file_to_bytes(f)
                    report = run_inspection(
                        sources=_np,
                        file_name=f.name,
                        file_size_bytes=len(_raw),
                    )
                    all_reports.append(report)
                except ValueError as exc:
                    # Gemini API key not configured
                    gemini_key_error = str(exc)
                    _np = _streamlit_file_to_np(f)
                    _raw = _streamlit_file_to_bytes(f)
                    report = run_inspection(
                        sources=_np,
                        file_name=f.name,
                        file_size_bytes=len(_raw),
                    )
                    all_reports.append(report)
                except Exception as exc:
                    render_info_box(
                        f"Failed to process '{f.name}': {exc}",
                        box_type="error",
                    )

        elif i == 2:
            # Stage 3: Damage detection already done
            pass

        elif i == 3:
            # Stage 4: Heatmap generation already done
            pass

        # Pause so the user sees the stage name
        duration = (
            STAGE_DISPLAY_DURATIONS[i]
            if i < len(STAGE_DISPLAY_DURATIONS)
            else 1.0
        )
        time.sleep(duration)

    # ── Step 5: Fuse all reports into a unified inspection ────────────
    fused = fuse_reports(all_reports)

    # ── Persist results ───────────────────────────────────────────────
    progress_bar.progress(1.0)
    with col_center:
        finding_count = fused.total_findings
        render_html(f"""
            <div style="
                text-align: center;
                padding: 0.75rem;
                background: rgba(16, 185, 129, 0.1);
                border: 1px solid rgba(16, 185, 129, 0.3);
                border-radius: 8px;
                margin-top: 1rem;
            ">
                <div style="color: #10B981; font-weight: 700;">
                    Analysis Complete — {finding_count} finding{'s' if finding_count != 1 else ''} detected
                </div>
            </div>
            """,
        )

    time.sleep(0.5)

    # ── Persist results ───────────────────────────────────────────────
    # Convert reports to serialisable dicts (strip numpy arrays) for storage
    serialisable = [r.to_dict() for r in all_reports]

    # Serialise the fused inspection for session state storage
    fused_dict = _serialise_fused(fused)

    st.session_state[SessionKeys.INSPECTION_DATA] = {
        "id": _generate_inspection_id(),
        "property_data": property_data,
        "results": serialisable,
        "fused_inspection": fused_dict,   # serialised FusedInspection
        "image_count": len(files_list),
        "image_names": [f.name for f in files_list],
        "status": "Completed",
        "gemini_key_error": gemini_key_error or "",
        "fusion_applied": True,
    }

    set_inspection_step(5)
    st.session_state["current_page"] = "results"
    st.rerun()


def _serialise_fused(fused: FusedInspection) -> dict:
    """Serialise a FusedInspection to a plain dict for session state storage.

    Numpy arrays from source reports are preserved by keeping the
    serialisable report dicts alongside the fused metadata.
    """
    return {
        "overall_damage_pct": fused.overall_damage_pct,
        "overall_confidence": fused.overall_confidence,
        "overall_severity": fused.overall_severity,
        "overall_health_score": fused.overall_health_score,
        "overall_estimated_cost_min": fused.overall_estimated_cost_min,
        "overall_estimated_cost_max": fused.overall_estimated_cost_max,
        "total_repair_area_px": fused.total_repair_area_px,
        "avg_crack_width_px": fused.avg_crack_width_px,
        "findings": [
            {
                "damage_type": f.damage_type,
                "severity": f.severity,
                "confidence": f.confidence,
                "damage_pct": f.damage_pct,
                "affected_images": f.affected_images,
                "image_count": f.image_count,
                "possible_causes": f.possible_causes,
                "repair_steps": f.repair_steps,
                "recommended_professional": f.recommended_professional,
                "estimated_cost_range": f.estimated_cost_range,
                "urgency": f.urgency,
                "prevention_tips": f.prevention_tips,
            }
            for f in fused.findings
        ],
        "image_rankings": [
            {
                "rank": r.rank,
                "file_name": r.file_name,
                "damage_pct": r.damage_pct,
                "severity": r.severity,
                "damage_type": r.damage_type,
                "confidence": r.confidence,
            }
            for r in fused.image_rankings
        ],
        "executive_summary": fused.executive_summary,
        "property_summary": fused.property_summary,
        "inspection_conclusion": fused.inspection_conclusion,
        "timeline": [
            {
                "bucket": t.bucket,
                "findings_count": len(t.findings),
                "color": t.color,
            }
            for t in fused.timeline
        ],
        "maintenance_tips": fused.maintenance_tips,
        "total_images": fused.total_images,
        "total_findings": fused.total_findings,
        "processing_time_sec": fused.processing_time_sec,
        "risk_assessment": {
            "overall_risk_score": fused.risk_assessment.overall_risk_score if fused.risk_assessment else 0.0,
            "risk_level": fused.risk_assessment.risk_level if fused.risk_assessment else "Low",
            "risk_color": fused.risk_assessment.risk_color if fused.risk_assessment else "#10B981",
            "risk_bg": fused.risk_assessment.risk_bg if fused.risk_assessment else "rgba(16,185,129,0.15)",
            "health_score": fused.risk_assessment.health_score if fused.risk_assessment else 100,
            "total_findings": fused.risk_assessment.total_findings if fused.risk_assessment else 0,
            "critical_count": fused.risk_assessment.critical_count if fused.risk_assessment else 0,
            "high_count": fused.risk_assessment.high_count if fused.risk_assessment else 0,
            "medium_count": fused.risk_assessment.medium_count if fused.risk_assessment else 0,
            "low_count": fused.risk_assessment.low_count if fused.risk_assessment else 0,
            "avg_damage_pct": fused.risk_assessment.avg_damage_pct if fused.risk_assessment else 0.0,
            "max_damage_pct": fused.risk_assessment.max_damage_pct if fused.risk_assessment else 0.0,
            "estimated_cost_min": fused.risk_assessment.estimated_cost_min if fused.risk_assessment else 0,
            "estimated_cost_max": fused.risk_assessment.estimated_cost_max if fused.risk_assessment else 0,
        },
        "source_reports_serialised": [r.to_dict() for r in fused.source_reports],
        "health_report": health_report_to_dict(fused.health_report) if fused.health_report else None,
        "comparison_report": comparison_report_to_dict(fused.comparison_report) if fused.comparison_report else None,
    }


def _generate_inspection_id() -> str:
    """Generate a unique inspection ID like INS-2026-0043."""
    import datetime, random
    today = datetime.date.today()
    suffix = random.randint(1000, 9999)
    return f"INS-{today.year}-{suffix}"