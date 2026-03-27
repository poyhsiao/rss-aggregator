import api from '.'
import type { Source } from '@/types/source'
import axios from 'axios'

export interface TrashItem extends Source {
  deleted_at: string
}

export interface ConflictDetail {
  trash_item: {
    id: number
    name: string
    url: string
  }
  existing_item: {
    id: number
    name: string
    url: string
  }
  conflict_type: string
}

export interface RestoreConflict {
  conflict: true
  existing_source: Source
  trash_source: TrashItem
  conflict_type: string
}

export interface RestoreSuccess {
  conflict: false
  source: Source
}

export type RestoreResult = RestoreConflict | RestoreSuccess

export class RestoreConflictError extends Error {
  detail: ConflictDetail

  constructor(detail: ConflictDetail) {
    super('Conflict detected')
    this.name = 'RestoreConflictError'
    this.detail = detail
  }
}

export async function getTrashItems(): Promise<TrashItem[]> {
  return api.get<TrashItem[]>('/trash')
}

export async function restoreSource(
  id: number,
  overwrite?: boolean
): Promise<RestoreResult> {
  try {
    let body: { conflict_resolution?: string } | undefined
    if (overwrite === true) {
      body = { conflict_resolution: 'overwrite' }
    } else if (overwrite === false) {
      body = { conflict_resolution: 'keep_existing' }
    }
    
    const result = await api.post<{ id: number; name: string; restored: boolean }>(
      `/trash/${id}/restore`,
      body
    )
    return {
      conflict: false,
      source: { id: result.id, name: result.name } as Source,
    }
  } catch (error) {
    if (axios.isAxiosError(error) && error.response?.status === 409) {
      const detail = error.response.data.detail as { conflict: ConflictDetail }
      throw new RestoreConflictError(detail.conflict)
    }
    throw error
  }
}

export async function permanentDeleteSource(id: number): Promise<void> {
  return api.delete(`/trash/${id}`)
}

export async function clearTrash(): Promise<{ deleted_count: number }> {
  return api.delete<{ deleted_count: number }>('/trash')
}