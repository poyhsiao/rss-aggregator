export function isTauri(): boolean {
  return typeof window !== 'undefined' && '__TAURI__' in window
}

export type Environment = 'web' | 'tauri'

export function getEnvironment(): Environment {
  return isTauri() ? 'tauri' : 'web'
}

export interface PlatformFeatures {
  showDesktopFeatures: boolean
  canOpenFolder: boolean
  canExportImport: boolean
  canRestartBackend: boolean
}

export function getPlatformFeatures(): PlatformFeatures {
  if (isTauri()) {
    return {
      showDesktopFeatures: true,
      canOpenFolder: true,
      canExportImport: true,
      canRestartBackend: true,
    }
  }
  return {
    showDesktopFeatures: false,
    canOpenFolder: false,
    canExportImport: false,
    canRestartBackend: false,
  }
}