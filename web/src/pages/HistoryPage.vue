<script setup lang="ts">
import { ChevronDown, ChevronUp, ExternalLink, RefreshCw } from "lucide-vue-next"
import { onMounted, ref } from "vue"
import { useI18n } from "vue-i18n"
import { getHistoryBatches, getHistoryByBatch } from "@/api/history"
import Button from "@/components/ui/Button.vue"
import type { HistoryBatch, HistoryItem } from "@/types/history"
import { useToast } from "@/composables/useToast"
import { formatDate } from "@/utils/format"

const { t } = useI18n()
const toast = useToast()

const batches = ref<HistoryBatch[]>([])
const loading = ref(false)
const expandedBatch = ref<number | null>(null)
const expandedItems = ref<HistoryItem[]>([])
const loadingItems = ref(false)
const totalItems = ref(0)
const totalBatches = ref(0)

onMounted(async () => {
  await fetchBatches()
})

async function fetchBatches(): Promise<void> {
  loading.value = true
  try {
    const response = await getHistoryBatches(50, 0)
    batches.value = response.batches
    totalBatches.value = response.total_batches
    totalItems.value = response.total_items
  } catch {
    toast.error(t("common.error"))
  } finally {
    loading.value = false
  }
}

async function toggleBatch(batchId: number): Promise<void> {
  if (expandedBatch.value === batchId) {
    expandedBatch.value = null
    expandedItems.value = []
    return
  }

  expandedBatch.value = batchId
  expandedItems.value = []
  loadingItems.value = true

  try {
    const response = await getHistoryByBatch(batchId, 1, 100)
    expandedItems.value = response.items
  } catch {
    toast.error(t("common.error"))
  } finally {
    loadingItems.value = false
  }
}
</script>

<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-semibold">📜 {{ t("history.title") }}</h1>
      <Button @click="fetchBatches">
        <RefreshCw class="h-4 w-4" />
        <span class="ml-1.5">{{ t("common.refresh") }}</span>
      </Button>
    </div>

    <div v-if="loading" class="text-center py-12 text-neutral-500">
      {{ t("common.loading") }}
    </div>

    <div v-else-if="batches.length === 0" class="text-center py-12 text-neutral-500">
      😴 {{ t("history.empty") }}
    </div>

    <template v-else>
      <div class="text-sm text-neutral-500">
        {{ t("history.result.total_batches", { count: totalBatches, items: totalItems }) }}
      </div>

      <div class="space-y-3">
        <button
          v-for="batch in batches"
          :key="batch.id"
          class="w-full text-left bg-white dark:bg-neutral-800 rounded-xl border border-neutral-200 dark:border-neutral-700 hover:border-primary-300 dark:hover:border-primary-700 transition-colors overflow-hidden"
          @click="toggleBatch(batch.id)"
        >
          <div class="p-4 flex items-center justify-between">
            <div class="flex-1">
              <div class="flex items-center gap-3">
                <span class="text-lg font-medium text-neutral-900 dark:text-neutral-100">
                  {{ t("history.batch_title", { id: batch.id }) }}
                </span>
                <span class="px-2 py-0.5 text-xs rounded-full bg-primary-100 dark:bg-primary-900 text-primary-700 dark:text-primary-300">
                  {{ batch.items_count }} {{ batch.items_count === 1 ? t("history.item") : t("history.items") }}
                </span>
              </div>
              <div class="mt-1 text-sm text-neutral-500">
                {{ formatDate(batch.created_at) }}
                <span v-if="batch.sources.length > 0" class="ml-2">
                  • {{ batch.sources.slice(0, 3).join(", ") }}
                  <span v-if="batch.sources.length > 3">+{{ batch.sources.length - 3 }}</span>
                </span>
              </div>
            </div>
            <div class="ml-4">
              <ChevronDown
                v-if="expandedBatch !== batch.id"
                class="h-5 w-5 text-neutral-400"
              />
              <ChevronUp
                v-else
                class="h-5 w-5 text-primary-500"
              />
            </div>
          </div>

          <div
            v-if="expandedBatch === batch.id"
            class="border-t border-neutral-200 dark:border-neutral-700"
          >
            <div v-if="loadingItems" class="p-4 text-center text-neutral-500">
              {{ t("common.loading") }}
            </div>
            <div v-else-if="expandedItems.length === 0" class="p-4 text-center text-neutral-500">
              {{ t("history.empty_items") }}
            </div>
            <div v-else class="divide-y divide-neutral-200 dark:divide-neutral-700">
              <a
                v-for="item in expandedItems"
                :key="item.id"
                :href="item.link"
                target="_blank"
                class="block p-4 hover:bg-neutral-50 dark:hover:bg-neutral-900 transition-colors"
              >
                <div class="flex items-start justify-between gap-3">
                  <div class="flex-1 min-w-0">
                    <div class="flex items-center gap-2 text-xs text-neutral-500 mb-1">
                      <span class="text-primary-600 dark:text-primary-400">{{ item.source }}</span>
                      <span v-if="item.published_at">•</span>
                      <span v-if="item.published_at">{{ formatDate(item.published_at) }}</span>
                    </div>
                    <h4 class="text-sm font-medium text-neutral-900 dark:text-neutral-100 truncate">
                      {{ item.title }}
                    </h4>
                    <p v-if="item.description" class="mt-1 text-xs text-neutral-500 line-clamp-2">
                      {{ item.description }}
                    </p>
                  </div>
                  <ExternalLink class="h-4 w-4 text-neutral-400 flex-shrink-0 mt-1" />
                </div>
              </a>
            </div>
          </div>
        </button>
      </div>
    </template>
  </div>
</template>