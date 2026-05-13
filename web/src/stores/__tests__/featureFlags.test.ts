import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useFeatureFlagsStore } from '../featureFlags'

// Mock localStorage
const localStorageMock = (() => {
  let store: Record<string, string> = {}
  return {
    getItem: vi.fn((key: string) => store[key] ?? null),
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

// Mock API module to prevent API calls
vi.mock('@/api/feature-flags', () => ({
  getFeatureFlags: vi.fn().mockResolvedValue({
    groups_enabled: true,
    group_schedules_enabled: true,
    source_group_schedules_enabled: true,
  }),
  updateFeatureFlags: vi.fn().mockResolvedValue({
    groups_enabled: true,
    group_schedules_enabled: true,
    source_group_schedules_enabled: true,
  }),
}))

describe('FeatureFlagsStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    localStorageMock.clear()
    vi.clearAllMocks()
  })

  it('initializes with localStorage false value', () => {
    localStorageMock.getItem.mockReturnValue('false')
    const store = useFeatureFlagsStore()
    expect(store.groupsEnabled).toBe(false)
  })

  it('initializes with default true when no localStorage', () => {
    localStorageMock.getItem.mockReturnValue(null)
    const store = useFeatureFlagsStore()
    expect(store.groupsEnabled).toBe(true)
  })
})