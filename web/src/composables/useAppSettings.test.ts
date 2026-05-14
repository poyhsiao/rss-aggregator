import { describe, it, expect, vi, beforeEach } from 'vitest'
import { useAppSettings } from './useAppSettings'

vi.mock('@/api/app-settings', () => ({
  getAppSettings: vi.fn(),
  updateAppSettings: vi.fn(),
}))

import { getAppSettings, updateAppSettings } from '@/api/app-settings'

const mockGetAppSettings = vi.mocked(getAppSettings)
const mockUpdateAppSettings = vi.mocked(updateAppSettings)

describe('useAppSettings', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('fetches settings on fetchSettings()', async () => {
    const mockData = { group_enabled: true, schedule_enabled: false, share_enabled: false }
    mockGetAppSettings.mockResolvedValueOnce(mockData)

    const { fetchSettings, settings } = useAppSettings()
    await fetchSettings()

    expect(mockGetAppSettings).toHaveBeenCalled()
    expect(settings.value.group_enabled).toBe(true)
    expect(settings.value.schedule_enabled).toBe(false)
    expect(settings.value.share_enabled).toBe(false)
  })

  it('saves settings and updates state on saveSettings()', async () => {
    const mockData = { group_enabled: true, schedule_enabled: true, share_enabled: false }
    mockUpdateAppSettings.mockResolvedValueOnce(mockData)

    const { saveSettings, settings } = useAppSettings()
    await saveSettings({ group_enabled: true, schedule_enabled: true })

    expect(mockUpdateAppSettings).toHaveBeenCalledWith({ group_enabled: true, schedule_enabled: true })
    expect(settings.value.group_enabled).toBe(true)
    expect(settings.value.schedule_enabled).toBe(true)
    expect(settings.value.share_enabled).toBe(false)
  })

  it('sets error when fetchSettings fails', async () => {
    mockGetAppSettings.mockRejectedValueOnce(new Error('Network error'))

    const { fetchSettings, error } = useAppSettings()
    await fetchSettings()

    expect(error.value).toBe('Network error')
  })

  it('sets error and throws when saveSettings fails', async () => {
    mockUpdateAppSettings.mockRejectedValueOnce(new Error('Save failed'))

    const { saveSettings, error } = useAppSettings()

    await expect(saveSettings({ share_enabled: true })).rejects.toThrow('Save failed')
    expect(error.value).toBe('Save failed')
  })

  it('resets to default settings on fetch failure', async () => {
    mockGetAppSettings.mockRejectedValueOnce(new Error('Network error'))

    const { fetchSettings, settings } = useAppSettings()
    await fetchSettings()

    expect(settings.value).toEqual({
      group_enabled: false,
      schedule_enabled: false,
      share_enabled: false,
    })
  })
})
