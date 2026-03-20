<script setup lang="ts">
/**
 * Select Component
 * A dropdown select component built with radix-vue
 * 
 * Usage:
 * <Select v-model="selectedValue" :options="[{ value: '1', label: 'Option 1' }]" />
 */
import { computed } from 'vue'
import {
  SelectRoot,
  SelectTrigger,
  SelectValue,
  SelectPortal,
  SelectContent,
  SelectViewport,
  SelectItem,
  SelectItemText,
  SelectItemIndicator,
} from 'radix-vue'
import { ChevronDown, Check } from 'lucide-vue-next'
import { cn } from '@/utils/cn'

interface SelectOption {
  value: string
  label: string
  disabled?: boolean
}

const props = withDefaults(defineProps<{
  modelValue?: string
  options: SelectOption[]
  placeholder?: string
  disabled?: boolean
}>(), {
  modelValue: '',
  placeholder: 'Select an option',
  disabled: false,
})

const emit = defineEmits<{
  (e: 'update:modelValue', value: string): void
}>()

const selectedLabel = computed(() => {
  const option = props.options.find(opt => opt.value === props.modelValue)
  return option?.label ?? ''
})
</script>

<template>
  <SelectRoot
    :model-value="modelValue"
    :disabled="disabled"
    @update:model-value="emit('update:modelValue', $event)"
  >
    <SelectTrigger
      :class="cn(
        'flex h-10 w-full items-center justify-between rounded-xl border border-neutral-200',
        'bg-white px-3 py-2 text-sm',
        'focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2',
        'disabled:cursor-not-allowed disabled:opacity-50',
        'dark:border-neutral-700 dark:bg-neutral-800 dark:text-neutral-100'
      )"
    >
      <SelectValue :placeholder="placeholder">
        {{ selectedLabel || placeholder }}
      </SelectValue>
      <ChevronDown class="h-4 w-4 opacity-50" />
    </SelectTrigger>

    <SelectPortal>
      <SelectContent
        :class="cn(
          'relative z-50 max-h-96 min-w-[8rem] overflow-hidden rounded-xl border border-neutral-200',
          'bg-white shadow-lg',
          'dark:border-neutral-700 dark:bg-neutral-800'
        )"
        position="popper"
        :side-offset="4"
      >
        <SelectViewport class="p-1">
          <SelectItem
            v-for="option in options"
            :key="option.value"
            :value="option.value"
            :disabled="option.disabled"
            :class="cn(
              'relative flex w-full cursor-pointer select-none items-center rounded-lg py-2 pl-8 pr-2 text-sm',
              'outline-none focus:bg-neutral-100 focus:text-neutral-900',
              'data-[disabled]:pointer-events-none data-[disabled]:opacity-50',
              'dark:focus:bg-neutral-700 dark:focus:text-neutral-100'
            )"
          >
            <span class="absolute left-2 flex h-3.5 w-3.5 items-center justify-center">
              <SelectItemIndicator>
                <Check class="h-4 w-4 text-primary-600" />
              </SelectItemIndicator>
            </span>
            <SelectItemText>{{ option.label }}</SelectItemText>
          </SelectItem>
        </SelectViewport>
      </SelectContent>
    </SelectPortal>
  </SelectRoot>
</template>