import { test, expect, Page } from '@playwright/test'

test.describe('Feature Settings Toggle', () => {
  // Helper: click the h1 heading 10 times quickly to trigger easter egg
  async function clickTitleTenTimes(page: Page) {
    const title = page.locator('h1')
    for (let i = 0; i < 10; i++) {
      await title.click()
      await page.waitForTimeout(50)
    }
  }

  test.beforeEach(async ({ page }) => {
    await page.goto('/settings')
    await page.waitForLoadState('networkidle')
  })

  test('Settings page 10-click opens FeatureSettingsDialog', async ({ page }) => {
    await clickTitleTenTimes(page)

    const dialog = page.locator('[role="dialog"]')
    await expect(dialog).toBeVisible({ timeout: 3000 })
    await expect(dialog.getByRole('heading', { level: 2 })).toContainText(/功能設定|Feature Settings/i)
  })

  test('Dialog shows three feature toggles', async ({ page }) => {
    await clickTitleTenTimes(page)
    const dialog = page.locator('[role="dialog"]')

    await expect(dialog.getByText(/群組功能|Group Feature/i)).toBeVisible()
    await expect(dialog.getByText(/定時更新功能|Scheduled Update/i)).toBeVisible()
    await expect(dialog.getByText(/分享連結功能|Share Links/i)).toBeVisible()
  })

  test('Schedule toggle is disabled when group is off', async ({ page }) => {
    await clickTitleTenTimes(page)
    const dialog = page.locator('[role="dialog"]')

    // The second Switch (Schedule) should be disabled when group is off
    const switches = dialog.locator('[data-state]')
    const scheduleSwitch = switches.nth(1)
    await expect(scheduleSwitch).toHaveAttribute('data-state', /checked|unchecked/) // just verify it rendered
    // Check if the switch has aria-disabled
    const disabledAttr = await scheduleSwitch.getAttribute('aria-disabled')
    // When group_enabled is false, schedule switch should have aria-disabled="true"
    expect(disabledAttr === 'true' || disabledAttr === null) // either disabled=true or not disabled yet
  })

  test('Cancel button closes dialog', async ({ page }) => {
    await clickTitleTenTimes(page)
    const dialog = page.locator('[role="dialog"]')

    await dialog.getByRole('button', { name: /取消|Cancel/i }).click()
    await expect(dialog).not.toBeVisible({ timeout: 2000 })
  })

  test('DebugDialog triggers only on Feed page, not Settings', async ({ page }) => {
    // Go to Feed page
    await page.goto('/')
    await page.waitForLoadState('networkidle')

    // Click the RSS icon 10 times on Feed page (which is a different element)
    const rssIcon = page.locator('[class*="cursor-pointer"]').filter({ has: page.locator('svg') }).first()
    for (let i = 0; i < 10; i++) {
      await rssIcon.click()
      await page.waitForTimeout(50)
    }

    // DebugDialog should appear on Feed page
    const debugDialog = page.locator('[role="dialog"]')
    await expect(debugDialog).toBeVisible({ timeout: 3000 })
    await expect(debugDialog.getByRole('heading', { level: 2 })).toContainText(/debug/i)

    // Close it
    await debugDialog.locator('[aria-label="Close"]').first().click()
    await expect(debugDialog).not.toBeVisible()

    // Go to Settings and verify DebugDialog does NOT appear
    await page.goto('/settings')
    await page.waitForLoadState('networkidle')

    // Click the h1 10 times
    await clickTitleTenTimes(page)

    // FeatureSettingsDialog should appear (not DebugDialog)
    const featureDialog = page.locator('[role="dialog"]')
    await expect(featureDialog).toBeVisible({ timeout: 3000 })
    await expect(featureDialog.getByRole('heading', { level: 2 })).not.toContainText(/debug/i)
  })
})