<script setup lang="ts">
/**
 * Tooltip Example
 * Demonstrates various tooltip configurations
 */
import Tooltip from '@/components/ui/Tooltip.vue'
import Button from '@/components/ui/Button.vue'
</script>

<template>
  <div class="space-y-8 p-8">
    <h1 class="text-2xl font-bold text-neutral-900 dark:text-neutral-100">
      Tooltip Examples
    </h1>

    <div class="space-y-4">
      <h2 class="text-lg font-semibold text-neutral-700 dark:text-neutral-300">
        Basic Tooltip
      </h2>
      <Tooltip content="This is a basic tooltip">
        <Button>Hover me</Button>
      </Tooltip>
    </div>

    <div class="space-y-4">
      <h2 class="text-lg font-semibold text-neutral-700 dark:text-neutral-300">
        Different Positions
      </h2>
      <div class="flex gap-4">
        <Tooltip content="Top tooltip" side="top">
          <Button>Top</Button>
        </Tooltip>
        <Tooltip content="Bottom tooltip" side="bottom">
          <Button>Bottom</Button>
        </Tooltip>
        <Tooltip content="Left tooltip" side="left">
          <Button>Left</Button>
        </Tooltip>
        <Tooltip content="Right tooltip" side="right">
          <Button>Right</Button>
        </Tooltip>
      </div>
    </div>

    <div class="space-y-4">
      <h2 class="text-lg font-semibold text-neutral-700 dark:text-neutral-300">
        Custom Delay
      </h2>
      <Tooltip content="Delayed tooltip (500ms)" :delay-duration="500">
        <Button>Hover me (500ms delay)</Button>
      </Tooltip>
    </div>

    <div class="space-y-4">
      <h2 class="text-lg font-semibold text-neutral-700 dark:text-neutral-300">
        With Custom Alignment
      </h2>
      <div class="flex gap-4">
        <Tooltip content="Start aligned" side="bottom" align="start">
          <Button>Start</Button>
        </Tooltip>
        <Tooltip content="Center aligned" side="bottom" align="center">
          <Button>Center</Button>
        </Tooltip>
        <Tooltip content="End aligned" side="bottom" align="end">
          <Button>End</Button>
        </Tooltip>
      </div>
    </div>

    <div class="space-y-4">
      <h2 class="text-lg font-semibold text-neutral-700 dark:text-neutral-300">
        Long Content
      </h2>
      <Tooltip content="This is a longer tooltip that demonstrates how the component handles multi-line content and text wrapping gracefully.">
        <Button>Hover for long content</Button>
      </Tooltip>
    </div>
  </div>
</template>
