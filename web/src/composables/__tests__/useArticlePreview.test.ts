import { describe, it, expect, vi, beforeEach } from 'vitest'
import { useArticlePreview } from '../useArticlePreview'

vi.mock('@/api/preview', () => ({
  getCachedPreview: vi.fn(),
  fetchAndCachePreview: vi.fn(),
}))

vi.mock('@/utils/urlNormalizer', () => ({
  computeUrlHash: vi.fn(),
}))

import { getCachedPreview, fetchAndCachePreview } from '@/api/preview'
import { computeUrlHash } from '@/utils/urlNormalizer'

const mockGetCachedPreview = vi.mocked(getCachedPreview)
const mockFetchAndCachePreview = vi.mocked(fetchAndCachePreview)
const mockComputeUrlHash = vi.mocked(computeUrlHash)

describe('useArticlePreview', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockComputeUrlHash.mockResolvedValue('abc123')
  })

  describe('fetchPreview', () => {
    it('should return cached content when available', async () => {
      const mockPreview = {
        id: 1,
        url: 'https://example.com/article',
        url_hash: 'abc123',
        markdown_content: '# Cached Content',
        title: 'Cached',
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      }
      mockGetCachedPreview.mockResolvedValueOnce(mockPreview)

      const { fetchPreview, content, source } = useArticlePreview()
      await fetchPreview('https://example.com/article')

      expect(mockGetCachedPreview).toHaveBeenCalled()
      expect(content.value).toBe('# Cached Content')
      expect(source.value).toBe('cache')
    })

    it('should fetch from backend when not cached', async () => {
      mockGetCachedPreview.mockResolvedValueOnce(null)
      mockFetchAndCachePreview.mockResolvedValueOnce({
        id: 1,
        url: 'https://example.com/article',
        url_hash: 'abc123',
        markdown_content: '# New Content',
        title: 'New Content',
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      })

      const { fetchPreview, content, source } = useArticlePreview()
      await fetchPreview('https://example.com/article')

      expect(mockFetchAndCachePreview).toHaveBeenCalledWith('https://example.com/article')
      expect(content.value).toBe('# New Content')
      expect(source.value).toBe('api')
    })

    it('should set loading state during fetch', async () => {
      mockGetCachedPreview.mockResolvedValueOnce(null)
      mockFetchAndCachePreview.mockImplementation(
        () =>
          new Promise((resolve) =>
            setTimeout(
              () =>
                resolve({
                  id: 1,
                  url: '',
                  url_hash: '',
                  markdown_content: '# Content',
                  title: null,
                  created_at: '',
                  updated_at: '',
                }),
              100
            )
          )
      )

      const { fetchPreview, loading } = useArticlePreview()
      const promise = fetchPreview('https://example.com/article')

      expect(loading.value).toBe(true)
      await promise
      expect(loading.value).toBe(false)
    })
  })

  describe('error handling', () => {
    it('should set error on fetch failure', async () => {
      mockGetCachedPreview.mockResolvedValueOnce(null)
      mockFetchAndCachePreview.mockRejectedValueOnce(new Error('Network error'))

      const { fetchPreview, error } = useArticlePreview()
      await fetchPreview('https://example.com/article')

      expect(error.value).toBeTruthy()
    })
  })
})