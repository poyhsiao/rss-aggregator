import api from '.'
import type { Source } from '@/types/source'

export async function getSources(): Promise<Source[]> {
  const { data } = await api.get('/sources')
  return data
}

export async function getSource(id: number): Promise<Source> {
  const { data } = await api.get(`/sources/${id}`)
  return data
}

export interface CreateSourceData {
  name: string
  url: string
  fetch_interval?: number
  is_active?: boolean
}

export async function createSource(data: CreateSourceData): Promise<Source> {
  const { data: result } = await api.post('/sources', data)
  return result
}

export async function updateSource(id: number, data: Partial<CreateSourceData>): Promise<Source> {
  const { data: result } = await api.put(`/sources/${id}`, data)
  return result
}

export async function deleteSource(id: number): Promise<void> {
  await api.delete(`/sources/${id}`)
}

export async function refreshSource(id: number): Promise<void> {
  await api.post(`/sources/${id}/refresh`)
}

export async function refreshAllSources(): Promise<void> {
  await api.post('/sources/refresh')
}