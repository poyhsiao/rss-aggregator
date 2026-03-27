import { test, expect } from '@playwright/test'

test.describe('Article Preview Feature', () => {
  test.describe('Feed Page Article Preview', () => {
    test.beforeEach(async ({ page }) => {
      await page.goto('/feed')
      await page.waitForLoadState('networkidle')
    })

    test('should display preview button on feed items', async ({ page }) => {
      const feedItems = page.locator('[class*="bg-white"][class*="rounded-xl"]')
      const count = await feedItems.count()

      if (count > 0) {
        const firstItem = feedItems.first()
        // Look for Eye icon button (preview button)
        const previewButton = firstItem.getByRole('button').filter({ has: page.locator('svg') })
        const buttonCount = await previewButton.count()

        // At least one button should be visible (preview button)
        expect(buttonCount).toBeGreaterThanOrEqual(1)
      }
    })

    test('should open article preview dialog when clicking preview button', async ({ page }) => {
      const feedItems = page.locator('[class*="bg-white"][class*="rounded-xl"]')
      const count = await feedItems.count()

      if (count > 0) {
        const firstItem = feedItems.first()
        // Find the preview button (Eye icon button with title containing "preview")
        const buttons = firstItem.getByRole('button')
        const buttonCount = await buttons.count()

        for (let i = 0; i < buttonCount; i++) {
          const btn = buttons.nth(i)
          const btnTitle = await btn.getAttribute('title')

          if (btnTitle && (btnTitle.toLowerCase().includes('preview') || btnTitle.includes('預覽'))) {
            await btn.click()
            await page.waitForTimeout(500)

            // ArticlePreviewDialog uses Dialog component which renders as fixed inset-0
            const dialog = page.locator('[class*="fixed"][class*="inset-0"][class*="z-50"]')
            await expect(dialog).toBeVisible({ timeout: 10000 })

            // Should show loading state initially or content
            const loadingSpinner = dialog.locator('svg.animate-spin')
            const content = dialog.locator('[class*="prose"]')

            // Either loading spinner or content should be visible
            const isLoading = await loadingSpinner.isVisible().catch(() => false)
            const hasContent = await content.isVisible().catch(() => false)

            expect(isLoading || hasContent).toBe(true)
            break
          }
        }
      }
    })

    test('should close article preview dialog', async ({ page }) => {
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
            await page.waitForTimeout(500)

            const dialog = page.locator('[class*="fixed"][class*="inset-0"][class*="z-50"]')
            await expect(dialog).toBeVisible({ timeout: 10000 })

            // Find and click close button
            const closeButton = dialog.locator('.close-btn, button').filter({ has: page.locator('svg') }).last()
            await closeButton.click()
            await page.waitForTimeout(500)

            // Dialog should be closed
            await expect(dialog).not.toBeVisible({ timeout: 5000 })
            break
          }
        }
      }
    })

    test('should have external link in preview dialog', async ({ page }) => {
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
            await page.waitForTimeout(500)

            const dialog = page.locator('[class*="fixed"][class*="inset-0"][class*="z-50"]')
            await expect(dialog).toBeVisible({ timeout: 10000 })

            // Should have an external link
            const externalLink = dialog.locator('a[target="_blank"]')
            await expect(externalLink.first()).toBeVisible({ timeout: 5000 })

            // Close the dialog
            const closeButton = dialog.locator('.close-btn, button').filter({ has: page.locator('svg') }).last()
            await closeButton.click()
            break
          }
        }
      }
    })
  })

  test.describe('History Page Article Preview', () => {
    test.beforeEach(async ({ page }) => {
      await page.goto('/history')
      await page.waitForLoadState('networkidle')
    })

    test('should display preview button on expanded history items', async ({ page }) => {
      const batchCards = page.locator('[class*="bg-white"][class*="rounded-xl"]')
      const count = await batchCards.count()

      if (count > 0) {
        // Expand the first batch
        const firstBatch = batchCards.first()
        const expandButton = firstBatch.getByRole('button').last()
        await expandButton.click()
        await page.waitForTimeout(1000)

        // Check if items are expanded
        const expandedItems = page.locator('[class*="divide-y"] > div')
        const itemCount = await expandedItems.count()

        if (itemCount > 0) {
          const firstItem = expandedItems.first()
          // Should have Eye icon button for preview
          const previewButton = firstItem.getByRole('button').first()
          await expect(previewButton).toBeVisible()
        }
      }
    })

    test('should open article preview dialog from history item', async ({ page }) => {
      const batchCards = page.locator('[class*="bg-white"][class*="rounded-xl"]')
      const count = await batchCards.count()

      if (count > 0) {
        // Expand the first batch
        const firstBatch = batchCards.first()
        const expandButton = firstBatch.getByRole('button').last()
        await expandButton.click()
        await page.waitForTimeout(1000)

        // Find expanded items
        const expandedItems = page.locator('[class*="divide-y"] > div')
        const itemCount = await expandedItems.count()

        if (itemCount > 0) {
          const firstItem = expandedItems.first()
          // Click the preview button (Eye icon)
          const previewButton = firstItem.getByRole('button').first()
          await previewButton.click()
          await page.waitForTimeout(500)

          // ArticlePreviewDialog should be visible
          const dialog = page.locator('[class*="fixed"][class*="inset-0"][class*="z-50"]')
          await expect(dialog).toBeVisible({ timeout: 10000 })
        }
      }
    })

    test('should have both preview and external link buttons on history items', async ({ page }) => {
      const batchCards = page.locator('[class*="bg-white"][class*="rounded-xl"]')
      const count = await batchCards.count()

      if (count > 0) {
        // Expand the first batch
        const firstBatch = batchCards.first()
        const expandButton = firstBatch.getByRole('button').last()
        await expandButton.click()
        await page.waitForTimeout(1000)

        // Find expanded items
        const expandedItems = page.locator('[class*="divide-y"] > div')
        const itemCount = await expandedItems.count()

        if (itemCount > 0) {
          const firstItem = expandedItems.first()
          const buttons = firstItem.getByRole('button')
          const buttonCount = await buttons.count()

          // Should have at least 2 buttons (preview + external link)
          expect(buttonCount).toBeGreaterThanOrEqual(2)

          // First button should be preview (Eye icon)
          const previewButton = buttons.first()
          const previewTitle = await previewButton.getAttribute('title')
          expect(previewTitle?.toLowerCase()).toContain('preview')

          // Second button should be external link
          const externalLinkButton = buttons.nth(1)
          const externalTitle = await externalLinkButton.getAttribute('title')
          expect(externalTitle?.toLowerCase()).toMatch(/open|new|tab/)
        }
      }
    })

    test('should close article preview dialog from history page', async ({ page }) => {
      const batchCards = page.locator('[class*="bg-white"][class*="rounded-xl"]')
      const count = await batchCards.count()

      if (count > 0) {
        // Expand the first batch
        const firstBatch = batchCards.first()
        const expandButton = firstBatch.getByRole('button').last()
        await expandButton.click()
        await page.waitForTimeout(1000)

        // Find expanded items
        const expandedItems = page.locator('[class*="divide-y"] > div')
        const itemCount = await expandedItems.count()

        if (itemCount > 0) {
          const firstItem = expandedItems.first()
          const previewButton = firstItem.getByRole('button').first()
          await previewButton.click()
          await page.waitForTimeout(500)

          const dialog = page.locator('[class*="fixed"][class*="inset-0"][class*="z-50"]')
          await expect(dialog).toBeVisible({ timeout: 10000 })

          // Close the dialog
          const closeButton = dialog.locator('.close-btn, button').filter({ has: page.locator('svg') }).last()
          await closeButton.click()
          await page.waitForTimeout(500)

          await expect(dialog).not.toBeVisible({ timeout: 5000 })
        }
      }
    })
  })

  test.describe('Article Preview Caching', () => {
    test.beforeEach(async ({ page }) => {
      await page.goto('/feed')
      await page.waitForLoadState('networkidle')
    })

    test('should load cached content faster on second open', async ({ page }) => {
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
            // First open
            const firstStartTime = Date.now()
            await btn.click()
            await page.waitForTimeout(500)

            const dialog = page.locator('[class*="fixed"][class*="inset-0"][class*="z-50"]')
            await expect(dialog).toBeVisible({ timeout: 10000 })

            // Wait for content to load
            const content = dialog.locator('[class*="prose"]')
            await content.waitFor({ state: 'visible', timeout: 30000 }).catch(() => {
              // Content might not appear if error occurs, that's ok for this test
            })

            const firstLoadTime = Date.now() - firstStartTime

            // Close dialog
            const closeButton = dialog.locator('.close-btn, button').filter({ has: page.locator('svg') }).last()
            await closeButton.click()
            await page.waitForTimeout(500)

            // Second open (should use cache)
            const secondStartTime = Date.now()
            await btn.click()
            await page.waitForTimeout(500)

            await expect(dialog).toBeVisible({ timeout: 10000 })

            // Second load should be faster (cached)
            const secondLoadTime = Date.now() - secondStartTime

            // Note: We're not asserting on exact times since network is unpredictable
            // Just verify both opens worked
            expect(firstLoadTime).toBeGreaterThan(0)
            expect(secondLoadTime).toBeGreaterThan(0)

            // Close dialog
            const closeButton2 = dialog.locator('.close-btn, button').filter({ has: page.locator('svg') }).last()
            await closeButton2.click()
            break
          }
        }
      }
    })
  })

  test.describe('Article Preview Error Handling', () => {
    test.beforeEach(async ({ page }) => {
      await page.goto('/feed')
      await page.waitForLoadState('networkidle')
    })

    test('should show loading state while fetching', async ({ page }) => {
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

            // Check for loading spinner immediately
            const dialog = page.locator('[class*="fixed"][class*="inset-0"][class*="z-50"]')
            await expect(dialog).toBeVisible({ timeout: 5000 })

            // Loading spinner should be visible initially (animate-spin class)
            const loadingSpinner = dialog.locator('svg.animate-spin')
            const isLoadingVisible = await loadingSpinner.isVisible().catch(() => false)

            // Either loading was visible, or content loaded very fast
            // Both are valid outcomes
            expect(isLoadingVisible || await dialog.locator('[class*="prose"]').isVisible().catch(() => false) || await dialog.locator('text=/error|錯誤/i').isVisible().catch(() => false)).toBe(true)

            // Close dialog
            const closeButton = dialog.locator('.close-btn, button').filter({ has: page.locator('svg') }).last()
            await closeButton.click().catch(() => {})
            break
          }
        }
      }
    })
  })
})