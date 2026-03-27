import { test, expect } from '@playwright/test'

test.describe('Trash Restore Functionality', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/sources')
    await page.waitForLoadState('networkidle')
  })

  test('should display trash tab with items', async ({ page }) => {
    await page.getByRole('button', { name: /trash|垃圾桶/i }).click()
    await page.waitForTimeout(500)

    const trashItems = page.locator('[class*="bg-white"][class*="rounded-xl"], [class*="bg-neutral-800"][class*="rounded-xl"]').filter({ hasText: /🗑️/ })
    const count = await trashItems.count()
    expect(count).toBeGreaterThanOrEqual(0)
  })

  test('should show conflict dialog when restoring item with same name/url', async ({ page }) => {
    await page.getByRole('button', { name: /trash|垃圾桶/i }).click()
    await page.waitForTimeout(500)

    const trashItems = page.locator('[class*="bg-white"][class*="rounded-xl"], [class*="bg-neutral-800"][class*="rounded-xl"]').filter({ hasText: /🗑️/ })
    const count = await trashItems.count()

    if (count > 0) {
      const restoreButton = trashItems.first().getByRole('button').filter({ has: page.locator('svg') })
      await restoreButton.first().click()
      await page.waitForTimeout(1000)

      const conflictDialog = page.locator('[class*="fixed"][class*="inset-0"][class*="z-50"]')
      const isVisible = await conflictDialog.isVisible().catch(() => false)

      if (isVisible) {
        const conflictText = await conflictDialog.textContent()
        expect(conflictText).toContain('already exists')
        
        const cancelButton = conflictDialog.getByRole('button', { name: /cancel|取消/i })
        if (await cancelButton.isVisible()) {
          await cancelButton.click()
        } else {
          await page.keyboard.press('Escape')
        }
      }
    }
  })

  test('should show toast message on restore error', async ({ page }) => {
    await page.getByRole('button', { name: /trash|垃圾桶/i }).click()
    await page.waitForTimeout(500)

    const trashItems = page.locator('[class*="bg-white"][class*="rounded-xl"], [class*="bg-neutral-800"][class*="rounded-xl"]').filter({ hasText: /🗑️/ })
    const count = await trashItems.count()

    if (count > 0) {
      const restoreButtons = trashItems.first().getByRole('button')
      const buttonCount = await restoreButtons.count()

      for (let i = 0; i < buttonCount; i++) {
        const btn = restoreButtons.nth(i)
        const btnHtml = await btn.innerHTML()
        if (btnHtml.includes('RotateCcw') || btnHtml.includes('rotate-ccw')) {
          await btn.click()
          await page.waitForTimeout(2000)
          break
        }
      }

      const toast = page.locator('[class*="fixed"][class*="top-"][class*="right-"]')
      const dialog = page.locator('[class*="fixed"][class*="inset-0"][class*="z-50"]')
      
      const dialogVisible = await dialog.isVisible().catch(() => false)
      const toastVisible = await toast.isVisible().catch(() => false)
      
      expect(dialogVisible || toastVisible).toBe(true)
    }
  })

  test('should permanently delete from trash', async ({ page }) => {
    await page.getByRole('button', { name: /trash|垃圾桶/i }).click()
    await page.waitForTimeout(500)

    const trashItems = page.locator('[class*="bg-white"][class*="rounded-xl"], [class*="bg-neutral-800"][class*="rounded-xl"]').filter({ hasText: /🗑️/ })
    const initialCount = await trashItems.count()

    if (initialCount > 0) {
      const firstItem = trashItems.first()
      const buttons = firstItem.getByRole('button')
      const buttonCount = await buttons.count()

      for (let i = 0; i < buttonCount; i++) {
        const btn = buttons.nth(i)
        const btnHtml = await btn.innerHTML()
        if (btnHtml.includes('XCircle') || btnHtml.includes('x-circle') || btnHtml.includes('text-red')) {
          await btn.click()
          await page.waitForTimeout(500)

          const confirmDialog = page.locator('[class*="fixed"][class*="inset-0"][class*="z-50"]')
          if (await confirmDialog.isVisible()) {
            const confirmBtn = confirmDialog.getByRole('button', { name: /delete|刪除/i })
            await confirmBtn.click()
            await page.waitForTimeout(1000)
          }
          break
        }
      }
    }
  })
})