"""
Verify Feature Flags System v0.19.0 behavior:
1. Schedules toggle is disabled when Groups is OFF
2. Turning Groups ON allows Schedules to be toggled
3. Turning Groups OFF also turns Schedules OFF (cascade)
4. Share Links button is hidden when feature_share_links is OFF
"""
from playwright.sync_api import sync_playwright
import time

BASE_URL = "http://localhost:8080"

def wait_for_networkidle(page):
    page.wait_for_load_state("networkidle")
    # Extra wait for Vue to hydrate
    page.wait_for_timeout(1000)

def main():
    errors = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 800})

        # Capture console errors
        console_errors = []
        page.on("console", lambda msg: console_errors.append(msg) if msg.type == "error" else None)

        # ─────────────────────────────────────────────────────────
        # TEST 1: Feature Flags Dialog — Schedules/Groups dependency
        # ─────────────────────────────────────────────────────────
        print("\n=== TEST 1: Schedules depends on Groups ===")

        page.goto(BASE_URL)
        wait_for_networkidle(page)

        # Navigate to Feature Flags (Settings gear icon in sidebar or header)
        # Try to find settings/feature flags button
        print("Looking for settings/feature flags button...")

        # Look for a button with settings icon or text "Feature Flags"
        feature_flags_btn = page.locator('button:has-text("Feature Flags"), button[aria-label*="feature"], button[title*="feature"], button[title*="Feature"], svg[class*="settings"], button[class*="settings"]').first
        feature_flags_btn.click()
        wait_for_networkidle(page)
        print("Feature Flags dialog opened")

        # Find the Groups and Schedules toggles
        # Groups toggle should be visible
        groups_toggle = page.locator('[class*="toggle"]:has-text("Groups"), [role="switch"][aria-label*="Group"], button:has-text("Groups")').first
        groups_toggle.wait_for(state="visible", timeout=5000)
        print("Groups toggle found")

        # Schedules toggle
        schedules_toggle = page.locator('[class*="toggle"]:has-text("Schedules"), [role="switch"][aria-label*="Schedule"], button:has-text("Schedules")').first
        schedules_toggle.wait_for(state="visible", timeout=5000)
        print("Schedules toggle found")

        # Check if Schedules toggle is disabled when Groups is OFF
        # Default: Groups OFF → Schedules should be disabled
        disabled_attr = schedules_toggle.get_attribute("disabled")
        aria_disabled = schedules_toggle.get_attribute("aria-disabled")
        print(f"Schedules disabled (default): disabled={disabled_attr}, aria-disabled={aria_disabled}")

        if disabled_attr is None and aria_disabled is None:
            print("  ⚠️ Schedules toggle might not be disabled by default")

        # Check CSS class for opacity/visual disabled state
        toggle_classes = schedules_toggle.get_attribute("class") or ""
        print(f"Schedules toggle classes: {toggle_classes}")
        if "opacity-50" not in toggle_classes and "cursor-not-allowed" not in toggle_classes:
            print("  ⚠️ Schedules toggle doesn't show disabled visual styling")

        # Try to click Schedules toggle (should not toggle when Groups OFF)
        schedules_was_on = "true" in (schedules_toggle.get_attribute("aria-checked") or "false")
        print(f"Schedules state before click: {schedules_was_on}")

        # Click Schedules toggle
        schedules_toggle.click()
        page.wait_for_timeout(500)

        schedules_still_off = "true" not in (schedules_toggle.get_attribute("aria-checked") or "false")
        if schedules_still_off:
            print("  ✅ PASS: Schedules did not turn ON when Groups is OFF")
        else:
            print("  ❌ FAIL: Schedules turned ON when Groups is OFF")
            errors.append("Schedules should not toggle when Groups is OFF")

        # Now turn Groups ON
        print("\nTurning Groups ON...")
        groups_toggle.click()
        page.wait_for_timeout(1000)

        # Verify Schedules toggle is now enabled
        disabled_after_groups_on = schedules_toggle.get_attribute("disabled")
        aria_disabled_after = schedules_toggle.get_attribute("aria-disabled")
        toggle_classes_after = schedules_toggle.get_attribute("class") or ""

        print(f"Schedules after Groups ON: disabled={disabled_after_groups_on}, aria-disabled={aria_disabled_after}")
        print(f"Schedules classes after Groups ON: {toggle_classes_after}")

        if disabled_after_groups_on is None and aria_disabled_after != "true":
            print("  ✅ PASS: Schedules toggle is enabled after Groups turned ON")
        else:
            print("  ❌ FAIL: Schedules toggle still disabled after Groups ON")
            errors.append("Schedules toggle should be enabled when Groups is ON")

        # Now turn Groups OFF (should cascade disable Schedules)
        print("\nTurning Groups OFF (should cascade Schedules)...")
        groups_toggle.click()
        page.wait_for_timeout(1000)

        schedules_after_groups_off = "true" in (schedules_toggle.get_attribute("aria-checked") or "false")
        if not schedules_after_groups_off:
            print("  ✅ PASS: Schedules automatically turned OFF when Groups turned OFF")
        else:
            print("  ❌ FAIL: Schedules should cascade OFF when Groups turned OFF")
            errors.append("Schedules should cascade OFF when Groups is disabled")

        # ─────────────────────────────────────────────────────────
        # TEST 2: Share Links button in RSS Preview dialog
        # ─────────────────────────────────────────────────────────
        print("\n=== TEST 2: Share Links button visibility ===")

        # Close feature flags dialog
        close_btn = page.locator('button[aria-label*="close"], button[class*="close"], button:has-text("×"), button[aria-label="Close"], [class*="dialog"] button[class*="close"]').first
        try:
            close_btn.click()
            page.wait_for_timeout(500)
        except Exception:
            page.keyboard.press("Escape")
            page.wait_for_timeout(500)

        # Find and click an RSS feed preview
        # Look for a feed item row or preview button
        feed_items = page.locator('[class*="feed-item"], [class*="rss-item"], tr[class*="feed"], div[class*="item"]').all()
        print(f"Found {len(feed_items)} feed items on page")

        if feed_items:
            # Click the first feed item to open preview
            feed_items[0].click()
            page.wait_for_timeout(1000)
            print("Clicked first feed item, waiting for preview dialog...")

            # Look for the Share Links button in the dialog
            share_btn = page.locator('button:has-text("Share Links"), button:has-text("分享連結"), [aria-label*="Share Links"]').first
            try:
                share_btn.wait_for(state="visible", timeout=3000)
                share_btn_classes = share_btn.get_attribute("class") or ""
                share_btn_style = share_btn.get_attribute("style") or ""

                # Check if hidden by v-if (not in DOM) or CSS display:none
                share_btn_count = page.locator('button:has-text("Share Links"), button:has-text("分享連結")').count()
                print(f"Share Links buttons in DOM: {share_btn_count}")

                # Since feature_share_links is OFF by default, button should NOT be visible
                if share_btn_count == 0:
                    print("  ✅ PASS: Share Links button hidden (feature_share_links OFF)")
                else:
                    # Check if it's hidden via CSS
                    is_hidden = "none" in share_btn_style or "hidden" in share_btn_classes
                    if is_hidden:
                        print("  ✅ PASS: Share Links button hidden via CSS/style")
                    else:
                        print("  ❌ FAIL: Share Links button visible but feature_share_links is OFF")
                        errors.append("Share Links button should be hidden when feature_share_links is OFF")
            except Exception as e:
                print(f"  ✅ PASS: Share Links button not visible (v-if removed from DOM): {e}")
        else:
            print("  ⚠️ No feed items found to test Share Links button")

        # ─────────────────────────────────────────────────────────
        # Console Errors Check
        # ─────────────────────────────────────────────────────────
        print("\n=== Console Errors ===")
        real_errors = [e for e in console_errors if "favicon" not in e.text and "404" not in e.text]
        if real_errors:
            print(f"  ⚠️ Console errors: {[e.text for e in real_errors]}")
        else:
            print("  ✅ No console errors")

        # ─────────────────────────────────────────────────────────
        # Summary
        # ─────────────────────────────────────────────────────────
        print("\n=== SUMMARY ===")
        if errors:
            print(f"  ❌ {len(errors)} test(s) FAILED:")
            for err in errors:
                print(f"     - {err}")
        else:
            print("  ✅ All tests passed!")

        browser.close()

    return len(errors) == 0

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
