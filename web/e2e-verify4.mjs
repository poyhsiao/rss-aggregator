import { chromium } from '@playwright/test';

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage();

await page.goto('http://localhost:8080/settings');
await page.waitForLoadState('networkidle');

// Click RSS icon 10 times
const headerSvg = page.locator('header svg').first();
for (let i = 0; i < 10; i++) {
  await headerSvg.click({ timeout: 500 });
  await page.waitForTimeout(100);
}

await page.waitForTimeout(500);

// Take screenshot focused on dialog
await page.screenshot({ path: '/tmp/feature-flags-dialog.png', fullPage: false });
console.log('Dialog screenshot saved');

// Find the dialog content
const dialogContent = page.locator('.fixed.inset-0.flex.items-center.justify-center p-4, [class*="backdrop-blur"]');
const dcCount = await dialogContent.count();
console.log('Found dialog elements:', dcCount);

if (dcCount > 0) {
  // Get inner content of the dialog
  const inner = await dialogContent.first().innerText();
  console.log('\n=== DIALOG CONTENT ===\n', inner);
  
  // Find all toggle buttons
  const toggles = await page.locator('button').all();
  console.log('\n=== ALL BUTTONS ===');
  for (const btn of toggles) {
    const txt = await btn.innerText().catch(() => '');
    const classes = await btn.getAttribute('class').catch(() => '');
    const disabled = await btn.getAttribute('disabled').catch(() => 'none');
    console.log(`"${txt}" | disabled: ${disabled} | classes: ${classes.substring(0, 100)}`);
  }
}

// Now let's specifically look for Share Links toggle/switch
const shareLinksSwitch = page.locator('text=Share Links').first();
if (await shareLinksSwitch.count() > 0) {
  console.log('\n=== SHARE LINKS ELEMENT FOUND ===');
  const bb = await shareLinksSwitch.boundingBox();
  console.log('Share Links bounding box:', bb);
}

// Look for Group Settings
const groupSettings = page.locator('text=Group Settings').first();
if (await groupSettings.count() > 0) {
  console.log('\n=== GROUP SETTINGS FOUND ===');
  const bb = await groupSettings.boundingBox();
  console.log('Group Settings bounding box:', bb);
}

// Now let's try to find the Share Links toggle specifically
const allText = await page.locator('body').innerText();
const lines = allText.split('\n').filter(l => l.trim().length > 0);
console.log('\n=== ALL TEXT LINES ===');
for (const line of lines) {
  console.log(line);
}

await browser.close();
console.log('\nDone');
