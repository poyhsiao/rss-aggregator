import { chromium } from '@playwright/test';

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage();

await page.goto('http://localhost:8080/');
await page.waitForLoadState('networkidle');
await page.waitForTimeout(1000);

// Take screenshot of feed page
await page.screenshot({ path: '/tmp/feed-overview.png', fullPage: true });
console.log('Feed page screenshot saved');

// Look for "Preview Feed" button
const previewFeedBtns = page.locator('button:has-text("Preview Feed"), button:has-text("Preview")');
const pCount = await previewFeedBtns.count();
console.log('Preview Feed buttons found:', pCount);

if (pCount > 0) {
  console.log('Clicking first Preview Feed button...');
  await previewFeedBtns.first().click();
  await page.waitForTimeout(1000);
  
  await page.screenshot({ path: '/tmp/after-preview-click.png' });
  
  // Look for Share Links button in the opened dialog
  const shareLinksBtn = page.locator('button:has-text("Share Links"), text=Share Links');
  const slCount = await shareLinksBtn.count();
  console.log('Share Links button count:', slCount);
  
  if (slCount > 0) {
    console.log('✓ Share Links button found in preview dialog!');
    const bb = await shareLinksBtn.first().boundingBox();
    console.log('Share Links button position:', bb);
  } else {
    console.log('✗ Share Links button NOT found in preview dialog');
  }
  
  // Print page content to find what's in the dialog
  const dialogText = await page.locator('[role="dialog"], .fixed.inset-0').first().innerText().catch(() => 'no dialog');
  console.log('\nDialog content:', dialogText.substring(0, 500));
} else {
  console.log('No Preview Feed button found');
}

// Also look for any dialog/modal
const dialogs = await page.locator('[role="dialog"]').count();
console.log('\nDialogs found:', dialogs);

if (dialogs > 0) {
  await page.screenshot({ path: '/tmp/dialog-visible.png' });
}

await browser.close();
console.log('\nDone');
