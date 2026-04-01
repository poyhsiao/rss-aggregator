import api from '.'
import { useAuthStore } from '@/stores/auth'
import { isTauri } from '@/utils/environment'

export interface FeedItem {
  id: number
  title: string
  link: string
  description: string
  source: string
  published_at: string
  source_groups?: { id: number; name: string }[]
}

export interface FeedParams {
  sort_by?: 'published_at' | 'source'
  sort_order?: 'asc' | 'desc'
  valid_time?: number
  keywords?: string
  source_id?: number
}

export type FeedFormat = 'rss' | 'json' | 'markdown'

export interface FormattedFeedResponse {
  content: string
  contentType: string
}

function buildQueryString(params?: Record<string, unknown>): string {
  if (!params) return ''
  const searchParams = new URLSearchParams()
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null) {
      searchParams.append(key, String(value))
    }
  })
  const qs = searchParams.toString()
  return qs ? `?${qs}` : ''
}

export async function getFeed(params?: FeedParams): Promise<FeedItem[]> {
  return api.get<FeedItem[]>(`/feed${buildQueryString({ ...params, format: 'json' })}`)
}

export async function getFormattedFeed(
  format: FeedFormat,
  params?: FeedParams
): Promise<FormattedFeedResponse> {
  const authStore = useAuthStore()
  const headers: Record<string, string> = {
    'Accept': format === 'json' ? 'application/json' : 'text/plain',
  }

  if (authStore.apiKey) {
    headers['X-API-Key'] = authStore.apiKey
  }

  const getWebBaseUrl = (): string => {
    const win = window as { __VITE_API_BASE_URL__?: string }
    return win.__VITE_API_BASE_URL__ || '/api/v1'
  }
  const baseUrl = isTauri() ? 'app://localhost/api/v1' : getWebBaseUrl()
  const response = await fetch(
    `${baseUrl}/feed${buildQueryString({ ...params, format })}`,
    { headers }
  )

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: ${response.statusText}`)
  }

  const content = await response.text()
  return {
    content,
    contentType: response.headers.get('content-type') || 'text/plain',
  }
}

export async function getRssFeed(params?: FeedParams): Promise<string> {
  const { content } = await getFormattedFeed('rss', params)
  return content
}