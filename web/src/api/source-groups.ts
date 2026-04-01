import api from '.'
import type { SourceGroup } from '@/types/source-group'
import type { Source } from '@/types/source'

export async function getGroups(): Promise<SourceGroup[]> {
  return api.get<SourceGroup[]>('/source-groups')
}

export async function createGroup(data: { name: string }): Promise<SourceGroup> {
  return api.post<SourceGroup>('/source-groups', data)
}

export async function updateGroup(id: number, data: { name: string }): Promise<SourceGroup> {
  return api.put<SourceGroup>(`/source-groups/${id}`, data)
}

export async function deleteGroup(id: number): Promise<void> {
  return api.delete(`/source-groups/${id}`)
}

export async function getGroupSources(id: number): Promise<Source[]> {
  return api.get<Source[]>(`/source-groups/${id}/sources`)
}

export async function addSourceToGroup(groupId: number, sourceId: number): Promise<void> {
  return api.post(`/source-groups/${groupId}/sources`, { source_id: sourceId })
}

export async function removeSourceFromGroup(groupId: number, sourceId: number): Promise<void> {
  return api.delete(`/source-groups/${groupId}/sources/${sourceId}`)
}
