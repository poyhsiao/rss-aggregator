<script setup lang="ts">
import { ref, watch, watchEffect } from 'vue'
import { useI18n } from 'vue-i18n'
import { useFeatureFlagsStore } from '@/stores/featureFlags'
import { useToast } from '@/composables/useToast'
import Dialog from '@/components/ui/Dialog.vue'
import Button from '@/components/ui/Button.vue'
import CascadeWarningDialog from '@/components/ui/CascadeWarningDialog.vue'
import { SwitchRoot, SwitchThumb } from 'radix-vue'
import { Settings } from 'lucide-vue-next'

const dialogOpen = defineModel<boolean>('open', { required: true })
const store = useFeatureFlagsStore()
const { t } = useI18n()
const toast = useToast()

// Local refs for Apply/Cancel pattern
const localGroup = ref(false)
const localSourceGroupSchedules = ref(false)
const localSchedule = ref(false)
const localShare = ref(false)
const showCascadeWarning = ref(false)

function syncFromStore() {
  localGroup.value = store.groupsEnabled
  localSourceGroupSchedules.value = store.sourceGroupSchedulesEnabled
  localSchedule.value = store.scheduleEnabled
  localShare.value = store.shareEnabled
}

// Cascade: Group OFF → warn if dependents ON
watch(localGroup, (newVal, oldVal) => {
  if (oldVal === true && newVal === false) {
    if (localSourceGroupSchedules.value || localSchedule.value) {
      showCascadeWarning.value = true
    }
  } else if (oldVal === false && newVal === true) {
    showCascadeWarning.value = false
  }
})

function handleCascadeConfirm() {
  localSourceGroupSchedules.value = false
  localSchedule.value = false
  showCascadeWarning.value = false
}

function handleCascadeCancel() {
  localGroup.value = true
  showCascadeWarning.value = false
}

async function handleApply() {
  try {
    if (!localGroup.value) {
      localSourceGroupSchedules.value = false
      localSchedule.value = false
    }
    store.groupsEnabled = localGroup.value
    store.sourceGroupSchedulesEnabled = localSourceGroupSchedules.value
    store.scheduleEnabled = localSchedule.value
    store.shareEnabled = localShare.value
    await store.saveSettings()
    toast.success(t('featureSettings.applied'))
    dialogOpen.value = false
  } catch (e) {
    toast.error(e instanceof Error ? e.message : 'Save failed')
  }
}

function handleClose() {
  if (showCascadeWarning.value) {
    handleCascadeCancel()
  }
  dialogOpen.value = false
}

watchEffect(async () => {
  if (dialogOpen.value) {
    await store.fetchSettings()
    syncFromStore()
  }
})
</script>

<template>
  <Dialog :open="dialogOpen" @update:open="dialogOpen = $event">
    <div class="p-6">
      <!-- Header -->
      <div class="flex items-center justify-between mb-6">
        <div class="flex items-center gap-2">
          <Settings class="h-5 w-5 text-primary-600" />
          <h2 class="text-lg font-semibold">{{ $t('featureSettings.title') }}</h2>
        </div>
        <Button variant="ghost" size="icon" @click="handleClose">
          <span class="sr-only">Close</span>
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>
        </Button>
      </div>

      <!-- Feature toggles -->
      <div class="space-y-5">
        <!-- Group toggle -->
        <div class="flex items-start justify-between gap-4">
          <div class="flex-1">
            <div class="font-medium text-sm">{{ $t('featureSettings.group.label') }}</div>
            <div class="text-xs text-muted-foreground mt-0.5">{{ $t('featureSettings.group.description') }}</div>
          </div>
          <SwitchRoot
            v-model:checked="localGroup"
            class="relative inline-flex h-6 w-11 shrink-0 cursor-pointer items-center rounded-full border-2 border-transparent transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 data-[state=checked]:bg-primary-600 data-[state=unchecked]:bg-neutral-200 dark:data-[state=unchecked]:bg-neutral-700"
          >
            <SwitchThumb class="pointer-events-none block h-5 w-5 rounded-full bg-white shadow-lg ring-0 transition-transform data-[state=checked]:translate-x-5 data-[state=unchecked]:translate-x-0" />
          </SwitchRoot>
        </div>

        <!-- SourceGroupSchedules toggle -->
        <div class="flex items-start justify-between gap-4">
          <div class="flex-1">
            <div class="font-medium text-sm">{{ $t('featureSettings.sourceGroupSchedules.label') }}</div>
            <div class="text-xs text-muted-foreground mt-0.5">{{ $t('featureSettings.sourceGroupSchedules.description') }}</div>
            <div v-if="!localGroup" class="text-xs text-muted-foreground/60 mt-1">
              {{ $t('featureSettings.sourceGroupSchedules.disabledHint') }}
            </div>
          </div>
          <SwitchRoot
            v-model:checked="localSourceGroupSchedules"
            :disabled="!localGroup"
            class="relative inline-flex h-6 w-11 shrink-0 cursor-pointer items-center rounded-full border-2 border-transparent transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 data-[state=checked]:bg-primary-600 data-[state=unchecked]:bg-neutral-200 dark:data-[state=unchecked]:bg-neutral-700"
          >
            <SwitchThumb class="pointer-events-none block h-5 w-5 rounded-full bg-white shadow-lg ring-0 transition-transform data-[state=checked]:translate-x-5 data-[state=unchecked]:translate-x-0" />
          </SwitchRoot>
        </div>

        <!-- Schedule toggle -->
        <div class="flex items-start justify-between gap-4">
          <div class="flex-1">
            <div class="font-medium text-sm">{{ $t('featureSettings.schedule.label') }}</div>
            <div class="text-xs text-muted-foreground mt-0.5">{{ $t('featureSettings.schedule.description') }}</div>
            <div v-if="!localGroup" class="text-xs text-muted-foreground/60 mt-1">
              {{ $t('featureSettings.schedule.disabledHint') }}
            </div>
          </div>
          <SwitchRoot
            v-model:checked="localSchedule"
            :disabled="!localGroup"
            class="relative inline-flex h-6 w-11 shrink-0 cursor-pointer items-center rounded-full border-2 border-transparent transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 data-[state=checked]:bg-primary-600 data-[state=unchecked]:bg-neutral-200 dark:data-[state=unchecked]:bg-neutral-700"
          >
            <SwitchThumb class="pointer-events-none block h-5 w-5 rounded-full bg-white shadow-lg ring-0 transition-transform data-[state=checked]:translate-x-5 data-[state=unchecked]:translate-x-0" />
          </SwitchRoot>
        </div>

        <!-- Share toggle -->
        <div class="flex items-start justify-between gap-4">
          <div class="flex-1">
            <div class="font-medium text-sm">{{ $t('featureSettings.share.label') }}</div>
            <div class="text-xs text-muted-foreground mt-0.5">{{ $t('featureSettings.share.description') }}</div>
          </div>
          <SwitchRoot
            v-model:checked="localShare"
            class="relative inline-flex h-6 w-11 shrink-0 cursor-pointer items-center rounded-full border-2 border-transparent transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 data-[state=checked]:bg-primary-600 data-[state=unchecked]:bg-neutral-200 dark:data-[state=unchecked]:bg-neutral-700"
          >
            <SwitchThumb class="pointer-events-none block h-5 w-5 rounded-full bg-white shadow-lg ring-0 transition-transform data-[state=checked]:translate-x-5 data-[state=unchecked]:translate-x-0" />
          </SwitchRoot>
        </div>
      </div>

      <!-- Cascade Warning -->
      <CascadeWarningDialog
        :open="showCascadeWarning"
        @update:open="showCascadeWarning = $event"
        @confirm="handleCascadeConfirm"
        @cancel="handleCascadeCancel"
      />

      <!-- Footer actions -->
      <div class="flex justify-end gap-2 mt-6 pt-4 border-t border-neutral-200 dark:border-neutral-700">
        <Button variant="outline" size="sm" @click="handleClose">
          {{ $t('featureSettings.cancel') }}
        </Button>
        <Button size="sm" :disabled="store.loading" @click="handleApply">
          {{ $t('featureSettings.apply') }}
        </Button>
      </div>
    </div>
  </Dialog>
</template>
