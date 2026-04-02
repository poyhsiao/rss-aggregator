<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { Copy, Check, Trash2, Key, Plus } from 'lucide-vue-next'
import { getKeys, deleteKey } from '@/api/keys'
import type { ApiKey } from '@/types/key'
import Button from '@/components/ui/Button.vue'
import Badge from '@/components/ui/Badge.vue'
import KeyDialog from '@/components/KeyDialog.vue'
import ConfirmDialog from '@/components/ui/ConfirmDialog.vue'
import { useToast } from '@/composables/useToast'
import { useConfirm } from '@/composables/useConfirm'

const { t } = useI18n()
const toast = useToast()
const confirm = useConfirm()

const keys = ref<ApiKey[]>([])
const loading = ref(true)
const showDialog = ref(false)
const copiedId = ref<number | null>(null)

async function fetchKeys(): Promise<void> {
  loading.value = true
  try {
    keys.value = await getKeys()
  } finally {
    loading.value = false
  }
}

function handleKeyCreated(key: ApiKey): void {
  keys.value.unshift(key)
}

async function copyToClipboard(text: string, id: number): Promise<void> {
  try {
    await navigator.clipboard.writeText(text)
    copiedId.value = id
    toast.success(t('keys.copied'))
    setTimeout(() => {
      copiedId.value = null
    }, 2000)
  } catch {
    toast.error(t('keys.copy_failed'))
  }
}

async function handleDelete(id: number): Promise<void> {
  const confirmed = await confirm.show({
    title: t('keys.delete_title'),
    message: t('keys.delete_confirm'),
    confirmText: t('common.delete'),
    cancelText: t('common.cancel'),
    variant: 'danger'
  })
  if (!confirmed) return
  
  try {
    await deleteKey(id)
    keys.value = keys.value.filter(k => k.id !== id)
    toast.success(t('keys.deleted'))
  } catch {
    toast.error(t('common.error'))
  }
}

onMounted(fetchKeys)
</script>

<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-semibold"><Key class="h-6 w-6 inline mr-2" />{{ t('keys.title') }}</h1>
      <Button @click="showDialog = true" :title="t('keys.add')">
        <Plus class="h-4 w-4 mr-2" /> {{ t('keys.add') }}
      </Button>
    </div>
    
    <div v-if="loading" class="text-center py-12 text-neutral-500">
      {{ t('common.loading') }}
    </div>
    
    <div v-else-if="!keys.length" class="text-center py-12 text-neutral-500">
      <Key class="h-6 w-6 inline mr-2" />{{ t('keys.empty') }}
    </div>
    
    <div v-else class="space-y-2">
      <div
        v-for="key in keys"
        :key="key.id"
        class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 p-4 bg-white dark:bg-neutral-800 rounded-xl border border-neutral-200 dark:border-neutral-700"
      >
        <div class="flex-1 min-w-0 flex items-center gap-3">
          <code class="text-sm bg-neutral-100 dark:bg-neutral-700 px-2 py-1 rounded block truncate">
            {{ key.key.slice(0, 8) }}...{{ key.key.slice(-4) }}
          </code>
          <span v-if="key.name" class="text-neutral-500 dark:text-neutral-400 truncate">{{ key.name }}</span>
        </div>
        <div class="flex items-center gap-2">
          <Badge :variant="key.is_active ? 'success' : 'secondary'">
            {{ key.is_active ? t('sources.active') : t('sources.inactive') }}
          </Badge>
          <Button
            variant="ghost"
            size="sm"
            class="gap-1"
            :title="t('keys.copy')"
            @click="copyToClipboard(key.key, key.id)"
          >
            <Check v-if="copiedId === key.id" class="h-4 w-4 text-green-500" />
            <Copy v-else class="h-4 w-4" />
            {{ copiedId === key.id ? t('keys.copied') : t('keys.copy') }}
          </Button>
          <Button
            variant="ghost"
            size="sm"
            class="text-red-500 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20"
            :title="t('common.delete')"
            @click="handleDelete(key.id)"
          >
            <Trash2 class="h-4 w-4" />
            {{ t('common.delete') }}
          </Button>
        </div>
      </div>
    </div>

    <KeyDialog
      v-model:open="showDialog"
      @created="handleKeyCreated"
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