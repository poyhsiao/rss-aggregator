import { test, expect } from '@playwright/test'

test('debug header HTML', async ({ page }) => {
  await page.goto('/settings')
  await page.waitForLoadState('networkidle')
  
  // Get header HTML
  const headerHtml = await page.locator('header').innerHTML()
  console.log('Header HTML:', headerHtml.substring(0, 1000))
  
  // Check for any element with class containing h-6
  const h6Elements = await page.locator('.h-6').count()
  console.log('Elements with h-6 class:', h6Elements)
  
  // Find all SVGs and their parents
  const svgs = await page.locator('header svg').all()
  console.log('Number of SVGs:', svgs.length)
  for (let i = 0; i < svgs.length; i++) {
    const parent = await svgs[i].locator('..').innerHTML()
    console.log(`SVG ${i} parent:`, parent.substring(0, 200))
  }
})
