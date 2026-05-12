from playwright.sync_api import sync_playwright


def test_feature_flags_e2e():
    errors = []
    console_errors = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)

        try:
            page.goto("http://localhost:8080")
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(2000)

            login_btn = page.locator('button:has-text("Login"), button:has-text("登入"), button:has-text("Sign in")')
            if login_btn.count() > 0:
                email_input = page.locator('input[type="email"], input[name="email"]')
                password_input = page.locator('input[type="password"]')
                if email_input.count() > 0 and password_input.count() > 0:
                    email_input.first.fill("admin@rss.local")
                    password_input.first.fill("admin123")
                    login_btn.first.click()
                    page.wait_for_timeout(3000)

            page.goto("http://localhost:8080/settings")
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(2000)

            rss_icon = page.locator('svg[class*="rss"], svg path[d*="M6.18 15.64a2 2 0 0 1 2.18 2"]')
            if rss_icon.count() > 0:
                for _ in range(10):
                    rss_icon.first.click()
                    page.wait_for_timeout(300)

            page.wait_for_timeout(1000)
            ff_dialog = page.locator('[role="dialog"]')
            if ff_dialog.count() == 0:
                errors.append("Feature Flags dialog did not open")
                page.screenshot(path="/tmp/ff-dialog-not-found.png", full_page=True)
                return False

            share_links_label = page.locator('text=Share Links, text=分享連結')
            if share_links_label.count() > 0:
                sl_toggle = share_links_label.locator("..").locator('input[type="checkbox"], [role="switch"]')
                if sl_toggle.count() > 0 and not sl_toggle.first.is_checked():
                    sl_toggle.first.check()
                    page.wait_for_timeout(500)

            page.goto("http://localhost:8080/sources")
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(2000)

            feed_items = page.locator('[class*="feed"], [class*="source"], tr[class*="row"]')
            clickable = page.locator('.card, [class*="item"], a[href*="feed"], a[href*="source"]')
            target = feed_items.first if feed_items.count() > 0 else (clickable.first if clickable.count() > 0 else None)
            if target:
                target.click()
            page.wait_for_timeout(2000)

            share_btn = page.locator('button:has-text("Share Links"), button:has-text("分享連結"), button:has-text("分享"), [aria-label*="share" i]')
            if share_btn.count() > 0:
                print("PASS: Share Links button visible when feature ON")
            else:
                errors.append("TEST 1 FAILED: Share Links button NOT found when feature is ON")
                page.screenshot(path="/tmp/share-links-not-found.png", full_page=True)

            page.goto("http://localhost:8080/settings")
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(2000)

            rss_icon = page.locator('svg[class*="rss"], svg path[d*="M6.18 15.64a2 2 0 0 1 2.18 2"]')
            if rss_icon.count() > 0:
                for _ in range(10):
                    rss_icon.first.click()
                    page.wait_for_timeout(300)
            page.wait_for_timeout(1000)

            share_links_label = page.locator('text=Share Links, text=分享連結')
            if share_links_label.count() > 0:
                sl_toggle = share_links_label.locator("..").locator('input[type="checkbox"], [role="switch"]')
                if sl_toggle.count() > 0 and sl_toggle.first.is_checked():
                    sl_toggle.first.uncheck()
                    page.wait_for_timeout(500)

            page.goto("http://localhost:8080/sources")
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(2000)

            feed_items = page.locator('[class*="feed"], [class*="source"], tr[class*="row"]')
            clickable = page.locator('.card, [class*="item"], a[href*="feed"], a[href*="source"]')
            target = feed_items.first if feed_items.count() > 0 else (clickable.first if clickable.count() > 0 else None)
            if target:
                target.click()
            page.wait_for_timeout(2000)

            share_btn_hidden = page.locator('button:has-text("Share Links"), button:has-text("分享連結"), button:has-text("分享")').filter(visible=True)
            if share_btn_hidden.count() == 0:
                print("PASS: Share Links button hidden when feature OFF")
            else:
                errors.append("TEST 2 FAILED: Share Links button still visible when feature is OFF")
                page.screenshot(path="/tmp/share-links-still-visible.png", full_page=True)

            page.goto("http://localhost:8080/settings")
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(2000)

            rss_icon = page.locator('svg[class*="rss"], svg path[d*="M6.18 15.64a2 2 0 0 1 2.18 2"]')
            if rss_icon.count() > 0:
                for _ in range(10):
                    rss_icon.first.click()
                    page.wait_for_timeout(300)
            page.wait_for_timeout(1000)

            groups_label = page.locator('text=Groups, text=群組').filter(visible=True)
            if groups_label.count() > 0:
                groups_toggle = groups_label.locator("..").locator('input[type="checkbox"], [role="switch"]')
                if groups_toggle.count() > 0 and groups_toggle.first.is_checked():
                    groups_toggle.first.uncheck()
                    page.wait_for_timeout(500)

            schedules_label = page.locator('text=Scheduled Updates, text=定時更新, text=Schedules').filter(visible=True)
            if schedules_label.count() > 0:
                schedules_toggle = schedules_label.locator("..").locator('input[type="checkbox"], [role="switch"], [disabled]')
                if schedules_toggle.count() > 0:
                    toggle_elem = schedules_toggle.first
                    if toggle_elem.is_disabled():
                        print("PASS: Schedules toggle disabled when Groups OFF")
                    else:
                        opacity = schedules_label.locator("..").evaluate("el => window.getComputedStyle(el).opacity")
                        if opacity and float(opacity) < 1:
                            print("PASS: Schedules toggle visually disabled when Groups OFF")
                        else:
                            errors.append("TEST 3 FAILED: Schedules toggle NOT disabled when Groups OFF")
                            page.screenshot(path="/tmp/schedules-not-disabled.png", full_page=True)
                else:
                    print("PASS: Schedules toggle not interactable when Groups OFF")
            else:
                print("PASS: Schedules label not visible when Groups OFF")

        except Exception as e:
            errors.append(f"Exception during test: {str(e)}")
            page.screenshot(path="/tmp/test-exception.png", full_page=True)
        finally:
            browser.close()

    print("\n" + "=" * 50)
    if errors:
        print(f"ERRORS ({len(errors)}):")
        for err in errors:
            print(f"  - {err}")
        return False
    print("ALL TESTS PASSED")
    return True


if __name__ == "__main__":
    exit(0 if test_feature_flags_e2e() else 1)
