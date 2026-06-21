import { test, expect } from '@playwright/test'

test.describe('Feed URL Dialog Feature', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/feed')
    await page.waitForLoadState('networkidle')
  })

  test('feature toggle workflow - happy path', async ({ page }) => {
    // Open preview dialog by clicking the preview button on a feed item
    const feedItems = page.locator('[class*="bg-white"][class*="rounded-xl"]')
    const count = await feedItems.count()

    // Skip test if no feed items are available
    if (count === 0) {
      test.skip()
    }

    // Find and click the preview button (Eye icon)
    const firstItem = feedItems.first()
    const buttons = firstItem.getByRole('button')
    const buttonCount = await buttons.count()

    let previewClicked = false
    for (let i = 0; i < buttonCount; i++) {
      const btn = buttons.nth(i)
      const btnTitle = await btn.getAttribute('title')

      if (btnTitle && (btnTitle.toLowerCase().includes('preview') || btnTitle.includes('預覽'))) {
        await btn.click()
        previewClicked = true
        break
      }
    }
    expect(previewClicked).toBe(true)

    // Wait for dialog to appear
    await page.waitForTimeout(500)
    const dialog = page.locator('[class*="fixed"][class*="inset-0"][class*="z-50"]')
    await expect(dialog).toBeVisible({ timeout: 10000 })

    // URL section should be hidden by default (when feedUrlStore.enabled is false initially)
    // First, we need to enable the feature via the info button
    const infoBtn = dialog.locator('[data-testid="info-btn"]')
    const infoBtnCount = await infoBtn.count()

    if (infoBtnCount > 0) {
      // Info button is visible only when feedUrlStore.enabled is true
      // If visible, feature is already enabled

      // Click info icon to open feature dialog
      await infoBtn.click()
      await expect(dialog.locator('[data-testid="feature-dialog"]')).toBeVisible()

      // Toggle the feature OFF first to test the full workflow
      const featureToggle = dialog.locator('[data-testid="feature-toggle"]')
      if (await featureToggle.isVisible()) {
        await featureToggle.click()
      }

      // Close feature dialog
      const closeBtn = dialog.locator('[data-testid="close-btn"]')
      if (await closeBtn.isVisible()) {
        await closeBtn.click()
      }

      // Wait for dialog to close
      await page.waitForTimeout(300)

      // Now enable the feature
      await infoBtn.click()
      await expect(dialog.locator('[data-testid="feature-dialog"]')).toBeVisible()

      // Enable feature
      await dialog.locator('[data-testid="feature-toggle"]').click()

      // Close feature dialog
      await dialog.locator('[data-testid="close-btn"]').click()

      // Wait for dialog to close
      await page.waitForTimeout(300)
    }

    // Re-open dialog if it closed
    const isDialogVisible = await dialog.isVisible().catch(() => false)
    if (!isDialogVisible) {
      // Re-click preview button
      const newFirstItem = page.locator('[class*="bg-white"][class*="rounded-xl"]').first()
      const newButtons = newFirstItem.getByRole('button')
      for (let i = 0; i < await newButtons.count(); i++) {
        const btn = newButtons.nth(i)
        const btnTitle = await btn.getAttribute('title')
        if (btnTitle && (btnTitle.toLowerCase().includes('preview') || btnTitle.includes('預覽'))) {
          await btn.click()
          break
        }
      }
      await page.waitForTimeout(500)
    }

    // Now URL section should be visible (feature is enabled)
    const urlSection = dialog.locator('[data-testid="url-section"]')
    await expect(urlSection).toBeVisible()

    // URL section is visible but collapsed - expand it
    const expandBtn = dialog.locator('[data-testid="expand-btn"]')
    if (await expandBtn.isVisible()) {
      await expandBtn.click()
    }

    // URLs should be visible after expanding
    await expect(dialog.locator('[data-testid="rss-url"]')).toBeVisible()
    await expect(dialog.locator('[data-testid="json-url"]')).toBeVisible()
    await expect(dialog.locator('[data-testid="markdown-url"]')).toBeVisible()

    // Copy RSS URL
    await dialog.locator('[data-testid="copy-rss-btn"]').click()

    // Copied toast should be visible
    await expect(dialog.locator('.copied-toast')).toBeVisible()
  })

  test('error handling - API failure shows hidden URLs', async ({ page }) => {
    // Simulate network error by intercepting
    await page.route('**/api/v1/settings/feed-url', route => {
      route.abort('failed')
    })

    // Open preview dialog
    const feedItems = page.locator('[class*="bg-white"][class*="rounded-xl"]')
    const count = await feedItems.count()

    if (count > 0) {
      const firstItem = feedItems.first()
      const buttons = firstItem.getByRole('button')
      const buttonCount = await buttons.count()

      for (let i = 0; i < buttonCount; i++) {
        const btn = buttons.nth(i)
        const btnTitle = await btn.getAttribute('title')
        if (btnTitle && (btnTitle.toLowerCase().includes('preview') || btnTitle.includes('預覽'))) {
          await btn.click()
          break
        }
      }

      await page.waitForTimeout(500)
      const dialog = page.locator('[class*="fixed"][class*="inset-0"][class*="z-50"]')

      // URL section should remain hidden due to API failure
      await expect(dialog.locator('[data-testid="url-section"]')).not.toBeVisible()
    }
  })

  test('disable feature hides URL section', async ({ page }) => {
    // First, enable the feature
    const feedItems = page.locator('[class*="bg-white"][class*="rounded-xl"]')
    const count = await feedItems.count()

    // Skip test if no feed items are available
    if (count === 0) {
      test.skip()
    }

    // Find and click the preview button
    const firstItem = feedItems.first()
    const buttons = firstItem.getByRole('button')
    const buttonCount = await buttons.count()

    for (let i = 0; i < buttonCount; i++) {
      const btn = buttons.nth(i)
      const btnTitle = await btn.getAttribute('title')
      if (btnTitle && (btnTitle.toLowerCase().includes('preview') || btnTitle.includes('預覽'))) {
        await btn.click()
        break
      }
    }

    await page.waitForTimeout(500)
    const dialog = page.locator('[class*="fixed"][class*="inset-0"][class*="z-50"]')
    await expect(dialog).toBeVisible({ timeout: 10000 })

    // Check if info button exists and click it to enable feature
    const infoBtn = dialog.locator('[data-testid="info-btn"]')
    if (await infoBtn.count() > 0) {
      // Open feature dialog
      await infoBtn.click()
      await expect(dialog.locator('[data-testid="feature-dialog"]')).toBeVisible()

      // Ensure feature is enabled
      const featureToggle = dialog.locator('[data-testid="feature-toggle"]')
      const isChecked = await featureToggle.getAttribute('aria-checked')
      if (isChecked === 'false') {
        await featureToggle.click()
      }

      // Close dialog
      await dialog.locator('[data-testid="close-btn"]').click()
      await page.waitForTimeout(300)

      // Expand URL section
      const expandBtn = dialog.locator('[data-testid="expand-btn"]')
      if (await expandBtn.isVisible()) {
        await expandBtn.click()
      }

      // URLs should be visible
      await expect(dialog.locator('[data-testid="rss-url"]')).toBeVisible()

      // Now disable the feature via feature dialog
      await infoBtn.click()
      await expect(dialog.locator('[data-testid="feature-dialog"]')).toBeVisible()

      // Disable feature
      const toggle = dialog.locator('[data-testid="feature-toggle"]')
      const currentState = await toggle.getAttribute('aria-checked')
      if (currentState === 'true') {
        await toggle.click()
      }

      // Close dialog
      await dialog.locator('[data-testid="close-btn"]').click()
      await page.waitForTimeout(300)

      // URL section should be hidden
      await expect(dialog.locator('[data-testid="url-section"]')).not.toBeVisible()
    }
  })
})
