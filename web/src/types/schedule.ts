export interface Schedule {
  id: number
  group_id: number
  cron_expression: string
  is_enabled: boolean
  next_run_at: string | null
  created_at: string
  updated_at: string
}

export interface ScheduleCreate {
  cron_expression: string
}