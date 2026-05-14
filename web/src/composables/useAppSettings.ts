/**
 * useAppSettings — reads and updates global feature toggle settings.
 * Fetches settings once; updates apply on next page load.
 */
import { ref, readonly } from 'vue'
import { getAppSettings, updateAppSettings } from '@/api/app-settings'
import type { AppSettingsResponse } from '@/types/app-settings'

const DEFAULT_SETTINGS: AppSettingsResponse = {
  group_enabled: false,
  schedule_enabled: false,
  share_enabled: false,
}

const settings = ref<AppSettingsResponse>({ ...DEFAULT_SETTINGS })
const loading = ref(false)
const error = ref<string | null>(null)

export function useAppSettings() {
  async function fetchSettings() {
    loading.value = true
    error.value = null
    try {
      settings.value = await getAppSettings()
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to load settings'
      settings.value = { ...DEFAULT_SETTINGS }
    } finally {
      loading.value = false
    }
  }

  async function saveSettings(data: Partial<AppSettingsResponse>) {
    loading.value = true
    error.value = null
    try {
      settings.value = await updateAppSettings(data)
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to save settings'
      throw e
    } finally {
      loading.value = false
    }
  }

  return {
    settings: readonly(settings),
    loading: readonly(loading),
    error: readonly(error),
    fetchSettings,
    saveSettings,
  }
}
