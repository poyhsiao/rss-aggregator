import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useSettingsStore = defineStore('settings', () => {
  const theme = ref<'light' | 'dark' | 'system'>('system')
  const locale = ref<'zh' | 'en'>('zh')

  return {
    theme,
    locale,
  }
})