"""Batch AI pipeline test: 10 images, save intermediates, compare OpenCV-only vs Gemini+OpenCV."""
import os
os.environ["PYTHONIOENCODING"] = "utf-8"
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import json
import time
import shutil
from pathlib import Path

import cv2
import numpy as np

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)
os.chdir(PROJECT_ROOT)

from dotenv import load_dotenv
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

OUT_DIR = os.path.join(PROJECT_ROOT, "cv_debug_output")
os.makedirs(OUT_DIR, exist_ok=True)

# ── Helpers ─────────────────────────────────────────────────────────────────────

def make_damage_image(name, fn, size=(800, 600)):
    """Create a synthetic damaged-wall image. fn is a draw function."""
    h, w = size[1], size[0]
    base = np.full((h, w, 3), 218, dtype=np.uint8)
    # Add subtle texture (paint patchiness)
    noise = np.random.randint(-8, 8, (h, w, 3), dtype=np.int16)
    base = np.clip(base.astype(np.int16) + noise, 0, 255).astype(np.uint8)
    base = fn(base, w, h)
    path = os.path.join(OUT_DIR, name)
    cv2.imwrite(path, base)
    return path

def draw_crack(base, w, h):
    img = base.copy()
    cv2.line(img, (0, h//2), (w, h//2), (45, 40, 38), 15)
    return img

def draw_crack_vertical(base, w, h):
    img = base.copy()
    cv2.line(img, (w//2-7, 0), (w//2+7, h), (45, 40, 38), 15)
    return img

def draw_water_stain(base, w, h):
    img = base.copy()
    cv2.ellipse(img, (w//2, h//2), (w//5, h//4), 0, 0, 360, (160, 140, 120), -1)
    cv2.ellipse(img, (w//2, h//2), (w//7, h//6), 0, 0, 360, (140, 115, 95), -1)
    return img

def draw_peeling_paint(base, w, h):
    img = base.copy()
    cv2.rectangle(img, (w//4, h//4), (w*3//4, h*3//4), (200, 190, 180), -1)
    cv2.rectangle(img, (w//4, h//4), (w*3//4, h*3//4), (100, 90, 80), 3)
    return img

def draw_hole(base, w, h):
    img = base.copy()
    cv2.circle(img, (w//2, h//2), 40, (50, 45, 40), -1)
    return img

def draw_flat_stain(base, w, h):
    """Simulate flat texture — no real edge structure."""
    return base  # return plain noise background

def draw_multiple_cracks(base, w, h):
    img = base.copy()
    for i in range(4):
        cv2.line(img, (0, h//5 + i*h//8), (w, h//5 + i*h//8 + 10), (42, 38, 35), 12)
    return img

def draw_diagonal_crack(base, w, h):
    img = base.copy()
    cv2.line(img, (0, h), (w, 0), (48, 42, 38), 15)
    return img

def draw_stucco_damage(base, w, h):
    img = base.copy()
    rng = np.random.default_rng(42)
    for _ in range(20):
        cx, cy = rng.integers(0, w), rng.integers(0, h)
        rx, ry = rng.integers(15, 45), rng.integers(10, 30)
        cv2.ellipse(img, (int(cx), int(cy)), (int(rx), int(ry)), 0, 0, 360, (170, 155, 140), -1)
    return img

# ── Build 10-image test set ─────────────────────────────────────────────────────

real_images = []
if os.path.exists(os.path.join(PROJECT_ROOT, "test_damaged_wall.jpg")):
    sz = os.path.getsize(os.path.join(PROJECT_ROOT, "test_damaged_wall.jpg"))
    if sz > 1024:  # > 1 KB
        real_images.append(("real_damaged_wall_01.jpg", os.path.join(PROJECT_ROOT, "test_damaged_wall.jpg")))
if os.path.exists(os.path.join(PROJECT_ROOT, "test_image.jpg")):
    sz = os.path.getsize(os.path.join(PROJECT_ROOT, "test_image.jpg"))
    if sz > 1024:
        real_images.append(("real_image_02.jpg", os.path.join(PROJECT_ROOT, "test_image.jpg")))

synthetic = [
    ("syn_crack_horizontal.jpg",   draw_crack),
    ("syn_crack_vertical.jpg",      draw_crack_vertical),
    ("syn_crack_diagonal.jpg",      draw_diagonal_crack),
    ("syn_crack_multiple.jpg",      draw_multiple_cracks),
    ("syn_water_stain.jpg",         draw_water_stain),
    ("syn_peeling_paint.jpg",       draw_peeling_paint),
    ("syn_hole.jpg",                draw_hole),
    ("syn_flat_stain.jpg",          draw_flat_stain),
    ("syn_stucco_damage.jpg",       draw_stucco_damage),
]

# Copy real images into OUT_DIR
for dst_name, src_path in real_images:
    dst = os.path.join(OUT_DIR, dst_name)
    if os.path.abspath(src_path) != os.path.abspath(dst):
        shutil.copy2(src_path, dst)

# Generate synthetic images
for name, fn in synthetic[:max(0, 10 - len(real_images))]:
    make_damage_image(name, fn)

# Collect final list (up to 10)
all_names = [dst for _, dst in real_images] + \
            [os.path.join(OUT_DIR, name) for name, _ in synthetic[:max(0, 10 - len(real_images))]]
all_names = all_names[:10]
print(f"Test set: {len(all_names)} images")
for n in all_names:
    sz = os.path.getsize(n) // 1024
    print(f"  {os.path.basename(n):35s} {sz} KB")

# ── Imports ─────────────────────────────────────────────────────────────────────

from streamlit_app.ai.opencv_engine import (
    preprocess_image, detect_edges, detect_contours,
    analyze_defects, generate_severity_report, run_full_analysis,
)
from streamlit_app.ai.image_validator import validate_image
from streamlit_app.ai.gemini_engine import configure_gemini, build_prompt
from streamlit_app.ai.inspection_engine import stage_gemini

configure_gemini()
prompt = build_prompt()

# ── Per-image trace ─────────────────────────────────────────────────────────────

print("\n" + "=" * 72)
print("  BATCH TEST RESULTS — OpenCV-only + Gemini")
print("=" * 72)

header = (
    f"{'Image':<35} {'Confs':>8} {'TopConf':>7} {'dmg%':>6} "
    f"{'cv_s':>5} {'gem':>4} {'sev':>10} {'gemini_error':<40}"
)
print(header)
print("-" * 72)

summary = []

for img_path in all_names:
    img_name = os.path.basename(img_path)
    base_name = os.path.splitext(img_name)[0]
    img_bgr = cv2.imread(img_path)
    if img_bgr is None:
        print(f"  SKIP {img_name}: could not load")
        continue
    ih, iw = img_bgr.shape[:2]
    img_area = ih * iw

    with open(img_path, "rb") as fh:
        raw = fh.read()
    validation = validate_image(raw, file_name=img_name, file_size_bytes=len(raw))

    # CV pipeline
    gray = preprocess_image(img_bgr)
    edges = detect_edges(gray)
    contours = detect_contours(edges)
    defects = analyze_defects(contours, gray.shape)
    _, mask_rfa, overlay_rfa, metrics, _ = run_full_analysis(img_bgr)

    # Save per-image outputs
    sub = os.path.join(OUT_DIR, base_name)
    os.makedirs(sub, exist_ok=True)
    cv2.imwrite(os.path.join(sub, "original.jpg"), img_bgr)
    cv2.imwrite(os.path.join(sub, "gray.jpg"), gray)
    cv2.imwrite(os.path.join(sub, "edges_canny.jpg"), edges)
    cv2.imwrite(os.path.join(sub, "mask.jpg"), mask_rfa)
    cv2.imwrite(os.path.join(sub, "overlay.jpg"), overlay_rfa)

    # Contour overlay (green contours on gray)
    overlay_cnt = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
    if contours:
        cv2.drawContours(overlay_cnt, contours, -1, (0, 255, 0), 2)
        for c in contours:
            x, y, w, h = cv2.boundingRect(c)
            cv2.rectangle(overlay_cnt, (x, y), (x+w, y+h), (0, 0, 255), 1)
    cv2.imwrite(os.path.join(sub, "contours.jpg"), overlay_cnt)

    # Confidence breakdown per defect (matches new formula in opencv_engine.py)
    def conf_breakdown(d, contours, img_w, img_h):
        idx = d["id"] - 1
        if 0 <= idx < len(contours):
            c = contours[idx]
            area = float(cv2.contourArea(c))
            hull = cv2.convexHull(c)
            hull_area = float(cv2.contourArea(hull))
            hull_w = float(hull[:, 0, 0].max() - hull[:, 0, 0].min() + 1)
            hull_h = float(hull[:, 0, 1].max() - hull[:, 0, 1].min() + 1)
            x, y, bw, bh = cv2.boundingRect(c)

            extent_x = hull_w / img_w
            extent_y = hull_h / img_h
            if extent_y > 0.001:
                extent_ratio = max(extent_x, extent_y) / min(extent_x, extent_y)
            else:
                extent_ratio = 100.0
            ex_s = min(extent_ratio / 5.0, 1.0) * 35

            solidity = area / hull_area if hull_area > 0 else 0.0
            sol_s = (1.0 - solidity) * 35

            bbox_area = float(bw * bh)
            fill_ratio = area / bbox_area if bbox_area > 0 else 0.0
            fill_s = (1.0 - fill_ratio) * 30
        else:
            ex_s = sol_s = fill_s = 0.0
        return ex_s, sol_s, fill_s

    confs = [d["confidence"] for d in defects]
    top_conf = max(confs) if confs else 0

    # Gemini
    t0 = time.perf_counter()
    gemini_skipped = True
    gemini_sev = "N/A"
    gemini_err = ""
    try:
        greport = stage_gemini(img_bgr, prompt=prompt)
        gemini_skipped = greport.gemini_skipped
        gemini_sev = greport.severity if not gemini_skipped else "SKIP"
        gemini_err = greport.gemini_error
    except Exception as exc:
        gemini_sev = f"ERR:{exc.__class__.__name__}"
        gemini_err = str(exc)

    cv_time = metrics.cv_processing_time_sec if hasattr(metrics, 'cv_processing_time_sec') else 0.0
    top_ar = max((d["aspect_ratio"] for d in defects), default=0.0)

    # Print per-image line
    cv_s_str = f"{cv_time:.2f}"
    dmg_str = f"{metrics.damage_percentage:.1f}%"
    gem_str = "yes" if not gemini_skipped else "no"
    sev_str = defects[0]["severity"] if defects else "None"
    gem_err_str = greport.gemini_error[:60] if not gemini_skipped and greport.gemini_error else ("SKIP" if gemini_skipped else "")
    n_defects = len(confs)
    err_display = (gemini_err[:38] + "..") if len(gemini_err) > 40 else gemini_err
    print(f"  {img_name:<35} {n_defects:>8} {top_conf:>7} {dmg_str:>6} "
          f"{cv_s_str:>5} {gem_str:>4} {sev_str:>10}  {err_display}")

    # Confidence breakdown
    if defects:
        print(f"    Defect breakdown:")
        for d in defects:
            ex_s, sol_s, fill_s = conf_breakdown(d, contours, iw, ih)
            print(f"      [{d['severity']:8s}] conf={d['confidence']:>3d}  "
                  f"area={d['area_px']:>6d}px  "
                  f"ex_s={ex_s:5.1f}  sol_s={sol_s:5.1f}  fill_s={fill_s:5.1f}")
    else:
        print(f"    (no contours found)")

    summary.append({
        "name": img_name,
        "contours": len(contours),
        "defects": len(defects),
        "top_confidence": top_conf,
        "damage_pct": round(metrics.damage_percentage, 2),
        "top_severity": sev_str,
        "gemini_skipped": gemini_skipped,
        "gemini_severity": gemini_sev,
        "output_dir": sub,
    })

# ── Summary table ──────────────────────────────────────────────────────────────

print("\n" + "=" * 72)
print("  SUMMARY TABLE")
print("=" * 72)
print(f"  {'Image':<35} {'Contours':>9} {'Defects':>8} {'TopConf':>8} {'Dmg%':>6} {'CV Sev':>8} {'Gem Sev':>9} {'Gemini':>8}")
print("-" * 72)

for s in summary:
    gem_str = "skipped" if s["gemini_skipped"] else "OK"
    cv_s = s["top_severity"]
    gem_s = s.get("gemini_severity", "N/A")
    print(f"  {s['name']:<35} {s['contours']:>9} {s['defects']:>8} "
          f"{s['top_confidence']:>8} {s['damage_pct']:>6.2f} {cv_s:>8} {gem_s:>9} {gem_str:>8}")

# ── Scoring validation ─────────────────────────────────────────────────────────

print("\n" + "=" * 72)
print("  SCORING VALIDATION")
print("=" * 72)

flat_images = [s for s in summary if "flat" in s["name"] or "stain" in s["name"]]
crack_images = [s for s in summary if "crack" in s["name"]]

if flat_images:
    flat_confs = [s["top_confidence"] for s in flat_images if s["top_confidence"] > 0]
    if flat_confs:
        print(f"  Flat texture images — top confidence: max={max(flat_confs)}, avg={sum(flat_confs)/len(flat_confs):.1f}")
        print(f"  Target: < 20  → {'PASS' if max(flat_confs) < 20 else 'FAIL'}")
    else:
        print(f"  Flat texture images — 0 contours detected (no false positives)")

if crack_images:
    crack_confs = [s["top_confidence"] for s in crack_images if s["top_confidence"] > 0]
    if crack_confs:
        print(f"  Crack images — top confidence: min={min(crack_confs)}, max={max(crack_confs)}, avg={sum(crack_confs)/len(crack_confs):.1f}")
        print(f"  Target: > 60  → {'PASS' if min(crack_confs) > 60 else 'FAIL (see breakdown above)'}")
    else:
        print(f"  Crack images — 0 contours detected")

# ── OpenCV vs Gemini comparison ────────────────────────────────────────────────

print("\n" + "=" * 72)
print("  OpenCV-only vs Gemini+OpenCV SEVERITY COMPARISON")
print("=" * 72)
print(f"  {'Image':<35} {'CV TopConf':>10} {'CV Sev':>8} {'Gem Sev':>14} {'Match':>6}")
print("-" * 72)

n_match = 0
n_total = 0
for s in summary:
    cv_s = s["top_severity"]
    gem_s = s.get("gemini_severity", "N/A")
    if gem_s in ("N/A", "SKIP", "ERR") or gem_s.startswith("SKIP") or gem_s.startswith("ERR"):
        match = "—"
    else:
        n_total += 1
        # Severity normalization: "None" ↔ "Minimal"
        cv_norm = "Minimal" if cv_s == "None" else cv_s
        match = "YES" if cv_norm == gem_s else "NO"
        if match == "YES":
            n_match += 1
    print(f"  {s['name']:<35} {s['top_confidence']:>10} {cv_s:>8} {gem_s:>14} {match:>6}")

if n_total > 0:
    print(f"\n  Severity agreement: {n_match}/{n_total} ({n_match/n_total*100:.0f}%)")

print(f"\n  Output directory: {OUT_DIR}")
print(f"  Per-image subdirs: {[s['output_dir'] for s in summary]}")
