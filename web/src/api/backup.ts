import api from '.'
import type { BackupPreview, ExportOptions, ImportResult } from '@/types/backup'

export async function exportBackup(options?: ExportOptions): Promise<Blob> {
  return api.postBlob('/backup/export', options)
}

export async function importBackup(zipData: ArrayBuffer): Promise<ImportResult> {
  return api.postBinary<ImportResult>('/backup/import', zipData)
}

export async function previewBackup(zipData: ArrayBuffer): Promise<BackupPreview | null> {
  return api.postBinary<BackupPreview | null>('/backup/preview', zipData)
}

export function downloadBlob(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}