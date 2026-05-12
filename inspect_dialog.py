"""Inspect Feature Flags dialog DOM."""
from playwright.sync_api import sync_playwright

BASE_URL = "http://localhost:8080"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1280, "height": 800})
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(2000)

    # Open feature flags dialog
    ff_btn = page.locator("button:has-text('Feature Flags'), button[title*='eature']").first
    ff_btn.click()
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(2000)

    # Screenshot
    page.screenshot(path="/tmp/ff_dialog.png", full_page=False)
    print("Screenshot saved to /tmp/ff_dialog.png")

    # Print all buttons in dialog
    buttons = page.locator("button").all()
    print(f"\nAll buttons ({len(buttons)}):")
    for b in buttons:
        txt = b.inner_text().replace("\n", " ")[:60]
        cls = b.get_attribute("class") or ""
        role = b.get_attribute("role") or ""
        aria = b.get_attribute("aria-label") or ""
        disabled = b.get_attribute("disabled")
        print(f"  [{txt}] class={cls[:50]} role={role} aria={aria[:40]} disabled={disabled}")

    # Print all text content
    content = page.inner_text("body")
    print(f"\nBody text (first 2000 chars):\n{content[:2000]}")

    browser.close()
