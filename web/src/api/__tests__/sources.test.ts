import { describe, it, expect, vi, beforeEach } from 'vitest'
import api from '../index'
import { createSource, updateSource } from '../sources'
import type { Source } from '@/types/source'

vi.mock('../index', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
  },
}))

describe('sources API', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('createSource', () => {
    it('should not include fetch_interval in request', async () => {
      const mockSource: Source = {
        id: 1, name: 'Test', url: 'https://example.com/rss', is_active: true,
        last_fetched_at: null, last_error: null, created_at: '', updated_at: '', groups: [],
      }
      vi.mocked(api.post).mockResolvedValue(mockSource)

      await createSource({ name: 'Test', url: 'https://example.com/rss' })

      expect(api.post).toHaveBeenCalledWith('/sources', { name: 'Test', url: 'https://example.com/rss' })
    })
  })

  describe('updateSource', () => {
    it('should update source without fetch_interval', async () => {
      const mockSource: Source = {
        id: 1, name: 'Updated', url: 'https://example.com/rss', is_active: true,
        last_fetched_at: null, last_error: null, created_at: '', updated_at: '', groups: [],
      }
      vi.mocked(api.put).mockResolvedValue(mockSource)

      await updateSource(1, { name: 'Updated' })

      expect(api.put).toHaveBeenCalledWith('/sources/1', { name: 'Updated' })
    })
  })
})
