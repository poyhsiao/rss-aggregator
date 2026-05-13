import { test, expect } from '@playwright/test'

test('debug dialog opening', async ({ page }) => {
  await page.goto('/settings')
  await page.waitForLoadState('networkidle')
  
  // Manually set up the click handler via Vue
  const result = await page.evaluate(async () => {
    // Wait for Vue to be ready
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    // Try to find the Vue app
    const app = document.querySelector('#app')
    if (!app) return { error: 'No #app found' }
    
    const vueInstance = (app as any).__vue_app__
    if (!vueInstance) return { error: 'No Vue app found' }
    
    // Try to access Vue's internal state
    return { 
      vueFound: true,
      appChildren: app.children.length,
      headerExists: !!document.querySelector('header')
    }
  })
  console.log('Debug result:', result)
  
  // Count clicks
  const rssIcon = page.locator('header svg').first()
  console.log('Clicking RSS icon 10 times...')
  
  for (let i = 1; i <= 10; i++) {
    await rssIcon.click()
    console.log(`Click ${i} completed`)
    await page.waitForTimeout(200)
  }
  
  // Check for dialog in DOM
  const html = await page.content()
  console.log('Contains role="dialog":', html.includes('role="dialog"'))
  console.log('Contains 🔧:', html.includes('🔧'))
  
  // Count any dialog-like elements
  const dialogs = await page.locator('[role="dialog"], .fixed.inset-0.z-50, [class*="backdrop"]').count()
  console.log('Potential dialog elements:', dialogs)
  
  await page.screenshot({ path: '/tmp/dialog-debug.png' })
})
