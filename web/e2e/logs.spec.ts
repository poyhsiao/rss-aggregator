import { test, expect } from '@playwright/test'

test.describe('Logs Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/logs')
    await page.waitForLoadState('networkidle')
  })

  test('should display logs page with tabs', async ({ page }) => {
    await expect(page.getByRole('heading', { name: /log/i })).toBeVisible()
    
    await expect(page.getByRole('button', { name: /system log|系統日誌/i })).toBeVisible()
    await expect(page.getByRole('button', { name: /operation log|操作日誌/i })).toBeVisible()
  })

  test('should switch between tabs', async ({ page }) => {
    const systemTab = page.getByRole('button', { name: /system log|系統日誌/i })
    const operationTab = page.getByRole('button', { name: /operation log|操作日誌/i })

    await systemTab.click()
    await page.waitForTimeout(300)
    
    await operationTab.click()
    await page.waitForTimeout(300)

    await expect(operationTab).toHaveText(/operation log|操作日誌/i)
  })

  test('should display empty state for operation logs when no operations', async ({ page }) => {
    await page.getByRole('button', { name: /operation log|操作日誌/i }).click()
    await page.waitForTimeout(300)

    const emptyText = page.getByText(/no operation record|沒有操作記錄/i)
    await expect(emptyText).toBeVisible()
  })
})

test.describe('Operation Logs', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/logs')
    await page.waitForLoadState('networkidle')
  })

  test('should log source creation in operation logs', async ({ page }) => {
    const timestamp = Date.now()
    const sourceName = `Test Log Source ${timestamp}`
    const sourceUrl = `https://${timestamp}.example.com/rss.xml`

    await page.goto('/sources')
    await page.waitForLoadState('networkidle')
    
    await page.getByRole('button', { name: /add|新增/i }).click()
    await page.waitForTimeout(500)
    
    const heading = page.getByRole('heading', { name: /add source/i, level: 2 })
    await expect(heading).toBeVisible({ timeout: 5000 })
    
    await page.getByPlaceholder(/enter source name/i).fill(sourceName)
    await page.getByPlaceholder(/enter rss url/i).fill(sourceUrl)
    
    await page.getByRole('button', { name: /^confirm$/i }).click()
    
    await expect(heading).not.toBeVisible({ timeout: 10000 })

    await page.goto('/logs')
    await page.waitForLoadState('networkidle')

    await page.getByRole('button', { name: /operation log|操作日誌/i }).click()
    await page.waitForTimeout(300)

    const logCard = page.locator('[class*="rounded-xl"]').filter({ hasText: /create source|新增來源/i })
    await expect(logCard).toBeVisible({ timeout: 5000 })
  })

  test('should log API key creation in operation logs', async ({ page }) => {
    const timestamp = Date.now()
    const keyName = `Test Log Key ${timestamp}`

    await page.goto('/keys')
    await page.waitForLoadState('networkidle')

    await page.getByRole('button', { name: /add|新增/i }).click()
    
    const dialog = page.locator('[class*="rounded-2xl"]').filter({ has: page.getByRole('heading', { level: 2 }) })
    await dialog.waitFor({ state: 'visible', timeout: 5000 })
    
    await page.getByPlaceholder(/enter a name to identify this key/i).fill(keyName)
    
    await Promise.all([
      page.waitForResponse(resp => resp.url().includes('/api/v1/keys') && resp.request().method() === 'POST', { timeout: 15000 }),
      dialog.getByRole('button', { name: /^confirm$/i }).click()
    ])
    
    await dialog.locator('code').waitFor({ timeout: 5000 })
    
    const confirmButtons = dialog.getByRole('button')
    await confirmButtons.filter({ hasText: /confirm/i }).click()
    await dialog.waitFor({ state: 'hidden', timeout: 5000 })

    await page.goto('/logs')
    await page.waitForLoadState('networkidle')

    await page.getByRole('button', { name: /operation log|操作日誌/i }).click()
    await page.waitForTimeout(300)

    const logCard = page.locator('[class*="rounded-xl"]').filter({ hasText: /create api key|新增 api key/i })
    await expect(logCard).toBeVisible({ timeout: 5000 })
  })
})

test.describe('Log Card Interaction', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/logs')
    await page.waitForLoadState('networkidle')
  })

  test('should expand and collapse log card', async ({ page }) => {
    await page.getByRole('button', { name: /system log|系統日誌/i }).click()
    await page.waitForTimeout(300)

    const cards = page.locator('[class*="rounded-xl"][class*="border"]')
    const count = await cards.count()
    
    if (count > 0) {
      const card = cards.first()
      await card.click()
      await page.waitForTimeout(300)
      
      const chevron = card.locator('svg').last()
      await expect(chevron).toHaveClass(/rotate-180/)
      
      await card.click()
      await page.waitForTimeout(300)
      
      await expect(chevron).not.toHaveClass(/rotate-180/)
    }
  })

  test('should show copy button for error logs', async ({ page }) => {
    await page.getByRole('button', { name: /system log|系統日誌/i }).click()
    await page.waitForTimeout(300)

    const errorCards = page.locator('[class*="rounded-xl"][class*="border-red"]')
    const count = await errorCards.count()
    
    if (count > 0) {
      const card = errorCards.first()
      await card.click()
      await page.waitForTimeout(300)

      const copyButton = card.getByRole('button', { name: /copy error|複製錯誤/i })
      if (await copyButton.isVisible()) {
        await copyButton.click()
        await page.waitForTimeout(300)

        await expect(card.getByRole('button', { name: /copied|已複製/i })).toBeVisible()
      }
    }
  })
})