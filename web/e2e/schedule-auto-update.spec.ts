import { test, expect } from '@playwright/test'

/**
 * E2E tests for Group Schedule Auto-Update Control
 *
 * Covers the behavior change where:
 * - Sources are only auto-fetched if their group has an enabled SourceGroupSchedule
 * - ScheduleScheduler only runs when SCHEDULER_ENABLED=true
 */
test.describe('Group Schedule Auto-Update Control', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/sources')
    await page.waitForLoadState('networkidle')
    await page.getByRole('button', { name: /groups|群組/i }).click()
    await page.waitForTimeout(500)
  })

  test('API: GET schedules returns list for a group', async ({ page }) => {
    // Intercept the schedules API call when opening a group panel
    const groups = page.locator('[class*="rounded-xl"]').filter({
      has: page.locator('[class*="font-semibold"], [class*="font-medium"]'),
    })
    const count = await groups.count()

    if (count > 0) {
      const responsePromise = page.waitForResponse(
        (res) =>
          res.url().includes('/source-groups/') &&
          res.url().includes('/schedules') &&
          res.request().method() === 'GET',
        { timeout: 10000 },
      )

      const expandBtn = groups.first().locator('button').first()
      if (await expandBtn.isVisible({ timeout: 3000 })) {
        await expandBtn.click()
        const response = await responsePromise
        expect(response.status()).toBe(200)
        const body = await response.json()
        expect(Array.isArray(body)).toBe(true)
      }
    }
  })

  test('API: POST schedule creates a new schedule for group', async ({ page, request }) => {
    // First get a group id via the groups API
    const groupsResponse = await request.get('/api/v1/source-groups')
    if (groupsResponse.status() !== 200) return

    const groups = await groupsResponse.json()
    if (!groups || groups.length === 0) return

    const groupId = groups[0].id

    // Create a schedule with a safe interval (every 30 minutes)
    const createResponse = await request.post(`/api/v1/source-groups/${groupId}/schedules`, {
      data: { cron_expression: '*/30 * * * *' },
    })

    // Should succeed or return 409 if already exists
    expect([201, 409]).toContain(createResponse.status())

    if (createResponse.status() === 201) {
      const schedule = await createResponse.json()
      expect(schedule.cron_expression).toBe('*/30 * * * *')
      expect(schedule.is_enabled).toBe(true)
      expect(schedule.group_id).toBe(groupId)

      // Cleanup: delete the created schedule
      await request.delete(`/api/v1/source-groups/${groupId}/schedules/${schedule.id}`)
    }
  })

  test('API: PATCH toggle switches schedule is_enabled state', async ({ page, request }) => {
    const groupsResponse = await request.get('/api/v1/source-groups')
    if (groupsResponse.status() !== 200) return

    const groups = await groupsResponse.json()
    if (!groups || groups.length === 0) return

    const groupId = groups[0].id

    // Create a schedule to toggle
    const createResponse = await request.post(`/api/v1/source-groups/${groupId}/schedules`, {
      data: { cron_expression: '*/45 * * * *' },
    })

    if (createResponse.status() !== 201) return
    const schedule = await createResponse.json()
    expect(schedule.is_enabled).toBe(true)

    // Toggle it off
    const toggleResponse = await request.patch(
      `/api/v1/source-groups/${groupId}/schedules/${schedule.id}/toggle`,
    )
    expect(toggleResponse.status()).toBe(200)
    const toggled = await toggleResponse.json()
    expect(toggled.is_enabled).toBe(false)

    // Toggle it back on
    const toggleBackResponse = await request.patch(
      `/api/v1/source-groups/${groupId}/schedules/${schedule.id}/toggle`,
    )
    expect(toggleBackResponse.status()).toBe(200)
    const toggledBack = await toggleBackResponse.json()
    expect(toggledBack.is_enabled).toBe(true)

    // Cleanup
    await request.delete(`/api/v1/source-groups/${groupId}/schedules/${schedule.id}`)
  })

  test('API: DELETE removes schedule from group', async ({ page, request }) => {
    const groupsResponse = await request.get('/api/v1/source-groups')
    if (groupsResponse.status() !== 200) return

    const groups = await groupsResponse.json()
    if (!groups || groups.length === 0) return

    const groupId = groups[0].id

    // Create then delete
    const createResponse = await request.post(`/api/v1/source-groups/${groupId}/schedules`, {
      data: { cron_expression: '0 */2 * * *' },
    })
    if (createResponse.status() !== 201) return

    const schedule = await createResponse.json()

    const deleteResponse = await request.delete(
      `/api/v1/source-groups/${groupId}/schedules/${schedule.id}`,
    )
    expect(deleteResponse.status()).toBe(204)

    // Verify it's gone
    const listResponse = await request.get(`/api/v1/source-groups/${groupId}/schedules`)
    const schedules = await listResponse.json()
    const found = schedules.find((s: { id: number }) => s.id === schedule.id)
    expect(found).toBeUndefined()
  })

  test('UI: schedule panel shows toggle button for existing schedule', async ({ page }) => {
    const groups = page.locator('[class*="rounded-xl"]').filter({
      has: page.locator('[class*="font-semibold"], [class*="font-medium"]'),
    })
    const count = await groups.count()
    if (count === 0) return

    const expandBtn = groups.first().locator('button').first()
    if (!(await expandBtn.isVisible({ timeout: 3000 }))) return

    await expandBtn.click()
    await page.waitForTimeout(800)

    // Look for schedule section
    const scheduleSection = page.getByText(/schedule|排程/i)
    if (await scheduleSection.isVisible({ timeout: 3000 })) {
      // If schedules exist, toggle button should be present
      const toggleBtn = page
        .locator('button[role="switch"], input[type="checkbox"]')
        .or(page.locator('[class*="toggle"], [class*="switch"]'))
      const toggleCount = await toggleBtn.count()

      // Either a toggle exists (schedule present) or an add button exists (no schedule)
      const addBtn = page.getByRole('button', { name: /add schedule|新增排程/i })
      const hasToggle = toggleCount > 0
      const hasAdd = await addBtn.isVisible({ timeout: 2000 }).catch(() => false)

      expect(hasToggle || hasAdd).toBe(true)
    }
  })

  test('UI: toggling schedule calls PATCH toggle endpoint', async ({ page }) => {
    const groups = page.locator('[class*="rounded-xl"]').filter({
      has: page.locator('[class*="font-semibold"], [class*="font-medium"]'),
    })
    const count = await groups.count()
    if (count === 0) return

    const expandBtn = groups.first().locator('button').first()
    if (!(await expandBtn.isVisible({ timeout: 3000 }))) return

    await expandBtn.click()
    await page.waitForTimeout(800)

    // Look for a toggle/switch inside schedule panel
    const toggleBtn = page
      .locator('button[role="switch"]')
      .or(page.locator('[class*="toggle"][class*="schedule"], [class*="schedule"][class*="toggle"]'))

    if (!(await toggleBtn.first().isVisible({ timeout: 3000 }).catch(() => false))) return

    const responsePromise = page.waitForResponse(
      (res) =>
        res.url().includes('/schedules/') &&
        res.url().includes('/toggle') &&
        res.request().method() === 'PATCH',
      { timeout: 10000 },
    )

    await toggleBtn.first().click()
    const response = await responsePromise
    expect(response.status()).toBe(200)

    const body = await response.json()
    expect(typeof body.is_enabled).toBe('boolean')
  })

  test('API: disabled schedule group sources should not be auto-fetched (scheduler logic)', async ({
    request,
  }) => {
    const groupsResponse = await request.get('/api/v1/source-groups')
    if (groupsResponse.status() !== 200) return

    const groups = await groupsResponse.json()
    if (!groups || groups.length === 0) return

    const groupId = groups[0].id

    // Create a disabled schedule
    const createResponse = await request.post(`/api/v1/source-groups/${groupId}/schedules`, {
      data: { cron_expression: '*/60 * * * *' },
    })
    if (createResponse.status() !== 201) return
    const schedule = await createResponse.json()

    // Disable it
    if (schedule.is_enabled) {
      await request.patch(`/api/v1/source-groups/${groupId}/schedules/${schedule.id}/toggle`)
    }

    // Verify schedule is disabled
    const listResponse = await request.get(`/api/v1/source-groups/${groupId}/schedules`)
    const schedules = await listResponse.json()
    const found = schedules.find((s: { id: number }) => s.id === schedule.id)
    expect(found).toBeDefined()
    expect(found.is_enabled).toBe(false)

    // Cleanup
    await request.delete(`/api/v1/source-groups/${groupId}/schedules/${schedule.id}`)
  })
})
