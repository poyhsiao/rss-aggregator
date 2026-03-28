<script setup lang="ts">
import { computed, type Component } from 'vue'
import { cn } from '@/utils/cn'

interface Props {
  icon?: string | Component
  title: string
  description?: string
  size?: 'sm' | 'md' | 'lg'
}

const props = withDefaults(defineProps<Props>(), {
  description: '',
  size: 'md',
})

const sizeClasses = computed(() => {
  const sizeMap = {
    sm: {
      container: 'py-8 px-4',
      icon: 'h-8 w-8',
      title: 'text-lg',
      description: 'text-sm',
    },
    md: {
      container: 'py-12 px-6',
      icon: 'h-12 w-12',
      title: 'text-xl',
      description: 'text-base',
    },
    lg: {
      container: 'py-16 px-8',
      icon: 'h-16 w-16',
      title: 'text-2xl',
      description: 'text-lg',
    },
  }
  return sizeMap[props.size]
})

const iconComponent = computed(() => {
  if (typeof props.icon === 'string') {
    // For emoji or string icons
    return null
  }
  return props.icon
})
</script>

<template>
  <div
    :class="cn(
      'flex flex-col items-center justify-center text-center',
      sizeClasses.container,
      $attrs.class as string
    )"
  >
    <!-- Icon -->
    <div
      v-if="icon"
      :class="cn(
        'mb-4 text-neutral-400 dark:text-neutral-600',
        sizeClasses.icon
      )"
    >
      <component
        v-if="iconComponent"
        :is="iconComponent"
        :class="sizeClasses.icon"
      />
      <span v-else class="text-4xl">{{ icon }}</span>
    </div>

    <!-- Title -->
    <h3
      :class="cn(
        'mb-2 font-semibold text-neutral-900 dark:text-neutral-100',
        sizeClasses.title
      )"
    >
      {{ title }}
    </h3>

    <!-- Description -->
    <p
      v-if="description"
      :class="cn(
        'mb-6 max-w-md text-neutral-600 dark:text-neutral-400',
        sizeClasses.description
      )"
    >
      {{ description }}
    </p>

    <!-- Action Slot -->
    <slot name="action" />
  </div>
</template>
