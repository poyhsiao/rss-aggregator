export interface ErrorLog {
  id: number
  source_id: number | null
  status: 'success' | 'error'
  log_type: string
  message: string
  items_count: number | null
  created_at: string
}