<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { getSources, deleteSource, refreshSource } from '@/api/sources'
import type { Source } from '@/types/source'
import Button from '@/components/ui/Button.vue'
import Badge from '@/components/ui/Badge.vue'

const { t } = useI18n()

const sources = ref<Source[]>([])
const loading = ref(true)

async function fetchSources(): Promise<void> {
  loading.value = true
  try {
    sources.value = await getSources()
  } finally {
    loading.value = false
  }
}

async function handleRefresh(id: number): Promise<void> {
  await refreshSource(id)
  await fetchSources()
}

async function handleDelete(id: number): Promise<void> {
  if (confirm(t('common.confirm') + '?')) {
    await deleteSource(id)
    await fetchSources()
  }
}

onMounted(fetchSources)
</script>

<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-semibold">📡 {{ t('sources.title') }}</h1>
      <Button>
        ➕ {{ t('sources.add') }}
      </Button>
    </div>
    
    <div v-if="loading" class="text-center py-12 text-neutral-500">
      {{ t('common.loading') }}
    </div>
    
    <div v-else-if="!sources.length" class="text-center py-12 text-neutral-500">
      📭 {{ t('sources.empty') }}
    </div>
    
    <div v-else class="space-y-3">
      <div
        v-for="source in sources"
        :key="source.id"
        class="flex items-center justify-between p-4 bg-white dark:bg-neutral-800 rounded-xl border border-neutral-200 dark:border-neutral-700"
      >
        <div class="flex items-center gap-3">
          <span>{{ source.is_active ? '🟢' : '🔴' }}</span>
          <div>
            <div class="font-medium">{{ source.name }}</div>
            <div class="text-sm text-neutral-500">{{ source.url }}</div>
          </div>
        </div>
        
        <div class="flex items-center gap-3">
          <Badge :variant="source.is_active ? 'success' : 'secondary'">
            {{ source.is_active ? t('sources.active') : t('sources.inactive') }}
          </Badge>
          
          <div class="flex gap-1">
            <Button variant="ghost" size="sm" @click="handleRefresh(source.id)">
              🔄
            </Button>
            <Button variant="ghost" size="sm" @click="handleDelete(source.id)">
              🗑️
            </Button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>