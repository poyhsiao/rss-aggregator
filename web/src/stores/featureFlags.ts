import { defineStore } from 'pinia'
import { ref, watch } from 'vue'
import { getAppSettings, updateAppSettings } from '@/api/app-settings'
import type { AppSettingsResponse } from '@/types/app-settings'

export const useFeatureFlagsStore = defineStore('featureFlags', () => {
  const groupsEnabled = ref(false)
  const scheduleEnabled = ref(false)
  const sourceGroupSchedulesEnabled = ref(false)
  const shareEnabled = ref(false)
  const initialized = ref(false)
  const loading = ref(false)
  const error = ref<string | null>(null)

  // Cascade: when groupsEnabled turns OFF via UI, disable dependents.
  // Skipped during fetchSettings to avoid resetting values loaded from API.
  let fetching = false
  watch(groupsEnabled, (val) => {
    if (!fetching && !val) {
      scheduleEnabled.value = false
      sourceGroupSchedulesEnabled.value = false
    }
  })

  async function fetchSettings() {
    loading.value = true
    error.value = null
    fetching = true
    try {
      const data: AppSettingsResponse = await getAppSettings()
      groupsEnabled.value = data.group_enabled
      scheduleEnabled.value = data.schedule_enabled
      sourceGroupSchedulesEnabled.value = data.source_group_schedules_enabled
      shareEnabled.value = data.share_enabled
      initialized.value = true
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to load settings'
    } finally {
      fetching = false
      loading.value = false
    }
  }

  async function saveSettings() {
    loading.value = true
    error.value = null
    try {
      const payload = {
        group_enabled: groupsEnabled.value,
        schedule_enabled: scheduleEnabled.value,
        source_group_schedules_enabled: sourceGroupSchedulesEnabled.value,
        share_enabled: shareEnabled.value,
      }
      const updated = await updateAppSettings(payload)
      groupsEnabled.value = updated.group_enabled
      scheduleEnabled.value = updated.schedule_enabled
      sourceGroupSchedulesEnabled.value = updated.source_group_schedules_enabled
      shareEnabled.value = updated.share_enabled
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to save settings'
      throw e
    } finally {
      loading.value = false
    }
  }

  return {
    groupsEnabled,
    scheduleEnabled,
    sourceGroupSchedulesEnabled,
    shareEnabled,
    initialized,
    loading,
    error,
    fetchSettings,
    saveSettings,
  }
})
