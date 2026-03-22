<script setup lang="ts">
import DOMPurify from 'dompurify'
import hljs from 'highlight.js'
import { Marked } from 'marked'
import { markedHighlight } from 'marked-highlight'
import { computed, ref, watch } from 'vue'
import { Code, Eye } from 'lucide-vue-next'
import { useI18n } from 'vue-i18n'

const props = defineProps<{
	content: string
}>()

const { t } = useI18n()
const viewMode = ref<'source' | 'preview'>('preview')
const renderedHtml = ref('')

// Configure marked with highlight.js
const marked = new Marked(
	markedHighlight({
		highlight(code: string, lang: string) {
			if (lang && hljs.getLanguage(lang)) {
				try {
					return hljs.highlight(code, { language: lang }).value
				} catch {
					// Fall back to auto-detection
				}
			}
			return hljs.highlightAuto(code).value
		},
	}),
	{
		gfm: true,
		breaks: true,
	},
)

// Watch content changes and render markdown
watch(
	() => props.content,
	async (newContent) => {
		if (newContent) {
			try {
				renderedHtml.value = await marked.parse(newContent)
			} catch {
				renderedHtml.value = ''
			}
		} else {
			renderedHtml.value = ''
		}
	},
	{ immediate: true }
)

// Clean the content - remove surrounding quotes if present
function cleanContent(content: string): string {
	if (!content) return ''
	let cleaned = content.trim()
	if ((cleaned.startsWith('"') && cleaned.endsWith('"')) ||
		(cleaned.startsWith("'") && cleaned.endsWith("'"))) {
		// Check if it's a quoted string (not actual markdown)
		const inner = cleaned.slice(1, -1).trim()
		if (!inner.startsWith('#') && !inner.startsWith('-') && !inner.startsWith('*')) {
			cleaned = inner
		}
	}
	return cleaned
}

function highlightSourceCode(source: string): string {
	// First, escape HTML entities
	let result = source
		.replace(/&/g, '&amp;')
		.replace(/</g, '&lt;')
		.replace(/>/g, '&gt;')

	// Track code blocks to avoid double processing
	const codeBlocks: { placeholder: string; html: string }[] = []

	// Extract and highlight code blocks first
	result = result.replace(/```(\w*)\n([\s\S]*?)```/g, (_match, lang, code) => {
		let highlightedCode = code
		if (lang && hljs.getLanguage(lang)) {
			try {
				highlightedCode = hljs.highlight(code.trim(), { language: lang }).value
			} catch {
				highlightedCode = hljs.highlightAuto(code.trim()).value
			}
		} else {
			highlightedCode = hljs.highlightAuto(code.trim()).value
		}
		const placeholder = `__CODE_BLOCK_${codeBlocks.length}__`
		codeBlocks.push({
			placeholder,
			html: `<div class="source-code-block"><code class="language-${lang || 'text'}">${highlightedCode}</code></div>`
		})
		return placeholder
	})

	// Highlight inline code (but not inside code blocks)
	result = result.replace(/`([^`\n]+)`/g, '<code class="source-inline-code">$1</code>')

	// Restore code blocks
	for (const block of codeBlocks) {
		result = result.replace(block.placeholder, block.html)
	}

	// Highlight headings (must be at line start)
	result = result.replace(/^(#{1,6})\s(.*)$/gm, '<span class="md-header">$1</span> <span class="md-header-text">$2</span>')

	// Highlight bold
	result = result.replace(/\*\*([^*\n]+)\*\*/g, '<span class="md-bold">**$1**</span>')
	result = result.replace(/__([^_\n]+)__/g, '<span class="md-bold">__$1__</span>')

	// Highlight italic
	result = result.replace(/\*([^*\n]+)\*/g, '<span class="md-italic">*$1*</span>')
	result = result.replace(/_([^_\n]+)_/g, '<span class="md-italic">_$1_</span>')

	// Highlight links
	result = result.replace(/\[([^\]\n]+)\]\(([^)\n]+)\)/g, '[<span class="md-link-text">$1</span>](<span class="md-link-url">$2</span>)')

	// Highlight list markers (unordered)
	result = result.replace(/^(\s*)([-*+])\s/gm, '$1<span class="md-list">$2</span> ')

	// Highlight list markers (ordered)
	result = result.replace(/^(\s*)(\d+)\.\s/gm, '$1<span class="md-list">$2.</span> ')

	// Highlight blockquotes
	result = result.replace(/^(&gt;)\s?/gm, '<span class="md-quote">$1</span> ')

	// Highlight horizontal rules
	result = result.replace(/^(---|\*\*\*|___)$/gm, '<span class="md-hr">$1</span>')

	return result
}

function addLineNumbers(content: string): string {
	const lines = content.split('\n')
	const maxLineNum = lines.length
	const lineNumWidth = Math.max(maxLineNum.toString().length, 3)

	return lines
		.map((line, index) => {
			const lineNum = (index + 1).toString().padStart(lineNumWidth, ' ')
			// Preserve empty lines for proper display
			const lineContent = line || ' '
			return `<div class="md-line"><span class="md-line-number">${lineNum}</span><span class="md-line-content">${lineContent}</span></div>`
		})
		.join('')
}

const cleanedContent = computed(() => {
	return cleanContent(props.content)
})

const highlightedSource = computed(() => {
	if (!cleanedContent.value) return ''
	const highlighted = highlightSourceCode(cleanedContent.value)
	return addLineNumbers(highlighted)
})

const sanitizedSource = computed(() => {
	if (!highlightedSource.value) return ''
	return DOMPurify.sanitize(highlightedSource.value, {
		ADD_TAGS: ['pre', 'code', 'span', 'div'],
		ADD_ATTR: ['class'],
	})
})

const sanitizedHtml = computed(() => {
	if (!renderedHtml.value) return ''
	return DOMPurify.sanitize(renderedHtml.value)
})
</script>

<template>
	<div>
		<div class="flex gap-1 p-2 border-b border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900">
			<button
				@click="viewMode = 'source'"
				:class="[
					'flex items-center gap-1.5 px-2 py-1 rounded text-xs font-medium transition-colors',
					viewMode === 'source'
						? 'bg-slate-600 dark:bg-slate-700 text-white'
						: 'text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-white'
				]"
			>
				<Code class="h-3 w-3" />
				{{ t('feed.view_source') }}
			</button>
			<button
				@click="viewMode = 'preview'"
				:class="[
					'flex items-center gap-1.5 px-2 py-1 rounded text-xs font-medium transition-colors',
					viewMode === 'preview'
						? 'bg-slate-600 dark:bg-slate-700 text-white'
						: 'text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-white'
				]"
			>
				<Eye class="h-3 w-3" />
				{{ t('feed.view_preview') }}
			</button>
		</div>

		<div v-if="viewMode === 'source'" class="p-4 max-h-[40vh] overflow-auto bg-white dark:bg-slate-950">
			<div
				class="text-xs font-mono whitespace-pre code-content"
				v-html="sanitizedSource"
			></div>
		</div>

		<div v-else class="p-4 max-h-[40vh] overflow-auto prose prose-slate dark:prose-invert max-w-none bg-white dark:bg-slate-950">
			<div v-html="sanitizedHtml" />
		</div>
	</div>
</template>

<style>
/* Light mode source code styles */
.code-content {
	color: #334155;
	font-size: 0.75rem;
	line-height: 1.6;
}

.code-content .md-line {
	display: flex;
	line-height: 1.6;
}

.code-content .md-line-number {
	flex-shrink: 0;
	width: 3rem;
	text-align: right;
	padding-right: 1rem;
	user-select: none;
	color: #94a3b8;
}

.code-content .md-line-content {
	flex: 1;
	user-select: text;
	color: #1e293b;
}

.code-content .md-header { color: #0369a1; font-weight: 600; }
.code-content .md-header-text { color: #0f172a; font-weight: 600; }
.code-content .md-bold { font-weight: 700; color: #1e293b; }
.code-content .md-italic { font-style: italic; color: #475569; }
.code-content .md-link-text { color: #0369a1; text-decoration: underline; }
.code-content .md-link-url { color: #059669; }
.code-content .md-list { color: #6366f1; font-weight: 600; }
.code-content .md-hr { color: #94a3b8; }
.code-content .md-quote { color: #6b7280; font-weight: 600; }
.code-content .source-inline-code {
	background: #f1f5f9;
	padding: 0.125rem 0.25rem;
	border-radius: 0.25rem;
	color: #dc2626;
}
.code-content .source-code-block {
	margin: 0.5rem 0;
	padding: 0.75rem;
	background: #f8fafc;
	border-radius: 0.375rem;
	overflow-x: auto;
	border: 1px solid #e2e8f0;
}
.code-content .source-code-block code {
	font-size: 0.7rem;
	line-height: 1.5;
}

/* Dark mode source code styles */
.dark .code-content { color: #e2e8f0; }
.dark .code-content .md-line-number { color: #64748b; }
.dark .code-content .md-line-content { color: #e2e8f0; }
.dark .code-content .md-header { color: #38bdf8; }
.dark .code-content .md-header-text { color: #f1f5f9; }
.dark .code-content .md-bold { color: #f1f5f9; }
.dark .code-content .md-italic { color: #cbd5e1; }
.dark .code-content .md-link-text { color: #38bdf8; }
.dark .code-content .md-link-url { color: #34d399; }
.dark .code-content .md-list { color: #a5b4fc; }
.dark .code-content .md-hr { color: #64748b; }
.dark .code-content .md-quote { color: #9ca3af; }
.dark .code-content .source-inline-code {
	background: #1e293b;
	color: #fb7185;
}
.dark .code-content .source-code-block {
	background: #0f172a;
	border-color: #334155;
}

/* Light mode prose styles */
.prose h1 { font-size: 1.5rem; font-weight: 700; color: #0f172a; margin-top: 1.5rem; margin-bottom: 1rem; }
.prose h2 { font-size: 1.25rem; font-weight: 700; color: #1e293b; margin-top: 1.5rem; margin-bottom: 0.75rem; }
.prose h3 { font-size: 1.125rem; font-weight: 600; color: #334155; margin-top: 1rem; margin-bottom: 0.5rem; }
.prose h4 { font-size: 1rem; font-weight: 600; color: #475569; margin-top: 0.75rem; margin-bottom: 0.5rem; }
.prose p { color: #475569; margin-top: 0.5rem; margin-bottom: 0.5rem; line-height: 1.7; }
.prose a { color: #0369a1; text-decoration: underline; }
.prose a:hover { color: #0284c7; }
.prose ul { list-style-type: disc; padding-left: 1.5rem; margin-top: 0.5rem; margin-bottom: 0.5rem; }
.prose ol { list-style-type: decimal; padding-left: 1.5rem; margin-top: 0.5rem; margin-bottom: 0.5rem; }
.prose li { color: #475569; margin-top: 0.25rem; margin-bottom: 0.25rem; }
.prose hr { border-color: #e2e8f0; margin-top: 1rem; margin-bottom: 1rem; }
.prose strong { font-weight: 600; color: #1e293b; }
.prose em { font-style: italic; }
.prose blockquote { border-left: 4px solid #e2e8f0; padding-left: 1rem; margin: 1rem 0; color: #64748b; }
.prose code:not(pre code) {
	background: #f1f5f9;
	padding: 0.125rem 0.375rem;
	border-radius: 0.25rem;
	font-size: 0.875em;
	color: #dc2626;
}
.prose pre {
	background: #f8fafc;
	padding: 0.75rem 1rem;
	border-radius: 0.5rem;
	overflow-x: auto;
	margin: 0.75rem 0;
	border: 1px solid #e2e8f0;
}
.prose pre code {
	background: transparent;
	padding: 0;
	color: inherit;
	font-size: 0.8125rem;
}
.prose table { width: 100%; border-collapse: collapse; margin: 1rem 0; }
.prose th { background: #f1f5f9; padding: 0.5rem; text-align: left; border: 1px solid #e2e8f0; }
.prose td { padding: 0.5rem; border: 1px solid #e2e8f0; }
.prose img { max-width: 100%; height: auto; border-radius: 0.5rem; }

/* Dark mode prose styles */
.dark .prose h1 { color: #f1f5f9; }
.dark .prose h2 { color: #f1f5f9; }
.dark .prose h3 { color: #f1f5f9; }
.dark .prose h4 { color: #e2e8f0; }
.dark .prose p { color: #cbd5e1; }
.dark .prose a { color: #38bdf8; }
.dark .prose a:hover { color: #7dd3fc; }
.dark .prose li { color: #cbd5e1; }
.dark .prose hr { border-color: #334155; }
.dark .prose strong { color: #f1f5f9; }
.dark .prose blockquote { border-color: #475569; color: #94a3b8; }
.dark .prose code:not(pre code) {
	background: #334155;
	color: #fb7185;
}
.dark .prose pre {
	background: #0f172a;
	border-color: #334155;
}
.dark .prose th { background: #1e293b; border-color: #334155; color: #e2e8f0; }
.dark .prose td { border-color: #334155; color: #cbd5e1; }

/* Highlight.js theme overrides */
.code-content .hljs { background: transparent; }
</style>