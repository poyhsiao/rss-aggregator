import api from '.'
import type { ErrorLog } from '@/types/log'

export interface LogsParams {
  limit?: number
  source_id?: number
}

export async function getLogs(params?: LogsParams): Promise<ErrorLog[]> {
  const queryParts: string[] = []
  if (params?.limit) queryParts.push(`limit=${params.limit}`)
  if (params?.source_id) queryParts.push(`source_id=${params.source_id}`)
  const query = queryParts.length > 0 ? `?${queryParts.join('&')}` : ''
  const result = await api.get<ErrorLog[]>(`/logs${query}`)
  return result
}