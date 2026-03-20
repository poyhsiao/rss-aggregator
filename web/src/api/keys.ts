import api from '.'
import type { ApiKey } from '@/types/key'

export async function getKeys(): Promise<ApiKey[]> {
  const { data } = await api.get('/keys')
  return data
}

export interface CreateKeyData {
  name?: string
  key?: string
}

export async function createKey(data?: CreateKeyData): Promise<ApiKey> {
  const { data: result } = await api.post('/keys', data)
  return result
}

export async function deleteKey(id: number): Promise<void> {
  await api.delete(`/keys/${id}`)
}