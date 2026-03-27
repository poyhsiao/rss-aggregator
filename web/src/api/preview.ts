import api from '.'
import { isTauri } from '@/utils/environment'

export interface PreviewContent {
  id: number
  url: string
  url_hash: string
  markdown_content: string
  title: string | null
  created_at: string
  updated_at: string
}

export interface TauriPreviewContent {
  url: string
  url_hash: string
  markdown_content: string
  title: string | null
}

export async function clearAllPreviews(): Promise<void> {
  await api.delete('/previews')
}

export async function getCachedPreview(urlHash: string): Promise<PreviewContent | null> {
  try {
    return await api.get<PreviewContent>(`/previews/${urlHash}`)
  } catch (error) {
    if (error instanceof Error && (error.message.includes('404') || error.message.includes('500'))) {
      return null
    }
    throw error
  }
}

export async function getCachedPreviewByUrl(url: string): Promise<PreviewContent | null> {
  try {
    return await api.get<PreviewContent>(`/previews?url=${encodeURIComponent(url)}`)
  } catch (error) {
    if (error instanceof Error && (error.message.includes('404') || error.message.includes('500'))) {
      return null
    }
    throw error
  }
}

export async function savePreview(
  url: string,
  markdownContent: string,
  title?: string
): Promise<PreviewContent> {
  return await api.post<PreviewContent>('/previews', {
    url,
    markdown_content: markdownContent,
    title: title || null,
  })
}

export async function fetchAndCachePreview(url: string): Promise<PreviewContent> {
  console.log('[PREVIEW] fetchAndCachePreview called for:', url)

  if (isTauri()) {
    console.log('[PREVIEW] Tauri environment detected')
    return await fetchAndCachePreviewTauri(url)
  }

  console.log('[PREVIEW] Web environment detected')
  return await api.post<PreviewContent>('/previews/fetch', { url })
}

async function fetchAndCachePreviewTauri(url: string): Promise<PreviewContent> {
  console.log('[PREVIEW] Checking cache first via sidecar API')
  
  try {
    const cached = await getCachedPreviewByUrl(url)
    if (cached) {
      console.log('[PREVIEW] Cache hit:', cached.url_hash)
      return cached
    }
  } catch (cacheError) {
    console.warn('[PREVIEW] Cache check failed, proceeding with fetch:', cacheError)
  }

  console.log('[PREVIEW] Cache miss, using native Tauri invoke')
  
  const { invoke } = await import('@tauri-apps/api/core')
  const result = await invoke<TauriPreviewContent>('fetch_preview', { url })
  console.log('[PREVIEW] Native fetch success, content length:', result?.markdown_content?.length)

  // Save to database via sidecar (async, but wait for result to ensure persistence)
  try {
    const saved = await savePreview(result.url, result.markdown_content, result.title || undefined)
    console.log('[PREVIEW] Saved to database:', saved.url_hash)
    return saved
  } catch (saveError) {
    console.warn('[PREVIEW] Failed to save to database, returning unsaved content:', saveError)
    return {
      id: 0,
      url: result.url,
      url_hash: result.url_hash,
      markdown_content: result.markdown_content,
      title: result.title,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    }
  }
}