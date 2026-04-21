<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { FileText, RefreshCw, Trash2, RotateCcw, XCircle, Radio, FolderPlus, FolderOpen, X, Check, ChevronDown, ChevronUp, Plus, Inbox, Pencil, Circle, Calendar, RotateCw, Clock, AlertTriangle } from 'lucide-vue-next'
import { getSources, deleteSource, refreshSource, refreshAllSources } from '@/api/sources'
import { getGroups, createGroup, updateGroup, deleteGroup, addSourceToGroup, removeSourceFromGroup, getGroupSources, refreshGroupSources } from '@/api/source-groups'
import { deleteHistoryByGroup } from '@/api/history'
import { 
  getTrashItems, 
  restoreSource, 
  permanentDeleteSource, 
  clearTrash, 
  type TrashItem, 
  type RestoreConflict,
  RestoreConflictError 
} from '@/api/trash'
import type { Source } from '@/types/source'
import type { SourceGroup } from '@/types/source-group'
import type { FeedParams } from '@/api/feed'
import Button from '@/components/ui/Button.vue'
import Badge from '@/components/ui/Badge.vue'
import Dialog from '@/components/ui/Dialog.vue'
import Input from '@/components/ui/Input.vue'
import SourceDialog from '@/components/SourceDialog.vue'
import RssPreviewDialog from '@/components/RssPreviewDialog.vue'
import RestoreConflictDialog from '@/components/RestoreConflictDialog.vue'
import { useToast } from '@/composables/useToast'
import { useConfirm } from '@/composables/useConfirm'
import ConfirmDialog from '@/components/ui/ConfirmDialog.vue'
import ScheduleConfigPanel from '@/components/ScheduleConfigPanel.vue'
import TooltipButton from '@/components/ui/TooltipButton.vue'
import { formatDate } from '@/utils/format'
import { isTauri } from '@/utils/environment'
import { useFeatureFlagsStore } from '@/stores/featureFlags'

const { t } = useI18n()
const store = useFeatureFlagsStore()
const toast = useToast()
const confirm = useConfirm()

const activeTab = ref<'active' | 'trash' | 'groups'>('active')
const sources = ref<Source[]>([])
const trashItems = ref<TrashItem[]>([])
const groups = ref<SourceGroup[]>([])
const groupSources = ref<Record<number, Source[]>>({})
const loading = ref(true)
const refreshing = ref(false)
const showDialog = ref(false)
const showGroupDialog = ref(false)
const editingSource = ref<Source | null>(null)
const editingGroup = ref<SourceGroup | null>(null)
const newGroupName = ref('')
const expandedGroupId = ref<number | null>(null)
const previewDialogOpen = ref(false)
const previewParams = ref<FeedParams | undefined>(undefined)
const previewTitle = ref<string | undefined>(undefined)
const conflictDialogOpen = ref(false)
const currentConflict = ref<RestoreConflict | null>(null)
const restoringId = ref<number | null>(null)
const editingGroupId = ref<number | null>(null)
const editingGroupName = ref('')
const savingGroupName = ref(false)

const isActiveTab = computed(() => activeTab.value === 'active')
const isTrashTab = computed(() => activeTab.value === 'trash')
const isGroupsTab = computed(() => activeTab.value === 'groups')

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

async function fetchTrash(): Promise<void> {
  loading.value = true
  try {
    trashItems.value = await getTrashItems()
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

async function handleRestore(id: number): Promise<void> {
  restoringId.value = id
  try {
    await restoreSource(id)
    await fetchTrash()
    await fetchSources()
    toast.success(t('trash.restored'))
  } catch (error) {
    if (error instanceof RestoreConflictError) {
      currentConflict.value = {
        conflict: true,
        trash_source: {
          id: error.detail.trash_item.id,
          name: error.detail.trash_item.name,
          url: error.detail.trash_item.url,
        } as TrashItem,
        existing_source: {
          id: error.detail.existing_item.id,
          name: error.detail.existing_item.name,
          url: error.detail.existing_item.url,
        } as Source,
        conflict_type: error.detail.conflict_type,
      }
      conflictDialogOpen.value = true
    } else {
      const message = error instanceof Error ? error.message : t('common.error')
      toast.error(message)
    }
  } finally {
    restoringId.value = null
  }
}

async function handleRestoreOverwrite(): Promise<void> {
  if (!currentConflict.value) return
  
  try {
    await restoreSource(currentConflict.value.trash_source.id, true)
    await fetchTrash()
    await fetchSources()
    toast.success(t('trash.restored'))
  } catch (error) {
    const message = error instanceof Error ? error.message : t('common.error')
    toast.error(message)
  }
  currentConflict.value = null
}

async function handleRestoreKeepExisting(): Promise<void> {
  if (!currentConflict.value) return
  
  try {
    await restoreSource(currentConflict.value.trash_source.id, false)
    await fetchTrash()
    toast.success(t('trash.restored'))
  } catch (error) {
    const message = error instanceof Error ? error.message : t('common.error')
    toast.error(message)
  }
  currentConflict.value = null
}

async function handlePermanentDelete(id: number): Promise<void> {
  const confirmed = await confirm.show({
    title: t('trash.permanent_delete_title'),
    message: t('trash.permanent_delete_confirm'),
    confirmText: t('common.delete'),
    cancelText: t('common.cancel'),
    variant: 'danger'
  })
  if (!confirmed) return
  
  try {
    await permanentDeleteSource(id)
    await fetchTrash()
    toast.success(t('trash.permanently_deleted'))
  } catch {
    toast.error(t('common.error'))
  }
}

async function handleClearTrash(): Promise<void> {
  const confirmed = await confirm.show({
    title: t('trash.clear_title'),
    message: t('trash.clear_confirm'),
    confirmText: t('common.delete'),
    cancelText: t('common.cancel'),
    variant: 'danger'
  })
  if (!confirmed) return
  
  try {
    const result = await clearTrash()
    await fetchTrash()
    toast.success(t('trash.cleared', { count: result.deleted_count }))
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

// Group management
async function fetchGroups(): Promise<void> {
  try {
    groups.value = await getGroups()
  } catch { /* ignore */ }
}

async function fetchGroupSources(groupId: number): Promise<void> {
  try {
    groupSources.value[groupId] = await getGroupSources(groupId)
  } catch { /* ignore */ }
}

function openAddGroupDialog(): void {
  editingGroup.value = null
  newGroupName.value = ''
  showGroupDialog.value = true
}

function startEditGroupName(group: SourceGroup): void {
  editingGroupId.value = group.id
  editingGroupName.value = group.name
}

function cancelEditGroupName(): void {
  editingGroupId.value = null
  editingGroupName.value = ''
}

async function saveGroupName(groupId: number): Promise<void> {
  if (!editingGroupName.value.trim()) {
    toast.error(t('groups.name_required'))
    return
  }
  savingGroupName.value = true
  try {
    await updateGroup(groupId, { name: editingGroupName.value.trim() })
    toast.success(t('groups.updated'))
    editingGroupId.value = null
    editingGroupName.value = ''
    await fetchGroups()
  } catch {
    toast.error(t('common.error'))
  } finally {
    savingGroupName.value = false
  }
}

async function handleSaveGroup(): Promise<void> {
  if (!newGroupName.value.trim()) {
    toast.error(t('groups.name_required'))
    return
  }
  try {
    if (editingGroup.value) {
      await updateGroup(editingGroup.value.id, { name: newGroupName.value })
      toast.success(t('groups.updated'))
    } else {
      await createGroup({ name: newGroupName.value })
      toast.success(t('groups.created'))
    }
    showGroupDialog.value = false
    await fetchGroups()
  } catch {
    toast.error(t('common.error'))
  }
}

async function handleDeleteGroup(id: number): Promise<void> {
  const confirmed = await confirm.show({
    title: t('groups.delete_title'),
    message: t('groups.delete_confirm'),
    confirmText: t('common.delete'),
    cancelText: t('common.cancel'),
    variant: 'danger'
  })
  if (!confirmed) return
  try {
    await deleteGroup(id)
    toast.success(t('groups.deleted'))
    delete groupSources.value[id]
    await fetchGroups()
  } catch {
    toast.error(t('common.error'))
  }
}

async function handleDeleteHistoryByGroup(groupId: number, groupName: string): Promise<void> {
  const confirmed = await confirm.show({
    title: t('history.delete_by_group_title'),
    message: t('history.delete_by_group_confirm', { name: groupName }),
    confirmText: t('common.delete'),
    cancelText: t('common.cancel'),
    variant: 'danger'
  })
  if (!confirmed) return
  try {
    await deleteHistoryByGroup(groupId)
    toast.success(t('history.deleted_by_group'))
  } catch {
    toast.error(t('common.error'))
  }
}

async function handleToggleGroupExpand(groupId: number): Promise<void> {
  if (expandedGroupId.value === groupId) {
    expandedGroupId.value = null
  } else {
    expandedGroupId.value = groupId
    if (!groupSources.value[groupId]) {
      await fetchGroupSources(groupId)
    }
  }
}

async function handleAddSourceToGroup(groupId: number, sourceId: number): Promise<void> {
  try {
    await addSourceToGroup(groupId, sourceId)
    toast.success(t('common.success'))
    await fetchGroupSources(groupId)
    await fetchGroups()
  } catch {
    toast.error(t('common.error'))
  }
}

async function handleRemoveSourceFromGroup(groupId: number, sourceId: number): Promise<void> {
  try {
    await removeSourceFromGroup(groupId, sourceId)
    toast.success(t('common.success'))
    await fetchGroupSources(groupId)
    await fetchGroups()
  } catch {
    toast.error(t('common.error'))
  }
}

const availableSourcesForGroup = computed(() => {
  const groupSourceIds = new Set((groupSources.value[expandedGroupId.value!] || []).map(s => s.id))
  return sources.value.filter(s => !groupSourceIds.has(s.id))
})

async function handleRefreshGroup(groupId: number): Promise<void> {
  try {
    await refreshGroupSources(groupId)
    if (groupSources.value[groupId]) {
      await fetchGroupSources(groupId)
    }
    toast.success(t('common.success'))
  } catch {
    toast.error(t('common.error'))
  }
}

function openPreviewGroupDialog(group: SourceGroup): void {
  previewParams.value = { group_id: group.id }
  previewTitle.value = group.name
  previewDialogOpen.value = true
}

async function handleTabChange(tab: 'active' | 'trash' | 'groups'): Promise<void> {
  activeTab.value = tab
  if (tab === 'active') {
    await fetchSources()
  } else if (tab === 'groups') {
    await fetchGroups()
  } else {
    await fetchTrash()
  }
}

onMounted(async () => {
  await Promise.all([fetchSources(), fetchTrash(), fetchGroups()])
})
</script>

<template>
  <div class="space-y-6 overflow-x-hidden">
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
      <div class="flex items-center gap-2">
        <Radio class="h-6 w-6" />
        <h1 class="text-2xl font-semibold">{{ t('sources.title') }}</h1>
      </div>
      <div class="flex flex-wrap gap-2">
        <template v-if="isActiveTab">
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
            <Plus class="h-4 w-4 mr-2" /> {{ t('sources.add') }}
          </Button>
        </template>
        <template v-else-if="isGroupsTab">
          <Button
            @click="openAddGroupDialog"
            :title="t('groups.add')"
          >
            <FolderPlus class="h-4 w-4 mr-2" /> {{ t('groups.add') }}
          </Button>
        </template>
        <template v-else>
          <Button
            variant="outline"
            :disabled="!trashItems.length"
            :title="t('trash.clear')"
            @click="handleClearTrash"
          >
            <Trash2 class="h-4 w-4 mr-2" />
            {{ t('trash.clear') }}
          </Button>
        </template>
      </div>
    </div>

    <!-- Tab Navigation (sticky on mobile) -->
    <div class="flex border-b border-neutral-200 dark:border-neutral-700 sticky top-16 md:top-0 z-30 bg-white dark:bg-neutral-900 -mx-4 px-4 md:-mx-0 md:px-0">
      <button
        class="px-4 py-2 text-sm font-medium border-b-2 transition-colors"
        :class="activeTab === 'active' 
          ? 'border-blue-500 text-blue-600 dark:text-blue-400' 
          : 'border-transparent text-neutral-500 hover:text-neutral-700 dark:text-neutral-400 dark:hover:text-neutral-300'"
        @click="handleTabChange('active')"
      >
        <Circle class="h-3 w-3 text-green-500 inline-block" /> {{ t('trash.tab_active') }} ({{ sources.length }})
      </button>
      <button
        class="px-4 py-2 text-sm font-medium border-b-2 transition-colors"
        :class="activeTab === 'trash' 
          ? 'border-blue-500 text-blue-600 dark:text-blue-400' 
          : 'border-transparent text-neutral-500 hover:text-neutral-700 dark:text-neutral-400 dark:hover:text-neutral-300'"
        @click="handleTabChange('trash')"
      >
        <Trash2 class="h-4 w-4 inline-block" /> {{ t('trash.tab_trash') }} ({{ trashItems.length }})
      </button>
      <button
        v-if="store.feature_groups"
        class="px-4 py-2 text-sm font-medium border-b-2 transition-colors"
        :class="activeTab === 'groups'
          ? 'border-blue-500 text-blue-600 dark:text-blue-400'
          : 'border-transparent text-neutral-500 hover:text-neutral-700 dark:text-neutral-400 dark:hover:text-neutral-300'"
        @click="handleTabChange('groups')"
      >
        <FolderOpen class="h-4 w-4 inline-block" /> {{ t('groups.title') }} ({{ groups.length }})
      </button>
    </div>
    
    <div v-if="loading" class="text-center py-12 text-neutral-500">
      {{ t('common.loading') }}
    </div>
    
    <!-- Active Sources List -->
    <div v-else-if="activeTab === 'active'">
      <div v-if="!sources.length" class="text-center py-12 text-neutral-500">
        <Inbox class="h-6 w-6 mx-auto mb-3 text-neutral-400" />
        {{ t('sources.empty') }}
      </div>
      <div v-else class="space-y-3">
      <div
        v-for="source in sources"
        :key="source.id"
        class="p-4 bg-white dark:bg-neutral-800 rounded-xl border border-neutral-200 dark:border-neutral-700"
      >
        <div class="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3">
          <div class="flex items-start gap-3 min-w-0 flex-1">
            <Circle class="h-3 w-3 mt-0.5 shrink-0" :class="source.is_active ? 'text-green-500' : 'text-red-500'" />
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
                <Pencil class="h-4 w-4 text-blue-500" />
              </Button>
              <Button
                variant="ghost"
                size="sm"
                :title="t('sources.view_data')"
                @click="openPreviewDialog(source)"
              >
                <FileText class="h-4 w-4 text-purple-500" />
              </Button>
              <Button
                variant="ghost"
                size="sm"
                :title="t('common.refresh')"
                @click="handleRefresh(source.id)"
              >
                <RefreshCw class="h-4 w-4 text-green-500" />
              </Button>
              <Button
                variant="ghost"
                size="sm"
                :title="t('common.delete')"
                @click="handleDelete(source.id)"
              >
                <Trash2 class="h-4 w-4 text-red-500" />
              </Button>
            </div>
          </div>
        </div>
        
        <div class="mt-3 pt-3 border-t border-neutral-100 dark:border-neutral-700">
          <div class="flex flex-col sm:flex-row sm:flex-wrap gap-1 sm:gap-x-4 text-xs sm:text-sm text-neutral-500 dark:text-neutral-400">
            <span class="truncate">
              <Calendar class="h-3 w-3 inline mr-1" />{{ t('sources.created_at') }}: {{ formatDate(source.created_at) }}
            </span>
            <span class="truncate">
              <RotateCw class="h-3 w-3 inline mr-1" />{{ t('sources.updated_at') }}: {{ formatDate(source.updated_at) }}
            </span>
            <span v-if="source.last_fetched_at" class="truncate">
              <Clock class="h-3 w-3 inline mr-1" />{{ t('sources.last_fetched') }}: {{ formatDate(source.last_fetched_at) }}
            </span>
          </div>
          <div v-if="source.last_error" class="mt-2 text-xs sm:text-sm text-red-500 dark:text-red-400 truncate">
            <AlertTriangle class="h-3 w-3 inline mr-1" />{{ source.last_error }}
          </div>
        </div>
      </div>
      </div>
    </div>

    <!-- Trash Items List -->
    <div v-if="isTrashTab && !loading">
      <div v-if="!trashItems.length" class="text-center py-12 text-neutral-500">
        <Inbox class="h-6 w-6 mx-auto mb-3 text-neutral-400" />
        {{ t('trash.empty') }}
      </div>
      <div v-else class="space-y-3">
      <div
        v-for="item in trashItems"
        :key="item.id"
        class="p-4 bg-white dark:bg-neutral-800 rounded-xl border border-neutral-200 dark:border-neutral-700 opacity-75"
      >
        <div class="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3">
          <div class="flex items-start gap-3 min-w-0 flex-1">
            <Trash2 class="h-4 w-4 mt-0.5 shrink-0 text-neutral-400" />
            <div class="min-w-0 flex-1">
              <div class="font-medium truncate">{{ item.name }}</div>
              <div 
                class="text-sm text-neutral-500 dark:text-neutral-400 truncate cursor-help"
                :title="item.url"
              >
                {{ getDisplayUrl(item.url).display }}
              </div>
            </div>
          </div>
          
          <div class="flex items-center gap-3 shrink-0">
            <div class="flex gap-1">
              <Button
                variant="ghost"
                size="sm"
                :title="t('trash.restore')"
                :disabled="restoringId === item.id"
                @click="handleRestore(item.id)"
              >
                <RotateCcw class="h-4 w-4" />
              </Button>
              <Button
                variant="ghost"
                size="sm"
                :title="t('trash.permanent_delete')"
                @click="handlePermanentDelete(item.id)"
              >
                <XCircle class="h-4 w-4 text-red-500" />
              </Button>
            </div>
          </div>
        </div>
        
        <div class="mt-3 pt-3 border-t border-neutral-100 dark:border-neutral-700">
          <div class="flex flex-col sm:flex-row sm:flex-wrap gap-1 sm:gap-x-4 text-xs sm:text-sm text-neutral-500 dark:text-neutral-400">
            <span class="truncate">
              <Trash2 class="h-3 w-3 inline mr-1" />{{ t('trash.deleted_at') }}: {{ formatDate(item.deleted_at) }}
            </span>
          </div>
        </div>
      </div>
      </div>
    </div>

    <!-- Groups Tab -->
    <div v-if="isGroupsTab && !loading && store.feature_groups">
      <div v-if="!groups.length" class="text-center py-12 text-neutral-500">
        <Inbox class="h-6 w-6 mx-auto mb-3 text-neutral-400" />
        {{ t('groups.empty') }}
      </div>
      <div v-else class="space-y-4">
        <div v-for="group in groups" :key="group.id" class="bg-white dark:bg-neutral-800 rounded-xl border border-neutral-200 dark:border-neutral-700 overflow-hidden">
          <!-- Group Header -->
          <div class="p-4">
            <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
              <!-- Name and Badges -->
              <div class="flex items-center gap-2 min-w-0">
                <FolderOpen class="h-5 w-5 text-blue-500 shrink-0" />
                <template v-if="editingGroupId === group.id">
                  <input
                    v-model="editingGroupName"
                    type="text"
                    class="flex-1 px-2 py-1.5 text-base font-semibold bg-white dark:bg-neutral-900 border border-primary-500 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 text-neutral-900 dark:text-neutral-100"
                    :placeholder="t('groups.name_placeholder')"
                    @keydown.enter="saveGroupName(group.id)"
                    @keydown.escape="cancelEditGroupName"
                  />
                  <button
                    type="button"
                    :disabled="savingGroupName"
                    class="p-2 rounded-lg hover:bg-green-100 dark:hover:bg-green-900 text-green-600 dark:text-green-400 disabled:opacity-50"
                    :title="t('common.save')"
                    @click="saveGroupName(group.id)"
                  >
                    <Check v-if="!savingGroupName" class="h-4 w-4" />
                    <RefreshCw v-else class="h-4 w-4 animate-spin" />
                  </button>
                  <button
                    type="button"
                    class="p-2 rounded-lg hover:bg-neutral-100 dark:hover:bg-neutral-700 text-neutral-500 dark:text-neutral-400"
                    :title="t('common.cancel')"
                    @click="cancelEditGroupName"
                  >
                    <X class="h-4 w-4" />
                  </button>
                </template>
                <template v-else>
                  <button
                    class="text-lg font-semibold break-words text-left hover:text-blue-600 dark:hover:text-blue-400 transition-colors min-w-0"
                    @click="handleToggleGroupExpand(group.id)"
                  >
                    {{ group.name }}
                  </button>
                  <div class="flex items-center gap-1.5 shrink-0">
                    <Badge variant="secondary">{{ group.member_count }} {{ t('groups.sources_badge') }}</Badge>
                    <Badge v-if="group.schedule_count" class="text-blue-600 dark:text-blue-400 border-blue-300 dark:border-blue-700 bg-blue-50 dark:bg-blue-950/30">
                      <Clock class="h-3 w-3 mr-0.5" /> {{ group.schedule_count }} {{ t('groups.schedules_badge') }}
                    </Badge>
                  </div>
                </template>
              </div>
              <!-- Action Buttons - Always visible on all screen sizes -->
              <div v-if="editingGroupId !== group.id" class="flex items-center gap-1 shrink-0">
                <Button variant="ghost" size="sm" :title="t('common.refresh')" @click="handleRefreshGroup(group.id)">
                  <RefreshCw class="h-4 w-4 text-green-500" />
                </Button>
                <Button variant="ghost" size="sm" :title="t('sources.view_data')" @click="openPreviewGroupDialog(group)">
                  <FileText class="h-4 w-4 text-purple-500" />
                </Button>
                <Button variant="ghost" size="sm" :title="t('common.edit')" @click="startEditGroupName(group)">
                  <Pencil class="h-4 w-4 text-blue-500" />
                </Button>
                <Button variant="ghost" size="sm" :title="t('common.delete')" @click="handleDeleteGroup(group.id)">
                  <Trash2 class="h-4 w-4 text-red-500" />
                </Button>
                <Button variant="ghost" size="sm" :title="t('history.delete_by_group')" @click="handleDeleteHistoryByGroup(group.id, group.name)">
                  <RotateCcw class="h-4 w-4 text-orange-500" />
                </Button>
                <Button variant="ghost" size="sm" :title="expandedGroupId === group.id ? t('common.collapse') : t('common.expand')" @click="handleToggleGroupExpand(group.id)">
                  <ChevronUp v-if="expandedGroupId === group.id" class="h-4 w-4" />
                  <ChevronDown v-else class="h-4 w-4" />
                </Button>
              </div>
            </div>
          </div>

          <!-- Expanded Content -->
          <div v-if="expandedGroupId === group.id" class="border-t border-neutral-100 dark:border-neutral-700">
            <div class="p-4 space-y-6">
              <!-- Sources Section -->
              <div>
                <div class="flex items-center justify-between mb-3">
                  <div class="flex items-center gap-2">
                    <Radio class="h-4 w-4 text-green-500" />
                    <span class="font-medium text-sm">{{ t('groups.sources_section') }}</span>
                  </div>
                  <TooltipButton :text="t('groups.sources_help')" />
                </div>
                <div v-if="groupSources[group.id]?.length" class="space-y-2 mb-3">
                  <div v-for="s in groupSources[group.id]" :key="s.id" class="flex items-center justify-between text-sm">
                    <span class="truncate flex-1 mr-2">{{ s.name }}</span>
                    <Button variant="ghost" size="sm" :title="t('groups.remove_source')" @click="handleRemoveSourceFromGroup(group.id, s.id)">
                      <XCircle class="h-4 w-4 text-red-500 shrink-0" />
                    </Button>
                  </div>
                </div>
                <div v-else class="text-sm text-neutral-500 mb-3">{{ t('groups.no_sources') }}</div>
                <div v-if="availableSourcesForGroup.length">
                  <select
                    :id="`add-source-${group.id}`"
                    class="w-full text-sm rounded border border-neutral-300 dark:border-neutral-600 bg-white dark:bg-neutral-800 px-3 py-2.5 min-h-[44px]"
                    @change="handleAddSourceToGroup(group.id, Number(($event.target as HTMLSelectElement).value)); ($event.target as HTMLSelectElement).value = ''"
                  >
                    <option value="" disabled>{{ t('groups.add_source') }}</option>
                    <option v-for="s in availableSourcesForGroup" :key="s.id" :value="s.id">{{ s.name }}</option>
                  </select>
                </div>
              </div>

              <!-- Schedule Section (Web only) -->
              <ScheduleConfigPanel v-if="!isTauri() && store.feature_schedules" :group-id="group.id" @saved="() => {}" />
            </div>
          </div>
        </div>
      </div>
    </div>

    <SourceDialog
      v-model:open="showDialog"
      :source="editingSource"
      @saved="handleSaved"
    />

    <!-- Group Dialog (Add only) -->
    <Dialog v-model:open="showGroupDialog">
      <div class="p-6">
        <h2 class="text-xl font-semibold mb-4">
          {{ t('groups.add') }}
        </h2>
        <form class="space-y-4" @submit.prevent="handleSaveGroup">
          <div>
            <label class="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-1">
              {{ t('groups.name') }} *
            </label>
            <Input v-model="newGroupName" :placeholder="t('groups.name_placeholder')" />
          </div>
          <div class="flex justify-end gap-2 pt-4">
            <Button type="button" variant="outline" @click="showGroupDialog = false" :title="t('common.cancel')">
              <X class="h-4 w-4" /> {{ t('common.cancel') }}
            </Button>
            <Button type="submit" :title="t('common.confirm')">
              <Check class="h-4 w-4" /> {{ t('common.confirm') }}
            </Button>
          </div>
        </form>
      </div>
    </Dialog>

    <RssPreviewDialog
      v-model:open="previewDialogOpen"
      :params="previewParams"
      :title="previewTitle"
    />

    <RestoreConflictDialog
      v-model:open="conflictDialogOpen"
      :conflict="currentConflict"
      @overwrite="handleRestoreOverwrite"
      @keep-existing="handleRestoreKeepExisting"
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