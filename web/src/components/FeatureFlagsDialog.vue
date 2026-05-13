<script setup lang="ts">
import { ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import Dialog from '@/components/ui/Dialog.vue'
import Button from '@/components/ui/Button.vue'
import { useFeatureFlagsStore } from '@/stores/featureFlags'

const { t } = useI18n()
const store = useFeatureFlagsStore()

const props = defineProps<{ open: boolean }>()
const emit = defineEmits<{ (e: 'update:open', value: boolean): void }>()

const showCascadeWarning = ref(false)

const localGroupsEnabled = ref(store.groupsEnabled)
const localSchedulesEnabled = ref(store.groupSchedulesEnabled)

watch(() => props.open, (val) => {
  if (val) {
    localGroupsEnabled.value = store.groupsEnabled
    localSchedulesEnabled.value = store.groupSchedulesEnabled
    showCascadeWarning.value = false
  }
})

function handleGroupsToggle(val: boolean) {
  localGroupsEnabled.value = val
  if (!val && store.groupSchedulesEnabled) {
    showCascadeWarning.value = true
  } else {
    showCascadeWarning.value = false
    store.groupsEnabled = val
    localSchedulesEnabled.value = store.groupSchedulesEnabled
  }
}

function handleSchedulesToggle(val: boolean) {
  localSchedulesEnabled.value = val
  store.groupSchedulesEnabled = val
}

function handleCascadeConfirm() {
  store.groupsEnabled = false
  localSchedulesEnabled.value = false
  showCascadeWarning.value = false
  emit('update:open', false)
}

function handleCascadeCancel() {
  localGroupsEnabled.value = true
  showCascadeWarning.value = false
}

function handleConfirm() {
  store.groupsEnabled = localGroupsEnabled.value
  store.groupSchedulesEnabled = localSchedulesEnabled.value
  emit('update:open', false)
}

function handleClose() {
  if (showCascadeWarning.value) {
    handleCascadeCancel()
  }
  emit('update:open', false)
}
</script>

<template>
  <Dialog :open="open" size="sm" @update:open="handleClose">
    <template #header>
      <span class="flex items-center gap-2">
        <span>🔧</span>
        {{ t('featureFlags.title') }}
      </span>
    </template>

    <div class="space-y-4">
      <!-- Groups Feature Toggle -->
      <div class="flex items-start justify-between gap-3">
        <div class="flex-1">
          <div class="font-medium">{{ t('featureFlags.groupsEnabled') }}</div>
          <div class="text-sm text-neutral-500">{{ t('featureFlags.groupsEnabledDesc') }}</div>
        </div>
        <button
          type="button"
          class="relative inline-flex h-6 w-11 items-center rounded-full transition-colors"
          :class="localGroupsEnabled ? 'bg-purple-600' : 'bg-neutral-300 dark:bg-neutral-600'"
          @click="handleGroupsToggle(!localGroupsEnabled)"
        >
          <span
            class="inline-block h-4 w-4 transform rounded-full bg-white transition-transform"
            :class="localGroupsEnabled ? 'translate-x-6' : 'translate-x-1'"
          />
        </button>
      </div>

      <!-- Cascade Warning (inline) -->
      <div
        v-if="showCascadeWarning"
        class="rounded-lg border border-amber-300 dark:border-amber-600 bg-amber-50 dark:bg-amber-950/30 p-3 space-y-3"
      >
        <div class="flex items-start gap-2">
          <span class="text-amber-500 mt-0.5">⚠️</span>
          <div class="text-sm">{{ t('featureFlags.cascadeWarningTitle') }}</div>
        </div>
        <div class="flex gap-2">
          <Button size="sm" @click="handleCascadeConfirm">
            {{ t('featureFlags.cascadeWarningConfirm') }}
          </Button>
          <Button size="sm" variant="secondary" @click="handleCascadeCancel">
            {{ t('featureFlags.cascadeWarningCancel') }}
          </Button>
        </div>
      </div>

      <!-- Group Schedules Toggle -->
      <div class="flex items-start justify-between gap-3">
        <div class="flex-1">
          <div class="font-medium">{{ t('featureFlags.groupSchedulesEnabled') }}</div>
          <div class="text-sm text-neutral-500">
            {{ store.groupsEnabled ? t('featureFlags.groupSchedulesEnabledDesc') : t('featureFlags.schedulesDisabledHint') }}
          </div>
        </div>
        <button
          type="button"
          class="relative inline-flex h-6 w-11 items-center rounded-full transition-colors"
          :class="[
            localSchedulesEnabled
              ? 'bg-purple-600'
              : 'bg-neutral-300 dark:bg-neutral-600',
            !localGroupsEnabled && 'opacity-50 cursor-not-allowed'
          ]"
          :disabled="!localGroupsEnabled"
          @click="localGroupsEnabled && handleSchedulesToggle(!localSchedulesEnabled)"
        >
          <span
            class="inline-block h-4 w-4 transform rounded-full bg-white transition-transform"
            :class="localSchedulesEnabled ? 'translate-x-6' : 'translate-x-1'"
          />
        </button>
      </div>
    </div>

    <template #footer>
      <Button @click="handleConfirm">
        {{ t('featureFlags.confirm') }}
      </Button>
    </template>
  </Dialog>
</template>