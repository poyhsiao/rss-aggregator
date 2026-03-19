<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { getLogs } from '@/api/logs'
import type { ErrorLog } from '@/types/log'
import { formatDate } from '@/utils/format'

const { t } = useI18n()

const logs = ref<ErrorLog[]>([])
const loading = ref(true)

async function fetchLogs(): Promise<void> {
  loading.value = true
  try {
    logs.value = await getLogs({ limit: 100 })
  } finally {
    loading.value = false
  }
}

onMounted(fetchLogs)
</script>

<template>
  <div class="space-y-6">
    <h1 class="text-2xl font-semibold">📝 {{ t('logs.title') }}</h1>
    
    <div v-if="loading" class="text-center py-12 text-neutral-500">
      {{ t('common.loading') }}
    </div>
    
    <div v-else-if="!logs.length" class="text-center py-12 text-neutral-500">
      ✨ {{ t('logs.empty') }}
    </div>
    
    <div v-else class="space-y-2">
      <div
        v-for="log in logs"
        :key="log.id"
        class="p-4 bg-red-50 dark:bg-red-900/20 rounded-xl border border-red-200 dark:border-red-800"
      >
        <div class="flex items-center justify-between mb-1">
          <span class="font-medium text-red-700 dark:text-red-400">
            {{ log.error_type }}
          </span>
          <span class="text-sm text-neutral-500">
            {{ formatDate(log.created_at) }}
          </span>
        </div>
        <p class="text-sm text-neutral-600 dark:text-neutral-400">
          {{ log.error_message }}
        </p>
      </div>
    </div>
  </div>
</template>