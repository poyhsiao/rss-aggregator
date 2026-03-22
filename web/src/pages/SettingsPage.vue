<script setup lang="ts">
import { FolderOpen, RefreshCw, Upload } from 'lucide-vue-next'
import { useSettingsStore } from '@/stores/settings'
import { getPlatformFeatures } from '@/utils/environment'
import { openDataFolder, restartBackend, importData } from '@/utils/tauri-bridge'
import { useToast } from '@/composables/useToast'

const settingsStore = useSettingsStore()
const { showDesktopFeatures } = getPlatformFeatures()
const toast = useToast()

async function handleOpenDataFolder() {
  try {
    await openDataFolder()
  } catch (error) {
    toast.error(String(error))
  }
}

async function handleRestartBackend() {
  try {
    await restartBackend()
    toast.success('Backend restarted successfully')
  } catch (error) {
    toast.error(String(error))
  }
}

async function handleImportData(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (file) {
    try {
      const path = (file as unknown as { path?: string }).path
      if (path) {
        await importData(path)
        toast.success('Data imported successfully')
      }
    } catch (error) {
      toast.error(String(error))
    }
  }
  input.value = ''
}
</script>

<template>
  <div class="p-6 space-y-6">
    <h1 class="text-2xl font-bold">Settings</h1>

    <div class="space-y-4">
      <div>
        <label class="block text-sm font-medium mb-2">Theme</label>
        <select
          v-model="settingsStore.theme"
          class="w-full px-3 py-2 border rounded-md"
        >
          <option value="light">Light</option>
          <option value="dark">Dark</option>
          <option value="system">System</option>
        </select>
      </div>

      <div>
        <label class="block text-sm font-medium mb-2">Language</label>
        <select
          v-model="settingsStore.locale"
          class="w-full px-3 py-2 border rounded-md"
        >
          <option value="zh">中文</option>
          <option value="en">English</option>
        </select>
      </div>
    </div>

    <div v-if="showDesktopFeatures" class="space-y-4 pt-4 border-t">
      <h2 class="text-lg font-semibold">Desktop Settings</h2>

      <div class="grid gap-3">
        <button
          class="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90"
          @click="handleOpenDataFolder"
        >
          <FolderOpen class="w-4 h-4" />
          Open Data Folder
        </button>

        <button
          class="flex items-center gap-2 px-4 py-2 bg-secondary text-secondary-foreground rounded-md hover:bg-secondary/80"
          @click="handleRestartBackend"
        >
          <RefreshCw class="w-4 h-4" />
          Restart Backend
        </button>

        <label class="flex items-center gap-2 px-4 py-2 bg-secondary text-secondary-foreground rounded-md hover:bg-secondary/80 cursor-pointer">
          <Upload class="w-4 h-4" />
          Import Database
          <input
            type="file"
            accept=".db"
            class="hidden"
            @change="handleImportData"
          />
        </label>
      </div>
    </div>
  </div>
</template>