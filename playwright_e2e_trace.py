"""Playwright end-to-end trace: upload image, run full pipeline, capture terminal trace."""
import os
os.environ["PYTHONIOENCODING"] = "utf-8"
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import time
import json
from playwright.sync_api import sync_playwright

BASE_URL = "http://localhost:8501"
TEST_IMAGE = r"c:\Users\pjaya\OneDrive\Desktop\InspectAI - AI Property Inspection Platform\test_damaged_wall.jpg"
TRACE_PATHS = [
    r"c:\Users\pjaya\OneDrive\Desktop\InspectAI - AI Property Inspection Platform\trace_pipeline.jsonl",
    r"c:\Users\pjaya\OneDrive\Desktop\InspectAI - AI Property Inspection Platform\streamlit_app\trace_pipeline.jsonl",
]


def click_button_with(page, text, timeout=15000):
    """Click button matching text (substring, case-insensitive)."""
    btn = page.locator("button").filter(has_text=text).first
    btn.wait_for(state="visible", timeout=timeout)
    btn.click()
    return btn


def main():
    # Clear old traces
    for tp in TRACE_PATHS:
        if os.path.exists(tp):
            os.remove(tp)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()

        console_logs = []
        page.on("console", lambda msg: console_logs.append(f"[{msg.type}] {msg.text}"))
        page.on("pageerror", lambda exc: print(f"  [PAGE ERROR] {exc}"))

        # ── Navigate ──────────────────────────────────────────────────────────
        print("=== Navigate to app ===")
        page.goto(BASE_URL, wait_until="domcontentloaded", timeout=60000)
        time.sleep(15)

        # ── Step 1: Property Details ─────────────────────────────────────────
        print("\n=== Click Start New Inspection ===")
        click_button_with(page, "Start New Inspection")
        time.sleep(8)

        body = page.evaluate("document.body.innerText")
        print(f"  After nav (200 chars): {body[:200]}")

        print("\n=== Fill property form ===")
        inputs = page.locator("input[type='text']").all()
        print(f"  Found {len(inputs)} text inputs")
        inputs[0].fill("Test Wall")
        inputs[1].fill("42 Main Street")
        inputs[2].fill("Inspector Jane")
        time.sleep(1)

        # Property type dropdown
        selects = page.locator("select").all()
        if selects:
            try:
                selects[0].select_option("Residential")
            except Exception:
                pass
            time.sleep(0.5)

        # Submit form (Continue to Upload Images)
        click_button_with(page, "Continue to Upload")
        print("  Clicked Continue to Upload Images →")
        time.sleep(5)

        # ── Step 2: Upload ────────────────────────────────────────────────────
        body = page.evaluate("document.body.innerText")
        print(f"\n=== After step1 nav (300 chars) ===\n{body[:300]}")

        print("\n=== Upload image ===")
        file_input = page.locator("input[type='file']").first
        file_input.set_input_files(TEST_IMAGE)
        time.sleep(5)
        body = page.evaluate("document.body.innerText")
        print(f"  After upload (300 chars): {body[:300]}")

        # Click next to Review
        click_button_with(page, "Review")
        print("  Clicked Continue to Review →")
        time.sleep(5)

        body = page.evaluate("document.body.innerText")
        print(f"\n=== After step2 nav (300 chars) ===\n{body[:300]}")

        # ── Step 3: Start Inspection ──────────────────────────────────────────
        print("\n=== Click Start Inspection ===")
        click_button_with(page, "Start Inspection")
        print("  Clicked Start Inspection, waiting for AI processing...")

        # Wait for processing → results
        result_found_at = None
        for i in range(150):
            time.sleep(1)
            body = page.evaluate("document.body.innerText")
            if any(kw in body.lower() for kw in [
                "unified analysis",
                "overall property health",
                "repair cost",
                "no inspection results found",
                "property summary",
                "analysis complete"
            ]):
                result_found_at = i + 1
                print(f"  Results/processing-complete detected at ~{i+1}s")
                break
            if i % 20 == 19:
                print(f"  ... {i+1}s elapsed, body preview: {body[:150]}")

        time.sleep(3)
        body = page.evaluate("document.body.innerText")
        print(f"\n=== Final page body (3000 chars) ===\n{body[:3000]}")

        # ── Print TRACE entries from console ─────────────────────────────────
        print("\n=== Console [TRACE] entries ===")
        trace_lines = [l for l in console_logs if "[TRACE]" in l]
        if trace_lines:
            for log in trace_lines:
                print(f"  {log}")
        else:
            print("  (no TRACE entries in console)")

        # ── Read JSONL trace file(s) ────────────────────────────────────────
        print("\n=== JSONL Trace File(s) ===")
        time.sleep(2)
        found_trace_path = None
        for tp in TRACE_PATHS:
            if os.path.exists(tp) and os.path.getsize(tp) > 0:
                found_trace_path = tp
                break
        if found_trace_path:
            with open(found_trace_path, encoding="utf-8") as f:
                content = f.read()
            if content.strip():
                for line in content.strip().split("\n"):
                    try:
                        obj = json.loads(line)
                        print(f"  {json.dumps(obj)}")
                    except json.JSONDecodeError:
                        print(f"  [RAW] {line[:200]}")
            else:
                print("  (file exists but is empty)")
        else:
            print("  (no trace file found in any expected location)")

        # ── Verification ─────────────────────────────────────────────────────
        print("\n=== Verification ===")
        has_trace_content = found_trace_path is not None
        checks = {
            "page_has_results": any(kw in body.lower() for kw in [
                "unified analysis", "overall property health", "analysis complete"
            ]),
            "no_zero_images_header": "unified analysis across 0 images" not in body.lower(),
            "trace_file_has_content": has_trace_content,
            "no_merge_results_error": "missing 1 required positional argument" not in body.lower(),
        }
        for k, v in checks.items():
            print(f"  {k}: {'PASS' if v else 'FAIL'}")

        page.screenshot(
            path=r"c:\Users\pjaya\OneDrive\Desktop\InspectAI - AI Property Inspection Platform\screenshot_e2e_results.png",
            full_page=True,
        )
        print("\nScreenshot: screenshot_e2e_results.png")
        browser.close()


if __name__ == "__main__":
    main()