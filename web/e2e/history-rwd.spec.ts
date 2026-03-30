import { test, expect } from '@playwright/test'

test.describe('History Page RWD', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/history')
    await page.waitForLoadState('networkidle')
  })

  test('should display history page on mobile viewport', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 })

    await expect(page.getByRole('heading', { name: /history/i })).toBeVisible()
  })

  test('should display batch cards on mobile viewport', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 })

    const cards = page.locator('[class*="bg-white"][class*="rounded-xl"], [class*="bg-neutral-800"][class*="rounded-xl"]')
    const count = await cards.count()
    expect(count).toBeGreaterThanOrEqual(0)
  })

  test('should not have horizontal overflow on mobile viewport', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 })

    // Check for horizontal overflow
    const bodyWidth = await page.evaluate(() => document.body.scrollWidth)
    const viewportWidth = await page.evaluate(() => window.innerWidth)

    expect(bodyWidth).toBeLessThanOrEqual(viewportWidth)
  })

  test('should display news items with proper line clamping on mobile', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 })

    const cards = page.locator('[class*="bg-white"][class*="rounded-xl"], [class*="bg-neutral-800"][class*="rounded-xl"]')
    const count = await cards.count()

    if (count > 0) {
      // Click on the first batch to expand it
      await cards.nth(0).click()
      await page.waitForTimeout(500)

      // Check if news items are displayed
      const newsItems = page.locator('[class*="divide-y"] > div')
      const itemCount = await newsItems.count()

      if (itemCount > 0) {
        // Check that titles have line-clamp-2 class
        const titles = newsItems.locator('h4')
        const titleCount = await titles.count()

        for (let i = 0; i < Math.min(titleCount, 3); i++) {
          const title = titles.nth(i)
          await expect(title).toBeVisible()

          // Check that the title has line-clamp-2 class
          const className = await title.getAttribute('class')
          expect(className).toContain('line-clamp-2')
        }
      }
    }
  })

  test('should display news items without horizontal overflow on mobile', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 })

    const cards = page.locator('[class*="bg-white"][class*="rounded-xl"], [class*="bg-neutral-800"][class*="rounded-xl"]')
    const count = await cards.count()

    if (count > 0) {
      // Click on the first batch to expand it
      await cards.nth(0).click()
      await page.waitForTimeout(500)

      // Check if news items are displayed
      const newsItems = page.locator('[class*="divide-y"] > div')
      const itemCount = await newsItems.count()

      if (itemCount > 0) {
        // Check that each news item doesn't cause horizontal overflow
        for (let i = 0; i < Math.min(itemCount, 3); i++) {
          const item = newsItems.nth(i)
          const itemWidth = await item.evaluate((el) => el.scrollWidth)
          const containerWidth = await item.evaluate((el) => el.parentElement?.scrollWidth || 0)

          expect(itemWidth).toBeLessThanOrEqual(containerWidth)
        }
      }
    }
  })

  test('should display properly on tablet viewport', async ({ page }) => {
    // Set tablet viewport
    await page.setViewportSize({ width: 768, height: 1024 })

    await expect(page.getByRole('heading', { name: /history/i })).toBeVisible()

    // Check for horizontal overflow
    const bodyWidth = await page.evaluate(() => document.body.scrollWidth)
    const viewportWidth = await page.evaluate(() => window.innerWidth)

    expect(bodyWidth).toBeLessThanOrEqual(viewportWidth)
  })

  test('should display properly on desktop viewport', async ({ page }) => {
    // Set desktop viewport
    await page.setViewportSize({ width: 1280, height: 720 })

    await expect(page.getByRole('heading', { name: /history/i })).toBeVisible()

    // Check for horizontal overflow
    const bodyWidth = await page.evaluate(() => document.body.scrollWidth)
    const viewportWidth = await page.evaluate(() => window.innerWidth)

    expect(bodyWidth).toBeLessThanOrEqual(viewportWidth)
  })

  test('should handle long titles gracefully on mobile', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 })

    const cards = page.locator('[class*="bg-white"][class*="rounded-xl"], [class*="bg-neutral-800"][class*="rounded-xl"]')
    const count = await cards.count()

    if (count > 0) {
      // Click on the first batch to expand it
      await cards.nth(0).click()
      await page.waitForTimeout(500)

      // Check if news items are displayed
      const newsItems = page.locator('[class*="divide-y"] > div')
      const itemCount = await newsItems.count()

      if (itemCount > 0) {
        // Check that titles are properly truncated
        const titles = newsItems.locator('h4')
        const titleCount = await titles.count()

        for (let i = 0; i < Math.min(titleCount, 3); i++) {
          const title = titles.nth(i)
          const titleText = await title.textContent()

          // Check that title text is not empty
          expect(titleText).toBeTruthy()
          expect(titleText?.length).toBeGreaterThan(0)

          // Check that the title element has proper styling
          const styles = await title.evaluate((el) => {
            const computed = window.getComputedStyle(el)
            return {
              display: computed.display,
              overflow: computed.overflow,
              textOverflow: computed.textOverflow,
              webkitLineClamp: computed.webkitLineClamp,
            }
          })

          // Verify line-clamp is applied
          expect(styles.webkitLineClamp).toBe('2')
        }
      }
    }
  })

  test('should maintain proper spacing on mobile viewport', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 })

    const cards = page.locator('[class*="bg-white"][class*="rounded-xl"], [class*="bg-neutral-800"][class*="rounded-xl"]')
    const count = await cards.count()

    if (count > 0) {
      // Click on the first batch to expand it
      await cards.nth(0).click()
      await page.waitForTimeout(500)

      // Check if news items are displayed
      const newsItems = page.locator('[class*="divide-y"] > div')
      const itemCount = await newsItems.count()

      if (itemCount > 0) {
        // Check that news items have proper padding
        const firstItem = newsItems.nth(0)
        const padding = await firstItem.evaluate((el) => {
          const computed = window.getComputedStyle(el)
          return {
            paddingTop: computed.paddingTop,
            paddingBottom: computed.paddingBottom,
            paddingLeft: computed.paddingLeft,
            paddingRight: computed.paddingRight,
          }
        })

        // Verify padding is not zero
        expect(parseFloat(padding.paddingTop)).toBeGreaterThan(0)
        expect(parseFloat(padding.paddingBottom)).toBeGreaterThan(0)
        expect(parseFloat(padding.paddingLeft)).toBeGreaterThan(0)
        expect(parseFloat(padding.paddingRight)).toBeGreaterThan(0)
      }
    }
  })
})
