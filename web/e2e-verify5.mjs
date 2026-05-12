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

// Find and click Share Links toggle
const shareLinksToggle = page.locator('.toggle-shareLinks');
const shareLinksBB = await shareLinksToggle.boundingBox();
console.log('Share Links toggle position:', shareLinksBB);

// Get toggle background color (ON = green/blue, OFF = gray)
const toggleBg = await shareLinksToggle.evaluate(el => {
  const bg = getComputedStyle(el).backgroundColor;
  return bg;
});
console.log('Share Links toggle bg color:', toggleBg);

// Check if Share Links is currently ON or OFF based on position
// The toggle has a circle that moves - if on right, it's ON
const circlePos = await shareLinksToggle.locator('span').first().evaluate(el => {
  const bb = el.getBoundingClientRect();
  const parentBB = el.parentElement.getBoundingClientRect();
  const relativeLeft = bb.left - parentBB.left;
  return relativeLeft;
});
console.log('Share Links toggle circle relative position:', circlePos);
console.log('Share Links is currently:', circlePos > 20 ? 'ON' : 'OFF');

// Now let's find the Schedule Updates toggle and check if it's disabled
const schedulesToggle = page.locator('.toggle-schedules');
const schedDisabled = await schedulesToggle.getAttribute('disabled');
console.log('\nSchedules toggle disabled attr:', schedDisabled);

// Get schedules toggle styling
const schedClasses = await schedulesToggle.getAttribute('class');
console.log('Schedules toggle classes:', schedClasses);

// Check Group Settings toggle state
const groupsToggle = page.locator('.toggle-groups');
const groupsCirclePos = await groupsToggle.locator('span').first().evaluate(el => {
  const bb = el.getBoundingClientRect();
  const parentBB = el.parentElement.getBoundingClientRect();
  return bb.left - parentBB.left;
});
console.log('\nGroup Settings toggle circle position:', groupsCirclePos);
console.log('Group Settings is currently:', groupsCirclePos > 20 ? 'ON' : 'OFF');

console.log('\n=== VERIFICATION SUMMARY ===');
console.log('Share Links:', circlePos > 20 ? 'ON ✓' : 'OFF');
console.log('Group Settings:', groupsCirclePos > 20 ? 'ON ✓' : 'OFF');
console.log('Schedules toggle disabled:', schedDisabled !== null && schedDisabled !== 'false' ? 'YES (disabled)' : 'NO (enabled)');

await page.screenshot({ path: '/tmp/dialog-state.png' });
console.log('\nScreenshot saved to /tmp/dialog-state.png');

await browser.close();
console.log('Done');
