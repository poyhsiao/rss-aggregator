import axios from 'axios'
import { useAuthStore } from '@/stores/auth'
import { isTauri } from '@/utils/environment'

const getWebBaseUrl = (): string => {
  const win = window as { __VITE_API_BASE_URL__?: string }
  return win.__VITE_API_BASE_URL__ || '/api/v1'
}

function getBaseURL(): string {
  if (isTauri()) {
    return 'app://localhost/api/v1'
  }
  return getWebBaseUrl()
}

const axiosInstance = axios.create({
  baseURL: isTauri() ? undefined : getBaseURL(),
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

axiosInstance.interceptors.request.use((config) => {
  const authStore = useAuthStore()
  if (authStore.apiKey) {
    config.headers['X-API-Key'] = authStore.apiKey
  }
  return config
})

axiosInstance.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      const authStore = useAuthStore()
      authStore.logout()
    }
    return Promise.reject(error)
  }
)

async function tauriFetch<T>(
  url: string,
  options: RequestInit = {}
): Promise<T> {
  const authStore = useAuthStore()
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
  }

  if (authStore.apiKey) {
    headers['X-API-Key'] = authStore.apiKey
  }

  const fullUrl = `app://localhost/api/v1${url}`
  console.log('[tauriFetch] Fetching:', fullUrl)

  const response = await fetch(fullUrl, {
    ...options,
    headers,
  })

  console.log('[tauriFetch] Response status:', response.status)

  if (!response.ok) {
    if (response.status === 401) {
      authStore.logout()
    }
    const error = await response.json().catch(() => ({ message: response.statusText }))
    console.error('[tauriFetch] Error:', error)
    throw new Error(error.message || `HTTP ${response.status}`)
  }

  const data = await response.json()
  console.log('[tauriFetch] Response data:', data)
  return data
}

const api = {
  get<T>(url: string, config?: { headers?: Record<string, string> }): Promise<T> {
    if (isTauri()) {
      return tauriFetch<T>(url, { method: 'GET', headers: config?.headers })
    }
    return axiosInstance.get(url, config).then((r) => r.data)
  },

  post<T>(url: string, data?: unknown, config?: { headers?: Record<string, string> }): Promise<T> {
    if (isTauri()) {
      return tauriFetch<T>(url, {
        method: 'POST',
        body: data ? JSON.stringify(data) : undefined,
        headers: config?.headers,
      })
    }
    return axiosInstance.post(url, data, config).then((r) => r.data)
  },

  put<T>(url: string, data?: unknown, config?: { headers?: Record<string, string> }): Promise<T> {
    if (isTauri()) {
      return tauriFetch<T>(url, {
        method: 'PUT',
        body: data ? JSON.stringify(data) : undefined,
        headers: config?.headers,
      })
    }
    return axiosInstance.put(url, data, config).then((r) => r.data)
  },

  delete<T>(url: string, config?: { headers?: Record<string, string> }): Promise<T> {
    if (isTauri()) {
      return tauriFetch<T>(url, { method: 'DELETE', headers: config?.headers })
    }
    return axiosInstance.delete(url, config).then((r) => r.data)
  },
}

export default api