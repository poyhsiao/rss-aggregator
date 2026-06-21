import api from '.'

export interface FeatureFlags {
  groups_enabled: boolean
  schedule_enabled: boolean
  source_group_schedules_enabled: boolean
  share_enabled: boolean
}

export async function getFeatureFlags(): Promise<FeatureFlags> {
  return api.get<FeatureFlags>('/feature-flags')
}

export async function updateFeatureFlags(
  flags: Partial<FeatureFlags>
): Promise<FeatureFlags> {
  return api.put<FeatureFlags>('/feature-flags', flags)
}