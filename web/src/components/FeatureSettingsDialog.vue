<script setup lang="ts">
import { ref, watch } from 'vue'
import { useAppSettings } from '@/composables/useAppSettings'
import { useToast } from '@/composables/useToast'
import Dialog from '@/components/ui/Dialog.vue'
import Button from '@/components/ui/Button.vue'
import { SwitchRoot, SwitchThumb } from 'radix-vue'
import { Settings } from 'lucide-vue-next'

const dialogOpen = defineModel<boolean>('open', { required: true })
const { settings, loading, saveSettings } = useAppSettings()
const toast = useToast()

const localGroup = ref(false)
const localSchedule = ref(false)
const localShare = ref(false)

function syncFromStore() {
  localGroup.value = settings.value.group_enabled
  localSchedule.value = settings.value.schedule_enabled
  localShare.value = settings.value.share_enabled
}

async function handleApply() {
  await saveSettings({
    group_enabled: localGroup.value,
    schedule_enabled: localSchedule.value,
    share_enabled: localShare.value,
  })
  toast.success('已套用設定')
  setTimeout(() => {
    window.location.reload()
  }, 500)
}

function handleClose() {
  dialogOpen.value = false
}

watch(dialogOpen, (open) => {
  if (open) syncFromStore()
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
            v-model="localGroup"
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
            v-model="localSchedule"
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
            v-model="localShare"
            class="relative inline-flex h-6 w-11 shrink-0 cursor-pointer items-center rounded-full border-2 border-transparent transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 data-[state=checked]:bg-primary-600 data-[state=unchecked]:bg-neutral-200 dark:data-[state=unchecked]:bg-neutral-700"
          >
            <SwitchThumb class="pointer-events-none block h-5 w-5 rounded-full bg-white shadow-lg ring-0 transition-transform data-[state=checked]:translate-x-5 data-[state=unchecked]:translate-x-0" />
          </SwitchRoot>
        </div>
      </div>

      <!-- Footer actions -->
      <div class="flex justify-end gap-2 mt-6 pt-4 border-t border-neutral-200 dark:border-neutral-700">
        <Button variant="outline" size="sm" @click="handleClose">
          {{ $t('featureSettings.cancel') }}
        </Button>
        <Button size="sm" :disabled="loading" @click="handleApply">
          {{ $t('featureSettings.apply') }}
        </Button>
      </div>
    </div>
  </Dialog>
</template>
