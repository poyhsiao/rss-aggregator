<script setup lang="ts">
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { ChevronDown, Copy, Check, AlertCircle, CheckCircle } from 'lucide-vue-next'
import type { OperationLog, ErrorLog, OperationLogDetails } from '@/types/log'
import { formatDate } from '@/utils/format'

const props = defineProps<{
  log: OperationLog | ErrorLog
}>()

const { t } = useI18n()
const isExpanded = ref(false)
const copied = ref(false)

const isOperationLog = computed(() => 'action' in props.log)

const status = computed(() => props.log.status)
const isError = computed(() => status.value === 'error')

const statusClasses = computed(() => {
  if (isError.value) {
    return 'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800'
  }
  return 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800'
})

const textClasses = computed(() => {
  if (isError.value) {
    return 'text-red-700 dark:text-red-400'
  }
  return 'text-green-700 dark:text-green-400'
})

const title = computed(() => {
  if (isOperationLog.value) {
    const opLog = props.log as OperationLog
    return t(`logs.actions.${opLog.action}`)
  }
  const errLog = props.log as ErrorLog
  return errLog.log_type
})

const subtitle = computed(() => {
  if (isOperationLog.value) {
    const opLog = props.log as OperationLog
    if (opLog.details.target) {
      return opLog.details.target
    }
  }
  return props.log.message
})

const errorMessage = computed(() => {
  if (isOperationLog.value) {
    const opLog = props.log as OperationLog
    return opLog.details.error || opLog.message
  }
  const errLog = props.log as ErrorLog
  return errLog.details || errLog.message
})

const opLogDetails = computed((): OperationLogDetails | null => {
  if (isOperationLog.value) {
    return (props.log as OperationLog).details
  }
  return null
})

const errLogDetails = computed((): string | null => {
  if (!isOperationLog.value) {
    return (props.log as ErrorLog).details || null
  }
  return null
})

const errLogRequestData = computed((): string | null => {
  if (!isOperationLog.value) {
    return (props.log as ErrorLog).request_data || null
  }
  return null
})

const hasDetails = computed(() => {
  if (isOperationLog.value) {
    const details = opLogDetails.value
    return !!details?.request || !!details?.response || !!details?.error
  }
  return !!errLogDetails.value || !!errLogRequestData.value
})

function toggleExpand() {
  isExpanded.value = !isExpanded.value
}

async function copyError() {
  try {
    await navigator.clipboard.writeText(errorMessage.value)
    copied.value = true
    setTimeout(() => {
      copied.value = false
    }, 2000)
  } catch {
    const textArea = document.createElement('textarea')
    textArea.value = errorMessage.value
    textArea.style.position = 'fixed'
    textArea.style.left = '-999999px'
    document.body.appendChild(textArea)
    textArea.select()
    try {
      document.execCommand('copy')
      copied.value = true
      setTimeout(() => {
        copied.value = false
      }, 2000)
    } catch {
      // Copy failed
    }
    document.body.removeChild(textArea)
  }
}
</script>

<template>
  <div
    class="rounded-xl border transition-all duration-200"
    :class="statusClasses"
  >
    <button
      type="button"
      class="w-full p-4 text-left focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 rounded-xl"
      @click="toggleExpand"
    >
      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
        <div class="flex items-center gap-2">
          <component
            :is="isError ? AlertCircle : CheckCircle"
            class="h-5 w-5 flex-shrink-0"
            :class="textClasses"
          />
          <span class="font-medium" :class="textClasses">
            {{ title }}
          </span>
          <span
            v-if="'items_count' in log && log.items_count !== null"
            class="text-sm opacity-75"
          >
            ({{ log.items_count }} {{ log.items_count === 1 ? t('logs.item') : t('logs.items') }})
          </span>
        </div>
        <div class="flex items-center gap-2">
          <span class="text-sm text-neutral-500 dark:text-neutral-400">
            {{ formatDate('timestamp' in log ? log.timestamp : log.created_at) }}
          </span>
          <ChevronDown
            class="h-5 w-5 text-neutral-400 transition-transform duration-200"
            :class="{ 'rotate-180': isExpanded }"
          />
        </div>
      </div>
      <p class="mt-1 text-sm text-neutral-600 dark:text-neutral-400">
        {{ subtitle }}
      </p>
    </button>

    <Transition
      enter-active-class="transition-all duration-200 ease-out"
      leave-active-class="transition-all duration-200 ease-in"
      enter-from-class="opacity-0 max-h-0"
      leave-to-class="opacity-0 max-h-0"
    >
      <div
        v-if="isExpanded && hasDetails"
        class="border-t border-neutral-200 dark:border-neutral-700 px-4 pb-4 overflow-hidden"
      >
        <div class="pt-3 space-y-3">
          <div v-if="opLogDetails?.request" class="space-y-1">
            <span class="text-xs font-medium text-neutral-500 dark:text-neutral-400 uppercase tracking-wider">
              {{ t('logs.details.request') }}
            </span>
            <pre class="text-xs bg-neutral-100 dark:bg-neutral-900 p-2 rounded-lg overflow-x-auto">{{ JSON.stringify(opLogDetails.request, null, 2) }}</pre>
          </div>

          <div v-if="opLogDetails?.response" class="space-y-1">
            <span class="text-xs font-medium text-neutral-500 dark:text-neutral-400 uppercase tracking-wider">
              {{ t('logs.details.response') }}
            </span>
            <pre class="text-xs bg-neutral-100 dark:bg-neutral-900 p-2 rounded-lg overflow-x-auto">{{ JSON.stringify(opLogDetails.response, null, 2) }}</pre>
          </div>

          <div v-if="opLogDetails?.error" class="space-y-1">
            <span class="text-xs font-medium text-neutral-500 dark:text-neutral-400 uppercase tracking-wider">
              {{ t('logs.details.error') }}
            </span>
            <pre class="text-xs bg-red-100 dark:bg-red-900/30 p-2 rounded-lg overflow-x-auto text-red-700 dark:text-red-400">{{ opLogDetails.error }}</pre>
          </div>

          <div v-if="errLogRequestData" class="space-y-1">
            <span class="text-xs font-medium text-neutral-500 dark:text-neutral-400 uppercase tracking-wider">
              {{ t('logs.details.request_data') }}
            </span>
            <pre class="text-xs bg-neutral-100 dark:bg-neutral-900 p-2 rounded-lg overflow-x-auto">{{ errLogRequestData }}</pre>
          </div>

          <div v-if="errLogDetails" class="space-y-1">
            <span class="text-xs font-medium text-neutral-500 dark:text-neutral-400 uppercase tracking-wider">
              {{ t('logs.details.error') }}
            </span>
            <pre class="text-xs bg-red-100 dark:bg-red-900/30 p-2 rounded-lg overflow-x-auto text-red-700 dark:text-red-400">{{ errLogDetails }}</pre>
          </div>

          <div v-if="isError" class="pt-2">
            <button
              type="button"
              class="inline-flex items-center gap-2 px-3 py-1.5 text-sm font-medium rounded-lg bg-neutral-100 dark:bg-neutral-700 hover:bg-neutral-200 dark:hover:bg-neutral-600 transition-colors"
              @click.stop="copyError"
            >
              <component
                :is="copied ? Check : Copy"
                class="h-4 w-4"
              />
              {{ copied ? t('keys.copied') : t('logs.copy_error') }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>