import { test, expect } from '@playwright/test'

test.describe('Group Filter Functionality', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/')
    await page.waitForLoadState('networkidle')
  })

  test('Feed page group filter chips should filter items by group', async ({ page }) => {
    const groupChips = page.locator('[class*="rounded-full"][class*="px-3"]')
    const count = await groupChips.count()

    if (count > 1) {
      await groupChips.nth(1).click()
      await page.waitForTimeout(500)

      const feedCards = page.locator('[class*="rounded-xl"]').filter({ has: page.locator('a') })
      const cardCount = await feedCards.count()

      for (let i = 0; i < Math.min(cardCount, 3); i++) {
        const cardText = await feedCards.nth(i).textContent()
        const secondChipText = await groupChips.nth(1).textContent()
        if (secondChipText && cardText) {
          expect(cardText).toContain(secondChipText.trim())
        }
      }
    }
  })

  test('History page group filter should filter batches by group', async ({ page }) => {
    await page.goto('/history')
    await page.waitForLoadState('networkidle')

    const groupChips = page.locator('[class*="rounded-full"][class*="px-3"]')
    const count = await groupChips.count()

    if (count > 1) {
      const initialCards = page.locator('[class*="rounded-xl"]').filter({ has: page.locator('[class*="font-medium"]') })
      const initialCount = await initialCards.count()

      await groupChips.nth(1).click()
      await page.waitForTimeout(500)

      const filteredCards = page.locator('[class*="rounded-xl"]').filter({ has: page.locator('[class*="font-medium"]') })
      const filteredCount = await filteredCards.count()

      expect(filteredCount).toBeLessThanOrEqual(initialCount)
    }
  })
})

test.describe('Icon Color Consistency', () => {
  test('Sources page action icons should have consistent colors', async ({ page }) => {
    await page.goto('/sources')
    await page.waitForLoadState('networkidle')

    const editButtons = page.locator('button[title*="edit"], button[title*="編輯"]')
    const editCount = await editButtons.count()
    if (editCount > 0) {
      const editIcon = editButtons.first().locator('svg')
      const classes = await editIcon.getAttribute('class')
      expect(classes).toContain('text-blue-500')
    }

    const deleteButtons = page.locator('button[title*="delete"], button[title*="刪除"]')
    const deleteCount = await deleteButtons.count()
    if (deleteCount > 0) {
      const deleteIcon = deleteButtons.first().locator('svg')
      const classes = await deleteIcon.getAttribute('class')
      expect(classes).toContain('text-red-500')
    }
  })

  test('Feed page action icons should have consistent colors', async ({ page }) => {
    await page.goto('/')
    await page.waitForLoadState('networkidle')

    const refreshBtn = page.locator('button:has-text("一鍵更新"), button:has-text("Refresh All")')
    if (await refreshBtn.isVisible()) {
      const icon = refreshBtn.locator('svg')
      const classes = await icon.getAttribute('class')
      expect(classes).toContain('text-green-500')
    }

    const previewBtn = page.locator('button:has-text("預覽摘要"), button:has-text("Preview Feed")')
    if (await previewBtn.isVisible()) {
      const icon = previewBtn.locator('svg')
      const classes = await icon.getAttribute('class')
      expect(classes).toContain('text-purple-500')
    }
  })

  test('History page action icons should have consistent colors', async ({ page }) => {
    await page.goto('/history')
    await page.waitForLoadState('networkidle')

    const cards = page.locator('[class*="rounded-xl"]').filter({ has: page.locator('[class*="font-medium"]') })
    const count = await cards.count()

    if (count > 0) {
      const editBtn = cards.first().locator('button[title*="edit"], button[title*="編輯"]')
      if (await editBtn.isVisible()) {
        const icon = editBtn.locator('svg')
        const classes = await icon.getAttribute('class')
        expect(classes).toContain('text-blue-500')
      }

      const previewBtn = cards.first().locator('button[title*="preview"], button[title*="預覽"]')
      if (await previewBtn.isVisible()) {
        const icon = previewBtn.locator('svg')
        const classes = await icon.getAttribute('class')
        expect(classes).toContain('text-purple-500')
      }

      const deleteBtn = cards.first().locator('button[title*="delete"], button[title*="刪除"]')
      if (await deleteBtn.isVisible()) {
        const icon = deleteBtn.locator('svg')
        const classes = await icon.getAttribute('class')
        expect(classes).toContain('text-red-500')
      }
    }
  })
})

test.describe('Inline Group Name Editing', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/sources')
    await page.waitForLoadState('networkidle')
    await page.getByRole('button', { name: /groups|群組/i }).click()
    await page.waitForTimeout(500)
  })

  test('Group name should be editable inline via pencil icon', async ({ page }) => {
    const groups = page.locator('[class*="rounded-xl"]').filter({ has: page.locator('[class*="font-medium"]') })
    const count = await groups.count()

    if (count > 0) {
      const editBtn = groups.first().locator('button[title*="edit"], button[title*="編輯"]')
      await editBtn.click()

      const input = groups.first().locator('input[type="text"]')
      await expect(input).toBeVisible({ timeout: 3000 })
    }
  })

  test('Inline group name edit should have save and cancel buttons', async ({ page }) => {
    const groups = page.locator('[class*="rounded-xl"]').filter({ has: page.locator('[class*="font-medium"]') })
    const count = await groups.count()

    if (count > 0) {
      const editBtn = groups.first().locator('button[title*="edit"], button[title*="編輯"]')
      await editBtn.click()

      const saveBtn = groups.first().locator('button[title*="save"], button[title*="儲存"]')
      const cancelBtn = groups.first().locator('button[title*="cancel"], button[title*="取消"]')

      await expect(saveBtn).toBeVisible({ timeout: 3000 })
      await expect(cancelBtn).toBeVisible({ timeout: 3000 })
    }
  })

  test('Cancel inline editing should restore original name', async ({ page }) => {
    const groups = page.locator('[class*="rounded-xl"]').filter({ has: page.locator('[class*="font-medium"]') })
    const count = await groups.count()

    if (count > 0) {
      const originalName = await groups.first().locator('[class*="font-medium"]').textContent()

      const editBtn = groups.first().locator('button[title*="edit"], button[title*="編輯"]')
      await editBtn.click()

      const cancelBtn = groups.first().locator('button[title*="cancel"], button[title*="取消"]')
      await cancelBtn.click()

      await page.waitForTimeout(300)

      const restoredName = await groups.first().locator('[class*="font-medium"]').textContent()
      expect(restoredName?.trim()).toBe(originalName?.trim())
    }
  })
})
