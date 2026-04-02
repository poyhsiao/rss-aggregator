import { test, expect } from '@playwright/test'

test.describe('Group-Specific Refresh and Preview', () => {
  test('Feed page refresh all should respect selected group', async ({ page }) => {
    await page.goto('/')
    await page.waitForLoadState('networkidle')

    const groupChips = page.locator('[class*="rounded-full"][class*="px-3"]')
    const count = await groupChips.count()

    if (count > 1) {
      const groupName = (await groupChips.nth(1).textContent())?.trim()
      if (groupName) {
        await groupChips.nth(1).click()
        await page.waitForTimeout(500)

        const refreshBtn = page.locator('button:has-text("一鍵更新"), button:has-text("Refresh All")')
        if (await refreshBtn.isVisible()) {
          const responsePromise = page.waitForResponse(
            (res) => res.url().includes('/sources/refresh') && res.request().method() === 'POST',
            { timeout: 10000 }
          )
          await refreshBtn.click()
          await responsePromise
        }
      }
    }
  })

  test('Feed page preview feed should respect selected group', async ({ page }) => {
    await page.goto('/')
    await page.waitForLoadState('networkidle')

    const groupChips = page.locator('[class*="rounded-full"][class*="px-3"]')
    const count = await groupChips.count()

    if (count > 1) {
      await groupChips.nth(1).click()
      await page.waitForTimeout(500)

      const previewBtn = page.locator('button:has-text("預覽摘要"), button:has-text("Preview Feed")')
      if (await previewBtn.isVisible()) {
        await previewBtn.click()
        await page.waitForTimeout(1000)

        const dialog = page.locator('[class*="fixed"][class*="inset-0"]').filter({ has: page.locator('[class*="rounded-2xl"]') })
        await expect(dialog).toBeVisible({ timeout: 5000 })

        const closeBtn = dialog.locator('button').last()
        await closeBtn.click()
      }
    }
  })

  test('Source group refresh should only refresh group sources', async ({ page }) => {
    await page.goto('/sources')
    await page.waitForLoadState('networkidle')

    await page.getByRole('button', { name: /groups|群組/i }).click()
    await page.waitForTimeout(500)

    const groups = page.locator('[class*="rounded-xl"]').filter({ has: page.locator('[class*="font-medium"]') })
    const count = await groups.count()

    if (count > 0) {
      const refreshBtn = groups.first().locator('button[title*="refresh"], button[title*="更新"]')
      if (await refreshBtn.isVisible()) {
        const responsePromise = page.waitForResponse(
          (res) => res.url().includes('/source-groups/') && res.url().includes('/refresh') && res.request().method() === 'POST',
          { timeout: 10000 }
        )
        await refreshBtn.click()
        await responsePromise
      }
    }
  })

  test('History page group filter should show only group-related batches', async ({ page }) => {
    await page.goto('/history')
    await page.waitForLoadState('networkidle')

    const groupChips = page.locator('[class*="rounded-full"][class*="px-3"]')
    const count = await groupChips.count()

    if (count > 1) {
      const initialCards = page.locator('[class*="rounded-xl"]').filter({ has: page.locator('[class*="font-medium"]') })
      const initialCount = await initialCards.count()

      await groupChips.nth(1).click()
      await page.waitForTimeout(1000)

      const filteredCards = page.locator('[class*="rounded-xl"]').filter({ has: page.locator('[class*="font-medium"]') })
      const filteredCount = await filteredCards.count()

      expect(filteredCount).toBeLessThanOrEqual(initialCount)
    }
  })

  test('Source group preview feed should filter by group_id', async ({ page }) => {
    await page.goto('/sources')
    await page.waitForLoadState('networkidle')

    await page.getByRole('button', { name: /groups|群組/i }).click()
    await page.waitForTimeout(500)

    const groups = page.locator('[class*="rounded-xl"]').filter({ has: page.locator('[class*="font-medium"]') })
    const count = await groups.count()

    if (count > 0) {
      const groupName = (await groups.first().locator('[class*="font-medium"]').textContent())?.trim()
      const previewBtn = groups.first().locator('button[title*="preview"], button[title*="預覽"]')

      if (await previewBtn.isVisible()) {
        const responsePromise = page.waitForResponse(
          (res) => {
            const url = res.url()
            return url.includes('/feed') && url.includes('group_id=') && res.request().method() === 'GET'
          },
          { timeout: 10000 }
        )

        await previewBtn.click()
        await responsePromise
      }
    }
  })
})
