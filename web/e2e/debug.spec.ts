import { test, expect } from '@playwright/test'

test('debug create source', async ({ page }) => {
  // Collect console messages
  const consoleMessages: string[] = []
  page.on('console', msg => {
    consoleMessages.push(`${msg.type()}: ${msg.text()}`)
  })
  
  // Collect network requests
  const requests: string[] = []
  page.on('request', req => requests.push(`${req.method()} ${req.url()}`))
  page.on('response', res => {
    if (res.status() >= 400) {
      consoleMessages.push(`HTTP ${res.status()}: ${res.url()}`)
    }
  })
  
  await page.goto('/sources')
  await page.waitForLoadState('networkidle')
  
  // Click Add button
  await page.getByRole('button', { name: /add|新增/i }).click()
  await page.waitForTimeout(500)
  
  // Fill form
  const dialog = page.locator('[class*="rounded-2xl"]').filter({ has: page.getByRole('heading', { level: 2 }) })
  await dialog.waitFor({ state: 'visible', timeout: 5000 })
  
  await page.getByPlaceholder(/enter source name/i).fill('Debug Test Source')
  await page.getByPlaceholder(/enter rss url/i).fill('https://debug.example.com/rss.xml')
  
  // Click Confirm button
  const confirmBtn = dialog.getByRole('button', { name: /^confirm$/i })
  await confirmBtn.click()
  
  // Wait and check
  await page.waitForTimeout(3000)
  
  // Print console messages
  console.log('Console messages:', consoleMessages)
  console.log('Requests:', requests.filter(r => r.includes('sources')))
  
  // Check if dialog is still visible
  const dialogVisible = await dialog.isVisible()
  console.log('Dialog visible:', dialogVisible)
  
  // Take screenshot
  await page.screenshot({ path: 'test-results/debug-screenshot.png' })
})
