import { chromium } from '@playwright/test';

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage();

// Check Feed page
await page.goto('http://localhost:8080/feed');
await page.waitForLoadState('networkidle');
await page.waitForTimeout(1000);

console.log('=== FEED PAGE ===');
const feedTitle = await page.title();
console.log('Title:', feedTitle);

const pageText = await page.locator('body').innerText();
console.log('Feed page text (first 500):', pageText.substring(0, 500));

// Find any clickable cards/items
const clickables = await page.locator('a[href*="/feed/"], [class*="card"], [class*="item"]').all();
console.log('\nClickable elements:', clickables.length);
for (const c of clickables.slice(0, 5)) {
  const txt = await c.innerText().catch(() => '');
  const href = await c.getAttribute('href').catch(() => '');
  console.log(`"${txt.substring(0, 50)}" | href: ${href}`);
}

await page.screenshot({ path: '/tmp/feed-page.png', fullPage: true });

// Check History page
await page.goto('http://localhost:8080/history');
await page.waitForLoadState('networkidle');
await page.waitForTimeout(1000);

console.log('\n=== HISTORY PAGE ===');
const histText = await page.locator('body').innerText();
console.log('History page text (first 500):', histText.substring(0, 500));

await page.screenshot({ path: '/tmp/history-page.png', fullPage: true });

// Check main page
await page.goto('http://localhost:8080/');
await page.waitForLoadState('networkidle');
await page.waitForTimeout(1000);

console.log('\n=== MAIN PAGE ===');
const mainText = await page.locator('body').innerText();
console.log('Main page text (first 500):', mainText.substring(0, 500));

await page.screenshot({ path: '/tmp/main-page2.png', fullPage: true });

await browser.close();
console.log('\nDone');
