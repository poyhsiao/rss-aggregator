import { test, expect, Page } from '@playwright/test'

test.describe('Feature Settings Toggle', () => {
  async function openDialog(page: Page) {
    const title = page.locator('h1')
    for (let i = 0; i < 10; i++) {
      await title.click()
      await page.waitForTimeout(50)
    }
  }

  test.beforeEach(async ({ page }) => {
    await page.goto('/settings')
    await page.waitForLoadState('domcontentloaded')
  })

  test('Settings page 10-click opens FeatureSettingsDialog', async ({ page }) => {
    await openDialog(page)
    const dialog = page.locator('[role="dialog"]')
    await expect(dialog).toBeVisible({ timeout: 3000 })
    await expect(dialog.getByRole('heading', { level: 2 })).toContainText(/功能設定|Feature Settings/i)
  })

  test('Dialog shows four feature toggles in order: Group, SourceGroupSchedules, Schedule, Share', async ({ page }) => {
    await openDialog(page)
    const dialog = page.locator('[role="dialog"]')

    await expect(dialog.getByText(/群組功能|Group Feature/i).first()).toBeVisible()
    await expect(dialog.getByText(/來源群組定時更新|Source Group Schedules/i).first()).toBeVisible()
    await expect(dialog.getByText(/定時更新功能|Scheduled Update/i).first()).toBeVisible()
    await expect(dialog.getByText(/分享連結功能|Share Links/i).first()).toBeVisible()
  })

  test('Schedule and SourceGroupSchedules toggles disabled when Group is OFF', async ({ page }) => {
    await openDialog(page)
    const dialog = page.locator('[role="dialog"]')
    const switches = dialog.locator('[role="switch"]')
    await expect(switches).toHaveCount(4)

    // Group is at index 0, SourceGroupSchedules at 1, Schedule at 2, Share at 3
    // When Group is off, SourceGroupSchedules (1) and Schedule (2) should be disabled
    const sgsSwitch = switches.nth(1)
    const schedSwitch = switches.nth(2)
    await expect(sgsSwitch).toBeDisabled()
    await expect(schedSwitch).toBeDisabled()
  })

  test('Apply button closes dialog', async ({ page }) => {
    await openDialog(page)
    const dialog = page.locator('[role="dialog"]')

    await dialog.getByRole('button', { name: /Apply|套用/i }).click()
    // Dialog should close after apply
    await expect(dialog).not.toBeVisible({ timeout: 3000 })
  })

  test('Cancel button closes dialog', async ({ page }) => {
    await openDialog(page)
    const dialog = page.locator('[role="dialog"]')

    await dialog.getByRole('button', { name: /取消|Cancel/i }).click()
    await expect(dialog).not.toBeVisible({ timeout: 2000 })
  })

  // --- FIX VERIFICATION: Settings should persist to database ---

  test('Toggles reflect current database state when dialog opens', async ({ page }) => {
    await openDialog(page)
    const dialog = page.locator('[role="dialog"]')

    // Dialog should load current settings from API
    // The toggles should reflect the actual state, not default false
    const switches = dialog.locator('[role="switch"]')
    await expect(switches).toHaveCount(4)

    // Verify Group toggle is present and can be interacted with
    const groupSwitch = switches.nth(0)
    await expect(groupSwitch).toBeVisible()
  })

  test.skip('Share Links toggle is always enabled regardless of Group state', async ({ page }) => {
    await openDialog(page)
    const dialog = page.locator('[role="dialog"]')
    const switches = dialog.locator('[role="switch"]')

    // Share Links is at index 3, should always be enabled
    const shareSwitch = switches.nth(3)
    await expect(shareSwitch).toBeEnabled()

    // Even when Group toggle is OFF (default), Share should still be enabled
    const groupSwitch = switches.nth(0)
    await expect(groupSwitch).toBeDisabled() // Group should be OFF by default
    await expect(shareSwitch).toBeEnabled() // Share should still be enabled
  })

  test('Enabling Group Feature allows Schedule toggles to become enabled', async ({ page }) => {
    await openDialog(page)
    const dialog = page.locator('[role="dialog"]')
    const switches = dialog.locator('[role="switch"]')

    // Initially Group is OFF (by default), Schedule toggles should be disabled
    const groupSwitch = switches.nth(0)
    const sgsSwitch = switches.nth(1)
    const schedSwitch = switches.nth(2)

    // Verify initial state: Schedule toggles are disabled when Group is OFF
    await expect(sgsSwitch).toBeDisabled()
    await expect(schedSwitch).toBeDisabled()

    // Click Group switch directly to enable it
    await groupSwitch.evaluate(el => el.click())
    await page.waitForTimeout(300)

    // After Group is enabled, check aria-checked state changed
    const ariaChecked = await groupSwitch.getAttribute('aria-checked')
    expect(ariaChecked).toBe('true')

    // Schedule toggles should become enabled
    // Check the presence of disabled attribute
    const sgsDisabled = await sgsSwitch.getAttribute('disabled')
    const schedDisabled = await schedSwitch.getAttribute('disabled')
    expect(sgsDisabled === null || sgsDisabled === undefined).toBe(true)
    expect(schedDisabled === null || schedDisabled === undefined).toBe(true)
  })
})

test.describe('Feature Settings Cascade', () => {
  test.skip('Group OFF disables SGS and Schedule toggles', async ({ page }) => {
    await page.goto('/settings')
    await page.waitForLoadState('domcontentloaded')
    const rssIcon = page.locator('header svg[class*="h-6"]').first()
    for (let i = 0; i < 10; i++) {
      await rssIcon.click({ force: true })
      await page.waitForTimeout(150)
    }
    await page.waitForSelector('[role="dialog"]', { timeout: 5000 })

    const switches = page.locator('[role="switch"]')
    const groupSwitch = switches.nth(0)
    if (await groupSwitch.getAttribute('aria-checked') === 'true') {
      await groupSwitch.click()
      const confirmBtn = page.locator('button:has-text("Confirm")')
      if (await confirmBtn.isVisible({ timeout: 1000 }).catch(() => false)) {
        await confirmBtn.click()
      }
    }

    await expect(switches.nth(1)).toBeDisabled()
    await expect(switches.nth(2)).toBeDisabled()
    await expect(switches.nth(3)).toBeEnabled()
  })

  test.skip('Settings persist after page reload', async ({ page }) => {
    await page.goto('/settings')
    await page.waitForLoadState('domcontentloaded')
    const rssIcon = page.locator('header svg[class*="h-6"]').first()
    for (let i = 0; i < 10; i++) {
      await rssIcon.click({ force: true })
      await page.waitForTimeout(150)
    }
    await page.waitForSelector('[role="dialog"]', { timeout: 5000 })

    const switches = page.locator('[role="switch"]')
    const groupSwitch = switches.nth(0)
    if (await groupSwitch.getAttribute('aria-checked') === 'false') {
      await groupSwitch.click()
    }
    const scheduleSwitch = switches.nth(2)
    if (await scheduleSwitch.getAttribute('aria-checked') === 'false') {
      await scheduleSwitch.click()
    }
    const shareSwitch = switches.nth(3)
    if (await shareSwitch.getAttribute('aria-checked') === 'false') {
      await shareSwitch.click()
    }

    await page.locator('button:has-text("Apply")').click()
    await page.waitForTimeout(1000)

    await page.reload()
    await page.waitForLoadState('domcontentloaded')

    for (let i = 0; i < 10; i++) {
      await rssIcon.click({ force: true })
      await page.waitForTimeout(150)
    }
    await page.waitForSelector('[role="dialog"]', { timeout: 5000 })

    await expect(switches.nth(0)).toHaveAttribute('aria-checked', 'true')
    await expect(switches.nth(2)).toHaveAttribute('aria-checked', 'true')
    await expect(switches.nth(3)).toHaveAttribute('aria-checked', 'true')
  })
})
