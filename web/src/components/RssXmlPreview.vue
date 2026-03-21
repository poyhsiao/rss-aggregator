<script setup lang="ts">
import DOMPurify from 'dompurify'
import { computed } from 'vue'

const props = defineProps<{
	content: string
}>()

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

function highlightXml(xml: string): string {
	xml = xml
		.replace(/&/g, '&amp;')
		.replace(/</g, '&lt;')
		.replace(/>/g, '&gt;')

	xml = xml.replace(/(&lt;\/?)([\w:.-]+)(&gt;)/g, (_match, open, tag, close) => {
		return `<span class="xml-tag-bracket">${open}</span><span class="xml-tag-name">${tag}</span><span class="xml-tag-bracket">${close}</span>`
	})

	xml = xml.replace(/(\s)([\w:.-]+)(=)(&quot;[^&]*&quot;)/g, (_match, space, attr, eq, value) => {
		return `${space}<span class="xml-attr-name">${attr}</span>${eq}<span class="xml-attr-value">${value}</span>`
	})

	xml = xml.replace(/(&lt;\!\[CDATA\[)([\s\S]*?)(\]\]&gt;)/g, (_match, open, content, close) => {
		return `<span class="xml-cdata">${open}${content}${close}</span>`
	})

	xml = xml.replace(/(&lt;!--)([\s\S]*?)(--&gt;)/g, (_match, open, content, close) => {
		return `<span class="xml-comment">${open}${content}${close}</span>`
	})

	xml = xml.replace(/(&lt;\?)([\w:.-]+)(.*?)(\?&gt;)/g, (_match, open, target, content, close) => {
		return `<span class="xml-pi">${open}${target}${content}${close}</span>`
	})

	return xml
}

function addLineNumbers(xml: string): string {
	const lines = xml.split('\n')
	const maxLineNum = lines.length
	const lineNumWidth = maxLineNum.toString().length

	return lines
		.map((line, index) => {
			const lineNum = (index + 1).toString().padStart(lineNumWidth, ' ')
			return `<div class="xml-line"><span class="xml-line-number">${lineNum}</span><span class="xml-line-content">${line || ' '}</span></div>`
		})
		.join('')
}

const formattedContent = computed(() => {
	if (!props.content) return ''
	const formatted = formatXml(props.content)
	const highlighted = highlightXml(formatted)
	return addLineNumbers(highlighted)
})

const sanitizedContent = computed(() => {
	if (!formattedContent.value) return ''
	return DOMPurify.sanitize(formattedContent.value)
})
</script>

<template>
	<div
		class="text-xs font-mono whitespace-pre code-content"
		v-html="sanitizedContent"
	></div>
</template>

<style scoped>
:deep(.code-content) {
	color: #334155;
}

:deep(.xml-line-number) {
	color: #94a3b8;
	user-select: none;
}

:deep(.xml-line-content) {
	color: #1e293b;
}

:deep(.xml-line) {
	display: flex;
	line-height: 1.6;
}

:deep(.xml-line-number) {
	flex-shrink: 0;
	width: 3rem;
	text-align: right;
	padding-right: 1rem;
	user-select: none;
}

:deep(.xml-line-content) {
	flex: 1;
	user-select: text;
}

:deep(.xml-tag-bracket) { color: #6366f1; }
:deep(.xml-tag-name) { color: #0369a1; font-weight: 600; }
:deep(.xml-attr-name) { color: #059669; }
:deep(.xml-attr-value) { color: #dc2626; }
:deep(.xml-cdata) { color: #7c3aed; font-style: italic; }
:deep(.xml-comment) { color: #6b7280; font-style: italic; }
:deep(.xml-pi) { color: #d97706; }
</style>

<style>
.dark .code-content { color: #e2e8f0; }
.dark .code-content .xml-line-number { color: #64748b; }
.dark .code-content .xml-line-content { color: #e2e8f0; }
.dark .xml-tag-bracket { color: #818cf8; }
.dark .xml-tag-name { color: #38bdf8; }
.dark .xml-attr-name { color: #34d399; }
.dark .xml-attr-value { color: #fb7185; }
.dark .xml-cdata { color: #a78bfa; }
.dark .xml-comment { color: #64748b; }
.dark .xml-pi { color: #fbbf24; }
</style>