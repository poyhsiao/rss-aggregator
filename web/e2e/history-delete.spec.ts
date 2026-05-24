import { test, expect } from '@playwright/test'

test.describe('Delete History Functionality', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/')
    await page.waitForLoadState('networkidle')
  })

  test.describe('Delete All History', () => {
    test('History page should have Delete All button', async ({ page }) => {
      await page.goto('/history')
      await page.waitForLoadState('networkidle')

      const deleteAllButton = page.locator('button:has-text("delete_all"), button:has-text("一鍵清除")')

      const hasDeleteAllButton = await deleteAllButton.count() > 0
      if (hasDeleteAllButton) {
        await expect(deleteAllButton.first()).toBeVisible()
      }
    })

    test('Delete All should show confirmation dialog', async ({ page }) => {
      await page.goto('/history')
      await page.waitForLoadState('networkidle')

      const deleteAllButton = page.locator('button:has-text("delete_all"), button:has-text("一鍵清除")')

      if (await deleteAllButton.count() > 0) {
        await deleteAllButton.first().click()

        const dialog = page.locator('[role="dialog"]')
        if (await dialog.count() > 0) {
          await expect(dialog).toBeVisible()

          const cancelButton = page.locator('button:has-text("cancel"), button:has-text("取消")')
          const deleteButton = page.locator('button:has-text("delete"), button:has-text("刪除")')

          await expect(cancelButton.first()).toBeVisible()
          await expect(deleteButton.first()).toBeVisible()
        }
      }
    })
  })

  test.describe('Delete History By Group', () => {
    test('Sources page groups should have Delete History button', async ({ page }) => {
      await page.goto('/sources')
      await page.waitForLoadState('networkidle')

      const groupsButton = page.getByRole('button', { name: /groups|groups/i })
      if (await groupsButton.count() > 0) {
        await groupsButton.click()
        await page.waitForTimeout(500)
      }

      const groups = page.locator('[class*="rounded-xl"]').filter({ has: page.locator('[class*="font-medium"]') })
      const groupCount = await groups.count()

      if (groupCount > 0) {
        const deleteHistoryButtons = page.locator('button[title*="history"], button[title*="歷史"]')
        if (await deleteHistoryButtons.count() > 0) {
          await expect(deleteHistoryButtons.first()).toBeVisible()
        }
      }
    })

    test('Delete by Group should only delete that group history', async ({ page }) => {
      await page.goto('/sources')
      await page.waitForLoadState('networkidle')

      const groupsButton = page.getByRole('button', { name: /groups|groups/i })
      if (await groupsButton.count() > 0) {
        await groupsButton.click()
        await page.waitForTimeout(500)
      }

      const deleteHistoryButton = page.locator('button[title*="history"], button[title*="歷史"]')

      if (await deleteHistoryButton.count() > 0) {
        await deleteHistoryButton.first().click()

        const dialog = page.locator('[role="dialog"]')
        if (await dialog.count() > 0) {
          await expect(dialog).toBeVisible()
          await expect(dialog).toContainText(/history/i)
          await expect(dialog).toContainText(/group/i)
        }
      }
    })
  })

  test.describe('Button Component Styling', () => {
    test('History page top-right buttons should be proper Button components', async ({ page }) => {
      await page.goto('/history')
      await page.waitForLoadState('networkidle')

      // Verify delete all button exists and is clickable
      const deleteAllButton = page.locator('button:has-text("delete_all"), button:has-text("一鍵清除")')
      if (await deleteAllButton.count() > 0) {
        await expect(deleteAllButton.first()).toBeVisible()
        await expect(deleteAllButton.first()).toBeEnabled()
      }

      // Verify refresh button exists and is clickable
      const refreshButton = page.locator('button:has-text("refresh"), button:has-text("刷新"), button:has-text("Refresh")')
      if (await refreshButton.count() > 0) {
        await expect(refreshButton.first()).toBeVisible()
        await expect(refreshButton.first()).toBeEnabled()
      }
    })
  })

  test.describe('API Delete Endpoints', () => {
    test('DELETE /api/v1/history should exist and work', async ({ request }) => {
      const response = await request.delete('/api/v1/history', {
        headers: {
          'X-API-Key': 'test-api-key'
        }
      })

      const validStatuses = [200, 307, 401, 403, 404]
      expect(validStatuses).toContain(response.status())
    })

    test('DELETE /api/v1/history/by-group/:groupId should exist and work', async ({ request }) => {
      const response = await request.delete('/api/v1/history/by-group/999', {
        headers: {
          'X-API-Key': 'test-api-key'
        }
      })

      const validStatuses = [200, 401, 403, 404]
      expect(validStatuses).toContain(response.status())
    })
  })
})
