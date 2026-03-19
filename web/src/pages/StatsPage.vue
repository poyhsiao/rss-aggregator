<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { getStats } from '@/api/stats'
import type { Stats } from '@/types/stats'
import Card from '@/components/ui/Card.vue'

const { t } = useI18n()

const stats = ref<Stats[]>([])
const loading = ref(true)

async function fetchStats(): Promise<void> {
  loading.value = true
  try {
    stats.value = await getStats(7)
  } finally {
    loading.value = false
  }
}

const totalRequests = () => stats.value.reduce((sum, s) => sum + s.total_requests, 0)
const successfulFetches = () => stats.value.reduce((sum, s) => sum + s.successful_fetches, 0)
const failedFetches = () => stats.value.reduce((sum, s) => sum + s.failed_fetches, 0)

onMounted(fetchStats)
</script>

<template>
  <div class="space-y-6">
    <h1 class="text-2xl font-semibold">📊 {{ t('stats.title') }}</h1>
    
    <div v-if="loading" class="text-center py-12 text-neutral-500">
      {{ t('common.loading') }}
    </div>
    
    <template v-else>
      <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Card class="p-6 text-center">
          <div class="text-3xl font-bold text-primary-600">{{ totalRequests() }}</div>
          <div class="text-neutral-500 mt-1">{{ t('stats.total_requests') }}</div>
        </Card>
        
        <Card class="p-6 text-center">
          <div class="text-3xl font-bold text-green-600">{{ successfulFetches() }}</div>
          <div class="text-neutral-500 mt-1">{{ t('stats.successful_fetches') }}</div>
        </Card>
        
        <Card class="p-6 text-center">
          <div class="text-3xl font-bold text-red-600">{{ failedFetches() }}</div>
          <div class="text-neutral-500 mt-1">{{ t('stats.failed_fetches') }}</div>
        </Card>
      </div>
      
      <Card class="p-6">
        <h2 class="text-lg font-medium mb-4">{{ t('stats.daily_trend') }}</h2>
        <div class="h-64 flex items-center justify-center text-neutral-400">
          📈 圖表區域
        </div>
      </Card>
    </template>
  </div>
</template>