<script setup lang="ts">
import { computed } from 'vue'
import { watch } from 'vue'
import { cn } from '@/utils/cn'

const props = withDefaults(defineProps<{
  open: boolean
  size?: 'sm' | 'md' | 'lg' | 'xl' | '2xl'
}>(), {
  open: false,
  size: 'lg',
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
      <div v-if="open" class="fixed inset-0 z-50">
        <div 
          class="fixed inset-0 bg-black/50 backdrop-blur-sm"
          @click="close"
        />
        <div class="fixed inset-0 flex items-center justify-center p-4">
          <div 
            :class="cn(
              'relative w-full bg-white dark:bg-neutral-800 rounded-2xl shadow-xl',
              sizeClasses,
              'max-h-[85vh] overflow-auto'
            )"
            @click.stop
          >
            <slot />
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