import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useFeedUrlSettingsStore } from '../feedUrlSettings'

vi.mock('@/api/settings', () => ({
  feedUrlApi: {
    get: vi.fn(),
    set: vi.fn(),
  },
}))

describe('feedUrlSettingsStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('has enabled false by default', () => {
    const store = useFeedUrlSettingsStore()
    expect(store.enabled).toBe(false)
  })

  it('fetchSettings sets enabled to true', async () => {
    const { feedUrlApi } = await import('@/api/settings')
    vi.mocked(feedUrlApi.get).mockResolvedValue({ enabled: true })

    const store = useFeedUrlSettingsStore()
    await store.fetchSettings()

    expect(store.enabled).toBe(true)
  })

  it('setEnabled updates enabled and calls API', async () => {
    const { feedUrlApi } = await import('@/api/settings')
    const mockSet = vi.mocked(feedUrlApi.set).mockResolvedValue(undefined)

    const store = useFeedUrlSettingsStore()
    await store.setEnabled(true)

    expect(mockSet).toHaveBeenCalledWith(true)
    expect(store.enabled).toBe(true)
  })
})