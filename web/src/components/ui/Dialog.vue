<script setup lang="ts">
import { computed } from 'vue'
import { watch } from 'vue'
import { cn } from '@/utils/cn'

const props = withDefaults(defineProps<{
  open: boolean
  size?: 'sm' | 'md' | 'lg' | 'xl' | '2xl'
  titleId?: string
}>(), {
  open: false,
  size: 'lg',
  titleId: 'dialog-title',
})

const emit = defineEmits<{
  (e: 'update:open', value: boolean): void
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

const sizeClasses = computed(() => {
  const sizes = {
    sm: 'max-w-sm',
    md: 'max-w-md',
    lg: 'max-w-lg',
    xl: 'max-w-xl',
    '2xl': 'max-w-2xl',
  }
  return sizes[props.size]
})
</script>

<template>
  <Teleport to="body">
    <Transition name="dialog">
      <div v-if="open" class="fixed inset-0 z-50" role="dialog" aria-modal="true" :aria-labelledby="titleId">
        <!-- Backdrop -->
        <div 
          class="fixed inset-0 bg-black/50 backdrop-blur-sm transition-opacity"
          @click="close"
        />
        <!-- Dialog container -->
        <div class="fixed inset-0 flex items-center justify-center p-4">
          <div 
            :id="titleId"
            :class="cn(
              'relative w-full bg-white dark:bg-neutral-800 rounded-2xl shadow-2xl',
              sizeClasses,
              'max-h-[90vh] flex flex-col',
              'min-w-[320px] md:min-w-[400px]'
            )"
            @click.stop
          >
            <!-- Header -->
            <div v-if="$slots.header" class="flex-shrink-0 flex items-center justify-between px-6 py-4 border-b border-neutral-200 dark:border-neutral-700">
              <slot name="header" />
            </div>
            <!-- Default slot (scrollable content) -->
            <div class="flex-1 overflow-y-auto">
              <slot />
            </div>
            <!-- Footer -->
            <div v-if="$slots.footer" class="flex-shrink-0 px-6 py-4 border-t border-neutral-200 dark:border-neutral-700 bg-neutral-50 dark:bg-neutral-800/50">
              <slot name="footer" />
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