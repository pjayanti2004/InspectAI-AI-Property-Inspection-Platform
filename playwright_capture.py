"""Playwright script v4 — navigate directly to New Inspection and interact with form."""
from playwright.sync_api import sync_playwright
import time
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

TEST_IMAGE = r"c:\Users\pjaya\OneDrive\Desktop\InspectAI - AI Property Inspection Platform\test_damaged_wall.jpg"
URL = "http://localhost:8501"
SCREENSHOT_DIR = r"c:\Users\pjaya\OneDrive\Desktop\InspectAI - AI Property Inspection Platform"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context(viewport={'width': 1440, 'height': 900})
    page = context.new_page()

    print("Navigating to New Inspection page...", flush=True)
    # Navigate directly to new inspection page
    page.goto(f"{URL}/?page=new_inspection", wait_until="domcontentloaded", timeout=60000)
    time.sleep(10)

    # Screenshot 2: New Inspection form
    page.screenshot(path=f"{SCREENSHOT_DIR}\\screenshot_02_form.png")
    print("Screenshot 2: New Inspection form saved", flush=True)

    # Get all Streamlit components
    body_text = page.evaluate("document.body.innerText")
    print(f"Body text (first 800 chars): {body_text[:800]}", flush=True)

    # Try to find all input elements
    inputs = page.locator("input").all()
    print(f"\nFound {len(inputs)} input elements", flush=True)
    for i, inp in enumerate(inputs[:15]):
        try:
            attrs = inp.evaluate("el => ({type: el.type, placeholder: el.placeholder, value: el.value})")
            print(f"  Input {i}: {attrs}", flush=True)
        except Exception as e:
            print(f"  Input {i}: Error - {e}", flush=True)

    # Try to find all buttons
    buttons = page.locator("button").all()
    print(f"\nFound {len(buttons)} buttons", flush=True)
    for i, btn in enumerate(buttons[:10]):
        try:
            text = btn.inner_text(timeout=1000)
            print(f"  Button {i}: '{text}'", flush=True)
        except Exception as e:
            print(f"  Button {i}: Error - {e}", flush=True)

    # Try to find select boxes
    selects = page.locator("select").all()
    print(f"\nFound {len(selects)} select elements", flush=True)

    browser.close()
    print("\nDone!", flush=True)
