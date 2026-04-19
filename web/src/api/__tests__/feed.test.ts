import { describe, it, expect, beforeEach, vi } from 'vitest'
import { buildFeedPathUrl } from '../feed'

// Mock environment utils
vi.mock('@/utils/environment', () => ({
  isTauri: vi.fn(),
}))

import { isTauri } from '@/utils/environment'

describe('buildFeedPathUrl', () => {
  beforeEach(() => {
    vi.resetAllMocks()
    // Reset window global
    delete (window as any).__VITE_API_BASE_URL__
  })

  describe('global feed', () => {
    it('should build global feed URL with rss format', () => {
      vi.mocked(isTauri).mockReturnValue(false)
      const url = buildFeedPathUrl('rss')
      expect(url).toBe('/api/v1/feed/rss')
    })

    it('should build global feed URL with json format', () => {
      vi.mocked(isTauri).mockReturnValue(false)
      const url = buildFeedPathUrl('json')
      expect(url).toBe('/api/v1/feed/json')
    })

    it('should build global feed URL with markdown format', () => {
      vi.mocked(isTauri).mockReturnValue(false)
      const url = buildFeedPathUrl('markdown')
      expect(url).toBe('/api/v1/feed/markdown')
    })

    it('should include non-default sort_by parameter', () => {
      vi.mocked(isTauri).mockReturnValue(false)
      const url = buildFeedPathUrl('rss', { sort_by: 'source' })
      expect(url).toBe('/api/v1/feed/rss?sort_by=source')
    })

    it('should include non-default sort_order parameter', () => {
      vi.mocked(isTauri).mockReturnValue(false)
      const url = buildFeedPathUrl('rss', { sort_order: 'asc' })
      expect(url).toBe('/api/v1/feed/rss?sort_order=asc')
    })

    it('should include valid_time parameter', () => {
      vi.mocked(isTauri).mockReturnValue(false)
      const url = buildFeedPathUrl('rss', { valid_time: 24 })
      expect(url).toBe('/api/v1/feed/rss?valid_time=24')
    })

    it('should include keywords parameter', () => {
      vi.mocked(isTauri).mockReturnValue(false)
      const url = buildFeedPathUrl('rss', { keywords: 'python,ai' })
      expect(url).toBe('/api/v1/feed/rss?keywords=python%2Cai')
    })

    it('should exclude default sort_by parameter', () => {
      vi.mocked(isTauri).mockReturnValue(false)
      const url = buildFeedPathUrl('rss', { sort_by: 'published_at' })
      expect(url).toBe('/api/v1/feed/rss')
    })

    it('should exclude default sort_order parameter', () => {
      vi.mocked(isTauri).mockReturnValue(false)
      const url = buildFeedPathUrl('rss', { sort_order: 'desc' })
      expect(url).toBe('/api/v1/feed/rss')
    })

    it('should include multiple non-default params', () => {
      vi.mocked(isTauri).mockReturnValue(false)
      const url = buildFeedPathUrl('json', {
        sort_by: 'source',
        sort_order: 'asc',
        valid_time: 48,
      })
      expect(url).toBe(
        '/api/v1/feed/json?sort_by=source&sort_order=asc&valid_time=48'
      )
    })
  })

  describe('source feed', () => {
    it('should build source feed URL with rss format', () => {
      vi.mocked(isTauri).mockReturnValue(false)
      const url = buildFeedPathUrl('rss', { source_id: 5 })
      expect(url).toBe('/api/v1/sources/5/rss')
    })

    it('should build source feed URL with json format', () => {
      vi.mocked(isTauri).mockReturnValue(false)
      const url = buildFeedPathUrl('json', { source_id: 1 })
      expect(url).toBe('/api/v1/sources/1/json')
    })

    it('should build source feed URL with markdown format', () => {
      vi.mocked(isTauri).mockReturnValue(false)
      const url = buildFeedPathUrl('markdown', { source_id: 10 })
      expect(url).toBe('/api/v1/sources/10/markdown')
    })

    it('should include query params for source feed', () => {
      vi.mocked(isTauri).mockReturnValue(false)
      const url = buildFeedPathUrl('json', {
        source_id: 3,
        sort_by: 'source',
      })
      expect(url).toBe('/api/v1/sources/3/json?sort_by=source')
    })
  })

  describe('group feed', () => {
    it('should build group feed URL with rss format', () => {
      vi.mocked(isTauri).mockReturnValue(false)
      const url = buildFeedPathUrl('rss', { group_id: 2 })
      expect(url).toBe('/api/v1/groups/2/rss')
    })

    it('should build group feed URL with json format', () => {
      vi.mocked(isTauri).mockReturnValue(false)
      const url = buildFeedPathUrl('json', { group_id: 1 })
      expect(url).toBe('/api/v1/groups/1/json')
    })

    it('should build group feed URL with markdown format', () => {
      vi.mocked(isTauri).mockReturnValue(false)
      const url = buildFeedPathUrl('markdown', { group_id: 7 })
      expect(url).toBe('/api/v1/groups/7/markdown')
    })

    it('should include query params for group feed', () => {
      vi.mocked(isTauri).mockReturnValue(false)
      const url = buildFeedPathUrl('markdown', {
        group_id: 5,
        keywords: 'tech',
      })
      expect(url).toBe('/api/v1/groups/5/markdown?keywords=tech')
    })
  })

  describe('Tauri environment', () => {
    it('should use localhost URL in Tauri mode', () => {
      vi.mocked(isTauri).mockReturnValue(true)
      const url = buildFeedPathUrl('rss')
      expect(url).toBe('http://localhost:8000/api/v1/feed/rss')
    })

    it('should use localhost URL for source feed in Tauri mode', () => {
      vi.mocked(isTauri).mockReturnValue(true)
      const url = buildFeedPathUrl('json', { source_id: 1 })
      expect(url).toBe('http://localhost:8000/api/v1/sources/1/json')
    })

    it('should use localhost URL for group feed in Tauri mode', () => {
      vi.mocked(isTauri).mockReturnValue(true)
      const url = buildFeedPathUrl('markdown', { group_id: 2 })
      expect(url).toBe('http://localhost:8000/api/v1/groups/2/markdown')
    })
  })

  describe('custom base URL', () => {
    it('should use custom base URL from window', () => {
      vi.mocked(isTauri).mockReturnValue(false)
      ;(window as any).__VITE_API_BASE_URL__ = 'https://api.example.com/v1'
      const url = buildFeedPathUrl('rss')
      expect(url).toBe('https://api.example.com/v1/feed/rss')
    })
  })
})