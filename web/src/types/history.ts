export interface HistoryItem {
  id: number
  source_id: number
  source: string
  title: string
  link: string
  description: string
  published_at: string | null
  fetched_at: string | null
}

export interface PaginationInfo {
  page: number
  page_size: number
  total_items: number
  total_pages: number
}

export interface HistoryResponse {
  items: HistoryItem[]
  pagination: PaginationInfo
}

export interface HistoryParams {
  start_date?: string
  end_date?: string
  source_ids?: string
  keywords?: string
  sort_by?: 'fetched_at' | 'published_at'
  sort_order?: 'asc' | 'desc'
  page?: number
  page_size?: number
}
