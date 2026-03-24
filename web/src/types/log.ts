export interface ErrorLog {
  id: number
  source_id: number | null
  status: 'success' | 'error'
  log_type: string
  message: string
  items_count: number | null
  created_at: string
  details?: string
  request_data?: string
}

export type LogAction =
  | 'create_source'
  | 'update_source'
  | 'delete_source'
  | 'create_key'
  | 'delete_key'
  | 'refresh_source'
  | 'refresh_all'

export interface OperationLogDetails {
  target?: string
  targetId?: number
  request?: unknown
  response?: unknown
  error?: string
}

export interface OperationLog {
  id: string
  timestamp: string
  action: LogAction
  status: 'success' | 'error'
  message: string
  details: OperationLogDetails
}