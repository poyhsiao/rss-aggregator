import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import api from '@/api'
import { useFeatureFlagsStore } from '../../stores/featureFlags'

// Mock localStorage
const localStorageMock = (() => {
  let store: Record<string, string> = {}
  return {
    getItem: vi.fn((key: string) => store[key] || null),
    setItem: vi.fn((key: string, value: string) => {
      store[key] = value
    }),
    removeItem: vi.fn((key: string) => {
      delete store[key]
    }),
    clear: vi.fn(() => {
      store = {}
    }),
  }
})()

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
})

// Mock API
vi.mock('@/api', () => ({
  default: {
    get: vi.fn(),
    patch: vi.fn(),
  },
}))

describe('Feature Flags Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    localStorageMock.clear()
    vi.clearAllMocks()
  })

  describe('default values', () => {
    it('should have feature_groups set to false by default', () => {
      const store = useFeatureFlagsStore()
      expect(store.feature_groups).toBe(false)
    })

    it('should have feature_schedules set to false by default', () => {
      const store = useFeatureFlagsStore()
      expect(store.feature_schedules).toBe(false)
    })

    it('should have feature_share_links set to false by default', () => {
      const store = useFeatureFlagsStore()
      expect(store.feature_share_links).toBe(false)
    })
  })

  describe('toggle', () => {
    it('should toggle feature_groups', async () => {
      const store = useFeatureFlagsStore()
      expect(store.feature_groups).toBe(false)

      await store.toggle('feature_groups')

      expect(store.feature_groups).toBe(true)
    })

    it('should toggle feature_schedules', async () => {
      const store = useFeatureFlagsStore()
      expect(store.feature_schedules).toBe(false)

      await store.toggle('feature_schedules')

      expect(store.feature_schedules).toBe(true)
    })

    it('should toggle feature_share_links', async () => {
      const store = useFeatureFlagsStore()
      expect(store.feature_share_links).toBe(false)

      await store.toggle('feature_share_links')

      expect(store.feature_share_links).toBe(true)
    })

    it('should update localStorage immediately on toggle', async () => {
      const store = useFeatureFlagsStore()

      await store.toggle('feature_groups')

      expect(localStorageMock.setItem).toHaveBeenCalledWith(
        'feature_flags',
        expect.stringContaining('"feature_groups":true')
      )
    })
  })

  describe('init', () => {
    it('should try API first on init', async () => {
      const store = useFeatureFlagsStore()

      await store.init()

      expect(api.get).toHaveBeenCalledWith('/feature-flags')
    })

    it('should fallback to localStorage when API fails', async () => {
      vi.mocked(api.get).mockRejectedValueOnce(new Error('API unavailable'))

      // Pre-populate localStorage
      localStorageMock.getItem = vi.fn().mockReturnValue(
        JSON.stringify({
          feature_groups: true,
          feature_schedules: true,
          feature_share_links: true,
        })
      )

      const store = useFeatureFlagsStore()
      await store.init()

      expect(store.feature_groups).toBe(true)
      expect(store.feature_schedules).toBe(true)
      expect(store.feature_share_links).toBe(true)
    })

    it('should use localStorage defaults when both API and localStorage fail', async () => {
      vi.mocked(api.get).mockRejectedValueOnce(new Error('API unavailable'))
      localStorageMock.getItem = vi.fn().mockReturnValue(null)

      const store = useFeatureFlagsStore()
      await store.init()

      expect(store.feature_groups).toBe(false)
      expect(store.feature_schedules).toBe(false)
      expect(store.feature_share_links).toBe(false)
    })
  })

  describe('syncToApi', () => {
    it('should call API patch when syncing', async () => {
      const store = useFeatureFlagsStore()

      await store.toggle('feature_groups')
      await vi.waitFor(() => {
        expect(api.patch).toHaveBeenCalledWith(
          '/feature-flags',
          expect.objectContaining({ feature_groups: true })
        )
      })
    })

    it('should not block UI on API sync failure', async () => {
      vi.mocked(api.patch).mockRejectedValueOnce(new Error('Network error'))

      const store = useFeatureFlagsStore()
      const togglePromise = store.toggle('feature_groups')

      // Toggle should resolve even if API fails
      await expect(togglePromise).resolves.toBeUndefined()
      expect(store.feature_groups).toBe(true) // localStorage update should still work
    })
  })

  describe('isLoading', () => {
    it('should be true while init is fetching API', async () => {
      vi.mocked(api.get).mockImplementation(
        () => new Promise((resolve) => setTimeout(resolve, 100)) as ReturnType<typeof api.get>
      )

      const store = useFeatureFlagsStore()
      const initPromise = store.init()

      expect(store.isLoading).toBe(true)

      await initPromise
      expect(store.isLoading).toBe(false)
    })
  })

  describe('error', () => {
    it('should store error message when API fails', async () => {
      vi.mocked(api.get).mockRejectedValueOnce(new Error('Failed to fetch'))

      const store = useFeatureFlagsStore()
      await store.init()

      expect(store.error).toBe('Failed to sync with server — using local settings')
    })

    it('should clear error on successful init', async () => {
      vi.mocked(api.get).mockRejectedValueOnce(new Error('Failed to fetch'))
      localStorageMock.getItem = vi.fn().mockReturnValue(null)

      const store = useFeatureFlagsStore()
      await store.init()
      expect(store.error).toBe('Failed to sync with server — using local settings')

      // Now API succeeds
      vi.mocked(api.get).mockResolvedValueOnce([
        { key: 'feature_groups', enabled: true },
        { key: 'feature_schedules', enabled: false },
        { key: 'feature_share_links', enabled: false },
      ])

      await store.init()
      expect(store.error).toBe(null)
    })
  })

  describe('persistence', () => {
    it('should save all flags to localStorage', async () => {
      const store = useFeatureFlagsStore()

      await store.toggle('feature_groups')
      await store.toggle('feature_schedules')

      expect(localStorageMock.setItem).toHaveBeenCalledWith(
        'feature_flags',
        expect.stringContaining('"feature_groups":true')
      )
      expect(localStorageMock.setItem).toHaveBeenCalledWith(
        'feature_flags',
        expect.stringContaining('"feature_schedules":true')
      )
    })
  })
})