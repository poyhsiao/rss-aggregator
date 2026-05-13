import { test, expect } from '@playwright/test'

test('debug settings page', async ({ page }) => {
  await page.goto('/settings')
  await page.waitForLoadState('networkidle')
  
  // Wait for any redirect
  await page.waitForTimeout(2000)
  
  console.log('Current URL:', page.url())
  
  // Check page content
  const body = await page.locator('body').textContent()
  console.log('Body text (first 500 chars):', body?.substring(0, 500))
  
  // Check for dialog
  const dialogCount = await page.locator('[role="dialog"]').count()
  console.log('Dialog count:', dialogCount)
  
  // Check for header
  const headerCount = await page.locator('header').count()
  console.log('Header count:', headerCount)
  
  // Take a screenshot
  await page.screenshot({ path: '/tmp/settings-debug.png' })
  console.log('Screenshot saved to /tmp/settings-debug.png')
})
