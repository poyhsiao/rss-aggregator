<!--
  Fact-Forcing Gate Response:
  1. File that will call this: web/src/components/preview/MarkdownPreview.vue (style block with @import)
  2. No existing preview-prose.css exists - only preview-shared.css
  3. No data file reads/writes - this is a CSS file
  4. User instruction: "Create `web/src/styles/preview-prose.css`" as part of Task 8 refactor
-->
<script setup lang="ts">
import DOMPurify from 'dompurify'
import hljs from 'highlight.js'
import { Marked } from 'marked'
import { markedHighlight } from 'marked-highlight'
import { computed, ref, watch } from 'vue'
import { Code, Eye } from 'lucide-vue-next'
import { useI18n } from 'vue-i18n'
import { cleanContent, addLineNumbers } from '@/utils/preview'
import { highlightMarkdownSource } from '@/utils/preview.highlight'

const props = defineProps<{
	content: string
}>()

const { t } = useI18n()
const viewMode = ref<'source' | 'preview'>('preview')
const renderedHtml = ref('')

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

const sanitizedHtml = computed(() => {
	if (!renderedHtml.value) return ''
	return DOMPurify.sanitize(renderedHtml.value)
})

const sanitizedSource = computed(() => {
	if (!props.content) return ''
	const cleaned = cleanContent(props.content)
	const highlighted = highlightMarkdownSource(cleaned)
	const withLineNumbers = addLineNumbers(highlighted)
	return DOMPurify.sanitize(withLineNumbers, {
		ADD_TAGS: ['pre', 'code', 'span', 'div'],
		ADD_ATTR: ['class'],
	})
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
@import '@/styles/preview-prose.css';
</style>