import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/api'

const STORAGE_KEY = 'feature_flags'

export type FeatureFlagKey = 'feature_groups' | 'feature_schedules' | 'feature_share_links'

interface FeatureFlags {
  feature_groups: boolean
  feature_schedules: boolean
  feature_share_links: boolean
}

function loadFromStorage(): FeatureFlags | null {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored) {
      return JSON.parse(stored) as FeatureFlags
    }
  } catch {
    // Ignore parsing errors
  }
  return null
}

function saveToStorage(flags: FeatureFlags): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(flags))
  } catch {
    // Ignore storage errors
  }
}

function getDefaultFlags(): FeatureFlags {
  return {
    feature_groups: false,
    feature_schedules: false,
    feature_share_links: false,
  }
}

export const useFeatureFlagsStore = defineStore('featureFlags', () => {
  const feature_groups = ref(false)
  const feature_schedules = ref(false)
  const feature_share_links = ref(false)
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  async function syncToApi(): Promise<void> {
    try {
      await api.patch('/feature-flags', {
        feature_groups: feature_groups.value,
        feature_schedules: feature_schedules.value,
        feature_share_links: feature_share_links.value,
      })
    } catch {
      // Fire-and-forget: don't block UI on sync failure
    }
  }

  function saveCurrentFlags(): void {
    saveToStorage({
      feature_groups: feature_groups.value,
      feature_schedules: feature_schedules.value,
      feature_share_links: feature_share_links.value,
    })
  }

  async function toggle(flag: FeatureFlagKey): Promise<void> {
    const flagRef = flag === 'feature_groups'
      ? feature_groups
      : flag === 'feature_schedules'
        ? feature_schedules
        : feature_share_links

    flagRef.value = !flagRef.value

    saveCurrentFlags()

    syncToApi()
  }

  async function init(): Promise<void> {
    isLoading.value = true
    error.value = null

    try {
      const data = await api.get<FeatureFlags>('/feature-flags')
      feature_groups.value = data.feature_groups
      feature_schedules.value = data.feature_schedules
      feature_share_links.value = data.feature_share_links
      saveCurrentFlags()
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to fetch'
      const stored = loadFromStorage()
      if (stored) {
        feature_groups.value = stored.feature_groups
        feature_schedules.value = stored.feature_schedules
        feature_share_links.value = stored.feature_share_links
      } else {
        const defaults = getDefaultFlags()
        feature_groups.value = defaults.feature_groups
        feature_schedules.value = defaults.feature_schedules
        feature_share_links.value = defaults.feature_share_links
      }
    } finally {
      isLoading.value = false
    }
  }

  return {
    feature_groups,
    feature_schedules,
    feature_share_links,
    isLoading,
    error,
    toggle,
    init,
  }
})