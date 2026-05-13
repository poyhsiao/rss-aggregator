import { test, expect } from '@playwright/test'

test('debug click RSS icon 10 times', async ({ page }) => {
  await page.goto('/settings')
  await page.waitForLoadState('networkidle')
  
  console.log('Current URL:', page.url())
  
  // Find the RSS icon - it should be the first SVG in header
  const rssIcon = page.locator('header svg').first()
  console.log('RSS icon found:', await rssIcon.count())
  
  // Check if it's clickable
  const isVisible = await rssIcon.isVisible()
  console.log('RSS icon visible:', isVisible)
  
  // Get bounding box
  const box = await rssIcon.boundingBox()
  console.log('RSS icon bounding box:', box)
  
  // Click 10 times
  for (let i = 1; i <= 10; i++) {
    await rssIcon.click()
    console.log(`Click ${i} done`)
    await page.waitForTimeout(100)
  }
  
  // Check for dialog
  await page.waitForTimeout(500)
  const dialogCount = await page.locator('[role="dialog"]').count()
  console.log('Dialog count after clicks:', dialogCount)
  
  // Get any visible text in dialog if exists
  if (dialogCount > 0) {
    const dialogText = await page.locator('[role="dialog"]').textContent()
    console.log('Dialog text:', dialogText?.substring(0, 200))
  }
  
  await page.screenshot({ path: '/tmp/click-debug.png' })
})
