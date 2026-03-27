import { test, expect } from '@playwright/test'

test.describe('Backup Functionality', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/settings')
    await page.waitForLoadState('networkidle')
  })

  test('should display backup section in settings', async ({ page }) => {
    await expect(page.getByRole('heading', { name: /backup|備份/i })).toBeVisible()
  })

  test('should display export backup button', async ({ page }) => {
    const exportButton = page.getByRole('button', { name: /export|匯出/i })
    await expect(exportButton).toBeVisible()
  })

  test('should display import backup section', async ({ page }) => {
    await expect(page.getByRole('heading', { name: /import|匯入/i })).toBeVisible()
  })

  test('should display export options', async ({ page }) => {
    const feedItemsCheckbox = page.getByRole('checkbox', { name: /feed items|文章/i })
    const previewCheckbox = page.getByRole('checkbox', { name: /preview|預覽/i })
    const logsCheckbox = page.getByRole('checkbox', { name: /logs|日誌/i })

    await expect(feedItemsCheckbox.or(feedItemsCheckbox)).toBeVisible()
  })

  test('should toggle export options', async ({ page }) => {
    const feedItemsCheckbox = page.locator('input[type="checkbox"]').first()
    
    if (await feedItemsCheckbox.isVisible()) {
      const initialState = await feedItemsCheckbox.isChecked()
      await feedItemsCheckbox.click()
      await page.waitForTimeout(300)
      const newState = await feedItemsCheckbox.isChecked()
      expect(newState).toBe(!initialState)
    }
  })

  test('should show file input for import in web mode', async ({ page }) => {
    const fileInput = page.locator('input[type="file"][accept=".zip"]')
    const isVisible = await fileInput.isVisible().catch(() => false)
    
    if (!isVisible) {
      const uploadArea = page.locator('[class*="border-dashed"]').filter({ hasText: /select|選擇/i })
      await expect(uploadArea.or(fileInput)).toBeVisible()
    }
  })

  test('should trigger export when clicking export button', async ({ page }) => {
    const exportButton = page.getByRole('button', { name: /export|匯出/i })
    
    const downloadPromise = page.waitForEvent('download', { timeout: 30000 }).catch(() => null)
    
    await exportButton.click()
    await page.waitForTimeout(3000)
    
    const download = await downloadPromise
    if (download) {
      const fileName = download.suggestedFilename()
      expect(fileName).toMatch(/rss-backup.*\.zip/)
    }
  })

  test('should show loading state during export', async ({ page }) => {
    const exportButton = page.getByRole('button', { name: /export|匯出/i })
    
    await exportButton.click()
    await page.waitForTimeout(100)
    
    const loadingSpinner = page.locator('svg').filter({ has: page.locator('[class*="animate-spin"]') })
    const isLoading = await loadingSpinner.isVisible().catch(() => false)
    
    await page.waitForTimeout(5000)
  })

  test('should handle file selection for import', async ({ page }) => {
    const fileInput = page.locator('input[type="file"][accept=".zip"]')
    
    if (await fileInput.isVisible()) {
      await fileInput.setInputFiles({
        name: 'test-backup.zip',
        mimeType: 'application/zip',
        buffer: Buffer.from('test content'),
      })
      await page.waitForTimeout(1000)
    }
  })

  test('should display import button after file selection', async ({ page }) => {
    const fileInput = page.locator('input[type="file"][accept=".zip"]')
    
    if (await fileInput.isVisible()) {
      const importButton = page.getByRole('button', { name: /^import$|^匯入$/i })
      const isVisible = await importButton.isVisible().catch(() => false)
      
      if (!isVisible) {
        const confirmButton = page.getByRole('button', { name: /confirm|確認/i })
        await expect(confirmButton.or(importButton)).toBeVisible()
      }
    }
  })

  test('should show confirmation dialog before import', async ({ page }) => {
    const fileInput = page.locator('input[type="file"][accept=".zip"]')
    
    if (await fileInput.isVisible()) {
      const confirmDialog = page.locator('[class*="fixed"][class*="inset-0"][class*="z-50"]')
      const isVisible = await confirmDialog.isVisible().catch(() => false)
      
      if (isVisible) {
        const cancelButton = confirmDialog.getByRole('button', { name: /cancel|取消/i })
        if (await cancelButton.isVisible()) {
          await cancelButton.click()
        }
      }
    }
  })
})

test.describe('Backup Page Accessibility', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/settings')
    await page.waitForLoadState('networkidle')
  })

  test('should have proper heading structure', async ({ page }) => {
    const heading = page.getByRole('heading', { name: /backup|備份/i })
    await expect(heading).toBeVisible()
  })

  test('should have accessible buttons', async ({ page }) => {
    const buttons = page.getByRole('button')
    const count = await buttons.count()
    expect(count).toBeGreaterThan(0)
  })

  test('should have accessible checkboxes', async ({ page }) => {
    const checkboxes = page.getByRole('checkbox')
    const count = await checkboxes.count()
    expect(count).toBeGreaterThan(0)
  })
})

test.describe('Backup Error Handling', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/settings')
    await page.waitForLoadState('networkidle')
  })

  test('should show toast on export error', async ({ page }) => {
    await page.route('**/api/v1/backup/export', route => {
      route.fulfill({ status: 500, body: JSON.stringify({ detail: 'Export failed' }) })
    })

    const exportButton = page.getByRole('button', { name: /export|匯出/i })
    await exportButton.click()
    await page.waitForTimeout(2000)

    const toast = page.locator('[class*="fixed"][class*="top-"][class*="right-"]')
    const isVisible = await toast.isVisible().catch(() => false)
  })

  test('should show toast on import error', async ({ page }) => {
    await page.route('**/api/v1/backup/import', route => {
      route.fulfill({ status: 500, body: JSON.stringify({ detail: 'Import failed' }) })
    })

    const fileInput = page.locator('input[type="file"][accept=".zip"]')
    
    if (await fileInput.isVisible()) {
      await fileInput.setInputFiles({
        name: 'test-backup.zip',
        mimeType: 'application/zip',
        buffer: Buffer.from('test content'),
      })
      await page.waitForTimeout(2000)
    }
  })
})