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

// Enable Groups
const groupsToggle = page.locator('.toggle-groups');
await groupsToggle.click();
await page.waitForTimeout(300);

// Enable Schedules
const schedulesToggle = page.locator('.toggle-schedules');
await schedulesToggle.click();
await page.waitForTimeout(300);

// Enable Share Links
const shareLinksToggle = page.locator('.toggle-shareLinks');
await shareLinksToggle.click();
await page.waitForTimeout(300);

// Check states
const getCirclePos = async (toggle) => {
  return toggle.locator('span').first().evaluate(el => {
    const bb = el.getBoundingClientRect();
    const parentBB = el.parentElement.getBoundingClientRect();
    return bb.left - parentBB.left;
  });
};

const groupsPos = await getCirclePos(groupsToggle);
const schedPos = await getCirclePos(schedulesToggle);
const sharePos = await getCirclePos(shareLinksToggle);

console.log('=== FINAL TOGGLE STATES ===');
console.log('Group Settings:', groupsPos > 20 ? 'ON ✓' : 'OFF');
console.log('Schedules:', schedPos > 20 ? 'ON ✓' : 'OFF');
console.log('Share Links:', sharePos > 20 ? 'ON ✓' : 'OFF');

// Now test Share Links button visibility in RSS Preview dialog
// First, close the Feature Flags dialog by clicking outside or close button
const closeBtn = page.locator('.close-btn');
if (await closeBtn.count() > 0) {
  await closeBtn.click();
  await page.waitForTimeout(500);
}

// Navigate to a feed source to open RSS Preview
await page.goto('http://localhost:8080/sources');
await page.waitForLoadState('networkidle');
await page.waitForTimeout(500);

// Look for any feed item to click on
const feedItems = page.locator('[class*="feed-item"], [class*="rss-item"], [class*="article"]');
const itemCount = await feedItems.count();
console.log('\n=== FEED ITEMS FOUND:', itemCount, '===');

if (itemCount > 0) {
  await feedItems.first().click();
  await page.waitForTimeout(1000);
  
  // Look for Share Links button in preview dialog
  const shareLinksBtn = page.locator('text=Share Links, button:has-text("Share Links")');
  const shareBtnCount = await shareLinksBtn.count();
  console.log('Share Links button count in preview:', shareBtnCount);
  
  if (shareBtnCount > 0) {
    console.log('✓ Share Links button IS VISIBLE when feature is ON');
    await page.screenshot({ path: '/tmp/share-links-visible.png' });
    
    // Now go back and turn Share Links OFF
    await page.goto('http://localhost:8080/settings');
    await page.waitForLoadState('networkidle');
    
    // Open Feature Flags dialog
    for (let i = 0; i < 10; i++) {
      await headerSvg.click({ timeout: 500 });
      await page.waitForTimeout(100);
    }
    await page.waitForTimeout(500);
    
    // Turn Share Links OFF
    const shareToggle = page.locator('.toggle-shareLinks');
    await shareToggle.click();
    await page.waitForTimeout(300);
    
    // Close dialog
    const closeBtn2 = page.locator('.close-btn');
    if (await closeBtn2.count() > 0) {
      await closeBtn2.click();
      await page.waitForTimeout(500);
    }
    
    // Go back to sources
    await page.goto('http://localhost:8080/sources');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(500);
    
    // Click a feed item again
    const feedItems2 = page.locator('[class*="feed-item"], [class*="rss-item"], [class*="article"]');
    if (await feedItems2.count() > 0) {
      await feedItems2.first().click();
      await page.waitForTimeout(1000);
    }
    
    // Check for Share Links button again
    const shareLinksBtn2 = page.locator('text=Share Links, button:has-text("Share Links")');
    const shareBtnCount2 = await shareLinksBtn2.count();
    console.log('Share Links button count after turning feature OFF:', shareBtnCount2);
    console.log(shareBtnCount2 === 0 ? '✓ Share Links button HIDDEN when feature is OFF' : '✗ Share Links button STILL VISIBLE (BUG)');
    
    await page.screenshot({ path: '/tmp/share-links-hidden.png' });
  } else {
    console.log('✗ Share Links button NOT FOUND in preview dialog');
    await page.screenshot({ path: '/tmp/no-share-links-btn.png' });
  }
} else {
  console.log('No feed items found to test Share Links');
  // Try finding any clickable element
  await page.screenshot({ path: '/tmp/sources-page.png' });
}

await browser.close();
console.log('\nDone');
