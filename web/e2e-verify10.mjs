import { chromium } from '@playwright/test';

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage();

await page.goto('http://localhost:8080/');
await page.waitForLoadState('networkidle');
await page.waitForTimeout(1000);

// Click Preview Feed button
const previewFeedBtns = page.locator('button:has-text("Preview Feed")');
const pCount = await previewFeedBtns.count();
console.log('Preview Feed buttons found:', pCount);

if (pCount > 0) {
  console.log('Clicking first Preview Feed button...');
  await previewFeedBtns.first().click();
  await page.waitForTimeout(1000);
  
  await page.screenshot({ path: '/tmp/after-preview-click.png' });
  console.log('Screenshot saved');
  
  // Look for Share Links text/button
  const shareLinksText = page.locator('text=Share Links');
  const slCount = await shareLinksText.count();
  console.log('Share Links elements found:', slCount);
  
  // Get all text in dialog-like elements
  const fixedElements = await page.locator('.fixed').all();
  console.log('\nFixed elements count:', fixedElements.length);
  
  for (const el of fixedElements.slice(0, 5)) {
    const classes = await el.getAttribute('class');
    const txt = await el.innerText().catch(() => '');
    if (txt.trim()) {
      console.log(`Fixed el classes: ${classes?.substring(0, 80)}`);
      console.log(`  Text: "${txt.substring(0, 200)}"`);
    }
  }
  
  // Check if Share Links toggle is visible on the page
  const shareToggle = page.locator('.toggle-shareLinks');
  const stCount = await shareToggle.count();
  console.log('\nShare Links toggle count:', stCount);
  
  // Get body text
  const bodyText = await page.locator('body').innerText();
  console.log('\nBody text (300 chars):', bodyText.substring(0, 300));
}

await browser.close();
console.log('\nDone');
