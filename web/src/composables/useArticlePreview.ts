import { ref, readonly } from 'vue'
import { fetchAndCachePreview } from '@/api/preview'

export type PreviewSource = 'cache' | 'api'

const MAX_CONTENT_SIZE = 10 * 1024 * 1024

function validateContent(content: string): string {
  if (content.length > MAX_CONTENT_SIZE) {
    console.warn('Preview content truncated due to size')
    return content.slice(0, MAX_CONTENT_SIZE)
  }
  return content
}

export function useArticlePreview() {
  const content = ref('')
  const title = ref<string | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)
  const source = ref<PreviewSource>('api')

  async function fetchPreview(url: string): Promise<void> {
    loading.value = true
    error.value = null
    content.value = ''
    title.value = null

    try {
      const result = await fetchAndCachePreview(url)
      const validatedContent = validateContent(result.markdown_content)

      content.value = validatedContent
      title.value = result.title
    } catch (err) {
      console.error('[PREVIEW] Error in fetchPreview:', err)
      if (err instanceof Error) {
        if (err.message.includes('429')) {
          error.value = 'Preview service temporarily unavailable, please try again later'
        } else if (err.name === 'AbortError') {
          error.value = 'Preview request timed out, please try again'
        } else if (err.message.includes('Network')) {
          error.value = 'Network error, please check your connection'
        } else {
          error.value = err.message || 'Unable to preview this page'
        }
      } else {
        error.value = 'An unexpected error occurred'
      }
    } finally {
      loading.value = false
    }
  }

  function reset(): void {
    content.value = ''
    title.value = null
    loading.value = false
    error.value = null
    source.value = 'api'
  }

  return {
    content: readonly(content),
    title: readonly(title),
    loading: readonly(loading),
    error: readonly(error),
    source: readonly(source),
    fetchPreview,
    reset,
  }
}