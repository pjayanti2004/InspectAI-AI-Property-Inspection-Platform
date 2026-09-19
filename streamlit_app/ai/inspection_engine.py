"""InspectAI inspection pipeline orchestrator.

Runs the full AI inspection workflow:

    image  →  image_validator  →  opencv_engine  →  gemini_engine  →  merge  →  report

Exposes two entry points:
    - ``run_inspection()``   — run on a single image or list (returns InspectionReport or list).
    - ``run_batch()``        — run on a list of images (returns list of reports).
"""
from __future__ import annotations

import io
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional, Sequence, Union

import numpy as np
import cv2
from PIL import Image

from streamlit_app.ai.gemini_engine import (
    GeminiAnalysis,
    analyze_image_with_gemini,
    build_prompt,
    configure_gemini,
)
from streamlit_app.utils.image_optimizer import optimize_for_ai
from streamlit_app.utils.performance import PerformanceTracker
from streamlit_app.ai.image_validator import validate_image
from streamlit_app.ai.opencv_engine import (
    DEFAULT_MIN_CONTOUR_AREA,
    DamageMetrics,
    run_full_analysis,
)
from streamlit_app.utils.exceptions import (
    AIServiceError,
    ConfigurationError,
)
from streamlit_app.utils.logger import get_logger

# ── Logging ──────────────────────────────────────────────────────────────────

_logger = get_logger(__name__)

# ── Report Type ──────────────────────────────────────────────────────────────


@dataclass
class InspectionReport:
    """Complete inspection result for a single image."""

    file_name: str = ""
    image_width: int = 0
    image_height: int = 0
    file_size_mb: float = 0.0
    validation_passed: bool = True
    validation_error: str = ""
    damage_percentage: float = 0.0
    damage_area_px: int = 0
    image_area_px: int = 0
    contour_count: int = 0
    largest_damage_area_px: int = 0
    damage_type: str = "N/A"
    severity: str = "N/A"
    confidence: int = 0
    possible_causes: list[str] = field(default_factory=list)
    repair_steps: list[str] = field(default_factory=list)
    recommended_professional: str = "N/A"
    estimated_cost_range: str = "N/A"
    urgency: str = "N/A"
    prevention_tips: list[str] = field(default_factory=list)
    processed_image: Optional[np.ndarray] = None
    damage_mask: Optional[np.ndarray] = None
    heatmap: Optional[np.ndarray] = None
    overlay_image: Optional[np.ndarray] = None
    measurement_report: Optional[Any] = None
    cv_processing_time_sec: float = 0.0
    gemini_processing_time_sec: float = 0.0
    total_processing_time_sec: float = 0.0
    gemini_skipped: bool = False
    gemini_error: str = ""

    def to_dict(self) -> dict:
        return {
            "file_name": self.file_name,
            "image_width": self.image_width,
            "image_height": self.image_height,
            "file_size_mb": self.file_size_mb,
            "validation_passed": self.validation_passed,
            "validation_error": self.validation_error,
            "damage_percentage": self.damage_percentage,
            "damage_area_px": self.damage_area_px,
            "image_area_px": self.image_area_px,
            "contour_count": self.contour_count,
            "largest_damage_area_px": self.largest_damage_area_px,
            "damage_type": self.damage_type,
            "severity": self.severity,
            "confidence": self.confidence,
            "possible_causes": self.possible_causes,
            "repair_steps": self.repair_steps,
            "recommended_professional": self.recommended_professional,
            "estimated_cost_range": self.estimated_cost_range,
            "urgency": self.urgency,
            "prevention_tips": self.prevention_tips,
            "cv_processing_time_sec": self.cv_processing_time_sec,
            "gemini_processing_time_sec": self.gemini_processing_time_sec,
            "total_processing_time_sec": self.total_processing_time_sec,
            "gemini_skipped": self.gemini_skipped,
            "gemini_error": self.gemini_error,
        }


# ── Individual stage functions ───────────────────────────────────────────────


def stage_validate(
    source, file_name: str = "", file_size_bytes: Optional[int] = None,
) -> tuple:
    """Stage 1: Validate and load the image."""
    t0 = time.perf_counter()
    src_type = type(source).__name__
    src_info = ""
    if isinstance(source, np.ndarray):
        src_info = f"ndarray shape={source.shape}"
    elif hasattr(source, "name"):
        src_info = f"file_name={getattr(source, 'name', '?')} size={getattr(source, 'size', '?')}"
    else:
        src_info = f"type={src_type}"
    result = validate_image(source, file_name=file_name, file_size_bytes=file_size_bytes)
    cv_img = None
    pil_img = None

    if result.is_valid:
        if isinstance(source, np.ndarray):
            cv_img = source.copy()
            pil_img = Image.fromarray(cv_img)
        elif isinstance(source, Image.Image):
            pil_img = source.copy()
            cv_img = np.array(pil_img)
        elif isinstance(source, bytes):
            pil_img = Image.open(io.BytesIO(source))
            pil_img.load()
            cv_img = np.array(pil_img)
        else:
            pil_img = Image.open(source)
            pil_img.load()
            cv_img = np.array(pil_img)

    elapsed = round(time.perf_counter() - t0, 3)
    return result, cv_img, pil_img


def stage_opencv(
    cv_image: np.ndarray, min_contour_area: int = DEFAULT_MIN_CONTOUR_AREA,
    file_name: str = "",
) -> InspectionReport:
    """Stage 2: Run classical CV pipeline. Returns an InspectionReport."""
    t0 = time.perf_counter()
    processed, mask, overlay, metrics, measurement, defects, severity_report = run_full_analysis(
        cv_image, min_contour_area=min_contour_area
    )
    elapsed = round(time.perf_counter() - t0, 3)

    report = InspectionReport(
        file_name=file_name,
        image_width=int(cv_image.shape[1]),
        image_height=int(cv_image.shape[0]),
        damage_percentage=float(metrics.damage_percentage) if metrics else 0.0,
        damage_area_px=int(metrics.damage_area_px) if metrics else 0,
        image_area_px=int(metrics.image_area_px) if metrics else 0,
        contour_count=int(metrics.contour_count) if metrics else 0,
        largest_damage_area_px=int(metrics.largest_damage_area_px) if metrics else 0,
        processed_image=processed,
        damage_mask=mask,
        overlay_image=overlay,
        cv_processing_time_sec=elapsed,
        total_processing_time_sec=elapsed,
        measurement_report=measurement,
    )
    return report, defects, severity_report


def stage_gemini(
    cv_image: np.ndarray, prompt: Optional[str] = None, api_key: Optional[str] = None,
) -> InspectionReport:
    """Stage 3: Run Gemini Vision analysis. Returns an InspectionReport.

    When no Gemini API key is configured or the API call fails, returns a
    report with ``gemini_skipped=True`` and ``gemini_error`` populated.
    """
    t0 = time.perf_counter()
    gemini_skipped = False
    gemini_error = ""
    analysis: Optional[GeminiAnalysis] = None

    pil_image: Image.Image
    if isinstance(cv_image, Image.Image):
        pil_image = cv_image
    else:
        pil_image = Image.fromarray(cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB))

    try:
        prompt_text = prompt or build_prompt()
        result = analyze_image_with_gemini(pil_image, prompt_text)
        analysis = GeminiAnalysis.from_response(result)
    except (AIServiceError, ConfigurationError) as exc:
        analysis = GeminiAnalysis(raw_response=str(exc))
        gemini_skipped = True
        gemini_error = str(exc)
    except Exception as exc:
        _logger.exception("Unexpected Gemini error.")
        analysis = GeminiAnalysis(raw_response=str(exc))
        gemini_skipped = True
        gemini_error = str(exc)

    elapsed = round(time.perf_counter() - t0, 3)
    h, w = (int(pil_image.height), int(pil_image.width)) if hasattr(pil_image, "height") else (0, 0)

    return InspectionReport(
        file_name="",
        image_width=w,
        image_height=h,
        gemini_processing_time_sec=elapsed,
        gemini_skipped=gemini_skipped,
        gemini_error=gemini_error,
        damage_type=analysis.damage_type if analysis else "N/A",
        severity=analysis.severity if analysis else "N/A",
        confidence=analysis.confidence if analysis else 0,
        possible_causes=list(analysis.possible_causes) if analysis else [],
        repair_steps=list(analysis.repair_steps) if analysis else [],
        recommended_professional=analysis.recommended_professional if analysis else "N/A",
        estimated_cost_range=analysis.estimated_cost_range if analysis else "N/A",
        urgency=analysis.urgency if analysis else "Low",
        prevention_tips=list(analysis.prevention_tips) if analysis else [],
    )


def merge_results(
    reports_or_cv_elapsed,
    cv_elapsed: float = 0.0,
    gemini_elapsed: float = 0.0,
    validation=None,
    cv_image: Optional[np.ndarray] = None,
    metrics=None,
    processed: Optional[np.ndarray] = None,
    mask: Optional[np.ndarray] = None,
    overlay: Optional[np.ndarray] = None,
    gemini: Optional[GeminiAnalysis] = None,
    file_name: str = "",
    file_size_mb: float = 0.0,
    measurement_report: Optional[Any] = None,
    opencv_defects: Optional[list[dict[str, Any]]] = None,
    opencv_severity_report: Optional[dict[str, Any]] = None,
) -> InspectionReport:
    """Merge stage outputs into a single InspectionReport.

    Two modes:
      - List mode: pass a list of InspectionReport objects.
      - Kwarg mode: pass individual stage outputs (used internally by run_inspection).
    """
    # ── List mode ────────────────────────────────────────────────────────
    if isinstance(reports_or_cv_elapsed, list):
        if reports_or_cv_elapsed and isinstance(reports_or_cv_elapsed[0], InspectionReport):
            reports = reports_or_cv_elapsed
            first = reports[0]
            return InspectionReport(
                file_name=first.file_name if first.file_name else (file_name or ""),
                image_width=first.image_width,
                image_height=first.image_height,
                file_size_mb=first.file_size_mb or file_size_mb,
                validation_passed=all(r.validation_passed for r in reports),
                validation_error="; ".join(r.validation_error for r in reports if r.validation_error),
                damage_percentage=sum(r.damage_percentage for r in reports),
                damage_area_px=sum(r.damage_area_px for r in reports),
                image_area_px=first.image_area_px,
                contour_count=sum(r.contour_count for r in reports),
                largest_damage_area_px=max(r.largest_damage_area_px for r in reports),
                damage_type=gemini.damage_type if gemini else first.damage_type,
                severity=gemini.severity if gemini else first.severity,
                confidence=gemini.confidence if gemini else first.confidence,
                possible_causes=list(gemini.possible_causes) if gemini else list(first.possible_causes),
                repair_steps=list(gemini.repair_steps) if gemini else list(first.repair_steps),
                recommended_professional=gemini.recommended_professional if gemini else first.recommended_professional,
                estimated_cost_range=gemini.estimated_cost_range if gemini else first.estimated_cost_range,
                urgency=gemini.urgency if gemini else first.urgency,
                prevention_tips=list(gemini.prevention_tips) if gemini else list(first.prevention_tips),
                processed_image=processed,
                damage_mask=mask,
                overlay_image=overlay,
                measurement_report=measurement_report,
                cv_processing_time_sec=round(sum(r.cv_processing_time_sec for r in reports), 3),
                gemini_processing_time_sec=round(sum(r.gemini_processing_time_sec for r in reports), 3),
                total_processing_time_sec=round(
                    sum(r.cv_processing_time_sec + r.gemini_processing_time_sec for r in reports), 3
                ),
                gemini_skipped=gemini.gemini_skipped if gemini else any(r.gemini_skipped for r in reports),
                gemini_error=gemini.gemini_error if gemini else "",
            )
        return InspectionReport()

    # ── Kwarg mode (internal) ────────────────────────────────────────────
    cv_elapsed = reports_or_cv_elapsed  # first positional is cv_elapsed when not a list

    w = int(cv_image.shape[1]) if cv_image is not None else 0
    h = int(cv_image.shape[0]) if cv_image is not None else 0

    dmg_pct = float(metrics.damage_percentage) if metrics else 0.0
    dmg_area = int(metrics.damage_area_px) if metrics else 0
    img_area = int(metrics.image_area_px) if metrics else 0
    contours = int(metrics.contour_count) if metrics else 0
    largest = int(metrics.largest_damage_area_px) if metrics else 0

    g = gemini if gemini is not None else GeminiAnalysis()
    gemini_skipped = gemini is None
    gemini_error = g.raw_response if (not g.has_damage and g.raw_response) else ""

    val_passed = getattr(validation, "is_valid", True)
    val_error = getattr(validation, "error", "") or ""

    # ── Fallback: when Gemini returns zero findings, derive fields from OpenCV ──
    _cv_pct = float(metrics.damage_percentage) if metrics else 0.0
    _cv_contours = int(metrics.contour_count) if metrics else 0
    _use_cv = not g.has_damage and _cv_contours > 0

    def _cv_damage_type(defects: list[dict[str, Any]]) -> str:
        """Derive a semantic damage type from top OpenCV defect."""
        if not defects:
            return "Surface Defect"
        top = max(defects, key=lambda d: d["confidence"])
        return top.get("damage_type", "Surface Defect")

    def _cv_repair_steps(defects: list[dict[str, Any]], severity: str) -> list[str]:
        """Professional inspection repair steps derived from defect damage types."""
        types = {d.get("damage_type", "") for d in defects}
        steps: list[str] = []
        if "Crack" in types or "Surface Crack" in types:
            steps.append("Inspect all identified cracks and seal using appropriate crack-filler material. "
                         "Clean the area thoroughly before application to ensure proper adhesion.")
        if "Water Damage" in types or "Moisture Damage" in types:
            steps.append("Identify and address the source of moisture ingress. "
                         "Dry the affected area completely, then apply a moisture-resistant primer "
                         "before repainting.")
        if "Paint Peeling" in types:
            steps.append("Remove all loose and peeling paint from the affected area. "
                         "Sand the surface smooth, prime with a suitable bonding primer, "
                         "and repaint with a matching finish.")
        if "Spalling" in types:
            steps.append("Remove loose and spalled concrete or plaster from the affected area. "
                         "Apply a bonding agent and repair with a suitable patching compound. "
                         "Consult a structural engineer for extensive spalling.")
        if "Mold / Fungus" in types:
            steps.append("Treat affected surfaces with an appropriate fungicidal wash. "
                         "Ensure the area is fully dry and well-ventilated. "
                         "Address any underlying dampness to prevent recurrence.")
        if "Rust" in types:
            steps.append("Remove all rust using a wire brush or appropriate abrasive method. "
                         "Apply a rust-inhibiting primer and protective coating. "
                         "Inspect for structural impact if reinforcement bars are exposed.")
        if "Surface Stain" in types:
            steps.append("Clean the stained surface using appropriate cleaning agents. "
                         "Assess whether the stain indicates an active issue (e.g. water ingress).")
        if not steps:
            steps = [
                "Inspect all identified regions and assess the extent of damage.",
                "Consult a qualified structural engineer or licensed contractor for a detailed assessment "
                "and professional repair recommendations.",
            ]
        steps.append("Schedule a follow-up inspection to monitor the condition of repaired areas.")
        return steps

    if _use_cv:
        _defects = opencv_defects or []
        _sev_rpt = opencv_severity_report or {}

        # Average confidence from actual per-defect scores
        if _defects:
            _avg_conf = int(sum(d["confidence"] for d in _defects) / len(_defects))
            _top = max(_defects, key=lambda d: d["confidence"])

            # Damage type: semantic classification from top defect
            _dt = _cv_damage_type(_defects)

            # Severity: use the top defect's severity, clamped to damage pct
            _sev = _top.get("severity", "Low")
            if _sev == "Minimal":
                _sev = "Low"
            if _cv_pct >= 5.0:
                _sev = max(_sev, "High")
            elif _cv_pct >= 2.0 and _sev not in ("High",):
                _sev = max(_sev, "Medium")

            _report_damage_type = _dt
            _report_severity = _sev
            _report_confidence = max(_avg_conf, min(100, int(_cv_pct * 10 + _cv_contours * 3)))

            # Causes: frame from defect severity distribution
            _by_sev = _sev_rpt.get("by_severity", {})
            _high_n = _by_sev.get("High", 0)
            _med_n  = _by_sev.get("Medium", 0)
            _report_causes = [f"AI analysis detected {_cv_contours} damage region(s) "
                              f"covering {_cv_pct:.1f}% of the image area "
                              f"({_high_n} high-severity, {_med_n} medium)."]

            # Repair steps: professional language derived from damage types
            _report_steps = _cv_repair_steps(_defects, _sev)

            _report_pro = "Licensed contractor (recommended)"
            _cost_min = _sev_rpt.get("estimated_cost_min")
            _cost_max = _sev_rpt.get("estimated_cost_max")
            if _cost_min and _cost_max:
                _report_cost = f"₹{_cost_min:,} — ₹{_cost_max:,} (estimate)"
            else:
                _report_cost = "Estimate pending professional assessment"

            _report_urgency = _sev if _sev in ("High", "Critical") else "Moderate"
            _report_tips = ["Schedule regular structural inspections.",
                            "Monitor detected regions for progression and address early."]
        else:
            # Defects list empty despite contours > 0 — use minimal fallback
            _report_damage_type = "Surface Defect"
            _report_severity = "Low"
            _report_confidence = min(100, int(_cv_pct * 10 + _cv_contours * 3))
            _report_causes = [f"AI analysis detected {_cv_contours} damage region(s) "
                              f"covering {_cv_pct:.1f}% of the image area."]
            _report_steps = ["Inspect detected regions manually.",
                             "Consult a structural engineer for assessment."]
            _report_pro = "Licensed contractor (recommended)"
            _report_cost = "Estimate pending professional assessment"
            _report_urgency = "Moderate"
            _report_tips = ["Schedule regular structural inspections.",
                            "Monitor detected regions for progression and address early."]
    else:
        _report_damage_type = g.damage_type
        _report_severity = g.severity
        _report_confidence = g.confidence
        _report_causes = list(g.possible_causes)
        _report_steps = list(g.repair_steps)
        _report_pro = g.recommended_professional
        _report_cost = g.estimated_cost_range
        _report_urgency = g.urgency
        _report_tips = list(g.prevention_tips)

    report = InspectionReport(
        file_name=file_name,
        image_width=w,
        image_height=h,
        file_size_mb=round(file_size_mb, 2),
        validation_passed=val_passed,
        validation_error=val_error,
        damage_percentage=dmg_pct,
        damage_area_px=dmg_area,
        image_area_px=img_area,
        contour_count=contours,
        largest_damage_area_px=largest,
        damage_type=_report_damage_type,
        severity=_report_severity,
        confidence=_report_confidence,
        possible_causes=_report_causes,
        repair_steps=_report_steps,
        recommended_professional=_report_pro,
        estimated_cost_range=_report_cost,
        urgency=_report_urgency,
        prevention_tips=_report_tips,
        processed_image=processed,
        damage_mask=mask,
        overlay_image=overlay,
        cv_processing_time_sec=round(cv_elapsed, 3),
        gemini_processing_time_sec=round(gemini_elapsed, 3),
        total_processing_time_sec=round(cv_elapsed + gemini_elapsed, 3),
        gemini_skipped=gemini_skipped,
        gemini_error=gemini_error,
        measurement_report=measurement_report,
    )
    return report


# ── Top-level entry points ───────────────────────────────────────────────────


def run_inspection(
    sources,
    file_name: str = "",
    file_size_bytes: Optional[int] = None,
    api_key: Optional[str] = None,
    min_contour_area: int = DEFAULT_MIN_CONTOUR_AREA,
):
    """Run the full AI inspection pipeline.

    Accepts a single image source or a list of sources.
    Returns InspectionReport for a single source, list[InspectionReport] for a list.
    Empty list → [].
    """
    if isinstance(sources, list):
        if not sources:
            return []
        names = [file_name] if file_name else None
        sizes = [file_size_bytes] if file_size_bytes else None
        return run_batch(sources, file_names=names, file_sizes=sizes, api_key=api_key)

    source = sources
    tracker = PerformanceTracker.get()

    with tracker.stage("optimize"):
        optimized = optimize_for_ai(source, file_name=file_name)

    with tracker.stage("validate"):
        validation, cv_image, _ = stage_validate(optimized, file_name, file_size_bytes)

    validation_passed = bool(getattr(validation, "is_valid", True))
    validation_error = getattr(validation, "error", "") or ""
    if not validation_passed:
        return merge_results(
            0.0,               # required positional arg (reports_or_cv_elapsed)
            cv_elapsed=0.0,
            gemini_elapsed=0.0,
            validation=validation,
            cv_image=None,
            metrics=None,
            processed=None,
            mask=None,
            overlay=None,
            gemini=None,
            file_name=file_name,
            file_size_mb=(file_size_bytes or 0) / (1024 * 1024),
        )

    file_size_mb = (file_size_bytes or 0) / (1024 * 1024)

    cv_elapsed = 0.0
    measurement = None
    ocv_report = None
    opencv_defects: list[dict[str, Any]] = []
    opencv_severity: dict[str, Any] = {}
    try:
        with tracker.stage("opencv"):
            ocv_report, opencv_defects, opencv_severity = stage_opencv(
                optimized, min_contour_area=min_contour_area, file_name=file_name
            )
            cv_elapsed = ocv_report.cv_processing_time_sec
            measurement = ocv_report.measurement_report
    except Exception:
        ocv_report = None

    effective_file_name = ocv_report.file_name if ocv_report and ocv_report.file_name else file_name

    gemini_result = None
    gemini_elapsed = 0.0
    gemini_skipped = False
    gemini_error = ""

    try:
        with tracker.stage("gemini"):
            gemini_report = stage_gemini(optimized, api_key=api_key)
            gemini_result = GeminiAnalysis(
                damage_type=gemini_report.damage_type,
                severity=gemini_report.severity,
                confidence=gemini_report.confidence,
                possible_causes=list(gemini_report.possible_causes),
                repair_steps=list(gemini_report.repair_steps),
                recommended_professional=gemini_report.recommended_professional,
                estimated_cost_range=gemini_report.estimated_cost_range,
                urgency=gemini_report.urgency,
                prevention_tips=list(gemini_report.prevention_tips),
            )
            gemini_elapsed = gemini_report.gemini_processing_time_sec
            gemini_skipped = gemini_report.gemini_skipped
            gemini_error = gemini_report.gemini_error
    except (ValueError, Exception) as exc:
        gemini_skipped = True
        gemini_error = str(exc)
        gemini_result = GeminiAnalysis()

    with tracker.stage("merge"):
        ocv_metrics = None
        if ocv_report is not None:
            ocv_metrics = DamageMetrics(
                damage_percentage=float(ocv_report.damage_percentage),
                damage_area_px=int(ocv_report.damage_area_px),
                image_area_px=int(ocv_report.image_area_px),
                contour_count=int(ocv_report.contour_count),
                largest_damage_area_px=int(ocv_report.largest_damage_area_px),
            )
        return merge_results(
            round(cv_elapsed, 3),
            cv_elapsed=round(cv_elapsed, 3),
            gemini_elapsed=round(gemini_elapsed, 3),
            validation=validation,
            cv_image=optimized,
            metrics=ocv_metrics,
            processed=ocv_report.processed_image if ocv_report else None,
            mask=ocv_report.damage_mask if ocv_report else None,
            overlay=ocv_report.overlay_image if ocv_report else None,
            gemini=gemini_result,
            file_name=effective_file_name,
            file_size_mb=file_size_mb,
            measurement_report=measurement,
            opencv_defects=opencv_defects,
            opencv_severity_report=opencv_severity,
        )


def run_batch(
    sources: Sequence,
    file_names: Optional[list[str]] = None,
    file_sizes: Optional[list[int]] = None,
    api_key: Optional[str] = None,
) -> list:
    """Run inspection on multiple images."""
    n = len(sources)
    names = file_names or [f"image_{i+1}" for i in range(n)]
    sizes = file_sizes or [None] * n

    return [
        run_inspection(src, fn, sz, api_key=api_key)
        for src, fn, sz in zip(sources, names, sizes)
    ]
