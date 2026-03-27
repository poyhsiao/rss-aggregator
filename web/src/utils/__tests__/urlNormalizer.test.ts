import { describe, it, expect } from 'vitest'
import { normalizeUrl, computeUrlHash } from '../urlNormalizer'

describe('normalizeUrl', () => {
  it('should lowercase domain', () => {
    expect(normalizeUrl('https://Example.COM/article')).toBe('https://example.com/article')
  })

  it('should sort query parameters alphabetically', () => {
    expect(normalizeUrl('https://example.com?b=2&a=1')).toBe('https://example.com/?a=1&b=2')
  })

  it('should remove fragment', () => {
    expect(normalizeUrl('https://example.com#section')).toBe('https://example.com/')
  })

  it('should remove trailing slash except root', () => {
    expect(normalizeUrl('https://example.com/path/')).toBe('https://example.com/path')
    expect(normalizeUrl('https://example.com/')).toBe('https://example.com/')
  })

  it('should throw error for invalid URL', () => {
    expect(() => normalizeUrl('not-a-url')).toThrow('Invalid URL')
  })

  it('should handle complex URLs', () => {
    const input = 'https://Example.com/Article?z=3&a=1&b=2#section'
    const expected = 'https://example.com/Article?a=1&b=2&z=3'
    expect(normalizeUrl(input)).toBe(expected)
  })
})

describe('computeUrlHash', () => {
  it('should return 64 character SHA-256 hash', async () => {
    const hash = await computeUrlHash('https://example.com/article')
    expect(hash).toHaveLength(64)
    expect(/^[a-f0-9]+$/.test(hash)).toBe(true)
  })

  it('should return consistent hash for same URL', async () => {
    const url = 'https://example.com/article'
    const hash1 = await computeUrlHash(url)
    const hash2 = await computeUrlHash(url)
    expect(hash1).toBe(hash2)
  })

  it('should return same hash for normalized-equivalent URLs', async () => {
    const hash1 = await computeUrlHash('https://Example.COM/path?b=2&a=1')
    const hash2 = await computeUrlHash('https://example.com/path?a=1&b=2')
    expect(hash1).toBe(hash2)
  })
})