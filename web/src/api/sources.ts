import api from '.'
import type { Source } from '@/types/source'

export async function getSources(): Promise<Source[]> {
  return api.get<Source[]>('/sources')
}

export async function getSource(id: number): Promise<Source> {
  return api.get<Source>(`/sources/${id}`)
}

export interface CreateSourceData {
  name: string
  url: string
  fetch_interval?: number
  is_active?: boolean
}

export async function createSource(data: CreateSourceData): Promise<Source> {
  return api.post<Source>('/sources', data)
}

export async function updateSource(id: number, data: Partial<CreateSourceData>): Promise<Source> {
  return api.put<Source>(`/sources/${id}`, data)
}

export async function deleteSource(id: number): Promise<void> {
  return api.delete(`/sources/${id}`)
}

export async function refreshSource(id: number): Promise<void> {
  return api.post(`/sources/${id}/refresh`)
}

export async function refreshAllSources(): Promise<void> {
  return api.post('/sources/refresh')
}