<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import { AlertTriangle } from 'lucide-vue-next'
import Dialog from '@/components/ui/Dialog.vue'
import Button from '@/components/ui/Button.vue'

const { t } = useI18n()

defineProps<{
  open: boolean
}>()

const emit = defineEmits<{
  (e: 'update:open', value: boolean): void
  (e: 'confirm'): void
  (e: 'cancel'): void
}>()

function handleConfirm() {
  emit('confirm')
}

function handleCancel() {
  emit('cancel')
}

function handleClose() {
  emit('update:open', false)
}
</script>

<template>
  <Dialog :open="open" size="sm" @update:open="handleClose">
    <template #header>
      <div class="flex items-center gap-2 text-lg font-semibold text-amber-800 dark:text-amber-200">
        <AlertTriangle class="h-5 w-5" />
        <span>{{ t('featureFlags.cascadeWarningTitle') }}</span>
      </div>
    </template>

    <div class="py-4">
      <p class="text-sm text-neutral-600 dark:text-neutral-300">
        {{ t('featureFlags.cascadeWarningMessage') }}
      </p>
    </div>

    <template #footer>
      <div class="flex justify-end gap-2">
        <Button variant="outline" @click="handleCancel">
          {{ t('featureFlags.cascadeWarningCancel') }}
        </Button>
        <Button variant="default" @click="handleConfirm">
          {{ t('featureFlags.cascadeWarningConfirm') }}
        </Button>
      </div>
    </template>
  </Dialog>
</template>