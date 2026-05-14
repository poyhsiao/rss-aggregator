<script setup lang="ts">
import { computed } from 'vue'
import { cleanContent, addLineNumbers } from '@/utils/preview'
import { highlightXml } from '@/utils/preview.highlight'
import PreviewContainer from './PreviewContainer.vue'

const props = defineProps<{ content: string }>()

function formatXml(xml: string): string {
  let formatted = ''
  let indent = 0
  const indentSize = 2

  xml = xml.replace(/>\s+</g, '><').trim()
  const tokens = xml.split(/(<[^>]+>)/g).filter((t) => t.trim())

  for (const token of tokens) {
    if (token.startsWith('</')) {
      indent = Math.max(0, indent - 1)
      formatted += ' '.repeat(indent * indentSize) + token + '\n'
    } else if (token.startsWith('<')) {
      formatted += ' '.repeat(indent * indentSize) + token + '\n'
      if (!token.startsWith('<?') && !token.startsWith('<!') && !token.endsWith('/>')) {
        indent++
      }
    } else if (token.trim()) {
      formatted += ' '.repeat(indent * indentSize) + token + '\n'
    }
  }

  return formatted.trim()
}

const rendered = computed(() => {
  if (!props.content) return ''
  const cleaned = cleanContent(props.content)
  const formatted = formatXml(cleaned)
  const highlighted = highlightXml(formatted)
  return addLineNumbers(highlighted)
})
</script>

<template>
  <PreviewContainer :content="rendered" />
</template>