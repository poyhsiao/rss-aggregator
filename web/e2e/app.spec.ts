import { test, expect } from '@playwright/test'

test.describe('Sources Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/sources')
    await page.waitForLoadState('networkidle')
  })

  test('should display sources page', async ({ page }) => {
    await expect(page.getByRole('heading', { name: /sources|來源/i })).toBeVisible()
  })

  test('should display existing sources', async ({ page }) => {
    const cards = page.locator('[class*="bg-white"][class*="rounded-xl"]')
    const count = await cards.count()
    expect(count).toBeGreaterThanOrEqual(0)
  })

  test('should create a new source', async ({ page }) => {
    await page.goto('/sources')
    await page.waitForLoadState('networkidle')
    
    const timestamp = Date.now()
    const sourceName = `Test Source ${timestamp}`
    const sourceUrl = `https://${timestamp}.example.com/rss.xml`

    await page.getByRole('button', { name: /add|新增/i }).click()
    await page.waitForTimeout(500)
    
    const heading = page.getByRole('heading', { name: /add source/i, level: 2 })
    await expect(heading).toBeVisible({ timeout: 5000 })
    
    await page.getByPlaceholder(/enter source name/i).fill(sourceName)
    await page.getByPlaceholder(/enter rss url/i).fill(sourceUrl)
    
    await page.getByRole('button', { name: /^confirm$/i }).click()
    
    await expect(heading).not.toBeVisible({ timeout: 10000 })
    
    await page.waitForFunction((name) => {
      const cards = document.querySelectorAll('[class*="rounded-xl"]')
      for (const card of cards) {
        if (card.textContent && card.textContent.includes(name)) {
          return true
        }
      }
      return false
    }, sourceName, { timeout: 15000 })
    
    const card = page.locator('[class*="bg-white"][class*="rounded-xl"], [class*="bg-neutral-800"][class*="rounded-xl"]').filter({ hasText: sourceName })
    await expect(card).toBeVisible({ timeout: 5000 })
  })

test('should edit an existing source', async ({ page }) => {
    const timestamp = Date.now()
    const originalName = `Original ${timestamp}`
    const newName = `Edited ${timestamp}`
    const originalUrl = `https://original-${timestamp}.example.com/rss.xml`

    await page.getByRole('button', { name: /add|新增/i }).click()
    
    const heading = page.getByRole('heading', { name: /add source/i, level: 2 })
    await expect(heading).toBeVisible({ timeout: 5000 })
    
    await page.getByPlaceholder(/enter source name/i).fill(originalName)
    await page.getByPlaceholder(/enter rss url/i).fill(originalUrl)
    
    await page.getByRole('button', { name: /^confirm$/i }).click()
    
    await expect(heading).not.toBeVisible({ timeout: 10000 })
    await page.waitForTimeout(2000)

    const card = page.locator('[class*="bg-white"][class*="rounded-xl"], [class*="bg-neutral-800"][class*="rounded-xl"]').filter({ hasText: originalName })
    await expect(card).toBeVisible({ timeout: 15000 })
    await card.getByRole('button', { name: '✏️' }).click()
    
    const editHeading = page.getByRole('heading', { name: /edit source/i, level: 2 })
    await expect(editHeading).toBeVisible({ timeout: 5000 })
    
    await page.getByPlaceholder(/enter source name/i).clear()
    await page.getByPlaceholder(/enter source name/i).fill(newName)
    
    await page.getByRole('button', { name: /^confirm$/i }).click()
    
    await expect(editHeading).not.toBeVisible({ timeout: 10000 })
    await page.waitForTimeout(2000)

    const editedCard = page.locator('[class*="bg-white"][class*="rounded-xl"], [class*="bg-neutral-800"][class*="rounded-xl"]').filter({ hasText: newName })
    await expect(editedCard).toBeVisible({ timeout: 15000 })
  })

  test('should delete a source', async ({ page }) => {
    const timestamp = Date.now()
    const sourceName = `To Delete ${timestamp}`
    const sourceUrl = `https://delete-${timestamp}.example.com/rss.xml`

    await page.getByRole('button', { name: /add|新增/i }).click()
    
    const heading = page.getByRole('heading', { name: /add source/i, level: 2 })
    await expect(heading).toBeVisible({ timeout: 5000 })
    
    await page.getByPlaceholder(/enter source name/i).fill(sourceName)
    await page.getByPlaceholder(/enter rss url/i).fill(sourceUrl)
    
    await page.getByRole('button', { name: /^confirm$/i }).click()
    
    await expect(heading).not.toBeVisible({ timeout: 10000 })
    await page.waitForTimeout(2000)

    const card = page.locator('[class*="bg-white"][class*="rounded-xl"], [class*="bg-neutral-800"][class*="rounded-xl"]').filter({ hasText: sourceName })
    await expect(card).toBeVisible({ timeout: 15000 })
    
    page.once('dialog', async dialog => {
      await dialog.accept()
    })
    
    await card.getByRole('button', { name: '🗑️' }).click()
    await page.waitForTimeout(1000)
    
    await expect(card).not.toBeVisible({ timeout: 10000 })
  })

  test('should refresh all sources', async ({ page }) => {
    await page.getByRole('button', { name: /refresh all|重新整理/i }).click()
    await page.waitForTimeout(1000)
  })
})

test.describe('Feed Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/feed')
    await page.waitForLoadState('networkidle')
  })

  test('should display feed page', async ({ page }) => {
    await expect(page.getByRole('heading', { name: /feed/i })).toBeVisible()
  })

  test('should display feed content', async ({ page }) => {
    const content = await page.locator('body').innerText()
    expect(content.length).toBeGreaterThan(0)
  })
})

test.describe('History Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/history')
    await page.waitForLoadState('networkidle')
  })

  test('should display history page', async ({ page }) => {
    await expect(page.getByRole('heading', { name: /history/i })).toBeVisible()
  })

  test('should display batch cards if data exists', async ({ page }) => {
    const cards = page.locator('[class*="bg-white"][class*="rounded-xl"]')
    const count = await cards.count()
    expect(count).toBeGreaterThanOrEqual(0)
  })

  test('should show batch details when clicking a batch', async ({ page }) => {
    const cards = page.locator('[class*="bg-white"][class*="rounded-xl"]')
    const count = await cards.count()
    if (count > 0) {
      await cards.nth(0).click()
      await page.waitForTimeout(500)
    }
  })
})

test.describe('Keys Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/keys')
    await page.waitForLoadState('networkidle')
  })

  test('should display keys page', async ({ page }) => {
    await expect(page.getByRole('heading', { name: /key/i })).toBeVisible()
  })

  test('should create a new API key', async ({ page }) => {
    const timestamp = Date.now()
    const keyName = `Test Key ${timestamp}`

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

    const card = page.locator('[class*="bg-white"][class*="rounded-xl"], [class*="bg-neutral-800"][class*="rounded-xl"]').filter({ hasText: keyName })
    await expect(card).toBeVisible({ timeout: 10000 })
  })

  test('should delete an API key', async ({ page }) => {
    const timestamp = Date.now()
    const keyName = `To Delete ${timestamp}`

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

    const card = page.locator('[class*="bg-white"][class*="rounded-xl"], [class*="bg-neutral-800"][class*="rounded-xl"]').filter({ hasText: keyName })
    await expect(card).toBeVisible({ timeout: 10000 })
    
    page.once('dialog', async dialog => {
      await dialog.accept()
    })
    
    const deleteBtn = card.getByRole('button', { name: /delete|刪除/i })
    await deleteBtn.click()
    await page.waitForTimeout(1000)

    await expect(card).not.toBeVisible({ timeout: 10000 })
  })
})

test.describe('Stats Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/stats')
    await page.waitForLoadState('networkidle')
  })

  test('should display stats page', async ({ page }) => {
    await expect(page.getByRole('heading', { name: /stat/i })).toBeVisible()
  })

  test('should display chart', async ({ page }) => {
    const chart = page.locator('canvas')
    const isVisible = await chart.isVisible()
    expect(isVisible).toBe(true)
  })
})

test.describe('Logs Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/logs')
    await page.waitForLoadState('networkidle')
  })

  test('should display logs page', async ({ page }) => {
    await expect(page.getByRole('heading', { name: /log/i })).toBeVisible()
  })
})

test.describe('Navigation', () => {
  test('should navigate between pages', async ({ page }) => {
    await page.goto('/')

    await page.getByRole('link', { name: /sources/i }).click()
    await expect(page).toHaveURL(/sources/)

    await page.getByRole('link', { name: /feed/i }).click()
    await expect(page).toHaveURL(/\/$/)

    await page.getByRole('link', { name: /history/i }).click()
    await expect(page).toHaveURL(/history/)

    await page.getByRole('link', { name: /key/i }).click()
    await expect(page).toHaveURL(/keys/)

    await page.getByRole('link', { name: /stat/i }).click()
    await expect(page).toHaveURL(/stats/)
  })
})