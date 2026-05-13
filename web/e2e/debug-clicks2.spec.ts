import { test, expect } from '@playwright/test'

test('debug click handler directly', async ({ page }) => {
  await page.goto('/settings')
  await page.waitForLoadState('networkidle')
  await page.waitForTimeout(1000)
  
  // Click the parent div with cursor-pointer (which should have the handler)
  const logoDiv = page.locator('header .cursor-pointer').first()
  console.log('Logo div found:', await logoDiv.count())
  
  // Click 10 times
  for (let i = 1; i <= 10; i++) {
    await logoDiv.click()
    console.log(`Click ${i}`)
    await page.waitForTimeout(200)
  }
  
  // Check for dialog
  const dialogHtml = await page.evaluate(() => {
    const allDivs = document.querySelectorAll('.fixed')
    return Array.from(allDivs).map(d => ({
      class: d.className,
      hasDialog: d.className.includes('dialog') || d.getAttribute('role') === 'dialog',
      text: d.textContent?.substring(0, 100)
    }))
  })
  console.log('Fixed elements:', JSON.stringify(dialogHtml, null, 2))
  
  const dialogCount = await page.locator('[role="dialog"]').count()
  console.log('Dialog count:', dialogCount)
})
