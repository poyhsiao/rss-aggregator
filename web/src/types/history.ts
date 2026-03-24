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

export interface HistoryBatch {
  id: number
  items_count: number
  sources: string[]
  created_at: string
}

export interface HistoryBatchesResponse {
  batches: HistoryBatch[]
  total_batches: number
  total_items: number
}