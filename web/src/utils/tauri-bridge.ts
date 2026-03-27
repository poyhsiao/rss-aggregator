import { invoke } from '@tauri-apps/api/core'
import { isTauri } from './environment'

export interface SetupConfig {
  timezone: string
  language: string
}

export interface Config {
  version: string
  setup_completed_at: string | null
  timezone: string
  language: string
  last_run_at: string | null
}

export async function openDataFolder(): Promise<void> {
  if (!isTauri()) {
    throw new Error('This feature is only available in desktop mode')
  }
  await invoke('open_data_folder')
}

export async function exportData(): Promise<string> {
  if (!isTauri()) {
    throw new Error('This feature is only available in desktop mode')
  }
  return await invoke<string>('export_data')
}

export async function importData(sourcePath: string): Promise<void> {
  if (!isTauri()) {
    throw new Error('This feature is only available in desktop mode')
  }
  await invoke('import_data', { sourcePath })
}

export async function restartBackend(): Promise<void> {
  if (!isTauri()) {
    throw new Error('This feature is only available in desktop mode')
  }
  await invoke('restart_backend')
}

export async function getAppVersion(): Promise<string> {
  if (!isTauri()) {
    return import.meta.env.VITE_APP_VERSION || '0.0.0'
  }
  return await invoke<string>('get_app_version')
}

export async function getDataPath(): Promise<string> {
  if (!isTauri()) {
    throw new Error('This feature is only available in desktop mode')
  }
  return await invoke<string>('get_data_path')
}

export async function isFirstRun(): Promise<boolean> {
  if (!isTauri()) {
    return false
  }
  return await invoke<boolean>('is_first_run')
}

export async function getSetupConfig(): Promise<Config> {
  if (!isTauri()) {
    throw new Error('This feature is only available in desktop mode')
  }
  return await invoke<Config>('get_setup_config')
}

export async function saveSetupConfig(config: SetupConfig): Promise<void> {
  if (!isTauri()) {
    throw new Error('This feature is only available in desktop mode')
  }
  await invoke('save_setup_config', { config })
}

export async function completeSetup(): Promise<void> {
  if (!isTauri()) {
    throw new Error('This feature is only available in desktop mode')
  }
  await invoke('complete_setup')
}

export interface ExportOptions {
  include_feed_items?: boolean
  include_preview_contents?: boolean
  include_logs?: boolean
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

export interface BackupConfig {
  timezone: string
  language: string
}

export interface BackupPreview {
  version: string
  exported_at: string
  counts: BackupCounts
  config: BackupConfig
}

export interface PreviewBackupResult {
  filePath: string
  preview: BackupPreview
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

export interface ExportBackupResult {
  filename: string
}

export async function exportBackup(options?: ExportOptions): Promise<ExportBackupResult> {
  if (!isTauri()) {
    throw new Error('This feature is only available in desktop mode')
  }
  return await invoke<ExportBackupResult>('export_backup', { options })
}

export async function importBackup(): Promise<ImportResult> {
  if (!isTauri()) {
    throw new Error('This feature is only available in desktop mode')
  }
  return await invoke<ImportResult>('import_backup')
}

export async function importBackupWithPath(filePath: string): Promise<ImportResult> {
  if (!isTauri()) {
    throw new Error('This feature is only available in desktop mode')
  }
  return await invoke<ImportResult>('import_backup_with_path', { filePath })
}

export async function previewBackup(): Promise<PreviewBackupResult | null> {
  if (!isTauri()) {
    throw new Error('This feature is only available in desktop mode')
  }
  const result = await invoke<[string, BackupPreview] | null>('preview_backup')
  if (result) {
    return {
      filePath: result[0],
      preview: result[1]
    }
  }
  return null
}