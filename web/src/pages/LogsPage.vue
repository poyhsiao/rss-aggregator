<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { getLogs } from '@/api/logs'
import { useLogStore } from '@/stores/log'
import LogCard from '@/components/LogCard.vue'
import type { ErrorLog } from '@/types/log'

const { t } = useI18n()
const logStore = useLogStore()

const systemLogs = ref<ErrorLog[]>([])
const loading = ref(true)
const activeTab = ref<'system' | 'operation'>('system')

const tabs = computed(() => [
  { id: 'system' as const, label: t('logs.system_logs') },
  { id: 'operation' as const, label: t('logs.operation_logs') },
])

async function fetchSystemLogs(): Promise<void> {
  loading.value = true
  try {
    const result = await getLogs({ limit: 100 })
    systemLogs.value = result
  } catch (error) {
    console.error('[LogsPage] Error fetching logs:', error)
  } finally {
    loading.value = false
  }
}

onMounted(fetchSystemLogs)
</script>

<template>
  <div class="space-y-6">
    <h1 class="text-2xl font-semibold">📝 {{ t('logs.title') }}</h1>

    <div class="flex gap-2 border-b border-neutral-200 dark:border-neutral-700">
      <button
        v-for="tab in tabs"
        :key="tab.id"
        type="button"
        class="px-4 py-2 text-sm font-medium transition-colors relative"
        :class="[
          activeTab === tab.id
            ? 'text-blue-600 dark:text-blue-400'
            : 'text-neutral-500 hover:text-neutral-700 dark:text-neutral-400 dark:hover:text-neutral-300'
        ]"
        @click="activeTab = tab.id"
      >
        {{ tab.label }}
        <span
          v-if="activeTab === tab.id"
          class="absolute bottom-0 left-0 right-0 h-0.5 bg-blue-600 dark:bg-blue-400"
        />
      </button>
    </div>

    <div v-if="activeTab === 'system'">
      <div v-if="loading" class="text-center py-12 text-neutral-500">
        {{ t('common.loading') }}
      </div>

      <div v-else-if="!systemLogs.length" class="text-center py-12 text-neutral-500">
        ✨ {{ t('logs.empty') }}
      </div>

      <div v-else class="space-y-2">
        <LogCard
          v-for="log in systemLogs"
          :key="log.id"
          :log="log"
        />
      </div>
    </div>

    <div v-else-if="activeTab === 'operation'">
      <div v-if="!logStore.hasLogs" class="text-center py-12 text-neutral-500">
        ✨ {{ t('logs.no_operation_logs') }}
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
</template>