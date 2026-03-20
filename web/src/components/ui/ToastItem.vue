<script setup lang="ts">
import { computed } from 'vue'
import { CheckCircle, XCircle, Info, AlertTriangle, X } from 'lucide-vue-next'
import { cn } from '@/utils/cn'
import type { ToastMessage, ToastType } from '@/composables/useToast'

const props = defineProps<{
  toast: ToastMessage
}>()

const emit = defineEmits<{
  (e: 'remove', id: string): void
}>()

const iconMap: Record<ToastType, typeof CheckCircle> = {
  success: CheckCircle,
  error: XCircle,
  info: Info,
  warning: AlertTriangle,
}

const colorMap: Record<ToastType, string> = {
  success: 'bg-green-50 border-green-200 text-green-800 dark:bg-green-900/20 dark:border-green-800 dark:text-green-200',
  error: 'bg-red-50 border-red-200 text-red-800 dark:bg-red-900/20 dark:border-red-800 dark:text-red-200',
  info: 'bg-blue-50 border-blue-200 text-blue-800 dark:bg-blue-900/20 dark:border-blue-800 dark:text-blue-200',
  warning: 'bg-yellow-50 border-yellow-200 text-yellow-800 dark:bg-yellow-900/20 dark:border-yellow-800 dark:text-yellow-200',
}

const Icon = computed(() => iconMap[props.toast.type])
const colorClass = computed(() => colorMap[props.toast.type])
</script>

<template>
  <div
    :class="cn(
      'flex items-center gap-3 px-4 py-3 rounded-xl border shadow-lg',
      'animate-in slide-in-from-right-full',
      colorClass
    )"
  >
    <component :is="Icon" class="h-5 w-5 flex-shrink-0" />
    <span class="flex-1 text-sm font-medium">{{ toast.message }}</span>
    <button
      class="flex-shrink-0 p-1 rounded-lg hover:bg-black/10 dark:hover:bg-white/10 transition-colors"
      @click="emit('remove', toast.id)"
    >
      <X class="h-4 w-4" />
    </button>
  </div>
</template>