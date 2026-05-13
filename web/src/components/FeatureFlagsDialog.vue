<script setup lang="ts">
import { ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import Dialog from '@/components/ui/Dialog.vue'
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
  <Dialog :open="open" size="xl" @update:open="handleClose">
    <template #header>
      <div class="flex items-center gap-2 text-lg font-semibold text-neutral-900 dark:text-neutral-100">
        <span>🔧</span>
        <span>{{ t('featureFlags.title') }}</span>
      </div>
      <button
        type="button"
        class="p-1.5 rounded-lg text-neutral-400 hover:text-neutral-600 hover:bg-neutral-100 dark:hover:text-neutral-200 dark:hover:bg-neutral-700 transition-colors"
        @click="handleClose"
        :title="t('common.close')"
      >
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
    </template>

    <div class="p-6 space-y-6">
      <!-- Groups Feature Toggle -->
      <div class="flex items-start justify-between gap-4 p-4 rounded-xl bg-neutral-50 dark:bg-neutral-900/50 border border-neutral-200 dark:border-neutral-700">
        <div class="flex-1">
          <div class="font-semibold text-neutral-900 dark:text-neutral-100">{{ t('featureFlags.groupsEnabled') }}</div>
          <div class="text-sm text-neutral-500 mt-1">{{ t('featureFlags.groupsEnabledDesc') }}</div>
        </div>
        <button
          type="button"
          class="relative inline-flex h-7 w-12 items-center rounded-full transition-colors flex-shrink-0 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2"
          :class="localGroupsEnabled ? 'bg-primary-600' : 'bg-neutral-300 dark:bg-neutral-600'"
          @click="handleGroupsToggle(!localGroupsEnabled)"
        >
          <span
            class="inline-block h-5 w-5 transform rounded-full bg-white shadow-sm transition-transform"
            :class="localGroupsEnabled ? 'translate-x-6' : 'translate-x-1'"
          />
        </button>
      </div>

      <!-- Cascade Warning (inline) -->
      <div
        v-if="showCascadeWarning"
        class="rounded-xl border-2 border-amber-400 dark:border-amber-500 bg-amber-50 dark:bg-amber-950/30 p-4 space-y-3"
      >
        <div class="flex items-start gap-3">
          <span class="text-2xl">⚠️</span>
          <div class="flex-1">
            <div class="font-semibold text-amber-800 dark:text-amber-200">{{ t('featureFlags.cascadeWarningTitle') }}</div>
            <div class="flex gap-2 pt-3">
              <button
                type="button"
                class="px-4 py-2 text-sm font-medium rounded-lg bg-amber-600 hover:bg-amber-700 text-white transition-colors focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2"
                @click="handleCascadeConfirm"
              >
                {{ t('featureFlags.cascadeWarningConfirm') }}
              </button>
              <button
                type="button"
                class="px-4 py-2 text-sm font-medium rounded-lg bg-neutral-200 hover:bg-neutral-300 dark:bg-neutral-700 dark:hover:bg-neutral-600 text-neutral-700 dark:text-neutral-200 transition-colors focus:outline-none focus:ring-2 focus:ring-neutral-400 focus:ring-offset-2"
                @click="handleCascadeCancel"
              >
                {{ t('featureFlags.cascadeWarningCancel') }}
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Group Schedules Toggle -->
      <div 
        class="flex items-start justify-between gap-4 p-4 rounded-xl border transition-all"
        :class="localGroupsEnabled 
          ? 'bg-neutral-50 dark:bg-neutral-900/50 border-neutral-200 dark:border-neutral-700' 
          : 'bg-neutral-100/50 dark:bg-neutral-900/20 border-neutral-200/50 dark:border-neutral-700/50 opacity-60'"
      >
        <div class="flex-1">
          <div class="font-semibold text-neutral-900 dark:text-neutral-100">{{ t('featureFlags.groupSchedulesEnabled') }}</div>
          <div class="text-sm mt-1" :class="localGroupsEnabled ? 'text-neutral-500' : 'text-neutral-400'">
            {{ localGroupsEnabled ? t('featureFlags.groupSchedulesEnabledDesc') : t('featureFlags.schedulesDisabledHint') }}
          </div>
        </div>
        <button
          type="button"
          class="relative inline-flex h-7 w-12 items-center rounded-full transition-colors flex-shrink-0 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2"
          :class="[
            localSchedulesEnabled ? 'bg-primary-600' : 'bg-neutral-300 dark:bg-neutral-600',
            !localGroupsEnabled && 'opacity-50 cursor-not-allowed'
          ]"
          :disabled="!localGroupsEnabled"
          @click="localGroupsEnabled && handleSchedulesToggle(!localSchedulesEnabled)"
        >
          <span
            class="inline-block h-5 w-5 transform rounded-full bg-white shadow-sm transition-transform"
            :class="localSchedulesEnabled ? 'translate-x-6' : 'translate-x-1'"
          />
        </button>
      </div>
    </div>

    <template #footer>
      <div class="flex justify-center">
        <button
          type="button"
          class="min-w-[140px] px-6 py-2.5 text-base font-medium rounded-xl bg-primary-600 hover:bg-primary-700 text-white shadow-sm transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2"
          @click="handleConfirm"
        >
          {{ t('featureFlags.confirm') }}
        </button>
      </div>
    </template>
  </Dialog>
</template>