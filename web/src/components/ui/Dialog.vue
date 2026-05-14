<script setup lang="ts">
import { computed, watch, onUnmounted } from 'vue'
import { cn } from '@/utils/cn'

let dialogInstanceCounter = 0

const props = withDefaults(defineProps<{
  open: boolean
  size?: 'sm' | 'md' | 'lg' | 'xl' | '2xl'
  titleId?: string
}>(), {
  open: false,
  size: 'lg',
  titleId: '',
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

onUnmounted(() => {
  document.body.style.overflow = ''
})

const instanceId = props.titleId || `dialog-title-${++dialogInstanceCounter}`
const resolvedTitleId = computed(() => instanceId)

function close(): void {
  emit('update:open', false)
}

const sizeClasses = computed(() => {
  const sizes = {
    sm: 'max-w-md',
    md: 'max-w-lg',
    lg: 'max-w-xl',
    xl: 'max-w-2xl',
    '2xl': 'max-w-3xl',
  }
  return sizes[props.size]
})
</script>

<template>
  <Teleport to="body">
    <Transition name="dialog">
      <div v-if="open" class="fixed inset-0 z-50" role="dialog" aria-modal="true" :aria-labelledby="resolvedTitleId">
        <!-- Backdrop -->
        <div 
          class="fixed inset-0 bg-black/50 backdrop-blur-sm transition-opacity"
          @click="close"
        />
        <!-- Dialog container -->
        <div class="fixed inset-0 flex items-center justify-center p-4">
          <div 
            :id="resolvedTitleId"
            :class="cn(
              'relative w-full bg-white dark:bg-neutral-800 rounded-2xl shadow-2xl',
              sizeClasses,
              'max-h-[90vh] flex flex-col',
              'min-w-[380px] md:min-w-[480px]'
            )"
            @click.stop
          >
            <!-- Header -->
            <div v-if="$slots.header" class="flex-shrink-0 px-8 py-6 border-b border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-800">
              <slot name="header" />
            </div>
            <!-- Default slot (scrollable content) -->
            <div class="flex-1 overflow-y-auto bg-white dark:bg-neutral-800">
              <slot />
            </div>
            <!-- Footer -->
            <div v-if="$slots.footer" class="flex-shrink-0 px-8 py-6 border-t border-neutral-200 dark:border-neutral-700 bg-neutral-50 dark:bg-neutral-800/50">
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