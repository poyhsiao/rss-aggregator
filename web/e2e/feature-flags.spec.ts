import { test, expect } from '@playwright/test'

test.describe('Feature Flags', () => {
  test.beforeEach(async ({ page }) => {
    await page.evaluate(() => {
      localStorage.removeItem('ff_groups_enabled')
      localStorage.removeItem('ff_group_schedules_enabled')
    })
    await page.goto('/settings')
  })

  test('trigger dialog by clicking Settings RSS icon 10 times', async ({ page }) => {
    const rssIcon = page.locator('header').locator('svg.h-6.w-6').first()
    for (let i = 0; i < 10; i++) {
      await rssIcon.click()
      await page.waitForTimeout(50)
    }
    await expect(page.locator('text=🔧')).toBeVisible()
  })

  test('cascade cancel — Groups stays ON when Cancel clicked', async ({ page }) => {
    const rssIcon = page.locator('header').locator('svg.h-6.w-6').first()
    for (let i = 0; i < 10; i++) {
      await rssIcon.click()
      await page.waitForTimeout(50)
    }

    // Turn OFF Groups toggle (first toggle button)
    const groupsToggle = page.locator('button.relative.inline-flex.h-6').first()
    await groupsToggle.click()

    // Warning should appear
    await expect(page.locator('text=停用群組功能也將停用排程更新')).toBeVisible()

    // Click Cancel
    await page.locator('button:has-text("取消")').click()

    // Warning should hide, Groups should stay ON
    await expect(page.locator('text=停用群組功能也將停用排程更新')).not.toBeVisible()
  })

  test('cascade confirm — Groups OFF and Schedules auto-disabled', async ({ page }) => {
    const rssIcon = page.locator('header').locator('svg.h-6.w-6').first()
    for (let i = 0; i < 10; i++) {
      await rssIcon.click()
      await page.waitForTimeout(50)
    }

    // Turn OFF Groups toggle
    const groupsToggle = page.locator('button.relative.inline-flex.h-6').first()
    await groupsToggle.click()

    // Click Confirm on warning (first confirm button)
    await page.locator('button:has-text("確認")').first().click()

    // Dialog should close
    await expect(page.locator('text=🔧')).not.toBeVisible()

    // Verify localStorage
    const stored = await page.evaluate(() => ({
      groups: localStorage.getItem('ff_groups_enabled'),
      schedules: localStorage.getItem('ff_group_schedules_enabled')
    }))
    expect(stored.groups).toBe('false')
    expect(stored.schedules).toBe('false')
  })

  test('visibility — Groups tab hidden when groups_enabled is OFF', async ({ page }) => {
    await page.evaluate(() => {
      localStorage.setItem('ff_groups_enabled', 'false')
      localStorage.setItem('ff_group_schedules_enabled', 'false')
    })
    await page.goto('/sources')

    // Groups tab should not be visible
    const groupsTab = page.locator('button', { hasText: 'groups' }).or(page.locator('button', { hasText: '群組' }))
    await expect(groupsTab).not.toBeVisible()
  })

  test('persistence — changes survive page reload', async ({ page }) => {
    const rssIcon = page.locator('header').locator('svg.h-6.w-6').first()
    for (let i = 0; i < 10; i++) {
      await rssIcon.click()
      await page.waitForTimeout(50)
    }

    // Turn OFF Groups
    await page.locator('button.relative.inline-flex.h-6').first().click()
    await page.locator('button:has-text("確認")').first().click()

    // Reload
    await page.reload()
    await page.goto('/sources')

    // Groups tab should still be hidden
    const groupsTab = page.locator('button', { hasText: 'groups' }).or(page.locator('button', { hasText: '群組' }))
    await expect(groupsTab).not.toBeVisible()
  })
})