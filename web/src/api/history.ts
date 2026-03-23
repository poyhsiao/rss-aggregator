import api from "./axios";
import type { HistoryParams, HistoryResponse } from "@/types/history";

export async function getHistory(params: HistoryParams): Promise<HistoryResponse> {
  const response = await api.get<HistoryResponse>("/history", { params });
  return response.data;
}