import { ref } from 'vue'
import type { FeedParams, FeedItem } from '@/api/feed'
import { getFeed, getFormattedFeed } from '@/api/feed'

export type Format = 'rss' | 'json' | 'markdown'

export function useFeedCache() {
	const rssContent = ref('')
	const jsonContent = ref<FeedItem[] | null>(null)
	const markdownContent = ref('')
	const loading = ref(false)
	const error = ref('')

	const cache = ref({
		rss: '',
		json: null as FeedItem[] | null,
		markdown: '',
	})

	async function fetchRssContent(params?: FeedParams): Promise<void> {
		loading.value = true
		error.value = ''
		try {
			const response = await getFormattedFeed('rss', params)
			rssContent.value = response.content
			cache.value.rss = rssContent.value
		} catch {
			error.value = 'Failed to fetch RSS content'
		} finally {
			loading.value = false
		}
	}

	async function fetchJsonContent(params?: FeedParams): Promise<void> {
		loading.value = true
		error.value = ''
		try {
			jsonContent.value = await getFeed(params)
			cache.value.json = jsonContent.value
		} catch {
			error.value = 'Failed to fetch JSON content'
		} finally {
			loading.value = false
		}
	}

	async function fetchMarkdownContent(params?: FeedParams): Promise<void> {
		loading.value = true
		error.value = ''
		try {
			const response = await getFormattedFeed('markdown', params)
			markdownContent.value = response.content
			cache.value.markdown = markdownContent.value
			if (!cache.value.json) {
				cache.value.json = await getFeed(params)
			}
			jsonContent.value = cache.value.json
		} catch {
			error.value = 'Failed to fetch Markdown content'
		} finally {
			loading.value = false
		}
	}

	async function fetchContentForFormat(format: Format, params?: FeedParams): Promise<void> {
		if (format === 'rss' && cache.value.rss) {
			rssContent.value = cache.value.rss
			return
		}
		if (format === 'json' && cache.value.json) {
			jsonContent.value = cache.value.json
			return
		}
		if (format === 'markdown' && cache.value.markdown) {
			markdownContent.value = cache.value.markdown
			return
		}

		if (format === 'rss') {
			await fetchRssContent(params)
		} else if (format === 'json') {
			await fetchJsonContent(params)
		} else if (format === 'markdown') {
			await fetchMarkdownContent(params)
		}
	}

	function resetCache(): void {
		cache.value = {
			rss: '',
			json: null,
			markdown: '',
		}
		rssContent.value = ''
		jsonContent.value = null
		markdownContent.value = ''
		error.value = ''
	}

	return {
		rssContent,
		jsonContent,
		markdownContent,
		loading,
		error,
		cache,
		fetchRssContent,
		fetchJsonContent,
		fetchMarkdownContent,
		fetchContentForFormat,
		resetCache,
	}
}