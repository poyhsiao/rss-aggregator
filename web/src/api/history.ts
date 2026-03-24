import api from "."
import type { HistoryResponse, HistoryBatchesResponse, HistoryBatch, UpdateBatchNameRequest } from "@/types/history"

export async function getHistoryBatches(
  limit: number = 50,
  offset: number = 0
): Promise<HistoryBatchesResponse> {
  return api.get<HistoryBatchesResponse>(`/history/batches?limit=${limit}&offset=${offset}`)
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