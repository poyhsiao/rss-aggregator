import api from '.'
import { useAuthStore } from '@/stores/auth'
import { isTauri } from '@/utils/environment'

// Default query parameter values to filter out from URLs
const DEFAULT_SORT_BY = 'published_at'
const DEFAULT_SORT_ORDER = 'desc'

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
  group_id?: number
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

/**
 * Get the base API URL for the current environment.
 */
function getBaseUrl(): string {
  if (isTauri()) {
    return 'http://localhost:8000/api/v1'
  }
  const win = window as { __VITE_API_BASE_URL__?: string }
  return win.__VITE_API_BASE_URL__ || '/api/v1'
}

/**
 * Build a path-based feed URL for a specific format.
 * Filters out query parameters with default values to keep URLs clean.
 *
 * @param format - Feed format (rss, json, markdown)
 * @param params - Feed params (source_id, group_id, sort_by, etc.)
 * @returns Full URL string with path-based format and non-default query params
 */
export function buildFeedPathUrl(
  format: FeedFormat,
  params?: FeedParams
): string {
  const baseUrl = getBaseUrl()

  // Build path based on params
  let path = '/feed'
  if (params?.source_id !== undefined) {
    path = `/sources/${params.source_id}`
  } else if (params?.group_id !== undefined) {
    path = `/groups/${params.group_id}`
  }

  // Add format to path
  path = `${path}/${format}`

  // Filter out default-valued query parameters
  const queryParams: Record<string, string> = {}

  if (params?.sort_by && params.sort_by !== DEFAULT_SORT_BY) {
    queryParams.sort_by = params.sort_by
  }
  if (params?.sort_order && params.sort_order !== DEFAULT_SORT_ORDER) {
    queryParams.sort_order = params.sort_order
  }
  if (params?.valid_time !== undefined) {
    queryParams.valid_time = String(params.valid_time)
  }
  if (params?.keywords) {
    queryParams.keywords = params.keywords
  }

  // Build query string from non-default params
  const qs = buildQueryString(queryParams)

  return `${baseUrl}${path}${qs}`
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