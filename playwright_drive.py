"""Playwright script to drive the Streamlit app and screenshot the Results page."""
from playwright.sync_api import sync_playwright, expect
import time

# Path to test image
TEST_IMAGE = r"c:\Users\pjaya\OneDrive\Desktop\InspectAI - AI Property Inspection Platform\test_damaged_wall.jpg"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(viewport={'width': 1440, 'height': 900})
    page = context.new_page()

    # Listen for console messages
    console_logs = []
    def handle_console(msg):
        console_logs.append(f"[{msg.type}] {msg.text}")
    page.on("console", handle_console)

    # Navigate to app
    print("Navigating to app...")
    page.goto("http://localhost:8501", wait_until="networkidle", timeout=60000)
    time.sleep(3)

    # Take screenshot of initial state
    page.screenshot(path=r"c:\Users\pjaya\OneDrive\Desktop\InspectAI - AI Property Inspection Platform\screenshot_01_dashboard.png")
    print("Screenshot 1: Dashboard")

    # Click "New Inspection" or navigate to step 1
    try:
        # Look for "New Inspection" button/link
        new_inspection = page.locator("text=New Inspection").first
        if new_inspection.is_visible(timeout=5000):
            new_inspection.click()
            time.sleep(2)
            page.screenshot(path=r"c:\Users\pjaya\OneDrive\Desktop\InspectAI - AI Property Inspection Platform\screenshot_02_new_inspection.png")
            print("Screenshot 2: New Inspection page")
    except Exception as e:
        print(f"Could not click New Inspection: {e}")

    # Fill property details
    try:
        # Fill property name
        text_inputs = page.locator("input[type='text']").all()
        if text_inputs:
            text_inputs[0].fill("Test Wall")
            time.sleep(0.5)

        # Click Next/Continue button
        next_btn = page.locator("button:has-text('Next'), button:has-text('Continue'), button:has-text('Start')").first
        if next_btn.is_visible(timeout=5000):
            next_btn.click()
            time.sleep(2)
            page.screenshot(path=r"c:\Users\pjaya\OneDrive\Desktop\InspectAI - AI Property Inspection Platform\screenshot_03_upload.png")
            print("Screenshot 3: Upload page")
    except Exception as e:
        print(f"Could not fill property details: {e}")

    # Upload image
    try:
        file_input = page.locator("input[type='file']").first
        if file_input.is_attached(timeout=5000):
            file_input.set_input_files(TEST_IMAGE)
            time.sleep(2)
            page.screenshot(path=r"c:\Users\pjaya\OneDrive\Desktop\InspectAI - AI Property Inspection Platform\screenshot_04_image_uploaded.png")
            print("Screenshot 4: Image uploaded")
    except Exception as e:
        print(f"Could not upload image: {e}")

    # Click to proceed to review
    try:
        next_btn = page.locator("button:has-text('Next'), button:has-text('Continue'), button:has-text('Review')").first
        if next_btn.is_visible(timeout=5000):
            next_btn.click()
            time.sleep(2)
            page.screenshot(path=r"c:\Users\pjaya\OneDrive\Desktop\InspectAI - AI Property Inspection Platform\screenshot_05_review.png")
            print("Screenshot 5: Review page")
    except Exception as e:
        print(f"Could not proceed to review: {e}")

    # Click to start inspection
    try:
        start_btn = page.locator("button:has-text('Start Inspection'), button:has-text('Start Analysis'), button:has-text('Begin')").first
        if start_btn.is_visible(timeout=5000):
            start_btn.click()
            print("Clicked Start Inspection, waiting for processing...")
            # Wait for processing to complete (up to 60 seconds)
            time.sleep(45)
            page.screenshot(path=r"c:\Users\pjaya\OneDrive\Desktop\InspectAI - AI Property Inspection Platform\screenshot_06_processing_complete.png")
            print("Screenshot 6: After processing")
    except Exception as e:
        print(f"Could not start inspection: {e}")

    # Wait for results page to fully load
    time.sleep(5)

    # Take final screenshot of Results page
    page.screenshot(path=r"c:\Users\pjaya\OneDrive\Desktop\InspectAI - AI Property Inspection Platform\screenshot_07_results_full.png", full_page=True)
    print("Screenshot 7: Results page (full page)")

    # Extract all visible text from the page
    body_text = page.evaluate("document.body.innerText")
    print("\n=== FULL PAGE TEXT ===")
    print(body_text[:3000])
    print("=== END PAGE TEXT ===\n")

    # Extract specific elements
    print("\n=== EXTRACTING KEY VALUES ===")

    # Try to find total_images
    try:
        total_images_text = page.evaluate("""
            () => {
                const elements = Array.from(document.querySelectorAll('*'));
                for (const el of elements) {
                    if (el.children.length === 0 && el.textContent.includes('image') && el.textContent.includes('analysis')) {
                        return el.textContent.trim();
                    }
                }
                return 'NOT FOUND';
            }
        """)
        print(f"total_images context: {total_images_text}")
    except Exception as e:
        print(f"Error extracting total_images: {e}")

    # Get all text content
    all_text = page.evaluate("document.body.innerText")
    lines = [line.strip() for line in all_text.split('\n') if line.strip()]

    print("\n=== ALL TEXT LINES ===")
    for i, line in enumerate(lines[:100]):
        print(f"{i}: {line}")

    browser.close()
    print("\nDone!")
