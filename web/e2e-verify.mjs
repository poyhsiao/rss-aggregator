import { chromium } from '@playwright/test';

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage();

console.log('Opening app...');
await page.goto('http://localhost:8080/settings');
await page.waitForLoadState('networkidle');

console.log('Page title:', await page.title());
console.log('URL:', page.url());

// Take screenshot of settings page
await page.screenshot({ path: '/tmp/settings-page.png', fullPage: false });
console.log('Screenshot saved to /tmp/settings-page.png');

// Look for RSS icon in header (10 clicks needed)
const rssIcon = page.locator('svg').first();
console.log('Looking for RSS icon...');

// Try to find and click the RSS icon 10 times
for (let i = 0; i < 10; i++) {
  try {
    await rssIcon.click({ timeout: 1000 });
    console.log(`Click ${i+1}: clicked RSS icon`);
  } catch (e) {
    console.log(`Click ${i+1}: could not click RSS icon`);
    break;
  }
}

// Wait a moment for any dialog
await page.waitForTimeout(500);

// Take screenshot after clicks
await page.screenshot({ path: '/tmp/after-clicks.png', fullPage: false });
console.log('Screenshot after clicks saved');

// Look for Feature Flags dialog
const dialog = page.locator('[role="dialog"], .dialog, .modal, .feature-flags');
const dialogCount = await dialog.count();
console.log('Found dialogs:', dialogCount);

if (dialogCount > 0) {
  console.log('Feature Flags dialog appeared!');
  await dialog.screenshot({ path: '/tmp/feature-flags-dialog.png' });
  
  // Look for toggles
  const toggles = page.locator('button[class*="toggle"], [class*="toggle"]');
  const toggleCount = await toggles.count();
  console.log('Found toggle buttons:', toggleCount);
  
  // Print page content for debugging
  const bodyText = await page.locator('body').innerText();
  console.log('Body text snippet:', bodyText.substring(0, 500));
} else {
  console.log('No dialog found');
  // Print page content for debugging
  const bodyText = await page.locator('body').innerText();
  console.log('Body text snippet:', bodyText.substring(0, 500));
}

await browser.close();
console.log('Done');
