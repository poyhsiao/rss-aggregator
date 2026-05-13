<script setup lang="ts">
const props = defineProps<{
  modelValue: boolean
  disabled?: boolean
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
}>()

function toggle() {
  if (!props.disabled) {
    emit('update:modelValue', !props.modelValue)
  }
}
</script>

<template>
  <button
    type="button"
    role="switch"
    class="relative inline-flex h-10 w-18 items-center rounded-full transition-all duration-300 focus:outline-none focus:ring-4 focus:ring-primary-500/30 focus:ring-offset-2"
    :class="[
      modelValue ? 'bg-primary-600 shadow-lg shadow-primary-500/40' : 'bg-neutral-300 dark:bg-neutral-600',
      disabled && 'opacity-50 cursor-not-allowed'
    ]"
    :disabled="disabled"
    :aria-checked="modelValue"
    @click="toggle"
  >
    <span
      class="inline-block h-8 w-8 transform rounded-full bg-white shadow-lg transition-transform duration-300"
      :class="modelValue ? 'translate-x-9' : 'translate-x-1'"
    />
  </button>
</template>
