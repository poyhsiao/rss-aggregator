import api from '.'
import type { Schedule } from '@/types/schedule'

export async function getSchedules(groupId: number): Promise<Schedule[]> {
  return api.get<Schedule[]>(`/source-groups/${groupId}/schedules`)
}

export async function createSchedule(groupId: number, data: { cron_expression: string }): Promise<Schedule> {
  return api.post<Schedule>(`/source-groups/${groupId}/schedules`, data)
}

export async function updateSchedule(groupId: number, scheduleId: number, data: { cron_expression: string }): Promise<Schedule> {
  return api.put<Schedule>(`/source-groups/${groupId}/schedules/${scheduleId}`, data)
}

export async function deleteSchedule(groupId: number, scheduleId: number): Promise<void> {
  return api.delete(`/source-groups/${groupId}/schedules/${scheduleId}`)
}

export async function toggleSchedule(groupId: number, scheduleId: number): Promise<Schedule> {
  return api.patch<Schedule>(`/source-groups/${groupId}/schedules/${scheduleId}/toggle`)
}