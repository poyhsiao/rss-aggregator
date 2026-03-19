<script setup lang="ts">
import { computed } from 'vue'
import { cn } from '@/utils/cn'

withDefaults(defineProps<{
  modelValue?: string
  type?: string
  placeholder?: string
  disabled?: boolean
}>(), {
  modelValue: '',
  type: 'text',
  placeholder: '',
  disabled: false,
})

const emit = defineEmits<{
  (e: 'update:modelValue', value: string): void
}>()

const inputClasses = computed(() =>
  cn(
    'flex h-10 w-full rounded-md border border-neutral-200 bg-white px-3 py-2 text-sm',
    'placeholder:text-neutral-400',
    'focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent',
    'disabled:cursor-not-allowed disabled:opacity-50',
    'dark:border-neutral-700 dark:bg-neutral-800 dark:text-neutral-100'
  )
)

function onInput(event: Event): void {
  const target = event.target as HTMLInputElement
  emit('update:modelValue', target.value)
}
</script>

<template>
  <input
    :type="type"
    :value="modelValue"
    :placeholder="placeholder"
    :disabled="disabled"
    :class="inputClasses"
    @input="onInput"
  />
</template>