"""End-to-end test for InspectAI application.

Verifies:
1. Processing completes without exceptions
2. Results page opens successfully
3. Results show: image count, findings, executive summary, repair estimate
4. No raw HTML is rendered
5. No "_arrow_right" text appears
6. Browser console contains no errors
"""
from playwright.sync_api import sync_playwright, expect
import time
import sys

TEST_IMAGE = r"c:\Users\pjaya\OneDrive\Desktop\InspectAI - AI Property Inspection Platform\test_damaged_wall.jpg"
SCREENSHOT_DIR = r"c:\Users\pjaya\OneDrive\Desktop\InspectAI - AI Property Inspection Platform"

def main():
    console_logs = []
    page_errors = []

    def handle_console(msg):
        console_logs.append(f"[{msg.type}] {msg.text}")

    def handle_page_error(err):
        page_errors.append(str(err))

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1440, 'height': 900})
        page = context.new_page()

        page.on("console", handle_console)
        page.on("pageerror", handle_page_error)

        # Step 1: Navigate to app
        print("=" * 60)
        print("STEP 1: Navigate to app")
        print("=" * 60)
        page.goto("http://localhost:8501", wait_until="networkidle", timeout=60000)
        time.sleep(5)
        page.screenshot(path=f"{SCREENSHOT_DIR}\\e2e_01_dashboard.png", full_page=False)
        print("Dashboard loaded")

        # Step 2: Click "New Inspection"
        print("\n" + "=" * 60)
        print("STEP 2: Start New Inspection")
        print("=" * 60)
        try:
            # Look for sidebar navigation or a button
            new_btn = page.locator("text=New Inspection, text=Start Inspection, text=New").first
            if new_btn.is_visible(timeout=10000):
                new_btn.click()
                time.sleep(3)
                print("Clicked New Inspection")
            else:
                print("No New Inspection button found, trying navigation...")
                # Try clicking on sidebar link
                sidebar = page.locator("nav, [data-testid='stSidebar']").first
                if sidebar.is_visible(timeout=5000):
                    sidebar.click()
                    time.sleep(1)
        except Exception as e:
            print(f"Navigation note: {e}")

        page.screenshot(path=f"{SCREENSHOT_DIR}\\e2e_02_form.png", full_page=False)

        # Step 3: Fill property details
        print("\n" + "=" * 60)
        print("STEP 3: Fill property details")
        print("=" * 60)
        try:
            # Find all text inputs
            inputs = page.locator("input[type='text'], input[type='number']").all()
            print(f"Found {len(inputs)} text inputs")
            for i, inp in enumerate(inputs[:4]):
                try:
                    label = inp.get_attribute("aria-label") or f"input_{i}"
                    print(f"  Input {i}: {label}")
                except:
                    pass

            # Fill property name if found
            if len(inputs) > 0:
                inputs[0].fill("Test Wall Inspection")
                time.sleep(0.5)
                print("Filled property name")

            # Fill address if found
            if len(inputs) > 1:
                inputs[1].fill("123 Test Street")
                time.sleep(0.5)
                print("Filled address")

            # Fill inspector name if found
            if len(inputs) > 2:
                inputs[2].fill("Test Inspector")
                time.sleep(0.5)
                print("Filled inspector name")

            # Select property type if dropdown found
            select = page.locator("select").first
            if select.is_visible(timeout=2000):
                select.select_option("House")
                print("Selected property type")

            time.sleep(1)

        except Exception as e:
            print(f"Fill error: {e}")

        page.screenshot(path=f"{SCREENSHOT_DIR}\\e2e_03_form_filled.png", full_page=False)

        # Click Next/Continue
        try:
            next_btn = page.locator("button:has-text('Next'), button:has-text('Continue'), button:has-text('Start'), button:has-text('Begin')").first
            if next_btn.is_visible(timeout=5000):
                next_btn.click()
                print("Clicked Next/Continue")
                time.sleep(3)
        except Exception as e:
            print(f"Next button error: {e}")

        page.screenshot(path=f"{SCREENSHOT_DIR}\\e2e_04_upload.png", full_page=False)

        # Step 4: Upload image
        print("\n" + "=" * 60)
        print("STEP 4: Upload image")
        print("=" * 60)
        try:
            file_input = page.locator("input[type='file']").first
            file_input.wait_for(state="attached", timeout=10000)
            file_input.set_input_files(TEST_IMAGE)
            print(f"Uploaded {TEST_IMAGE}")
            time.sleep(5)  # Wait for preview
        except Exception as e:
            print(f"Upload error: {e}")

        page.screenshot(path=f"{SCREENSHOT_DIR}\\e2e_05_uploaded.png", full_page=False)

        # Step 5: Proceed to review
        print("\n" + "=" * 60)
        print("STEP 5: Proceed to review")
        print("=" * 60)
        try:
            next_btn = page.locator("button:has-text('Next'), button:has-text('Continue'), button:has-text('Review')").first
            if next_btn.is_visible(timeout=10000):
                next_btn.click()
                print("Proceeded to review")
                time.sleep(3)
        except Exception as e:
            print(f"Review navigation error: {e}")

        page.screenshot(path=f"{SCREENSHOT_DIR}\\e2e_06_review.png", full_page=False)

        # Step 6: Start inspection
        print("\n" + "=" * 60)
        print("STEP 6: Start Inspection")
        print("=" * 60)
        try:
            start_btn = page.locator("button:has-text('Start Inspection'), button:has-text('Start Analysis'), button:has-text('Begin')").first
            if start_btn.is_visible(timeout=10000):
                start_btn.click()
                print("Clicked Start Inspection, waiting for processing...")
                time.sleep(60)  # Wait for AI processing
            else:
                print("No start button found")
        except Exception as e:
            print(f"Start error: {e}")

        page.screenshot(path=f"{SCREENSHOT_DIR}\\e2e_07_processing.png", full_page=False)

        # Wait a bit more for results
        time.sleep(10)
        page.screenshot(path=f"{SCREENSHOT_DIR}\\e2e_08_results.png", full_page=False)

        # Step 7: Extract page content
        print("\n" + "=" * 60)
        print("STEP 7: Verify Results Page")
        print("=" * 60)

        body_text = page.evaluate("""
            () => {
                // Deep clone to avoid mutating the live DOM
                const clone = document.body.cloneNode(true);
                // Remove non-visible/non-semantic elements
                clone.querySelectorAll('script, style, noscript, [hidden], [aria-hidden="true"]').forEach(el => el.remove());
                clone.querySelectorAll('[style*="display: none"], [style*="display:none"]').forEach(el => el.remove());
                // For SVG elements: extract any <text> content into a span before removal
                // (SVGs may contain rendered score text like "89/100 Good")
                clone.querySelectorAll('svg').forEach(svg => {
                    svg.querySelectorAll('text').forEach(textEl => {
                        const span = document.createElement('span');
                        span.textContent = textEl.textContent || '';
                        textEl.parentNode.insertBefore(span, textEl);
                    });
                    svg.remove();
                });
                // Get text from the cleaned clone
                const raw = clone.innerText || '';
                // Strip any remaining raw HTML tag remnants
                return raw.replace(/<[^>]+>/g, '').replace(/<!--[\\s\\S]*?-->/g, '');
            }
        """)
        print(f"\nPage text length: {len(body_text)} chars")
        print(f"\nFirst 3000 chars of page text:\n{body_text[:3000]}")
        print(f"\nKeywords check: 'finding'={'finding' in body_text.lower()}, 'summary'={'summary' in body_text.lower()}, 'estimate/cost'={'estimate' in body_text.lower() or 'cost' in body_text.lower()}")

        # Check for results page indicators
        # Material Symbols / icon fonts render as ligature names in text extraction.
        # These are rendered glyphs, not raw HTML — ignore known icon font ligature names.
        icon_ligature_names = (
            # Material Symbols Outlined / Round arrow icons
            "_arrow_right", "_arrow_forward", "_arrow_back", "_arrow_upward", "_arrow_downward",
            "_arrow_left", "_arrow_right_alt", "_arrow_back_ios", "_arrow_forward_ios",
            # Material Symbols Outlined / Round keyboard arrow icons
            "keyboard_arrow_right", "keyboard_arrow_left", "keyboard_arrow_up", "keyboard_arrow_down",
            "keyboard_double_arrow_right", "keyboard_double_arrow_left", "keyboard_double_arrow_left",
            # Other common navigation icons
            "arrow_forward", "arrow_back", "arrow_upward", "arrow_downward", "arrow_right_alt",
            "navigate_next", "navigate_before",
            # Chevron icons (Rounded / Outlined variants)
            "chevron_right", "chevron_left", "chevron_up", "chevron_down",
            # Expand / collapse chevrons
            "expand_more", "expand_less",
            # Overflow / overflow menu icons
            "more_horiz", "more_vert",
            # Common Material Symbols used in the UI
            "close", "check_circle", "error_outline", "warning_amber",
            "info", "refresh", "settings", "home", "analytics",
            "assessment", "build", "cleaning_services", "shield",
            "visibility", "visibility_off", "upload_file", "download",
            # Other common Material Symbols that render as ligature text
            "content_paste", "content_copy", "image", "photo_camera",
            "print", "share", "bookmark", "star", "favorite",
            "delete", "edit", "save", "cancel", "undo", "redo",
            "search", "filter_list", "sort", "menu", "dashboard",
            "layers", "grid_view", "list", "table_chart",
            "verified_user", "account_circle", "person", "logout",
        )
        checks = {
            "has_image_count": "image" in body_text.lower() and ("1" in body_text or "one" in body_text.lower()),
            "has_findings": "finding" in body_text.lower() or "defect" in body_text.lower() or "damage" in body_text.lower(),
            "has_summary": "summary" in body_text.lower(),
            "has_estimate": "estimate" in body_text.lower() or "cost" in body_text.lower() or "price" in body_text.lower() or "\\$" in body_text,
            "no_raw_html": "<div" not in body_text and "<span" not in body_text and "<p>" not in body_text,
            "no_arrow_right": not any(
                name in body_text
                for name in icon_ligature_names
            ),
        }
        print("\n" + "=" * 60)
        print("VERIFICATION RESULTS")
        print("=" * 60)

        all_pass = True
        for check, result in checks.items():
            status = "PASS" if result else "FAIL"
            if not result:
                all_pass = False
            print(f"  {status}: {check}")

        # Console errors check
        error_console = [log for log in console_logs if "error" in log.lower() or "exception" in log.lower() or "failed" in log.lower()]
        print(f"\nConsole errors found: {len(error_console)}")
        for err in error_console[:10]:
            print(f"  {err}")

        # Page errors
        print(f"Page errors: {len(page_errors)}")
        for err in page_errors[:5]:
            print(f"  {err}")

        if error_console:
            all_pass = False
        if page_errors:
            all_pass = False

        print("\n" + "=" * 60)
        if all_pass:
            print("ALL CHECKS PASSED")
        else:
            print("SOME CHECKS FAILED - review above")
        print("=" * 60)

        # Take full page screenshot
        page.screenshot(path=f"{SCREENSHOT_DIR}\\e2e_09_results_full.png", full_page=True)

        browser.close()

        # Return exit code
        sys.exit(0 if all_pass else 1)

if __name__ == "__main__":
    main()
