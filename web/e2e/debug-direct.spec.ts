import { test, expect } from '@playwright/test'

test('debug direct dialog opening via JS', async ({ page }) => {
  await page.goto('/settings')
  await page.waitForLoadState('networkidle')
  await page.waitForTimeout(1000) // Wait for Vue to fully mount
  
  // Try to find any Vue component instance and trigger dialog
  const result = await page.evaluate(() => {
    // Check if there's any way to trigger dialog via DOM
    const app = document.querySelector('#app')
    const vueApp = (app as any).__vue_app__
    
    // Try to find FeatureFlagsDialog or SettingsPage
    const allElements = document.querySelectorAll('*')
    let hasSettingsPage = false
    for (const el of allElements) {
      if (el.className && typeof el.className === 'string' && el.className.includes('settings')) {
        hasSettingsPage = true
      }
    }
    
    return {
      vueAppFound: !!vueApp,
      settingsPageFound: hasSettingsPage,
      bodyHTML: document.body.innerHTML.substring(0, 500)
    }
  })
  console.log('Debug result:', JSON.stringify(result, null, 2))
  
  // Try clicking directly on the parent anchor tag instead of SVG
  const rssLink = page.locator('header a[href="/"]')
  console.log('RSS link count:', await rssLink.count())
  
  if (await rssLink.count() > 0) {
    console.log('Clicking parent anchor tag instead...')
    await rssLink.click({ force: true })
    await page.waitForTimeout(300)
    console.log('URL after anchor click:', page.url())
    
    // Try clicking the SVG with force
    console.log('Clicking SVG with force=true...')
    await page.locator('header svg').first().click({ force: true })
    await page.waitForTimeout(300)
    console.log('URL after SVG force click:', page.url())
  }
  
  // Check for any dialog-like elements
  const dialogHtml = await page.evaluate(() => {
    const allDivs = document.querySelectorAll('.fixed')
    return Array.from(allDivs).map(d => ({
      class: d.className,
      text: d.textContent?.substring(0, 50)
    }))
  })
  console.log('Fixed elements:', JSON.stringify(dialogHtml, null, 2))
})
