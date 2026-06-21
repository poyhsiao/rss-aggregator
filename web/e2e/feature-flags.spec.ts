import { test, expect } from '@playwright/test'

test.describe('Feature Flags', () => {
  // Helper: navigate to settings and open feature flags dialog
  async function openFeatureFlagsDialog(page: any) {
    await page.goto('/settings')
    await page.waitForLoadState('domcontentloaded')
    // Wait for Vue to be fully mounted
    await page.waitForTimeout(500)

    // Click the RSS icon in header 10 times - need to use partial class match
    // The RSS icon has classes: "lucide lucide-rss-icon h-6 w-6 cursor-pointer select-none"
    const rssIcon = page.locator('header svg[class*="h-6"]').first()
    for (let i = 0; i < 10; i++) {
      await rssIcon.click({ force: true })
      await page.waitForTimeout(150)
    }

    // Wait for dialog to appear
    await page.waitForSelector('[role="dialog"]', { timeout: 5000 })
  }

  test.beforeEach(async ({ page }) => {
    // Navigate to settings first to ensure localStorage is accessible
    await page.goto('/settings')
    await page.waitForLoadState('domcontentloaded')
    // Clear localStorage after page loads
    await page.evaluate(() => {
      localStorage.removeItem('ff_groups_enabled')
      localStorage.removeItem('ff_group_schedules_enabled')
    })
  })

  test.skip('trigger dialog by clicking Settings RSS icon 10 times', async ({ page }) => {
    const rssIcon = page.locator('header svg[class*="h-6"]').first()
    for (let i = 0; i < 10; i++) {
      await rssIcon.click({ timeout: 5000 }).catch(async () => {
        await page.waitForTimeout(200)
        await rssIcon.click({ force: true })
      })
      await page.waitForTimeout(150)
    }

    // Dialog should be visible
    await expect(page.locator('[role="dialog"]')).toBeVisible()
    // Title should contain the Feature Flags text
    await expect(page.locator('[role="dialog"]')).toContainText('Feature Flags')
    await expect(page.locator('[role="dialog"]')).toContainText('Groups Feature')
  })

  // Helper to find toggle buttons inside dialog
  function getToggleLocator(dialogLocator: any) {
    // Find all buttons inside the dialog that have the toggle appearance
    // They are: relative, inline-flex, rounded-full with a white circle inside
    return dialogLocator.locator('button:has(span.rounded-full.bg-white)')
  }

  test.skip('cascade cancel — Groups stays ON when Cancel clicked', async ({ page }) => {
    // Open dialog
    await openFeatureFlagsDialog(page)
    const dialog = page.locator('[role="dialog"]')

    // Get first toggle (Groups toggle)
    const groupsToggle = getToggleLocator(dialog).first()

    // Click to turn OFF groups
    await groupsToggle.click({ force: true })
    await page.waitForTimeout(200)

    // Warning should appear
    await expect(dialog).toContainText('Disabling groups will also disable schedules')

    // Click Cancel
    await dialog.locator('button:has-text("Cancel")').click()
    await page.waitForTimeout(200)

    // Groups should still be ON (null or 'true')
    const isOn = await page.evaluate(() => {
      return localStorage.getItem('ff_groups_enabled') === 'true' || localStorage.getItem('ff_groups_enabled') === null
    })
    expect(isOn).toBeTruthy()
  })

  test.skip('cascade confirm — Groups OFF and Schedules auto-disabled', async ({ page }) => {
    // Open dialog
    await openFeatureFlagsDialog(page)
    const dialog = page.locator('[role="dialog"]')

    // Turn OFF Groups toggle
    await getToggleLocator(dialog).first().click({ force: true })
    await page.waitForTimeout(200)

    // Click Confirm on warning
    await dialog.locator('button:has-text("Confirm")').first().click()
    await page.waitForTimeout(200)

    // Dialog should close
    await expect(dialog).not.toBeVisible()

    // Verify localStorage
    const stored = await page.evaluate(() => ({
      groups: localStorage.getItem('ff_groups_enabled'),
      schedules: localStorage.getItem('ff_group_schedules_enabled')
    }))
    expect(stored.groups).toBe('false')
    expect(stored.schedules).toBe('false')
  })

  test('visibility — Groups tab hidden when groups_enabled is OFF', async ({ page }) => {
    await page.goto('/settings')
    await page.waitForLoadState('domcontentloaded')
    await page.evaluate(() => {
      localStorage.setItem('ff_groups_enabled', 'false')
      localStorage.setItem('ff_group_schedules_enabled', 'false')
    })
    await page.goto('/sources')
    await page.waitForLoadState('domcontentloaded')

    // Groups tab should not be visible
    const groupsTab = page.locator('button', { hasText: 'groups' }).or(page.locator('button', { hasText: '群組' }))
    await expect(groupsTab).not.toBeVisible()
  })

  test.skip('persistence — changes survive page reload', async ({ page }) => {
    // Open dialog
    await openFeatureFlagsDialog(page)
    const dialog = page.locator('[role="dialog"]')

    // Turn OFF Groups
    await getToggleLocator(dialog).first().click({ force: true })
    await page.waitForTimeout(200)

    // If warning shows, confirm it
    const warningConfirm = dialog.locator('button:has-text("Confirm")').first()
    if (await warningConfirm.isVisible()) {
      await warningConfirm.click()
    } else {
      await dialog.locator('button:has-text("Confirm")').click()
    }
    await page.waitForTimeout(200)

    // Reload and check persistence
    await page.reload()
    await page.waitForLoadState('domcontentloaded')
    const groupsOff = await page.evaluate(() => localStorage.getItem('ff_groups_enabled') === 'false')
    expect(groupsOff).toBeTruthy()
  })

  test.skip('dialog is properly sized and all controls visible', async ({ page }) => {
    // Set viewport to standard desktop size
    await page.setViewportSize({ width: 1280, height: 800 })

    // Open dialog
    await openFeatureFlagsDialog(page)

    // Get dialog bounding box
    const dialogBox = await page.locator('[role="dialog"]').boundingBox()
    expect(dialogBox).not.toBeNull()
    expect(dialogBox!.width).toBeGreaterThanOrEqual(400)

    // All toggle switches should be visible (Groups and Schedules)
    const dialog = page.locator('[role="dialog"]')
    const toggles = getToggleLocator(dialog)
    await expect(toggles).toHaveCount(2)

    // Confirm button should be visible and not truncated
    const confirmBtn = dialog.locator('button:has-text("Confirm")').first()
    await expect(confirmBtn).toBeVisible()
    const btnBox = await confirmBtn.boundingBox()
    expect(btnBox!.width).toBeGreaterThanOrEqual(80)
  })

  test.skip('dialog is responsive on mobile viewport', async ({ page }) => {
    // Set viewport to mobile size
    await page.setViewportSize({ width: 375, height: 667 })

    // Open dialog
    await openFeatureFlagsDialog(page)

    // Toggle switches should still be clickable
    const dialog = page.locator('[role="dialog"]')
    await getToggleLocator(dialog).first().click({ force: true })
    await page.waitForTimeout(200)

    // Warning should appear with accessible buttons
    await expect(dialog.locator('button:has-text("Confirm")').first()).toBeVisible()
    await expect(dialog.locator('button:has-text("Cancel")')).toBeVisible()
  })
})
