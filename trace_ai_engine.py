"""Standalone AI engine trace: one image, every stage, raw output."""
import os
os.environ["PYTHONIOENCODING"] = "utf-8"
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import json
import base64
import io
import time

import cv2
import numpy as np
from PIL import Image

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)
os.chdir(PROJECT_ROOT)

from dotenv import load_dotenv
load_dotenv()

OUT_DIR = os.path.join(PROJECT_ROOT, "cv_debug_output")
os.makedirs(OUT_DIR, exist_ok=True)

IMAGE_PATH = os.path.join(PROJECT_ROOT, "test_damaged_wall.jpg")

# ── helpers ────────────────────────────────────────────────────────────────────

def img_to_b64(arr):
    """Encode a numpy array as base64 PNG for terminal display."""
    _, buf = cv2.imencode(".png", arr)
    return base64.b64encode(buf).decode()

def save_img(name, arr):
    path = os.path.join(OUT_DIR, name)
    cv2.imwrite(path, arr)
    print(f"  [SAVED] {path}  shape={arr.shape}  dtype={arr.dtype}")
    return path

def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

# ── load image ─────────────────────────────────────────────────────────────────

print_section("0. LOAD IMAGE")
img_bgr = cv2.imread(IMAGE_PATH)
if img_bgr is None:
    print(f"FATAL: cv2.imread returned None for {IMAGE_PATH}")
    sys.exit(1)

h, w = img_bgr.shape[:2]
print(f"  Original BGR shape : {w}x{h}")
print(f"  dtype              : {img_bgr.dtype}")
print(f"  size_mb            : {os.path.getsize(IMAGE_PATH)/1024/1024:.2f} MB")
print(f"  BGR channel means  : B={img_bgr[:,:,0].mean():.1f}  G={img_bgr[:,:,1].mean():.1f}  R={img_bgr[:,:,2].mean():.1f}")
print(f"  BGR channel stds   : B={img_bgr[:,:,0].std():.1f}  G={img_bgr[:,:,1].std():.1f}  R={img_bgr[:,:,2].std():.1f}")

# Save original
save_img("00_original.jpg", img_bgr)

# ── stage 1: validation ────────────────────────────────────────────────────────

print_section("1. VALIDATION")
from streamlit_app.ai.image_validator import validate_image

with open(IMAGE_PATH, "rb") as fh:
    raw_bytes = fh.read()

validation = validate_image(raw_bytes, file_name=os.path.basename(IMAGE_PATH),
                            file_size_bytes=len(raw_bytes))
print(f"  is_valid           : {validation.is_valid}")
print(f"  error              : {getattr(validation, 'error', 'N/A')}")
print(f"  validation object  : {validation}")

# ── stage 2: preprocess ────────────────────────────────────────────────────────

print_section("2. PREPROCESSING")
from streamlit_app.ai.opencv_engine import preprocess_image, detect_edges, detect_contours
from streamlit_app.ai.opencv_engine import analyze_defects, generate_severity_report, run_full_analysis

MAX_DIM = 1024
BLUR_K = (5, 5)

gray = preprocess_image(img_bgr, max_dimension=MAX_DIM, blur_kernel=BLUR_K)
gh, gw = gray.shape
print(f"  Grayscale shape    : {gw}x{gh}")
print(f"  dtype              : {gray.dtype}")
print(f"  pixel range        : min={gray.min()}  max={gray.max()}  mean={gray.mean():.2f}  std={gray.std():.2f}")
print(f"  unique values count: {len(np.unique(gray))}")
save_img("01_gray.jpg", gray)

# Also save blurred (before gray) to inspect
blurred = cv2.GaussianBlur(img_bgr, BLUR_K, 0)
save_img("01_blurred_bgr.jpg", blurred)

# ── stage 3: Canny edge detection ─────────────────────────────────────────────

print_section("3. CANNY EDGE DETECTION")
CANNY_LOW = 50
CANNY_HIGH = 150

edges = detect_edges(gray, low=CANNY_LOW, high=CANNY_HIGH)
edge_pixels = int(np.count_nonzero(edges))
edge_pct = edge_pixels / (gw * gh) * 100
print(f"  Canny thresholds   : low={CANNY_LOW}  high={CANNY_HIGH}")
print(f"  Edge pixels        : {edge_pixels} / {gw*gh}  ({edge_pct:.3f}%)")
print(f"  edges dtype        : {edges.dtype}  unique={np.unique(edges).tolist()}")
save_img("02_edges_canny.jpg", edges)

# Also try adaptive threshold as alternative
thresh_adapt = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                      cv2.THRESH_BINARY, 11, 2)
adapt_pixels = int(np.count_nonzero(thresh_adapt))
print(f"\n  [ALT] AdaptiveThreshold pixels: {adapt_pixels} / {gw*gh} ({adapt_pixels/(gw*gh)*100:.3f}%)")
save_img("02_thresh_adaptive.jpg", thresh_adapt)

# Otsu threshold
_, thresh_otsu = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
otsu_pixels = int(np.count_nonzero(thresh_otsu))
print(f"  [ALT] Otsu threshold (t={_})  : {otsu_pixels} / {gw*gh} ({otsu_pixels/(gw*gh)*100:.3f}%)")
save_img("02_thresh_otsu.jpg", thresh_otsu)

# ── stage 4: contour detection ────────────────────────────────────────────────

print_section("4. CONTOUR DETECTION")
MIN_CONTOUR_AREA = 100

# Raw (no filter)
contours_all, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
print(f"  Raw findContours   : {len(contours_all)} contours")
if contours_all:
    areas_raw = sorted([cv2.contourArea(c) for c in contours_all], reverse=True)
    print(f"  Top-5 raw areas    : {areas_raw[:5]}")
    print(f"  Min raw area       : {areas_raw[-1]:.1f}")
    print(f"  Max raw area       : {areas_raw[0]:.1f}")

# Filtered
contours = [c for c in contours_all if cv2.contourArea(c) >= MIN_CONTOUR_AREA]
print(f"\n  After area filter (min={MIN_CONTOUR_AREA}px): {len(contours)} contours")
if contours:
    areas_filt = sorted([cv2.contourArea(c) for c in contours], reverse=True)
    print(f"  Top-5 filtered areas: {areas_filt[:5]}")

# ── if zero contours, deep-dive why ───────────────────────────────────────────

if len(contours) == 0:
    print_section("4a. ZERO-CONTOUR DIAGNOSIS")

    # 1) Show raw contour areas before filtering
    print("\n  -- All raw contour areas --")
    for i, c in enumerate(contours_all):
        a = cv2.contourArea(c)
        print(f"    contour[{i}]: area={a:.1f}px  passes_filter={a >= MIN_CONTOUR_AREA}")

    # 2) Show edge statistics by intensity level
    print(f"\n  -- Edge pixel histogram --")
    unique, counts = np.unique(edges, return_counts=True)
    for u, c in zip(unique, counts):
        print(f"    value={u}: {c} pixels")

    # 3) Show what threshold would be needed to capture any edges
    print(f"\n  -- Minimum area that WOULD pass filter --")
    if contours_all:
        min_raw = min(cv2.contourArea(c) for c in contours_all)
        print(f"    Smallest raw contour area = {min_raw:.1f}px")
        print(f"    Filter threshold          = {MIN_CONTOUR_AREA}px")
        if min_raw < MIN_CONTOUR_AREA:
            print(f"    → Filter is EXCLUDING all contours. "
                  f"Need min_area <= {min_raw:.1f} to keep any.")
    else:
        print("    NO contours found at all — Canny produced no connected edges.")
        print("    Likely cause: image has no strong edges, OR Canny thresholds too high.")

    # 4) Try RETR_LIST mode to catch more
    contours_list, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    print(f"\n  -- RETR_LIST mode --")
    print(f"    Found {len(contours_list)} contours")
    if contours_list:
        areas_list = sorted([cv2.contourArea(c) for c in contours_list], reverse=True)
        print(f"    Top-5 areas: {areas_list[:5]}")

    # 5) Try dilating edges before contour detection
    kernel = np.ones((3, 3), np.uint8)
    edges_dilated = cv2.dilate(edges, kernel, iterations=1)
    contours_dil, _ = cv2.findContours(edges_dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours_dil_filt = [c for c in contours_dil if cv2.contourArea(c) >= MIN_CONTOUR_AREA]
    print(f"\n  -- After dilation (3x3, 1 iter) --")
    print(f"    Raw: {len(contours_dil)}, filtered: {len(contours_dil_filt)}")
    if contours_dil_filt:
        print(f"    Top-5 areas: {sorted([cv2.contourArea(c) for c in contours_dil_filt], reverse=True)[:5]}")
    save_img("02_edges_dilated.jpg", edges_dilated)

    # 6) Show what happens with different Canny thresholds
    for lo, hi in [(30, 100), (20, 80), (10, 50), (100, 200), (150, 250)]:
        e = cv2.Canny(gray, lo, hi)
        cnts, _ = cv2.findContours(e, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cnts_f = [c for c in cnts if cv2.contourArea(c) >= MIN_CONTOUR_AREA]
        print(f"  Canny({lo},{hi}): raw={len(cnts)}  filtered={len(cnts_f)}")
        if cnts_f:
            print(f"    → top area={max(cv2.contourArea(c) for c in cnts_f):.1f}")
        save_img(f"02_edges_canny_{lo}_{hi}.jpg", e)

    # 7) Save contour overlay (empty — just gray background)
    overlay_empty = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
    save_img("03_contour_overlay.jpg", overlay_empty)
    mask_empty = np.zeros(gray.shape, dtype=np.uint8)
    save_img("03_mask.jpg", mask_empty)

    print(f"\n  *** CONCLUSION: {len(contours)} contours → 0 defects → 0.0% damage ***")

else:
    # We have contours — build overlay and mask
    print_section("4b. CONTOUR OVERLAY + MASK")

    overlay = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
    cv2.drawContours(overlay, contours, -1, (0, 255, 0), 2)
    save_img("03_contour_overlay.jpg", overlay)

    mask = np.zeros(gray.shape, dtype=np.uint8)
    for contour in contours:
        cv2.drawContours(mask, [contour], -1, 255, -1)
    save_img("03_mask.jpg", mask)

    print(f"  Overlay saved  : contours drawn in green")
    print(f"  Mask saved     : {mask.shape}, white=damage region")

    # ── stage 5: defect analysis ─────────────────────────────────────────────

    print_section("5. DEFECT ANALYSIS")
    defects = analyze_defects(contours, gray.shape)
    print(f"  Defects found  : {len(defects)}")
    for d in defects:
        print(f"    id={d['id']}  area={d['area_px']}px  bbox={d['bbox']}  "
              f"aspect={d['aspect_ratio']}  conf={d['confidence']}  sev={d['severity']}")

    # ── stage 6: severity report ─────────────────────────────────────────────

    print_section("6. SEVERITY REPORT")
    report = generate_severity_report(defects)
    print(f"  total_defects           : {report['total_defects']}")
    print(f"  by_severity             : {report['by_severity']}")
    print(f"  average_confidence      : {report['average_confidence']}")
    print(f"  estimated_cost_min      : {report['estimated_cost_min']}")
    print(f"  estimated_cost_max      : {report['estimated_cost_max']}")
    print(f"  status                  : {report['status']}")
    print(f"  images_processed        : {report.get('images_processed', 'N/A')}")

# ── stage 7: run_full_analysis (metrics) ───────────────────────────────────────

print_section("7. run_full_analysis → DamageMetrics")
processed_bgr, mask_fa, overlay_fa, metrics, measurement = run_full_analysis(img_bgr)
print(f"  damage_percentage       : {metrics.damage_percentage}%")
print(f"  damage_area_px          : {metrics.damage_area_px}")
print(f"  image_area_px           : {metrics.image_area_px}")
print(f"  contour_count           : {metrics.contour_count}")
print(f"  largest_damage_area_px  : {metrics.largest_damage_area_px}")
save_img("04_processed_bgr.jpg", processed_bgr)
save_img("04_mask_full_analysis.jpg", mask_fa)
save_img("04_overlay_full_analysis.jpg", overlay_fa)

# ── stage 8: Gemini ────────────────────────────────────────────────────────────

print_section("8. GEMINI VISION ANALYSIS")
from streamlit_app.ai.gemini_engine import configure_gemini, analyze_image_with_gemini, build_prompt
from streamlit_app.ai.inspection_engine import stage_gemini, merge_results

configure_gemini()
prompt = build_prompt()
print(f"  Prompt (first 200 chars): {prompt[:200]}")

t0 = time.perf_counter()
gemini_report = stage_gemini(img_bgr, prompt=prompt)
elapsed = round(time.perf_counter() - t0, 3)

print(f"  elapsed                 : {elapsed}s")
print(f"  gemini_skipped          : {gemini_report.gemini_skipped}")
print(f"  gemini_error            : {gemini_report.gemini_error[:200] if gemini_report.gemini_error else 'None'}")
print(f"  damage_type             : {gemini_report.damage_type}")
print(f"  severity                : {gemini_report.severity}")
print(f"  confidence              : {gemini_report.confidence}")
print(f"  possible_causes         : {gemini_report.possible_causes}")
print(f"  repair_steps            : {gemini_report.repair_steps}")
print(f"  recommended_professional: {gemini_report.recommended_professional}")
print(f"  estimated_cost_range    : {gemini_report.estimated_cost_range}")
print(f"  urgency                 : {gemini_report.urgency}")
print(f"  prevention_tips         : {gemini_report.prevention_tips}")
print(f"  measurement_report      : {gemini_report.measurement_report}")

# ── stage 9: merge_results ─────────────────────────────────────────────────────

print_section("9. FINAL InspectionReport")
final = merge_results(
    round(metrics.cv_processing_time_sec if hasattr(metrics, 'cv_processing_time_sec') else 0.0, 3),
    cv_elapsed=round(metrics.cv_processing_time_sec if hasattr(metrics, 'cv_processing_time_sec') else 0.0, 3),
    gemini_elapsed=elapsed,
    validation=validation,
    cv_image=img_bgr,
    metrics=metrics,
    processed=processed_bgr,
    mask=mask_fa,
    overlay=overlay_fa,
    gemini=gemini_report if not gemini_report.gemini_skipped else None,
    file_name=os.path.basename(IMAGE_PATH),
    file_size_mb=os.path.getsize(IMAGE_PATH)/1024/1024,
    measurement_report=measurement,
)
d = final.to_dict()
for k, v in d.items():
    print(f"  {k:35s}: {v}")

# ── summary ────────────────────────────────────────────────────────────────────

print_section("SUMMARY")
print(f"  Image size              : {w}x{h}")
print(f"  Validation              : {validation.is_valid}")
print(f"  Contours found          : {metrics.contour_count}")
print(f"  Damage %                : {metrics.damage_percentage}%")
print(f"  Largest damage area     : {metrics.largest_damage_area_px}px")
print(f"  Gemini skipped          : {gemini_report.gemini_skipped}")
print(f"  Gemini damage_type      : {gemini_report.damage_type}")
print(f"  Gemini confidence       : {gemini_report.confidence}")
print(f"  Final report damage_pct : {d['damage_percentage']}%")
print(f"  Final report severity   : {d['severity']}")
print(f"  Final report confidence : {d['confidence']}")
print(f"\n  Debug images saved to  : {OUT_DIR}")
