<script setup lang="ts">
/**
 * Tooltip Component
 * An accessible tooltip component built with radix-vue
 *
 * Usage:
 * <Tooltip content="Helpful information">
 *   <Button>Hover me</Button>
 * </Tooltip>
 *
 * With custom position:
 * <Tooltip content="Helpful information" side="right">
 *   <Button>Hover me</Button>
 * </Tooltip>
 */
import { computed } from 'vue'
import {
  TooltipRoot,
  TooltipTrigger,
  TooltipPortal,
  TooltipContent,
  TooltipArrow,
  type TooltipContentProps,
} from 'radix-vue'
import { cn } from '@/utils/cn'

withDefaults(defineProps<{
  content: string
  side?: TooltipContentProps['side']
  align?: TooltipContentProps['align']
  alignOffset?: number
  sideOffset?: number
  delayDuration?: number
  disableHoverableContent?: boolean
}>(), {
  side: 'top',
  align: 'center',
  alignOffset: 0,
  sideOffset: 8,
  delayDuration: 200,
  disableHoverableContent: false,
})

const contentClasses = computed(() =>
  cn(
    'relative z-50 max-w-xs rounded-lg border border-neutral-200',
    'bg-white px-3 py-2 text-sm text-neutral-900 shadow-soft-md',
    'data-[state=closed]:animate-fade-out data-[state=closed]:animate-scale-out',
    'data-[state=open]:animate-fade-in data-[state=open]:animate-scale-in',
    'dark:border-neutral-700 dark:bg-neutral-800 dark:text-neutral-100'
  )
)

const arrowClasses = computed(() =>
  cn(
    'fill-white',
    'dark:fill-neutral-800'
  )
)
</script>

<template>
  <TooltipRoot
    :delay-duration="delayDuration"
    :disable-hoverable-content="disableHoverableContent"
  >
    <TooltipTrigger as-child>
      <slot />
    </TooltipTrigger>

    <TooltipPortal>
      <TooltipContent
        :side="side"
        :align="align"
        :align-offset="alignOffset"
        :side-offset="sideOffset"
        :class="contentClasses"
      >
        {{ content }}
        <TooltipArrow
          :width="10"
          :height="10"
          :class="arrowClasses"
        />
      </TooltipContent>
    </TooltipPortal>
  </TooltipRoot>
</template>
