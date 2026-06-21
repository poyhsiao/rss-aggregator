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
  await page.waitForLoadState('domcontentloaded')

  // Take screenshot of current state
  await page.screenshot({ path: 'test-results/debug-initial.png', fullPage: true })

  // Get page title and URL
  console.log('Page title:', await page.title())
  console.log('Page URL:', page.url())

  // List all buttons on the page
  const buttons = await page.getByRole('button').all()
  console.log('All buttons found:', await Promise.all(buttons.map(b => b.textContent())))

  // Click Add button
  const addBtn = page.getByRole('button', { name: /add|新增/i })
  console.log('Add button visible:', await addBtn.isVisible())
  console.log('Add button count:', await page.getByRole('button', { name: /add|新增/i }).count())

  try {
    await addBtn.click({ timeout: 5000 })
    console.log('Add button clicked successfully')
  } catch (e) {
    console.log('Add button click failed:', e)
    await page.screenshot({ path: 'test-results/debug-before-click.png', fullPage: true })
  }

  await page.waitForTimeout(500)

  // Fill form
  const dialog = page.locator('[class*="rounded-2xl"]').filter({ has: page.getByRole('heading', { level: 2 }) })

  try {
    await dialog.waitFor({ state: 'visible', timeout: 5000 })
    console.log('Dialog visible')

    await page.getByPlaceholder(/enter source name/i).fill('Debug Test Source')
    await page.getByPlaceholder(/enter rss url/i).fill('https://debug.example.com/rss.xml')

    // Click Confirm button
    const confirmBtn = dialog.getByRole('button', { name: /^confirm$/i })
    await confirmBtn.click()
    console.log('Confirm clicked')

    // Wait and check
    await page.waitForTimeout(3000)
  } catch (e) {
    console.log('Form interaction error:', e)
  }

  // Print console messages
  console.log('Console messages:', consoleMessages)
  console.log('Requests:', requests.filter(r => r.includes('sources') || r.includes('8000')))

  // Check if dialog is still visible
  const dialogVisible = await dialog.isVisible()
  console.log('Dialog visible:', dialogVisible)

  // Take screenshot
  await page.screenshot({ path: 'test-results/debug-screenshot.png', fullPage: true })
})
