/**
 * Types for backup and restore functionality.
 */

export interface BackupConfig {
  timezone: string
  language: string
}

export interface BackupCounts {
  sources: number
  feed_items: number
  api_keys: number
  preview_contents: number
  fetch_batches: number
  fetch_logs: number
  stats: number
}

export interface ExportOptions {
  include_feed_items?: boolean
  include_preview_contents?: boolean
  include_logs?: boolean
}

export interface ImportSummary {
  sources_imported: number
  sources_merged: number
  feed_items_imported: number
  api_keys_imported: number
}

export interface ImportResult {
  success: boolean
  message: string
  summary?: ImportSummary
}

export interface BackupPreview {
  version: string
  exported_at: string
  counts: BackupCounts
  config: BackupConfig
}