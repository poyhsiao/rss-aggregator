<script setup lang="ts">
import DOMPurify from 'dompurify'
import hljs from 'highlight.js'
import { computed } from 'vue'

const props = defineProps<{
 	content: unknown[] | null
}>()

function formatJson(data: unknown[]): string {
	return JSON.stringify(data, null, 2)
}

function highlightJson(json: string): string {
	// Use highlight.js for JSON highlighting
	try {
		return hljs.highlight(json, { language: 'json' }).value
	} catch {
		// Fallback to manual highlighting
		return manualHighlightJson(json)
	}
}

function manualHighlightJson(json: string): string {
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
			return `<div class="code-line"><span class="code-line-number">${lineNum}</span><span class="code-line-content">${line || ' '}</span></div>`
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
	return DOMPurify.sanitize(formattedContent.value, {
		ADD_TAGS: ['span'],
		ADD_ATTR: ['class'],
	})
})
</script>

<template>
	<div
		class="text-xs font-mono whitespace-pre code-content"
		v-html="sanitizedContent"
	></div>
</template>

<style>
/* Light mode styles */
.code-content {
	color: #334155;
	font-size: 0.75rem;
	line-height: 1.6;
}

.code-content .code-line {
	display: flex;
	line-height: 1.6;
}

.code-content .code-line-number {
	flex-shrink: 0;
	width: 3rem;
	text-align: right;
	padding-right: 1rem;
	user-select: none;
	color: #94a3b8;
}

.code-content .code-line-content {
	flex: 1;
	user-select: text;
	color: #1e293b;
}

/* JSON specific styles */
.code-content .json-key { color: #059669; font-weight: 500; }
.code-content .json-string { color: #dc2626; }
.code-content .json-number { color: #7c3aed; }
.code-content .json-boolean { color: #d97706; font-weight: 500; }
.code-content .json-null { color: #6b7280; font-style: italic; }

/* Highlight.js overrides */
.code-content .hljs-attr { color: #059669; font-weight: 500; }
.code-content .hljs-string { color: #dc2626; }
.code-content .hljs-number { color: #7c3aed; }
.code-content .hljs-literal { color: #d97706; font-weight: 500; }
.code-content .hljs-punctuation { color: #64748b; }

/* Dark mode styles */
.dark .code-content { color: #e2e8f0; }
.dark .code-content .code-line-number { color: #64748b; }
.dark .code-content .code-line-content { color: #e2e8f0; }
.dark .code-content .json-key { color: #34d399; }
.dark .code-content .json-string { color: #fb7185; }
.dark .code-content .json-number { color: #a78bfa; }
.dark .code-content .json-boolean { color: #fbbf24; }
.dark .code-content .json-null { color: #64748b; }

/* Highlight.js dark mode overrides */
.dark .code-content .hljs-attr { color: #34d399; }
.dark .code-content .hljs-string { color: #fb7185; }
.dark .code-content .hljs-number { color: #a78bfa; }
.dark .code-content .hljs-literal { color: #fbbf24; }
.dark .code-content .hljs-punctuation { color: #94a3b8; }
</style>