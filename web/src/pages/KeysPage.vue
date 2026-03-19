<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { getKeys } from '@/api/keys'
import type { ApiKey } from '@/types/key'
import Button from '@/components/ui/Button.vue'
import Badge from '@/components/ui/Badge.vue'

const { t } = useI18n()

const keys = ref<ApiKey[]>([])
const loading = ref(true)

async function fetchKeys(): Promise<void> {
  loading.value = true
  try {
    keys.value = await getKeys()
  } finally {
    loading.value = false
  }
}

onMounted(fetchKeys)
</script>

<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-semibold">🔑 {{ t('keys.title') }}</h1>
      <Button>
        ➕ {{ t('keys.add') }}
      </Button>
    </div>
    
    <div v-if="loading" class="text-center py-12 text-neutral-500">
      {{ t('common.loading') }}
    </div>
    
    <div v-else-if="!keys.length" class="text-center py-12 text-neutral-500">
      🔑 {{ t('keys.empty') }}
    </div>
    
    <div v-else class="space-y-2">
      <div
        v-for="key in keys"
        :key="key.id"
        class="flex items-center justify-between p-4 bg-white dark:bg-neutral-800 rounded-xl border border-neutral-200 dark:border-neutral-700"
      >
        <div>
          <code class="text-sm bg-neutral-100 dark:bg-neutral-700 px-2 py-1 rounded">
            {{ key.key.slice(0, 8) }}...{{ key.key.slice(-4) }}
          </code>
          <span v-if="key.name" class="ml-2 text-neutral-500">{{ key.name }}</span>
        </div>
        <Badge :variant="key.is_active ? 'success' : 'secondary'">
          {{ key.is_active ? t('sources.active') : t('sources.inactive') }}
        </Badge>
      </div>
    </div>
  </div>
</template>