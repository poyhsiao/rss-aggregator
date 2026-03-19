<script setup lang="ts">
import { cn } from '@/utils/cn'
</script>

<template>
  <div :class="cn('rounded-xl border border-neutral-200 bg-white dark:border-neutral-700 dark:bg-neutral-800', $attrs.class as string)">
    <slot />
  </div>
</template>