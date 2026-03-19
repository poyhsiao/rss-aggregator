export interface ApiKey {
  id: number
  key: string
  name: string | null
  is_active: boolean
  created_at: string
  updated_at: string
}