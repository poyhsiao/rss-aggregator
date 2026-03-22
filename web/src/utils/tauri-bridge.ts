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