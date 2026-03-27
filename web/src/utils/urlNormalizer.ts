export function normalizeUrl(url: string): string {
  try {
    const parsed = new URL(url)

    parsed.host = parsed.host.toLowerCase()

    const params = new URLSearchParams(parsed.search)
    const sortedParams = new URLSearchParams([...params.entries()].sort())
    parsed.search = sortedParams.toString()

    parsed.hash = ''

    if (parsed.pathname !== '/' && parsed.pathname.endsWith('/')) {
      parsed.pathname = parsed.pathname.slice(0, -1)
    }

    return parsed.toString()
  } catch {
    throw new Error('Invalid URL')
  }
}

export async function computeUrlHash(url: string): Promise<string> {
  const normalized = normalizeUrl(url)
  const encoder = new TextEncoder()
  const data = encoder.encode(normalized)
  const hashBuffer = await crypto.subtle.digest('SHA-256', data)
  const hashArray = Array.from(new Uint8Array(hashBuffer))
  const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('')
  return hashHex
}