import api from "."
import type { HistoryParams, HistoryResponse } from "@/types/history";

export async function getHistory(params: HistoryParams): Promise<HistoryResponse> {
  // Build query string from params
  const searchParams = new URLSearchParams();
  if (params.start_date) searchParams.append("start_date", params.start_date);
  if (params.end_date) searchParams.append("end_date", params.end_date);
  if (params.source_ids) searchParams.append("source_ids", params.source_ids);
  if (params.keywords) searchParams.append("keywords", params.keywords);
  if (params.sort_by) searchParams.append("sort_by", params.sort_by);
  if (params.sort_order) searchParams.append("sort_order", params.sort_order);
  if (params.page) searchParams.append("page", String(params.page));
  if (params.page_size) searchParams.append("page_size", String(params.page_size));

  const queryString = searchParams.toString();
  const url = queryString ? `/history?${queryString}` : "/history";
  
  return api.get<HistoryResponse>(url);
}