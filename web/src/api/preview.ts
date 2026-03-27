import api from '.'

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

/**
 * Fetch and cache preview content.
 * In Tauri environment, uses native command to bypass sidecar network limitations.
 * In web environment, uses backend API which calls markdown.new.
 */
export async function fetchAndCachePreview(url: string): Promise<PreviewContent> {
  try {
    const { invoke } = await import('@tauri-apps/api/core')
    console.log('[PREVIEW] Attempting Tauri invoke for:', url)
    
    const result = await invoke<TauriPreviewContent>('fetch_preview', { url })
    console.log('[PREVIEW] Tauri invoke success:', result?.url_hash)
    
    return {
      id: 0,
      url: result.url,
      url_hash: result.url_hash,
      markdown_content: result.markdown_content,
      title: result.title,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    }
  } catch (tauriError) {
    console.log('[PREVIEW] Tauri invoke not available, using HTTP API:', tauriError)
    return await api.post<PreviewContent>('/previews/fetch', { url })
  }
}