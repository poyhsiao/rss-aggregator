import { chromium } from '@playwright/test';

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage();

await page.goto('http://localhost:8080/settings');
await page.waitForLoadState('networkidle');

// Click RSS icon 10 times to open dialog
const headerSvg = page.locator('header svg').first();
for (let i = 0; i < 10; i++) {
  await headerSvg.click({ timeout: 500 });
  await page.waitForTimeout(100);
}
await page.waitForTimeout(500);

// === TEST 1: Enable Group Settings ===
console.log('=== TEST 1: Enable Group Settings ===');
const groupsToggle = page.locator('.toggle-groups');
await groupsToggle.click();
await page.waitForTimeout(500);

// Check if Schedules toggle became enabled
const schedulesToggle = page.locator('.toggle-schedules');
const schedDisabled = await schedulesToggle.getAttribute('disabled');
const schedClasses = await schedulesToggle.getAttribute('class');
console.log('Schedules disabled after Groups ON:', schedDisabled);
console.log('Schedules classes after Groups ON:', schedClasses?.includes('opacity-50') ? 'STILL has opacity-50 (BAD)' : 'NO opacity-50 (GOOD)');

// Get schedules circle position
const schedCirclePos = await schedulesToggle.locator('span').first().evaluate(el => {
  const bb = el.getBoundingClientRect();
  const parentBB = el.parentElement.getBoundingClientRect();
  return bb.left - parentBB.left;
});
console.log('Schedules toggle circle position:', schedCirclePos);
console.log('Schedules is now:', schedDisabled === null || schedDisabled === 'false' ? 'ENABLED ✓' : 'STILL DISABLED ✗');

// === TEST 2: Enable Schedules ===
console.log('\n=== TEST 2: Enable Schedules ===');
await schedulesToggle.click();
await page.waitForTimeout(500);
const schedCirclePosAfter = await schedulesToggle.locator('span').first().evaluate(el => {
  const bb = el.getBoundingClientRect();
  const parentBB = el.parentElement.getBoundingBox();
  return bb.left - parentBB.left;
});
console.log('Schedules circle position after click:', schedCirclePosAfter);
console.log('Schedules is now:', schedCirclePosAfter > 20 ? 'ON ✓' : 'OFF');

// === TEST 3: Enable Share Links ===
console.log('\n=== TEST 3: Enable Share Links ===');
const shareLinksToggle = page.locator('.toggle-shareLinks');
await shareLinksToggle.click();
await page.waitForTimeout(500);
const shareLinksCirclePos = await shareLinksToggle.locator('span').first().evaluate(el => {
  const bb = el.getBoundingClientRect();
  const parentBB = el.parentElement.getBoundingClientRect();
  return bb.left - parentBB.left;
});
console.log('Share Links circle position:', shareLinksCirclePos);
console.log('Share Links is now:', shareLinksCirclePos > 20 ? 'ON ✓' : 'OFF');

// Take screenshot of final dialog state
await page.screenshot({ path: '/tmp/dialog-all-on.png', fullPage: false });
console.log('\nScreenshot saved: /tmp/dialog-all-on.png');

await browser.close();
console.log('\nDone');
