import api from '.'
import type { FeatureFlags } from '@/types/feature-flags'

export async function getFeatureFlags(): Promise<FeatureFlags> {
  return api.get<FeatureFlags>('/feature-flags')
}

export async function updateFeatureFlags(
  flags: Partial<FeatureFlags>
): Promise<FeatureFlags> {
  return api.put<FeatureFlags>('/feature-flags', flags)
}