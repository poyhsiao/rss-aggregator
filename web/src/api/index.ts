import axios from 'axios'
import { useAuthStore } from '@/stores/auth'
import { isTauri } from '@/utils/environment'
import { getActionFromUrl, logApiOperation, sanitizeRequestData } from './logger'

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
  (response) => {
    const method = response.config.method?.toUpperCase() || 'GET'
    const url = response.config.url || ''
    const logConfig = getActionFromUrl(method, url)
    
    if (logConfig) {
      logApiOperation({
        action: logConfig.action,
        status: 'success',
        targetId: logConfig.targetId,
        request: sanitizeRequestData(response.config.data),
        response: response.data,
      })
    }
    
    return response
  },
  (error) => {
    if (error.response?.status === 401) {
      const authStore = useAuthStore()
      authStore.logout()
    }

    const method = error.config?.method?.toUpperCase() || 'GET'
    const url = error.config?.url || ''
    const logConfig = getActionFromUrl(method, url)
    
    if (logConfig) {
      logApiOperation({
        action: logConfig.action,
        status: 'error',
        targetId: logConfig.targetId,
        request: sanitizeRequestData(error.config?.data),
        error: error.response?.data?.detail || error.message || 'Unknown error',
      })
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
  const method = options.method || 'GET'
  const logConfig = getActionFromUrl(method, url)
  
  let requestBody: unknown = null
  if (options.body) {
    try {
      requestBody = JSON.parse(options.body as string)
    } catch {
      requestBody = options.body
    }
  }

  try {
    const response = await fetch(fullUrl, {
      ...options,
      headers,
    })

    if (!response.ok) {
      if (response.status === 401) {
        authStore.logout()
      }
      const errorData = await response.json().catch(() => ({ message: response.statusText }))
      const errorMessage = errorData.detail || errorData.error || errorData.message || `HTTP ${response.status}`
      
      if (logConfig) {
        logApiOperation({
          action: logConfig.action,
          status: 'error',
          targetId: logConfig.targetId,
          request: sanitizeRequestData(requestBody),
          error: errorMessage,
        })
      }
      
      throw new Error(errorMessage)
    }

    if (response.status === 204) {
      if (logConfig) {
        logApiOperation({
          action: logConfig.action,
          status: 'success',
          targetId: logConfig.targetId,
          request: sanitizeRequestData(requestBody),
          response: null,
        })
      }
      return null as T
    }

    const data = await response.json()
    
    if (logConfig) {
      logApiOperation({
        action: logConfig.action,
        status: 'success',
        targetId: logConfig.targetId,
        request: sanitizeRequestData(requestBody),
        response: data,
      })
    }
    
    return data
  } catch (err) {
    if (logConfig && err instanceof Error) {
      logApiOperation({
        action: logConfig.action,
        status: 'error',
        targetId: logConfig.targetId,
        request: sanitizeRequestData(requestBody),
        error: err.message,
      })
    }
    throw err
  }
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

  patch<T>(url: string, data?: unknown, config?: { headers?: Record<string, string> }): Promise<T> {
    if (isTauri()) {
      return tauriFetch<T>(url, {
        method: 'PATCH',
        body: data ? JSON.stringify(data) : undefined,
        headers: config?.headers,
      })
    }
    return axiosInstance.patch(url, data, config).then((r) => r.data)
  },

  /**
   * POST request that returns a Blob (binary response).
   * Used for file downloads like backup export.
   */
  async postBlob(url: string, data?: unknown, config?: { headers?: Record<string, string> }): Promise<Blob> {
    if (isTauri()) {
      const authStore = useAuthStore()
      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
        ...(config?.headers || {}),
      }
      if (authStore.apiKey) {
        headers['X-API-Key'] = authStore.apiKey
      }
      const fullUrl = `app://localhost/api/v1${url}`
      const response = await fetch(fullUrl, {
        method: 'POST',
        headers,
        body: data ? JSON.stringify(data) : undefined,
      })
      if (!response.ok) {
        if (response.status === 401) {
          authStore.logout()
        }
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }
      return response.blob()
    }
    const response = await axiosInstance.post(url, data, {
      ...config,
      responseType: 'blob',
    })
    return response.data
  },

  /**
   * POST binary data (ArrayBuffer/Blob) and return JSON response.
   * Used for file uploads like backup import and preview.
   */
  async postBinary<T>(url: string, data: ArrayBuffer | Blob, config?: { headers?: Record<string, string> }): Promise<T> {
    if (isTauri()) {
      const authStore = useAuthStore()
      const headers: Record<string, string> = {
        'Content-Type': 'application/zip',
        ...(config?.headers || {}),
      }
      if (authStore.apiKey) {
        headers['X-API-Key'] = authStore.apiKey
      }
      const fullUrl = `app://localhost/api/v1${url}`
      const response = await fetch(fullUrl, {
        method: 'POST',
        headers,
        body: data,
      })
      if (!response.ok) {
        if (response.status === 401) {
          authStore.logout()
        }
        const errorData = await response.json().catch(() => ({ message: response.statusText }))
        throw new Error(errorData.detail || errorData.message || `HTTP ${response.status}`)
      }
      return response.json()
    }
    const response = await axiosInstance.post(url, data, {
      ...config,
      headers: {
        'Content-Type': 'application/zip',
        ...(config?.headers || {}),
      },
    })
    return response.data
  },
}

export default api