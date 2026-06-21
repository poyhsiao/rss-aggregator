import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { nextTick } from 'vue'
import { useFeatureFlagsStore } from '../featureFlags'

vi.mock('@/api/app-settings', () => ({
  getAppSettings: vi.fn(),
  updateAppSettings: vi.fn(),
}))

import { getAppSettings, updateAppSettings } from '@/api/app-settings'

const mockGet = vi.mocked(getAppSettings)
const mockPut = vi.mocked(updateAppSettings)

describe('FeatureFlagsStore', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    setActivePinia(createPinia())
  })

  // --- Initial state ---
  it('initializes all flags as false and initialized as false', () => {
    const store = useFeatureFlagsStore()
    expect(store.groupsEnabled).toBe(false)
    expect(store.scheduleEnabled).toBe(false)
    expect(store.sourceGroupSchedulesEnabled).toBe(false)
    expect(store.shareEnabled).toBe(false)
    expect(store.initialized).toBe(false)
    expect(store.loading).toBe(false)
    expect(store.error).toBeNull()
  })

  // --- fetchSettings ---
  it('fetchSettings syncs API response to store refs', async () => {
    mockGet.mockResolvedValueOnce({
      group_enabled: true,
      schedule_enabled: true,
      share_enabled: true,
      source_group_schedules_enabled: true,
    })
    const store = useFeatureFlagsStore()
    await store.fetchSettings()

    expect(store.groupsEnabled).toBe(true)
    expect(store.scheduleEnabled).toBe(true)
    expect(store.sourceGroupSchedulesEnabled).toBe(true)
    expect(store.shareEnabled).toBe(true)
    expect(store.initialized).toBe(true)
  })

  it('fetchSettings sets initialized to true', async () => {
    mockGet.mockResolvedValueOnce({
      group_enabled: false, schedule_enabled: false,
      share_enabled: false, source_group_schedules_enabled: false,
    })
    const store = useFeatureFlagsStore()
    expect(store.initialized).toBe(false)
    await store.fetchSettings()
    expect(store.initialized).toBe(true)
  })

  it('fetchSettings failure sets error and store values unchanged', async () => {
    mockGet.mockRejectedValueOnce(new Error('Network error'))
    const store = useFeatureFlagsStore()
    await store.fetchSettings()

    expect(store.error).toBe('Network error')
    expect(store.groupsEnabled).toBe(false)
    expect(store.shareEnabled).toBe(false)
    expect(store.initialized).toBe(false)
  })

  it('fetchSettings sets loading during call', async () => {
    let resolve: (v: any) => void
    mockGet.mockReturnValueOnce(new Promise(r => { resolve = r }))
    const store = useFeatureFlagsStore()
    const promise = store.fetchSettings()
    expect(store.loading).toBe(true)
    resolve!({
      group_enabled: false, schedule_enabled: false,
      share_enabled: false, source_group_schedules_enabled: false,
    })
    await promise
    expect(store.loading).toBe(false)
  })

  // --- saveSettings ---
  it('saveSettings sends all values and updates store', async () => {
    mockPut.mockResolvedValueOnce({
      group_enabled: true,
      schedule_enabled: false,
      share_enabled: true,
      source_group_schedules_enabled: false,
    })
    const store = useFeatureFlagsStore()
    store.groupsEnabled = true
    store.shareEnabled = true
    await store.saveSettings()

    expect(mockPut).toHaveBeenCalledWith({
      group_enabled: true,
      schedule_enabled: false,
      share_enabled: true,
      source_group_schedules_enabled: false,
    })
    expect(store.groupsEnabled).toBe(true)
    expect(store.scheduleEnabled).toBe(false)
    expect(store.shareEnabled).toBe(true)
    expect(store.sourceGroupSchedulesEnabled).toBe(false)
  })

  it('saveSettings failure sets error and throws', async () => {
    mockPut.mockRejectedValueOnce(new Error('Save failed'))
    const store = useFeatureFlagsStore()
    await expect(store.saveSettings()).rejects.toThrow('Save failed')
    expect(store.error).toBe('Save failed')
  })

  // --- Cascade ---
  it('cascade: groupsEnabled=false resets scheduleEnabled and sourceGroupSchedulesEnabled', async () => {
    const store = useFeatureFlagsStore()
    store.groupsEnabled = true
    store.scheduleEnabled = true
    store.sourceGroupSchedulesEnabled = true
    await nextTick()

    store.groupsEnabled = false
    await nextTick()
    expect(store.scheduleEnabled).toBe(false)
    expect(store.sourceGroupSchedulesEnabled).toBe(false)
  })

  it('cascade: groupsEnabled=false does NOT reset shareEnabled', async () => {
    const store = useFeatureFlagsStore()
    store.shareEnabled = true
    store.groupsEnabled = true
    await nextTick()

    store.groupsEnabled = false
    await nextTick()
    expect(store.shareEnabled).toBe(true)
  })

  it('has no groupSchedulesEnabled field', () => {
    const store = useFeatureFlagsStore()
    expect((store as any).groupSchedulesEnabled).toBeUndefined()
  })
})
