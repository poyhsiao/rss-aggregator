import api from "."
import type { HistoryResponse, HistoryBatchesResponse, HistoryBatch, UpdateBatchNameRequest, DeleteHistoryResponse } from "@/types/history"

export async function getHistoryBatches(
  limit: number = 50,
  offset: number = 0,
  groupId?: number
): Promise<HistoryBatchesResponse> {
  const params = new URLSearchParams({ limit: String(limit), offset: String(offset) })
  if (groupId !== undefined) params.append('group_id', String(groupId))
  return api.get<HistoryBatchesResponse>(`/history/batches?${params.toString()}`)
}

export async function getHistoryByBatch(
  batchId: number,
  page: number = 1,
  pageSize: number = 50
): Promise<HistoryResponse> {
  return api.get<HistoryResponse>(
    `/history/batches/${batchId}?page=${page}&page_size=${pageSize}`
  )
}

export async function updateBatchName(
  batchId: number,
  request: UpdateBatchNameRequest
): Promise<HistoryBatch> {
  return api.patch<HistoryBatch>(`/history/batches/${batchId}/name`, request)
}

export async function deleteBatch(batchId: number): Promise<{ success: boolean }> {
  return api.delete<{ success: boolean }>(`/history/batches/${batchId}`)
}

export async function deleteAllHistory(): Promise<DeleteHistoryResponse> {
  return api.delete<DeleteHistoryResponse>("/history/")
}

export async function deleteHistoryByGroup(groupId: number): Promise<DeleteHistoryResponse> {
  return api.delete<DeleteHistoryResponse>(`/history/by-group/${groupId}`)
}