import { test, expect } from '@playwright/test'

test('debug with route check', async ({ page }) => {
  await page.goto('/settings')
  await page.waitForLoadState('networkidle')
  
  // Check route path
  const routePath = await page.evaluate(() => {
    return (window as any).__VUE_DEVTOOLS_GLOBAL_HOOK__ ? 'vue detected' : 'no vue devtools'
  })
  console.log('Vue state:', routePath)
  
  // Try to directly trigger the dialog via JS
  await page.evaluate(() => {
    // Find the layout component instance
    const layout = document.querySelector('#app > div')
    console.log('Layout element found:', !!layout)
    
    // Check if layout has the right children
    const header = document.querySelector('header')
    console.log('Header found:', !!header)
    
    if (header) {
      const rss = header.querySelector('svg')
      console.log('RSS svg found:', !!rss)
    }
  })
  
  // Use page.route to intercept and log API calls
  await page.route('**/api/**', route => {
    console.log('API call:', route.request().url())
    route.continue()
  })
  
  // Now click
  const rssIcon = page.locator('header svg').first()
  for (let i = 1; i <= 10; i++) {
    await rssIcon.click()
    await page.waitForTimeout(100)
  }
  
  await page.waitForTimeout(1000)
  
  // Check dialog
  const dialogCount = await page.locator('[role="dialog"]').count()
  console.log('Dialog count:', dialogCount)
  
  // Get any HTML that contains 🔧
  const pageContent = await page.content()
  if (pageContent.includes('🔧')) {
    console.log('🔧 found in page!')
    const dialogIndex = pageContent.indexOf('🔧')
    console.log('Context:', pageContent.substring(dialogIndex - 100, dialogIndex + 100))
  }
})
