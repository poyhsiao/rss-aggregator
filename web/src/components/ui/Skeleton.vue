<script setup lang="ts">
import { computed } from 'vue'
import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from '@/utils/cn'

const skeletonVariants = cva(
  'animate-pulse rounded-md bg-neutral-200 dark:bg-neutral-800',
  {
    variants: {
      size: {
        sm: 'h-4 w-4',
        md: 'h-6 w-6',
        lg: 'h-8 w-8',
        full: 'w-full',
      },
      shape: {
        text: 'h-4 w-full rounded-sm',
        circular: 'rounded-full',
        rectangular: 'rounded-md',
      },
    },
    defaultVariants: {
      size: 'md',
      shape: 'rectangular',
    },
  }
)

type SkeletonVariants = VariantProps<typeof skeletonVariants>

const props = withDefaults(defineProps<{
  size?: SkeletonVariants['size']
  shape?: SkeletonVariants['shape']
  class?: string
}>(), {
  size: 'md',
  shape: 'rectangular',
})

const classes = computed(() => cn(skeletonVariants({ size: props.size, shape: props.shape }), props.class))
</script>

<template>
  <div :class="classes" />
</template>
