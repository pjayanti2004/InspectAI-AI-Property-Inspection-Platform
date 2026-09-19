"""Inspection pipeline debug trace -- real-contour test image."""
from __future__ import annotations

import io
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
from PIL import Image, ImageDraw

# ── Build test image with actual dark features (crack-like) ──────────────────
img = Image.new("RGB", (2000, 1500), color=(200, 190, 175))  # wall color
draw = ImageDraw.Draw(img)

# Draw several dark crack-like lines + rectangles
features = [
    # (bbox, fill) -- x,y,w,h, color
    ((100, 200, 300, 8), (40, 30, 20)),       # horizontal crack
    ((500, 400, 8, 250), (30, 25, 15)),        # vertical crack
    ((900, 600, 200, 6), (50, 40, 30)),        # thin horizontal crack
    ((1300, 100, 12, 400), (35, 28, 18)),      # longer vertical crack
    ((600, 800, 150, 150), (60, 55, 45)),      # damp patch (rectangle)
    ((1500, 900, 180, 100), (45, 38, 28)),     # another damp area
]
for (x, y, w, h), color in features:
    draw.rectangle([x, y, x+w, y+h], fill=color)

_buf = io.BytesIO()
img.save(_buf, format="JPEG", quality=90)
_raw_bytes = _buf.getvalue()
_source_arr = np.array(img)  # RGB

print(f"[TEST] test image: {len(_raw_bytes)}B  shape={_source_arr.shape}")

# ── Mock st.session_state ─────────────────────────────────────────────────────
import streamlit as st

if not isinstance(getattr(st, "session_state", None), dict):
    st.session_state = {}

# Load .env
ENV_PATH = PROJECT_ROOT / ".env"
if ENV_PATH.exists():
    with open(ENV_PATH) as fh:
        for line in fh:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                if k.strip() not in os.environ:
                    os.environ[k.strip()] = v.strip().strip("\"'")

# ── Run pipeline ──────────────────────────────────────────────────────────────
print("\n" + "=" * 70)
print("CALLING run_inspection()")
print("=" * 70)

from streamlit_app.ai.inspection_engine import run_inspection

try:
    report = run_inspection(
        sources=_source_arr,
        file_name="test_cracked_wall.jpg",
        file_size_bytes=len(_raw_bytes),
    )
except Exception as exc:
    import traceback
    traceback.print_exc()
    print(f"\n[PIPELINE] run_inspection RAISED: {type(exc).__name__}: {exc}")
    sys.exit(1)

# ── Print final report ────────────────────────────────────────────────────────
print("\n" + "=" * 70)
print("FINAL InspectionReport")
print("=" * 70)

field_order = [
    "file_name", "image_width", "image_height", "file_size_mb",
    "validation_passed", "validation_error",
    "damage_percentage", "damage_area_px", "image_area_px",
    "contour_count", "largest_damage_area_px",
    "damage_type", "severity", "confidence",
    "possible_causes", "repair_steps",
    "recommended_professional", "estimated_cost_range",
    "urgency", "prevention_tips",
    "cv_processing_time_sec", "gemini_processing_time_sec", "total_processing_time_sec",
    "gemini_skipped", "gemini_error",
]
for fname in field_order:
    val = getattr(report, fname, "<MISSING>")
    if isinstance(val, list) and val:
        val_str = f"[{len(val)} items] {val[:3]}"
    else:
        val_str = repr(val)
    print(f"  {fname:<32} = {val_str}")

m = report.measurement_report
if m is not None:
    print(f"\n  measurement_report fields:")
    for attr in ["region_count", "total_damage_px", "total_damage_pct",
                 "avg_crack_width", "most_affected_wall", "avg_contour_complexity"]:
        print(f"    {attr:<32} = {getattr(m, attr, '<MISSING>')}")
    print(f"    regions[0]: {m.regions[0] if m.regions else '<none>'}")
else:
    print("\n  measurement_report = None (run_full_analysis does not call measure_damage_regions)")

# ── Session state ─────────────────────────────────────────────────────────────
print("\n" + "=" * 70)
print("SESSION STATE keys (after run_inspection)")
print("=" * 70)
keys = list(st.session_state.keys())
if keys:
    for k in keys:
        v = st.session_state[k]
        if isinstance(v, dict):
            print(f"  {k!r}: dict keys={list(v.keys())[:10]}")
        elif isinstance(v, list):
            print(f"  {k!r}: list len={len(v)}")
        else:
            print(f"  {k!r}: {type(v).__name__}")
else:
    print("  (empty -- run_inspection does not write to session state)")

# ── Simulate what processing.py does: fuse_reports() ──────────────────────────
print("\n" + "=" * 70)
print("FUSE_REPORTS -- processing.py:242")
print("=" * 70)

from streamlit_app.ai.fusion_engine import fuse_reports

reports_list = [report]
print(f"  reports passed: {len(reports_list)}")
print(f"  report[0] damage_pct={report.damage_percentage}  severity={report.severity!r}  validation_passed={report.validation_passed}")

fused = fuse_reports(reports_list)

print("\n" + "=" * 70)
print("FusedInspection result")
print("=" * 70)
print(f"  total_images          = {fused.total_images}")
print(f"  total_findings        = {fused.total_findings}")
print(f"  overall_health_score  = {fused.overall_health_score}")
print(f"  overall_damage_pct    = {fused.overall_damage_pct}")
print(f"  overall_severity      = {fused.overall_severity!r}")
print(f"  overall_confidence    = {fused.overall_confidence}")
print(f"  overall_estimated_cost_min  = {fused.overall_estimated_cost_min}")
print(f"  overall_estimated_cost_max  = {fused.overall_estimated_cost_max}")
print(f"  avg_crack_width_px    = {fused.avg_crack_width_px}")
print(f"  total_repair_area_px  = {fused.total_repair_area_px}")
print(f"  executive_summary[:120] = {fused.executive_summary[:120]!r}")
print(f"  findings count        = {len(fused.findings)}")
if fused.findings:
    for f in fused.findings[:3]:
        print(f"    finding: damage_type={f.damage_type!r} severity={f.severity!r} confidence={f.confidence} damage_pct={f.damage_pct}")

# ── Results-page serialization ────────────────────────────────────────────────
print("\n" + "=" * 70)
print("RESULTS PAGE VALUES (what render_results() reads from session state)")
print("=" * 70)
print("  The Results page reads st.session_state[SessionKeys.INSPECTION_DATA] via get_inspection_data().")
print("  That dict is populated in processing.py lines 273-283 as:")
print("  {")
print("    'id'            : _generate_inspection_id(),")
print("    'property_data' : property_data,")
print("    'results'       : serialisable (per-image report dicts),")
print("    'fused_inspection': fused_dict (serialised FusedInspection),")
print("    'image_count'   : len(files_list),")
print("    'image_names'   : [f.name for f in files_list],")
print("    'status'        : 'Completed',")
print("    'gemini_key_error': gemini_key_error,")
print("    'fusion_applied': True,")
print("  }")
print()
print("  After rebuild_fused_inspection():")
from streamlit_app.views.results.reconstruction import rebuild_fused_inspection
# Simulate the dict that processing.py puts into session state
sim_fused_dict = {
    "overall_damage_pct": fused.overall_damage_pct,
    "overall_confidence": fused.overall_confidence,
    "overall_severity": fused.overall_severity,
    "overall_health_score": fused.overall_health_score,
    "overall_estimated_cost_min": fused.overall_estimated_cost_min,
    "overall_estimated_cost_max": fused.overall_estimated_cost_max,
    "total_repair_area_px": fused.total_repair_area_px,
    "avg_crack_width_px": fused.avg_crack_width_px,
    "findings": [
        {"damage_type": f.damage_type, "severity": f.severity, "confidence": f.confidence,
         "damage_pct": f.damage_pct, "affected_images": f.affected_images,
         "image_count": f.image_count, "possible_causes": f.possible_causes,
         "repair_steps": f.repair_steps, "recommended_professional": f.recommended_professional,
         "estimated_cost_range": f.estimated_cost_range, "urgency": f.urgency,
         "prevention_tips": f.prevention_tips}
        for f in fused.findings
    ],
    "image_rankings": [
        {"rank": r.rank, "file_name": r.file_name, "damage_pct": r.damage_pct,
         "severity": r.severity, "damage_type": r.damage_type, "confidence": r.confidence}
        for r in fused.image_rankings
    ],
    "executive_summary": fused.executive_summary,
    "property_summary": fused.property_summary,
    "inspection_conclusion": fused.inspection_conclusion,
    "timeline": [{"bucket": t.bucket, "findings_count": 0, "color": t.color} for t in fused.timeline],
    "maintenance_tips": fused.maintenance_tips,
    "total_images": fused.total_images,
    "total_findings": fused.total_findings,
    "processing_time_sec": fused.processing_time_sec,
    "risk_assessment": {
        "overall_risk_score": fused.risk_assessment.overall_risk_score if fused.risk_assessment else 0.0,
        "risk_level": fused.risk_assessment.risk_level if fused.risk_assessment else "Low",
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
    "health_report": None,
    "comparison_report": None,
}
rebuilt = rebuild_fused_inspection(sim_fused_dict)
print(f"  After rebuild_fused_inspection():")
print(f"    total_images        = {rebuilt.total_images}")
print(f"    total_findings      = {rebuilt.total_findings}")
print(f"    overall_health_score= {rebuilt.overall_health_score}")
print(f"    overall_damage_pct  = {rebuilt.overall_damage_pct}")
print(f"    findings count      = {len(rebuilt.findings)}")

print("\n" + "=" * 70)
print("TRACE COMPLETE")
print("=" * 70)
