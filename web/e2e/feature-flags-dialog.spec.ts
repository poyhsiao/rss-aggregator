import { test, expect } from '@playwright/test'

test.describe('FeatureFlagsDialog UI', () => {
  async function openDialog(page: any) {
    await page.goto('/settings')
    await page.waitForLoadState('networkidle')

    // Click RSS icon 10 times
    const rssIcon = page.locator('header svg[class*="h-6"]').first()
    for (let i = 0; i < 10; i++) {
      await rssIcon.click()
      await page.waitForTimeout(50)
    }
    await expect(page.locator('[role="dialog"]')).toBeVisible()
  }

  test('dialog uses compact style (lg size)', async ({ page }) => {
    await openDialog(page)
    const dialog = page.locator('[role="dialog"]')

    // Verify has lg size class (max-w-xl)
    await expect(dialog.locator('.max-w-xl')).toBeVisible()

    // Verify no emoji (uses lucide icons)
    const content = await dialog.textContent()
    expect(content).not.toMatch(/[⚙️👥⏰]/)
  })

  test('dialog has three toggles', async ({ page }) => {
    await openDialog(page)

    // Find all toggle switches
    const toggles = page.locator('[role="switch"]')
    await expect(toggles).toHaveCount(3)
  })

  test('disabling groups shows cascade warning', async ({ page }) => {
    await openDialog(page)

    // Turn OFF groups (first toggle)
    await page.locator('[role="switch"]').first().click()

    // Warning should appear
    await expect(page.getByText(/Disabling groups will also disable/i)).toBeVisible()

    // Confirm button should work
    await page.getByRole('button', { name: 'Confirm' }).first().click()

    // Dialog should close
    await expect(page.locator('[role="dialog"]')).not.toBeVisible()
  })

  test('third toggle is disabled when groups disabled', async ({ page }) => {
    await openDialog(page)

    // Turn OFF groups
    await page.locator('[role="switch"]').first().click()
    await page.getByRole('button', { name: 'Confirm' }).first().click()

    // Reopen dialog
    await openDialog(page)

    // Third toggle should be disabled
    const thirdToggle = page.locator('[role="switch"]').nth(2)
    await expect(thirdToggle).toBeDisabled()
  })
})