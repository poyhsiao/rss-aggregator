import { chromium } from '@playwright/test';

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage();

console.log('Opening app...');
await page.goto('http://localhost:8080/');
await page.waitForLoadState('networkidle');

console.log('Page title:', await page.title());

// Take screenshot of main page
await page.screenshot({ path: '/tmp/main-page.png', fullPage: true });
console.log('Main page screenshot saved');

// Now go to settings
await page.goto('http://localhost:8080/settings');
await page.waitForLoadState('networkidle');

console.log('URL:', page.url());

// Take screenshot of settings page
await page.screenshot({ path: '/tmp/settings-page2.png', fullPage: true });
console.log('Settings page screenshot saved');

// Click 10 times on first SVG in header
const headerSvg = page.locator('header svg').first();
for (let i = 0; i < 10; i++) {
  try {
    await headerSvg.click({ timeout: 500 });
    console.log(`Click ${i+1}: success`);
  } catch (e) {
    console.log(`Click ${i+1}: ${e.message.split('\n')[0]}`);
  }
  await page.waitForTimeout(100);
}

await page.waitForTimeout(500);
await page.screenshot({ path: '/tmp/after-10-clicks.png', fullPage: true });
console.log('After 10 clicks screenshot saved');

// Get current page text
const pageText = await page.locator('body').innerText();
console.log('\n=== PAGE TEXT ===\n', pageText.substring(0, 1000));

// Check for any visible dialog
const overlays = await page.locator('.fixed, [style*="z-index"], [role="dialog"]').all();
console.log('\n=== FIXED/Z-INDEX ELEMENTS ===');
for (const el of overlays.slice(0, 10)) {
  const style = await el.getAttribute('style').catch(() => '');
  const classes = await el.getAttribute('class').catch(() => '');
  const role = await el.getAttribute('role').catch(() => '');
  console.log(`style: ${style} | classes: ${classes} | role: ${role}`);
}

await browser.close();
console.log('\nDone');
