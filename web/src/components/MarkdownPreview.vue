<script setup lang="ts">
import DOMPurify from 'dompurify'
import { computed, ref } from 'vue'
import { Code, Eye } from 'lucide-vue-next'
import { useI18n } from 'vue-i18n'

const props = defineProps<{
	content: string
}>()

const { t } = useI18n()
const viewMode = ref<'source' | 'preview'>('preview')

function highlightMarkdown(markdown: string): string {
	markdown = markdown
		.replace(/&/g, '&amp;')
		.replace(/</g, '&lt;')
		.replace(/>/g, '&gt;')

	markdown = markdown.replace(/^(#{1,3})\s(.+)$/gm, (_match, hashes, text) => {
		return `<span class="md-header">${hashes}</span> <span class="md-header-text">${text}</span>`
	})

	markdown = markdown.replace(/\*\*([^*]+)\*\*/g, (_match, text) => {
		return `<span class="md-bold">**${text}**</span>`
	})

	markdown = markdown.replace(/\[([^\]]+)\]\(([^)]+)\)/g, (_match, text, url) => {
		return `[<span class="md-link-text">${text}</span>](<span class="md-link-url">${url}</span>)`
	})

	markdown = markdown.replace(/^(\s*)-\s(.+)$/gm, (_match, indent, text) => {
		return `${indent}<span class="md-list">-</span> ${text}`
	})

	markdown = markdown.replace(/^---$/gm, '<span class="md-hr">---</span>')

	return markdown
}

function addLineNumbers(markdown: string): string {
	const lines = markdown.split('\n')
	const maxLineNum = lines.length
	const lineNumWidth = maxLineNum.toString().length

	return lines
		.map((line, index) => {
			const lineNum = (index + 1).toString().padStart(lineNumWidth, ' ')
			return `<div class="md-line"><span class="md-line-number">${lineNum}</span><span class="md-line-content">${line || ' '}</span></div>`
		})
		.join('')
}

function renderMarkdown(markdown: string): string {
	let html = markdown

	html = html.replace(/^### (.+)$/gm, '<h3 class="text-lg font-semibold text-slate-100 mt-4 mb-2">$1</h3>')
	html = html.replace(/^## (.+)$/gm, '<h2 class="text-xl font-bold text-slate-100 mt-6 mb-3">$1</h2>')
	html = html.replace(/^# (.+)$/gm, '<h1 class="text-2xl font-bold text-slate-100 mt-6 mb-4">$1</h1>')

	html = html.replace(/\*\*([^*]+)\*\*/g, '<strong class="font-semibold">$1</strong>')

	html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener" class="text-sky-400 hover:text-sky-300 underline">$1</a>')

	html = html.replace(/^- (.+)$/gm, '<li class="ml-4 text-slate-300">$1</li>')

	html = html.replace(/^---$/gm, '<hr class="border-slate-700 my-4" />')

	html = html.split('\n').map(line => {
		if (line.trim() && !line.match(/^<(h[1-6]|li|hr|ul|ol)/)) {
			return `<p class="text-slate-300 my-2">${line}</p>`
		}
		return line
	}).join('\n')

	return html
}

const highlightedSource = computed(() => {
	if (!props.content) return ''
	const highlighted = highlightMarkdown(props.content)
	return addLineNumbers(highlighted)
})

const sanitizedSource = computed(() => {
	if (!highlightedSource.value) return ''
	return DOMPurify.sanitize(highlightedSource.value)
})

const renderedHtml = computed(() => {
	if (!props.content) return ''
	return renderMarkdown(props.content)
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
						? 'bg-slate-400 dark:bg-slate-700 text-white'
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
						? 'bg-slate-400 dark:bg-slate-700 text-white'
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

		<div v-else class="p-4 max-h-[40vh] overflow-auto prose dark:prose-invert bg-white dark:bg-slate-950">
			<div v-html="sanitizedHtml" />
		</div>
	</div>
</template>

<style scoped>
:deep(.code-content) {
	color: #334155;
}

:deep(.md-line-number) {
	color: #94a3b8;
	user-select: none;
}

:deep(.md-line-content) {
	color: #1e293b;
}

:deep(.md-line) {
	display: flex;
	line-height: 1.6;
}

:deep(.md-line-number) {
	flex-shrink: 0;
	width: 3rem;
	text-align: right;
	padding-right: 1rem;
	user-select: none;
}

:deep(.md-line-content) {
	flex: 1;
	user-select: text;
}

:deep(.md-header) { color: #0369a1; font-weight: 600; }
:deep(.md-header-text) { color: #0f172a; font-weight: 600; }
:deep(.md-bold) { font-weight: 700; color: #1e293b; }
:deep(.md-link-text) { color: #0369a1; text-decoration: underline; }
:deep(.md-link-url) { color: #059669; }
:deep(.md-list) { color: #6366f1; }
:deep(.md-hr) { color: #94a3b8; }

:deep(.prose h1) { font-size: 1.5rem; font-weight: 700; color: #0f172a; margin-top: 1.5rem; margin-bottom: 1rem; }
:deep(.prose h2) { font-size: 1.25rem; font-weight: 700; color: #1e293b; margin-top: 1.5rem; margin-bottom: 0.75rem; }
:deep(.prose h3) { font-size: 1.125rem; font-weight: 600; color: #334155; margin-top: 1rem; margin-bottom: 0.5rem; }
:deep(.prose p) { color: #475569; margin-top: 0.5rem; margin-bottom: 0.5rem; line-height: 1.6; }
:deep(.prose a) { color: #0369a1; text-decoration: underline; }
:deep(.prose a:hover) { color: #0284c7; }
:deep(.prose ul) { list-style-type: disc; padding-left: 1.5rem; margin-top: 0.5rem; margin-bottom: 0.5rem; }
:deep(.prose li) { color: #475569; margin-top: 0.25rem; margin-bottom: 0.25rem; }
:deep(.prose hr) { border-color: #e2e8f0; margin-top: 1rem; margin-bottom: 1rem; }
:deep(.prose strong) { font-weight: 600; color: #1e293b; }
</style>

<style>
.dark .code-content { color: #e2e8f0; }
.dark .code-content .md-line-number { color: #64748b; }
.dark .code-content .md-line-content { color: #e2e8f0; }
.dark .md-header { color: #38bdf8; }
.dark .md-header-text { color: #f1f5f9; }
.dark .md-bold { color: #f1f5f9; }
.dark .md-link-text { color: #38bdf8; }
.dark .md-link-url { color: #34d399; }
.dark .md-list { color: #94a3b8; }
.dark .md-hr { color: #64748b; }
.dark .prose h1 { color: #f1f5f9; }
.dark .prose h2 { color: #f1f5f9; }
.dark .prose h3 { color: #f1f5f9; }
.dark .prose p { color: #cbd5e1; }
.dark .prose a { color: #38bdf8; }
.dark .prose a:hover { color: #7dd3fc; }
.dark .prose li { color: #cbd5e1; }
.dark .prose hr { border-color: #334155; }
.dark .prose strong { color: #f1f5f9; }
</style>