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
  if (isTauri()) {
    return await fetchAndCachePreviewTauri(url)
  }

  return await api.post<PreviewContent>('/previews/fetch', { url })
}

async function fetchAndCachePreviewTauri(url: string): Promise<PreviewContent> {
  try {
    const cached = await getCachedPreviewByUrl(url)
    if (cached) {
      return cached
    }
  } catch (cacheError) {
    // Cache check failed, proceeding with fetch
  }

  const { invoke } = await import('@tauri-apps/api/core')
  const result = await invoke<TauriPreviewContent>('fetch_preview', { url })

  // Save to database via sidecar (async, but wait for result to ensure persistence)
  try {
    const saved = await savePreview(result.url, result.markdown_content, result.title || undefined)
    return saved
  } catch (saveError) {
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