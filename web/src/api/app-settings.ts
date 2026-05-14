import api from '.'
import type { AppSettingsResponse } from '@/types/app-settings'

export async function getAppSettings(): Promise<AppSettingsResponse> {
  return api.get<AppSettingsResponse>('/settings')
}

export async function updateAppSettings(
  data: Partial<AppSettingsResponse>
): Promise<AppSettingsResponse> {
  return api.put<AppSettingsResponse>('/settings', data)
}
