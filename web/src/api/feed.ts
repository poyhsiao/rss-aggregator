import api from '.'

export interface FeedItem {
  id: number
  title: string
  link: string
  description: string
  source: string
  published_at: string
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

export async function getFeed(params?: FeedParams): Promise<FeedItem[]> {
  const { data } = await api.get('/feed', { params: { ...params, format: 'json' } })
  return data
}

export async function getFormattedFeed(
  format: FeedFormat,
  params?: FeedParams
): Promise<FormattedFeedResponse> {
  const { data, headers } = await api.get('/feed', {
    params: { ...params, format },
    responseType: 'text',
  })
  return {
    content: data,
    contentType: headers['content-type'] || 'text/plain',
  }
}

// Legacy function - kept for backward compatibility
export async function getRssFeed(params?: FeedParams): Promise<string> {
  const { content } = await getFormattedFeed('rss', params)
  return content
}