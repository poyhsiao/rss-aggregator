import api from '.'
import type { Stats } from '@/types/stats'

export async function getStats(days: number = 7): Promise<Stats[]> {
  return api.get<Stats[]>(`/stats?days=${days}`)
}