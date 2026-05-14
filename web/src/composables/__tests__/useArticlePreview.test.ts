import { describe, it, expect, vi, beforeEach } from 'vitest'
import { useArticlePreview } from '../useArticlePreview'

vi.mock('@/api/preview', () => ({
  fetchAndCachePreview: vi.fn(),
  getCachedPreview: vi.fn(),
  getCachedPreviewByUrl: vi.fn(),
  savePreview: vi.fn(),
}))

vi.mock('@/utils/urlNormalizer', () => ({
  computeUrlHash: vi.fn(),
}))

vi.mock('@/utils/environment', () => ({
  isTauri: vi.fn().mockReturnValue(false),
}))

import { fetchAndCachePreview, getCachedPreview, getCachedPreviewByUrl, savePreview } from '@/api/preview'
import { computeUrlHash } from '@/utils/urlNormalizer'
import { isTauri } from '@/utils/environment'

const mockFetchAndCachePreview = vi.mocked(fetchAndCachePreview)
const mockIsTauri = vi.mocked(isTauri)

describe('useArticlePreview', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockIsTauri.mockReturnValue(false)
    mockFetchAndCachePreview.mockResolvedValue({
      id: 1,
      url: '',
      url_hash: '',
      markdown_content: '# Content',
      title: null,
      created_at: '',
      updated_at: '',
    })
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
      mockFetchAndCachePreview.mockResolvedValueOnce(mockPreview)

      const { fetchPreview, content, source } = useArticlePreview()
      await fetchPreview('https://example.com/article')

      expect(mockFetchAndCachePreview).toHaveBeenCalledWith('https://example.com/article')
      expect(content.value).toBe('# Cached Content')
    })

    it('should fetch from backend when not cached', async () => {
      mockFetchAndCachePreview.mockResolvedValueOnce({
        id: 1,
        url: 'https://example.com/article',
        url_hash: 'abc123',
        markdown_content: '# New Content',
        title: 'New Content',
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      })

      const { fetchPreview, content } = useArticlePreview()
      await fetchPreview('https://example.com/article')

      expect(mockFetchAndCachePreview).toHaveBeenCalledWith('https://example.com/article')
      expect(content.value).toBe('# New Content')
    })

    it('should set loading state during fetch', async () => {
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
      mockFetchAndCachePreview.mockRejectedValueOnce(new Error('Network error'))

      const { fetchPreview, error } = useArticlePreview()
      await fetchPreview('https://example.com/article')

      expect(error.value).toBeTruthy()
    })
  })
})