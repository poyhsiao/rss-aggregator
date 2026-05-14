import { test, expect } from '@playwright/test'

test.describe('Feed Format Path Routes API', () => {
  const baseUrl = '/api/v1'

  test('GET /feed/rss returns XML content', async ({ request }) => {
    const response = await request.get(`${baseUrl}/feed/rss`)
    expect(response.status()).toBe(200)
    expect(response.headers()['content-type']).toContain('application/xml')
    const text = await response.text()
    expect(text).toContain('<?xml')
    expect(text).toContain('<rss')
  })

  test('GET /feed/json returns JSON content', async ({ request }) => {
    const response = await request.get(`${baseUrl}/feed/json`)
    expect(response.status()).toBe(200)
    expect(response.headers()['content-type']).toContain('application/json')
  })

  test('GET /feed/markdown returns Markdown content', async ({ request }) => {
    const response = await request.get(`${baseUrl}/feed/markdown`)
    expect(response.status()).toBe(200)
    expect(response.headers()['content-type']).toContain('text/markdown')
  })

  test('GET /feed/{invalid} returns 422 for invalid format', async ({ request }) => {
    const response = await request.get(`${baseUrl}/feed/invalid`)
    expect(response.status()).toBe(422)
  })

  test('GET /sources/{id}/rss returns RSS for source', async ({ request }) => {
    // First create a source, then get its feed
    const listResponse = await request.get(`${baseUrl}/sources`)
    if (listResponse.status() === 200) {
      const sources = await listResponse.json()
      if (sources.length > 0) {
        const sourceId = sources[0].id
        const response = await request.get(`${baseUrl}/sources/${sourceId}/rss`)
        expect(response.status()).toBe(200)
        expect(response.headers()['content-type']).toContain('application/xml')
      }
    }
  })

  test('GET /sources/{id}/json returns JSON for source', async ({ request }) => {
    const listResponse = await request.get(`${baseUrl}/sources`)
    if (listResponse.status() === 200) {
      const sources = await listResponse.json()
      if (sources.length > 0) {
        const sourceId = sources[0].id
        const response = await request.get(`${baseUrl}/sources/${sourceId}/json`)
        expect(response.status()).toBe(200)
        expect(response.headers()['content-type']).toContain('application/json')
      }
    }
  })

  test('GET /sources/{id}/markdown returns Markdown for source', async ({ request }) => {
    const listResponse = await request.get(`${baseUrl}/sources`)
    if (listResponse.status() === 200) {
      const sources = await listResponse.json()
      if (sources.length > 0) {
        const sourceId = sources[0].id
        const response = await request.get(`${baseUrl}/sources/${sourceId}/markdown`)
        expect(response.status()).toBe(200)
        expect(response.headers()['content-type']).toContain('text/markdown')
      }
    }
  })

  test('GET /sources/{id}/{invalid} returns 422 for invalid format', async ({ request }) => {
    const listResponse = await request.get(`${baseUrl}/sources`)
    if (listResponse.status() === 200) {
      const sources = await listResponse.json()
      if (sources.length > 0) {
        const sourceId = sources[0].id
        const response = await request.get(`${baseUrl}/sources/${sourceId}/invalid`)
        expect(response.status()).toBe(422)
      }
    }
  })

  test('GET /groups/{id}/rss returns RSS for group', async ({ request }) => {
    const listResponse = await request.get(`${baseUrl}/source-groups`)
    if (listResponse.status() === 200) {
      const groups = await listResponse.json()
      if (groups.length > 0) {
        const groupId = groups[0].id
        const response = await request.get(`${baseUrl}/groups/${groupId}/rss`)
        expect(response.status()).toBe(200)
        expect(response.headers()['content-type']).toContain('application/xml')
      }
    }
  })

  test('GET /groups/{id}/json returns JSON for group', async ({ request }) => {
    const listResponse = await request.get(`${baseUrl}/source-groups`)
    if (listResponse.status() === 200) {
      const groups = await listResponse.json()
      if (groups.length > 0) {
        const groupId = groups[0].id
        const response = await request.get(`${baseUrl}/groups/${groupId}/json`)
        expect(response.status()).toBe(200)
        expect(response.headers()['content-type']).toContain('application/json')
      }
    }
  })

  test('GET /groups/{id}/markdown returns Markdown for group', async ({ request }) => {
    const listResponse = await request.get(`${baseUrl}/source-groups`)
    if (listResponse.status() === 200) {
      const groups = await listResponse.json()
      if (groups.length > 0) {
        const groupId = groups[0].id
        const response = await request.get(`${baseUrl}/groups/${groupId}/markdown`)
        expect(response.status()).toBe(200)
        expect(response.headers()['content-type']).toContain('text/markdown')
      }
    }
  })

  test('GET /groups/{id}/{invalid} returns 422 for invalid format', async ({ request }) => {
    const listResponse = await request.get(`${baseUrl}/source-groups`)
    if (listResponse.status() === 200) {
      const groups = await listResponse.json()
      if (groups.length > 0) {
        const groupId = groups[0].id
        const response = await request.get(`${baseUrl}/groups/${groupId}/invalid`)
        expect(response.status()).toBe(422)
      }
    }
  })

  test('query params work with path-based format', async ({ request }) => {
    const response = await request.get(`${baseUrl}/feed/json`, {
      params: { sort_by: 'source', sort_order: 'asc' },
    })
    expect(response.status()).toBe(200)
    expect(response.headers()['content-type']).toContain('application/json')
  })
})