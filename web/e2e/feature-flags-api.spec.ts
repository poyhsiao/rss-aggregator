import { test, expect } from '@playwright/test'

test.describe('Feature Flags API', () => {
  test('GET /api/v1/feature-flags returns all flags', async ({ page }) => {
    const response = await page.request.get('/api/v1/feature-flags', {
      headers: { 'X-API-Key': 'test-api-key' }
    })
    expect(response.ok()).toBeTruthy()
    const data = await response.json()
    expect(data).toHaveProperty('groups_enabled')
    expect(data).toHaveProperty('group_schedules_enabled')
    expect(data).toHaveProperty('source_group_schedules_enabled')
    expect(typeof data.groups_enabled).toBe('boolean')
  })

  test('PUT /api/v1/feature-flags updates flags', async ({ page }) => {
    const response = await page.request.put('/api/v1/feature-flags', {
      headers: { 'X-API-Key': 'test-api-key' },
      data: { groups_enabled: false }
    })
    expect(response.ok()).toBeTruthy()
    const data = await response.json()
    expect(data.groups_enabled).toBe(false)
  })

  test('PUT /api/v1/feature-flags batch update', async ({ page }) => {
    const response = await page.request.put('/api/v1/feature-flags', {
      headers: { 'X-API-Key': 'test-api-key' },
      data: {
        groups_enabled: false,
        group_schedules_enabled: false,
      }
    })
    expect(response.ok()).toBeTruthy()
    const data = await response.json()
    expect(data.groups_enabled).toBe(false)
    expect(data.group_schedules_enabled).toBe(false)
  })
})