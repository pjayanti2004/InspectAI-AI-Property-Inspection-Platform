"""End-to-end test: complete inspection workflow.

Flow:
  Dashboard → New Inspection (Step 1) → Continue → Upload Images (Step 2)
  → Continue → Review (Step 3) → Start Inspection → Processing (auto) → Results
  → Save Inspection → Generate Report → History → View Report → Analytics
"""
import base64
import os
import sys
import time
from pathlib import Path

os.environ["PYTHONIOENCODING"] = "utf-8"
os.environ["PYTHONUTF8"] = "1"
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)
sys.stderr = open(sys.stderr.fileno(), mode='w', encoding='utf-8', buffering=1)

from playwright.sync_api import sync_playwright

BASE_URL = "http://localhost:8501"

# Minimal valid 1x1 PNG
PNG_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGA"
    "WjR9awAAAABJRU5ErkJggg=="
)

DASH = "🏠 Dashboard"
NEW_INSP = "➕ New Inspection"
HISTORY = "📋 History"
ANALYTICS = "📊 Analytics"


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()

        errors = []

        def on_page_error(exc):
            errors.append(str(exc))
        page.on("pageerror", on_page_error)

        def snapshot(label):
            body = page.evaluate("document.body.innerText")
            btns = page.locator("button").count()
            errs = list(errors)
            print(f"[{label}] buttons={btns} errors={len(errs)} body={repr(body[:200])}")
            for e in errs[-3:]:
                print(f"  ERR: {str(e)[:200]}")

        # ── Step 0: Dashboard ────────────────────────────────────────────────
        print("=== STEP 0: Dashboard ===")
        page.goto(BASE_URL, wait_until="networkidle", timeout=60000)
        time.sleep(4)
        snapshot("00-dashboard")

        # ── Step 1: New Inspection ───────────────────────────────────────────
        print("\n=== STEP 1: New Inspection ===")
        page.locator(f"button:has-text('{NEW_INSP}')").first.click()
        time.sleep(4)
        snapshot("01-new_inspection")

        # Fill the property details form
        text_inputs = page.locator("input[type='text']").all()
        print(f"  Text inputs found: {len(text_inputs)}")
        assert len(text_inputs) >= 3, f"Expected at least 3 text inputs, got {len(text_inputs)}"

        text_inputs[0].fill("Sunset Apartments Unit 4B")
        text_inputs[1].fill("42 Maple Street, Mumbai")
        text_inputs[2].fill("Rajesh Kumar")

        time.sleep(1)
        snapshot("02-form_filled")

        # Click Continue to Upload
        page.locator("button:has-text('Continue to Upload Images')").first.click()
        time.sleep(5)
        snapshot("03-upload_page")

        # ── Step 2: Upload Images ────────────────────────────────────────────
        print("\n=== STEP 2: Upload Images ===")

        # Create test image file
        png_bytes = base64.b64decode(PNG_B64)
        test_img = Path("c:/Users/pjaya/OneDrive/Desktop/InspectAI - AI Property Inspection Platform/test_image.jpg")
        test_img.write_bytes(png_bytes)

        file_inputs = page.locator("input[type='file']").all()
        print(f"  File inputs: {len(file_inputs)}")
        assert len(file_inputs) > 0, "No file input found on upload page"

        file_inputs[0].set_input_files(str(test_img))
        time.sleep(4)
        snapshot("04-image_uploaded")

        # Click Continue to Review
        page.locator("button:has-text('Continue to Review')").first.click()
        time.sleep(5)
        snapshot("05-review_page")

        # ── Step 3: Review ───────────────────────────────────────────────────
        print("\n=== STEP 3: Review ===")
        body = page.evaluate("document.body.innerText")
        print(f"  Review body: {repr(body[:300])}")
        snapshot("06-review")

        # Click Start Inspection
        page.locator("button:has-text('Start Inspection')").first.click()
        time.sleep(10)
        snapshot("07-processing_done")

        # ── Step 4: Results ──────────────────────────────────────────────────
        print("\n=== STEP 4: Results ===")
        body = page.evaluate("document.body.innerText")
        print(f"  Results body: {repr(body[:300])}")
        snapshot("08-results")

        # Click Save Inspection
        save_btn = page.locator("button:has-text('Save Inspection')").first
        if save_btn.count() > 0:
            save_btn.click()
            time.sleep(2)
            snapshot("09-saved")

        # Click Generate Report
        gen_btn = page.locator("button:has-text('Generate Report')").first
        if gen_btn.count() > 0:
            gen_btn.click()
            time.sleep(5)
            snapshot("10-report_page")
        else:
            print("[FAIL] Generate Report button not found")
            body = page.evaluate("document.body.innerText")
            print(f"  Body: {repr(body[:300])}")

        # ── Step 5: History ──────────────────────────────────────────────────
        print("\n=== STEP 5: History ===")
        page.locator(f"button:has-text('{HISTORY}')").first.click()
        time.sleep(5)
        snapshot("11-history")

        # Try to open the first report — button text varies by has_report
        view_btn = page.locator("button:has-text('View'), button:has-text('Open')").first
        if view_btn.count() > 0:
            view_btn.click()
            time.sleep(5)
            snapshot("12-view_report")
        else:
            print("[INFO] No 'View'/'Open' buttons in history")

        # ── Step 6: Analytics ────────────────────────────────────────────────
        print("\n=== STEP 6: Analytics ===")
        page.locator(f"button:has-text('{ANALYTICS}')").first.click()
        time.sleep(5)
        snapshot("13-analytics")

        # ── Summary ──────────────────────────────────────────────────────────
        print(f"\n=== SUMMARY ===")
        print(f"Total page errors: {len(errors)}")
        for e in errors:
            print(f"  ERROR: {str(e)[:300]}")
        if not errors:
            print("  No errors.")

        browser.close()
        print("\nDone.")


if __name__ == "__main__":
    main()
