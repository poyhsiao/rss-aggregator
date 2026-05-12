import { chromium } from '@playwright/test';

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage();

await page.goto('http://localhost:8080/settings');
await page.waitForLoadState('networkidle');
await page.waitForTimeout(500);

// Step 1: Open Feature Flags dialog (click RSS icon 10 times)
console.log('=== STEP 1: Open Feature Flags ===');
const headerSvg = page.locator('header svg').first();
for (let i = 0; i < 10; i++) {
  await headerSvg.click({ timeout: 500 });
  await page.waitForTimeout(100);
}
await page.waitForTimeout(500);

// Check dialog is open
const dialogText = await page.locator('body').innerText();
const hasFeatureFlags = dialogText.includes('Feature Flags');
console.log('Feature Flags dialog open:', hasFeatureFlags);

// Step 2: Enable Share Links toggle
console.log('\n=== STEP 2: Enable Share Links ===');
const shareToggle = page.locator('.toggle-shareLinks');
if (await shareToggle.count() > 0) {
  const circlePos = await shareToggle.locator('span').first().evaluate(el => {
    const bb = el.getBoundingClientRect();
    const parentBB = el.parentElement.getBoundingClientRect();
    return bb.left - parentBB.left;
  });
  console.log('Share Links current state:', circlePos > 20 ? 'ON' : 'OFF');
  
  if (circlePos <= 20) {
    await shareToggle.click();
    await page.waitForTimeout(300);
    console.log('Clicked Share Links toggle');
  }
  
  // Verify it's ON now
  const newPos = await shareToggle.locator('span').first().evaluate(el => {
    const bb = el.getBoundingClientRect();
    const parentBB = el.parentElement.getBoundingClientRect();
    return bb.left - parentBB.left;
  });
  console.log('Share Links after click:', newPos > 20 ? 'ON ✓' : 'OFF');
} else {
  console.log('Share Links toggle not found!');
}

// Take screenshot of dialog with Share Links ON
await page.screenshot({ path: '/tmp/ff-share-links-on.png' });
console.log('Screenshot saved');

// Step 3: Close Feature Flags dialog
console.log('\n=== STEP 3: Close Feature Flags ===');
const closeBtn = page.locator('.close-btn');
if (await closeBtn.count() > 0) {
  await closeBtn.click();
  await page.waitForTimeout(500);
  console.log('Dialog closed');
}

// Step 4: Go to Feed and open Preview
console.log('\n=== STEP 4: Open RSS Preview ===');
await page.goto('http://localhost:8080/');
await page.waitForLoadState('networkidle');
await page.waitForTimeout(500);

// Click Preview Feed
const previewBtn = page.locator('button:has-text("Preview Feed")');
if (await previewBtn.count() > 0) {
  await previewBtn.first().click();
  await page.waitForTimeout(1000);
  console.log('Clicked Preview Feed');
  
  await page.screenshot({ path: '/tmp/preview-with-share-links.png' });
  
  // Check for Share Links
  const shareLinksText = page.locator('text=Share Links');
  const slCount = await shareLinksText.count();
  console.log('Share Links elements in preview:', slCount);
  
  if (slCount > 0) {
    console.log('✓ Share Links button IS VISIBLE when feature is ON!');
    const bb = await shareLinksText.first().boundingBox();
    console.log('Position:', bb);
  } else {
    console.log('✗ Share Links NOT visible');
  }
  
  // Get preview dialog content
  const previewText = await page.locator('.fixed.inset-0').last().innerText().catch(() => '');
  console.log('\nPreview dialog content (200 chars):', previewText.substring(0, 200));
}

await browser.close();
console.log('\nDone');
