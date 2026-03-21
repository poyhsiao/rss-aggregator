<script setup lang="ts">
import DOMPurify from 'dompurify'
import { computed } from 'vue'
import type { FeedItem } from '@/api/feed'

const props = defineProps<{
	content: FeedItem[] | null
}>()

function formatJson(data: FeedItem[]): string {
	return JSON.stringify(data, null, 2)
}

function highlightJson(json: string): string {
	json = json
		.replace(/&/g, '&amp;')
		.replace(/</g, '&lt;')
		.replace(/>/g, '&gt;')

	let result = ''
	let i = 0

	while (i < json.length) {
		if (json[i] === '"') {
			let stringStart = i
			i++
			while (i < json.length) {
				if (json[i] === '\\' && i + 1 < json.length) {
					i += 2
				} else if (json[i] === '"') {
					i++
					break
				} else {
					i++
				}
			}
			const stringContent = json.substring(stringStart, i)

			let j = i
			while (j < json.length && /\s/.test(json[j])) j++
			const isKey = json[j] === ':'

			if (isKey) {
				result += `<span class="json-key">${stringContent}</span>`
			} else {
				result += `<span class="json-string">${stringContent}</span>`
			}
		}
		else if (/-?\d/.test(json[i]) && (json[i] !== '-' || (i + 1 < json.length && /\d/.test(json[i + 1])))) {
			let numStart = i
			if (json[i] === '-') i++
			while (i < json.length && /[\d.eE+-]/.test(json[i])) i++
			result += `<span class="json-number">${json.substring(numStart, i)}</span>`
		}
		else if (json.substring(i, i + 4) === 'true') {
			result += '<span class="json-boolean">true</span>'
			i += 4
		}
		else if (json.substring(i, i + 5) === 'false') {
			result += '<span class="json-boolean">false</span>'
			i += 5
		}
		else if (json.substring(i, i + 4) === 'null') {
			result += '<span class="json-null">null</span>'
			i += 4
		}
		else {
			result += json[i]
			i++
		}
	}

	return result
}

function addLineNumbers(json: string): string {
	const lines = json.split('\n')
	const maxLineNum = lines.length
	const lineNumWidth = maxLineNum.toString().length

	return lines
		.map((line, index) => {
			const lineNum = (index + 1).toString().padStart(lineNumWidth, ' ')
			return `<div class="json-line"><span class="json-line-number">${lineNum}</span><span class="json-line-content">${line || ' '}</span></div>`
		})
		.join('')
}

const formattedContent = computed(() => {
	if (!props.content) return ''
	const formatted = formatJson(props.content)
	const highlighted = highlightJson(formatted)
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

:deep(.json-line-number) {
	color: #94a3b8;
	user-select: none;
}

:deep(.json-line-content) {
	color: #1e293b;
}

:deep(.json-line) {
	display: flex;
	line-height: 1.6;
}

:deep(.json-line-number) {
	flex-shrink: 0;
	width: 3rem;
	text-align: right;
	padding-right: 1rem;
	user-select: none;
}

:deep(.json-line-content) {
	flex: 1;
	user-select: text;
}

:deep(.json-key) { color: #059669; font-weight: 500; }
:deep(.json-string) { color: #dc2626; }
:deep(.json-number) { color: #7c3aed; }
:deep(.json-boolean) { color: #d97706; font-weight: 500; }
:deep(.json-null) { color: #6b7280; font-style: italic; }
</style>

<style>
.dark .code-content { color: #e2e8f0; }
.dark .code-content .json-line-number { color: #64748b; }
.dark .code-content .json-line-content { color: #e2e8f0; }
.dark .json-key { color: #34d399; }
.dark .json-string { color: #fb7185; }
.dark .json-number { color: #a78bfa; }
.dark .json-boolean { color: #fbbf24; }
.dark .json-null { color: #64748b; }
</style>