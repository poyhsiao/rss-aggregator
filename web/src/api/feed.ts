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
}

export async function getFeed(params?: FeedParams): Promise<FeedItem[]> {
  const { data } = await api.get('/feed', { params })
  return data
}