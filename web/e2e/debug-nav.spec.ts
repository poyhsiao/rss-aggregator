import { test, expect } from '@playwright/test'

test('debug navigation on click', async ({ page }) => {
  await page.goto('/settings')
  await page.waitForLoadState('networkidle')
  
  const rssIcon = page.locator('header svg').first()
  
  console.log('URL before clicks:', page.url())
  
  for (let i = 1; i <= 3; i++) {
    await rssIcon.click()
    await page.waitForTimeout(300)
    console.log(`After click ${i}, URL:`, page.url())
  }
  
  // Check what page we're on
  const bodyText = await page.locator('body').textContent()
  console.log('Current page text (first 200):', bodyText?.substring(0, 200))
})
