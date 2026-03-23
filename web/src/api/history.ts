import api from '.'
import type { HistoryParams, HistoryResponse } from '@/types/history'

export async function getHistory(params: HistoryParams): Promise<HistoryResponse> {
  const queryParts: string[] = []
  if (params?.start_date) queryParts.push(`start_date=${encodeURIComponent(params.start_date)}`)
  if (params?.end_date) queryParts.push(`end_date=${encodeURIComponent(params.end_date)}`)
  if (params?.source_ids) queryParts.push(`source_ids=${encodeURIComponent(params.source_ids)}`)
  if (params?.keywords) queryParts.push(`keywords=${encodeURIComponent(params.keywords)}`)
  if (params?.sort_by) queryParts.push(`sort_by=${params.sort_by}`)
  if (params?.sort_order) queryParts.push(`sort_order=${params.sort_order}`)
  if (params?.page) queryParts.push(`page=${params.page}`)
  if (params?.page_size) queryParts.push(`page_size=${params.page_size}`)
  const query = queryParts.length > 0 ? `?${queryParts.join('&')}` : ''
  return api.get<HistoryResponse>(`/history${query}`)
}
