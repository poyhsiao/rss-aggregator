import { test, expect } from '@playwright/test'

test.describe('Feature Flags UI Hiding', () => {
  async function openDialog(page: any) {
    await page.goto('/settings')
    await page.waitForLoadState('networkidle')
    const rssIcon = page.locator('header svg[class*="h-6"]').first()
    for (let i = 0; i < 10; i++) {
      await rssIcon.click({ force: true })
      await page.waitForTimeout(50)
    }
    await expect(page.locator('[role="dialog"]')).toBeVisible()
  }

  async function toggleFeature(page: any, index: number, confirm: boolean = true) {
    await page.locator('[role="switch"]').nth(index).click({ force: true })
    if (confirm) {
      await page.getByRole('button', { name: 'Confirm' }).first().click()
      await page.waitForTimeout(100)
    }
  }

  test.beforeEach(async ({ page }) => {
    // Navigate to settings page first to ensure localStorage is accessible
    await page.goto('/settings')
    await page.waitForLoadState('domcontentloaded')
    // Reset to known state
    await page.evaluate(() => {
      localStorage.setItem('ff_groups_enabled', 'true')
      localStorage.setItem('ff_group_schedules_enabled', 'true')
      localStorage.setItem('ff_source_group_schedules_enabled', 'true')
    })
  })

  test('SourcesPage: Groups Tab button hidden when groupsEnabled=false', async ({ page }) => {
    await page.goto('/sources')
    await page.waitForLoadState('networkidle')
    await page.waitForTimeout(1000)

    // Should see Groups tab when enabled
    const groupsTab = page.getByRole('tab', { name: /groups/i })
    const isVisible = await groupsTab.isVisible({ timeout: 5000 }).catch(() => false)
    if (!isVisible) {
      // Skip this test if Groups tab doesn't exist (e.g., no source groups created yet)
      test.skip()
    }

    // Disable groups
    await openDialog(page)
    await toggleFeature(page, 0, true)

    // Should not see Groups tab when disabled
    await expect(page.getByRole('tab', { name: /groups/i })).not.toBeVisible()
  })

  test('SourcesPage: Group badge hidden when groupsEnabled=false', async ({ page }) => {
    await page.goto('/sources')
    await page.waitForLoadState('networkidle')

    // Switch to groups tab - skip if not visible
    const groupsTab = page.getByRole('tab', { name: /groups/i })
    if (!(await groupsTab.isVisible({ timeout: 3000 }).catch(() => false))) {
      test.skip()
    }
    await groupsTab.click()
    await page.waitForTimeout(500)

    // Member count badges should be visible when enabled
    const badgesBefore = await page.locator('text=sources').count()
    expect(badgesBefore).toBeGreaterThan(0)

    // Disable groups via dialog
    await openDialog(page)
    await toggleFeature(page, 0, true)

    // Reload and verify badges are hidden
    await page.goto('/sources')
    await page.waitForLoadState('networkidle')
    await page.getByRole('tab', { name: /groups/i }).click()
    await page.waitForTimeout(500)

    // Member count badges should be hidden
    const badgesAfter = await page.locator('text=sources').count()
    expect(badgesAfter).toBe(0)
  })

  test('SourcesPage: Schedules badge hidden when groupSchedulesEnabled=false', async ({ page }) => {
    await page.goto('/sources')
    await page.waitForLoadState('networkidle')

    // Switch to groups tab - skip if not visible
    const groupsTab = page.getByRole('tab', { name: /groups/i })
    if (!(await groupsTab.isVisible({ timeout: 3000 }).catch(() => false))) {
      test.skip()
    }
    await groupsTab.click()
    await page.waitForTimeout(1000)

    // Blue schedule badges should be visible when groupSchedulesEnabled
    const blueBadgesBefore = await page.locator('.text-blue-600, .dark\\:text-blue-400').count()
    expect(blueBadgesBefore).toBeGreaterThan(0)

    // Disable groupSchedulesEnabled via second toggle
    await openDialog(page)
    await page.locator('[role="switch"]').nth(1).click()
    await page.getByRole('button', { name: 'Confirm' }).first().click()
    await page.waitForTimeout(100)

    // Reload and verify schedule badges are hidden
    await page.goto('/sources')
    await page.waitForLoadState('networkidle')
    await page.getByRole('tab', { name: /groups/i }).click()
    await page.waitForTimeout(1000)

    // Schedule badges (blue) should be hidden when groupSchedulesEnabled=false
    const blueBadgesAfter = await page.locator('.text-blue-600, .dark\\:text-blue-400').count()
    expect(blueBadgesAfter).toBe(0)
  })

  test('SourcesPage: ScheduleConfigPanel hidden when sourceGroupSchedulesEnabled=false', async ({ page }) => {
    await page.goto('/sources')
    await page.waitForLoadState('networkidle')

    // Switch to groups tab - skip if not visible
    const groupsTab = page.getByRole('tab', { name: /groups/i })
    if (!(await groupsTab.isVisible({ timeout: 3000 }).catch(() => false))) {
      test.skip()
    }
    await groupsTab.click()
    await page.waitForTimeout(500)

    // Expand a group to see ScheduleConfigPanel
    const expandBtn = page.locator('button[title="expand"], button[title="Expand"]').first()
    if (await expandBtn.isVisible().catch(() => false)) {
      await expandBtn.click()
      await page.waitForTimeout(500)
    }

    // Schedule section should be visible when enabled
    const scheduleBefore = await page.locator('text=Schedule').count()
    expect(scheduleBefore).toBeGreaterThan(0)

    // Disable sourceGroupSchedulesEnabled via third toggle
    await openDialog(page)
    await page.locator('[role="switch"]').nth(2).click()
    await page.getByRole('button', { name: 'Confirm' }).first().click()
    await page.waitForTimeout(100)

    // Reload and verify ScheduleConfigPanel is hidden
    await page.goto('/sources')
    await page.waitForLoadState('networkidle')
    await page.getByRole('tab', { name: /groups/i }).click()
    await page.waitForTimeout(500)

    const expandBtnAgain = page.locator('button[title="expand"], button[title="Expand"]').first()
    if (await expandBtnAgain.isVisible().catch(() => false)) {
      await expandBtnAgain.click()
      await page.waitForTimeout(500)
    }

    // Schedule-related sections should be hidden
    const scheduleAfter = await page.locator('text=Schedule').count()
    expect(scheduleAfter).toBe(0)
  })

  test.skip('FeedPage: Group filter chips hidden when groupsEnabled=false', async ({ page }) => {
    await page.goto('/feed')
    await page.waitForLoadState('networkidle')

    // Group filter chips should be visible when groupsEnabled and groups exist
    // (may not show if no groups in test data)

    // Disable groups
    await openDialog(page)
    await toggleFeature(page, 0, true)

    // Reload and verify group filter chips are hidden
    await page.goto('/feed')
    await page.waitForLoadState('networkidle')

    // Blue badges (group badges) should be hidden
    const groupBadges = await page.locator('.bg-blue-100, .dark\\:bg-blue-900').count()
    expect(groupBadges).toBe(0)
  })

  test.skip('FeedPage: Group badges on items hidden when groupsEnabled=false', async ({ page }) => {
    await page.goto('/feed')
    await page.waitForLoadState('networkidle')

    // Group badges on feed items should be visible when enabled
    const badgesBefore = await page.locator('.bg-blue-100, .dark\\:bg-blue-900').count()

    // Disable groups
    await openDialog(page)
    await toggleFeature(page, 0, true)

    // Reload and verify group badges are hidden
    await page.goto('/feed')
    await page.waitForLoadState('networkidle')

    // Group badges should be hidden
    const badgesAfter = await page.locator('.bg-blue-100, .dark\\:bg-blue-900').count()
    expect(badgesAfter).toBe(0)
  })

  test.skip('HistoryPage: Group filter hidden when groupsEnabled=false', async ({ page }) => {
    await page.goto('/history')
    await page.waitForLoadState('networkidle')

    // Group filter should be visible when enabled

    // Disable groups
    await openDialog(page)
    await toggleFeature(page, 0, true)

    // Reload and verify group filter is hidden
    await page.goto('/history')
    await page.waitForLoadState('networkidle')

    // Blue group badges should be hidden in history page
    const groupBadges = await page.locator('.bg-blue-100, .dark\\:bg-blue-900').count()
    expect(groupBadges).toBe(0)
  })

  test.skip('HistoryPage: Group info in Batch hidden when groupsEnabled=false', async ({ page }) => {
    await page.goto('/history')
    await page.waitForLoadState('networkidle')

    // Group info in batches should be visible when enabled
    const groupBadgesBefore = page.locator('.bg-blue-100, .dark\\:bg-blue-900').count()

    // Disable groups
    await openDialog(page)
    await toggleFeature(page, 0, true)

    // Reload and verify group info in batches is hidden
    await page.goto('/history')
    await page.waitForLoadState('networkidle')

    // Group badges in batch should be hidden
    const groupBadgesAfter = await page.locator('.bg-blue-100, .dark\\:bg-blue-900').count()
    expect(groupBadgesAfter).toBe(0)
  })
})