<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { RefreshCw, Copy, Check, Trash2, Key, BarChart3, Settings, Plus, Inbox, FileText } from 'lucide-vue-next'
import { getPlatformFeatures } from '@/utils/environment'
import { restartBackend } from '@/utils/tauri-bridge'
import { useToast } from '@/composables/useToast'
import { useConfirm } from '@/composables/useConfirm'
import BackupManager from '@/components/BackupManager.vue'
import FeatureSettingsDialog from '@/components/FeatureSettingsDialog.vue'

// API Keys
import { getKeys, deleteKey } from '@/api/keys'
import type { ApiKey } from '@/types/key'
import Button from '@/components/ui/Button.vue'
import Badge from '@/components/ui/Badge.vue'
import KeyDialog from '@/components/KeyDialog.vue'
import ConfirmDialog from '@/components/ui/ConfirmDialog.vue'

// Statistics
import { getStats } from '@/api/stats'
import type { Stats } from '@/types/stats'
import Card from '@/components/ui/Card.vue'
import StatsChart from '@/components/StatsChart.vue'

// Logs
import { getLogs } from '@/api/logs'
import { useLogStore } from '@/stores/log'
import LogCard from '@/components/LogCard.vue'
import type { ErrorLog } from '@/types/log'

// Previews
import { clearAllPreviews } from '@/api/preview'

const { t } = useI18n()
const route = useRoute()
const { showDesktopFeatures } = getPlatformFeatures()
const toast = useToast()
const confirm = useConfirm()

// Feature settings 10-click easter egg (Settings page only)
const featureDialogOpen = ref(false)
const featureClickCount = ref(0)
const featureClickTimer = ref<ReturnType<typeof setTimeout> | null>(null)

function handleFeedIconClick(): void {
  // Only activate on Settings page
  if (route.path !== '/settings') return

  if (featureClickTimer.value) clearTimeout(featureClickTimer.value)
  featureClickCount.value++
  featureClickTimer.value = setTimeout(() => { featureClickCount.value = 0 }, 2000)
  if (featureClickCount.value >= 10) {
    featureDialogOpen.value = true
    featureClickCount.value = 0
  }
}

// Main tabs
const activeTab = ref<'keys' | 'stats' | 'settings'>('keys')

function initializeTab(): void {
  const tabParam = route.query.tab as string
  if (tabParam === 'keys' || tabParam === 'stats' || tabParam === 'settings') {
    activeTab.value = tabParam
  }
}

const mainTabs = computed(() => [
  { id: 'keys' as const, label: t('keys.title'), icon: Key },
  { id: 'stats' as const, label: t('stats.title'), icon: BarChart3 },
  { id: 'settings' as const, label: t('common.system'), icon: Settings },
])

// ==================== API Keys ====================
const keys = ref<ApiKey[]>([])
const keysLoading = ref(true)
const showKeyDialog = ref(false)
const copiedKeyId = ref<number | null>(null)

async function fetchKeys(): Promise<void> {
  keysLoading.value = true
  try {
    keys.value = await getKeys()
  } finally {
    keysLoading.value = false
  }
}

function handleKeyCreated(key: ApiKey): void {
  keys.value.unshift(key)
}

async function copyToClipboard(text: string, id: number): Promise<void> {
  try {
    await navigator.clipboard.writeText(text)
    copiedKeyId.value = id
    toast.success(t('keys.copied'))
    setTimeout(() => {
      copiedKeyId.value = null
    }, 2000)
  } catch {
    toast.error(t('keys.copy_failed'))
  }
}

async function handleDeleteKey(id: number): Promise<void> {
  const confirmed = await confirm.show({
    title: t('keys.delete_title'),
    message: t('keys.delete_confirm'),
    confirmText: t('common.delete'),
    cancelText: t('common.cancel'),
    variant: 'danger'
  })
  if (!confirmed) return

  try {
    await deleteKey(id)
    keys.value = keys.value.filter(k => k.id !== id)
    toast.success(t('keys.deleted'))
  } catch {
    toast.error(t('common.error'))
  }
}

// ==================== Statistics ====================
const stats = ref<Stats[]>([])
const statsLoading = ref(true)
const logsTab = ref<'system' | 'operation'>('system')
const systemLogs = ref<ErrorLog[]>([])
const logsLoading = ref(true)
const logStore = useLogStore()

const totalRequests = computed(() => stats.value.reduce((sum, s) => sum + s.total_requests, 0))
const successfulFetches = computed(() => stats.value.reduce((sum, s) => sum + s.successful_fetches, 0))
const failedFetches = computed(() => stats.value.reduce((sum, s) => sum + s.failed_fetches, 0))

async function fetchStats(): Promise<void> {
  statsLoading.value = true
  try {
    stats.value = await getStats(7)
  } finally {
    statsLoading.value = false
  }
}

async function fetchSystemLogs(): Promise<void> {
  logsLoading.value = true
  try {
    const result = await getLogs({ limit: 100 })
    systemLogs.value = result
  } catch (error) {
    console.error('[SettingsPage] Error fetching logs:', error)
  } finally {
    logsLoading.value = false
  }
}

// ==================== Settings ====================
async function handleRestartBackend(): Promise<void> {
  try {
    await restartBackend()
    toast.success(t('settings.desktop.restart_success'))
  } catch (error) {
    toast.error(t('common.error'))
  }
}

async function handleClearPreviews(): Promise<void> {
  const confirmed = await confirm.show({
    title: t('settings.clear_previews.confirm_title'),
    message: t('settings.clear_previews.confirm_message'),
    confirmText: t('common.confirm'),
    cancelText: t('common.cancel'),
    variant: 'danger'
  })
  if (!confirmed) return

  try {
    await clearAllPreviews()
    toast.success(t('settings.clear_previews.success'))
  } catch {
    toast.error(t('common.error'))
  }
}

// Initialize
onMounted(() => {
  initializeTab()
  fetchKeys()
  fetchStats()
  fetchSystemLogs()
})
</script>

<template>
  <div class="space-y-6">
    <h1 class="text-2xl font-bold cursor-pointer select-none" @click="handleFeedIconClick">
      {{ t('common.settings') }}
    </h1>

    <!-- Main Tabs -->
    <div class="flex gap-2 border-b border-neutral-200 dark:border-neutral-700">
      <button
        v-for="tab in mainTabs"
        :key="tab.id"
        type="button"
        class="px-4 py-2 text-sm font-medium transition-colors relative flex items-center gap-2"
        :class="[
          activeTab === tab.id
            ? 'text-blue-600 dark:text-blue-400'
            : 'text-neutral-500 hover:text-neutral-700 dark:text-neutral-400 dark:hover:text-neutral-300'
        ]"
        @click="activeTab = tab.id"
      >
        <component :is="tab.icon" class="w-4 h-4" />
        {{ tab.label }}
        <span
          v-if="activeTab === tab.id"
          class="absolute bottom-0 left-0 right-0 h-0.5 bg-blue-600 dark:bg-blue-400"
        />
      </button>
    </div>

    <!-- ==================== API Keys Tab ==================== -->
    <div v-if="activeTab === 'keys'" class="space-y-6">
      <div class="flex items-center justify-between">
        <h2 class="text-xl font-semibold"><Key class="h-5 w-5 inline mr-2" />{{ t('keys.title') }}</h2>
        <Button @click="showKeyDialog = true">
          <Plus class="h-4 w-4 mr-2" /> {{ t('keys.add') }}
        </Button>
      </div>

      <div v-if="keysLoading" class="text-center py-12 text-neutral-500">
        {{ t('common.loading') }}
      </div>

      <div v-else-if="!keys.length" class="text-center py-12 text-neutral-500">
        <Key class="h-5 w-5 inline mr-2" />{{ t('keys.empty') }}
      </div>

      <div v-else class="space-y-3">
        <div
          v-for="key in keys"
          :key="key.id"
          class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 p-4 bg-white dark:bg-neutral-800 rounded-lg border border-neutral-200 dark:border-neutral-700"
        >
          <div class="flex-1 min-w-0 flex items-center gap-3">
            <code class="text-sm bg-neutral-100 dark:bg-neutral-700 px-2 py-1 rounded block truncate">
              {{ key.key.slice(0, 8) }}...{{ key.key.slice(-4) }}
            </code>
            <span v-if="key.name" class="text-sm text-neutral-500 dark:text-neutral-400">
              {{ key.name }}
            </span>
          </div>
          <div class="flex items-center gap-2">
            <Badge :variant="key.is_active ? 'success' : 'secondary'">
              {{ key.is_active ? t('sources.active') : t('sources.inactive') }}
            </Badge>
            <Button
              variant="ghost"
              size="sm"
              class="gap-1"
              :title="t('keys.copy')"
              @click="copyToClipboard(key.key, key.id)"
            >
              <Check v-if="copiedKeyId === key.id" class="h-4 w-4 text-green-500" />
              <Copy v-else class="h-4 w-4" />
              {{ copiedKeyId === key.id ? t('keys.copied') : t('keys.copy') }}
            </Button>
            <Button
              variant="ghost"
              size="sm"
              class="text-red-500 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20"
              :title="t('common.delete')"
              @click="handleDeleteKey(key.id)"
            >
              <Trash2 class="h-4 w-4" />
              {{ t('common.delete') }}
            </Button>
          </div>
        </div>
      </div>

      <KeyDialog
        v-model:open="showKeyDialog"
        @created="handleKeyCreated"
      />
    </div>

    <!-- ==================== Statistics + Logs Tab ==================== -->
    <div v-if="activeTab === 'stats'" class="space-y-6">
      <!-- Statistics -->
      <div class="space-y-4">
        <h2 class="text-xl font-semibold"><BarChart3 class="h-5 w-5 inline mr-2" />{{ t('stats.title') }}</h2>

        <div v-if="statsLoading" class="text-center py-12 text-neutral-500">
          {{ t('common.loading') }}
        </div>

        <template v-else>
          <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <Card class="p-6 text-center">
              <div class="text-3xl font-bold text-blue-600">{{ totalRequests }}</div>
              <div class="text-neutral-500 mt-1">{{ t('stats.total_requests') }}</div>
            </Card>

            <Card class="p-6 text-center">
              <div class="text-3xl font-bold text-green-600">{{ successfulFetches }}</div>
              <div class="text-neutral-500 mt-1">{{ t('stats.successful_fetches') }}</div>
            </Card>

            <Card class="p-6 text-center">
              <div class="text-3xl font-bold text-red-600">{{ failedFetches }}</div>
              <div class="text-neutral-500 mt-1">{{ t('stats.failed_fetches') }}</div>
            </Card>
          </div>

          <Card class="p-6">
            <h3 class="text-lg font-medium mb-4">{{ t('stats.daily_trend') }}</h3>
            <div class="h-64">
              <StatsChart v-if="stats.length" :stats="stats" />
              <div v-else class="h-full flex items-center justify-center text-neutral-400">
                {{ t('common.loading') }}
              </div>
            </div>
          </Card>
        </template>
      </div>

      <!-- Logs -->
      <div class="space-y-4 pt-4 border-t border-neutral-200 dark:border-neutral-700">
        <h2 class="text-xl font-semibold"><FileText class="h-5 w-5 inline mr-2" />{{ t('logs.title') }}</h2>

        <!-- Logs Tabs -->
        <div class="flex gap-2 border-b border-neutral-200 dark:border-neutral-700">
          <button
            type="button"
            class="px-4 py-2 text-sm font-medium transition-colors relative"
            :class="[
              logsTab === 'system'
                ? 'text-blue-600 dark:text-blue-400'
                : 'text-neutral-500 hover:text-neutral-700 dark:text-neutral-400 dark:hover:text-neutral-300'
            ]"
            @click="logsTab = 'system'"
          >
            {{ t('logs.system_logs') }}
            <span
              v-if="logsTab === 'system'"
              class="absolute bottom-0 left-0 right-0 h-0.5 bg-blue-600 dark:bg-blue-400"
            />
          </button>
          <button
            type="button"
            class="px-4 py-2 text-sm font-medium transition-colors relative"
            :class="[
              logsTab === 'operation'
                ? 'text-blue-600 dark:text-blue-400'
                : 'text-neutral-500 hover:text-neutral-700 dark:text-neutral-400 dark:hover:text-neutral-300'
            ]"
            @click="logsTab = 'operation'"
          >
            {{ t('logs.operation_logs') }}
            <span
              v-if="logsTab === 'operation'"
              class="absolute bottom-0 left-0 right-0 h-0.5 bg-blue-600 dark:bg-blue-400"
            />
          </button>
        </div>

        <!-- System Logs -->
        <div v-if="logsTab === 'system'">
          <div v-if="logsLoading" class="text-center py-12 text-neutral-500">
            {{ t('common.loading') }}
          </div>

          <div v-else-if="!systemLogs.length" class="text-center py-12 text-neutral-500">
            <Inbox class="h-6 w-6 mx-auto mb-3 text-neutral-400" />
            {{ t('logs.empty') }}
          </div>

          <div v-else class="space-y-2">
            <LogCard
              v-for="log in systemLogs"
              :key="log.id"
              :log="log"
            />
          </div>
        </div>

        <!-- Operation Logs -->
        <div v-else>
          <div v-if="!logStore.logs.length" class="text-center py-12 text-neutral-500">
            <Inbox class="h-6 w-6 mx-auto mb-3 text-neutral-400" />
            {{ t('logs.no_operation_logs') }}
          </div>

          <div v-else class="space-y-2">
            <LogCard
              v-for="log in logStore.logs"
              :key="log.id"
              :log="log"
            />
          </div>
        </div>
      </div>
    </div>

    <!-- ==================== Settings Tab ==================== -->
    <div v-if="activeTab === 'settings'" class="space-y-6">
      <!-- Clear Previews -->
      <div class="space-y-4">
        <h2 class="text-lg font-semibold">{{ t('settings.clear_previews.title') }}</h2>
        <p class="text-sm text-neutral-500 dark:text-neutral-400">
          {{ t('settings.clear_previews.confirm_message') }}
        </p>
        <Button
          variant="outline"
          class="gap-2 text-red-600 hover:text-red-700 hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-900/20"
          @click="handleClearPreviews"
        >
          <Trash2 class="w-4 h-4" />
          {{ t('settings.clear_previews.button') }}
        </Button>
      </div>

      <!-- Backup & Restore -->
      <div class="pt-4 border-t border-neutral-200 dark:border-neutral-700">
        <BackupManager />
      </div>

      <!-- Desktop Settings -->
      <div v-if="showDesktopFeatures" class="pt-4 border-t border-neutral-200 dark:border-neutral-700 space-y-4">
        <h2 class="text-lg font-semibold">{{ t('settings.desktop.title') }}</h2>

        <div class="grid gap-3">
          <button
            class="flex items-center gap-2 px-4 py-2 bg-secondary text-secondary-foreground rounded-md hover:bg-secondary/80"
            @click="handleRestartBackend"
          >
            <RefreshCw class="w-4 h-4" />
            {{ t('settings.desktop.restart') }}
          </button>
        </div>
      </div>
    </div>

    <!-- Confirm Dialog (global for all tabs) -->
    <ConfirmDialog
      v-model:open="confirm.state.value.open"
      :title="confirm.state.value.title"
      :message="confirm.state.value.message"
      :confirm-text="confirm.state.value.confirmText"
      :cancel-text="confirm.state.value.cancelText"
      :variant="confirm.state.value.variant"
      @confirm="confirm.confirm"
      @cancel="confirm.cancel"
    />

    <!-- Feature Settings Dialog (10-click easter egg) -->
    <FeatureSettingsDialog v-model:open="featureDialogOpen" />
  </div>
</template>