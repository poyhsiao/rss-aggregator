<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import type { RestoreConflict } from '@/api/trash'
import Dialog from '@/components/ui/Dialog.vue'
import Button from '@/components/ui/Button.vue'

const props = defineProps<{
  open: boolean
  conflict: RestoreConflict | null
}>()

const emit = defineEmits<{
  'update:open': [value: boolean]
  overwrite: []
  keepExisting: []
}>()

const { t } = useI18n()

const existingSource = computed(() => props.conflict?.existing_source)
const trashSource = computed(() => props.conflict?.trash_source)

function handleOverwrite() {
  emit('overwrite')
  emit('update:open', false)
}

function handleKeepExisting() {
  emit('keepExisting')
  emit('update:open', false)
}

function handleClose() {
  emit('update:open', false)
}
</script>

<template>
  <Dialog :open="open" @update:open="emit('update:open', $event)">
    <div class="p-6 space-y-4">
      <h2 class="text-lg font-semibold text-neutral-900 dark:text-neutral-100">
        ⚠️ {{ t('trash.conflict_title') }}
      </h2>
      
      <p class="text-sm text-neutral-600 dark:text-neutral-400">
        {{ t('trash.conflict_description') }}
      </p>

      <div class="space-y-3">
        <div class="p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
          <div class="text-xs font-medium text-blue-600 dark:text-blue-400 mb-1">
            {{ t('trash.existing_source') }}
          </div>
          <div class="font-medium text-neutral-900 dark:text-neutral-100">
            {{ existingSource?.name }}
          </div>
          <div class="text-xs text-neutral-500 dark:text-neutral-400 truncate">
            {{ existingSource?.url }}
          </div>
        </div>

        <div class="p-3 bg-amber-50 dark:bg-amber-900/20 rounded-lg border border-amber-200 dark:border-amber-800">
          <div class="text-xs font-medium text-amber-600 dark:text-amber-400 mb-1">
            {{ t('trash.trash_source') }}
          </div>
          <div class="font-medium text-neutral-900 dark:text-neutral-100">
            {{ trashSource?.name }}
          </div>
          <div class="text-xs text-neutral-500 dark:text-neutral-400 truncate">
            {{ trashSource?.url }}
          </div>
        </div>
      </div>

      <div class="flex flex-col sm:flex-row gap-2 pt-2">
        <Button variant="outline" class="flex-1" @click="handleClose">
          {{ t('common.cancel') }}
        </Button>
        <Button variant="outline" class="flex-1" @click="handleKeepExisting">
          {{ t('trash.keep_existing') }}
        </Button>
        <Button variant="destructive" class="flex-1" @click="handleOverwrite">
          {{ t('trash.overwrite') }}
        </Button>
      </div>
    </div>
  </Dialog>
</template>