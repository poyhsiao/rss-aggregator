import type { Environment, PlatformFeatures } from '@/utils/environment'

declare module '@/utils/environment' {
  export function isTauri(): boolean
  export function getEnvironment(): Environment
  export function getPlatformFeatures(): PlatformFeatures
}

interface Window {
  __TAURI__?: unknown
}