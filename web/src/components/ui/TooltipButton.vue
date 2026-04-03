<script setup lang="ts">
import { ref } from 'vue'
import { Info, X } from 'lucide-vue-next'

defineProps<{
  text: string
}>()

const open = ref(false)
</script>

<template>
  <div class="relative inline-block">
    <button
      type="button"
      class="p-1.5 rounded-full hover:bg-neutral-100 dark:hover:bg-neutral-700 text-neutral-400 hover:text-neutral-600 dark:hover:text-neutral-300 transition-colors"
      @click="open = !open"
    >
      <Info class="h-3.5 w-3.5" />
    </button>
    <div
      v-if="open"
      class="absolute right-0 top-full mt-1 z-20 w-56 sm:w-64 p-3 bg-neutral-900 dark:bg-neutral-100 text-white dark:text-neutral-900 text-xs rounded-lg shadow-xl"
    >
      <button
        type="button"
        class="absolute top-1 right-1 p-0.5 hover:bg-neutral-700 dark:hover:bg-neutral-300 rounded"
        @click="open = false"
      >
        <X class="h-3 w-3" />
      </button>
      {{ text }}
    </div>
  </div>
</template>
