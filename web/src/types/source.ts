export interface Source {
  id: number
  name: string
  url: string
  is_active: boolean
  last_fetched_at: string | null
  last_error: string | null
  created_at: string
  updated_at: string
  groups: { id: number; name: string }[]
}