import { defineStore } from 'pinia'
import { feedUrlApi } from '@/api/settings'

export const useFeedUrlSettingsStore = defineStore('feedUrlSettings', {
  state: () => ({
    enabled: false,
  }),

  actions: {
    async fetchSettings() {
      try {
        const res = await feedUrlApi.get()
        this.enabled = res.enabled
      } catch {
        // On error, keep default false
        this.enabled = false
      }
    },

    async setEnabled(enabled: boolean) {
      await feedUrlApi.set(enabled)
      this.enabled = enabled
    },
  },
})