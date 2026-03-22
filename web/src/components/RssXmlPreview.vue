<script setup lang="ts">
import DOMPurify from 'dompurify'
import { computed } from 'vue'

const props = defineProps<{
	content: string
}>()

// Clean the content - remove surrounding quotes if present (from JSON stringification)
function cleanContent(content: string): string {
	if (!content) return ''
	// Remove leading/trailing quotes if the entire content is quoted
	let cleaned = content.trim()
	if ((cleaned.startsWith('"') && cleaned.endsWith('"')) ||
		(cleaned.startsWith("'") && cleaned.endsWith("'"))) {
		// Check if it's a quoted string (not actual XML starting with <)
		if (!cleaned.slice(1, -1).trim().startsWith('<')) {
			cleaned = cleaned.slice(1, -1)
		}
	}
	return cleaned
}

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

	// Highlight XML tags
	xml = xml.replace(/(&lt;\/?)([\w:.-]+)(&gt;)/g, (_match, open, tag, close) => {
		return `<span class="xml-tag-bracket">${open}</span><span class="xml-tag-name">${tag}</span><span class="xml-tag-bracket">${close}</span>`
	})

	// Highlight attributes
	xml = xml.replace(/(\s)([\w:.-]+)(=)(&quot;[^&]*&quot;)/g, (_match, space, attr, eq, value) => {
		return `${space}<span class="xml-attr-name">${attr}</span>${eq}<span class="xml-attr-value">${value}</span>`
	})

	// Highlight CDATA sections
	xml = xml.replace(/(&lt;\!\[CDATA\[)([\s\S]*?)(\]\]&gt;)/g, (_match, open, content, close) => {
		return `<span class="xml-cdata">${open}${content}${close}</span>`
	})

	// Highlight comments
	xml = xml.replace(/(&lt;!--)([\s\S]*?)(--&gt;)/g, (_match, open, content, close) => {
		return `<span class="xml-comment">${open}${content}${close}</span>`
	})

	// Highlight processing instructions
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
			return `<div class="code-line"><span class="code-line-number">${lineNum}</span><span class="code-line-content">${line || ' '}</span></div>`
		})
		.join('')
}

const formattedContent = computed(() => {
	if (!props.content) return ''
	const cleaned = cleanContent(props.content)
	const formatted = formatXml(cleaned)
	const highlighted = highlightXml(formatted)
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

/* XML specific styles */
.code-content .xml-tag-bracket { color: #6366f1; }
.code-content .xml-tag-name { color: #0369a1; font-weight: 600; }
.code-content .xml-attr-name { color: #059669; }
.code-content .xml-attr-value { color: #dc2626; }
.code-content .xml-cdata { color: #7c3aed; font-style: italic; }
.code-content .xml-comment { color: #6b7280; font-style: italic; }
.code-content .xml-pi { color: #d97706; }

/* Dark mode styles */
.dark .code-content { color: #e2e8f0; }
.dark .code-content .code-line-number { color: #64748b; }
.dark .code-content .code-line-content { color: #e2e8f0; }
.dark .code-content .xml-tag-bracket { color: #818cf8; }
.dark .code-content .xml-tag-name { color: #38bdf8; }
.dark .code-content .xml-attr-name { color: #34d399; }
.dark .code-content .xml-attr-value { color: #fb7185; }
.dark .code-content .xml-cdata { color: #a78bfa; }
.dark .code-content .xml-comment { color: #64748b; }
.dark .code-content .xml-pi { color: #fbbf24; }
</style>