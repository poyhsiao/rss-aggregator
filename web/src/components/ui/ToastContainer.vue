<script setup lang="ts">
import ToastItem from './ToastItem.vue'
import { useToast } from '@/composables/useToast'

const toast = useToast()
</script>

<template>
  <Teleport to="body">
    <TransitionGroup
      name="toast"
      tag="div"
      class="fixed top-4 right-4 z-[100] flex flex-col gap-2 max-w-sm w-full pointer-events-none"
    >
      <div
        v-for="t in toast.toasts.value"
        :key="t.id"
        class="pointer-events-auto"
      >
        <ToastItem :toast="t" @remove="toast.remove" />
      </div>
    </TransitionGroup>
  </Teleport>
</template>

<style scoped>
.toast-enter-active {
  animation: toast-in 0.3s ease-out;
}

.toast-leave-active {
  animation: toast-out 0.2s ease-in forwards;
}

@keyframes toast-in {
  from {
    opacity: 0;
    transform: translateX(100%);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

@keyframes toast-out {
  from {
    opacity: 1;
    transform: translateX(0);
  }
  to {
    opacity: 0;
    transform: translateX(100%);
  }
}
</style>