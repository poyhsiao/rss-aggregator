export interface FeedItem {
  id: number
  title: string
  link: string
  description: string
  source: string
  published_at: string | null
  source_groups?: { id: number; name: string }[]
}