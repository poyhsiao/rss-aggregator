import { test, expect } from '@playwright/test'

test.describe('FeatureFlagsDialog UI', () => {
  // Ensure dialog is closed before each test to prevent state pollution
  test.beforeEach(async ({ page }) => {
    await page.goto('/sources')
    await page.waitForLoadState('networkidle')
    // Close any open dialogs (e.g., from previous test in same worker)
    const dialog = page.locator('[role="dialog"]')
    if (await dialog.isVisible()) {
      await page.keyboard.press('Escape')
      await dialog.waitFor({ state: 'hidden', timeout: 5000 }).catch(() => {
        // Force reload if dialog won't close
        page.goto('/sources')
      })
    }
  })

  async function openDialog(page: any) {
    await page.goto('/settings')
    await page.waitForLoadState('networkidle')

    // Click the h1 heading 10 times to trigger the easter egg
    const heading = page.locator('h1.text-2xl, h1.cursor-pointer')
    for (let i = 0; i < 10; i++) {
      await heading.click()
      await page.waitForTimeout(300) // 3000ms total window
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