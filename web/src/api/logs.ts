import api from '.'
import type { ErrorLog } from '@/types/log'

export interface LogsParams {
  limit?: number
  source_id?: number
}

export async function getLogs(params?: LogsParams): Promise<ErrorLog[]> {
  const { data } = await api.get('/logs', { params })
  return data
}