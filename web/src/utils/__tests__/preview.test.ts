import { describe, it, expect } from 'vitest'
import { cleanContent, addLineNumbers } from '../preview'

describe('cleanContent', () => {
  it('removes surrounding double quotes when content is not XML', () => {
    expect(cleanContent('"hello world"')).toBe('hello world')
  })

  it('removes surrounding single quotes when content is not XML', () => {
    expect(cleanContent("'hello world'")).toBe('hello world')
  })

  it('preserves XML content starting with <', () => {
    expect(cleanContent('"<xml>content</xml>"')).toBe('"<xml>content</xml>"')
  })

  it('returns empty string for empty input', () => {
    expect(cleanContent('')).toBe('')
  })

  it('trims whitespace before checking quotes', () => {
    expect(cleanContent('  "hello"  ')).toBe('hello')
  })
})

describe('addLineNumbers', () => {
  it('wraps each line in code-line div with line number span', () => {
    const result = addLineNumbers('line1\nline2')
    expect(result).toContain('<div class="code-line">')
    expect(result).toContain('<span class="code-line-number">1</span>')
    expect(result).toContain('<span class="code-line-content">line1</span>')
  })

  it('calculates correct line number width for multi-digit counts', () => {
    const result = addLineNumbers('line1\nline2\nline3\nline4\nline5\nline6\nline7\nline8\nline9\nline10')
    expect(result).toContain('10') // two digits
  })

  it('handles single line content', () => {
    const result = addLineNumbers('hello')
    expect(result).toContain('<span class="code-line-number">1</span>')
    expect(result).toContain('<span class="code-line-content">hello</span>')
  })

  it('handles empty lines', () => {
    const result = addLineNumbers('line1\n\nline3')
    // Empty lines get a space placeholder (line || ' ')
    expect(result).toContain('<span class="code-line-content"> </span>')
  })
})
