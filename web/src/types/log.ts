export interface ErrorLog {
  id: number
  source_id: number | null
  error_type: string
  error_message: string
  created_at: string
  updated_at: string
}