<script setup lang="ts">
import { computed } from 'vue'
import { addLineNumbers } from '@/utils/preview'
import { highlightJson } from '@/utils/preview.highlight'
import PreviewContainer from './PreviewContainer.vue'

const props = defineProps<{ content: unknown[] | null }>()

const rendered = computed(() => {
  if (!props.content) return ''
  const formatted = JSON.stringify(props.content, null, 2)
  const highlighted = highlightJson(formatted)
  return addLineNumbers(highlighted)
})
</script>

<template>
  <PreviewContainer :content="rendered" />
</template>
