<script setup lang="ts">
import { computed, ref } from 'vue'
import {
  PopoverRoot,
  PopoverTrigger,
  PopoverContent,
  PopoverArrow,
} from 'radix-vue'
import { ChevronDown, X, Check } from 'lucide-vue-next'
import { cn } from '@/utils/cn'

export interface MultiSelectOption {
  value: string | number
  label: string
}

const props = withDefaults(defineProps<{
  modelValue: (string | number)[]
  options: MultiSelectOption[]
  placeholder?: string
  maxDisplay?: number
}>(), {
  placeholder: 'Select options',
  maxDisplay: 3,
})

const emit = defineEmits<{
  (e: 'update:modelValue', value: (string | number)[]): void
}>()

const open = ref(false)

const selectedLabels = computed(() => {
  return props.modelValue
    .map(v => props.options.find(o => o.value === v)?.label)
    .filter(Boolean) as string[]
})

const displayText = computed(() => {
  if (selectedLabels.value.length === 0) return props.placeholder
  if (selectedLabels.value.length <= props.maxDisplay) {
    return selectedLabels.value.join(', ')
  }
  return `${selectedLabels.value.slice(0, props.maxDisplay).join(', ')} +${selectedLabels.value.length - props.maxDisplay}`
})

function toggle(value: string | number) {
  const idx = props.modelValue.indexOf(value)
  if (idx > -1) {
    emit('update:modelValue', props.modelValue.filter(v => v !== value))
  } else {
    emit('update:modelValue', [...props.modelValue, value])
  }
}

function isSelected(value: string | number): boolean {
  return props.modelValue.includes(value)
}

function clearAll() {
  emit('update:modelValue', [])
}
</script>

<template>
  <PopoverRoot :open="open" @update:open="open = $event">
    <PopoverTrigger as-child>
      <button
        type="button"
        :class="cn(
          'flex min-h-[44px] w-full items-center justify-between rounded-xl border border-neutral-200',
          'bg-white px-3 py-2 text-sm',
          'focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2',
          'dark:border-neutral-700 dark:bg-neutral-800 dark:text-neutral-100',
          selectedLabels.length === 0 && 'text-neutral-400 dark:text-neutral-500'
        )"
      >
        <span class="truncate">{{ displayText }}</span>
        <div class="flex items-center gap-1 ml-2 shrink-0">
          <button
            v-if="selectedLabels.length > 0"
            type="button"
            class="p-0.5 rounded hover:bg-neutral-200 dark:hover:bg-neutral-600"
            @click.stop="clearAll"
          >
            <X class="h-3.5 w-3.5" />
          </button>
          <ChevronDown class="h-4 w-4 opacity-50" />
        </div>
      </button>
    </PopoverTrigger>

    <PopoverContent
      :class="cn(
        'relative z-50 w-[var(--radix-popover-trigger-width)] rounded-xl border border-neutral-200',
        'bg-white shadow-lg',
        'dark:border-neutral-700 dark:bg-neutral-800'
      )"
      :side-offset="4"
    >
      <PopoverArrow class="fill-white dark:fill-neutral-800" />

      <!-- Selected Tags -->
      <div v-if="selectedLabels.length > 0" class="flex flex-wrap gap-1.5 p-2 border-b border-neutral-100 dark:border-neutral-700">
        <span
          v-for="label in selectedLabels"
          :key="label"
          class="inline-flex items-center gap-1 px-2 py-0.5 text-xs rounded-md bg-primary-50 text-primary-700 dark:bg-primary-900/30 dark:text-primary-300"
        >
          {{ label }}
          <button
            type="button"
            class="hover:text-primary-900 dark:hover:text-primary-100"
            @click="toggle(options.find(o => o.label === label)?.value ?? '')"
          >
            <X class="h-3 w-3" />
          </button>
        </span>
      </div>

      <!-- Options List -->
      <div class="max-h-60 overflow-y-auto p-1">
        <button
          v-for="option in options"
          :key="option.value"
          type="button"
          :class="cn(
            'relative flex w-full cursor-pointer select-none items-center rounded-lg px-3 py-2.5 text-sm',
            'outline-none hover:bg-neutral-100',
            'dark:hover:bg-neutral-700',
            isSelected(option.value) && 'bg-primary-50 text-primary-700 dark:bg-primary-900/20 dark:text-primary-300'
          )"
          @click="toggle(option.value)"
        >
          <span class="absolute left-2 flex h-4 w-4 items-center justify-center">
            <Check v-if="isSelected(option.value)" class="h-4 w-4 text-primary-600" />
          </span>
          <span class="pl-6">{{ option.label }}</span>
        </button>
      </div>
    </PopoverContent>
  </PopoverRoot>
</template>
