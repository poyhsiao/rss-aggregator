import api from "."
import type { HistoryResponse, HistoryBatchesResponse } from "@/types/history"

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