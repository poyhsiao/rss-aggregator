import api from '.'
import type { ApiKey } from '@/types/key'

export async function getKeys(): Promise<ApiKey[]> {
  return api.get<ApiKey[]>('/keys')
}

export interface CreateKeyData {
  name?: string
  key?: string
}

export async function createKey(data?: CreateKeyData): Promise<ApiKey> {
  return api.post<ApiKey>('/keys', data)
}

export async function deleteKey(id: number): Promise<void> {
  return api.delete(`/keys/${id}`)
}