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
  <Dialog :open="open" size="2xl" @update:open="handleClose">
    <template #header>
      <div class="flex items-center justify-between w-full gap-4">
        <div class="flex items-center gap-3 text-xl font-bold text-neutral-900 dark:text-neutral-100">
          <span class="text-2xl">⚙️</span>
          <span>{{ t('featureFlags.title') }}</span>
        </div>
        <button
          type="button"
          class="flex-shrink-0 p-2.5 rounded-xl text-neutral-500 hover:text-neutral-700 hover:bg-neutral-100 dark:text-neutral-400 dark:hover:text-neutral-200 dark:hover:bg-neutral-700 transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-primary-500"
          @click="handleClose"
          :title="t('common.close')"
        >
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
    </template>

    <div class="p-8 space-y-6">
      <!-- Groups Feature Toggle -->
      <div class="flex items-start justify-between gap-6 p-5 rounded-2xl bg-gradient-to-br from-neutral-50 to-neutral-100 dark:from-neutral-800 dark:to-neutral-900 border border-neutral-200 dark:border-neutral-700 shadow-sm">
        <div class="flex-1 min-w-0">
          <div class="flex items-center gap-2 mb-1.5">
            <span class="text-lg">👥</span>
            <div class="font-bold text-base text-neutral-900 dark:text-neutral-100">{{ t('featureFlags.groupsEnabled') }}</div>
          </div>
          <div class="text-sm text-neutral-500 dark:text-neutral-400 leading-relaxed">{{ t('featureFlags.groupsEnabledDesc') }}</div>
        </div>
        <button
          type="button"
          class="relative inline-flex h-8 w-14 items-center rounded-full transition-all duration-300 flex-shrink-0 focus:outline-none focus:ring-4 focus:ring-primary-500/30 focus:ring-offset-2"
          :class="localGroupsEnabled ? 'bg-primary-600 shadow-lg shadow-primary-500/30' : 'bg-neutral-300 dark:bg-neutral-600'"
          @click="handleGroupsToggle(!localGroupsEnabled)"
        >
          <span
            class="inline-block h-6 w-6 transform rounded-full bg-white shadow-lg transition-transform duration-300"
            :class="localGroupsEnabled ? 'translate-x-7' : 'translate-x-1'"
          />
        </button>
      </div>

      <!-- Cascade Warning -->
      <div
        v-if="showCascadeWarning"
        class="p-5 rounded-2xl border-2 border-amber-400 dark:border-amber-500 bg-gradient-to-br from-amber-50 to-orange-50 dark:from-amber-950/50 dark:to-orange-950/50 shadow-lg"
      >
        <div class="flex items-start gap-4">
          <span class="text-3xl flex-shrink-0">⚠️</span>
          <div class="flex-1 min-w-0">
            <div class="font-bold text-amber-900 dark:text-amber-100 mb-3">{{ t('featureFlags.cascadeWarningTitle') }}</div>
            <div class="flex gap-3">
              <button
                type="button"
                class="px-5 py-2.5 text-sm font-semibold rounded-xl bg-amber-600 hover:bg-amber-700 text-white shadow-lg shadow-amber-500/30 transition-all focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2"
                @click="handleCascadeConfirm"
              >
                {{ t('featureFlags.cascadeWarningConfirm') }}
              </button>
              <button
                type="button"
                class="px-5 py-2.5 text-sm font-semibold rounded-xl bg-neutral-200 hover:bg-neutral-300 dark:bg-neutral-700 dark:hover:bg-neutral-600 text-neutral-700 dark:text-neutral-200 transition-all focus:outline-none focus:ring-2 focus:ring-neutral-400 focus:ring-offset-2"
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
        class="flex items-start justify-between gap-6 p-5 rounded-2xl border transition-all duration-300"
        :class="localGroupsEnabled 
          ? 'bg-gradient-to-br from-neutral-50 to-neutral-100 dark:from-neutral-800 dark:to-neutral-900 border-neutral-200 dark:border-neutral-700 shadow-sm' 
          : 'bg-neutral-50/50 dark:bg-neutral-900/50 border-neutral-200/50 dark:border-neutral-700/50 opacity-60'"
      >
        <div class="flex-1 min-w-0">
          <div class="flex items-center gap-2 mb-1.5">
            <span class="text-lg">⏰</span>
            <div class="font-bold text-base text-neutral-900 dark:text-neutral-100">{{ t('featureFlags.groupSchedulesEnabled') }}</div>
          </div>
          <div class="text-sm leading-relaxed" :class="localGroupsEnabled ? 'text-neutral-500 dark:text-neutral-400' : 'text-neutral-400 dark:text-neutral-500'">
            {{ localGroupsEnabled ? t('featureFlags.groupSchedulesEnabledDesc') : t('featureFlags.schedulesDisabledHint') }}
          </div>
        </div>
        <button
          type="button"
          class="relative inline-flex h-8 w-14 items-center rounded-full transition-all duration-300 flex-shrink-0 focus:outline-none focus:ring-4 focus:ring-primary-500/30 focus:ring-offset-2"
          :class="[
            localSchedulesEnabled ? 'bg-primary-600 shadow-lg shadow-primary-500/30' : 'bg-neutral-300 dark:bg-neutral-600',
            !localGroupsEnabled && 'opacity-50'
          ]"
          :disabled="!localGroupsEnabled"
          @click="localGroupsEnabled && handleSchedulesToggle(!localSchedulesEnabled)"
        >
          <span
            class="inline-block h-6 w-6 transform rounded-full bg-white shadow-lg transition-transform duration-300"
            :class="localSchedulesEnabled ? 'translate-x-7' : 'translate-x-1'"
          />
        </button>
      </div>
    </div>

    <template #footer>
      <div class="flex justify-center py-5">
        <button
          type="button"
          class="min-w-[160px] px-8 py-3 text-base font-bold rounded-xl bg-primary-600 hover:bg-primary-700 text-white shadow-lg shadow-primary-500/30 transition-all duration-200 focus:outline-none focus:ring-4 focus:ring-primary-500/30 focus:ring-offset-2"
          @click="handleConfirm"
        >
          {{ t('featureFlags.confirm') }}
        </button>
      </div>
    </template>
  </Dialog>
</template>