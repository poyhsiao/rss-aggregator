import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/api'
import { isTauri } from '@/utils/environment'

const STORAGE_KEY = 'rss-api-key'

export const useAuthStore = defineStore('auth', () => {
  const apiKey = ref<string | null>(null)
  const isValid = ref(false)
  const isVerifying = ref(false)
  const isInitialized = ref(false)
  const error = ref<string | null>(null)
  const requireApiKey = ref(true)

  const hasKey = computed(() => !!apiKey.value)

  async function init(): Promise<void> {
    try {
      const baseUrl = isTauri() ? 'app://localhost' : ''
      const response = await fetch(`${baseUrl}/health`)
      const data = await response.json() as { require_api_key?: boolean }
      requireApiKey.value = data?.require_api_key ?? true
    } catch {
      requireApiKey.value = true
    }

    if (!requireApiKey.value) {
      isValid.value = true
      isInitialized.value = true
      return
    }

    const stored = sessionStorage.getItem(STORAGE_KEY)
    if (stored) {
      apiKey.value = stored
      await verifyKey(stored)
    }
    isInitialized.value = true
  }

  async function verifyKey(key: string): Promise<boolean> {
    isVerifying.value = true
    error.value = null

    try {
      await api.get('/sources', {
        headers: { 'X-API-Key': key }
      })
      
      apiKey.value = key
      isValid.value = true
      sessionStorage.setItem(STORAGE_KEY, key)
      return true
    } catch (e: unknown) {
      const err = e as Error & { status?: number }
      if (err.message?.includes('401') || err.status === 401) {
        error.value = 'invalid'
      } else {
        error.value = 'failed'
      }
      isValid.value = false
      return false
    } finally {
      isVerifying.value = false
    }
  }

  function logout(): void {
    apiKey.value = null
    isValid.value = false
    sessionStorage.removeItem(STORAGE_KEY)
  }

  return {
    apiKey,
    isValid,
    isVerifying,
    isInitialized,
    error,
    hasKey,
    requireApiKey,
    init,
    verifyKey,
    logout,
  }
})