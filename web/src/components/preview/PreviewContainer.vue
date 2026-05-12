<script setup lang="ts">
import DOMPurify from 'dompurify'
import { computed } from 'vue'

const props = defineProps<{
  content: string
  allowedTags?: string[]
}>()

const sanitizedContent = computed(() => {
  if (!props.content) return ''
  return DOMPurify.sanitize(props.content, {
    ADD_TAGS: props.allowedTags ?? ['span'],
    ADD_ATTR: ['class'],
  })
})
</script>

<template>
  <div
    class="text-xs font-mono whitespace-pre code-content"
    v-html="sanitizedContent"
  />
</template>

<style>
@import '@/styles/preview-shared.css';
</style>