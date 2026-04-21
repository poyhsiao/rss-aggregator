<script setup lang="ts">
import { Check, ChevronDown, ChevronUp, Eye, ExternalLink, FileText, Pencil, RefreshCw, Trash2, X, ScrollText, Inbox, Newspaper } from "lucide-vue-next"
import { computed, onMounted, ref, watch } from "vue"
import { useI18n } from "vue-i18n"
import { deleteAllHistory, deleteBatch, getHistoryBatches, getHistoryByBatch, updateBatchName } from "@/api/history"
import { getGroups } from "@/api/source-groups"
import type { HistoryBatch, HistoryItem } from "@/types/history"
import type { SourceGroup } from "@/types/source-group"
import { useToast } from "@/composables/useToast"
import { useConfirm } from "@/composables/useConfirm"
import { formatDate } from "@/utils/format"
import Button from "@/components/ui/Button.vue"
import ConfirmDialog from "@/components/ui/ConfirmDialog.vue"
import ArticlePreviewDialog from "@/components/ArticlePreviewDialog.vue"
import RssPreviewDialog from "@/components/RssPreviewDialog.vue"
import { useFeatureFlagsStore } from "@/stores/featureFlags"

const { t } = useI18n()
const toast = useToast()
const confirm = useConfirm()
const featureFlags = useFeatureFlagsStore()

const batches = ref<HistoryBatch[]>([])
const groups = ref<SourceGroup[]>([])
const selectedGroupId = ref<number | null>(null)
const loading = ref(false)
const expandedBatch = ref<number | null>(null)
const expandedItems = ref<HistoryItem[]>([])
const loadingItems = ref(false)
const totalItems = ref(0)
const totalBatches = ref(0)

const filteredBatches = computed(() => {
  if (selectedGroupId.value === null) return batches.value;
  return batches.value.filter(batch =>
    batch.groups?.some(g => g.id === selectedGroupId.value)
  );
});

// Edit name state
const editingBatchId = ref<number | null>(null)
const editingName = ref("")
const savingName = ref(false)

// Delete state
const deletingBatchId = ref<number | null>(null)
const deleting = ref(false)
const deletingAll = ref(false)

// Preview state
const previewOpen = ref(false)
const previewBatchId = ref<number | null>(null)
const previewBatchTitle = ref("")

function openPreview(batch: HistoryBatch): void {
  previewBatchId.value = batch.id
  previewBatchTitle.value = batch.name || t("history.batch_title", { id: batch.id })
  previewOpen.value = true
}

function closePreview(): void {
  previewOpen.value = false
  previewBatchId.value = null
  previewBatchTitle.value = ""
}

// Article preview state
const articlePreviewOpen = ref(false)
const selectedArticle = ref<{ url: string; title: string } | null>(null)

onMounted(async () => {
  await fetchBatches()
  try {
    groups.value = await getGroups()
  } catch { /* ignore */ }
})

async function fetchBatches(): Promise<void> {
  loading.value = true
  try {
    const response = await getHistoryBatches(50, 0, selectedGroupId.value ?? undefined)
    batches.value = response.batches
    totalBatches.value = response.total_batches
    totalItems.value = response.total_items
  } catch {
    toast.error(t("common.error"))
  } finally {
    loading.value = false
  }
}

watch(selectedGroupId, () => {
  fetchBatches()
})

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

function startEditName(batch: HistoryBatch): void {
  editingBatchId.value = batch.id
  editingName.value = batch.name || ""
}

function cancelEditName(): void {
  editingBatchId.value = null
  editingName.value = ""
}

async function saveBatchName(batchId: number): Promise<void> {
  if (!editingName.value.trim()) {
    toast.error(t("history.name_required"))
    return
  }

  savingName.value = true
  try {
    const updated = await updateBatchName(batchId, { name: editingName.value.trim() })
    const index = batches.value.findIndex(b => b.id === batchId)
    if (index !== -1) {
      batches.value[index] = updated
    }
    toast.success(t("history.name_updated"))
    editingBatchId.value = null
    editingName.value = ""
  } catch {
    toast.error(t("common.error"))
  } finally {
    savingName.value = false
  }
}

async function confirmDeleteBatch(batchId: number): Promise<void> {
  const result = await confirm.show({
    title: t("history.delete_title"),
    message: t("history.delete_confirm"),
    confirmText: t("common.delete"),
    cancelText: t("common.cancel"),
    variant: "danger",
  })
  if (!result) return

  deletingBatchId.value = batchId
  deleting.value = true
  try {
    await deleteBatch(batchId)
    batches.value = batches.value.filter(b => b.id !== batchId)
    totalBatches.value -= 1
    if (expandedBatch.value === batchId) {
      expandedBatch.value = null
      expandedItems.value = []
    }
    toast.success(t("history.deleted"))
  } catch {
    toast.error(t("common.error"))
  } finally {
    deleting.value = false
    deletingBatchId.value = null
  }
}

async function confirmDeleteAll(): Promise<void> {
  const result = await confirm.show({
    title: t("history.delete_all_title"),
    message: t("history.delete_all_confirm"),
    confirmText: t("common.delete"),
    cancelText: t("common.cancel"),
    variant: "danger",
  })
  if (!result) return

  deletingAll.value = true
  try {
    await deleteAllHistory()
    batches.value = []
    totalBatches.value = 0
    totalItems.value = 0
    toast.success(t("history.deleted_all"))
  } catch {
    toast.error(t("common.error"))
  } finally {
    deletingAll.value = false
  }
}

function openArticlePreview(item: HistoryItem): void {
  selectedArticle.value = {
    url: item.link,
    title: item.title,
  }
  articlePreviewOpen.value = true
}
</script>

<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-semibold"><ScrollText class="h-6 w-6 inline mr-2" />{{ t("history.title") }}</h1>
      <div class="flex items-center gap-2">
        <Button
          v-if="selectedGroupId === null && batches.length > 0"
          variant="outline"
          size="sm"
          :disabled="deletingAll"
          @click="confirmDeleteAll"
        >
          <Trash2 class="h-4 w-4 text-red-500" />
          <span class="ml-1.5">{{ t("history.delete_all") }}</span>
        </Button>
        <Button @click="fetchBatches">
          <RefreshCw class="h-4 w-4 text-green-500" />
          <span class="ml-1.5">{{ t("common.refresh") }}</span>
        </Button>
      </div>
    </div>

    <!-- Group Filter Chips -->
    <div v-if="featureFlags.feature_groups && groups.length > 0" class="flex flex-wrap gap-2">
      <button
        :class="[
          'px-3 py-1 rounded-full text-sm font-medium transition-colors',
          selectedGroupId === null
            ? 'bg-primary-600 text-white'
            : 'bg-neutral-200 dark:bg-neutral-700 text-neutral-700 dark:text-neutral-300 hover:bg-neutral-300 dark:hover:bg-neutral-600'
        ]"
        @click="selectedGroupId = null"
      >
        {{ t('groups.all') }}
      </button>
      <button
        v-for="group in groups"
        :key="group.id"
        :class="[
          'px-3 py-1 rounded-full text-sm font-medium transition-colors',
          selectedGroupId === group.id
            ? 'bg-primary-600 text-white'
            : 'bg-neutral-200 dark:bg-neutral-700 text-neutral-700 dark:text-neutral-300 hover:bg-neutral-300 dark:hover:bg-neutral-600'
        ]"
        @click="selectedGroupId = group.id"
      >
        {{ group.name }}
      </button>
    </div>

    <div v-if="loading" class="text-center py-12 text-neutral-500">
      {{ t("common.loading") }}
    </div>

    <div v-else-if="filteredBatches.length === 0" class="text-center py-12 text-neutral-500">
      <Inbox class="h-6 w-6 mx-auto mb-3 text-neutral-400" />
      {{ t("history.empty") }}
    </div>

    <template v-else>
      <div class="text-sm text-neutral-500">
        {{ t("history.result.total_batches", { count: totalBatches, items: totalItems }) }}
      </div>

      <div class="space-y-3">
        <div
          v-for="batch in filteredBatches"
          :key="batch.id"
          class="w-full text-left bg-white dark:bg-neutral-800 rounded-xl border border-neutral-200 dark:border-neutral-700 hover:border-primary-300 dark:hover:border-primary-700 transition-colors overflow-hidden max-w-full"
        >
          <div class="p-4 flex items-center justify-between">
            <div class="flex-1">
              <div class="flex items-center gap-3">
                <template v-if="editingBatchId === batch.id">
                  <input
                    v-model="editingName"
                    type="text"
                    class="flex-1 px-3 py-1.5 text-lg font-medium bg-white dark:bg-neutral-900 border border-primary-500 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 text-neutral-900 dark:text-neutral-100"
                    :placeholder="t('history.name_placeholder')"
                    @keydown.enter="saveBatchName(batch.id)"
                    @keydown.escape="cancelEditName"
                  />
                  <button
                    type="button"
                    :disabled="savingName"
                    class="p-1.5 rounded-lg hover:bg-green-100 dark:hover:bg-green-900 text-green-600 dark:text-green-400 disabled:opacity-50"
                    :title="t('common.save')"
                    @click="saveBatchName(batch.id)"
                  >
                    <Check v-if="!savingName" class="h-5 w-5" />
                    <RefreshCw v-else class="h-5 w-5 animate-spin" />
                  </button>
                  <button
                    type="button"
                    :disabled="savingName"
                    class="p-1.5 rounded-lg hover:bg-neutral-100 dark:hover:bg-neutral-700 text-neutral-500 dark:text-neutral-400"
                    :title="t('common.cancel')"
                    @click="cancelEditName"
                  >
                    <X class="h-5 w-5" />
                  </button>
                </template>
                <template v-else>
                  <span class="text-lg font-medium text-neutral-900 dark:text-neutral-100">
                    {{ batch.name || t("history.batch_title", { id: batch.id }) }}
                  </span>
                  <span class="px-2 py-0.5 text-xs rounded-full bg-primary-100 dark:bg-primary-900 text-primary-700 dark:text-primary-300">
                    {{ batch.items_count }} {{ batch.items_count === 1 ? t("history.item") : t("history.items") }}
                  </span>
                </template>
              </div>
              <div class="mt-1 text-sm text-neutral-500">
                <span v-if="batch.latest_published_at" class="text-primary-600 dark:text-primary-400">
                  <Newspaper class="h-4 w-4 inline mr-1" />{{ formatDate(batch.latest_published_at) }}
                </span>
                <span v-if="batch.latest_fetched_at" class="ml-2">
                  • {{ t("history.fetched") }} {{ formatDate(batch.latest_fetched_at) }}
                </span>
                <span v-if="batch.sources.length > 0" class="ml-2">
                  • {{ batch.sources.slice(0, 3).join(", ") }}
                  <span v-if="batch.sources.length > 3">+{{ batch.sources.length - 3 }}</span>
                </span>
                <template v-if="batch.groups?.length">
                  <span
                    v-for="g in batch.groups.slice(0, 3)"
                    :key="g.id"
                    class="ml-1 inline-block px-2 py-0.5 text-xs rounded-full bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300"
                  >
                    {{ g.name }}
                  </span>
                  <span v-if="batch.groups.length > 3" class="ml-1 text-xs text-neutral-500">
                    +{{ batch.groups.length - 3 }}
                  </span>
                </template>
              </div>
            </div>
            <div class="ml-4 flex items-center gap-1">
              <button
                type="button"
                class="p-2 rounded-lg hover:bg-neutral-100 dark:hover:bg-neutral-700 text-neutral-500 dark:text-neutral-400 transition-colors"
                :title="t('history.edit_name')"
                @click.stop="startEditName(batch)"
              >
                <Pencil class="h-4 w-4 text-blue-500" />
              </button>
              <button
                type="button"
                class="p-2 rounded-lg hover:bg-purple-100 dark:hover:bg-purple-900 text-purple-600 dark:text-purple-400 transition-colors"
                :title="t('history.preview')"
                @click.stop="openPreview(batch)"
              >
                <FileText class="h-4 w-4 text-purple-500" />
              </button>
              <button
                type="button"
                class="p-2 rounded-lg hover:bg-red-100 dark:hover:bg-red-900 text-red-600 dark:text-red-400 transition-colors"
                :title="t('common.delete')"
                @click.stop="confirmDeleteBatch(batch.id)"
              >
                <Trash2 class="h-4 w-4 text-red-500" />
              </button>
              <button
                type="button"
                class="p-2 rounded-lg hover:bg-neutral-100 dark:hover:bg-neutral-700 text-neutral-400 transition-colors"
                @click="toggleBatch(batch.id)"
              >
                <ChevronDown
                  v-if="expandedBatch !== batch.id"
                  class="h-5 w-5"
                />
                <ChevronUp
                  v-else
                  class="h-5 w-5 text-primary-500"
                />
              </button>
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
              <div
                v-for="item in expandedItems"
                :key="item.id"
                class="block p-4 hover:bg-neutral-50 dark:hover:bg-neutral-900 transition-colors max-w-full overflow-hidden"
              >
                <div class="flex items-start justify-between gap-3 min-w-0 max-w-full overflow-hidden">
                  <a
                    :href="item.link"
                    target="_blank"
                    class="flex-1 min-w-0 overflow-hidden"
                  >
                    <div class="flex items-center gap-2 text-xs text-neutral-500 mb-1 shrink-0 flex-wrap">
                      <span class="text-primary-600 dark:text-primary-400">{{ item.source }}</span>
                      <template v-if="item.source_groups?.length">
                        <span
                          v-for="g in item.source_groups.slice(0, 2)"
                          :key="g.id"
                          class="inline-block px-2 py-0.5 text-xs rounded-full bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300"
                        >
                          {{ g.name }}
                        </span>
                        <span
                          v-if="item.source_groups.length > 2"
                          class="inline-block px-2 py-0.5 text-xs rounded-full bg-neutral-200 dark:bg-neutral-700 text-neutral-600 dark:text-neutral-400"
                        >
                          +{{ item.source_groups.length - 2 }}
                        </span>
                      </template>
                      <span v-if="item.published_at">•</span>
                      <span v-if="item.published_at">{{ formatDate(item.published_at) }}</span>
                    </div>
                    <h4 class="text-sm font-medium text-neutral-900 dark:text-neutral-100 line-clamp-2 leading-snug">
                      {{ item.title }}
                    </h4>
                    <p v-if="item.description" class="mt-1 text-xs text-neutral-500 line-clamp-2">
                      {{ item.description }}
                    </p>
                  </a>
                  <div class="flex items-center gap-1 shrink-0">
                    <button
                      type="button"
                      class="p-1.5 rounded-lg hover:bg-purple-100 dark:hover:bg-purple-900 text-purple-500 dark:text-purple-400 transition-colors"
                      :title="t('preview.preview_article')"
                      @click.stop="openArticlePreview(item)"
                    >
                      <Eye class="h-4 w-4 text-purple-500" />
                    </button>
                    <a
                      :href="item.link"
                      target="_blank"
                      class="p-1.5 rounded-lg hover:bg-neutral-100 dark:hover:bg-neutral-700 text-neutral-400 transition-colors"
                      :title="t('preview.open_in_new')"
                    >
                      <ExternalLink class="h-4 w-4" />
                    </a>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>

    <!-- Confirm Dialog -->
    <ConfirmDialog
      :open="confirm.state.value.open"
      :title="confirm.state.value.title"
      :message="confirm.state.value.message"
      :confirm-text="confirm.state.value.confirmText"
      :cancel-text="confirm.state.value.cancelText"
      :variant="confirm.state.value.variant"
      @update:open="(v: boolean) => v ? null : confirm.cancel()"
      @confirm="confirm.confirm"
      @cancel="confirm.cancel"
    />

    <!-- Preview Dialog -->
    <RssPreviewDialog
      :open="previewOpen"
      :title="previewBatchTitle"
      :params="previewBatchId !== null ? { batch_id: previewBatchId } : undefined"
      @update:open="(open) => { previewOpen = open; if (!open) closePreview() }"
    />

    <!-- Article Preview Dialog -->
    <ArticlePreviewDialog
      v-model:open="articlePreviewOpen"
      :url="selectedArticle?.url || ''"
      :title="selectedArticle?.title"
    />
  </div>
</template>

<style scoped>
.preview-dialog-enter-active,
.preview-dialog-leave-active {
  transition: opacity 0.2s ease;
}

.preview-dialog-enter-active .rounded-2xl,
.preview-dialog-leave-active .rounded-2xl {
  transition: transform 0.2s ease;
}

.preview-dialog-enter-from,
.preview-dialog-leave-to {
  opacity: 0;
}

.preview-dialog-enter-from .rounded-2xl,
.preview-dialog-leave-to .rounded-2xl {
  transform: scale(0.95);
}
</style>