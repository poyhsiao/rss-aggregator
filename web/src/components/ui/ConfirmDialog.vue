<script setup lang="ts">
/**
 * ConfirmDialog Component
 * A styled confirmation dialog that replaces browser's native confirm()
 * 
 * Usage with useConfirm composable:
 * const confirm = useConfirm()
 * const result = await confirm.show('Are you sure?', 'Delete item')
 */
import { computed, watch } from 'vue'
import { AlertTriangle, Zap, Info } from 'lucide-vue-next'
import { cn } from '@/utils/cn'

const props = withDefaults(defineProps<{
  open: boolean
  title?: string
  message: string
  confirmText?: string
  cancelText?: string
  variant?: 'danger' | 'warning' | 'info'
}>(), {
  open: false,
  title: '',
  confirmText: 'Confirm',
  cancelText: 'Cancel',
  variant: 'danger',
})

const emit = defineEmits<{
  (e: 'update:open', value: boolean): void
  (e: 'confirm'): void
  (e: 'cancel'): void
}>()

watch(() => props.open, (isOpen) => {
  if (isOpen) {
    document.body.style.overflow = 'hidden'
  } else {
    document.body.style.overflow = ''
  }
})

function close(): void {
  emit('update:open', false)
}

function handleConfirm(): void {
  emit('confirm')
  close()
}

function handleCancel(): void {
  emit('cancel')
  close()
}

const variantClasses = computed(() => {
  const variants = {
    danger: 'bg-red-600 hover:bg-red-700 dark:bg-red-500 dark:hover:bg-red-600',
    warning: 'bg-yellow-600 hover:bg-yellow-700 dark:bg-yellow-500 dark:hover:bg-yellow-600',
    info: 'bg-blue-600 hover:bg-blue-700 dark:bg-blue-500 dark:hover:bg-blue-600',
  }
  return variants[props.variant]
})

const iconComponent = computed(() => {
  const icons = {
    danger: AlertTriangle,
    warning: Zap,
    info: Info,
  }
  return icons[props.variant]
})
</script>

<template>
  <Teleport to="body">
    <Transition name="dialog">
      <div v-if="open" class="fixed inset-0 z-50">
        <div 
          class="fixed inset-0 bg-black/50 backdrop-blur-sm"
          @click="handleCancel"
        />
        <div class="fixed inset-0 flex items-center justify-center p-4">
          <div 
            :class="cn(
              'relative w-full bg-white dark:bg-neutral-800 rounded-2xl shadow-xl',
              'max-w-md',
              'overflow-auto'
            )"
            @click.stop
          >
            <!-- Header -->
            <div class="p-6 pb-0">
              <div class="flex items-start gap-3">
                <component :is="iconComponent" class="h-6 w-6 shrink-0" :class="{
                  'text-red-500': variant === 'danger',
                  'text-yellow-500': variant === 'warning',
                  'text-blue-500': variant === 'info',
                }" />
                <div class="flex-1 min-w-0">
                  <h3 v-if="title" class="text-lg font-semibold text-neutral-900 dark:text-neutral-100">
                    {{ title }}
                  </h3>
                  <p class="text-sm text-neutral-600 dark:text-neutral-400 mt-1">
                    {{ message }}
                  </p>
                </div>
              </div>
            </div>

            <!-- Actions -->
            <div class="flex justify-end gap-2 p-4">
              <button
                type="button"
                class="px-4 py-2 text-sm font-medium rounded-lg border border-neutral-300 dark:border-neutral-600 text-neutral-700 dark:text-neutral-300 bg-white dark:bg-neutral-700 hover:bg-neutral-50 dark:hover:bg-neutral-600 transition-colors"
                @click="handleCancel"
              >
                {{ cancelText }}
              </button>
              <button
                type="button"
                :class="cn(
                  'px-4 py-2 text-sm font-medium rounded-lg text-white transition-colors',
                  variantClasses
                )"
                @click="handleConfirm"
              >
                {{ confirmText }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.dialog-enter-active,
.dialog-leave-active {
  transition: opacity 0.2s ease;
}

.dialog-enter-active .rounded-2xl,
.dialog-leave-active .rounded-2xl {
  transition: transform 0.2s ease;
}

.dialog-enter-from,
.dialog-leave-to {
  opacity: 0;
}

.dialog-enter-from .rounded-2xl,
.dialog-leave-to .rounded-2xl {
  transform: scale(0.95);
}
</style>