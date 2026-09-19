"""Test all app pages by following the wizard flow and sidebar navigation."""
import os
import sys

os.environ["PYTHONIOENCODING"] = "utf-8"
os.environ["PYTHONUTF8"] = "1"
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)
sys.stderr = open(sys.stderr.fileno(), mode='w', encoding='utf-8', buffering=1)

from playwright.sync_api import sync_playwright
import time

BASE_URL = "http://localhost:8501"


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
            inp = page.locator("input").count()
            errs = list(errors)
            print(f"[{label}] inputs={inp} errors={len(errs)} body={repr(body[:200])}")
            for e in errs[-3:]:
                print(f"  ERR: {str(e)[:200]}")

        # 1. Dashboard
        page.goto(BASE_URL, wait_until="networkidle", timeout=60000)
        time.sleep(5)
        snapshot("01-dashboard")

        # 2. New Inspection - click action button
        page.locator("button:has-text('New Inspection')").first.click()
        time.sleep(6)
        snapshot("02-new_inspection")

        # Fill in the form
        page.locator("input[type='text']").first.fill("Test Property")
        inputs = page.locator("input[type='text']").all()
        if len(inputs) >= 3:
            inputs[1].fill("House")
            inputs[2].fill("Test Address")
        text_inputs = page.locator("input[type='text']").all()
        if len(text_inputs) >= 4:
            text_inputs[3].fill("Test Inspector")
        snapshot("03-form_filled")

        # Click Continue
        page.locator("button:has-text('Continue')").first.click()
        time.sleep(6)
        snapshot("04-after-continue")

        # Check where we are
        body = page.evaluate("document.body.innerText")
        if "Upload" in body or "upload" in body:
            print("[OK] On Upload page")
        elif "Review" in body:
            print("[OK] On Review page")
        else:
            print(f"[?] Unknown page: {repr(body[:300])}")

        # 5. History
        page.locator("button:has-text('History')").first.click()
        time.sleep(5)
        snapshot("05-history")

        # 6. Reports
        page.locator("button:has-text('Reports')").first.click()
        time.sleep(5)
        snapshot("06-reports")

        # 7. Analytics
        page.locator("button:has-text('Analytics')").first.click()
        time.sleep(5)
        snapshot("07-analytics")

        # 8. Settings
        page.locator("button:has-text('Settings')").first.click()
        time.sleep(5)
        snapshot("08-settings")

        # 9. About
        page.locator("button:has-text('About')").first.click()
        time.sleep(5)
        snapshot("09-about")

        browser.close()
        print("\nDone.")


if __name__ == "__main__":
    main()
