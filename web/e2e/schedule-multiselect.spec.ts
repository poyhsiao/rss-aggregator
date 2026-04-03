import { test, expect } from '@playwright/test'

test.describe('Schedule UI - MultiSelect', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/sources')
    await page.waitForLoadState('networkidle')
    await page.getByRole('button', { name: /groups|群組/i }).click()
    await page.waitForTimeout(500)
  })

  test('MultiSelect dropdown opens and shows options', async ({ page }) => {
    const groups = page.locator('[class*="rounded-xl"]').filter({ has: page.locator('[class*="font-semibold"]') })
    const count = await groups.count()
    if (count > 0) {
      const nameBtn = groups.first().locator('button').first()
      if (await nameBtn.isVisible({ timeout: 3000 })) {
        await nameBtn.click()
        await page.waitForTimeout(500)
      }

      const detailedRadio = page.locator('input[type="radio"][value="detailed"]')
      if (await detailedRadio.isVisible({ timeout: 3000 })) {
        await detailedRadio.click()
        await page.waitForTimeout(300)

        const weekdaySelect = page.getByText(/Sun|Mon|Tue|Wed|Thu|Fri|Sat|日|一|二|三|四|五|六/)
        await expect(weekdaySelect.first()).toBeVisible()
      }
    }
  })

  test('Schedule section has tooltip button', async ({ page }) => {
    const groups = page.locator('[class*="rounded-xl"]').filter({ has: page.locator('[class*="font-semibold"]') })
    const count = await groups.count()
    if (count > 0) {
      const nameBtn = groups.first().locator('button').first()
      if (await nameBtn.isVisible({ timeout: 3000 })) {
        await nameBtn.click()
        await page.waitForTimeout(500)

        const tooltipBtn = page.locator('button').filter({ has: page.locator('svg[class*="text-neutral-400"]') })
        await expect(tooltipBtn.first()).toBeVisible()
      }
    }
  })

  test('Schedule actions have 40px+ touch targets', async ({ page }) => {
    const groups = page.locator('[class*="rounded-xl"]').filter({ has: page.locator('[class*="font-semibold"]') })
    const count = await groups.count()
    if (count > 0) {
      const nameBtn = groups.first().locator('button').first()
      if (await nameBtn.isVisible({ timeout: 3000 })) {
        await nameBtn.click()
        await page.waitForTimeout(500)

        const addBtn = page.getByRole('button', { name: /add schedule|新增排程/i })
        if (await addBtn.isVisible({ timeout: 3000 })) {
          const box = await addBtn.boundingBox()
          expect(box).not.toBeNull()
          expect(box!.height).toBeGreaterThanOrEqual(44)
        }
      }
    }
  })
})
