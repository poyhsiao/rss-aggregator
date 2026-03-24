<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { FileText, RefreshCw } from 'lucide-vue-next'
import { getSources, deleteSource, refreshSource, refreshAllSources } from '@/api/sources'
import type { Source } from '@/types/source'
import type { FeedParams } from '@/api/feed'
import Button from '@/components/ui/Button.vue'
import Badge from '@/components/ui/Badge.vue'
import SourceDialog from '@/components/SourceDialog.vue'
import RssPreviewDialog from '@/components/RssPreviewDialog.vue'
import { useToast } from '@/composables/useToast'
import { useConfirm } from '@/composables/useConfirm'
import ConfirmDialog from '@/components/ui/ConfirmDialog.vue'
import { formatDate } from '@/utils/format'

const { t } = useI18n()
const toast = useToast()
const confirm = useConfirm()

const sources = ref<Source[]>([])
const loading = ref(true)
const refreshing = ref(false)
const showDialog = ref(false)
const editingSource = ref<Source | null>(null)
const previewDialogOpen = ref(false)
const previewParams = ref<FeedParams | undefined>(undefined)
const previewTitle = ref<string | undefined>(undefined)

function handleSaved(source: Source): void {
    const existingIndex = sources.value.findIndex(s => s.id === source.id)
    if (existingIndex >= 0) {
      sources.value[existingIndex] = source
    } else {
      sources.value.unshift(source)
    }
  }

  async function fetchSources(): Promise<void> {
    loading.value = true
    try {
      sources.value = await getSources()
    } finally {
      loading.value = false
    }
  }

function openAddDialog(): void {
  editingSource.value = null
  showDialog.value = true
}

function openEditDialog(source: Source): void {
  editingSource.value = source
  showDialog.value = true
}

function openPreviewDialog(source: Source): void {
  previewParams.value = { source_id: source.id }
  previewTitle.value = source.name
  previewDialogOpen.value = true
}

async function handleRefresh(id: number): Promise<void> {
  try {
    await refreshSource(id)
    await fetchSources()
    toast.success(t('common.success'))
  } catch {
    toast.error(t('common.error'))
  }
}

async function handleRefreshAll(): Promise<void> {
  refreshing.value = true
  try {
    await refreshAllSources()
    await fetchSources()
    toast.success(t('common.success'))
  } catch {
    toast.error(t('common.error'))
  } finally {
    refreshing.value = false
  }
}

async function handleDelete(id: number): Promise<void> {
  const confirmed = await confirm.show({
    title: t('sources.delete_title'),
    message: t('sources.delete_confirm'),
    confirmText: t('common.delete'),
    cancelText: t('common.cancel'),
    variant: 'danger'
  })
  if (!confirmed) return
  
  try {
    await deleteSource(id)
    await fetchSources()
    toast.success(t('sources.deleted'))
  } catch {
    toast.error(t('common.error'))
  }
}

function getDisplayUrl(url: string): { display: string; full: string } {
  const isMobile = window.innerWidth < 640
  const maxLength = isMobile ? 28 : 50
  
  if (url.length <= maxLength) {
    return { display: url, full: url }
  }
  
  try {
    const urlObj = new URL(url)
    const domain = urlObj.hostname
    const path = urlObj.pathname + urlObj.search
    
    const availableForPath = maxLength - domain.length - 4
    
    if (availableForPath > 8 && path.length > 0) {
      const truncatedPath = path.length > availableForPath 
        ? `...${path.slice(-availableForPath)}` 
        : path
      return { 
        display: `${domain}${truncatedPath}`, 
        full: url 
      }
    }
    
    return { display: `${domain}...`, full: url }
  } catch {
    return { 
      display: `${url.slice(0, maxLength)}...`, 
      full: url 
    }
  }
}

onMounted(fetchSources)
</script>

<template>
  <div class="space-y-6">
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
      <h1 class="text-2xl font-semibold">📡 {{ t('sources.title') }}</h1>
      <div class="flex flex-wrap gap-2">
        <Button
          variant="outline"
          :disabled="refreshing"
          :title="t('sources.refresh_all')"
          @click="handleRefreshAll"
        >
          <RefreshCw :class="{ 'animate-spin': refreshing }" class="h-4 w-4 mr-2" />
          {{ t('sources.refresh_all') }}
        </Button>
        <Button
          @click="openAddDialog"
          :title="t('sources.add')"
        >
          ➕ {{ t('sources.add') }}
        </Button>
      </div>
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
        class="p-4 bg-white dark:bg-neutral-800 rounded-xl border border-neutral-200 dark:border-neutral-700"
      >
        <div class="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3">
          <div class="flex items-start gap-3 min-w-0 flex-1">
            <span class="mt-0.5 shrink-0">{{ source.is_active ? '🟢' : '🔴' }}</span>
            <div class="min-w-0 flex-1">
              <div class="font-medium truncate">{{ source.name }}</div>
              <div 
                class="text-sm text-neutral-500 dark:text-neutral-400 truncate cursor-help"
                :title="source.url"
              >
                {{ getDisplayUrl(source.url).display }}
              </div>
            </div>
          </div>
          
          <div class="flex items-center gap-3 shrink-0">
            <Badge :variant="source.is_active ? 'success' : 'secondary'">
              {{ source.is_active ? t('sources.active') : t('sources.inactive') }}
            </Badge>
            
            <div class="flex gap-1">
              <Button
                variant="ghost"
                size="sm"
                :title="t('common.edit')"
                @click="openEditDialog(source)"
              >
                ✏️
              </Button>
              <Button
                variant="ghost"
                size="sm"
                :title="t('sources.view_data')"
                @click="openPreviewDialog(source)"
              >
                <FileText class="h-4 w-4" />
              </Button>
              <Button
                variant="ghost"
                size="sm"
                :title="t('common.refresh')"
                @click="handleRefresh(source.id)"
              >
                🔄
              </Button>
              <Button
                variant="ghost"
                size="sm"
                :title="t('common.delete')"
                @click="handleDelete(source.id)"
              >
                🗑️
              </Button>
            </div>
          </div>
        </div>
        
        <div class="mt-3 pt-3 border-t border-neutral-100 dark:border-neutral-700">
          <div class="flex flex-col sm:flex-row sm:flex-wrap gap-1 sm:gap-x-4 text-xs sm:text-sm text-neutral-500 dark:text-neutral-400">
            <span class="truncate">
              📅 {{ t('sources.created_at') }}: {{ formatDate(source.created_at) }}
            </span>
            <span class="truncate">
              🔄 {{ t('sources.updated_at') }}: {{ formatDate(source.updated_at) }}
            </span>
            <span v-if="source.last_fetched_at" class="truncate">
              ⏱️ {{ t('sources.last_fetched') }}: {{ formatDate(source.last_fetched_at) }}
            </span>
          </div>
          <div v-if="source.last_error" class="mt-2 text-xs sm:text-sm text-red-500 dark:text-red-400 truncate">
            ⚠️ {{ source.last_error }}
          </div>
        </div>
      </div>
    </div>

    <SourceDialog
      v-model:open="showDialog"
      :source="editingSource"
      @saved="handleSaved"
    />

    <RssPreviewDialog
      v-model:open="previewDialogOpen"
      :params="previewParams"
      :title="previewTitle"
    />

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
  </div>
</template>