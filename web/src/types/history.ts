export interface HistoryItem {
  id: number
  source_id: number
  source: string
  title: string
  link: string
  description: string
  published_at: string | null
  fetched_at: string | null
  source_groups?: { id: number; name: string }[]
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
  name: string | null
  items_count: number
  sources: string[]
  created_at: string
  latest_fetched_at: string | null
  latest_published_at: string | null
  groups?: { id: number; name: string }[]
}

export interface HistoryBatchesResponse {
  batches: HistoryBatch[]
  total_batches: number
  total_items: number
}

export interface UpdateBatchNameRequest {
  name: string
}

export interface DeleteBatchResponse {
  success: boolean
}

export interface DeleteHistoryResponse {
  success: boolean
  deleted_count: number
}