<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { RefreshCw, Clock, Database } from 'lucide-vue-next'
import { getFeed } from '@/api/feed'
import { refreshAllSources } from '@/api/sources'
import type { FeedItem } from '@/types/feed'
import { formatDate } from '@/utils/format'
import Input from '@/components/ui/Input.vue'
import Button from '@/components/ui/Button.vue'

const { t } = useI18n()

const feedItems = ref<FeedItem[]>([])
const loading = ref(true)
const refreshing = ref(false)
const sortBy = ref<'published_at' | 'source'>('published_at')
const keywords = ref('')

async function fetchFeed(): Promise<void> {
  loading.value = true
  try {
    feedItems.value = await getFeed({
      sort_by: sortBy.value,
      keywords: keywords.value || undefined,
    })
  } finally {
    loading.value = false
  }
}

async function handleRefreshAll(): Promise<void> {
  refreshing.value = true
  try {
    await refreshAllSources()
    await fetchFeed()
  } finally {
    refreshing.value = false
  }
}

onMounted(fetchFeed)

watch([sortBy, keywords], () => {
  fetchFeed()
})
</script>

<template>
  <div class="space-y-6">
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
      <h1 class="text-2xl font-semibold">📰 {{ t('feed.title') }}</h1>
      
      <div class="flex flex-wrap gap-2">
        <Button
          :variant="sortBy === 'published_at' ? 'default' : 'outline'"
          size="sm"
          :title="t('feed.sort_time')"
          @click="sortBy = 'published_at'"
        >
          <Clock class="h-4 w-4 mr-2" />
          {{ t('feed.sort_time') }}
        </Button>
        <Button
          :variant="sortBy === 'source' ? 'default' : 'outline'"
          size="sm"
          :title="t('feed.sort_source')"
          @click="sortBy = 'source'"
        >
          <Database class="h-4 w-4 mr-2" />
          {{ t('feed.sort_source') }}
        </Button>

        <Button
          variant="outline"
          size="sm"
          :title="t('feed.refresh')"
          :disabled="refreshing"
          @click="handleRefreshAll"
        >
          <RefreshCw :class="{ 'animate-spin': refreshing }" class="h-4 w-4 mr-2" />
          {{ t('feed.refresh') }}
        </Button>

        <Input
          v-model="keywords"
          :placeholder="t('feed.search_placeholder')"
          class="w-48"
        />
      </div>
    </div>
    
    <div v-if="loading" class="text-center py-12 text-neutral-500">
      {{ t('common.loading') }}
    </div>
    
    <div v-else-if="!feedItems.length" class="text-center py-12 text-neutral-500">
      😴 {{ t('feed.empty') }}
    </div>
    
    <div v-else class="grid gap-4">
      <a
        v-for="item in feedItems"
        :key="item.id"
        :href="item.link"
        target="_blank"
        class="block p-6 bg-white dark:bg-neutral-800 rounded-xl border border-neutral-200 dark:border-neutral-700 hover:shadow-md transition-shadow"
      >
        <div class="flex items-center gap-2 text-sm text-neutral-500 mb-2">
          <span class="text-primary-600 dark:text-primary-400">{{ item.source }}</span>
          <span>•</span>
          <span>{{ formatDate(item.published_at) }}</span>
        </div>
        
        <h3 class="text-lg font-medium text-neutral-900 dark:text-neutral-100 mb-2">
          {{ item.title }}
        </h3>
        
        <p class="text-neutral-600 dark:text-neutral-400 line-clamp-2">
          {{ item.description }}
        </p>
      </a>
    </div>
  </div>
</template>