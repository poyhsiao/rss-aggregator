<script setup lang="ts">
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { Download, Upload, FileArchive, Check, X, Loader2, RefreshCw } from 'lucide-vue-next'
import Dialog from '@/components/ui/Dialog.vue'
import Button from '@/components/ui/Button.vue'
import { exportBackup as exportBackupApi, importBackup as importBackupApi, previewBackup as previewBackupApi, downloadBlob } from '@/api/backup'
import { exportBackup as exportBackupTauri, previewBackup as previewBackupTauri, importBackupWithPath, restartBackend } from '@/utils/tauri-bridge'
import { isTauri } from '@/utils/environment'
import { useToast } from '@/composables/useToast'
import type { BackupPreview, ExportOptions, ImportResult } from '@/types/backup'

const { t } = useI18n()
const toast = useToast()

const isDesktop = computed(() => isTauri())

const exportLoading = ref(false)
const importLoading = ref(false)
const previewLoading = ref(false)
const previewData = ref<BackupPreview | null>(null)
const showImportConfirm = ref(false)
const showRestartDialog = ref(false)
const selectedFile = ref<File | null>(null)
const selectedFilePath = ref<string | null>(null)

const exportOptions = ref<ExportOptions>({
  include_feed_items: true,
  include_preview_contents: true,
  include_logs: false,
})

const hasFile = computed(() => selectedFile.value !== null || selectedFilePath.value !== null)

async function handleExport(): Promise<void> {
  exportLoading.value = true
  try {
    if (isDesktop.value) {
      await exportBackupTauri(exportOptions.value)
      toast.success(t('backup.export.success'))
    } else {
      const blob = await exportBackupApi(exportOptions.value)
      const now = new Date()
      const dateStr = now.toISOString().split('T')[0]
      const filename = `rss-backup-${dateStr}.zip`
      downloadBlob(blob, filename)
      toast.success(t('backup.export.success'))
    }
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : String(error)
    if (errorMessage !== 'No file selected') {
      toast.error(t('backup.export.failed'))
    }
  } finally {
    exportLoading.value = false
  }
}

async function handleFileSelect(event: Event): Promise<void> {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return

  selectedFile.value = file
  selectedFilePath.value = null
  previewLoading.value = true
  previewData.value = null

  try {
    const arrayBuffer = await file.arrayBuffer()
    const preview = await previewBackupApi(arrayBuffer)
    previewData.value = preview
  } catch {
    toast.error(t('backup.import.preview_failed'))
    selectedFile.value = null
  } finally {
    previewLoading.value = false
  }

  input.value = ''
}

async function handleDesktopImport(): Promise<void> {
  previewLoading.value = true
  previewData.value = null
  selectedFile.value = null
  selectedFilePath.value = null

  try {
    const result = await previewBackupTauri()
    if (result && result.preview) {
      previewData.value = result.preview
      selectedFilePath.value = result.filePath ?? null
    }
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : String(error)
    if (!errorMessage.includes('No file selected')) {
      toast.error(t('backup.import.preview_failed'))
    }
  } finally {
    previewLoading.value = false
  }
}

function handleImportClick(): void {
  if (!previewData.value) return
  showImportConfirm.value = true
}

async function confirmImport(): Promise<void> {
  importLoading.value = true
  showImportConfirm.value = false

  try {
    let result: ImportResult

    if (isDesktop.value && selectedFilePath.value) {
      result = await importBackupWithPath(selectedFilePath.value)
    } else if (selectedFile.value) {
      const arrayBuffer = await selectedFile.value.arrayBuffer()
      result = await importBackupApi(arrayBuffer)
    } else {
      return
    }

    if (result.success) {
      toast.success(t('backup.import.success'))
      selectedFile.value = null
      selectedFilePath.value = null
      previewData.value = null
      
      // Show restart dialog for desktop app
      if (isDesktop.value) {
        showRestartDialog.value = true
      }
    } else {
      toast.error(result.message || t('backup.import.failed'))
    }
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : String(error)
    toast.error(errorMessage || t('backup.import.failed'))
  } finally {
    importLoading.value = false
  }
}

function cancelImport(): void {
  showImportConfirm.value = false
}

async function handleRestartBackend(): Promise<void> {
  try {
    await restartBackend()
    toast.success(t('settings.desktop.restart_success'))
    showRestartDialog.value = false
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : String(error)
    toast.error(errorMessage)
  }
}

function clearFile(): void {
  selectedFile.value = null
  selectedFilePath.value = null
  previewData.value = null
}

function formatDate(isoString: string): string {
  return new Date(isoString).toLocaleString()
}
</script>

<template>
  <div class="space-y-6">
    <div>
      <h2 class="text-lg font-semibold mb-2">{{ t('backup.export.title') }}</h2>
      <p class="text-sm text-neutral-600 dark:text-neutral-400 mb-4">
        {{ t('backup.export.description') }}
      </p>

      <div class="space-y-3 mb-4 p-4 bg-neutral-50 dark:bg-neutral-800 rounded-lg">
        <h3 class="text-sm font-medium">{{ t('backup.export.options') }}</h3>
        <label class="flex items-center gap-2 cursor-pointer">
          <input
            v-model="exportOptions.include_feed_items"
            type="checkbox"
            class="rounded border-neutral-300 text-primary-600 focus:ring-primary-500"
          />
          <span class="text-sm">{{ t('backup.export.include_feed_items') }}</span>
        </label>
        <label class="flex items-center gap-2 cursor-pointer">
          <input
            v-model="exportOptions.include_preview_contents"
            type="checkbox"
            class="rounded border-neutral-300 text-primary-600 focus:ring-primary-500"
          />
          <span class="text-sm">{{ t('backup.export.include_preview_contents') }}</span>
        </label>
        <label class="flex items-center gap-2 cursor-pointer">
          <input
            v-model="exportOptions.include_logs"
            type="checkbox"
            class="rounded border-neutral-300 text-primary-600 focus:ring-primary-500"
          />
          <span class="text-sm">{{ t('backup.export.include_logs') }}</span>
        </label>
      </div>

      <Button
        :disabled="exportLoading"
        @click="handleExport"
      >
        <Loader2 v-if="exportLoading" class="w-4 h-4 animate-spin" />
        <Download v-else class="w-4 h-4" />
        {{ exportLoading ? t('backup.loading') : t('backup.export.button') }}
      </Button>
    </div>

    <hr class="border-neutral-200 dark:border-neutral-700" />

    <div>
      <h2 class="text-lg font-semibold mb-2">{{ t('backup.import.title') }}</h2>
      <p class="text-sm text-neutral-600 dark:text-neutral-400 mb-4">
        {{ t('backup.import.description') }}
      </p>

      <div class="space-y-4">
        <template v-if="isDesktop">
          <Button
            :disabled="previewLoading"
            @click="handleDesktopImport"
          >
            <Upload class="w-4 h-4" />
            {{ t('backup.import.select_file') }}
          </Button>
        </template>
        <template v-else>
          <label class="block">
            <div
              class="border-2 border-dashed border-neutral-300 dark:border-neutral-600 rounded-lg p-6 text-center cursor-pointer hover:border-primary-500 transition-colors"
              :class="{ 'border-primary-500 bg-primary-50 dark:bg-primary-900/20': hasFile }"
            >
              <FileArchive v-if="hasFile" class="w-8 h-8 mx-auto mb-2 text-primary-600" />
              <Upload v-else class="w-8 h-8 mx-auto mb-2 text-neutral-400" />
              <p class="text-sm text-neutral-600 dark:text-neutral-400">
                {{ hasFile ? selectedFile?.name : t('backup.import.select_file') }}
              </p>
            </div>
            <input
              type="file"
              accept=".zip"
              class="hidden"
              @change="handleFileSelect"
            />
          </label>
        </template>

        <div v-if="previewLoading" class="flex items-center justify-center py-4">
          <Loader2 class="w-6 h-6 animate-spin text-primary-600" />
          <span class="ml-2 text-sm">{{ t('backup.loading') }}</span>
        </div>

        <div v-if="previewData && !previewLoading" class="p-4 bg-neutral-50 dark:bg-neutral-800 rounded-lg space-y-3">
          <h3 class="font-medium">{{ t('backup.import.preview_title') }}</h3>

          <div class="grid grid-cols-2 gap-2 text-sm">
            <span class="text-neutral-600 dark:text-neutral-400">{{ t('backup.version') }}:</span>
            <span>{{ previewData.version }}</span>

            <span class="text-neutral-600 dark:text-neutral-400">{{ t('backup.exported_at') }}:</span>
            <span>{{ formatDate(previewData.exported_at) }}</span>
          </div>

          <div class="border-t border-neutral-200 dark:border-neutral-700 pt-3 mt-3">
            <h4 class="text-sm font-medium mb-2">{{ t('backup.counts.sources') }}</h4>
            <div class="grid grid-cols-2 gap-2 text-sm">
              <span class="text-neutral-600 dark:text-neutral-400">{{ t('backup.counts.sources') }}:</span>
              <span>{{ previewData.counts.sources }}</span>

              <span class="text-neutral-600 dark:text-neutral-400">{{ t('backup.counts.feed_items') }}:</span>
              <span>{{ previewData.counts.feed_items }}</span>

              <span class="text-neutral-600 dark:text-neutral-400">{{ t('backup.counts.api_keys') }}:</span>
              <span>{{ previewData.counts.api_keys }}</span>

              <span class="text-neutral-600 dark:text-neutral-400">{{ t('backup.counts.preview_contents') }}:</span>
              <span>{{ previewData.counts.preview_contents }}</span>
            </div>
          </div>

          <div class="flex gap-2 pt-2">
            <Button
              :disabled="importLoading"
              @click="handleImportClick"
            >
              <Check class="w-4 h-4" />
              {{ t('backup.import.button') }}
            </Button>
            <Button variant="outline" @click="clearFile">
              <X class="w-4 h-4" />
              {{ t('common.cancel') }}
            </Button>
          </div>
        </div>
      </div>
    </div>

    <Dialog :open="showImportConfirm" @update:open="showImportConfirm = $event">
      <div class="p-6">
        <h2 class="text-xl font-semibold mb-4">{{ t('backup.import.confirm_title') }}</h2>
        <p class="text-sm text-neutral-600 dark:text-neutral-400 mb-6">
          {{ t('backup.import.confirm_description') }}
        </p>
        <div class="flex justify-end gap-2">
          <Button variant="outline" @click="cancelImport">
            {{ t('common.cancel') }}
          </Button>
          <Button @click="confirmImport">
            {{ t('common.confirm') }}
          </Button>
        </div>
      </div>
    </Dialog>

    <Dialog :open="showRestartDialog" @update:open="showRestartDialog = $event">
      <div class="p-6">
        <h2 class="text-xl font-semibold mb-4">{{ t('backup.import.restart_title') }}</h2>
        <p class="text-sm text-neutral-600 dark:text-neutral-400 mb-6">
          {{ t('backup.import.restart_description') }}
        </p>
        <div class="flex justify-end gap-2">
          <Button variant="outline" @click="showRestartDialog = false">
            {{ t('common.cancel') }}
          </Button>
          <Button @click="handleRestartBackend">
            <RefreshCw class="w-4 h-4 mr-2" />
            {{ t('settings.desktop.restart') }}
          </Button>
        </div>
      </div>
    </Dialog>
  </div>
</template>