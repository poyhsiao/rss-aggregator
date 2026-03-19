import api from '.'
import type { Stats } from '@/types/stats'

export async function getStats(days: number = 7): Promise<Stats[]> {
  const { data } = await api.get('/stats', { params: { days } })
  return data
}