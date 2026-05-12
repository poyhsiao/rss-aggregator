import { chromium } from '@playwright/test';

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage();

console.log('Opening app...');
await page.goto('http://localhost:8080/settings');
await page.waitForLoadState('networkidle');

console.log('Page title:', await page.title());

// Take screenshot of settings page
await page.screenshot({ path: '/tmp/settings-page.png', fullPage: true });
console.log('Full page screenshot saved');

// Find "Feature Flags" text and click it
const featureFlagsText = page.locator('text=Feature Flags');
const ffCount = await featureFlagsText.count();
console.log('Found "Feature Flags" elements:', ffCount);

if (ffCount > 0) {
  // Get bounding box
  const bb = await featureFlagsText.first().boundingBox();
  console.log('Feature Flags bounding box:', bb);
  
  // Try clicking it
  try {
    await featureFlagsText.first().click({ timeout: 2000 });
    console.log('Clicked Feature Flags text');
  } catch (e) {
    console.log('Could not click Feature Flags:', e.message);
  }
  
  await page.waitForTimeout(1000);
  await page.screenshot({ path: '/tmp/after-ff-click.png', fullPage: false });
  console.log('Screenshot after FF click saved');
}

// Now let's look at the page HTML structure to find the dialog trigger
const allText = await page.locator('body').innerText();
console.log('\n=== FULL PAGE TEXT ===\n', allText);

// Find any buttons
const buttons = await page.locator('button').all();
console.log('\n=== BUTTONS ===');
for (const btn of buttons.slice(0, 20)) {
  const txt = await btn.innerText().catch(() => '');
  const classes = await btn.getAttribute('class').catch(() => '');
  console.log(`Button: "${txt}" | classes: ${classes}`);
}

// Find any dialog-like elements
const dialogs = await page.locator('[role="dialog"], [role="button"], .fixed, .absolute, .inset-0').all();
console.log('\n=== DIALOG-LIKE ELEMENTS ===', dialogs.length);
for (const d of dialogs.slice(0, 5)) {
  const tag = await d.evaluate(el => el.tagName);
  const classes = await d.getAttribute('class').catch(() => '');
  console.log(`Element: <${tag}> classes: ${classes}`);
}

await browser.close();
console.log('\nDone');
