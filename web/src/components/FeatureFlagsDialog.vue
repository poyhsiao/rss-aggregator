<script setup lang="ts">
import { ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { Settings, Users, Clock, CalendarClock, AlertTriangle, X } from 'lucide-vue-next'
import Dialog from '@/components/ui/Dialog.vue'
import Toggle from '@/components/ui/Toggle.vue'
import Button from '@/components/ui/Button.vue'
import { useFeatureFlagsStore } from '@/stores/featureFlags'

const { t } = useI18n()
const store = useFeatureFlagsStore()

const props = defineProps<{ open: boolean }>()
const emit = defineEmits<{ (e: 'update:open', value: boolean): void }>()

const showCascadeWarning = ref(false)

const localGroupsEnabled = ref(store.groupsEnabled)
const localSchedulesEnabled = ref(store.groupSchedulesEnabled)
const localSourceGroupSchedulesEnabled = ref(store.sourceGroupSchedulesEnabled)

watch(() => props.open, (val) => {
  if (val) {
    localGroupsEnabled.value = store.groupsEnabled
    localSchedulesEnabled.value = store.groupSchedulesEnabled
    localSourceGroupSchedulesEnabled.value = store.sourceGroupSchedulesEnabled
    showCascadeWarning.value = false
  }
})

function handleGroupsToggle(val: boolean) {
  if (val) {
    localGroupsEnabled.value = val
    showCascadeWarning.value = false
  } else {
    if (store.groupSchedulesEnabled || store.sourceGroupSchedulesEnabled) {
      localGroupsEnabled.value = val
      showCascadeWarning.value = true
    } else {
      localGroupsEnabled.value = val
      showCascadeWarning.value = false
    }
  }
}

function handleSchedulesToggle(val: boolean) {
  localSchedulesEnabled.value = val
  store.groupSchedulesEnabled = val
}

function handleSourceGroupSchedulesToggle(val: boolean) {
  localSourceGroupSchedulesEnabled.value = val
  store.sourceGroupSchedulesEnabled = val
}

function handleCascadeConfirm() {
  localSchedulesEnabled.value = false
  localSourceGroupSchedulesEnabled.value = false
  showCascadeWarning.value = false
}

function handleCascadeCancel() {
  localGroupsEnabled.value = true
  showCascadeWarning.value = false
}

function handleConfirm() {
  store.groupsEnabled = localGroupsEnabled.value
  store.groupSchedulesEnabled = localSchedulesEnabled.value
  store.sourceGroupSchedulesEnabled = localSourceGroupSchedulesEnabled.value
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
  <Dialog :open="open" size="lg" @update:open="handleClose">
    <template #header>
      <div class="flex items-center justify-between w-full gap-4">
        <div class="flex items-center gap-2 text-lg font-semibold text-neutral-900 dark:text-neutral-100">
          <Settings class="h-5 w-5" />
          <span>{{ t('featureFlags.title') }}</span>
        </div>
        <button
          type="button"
          class="p-1.5 rounded-lg text-neutral-400 hover:text-neutral-700 hover:bg-neutral-100 dark:hover:text-neutral-200 dark:hover:bg-neutral-700 transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-primary-500"
          @click="handleClose"
          :title="t('common.close')"
        >
          <X class="w-5 h-5" />
        </button>
      </div>
    </template>

    <div class="space-y-3">
      <!-- Groups Feature Toggle -->
      <div class="p-3 bg-neutral-100 dark:bg-neutral-700 rounded-lg flex items-start justify-between gap-4">
        <div class="flex items-start gap-3">
          <Users class="h-5 w-5 text-neutral-500 mt-0.5" />
          <div>
            <div class="font-medium text-neutral-900 dark:text-neutral-100 mb-1">
              {{ t('featureFlags.groupsEnabled') }}
            </div>
            <div class="text-xs text-neutral-500 dark:text-neutral-400">
              {{ t('featureFlags.groupsEnabledDesc') }}
            </div>
          </div>
        </div>
        <Toggle v-model="localGroupsEnabled" @update:model-value="handleGroupsToggle" />
      </div>

      <!-- Group Schedules Toggle -->
      <div
        class="p-3 bg-neutral-100 dark:bg-neutral-700 rounded-lg flex items-start justify-between gap-4"
        :class="{ 'opacity-60': !localGroupsEnabled }"
      >
        <div class="flex items-start gap-3">
          <Clock class="h-5 w-5 text-neutral-500 mt-0.5" />
          <div>
            <div class="font-medium text-neutral-900 dark:text-neutral-100 mb-1">
              {{ t('featureFlags.groupSchedulesEnabled') }}
            </div>
            <div class="text-xs text-neutral-500 dark:text-neutral-400">
              {{ t('featureFlags.groupSchedulesEnabledDesc') }}
            </div>
          </div>
        </div>
        <Toggle
          v-model="localSchedulesEnabled"
          @update:model-value="handleSchedulesToggle"
          :disabled="!localGroupsEnabled"
        />
      </div>

      <!-- Source Group Schedules Toggle -->
      <div
        class="p-3 bg-neutral-100 dark:bg-neutral-700 rounded-lg flex items-start justify-between gap-4"
        :class="{ 'opacity-60': !localGroupsEnabled }"
      >
        <div class="flex items-start gap-3">
          <CalendarClock class="h-5 w-5 text-neutral-500 mt-0.5" />
          <div>
            <div class="font-medium text-neutral-900 dark:text-neutral-100 mb-1">
              {{ t('featureFlags.sourceGroupSchedulesEnabled') }}
            </div>
            <div class="text-xs text-neutral-500 dark:text-neutral-400">
              {{ t('featureFlags.sourceGroupSchedulesEnabledDesc') }}
            </div>
          </div>
        </div>
        <Toggle
          v-model="localSourceGroupSchedulesEnabled"
          @update:model-value="handleSourceGroupSchedulesToggle"
          :disabled="!localGroupsEnabled"
        />
      </div>

      <!-- Cascade Warning -->
      <div
        v-if="showCascadeWarning"
        class="p-3 bg-amber-50 dark:bg-amber-900/30 rounded-lg border border-amber-300 dark:border-amber-700"
      >
        <div class="flex items-start gap-3">
          <AlertTriangle class="h-5 w-5 text-amber-600 dark:text-amber-400 mt-0.5" />
          <div class="flex-1">
            <div class="text-sm font-medium text-amber-800 dark:text-amber-200 mb-3">
              {{ t('featureFlags.cascadeWarningTitle') }}
            </div>
            <div class="flex gap-2">
              <Button size="sm" variant="default" @click="handleCascadeConfirm">
                {{ t('featureFlags.cascadeWarningConfirm') }}
              </Button>
              <Button size="sm" variant="outline" @click="handleCascadeCancel">
                {{ t('featureFlags.cascadeWarningCancel') }}
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <template #footer>
      <div class="flex justify-end gap-2">
        <Button variant="outline" @click="handleClose">
          {{ t('common.cancel') }}
        </Button>
        <Button variant="default" @click="handleConfirm">
          {{ t('featureFlags.confirm') }}
        </Button>
      </div>
    </template>
  </Dialog>
</template>
