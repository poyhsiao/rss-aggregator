import api from '.'
import type { Source } from '@/types/source'

export interface TrashItem extends Source {
  deleted_at: string
}

export interface RestoreConflict {
  conflict: true
  existing_source: Source
  trash_source: TrashItem
}

export interface RestoreSuccess {
  conflict: false
  source: Source
}

export type RestoreResult = RestoreConflict | RestoreSuccess

export async function getTrashItems(): Promise<TrashItem[]> {
  return api.get<TrashItem[]>('/trash')
}

export async function restoreSource(
  id: number,
  overwrite?: boolean
): Promise<RestoreResult> {
  if (overwrite) {
    return api.post<RestoreResult>(`/trash/${id}/restore?overwrite=true`)
  }
  return api.post<RestoreResult>(`/trash/${id}/restore`)
}

export async function permanentDeleteSource(id: number): Promise<void> {
  return api.post(`/trash/${id}/permanent-delete`)
}

export async function clearTrash(): Promise<{ deleted_count: number }> {
  return api.delete<{ deleted_count: number }>('/trash/clear')
}