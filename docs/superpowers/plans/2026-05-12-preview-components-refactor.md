# Preview Components 重構 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 重構 `RssXmlPreview`、`JsonPreview`、`MarkdownPreview` 三個 Vue 元件，消除重複的 `cleanContent()`、`addLineNumbers()`、CSS 邏輯，並提取為共用的 pure functions。

**Architecture:** 提取 pure utility functions (`utils/preview.ts` + `utils/preview.highlight.ts`) 與集中化 CSS (`styles/preview-shared.css`)，新 Vue 元件放在 `components/preview/`，確認行為一致後刪除舊檔。

**Tech Stack:** Vitest (unit test), Playwright (E2E), DOMPurify, highlight.js, marked + marked-highlight

---

## Phase 0: 準備

- [ ] Create new branch from `main`
- [ ] Verify existing tests pass: `cd web && pnpm test:run`

---

## Task 1: Phase 1 — Extract `cleanContent` and `addLineNumbers` Utils

**Files:**
- Create: `web/src/utils/preview.ts`
- Create: `web/src/utils/__tests__/preview.test.ts`
- Reference: `web/src/components/RssXmlPreview.vue` (cleanContent, addLineNumbers implementation)

### Steps

- [ ] **Step 1: Write failing test for `cleanContent`**

```typescript
// web/src/utils/__tests__/preview.test.ts
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd web && pnpm vitest run src/utils/__tests__/preview.test.ts`
Expected: FAIL — "cleanContent is not a function"

- [ ] **Step 3: Write minimal `cleanContent` implementation**

```typescript
// web/src/utils/preview.ts
/**
 * Removes surrounding quotes (double or single) from content.
 * Condition: entire content is quoted and inner content does not start with < (not real XML).
 */
export function cleanContent(content: string): string {
  if (!content) return ''
  let cleaned = content.trim()
  if ((cleaned.startsWith('"') && cleaned.endsWith('"')) ||
      (cleaned.startsWith("'") && cleaned.endsWith("'"))) {
    if (!cleaned.slice(1, -1).trim().startsWith('<')) {
      cleaned = cleaned.slice(1, -1)
    }
  }
  return cleaned
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd web && pnpm vitest run src/utils/__tests__/preview.test.ts`
Expected: PASS (cleanContent tests)

- [ ] **Step 5: Write failing test for `addLineNumbers`**

```typescript
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
    expect(result).toContain('<span class="code-line-content"></span>')
  })
})
```

- [ ] **Step 6: Run test to verify it fails**

Run: `cd web && pnpm vitest run src/utils/__tests__/preview.test.ts`
Expected: FAIL — "addLineNumbers is not a function"

- [ ] **Step 7: Write minimal `addLineNumbers` implementation**

```typescript
// web/src/utils/preview.ts (append)
export interface LineNumberOptions {
  maxWidth?: number
}

export function addLineNumbers(content: string, options?: LineNumberOptions): string {
  const lines = content.split('\n')
  const maxLineNum = lines.length
  const lineNumWidth = maxLineNum.toString().length

  return lines
    .map((line, index) => {
      const lineNum = (index + 1).toString().padStart(lineNumWidth, ' ')
      return `<div class="code-line"><span class="code-line-number">${lineNum}</span><span class="code-line-content">${line}</span></div>`
    })
    .join('\n')
}
```

- [ ] **Step 8: Run test to verify it passes**

Run: `cd web && pnpm vitest run src/utils/__tests__/preview.test.ts`
Expected: PASS

- [ ] **Step 9: Commit**

```bash
git add web/src/utils/preview.ts web/src/utils/__tests__/preview.test.ts
git commit -m "feat(preview): extract cleanContent and addLineNumbers as pure utils"
```

---

## Task 2: Phase 1 — Extract `highlightXml` Utils

**Files:**
- Create: `web/src/utils/preview.highlight.ts`
- Modify: `web/src/utils/__tests__/preview.test.ts`
- Reference: `web/src/components/RssXmlPreview.vue` (lines 27-77, highlightXml implementation)

### Steps

- [ ] **Step 1: Write failing test for `highlightXml`**

```typescript
describe('highlightXml', () => {
  it('highlights XML tag names', () => {
    const result = highlightXml('<rss>')
    expect(result).toContain('<span class="xml-tag-name">rss</span>')
  })

  it('highlights attribute names and values', () => {
    const result = highlightXml('<item title="hello">')
    expect(result).toContain('<span class="xml-attr-name">title</span>')
    expect(result).toContain('<span class="xml-attr-value">"hello"</span>')
  })

  it('highlights CDATA sections', () => {
    const result = highlightXml('<![CDATA[data]]>')
    expect(result).toContain('<span class="xml-cdata">')
  })

  it('highlights comments', () => {
    const result = highlightXml('<!-- comment -->')
    expect(result).toContain('<span class="xml-comment">')
  })

  it('highlights processing instructions', () => {
    const result = highlightXml('<?xml version="1.0"?>')
    expect(result).toContain('<span class="xml-pi">')
  })

  it('escapes &, <, > characters', () => {
    const result = highlightXml('a & b < c > d')
    expect(result).toContain('&amp;')
    expect(result).toContain('&lt;')
    expect(result).toContain('&gt;')
  })
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd web && pnpm vitest run src/utils/__tests__/preview.test.ts`
Expected: FAIL — "highlightXml is not a function"

- [ ] **Step 3: Write `highlightXml` implementation from RssXmlPreview.vue lines 27-77**

```typescript
// web/src/utils/preview.highlight.ts
export function highlightXml(xml: string): string {
  xml = xml
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')

  // Highlight XML tags
  xml = xml.replace(/(&lt;\/?)([\w:.-]+)(&gt;)/g, (_match, open, tag, close) => {
    return `<span class="xml-tag-bracket">${open}</span><span class="xml-tag-name">${tag}</span><span class="xml-tag-bracket">${close}</span>`
  })

  // Highlight attributes
  xml = xml.replace(/(\s)([\w:.-]+)(=)(&quot;[^&]*&quot;)/g, (_match, space, attr, eq, value) => {
    return `${space}<span class="xml-attr-name">${attr}</span>${eq}<span class="xml-attr-value">${value}</span>`
  })

  // Highlight CDATA sections
  xml = xml.replace(/(&lt;\!\[CDATA\[)([\s\S]*?)(\]\]&gt;)/g, (_match, open, content, close) => {
    return `<span class="xml-cdata">${open}${content}${close}</span>`
  })

  // Highlight comments
  xml = xml.replace(/(&lt;!--)([\s\S]*?)(--&gt;)/g, (_match, open, content, close) => {
    return `<span class="xml-comment">${open}${content}${close}</span>`
  })

  // Highlight processing instructions
  xml = xml.replace(/(&lt;\?)([\w:.-]+)(.*?)(\?&gt;)/g, (_match, open, target, content, close) => {
    return `<span class="xml-pi">${open}${target}${content}${close}</span>`
  })

  return xml
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd web && pnpm vitest run src/utils/__tests__/preview.test.ts`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add web/src/utils/preview.highlight.ts web/src/utils/__tests__/preview.test.ts
git commit -m "feat(preview): extract highlightXml as pure utils"
```

---

## Task 3: Phase 1 — Extract `highlightJson` and `manualHighlightJson` Utils

**Files:**
- Modify: `web/src/utils/preview.highlight.ts`
- Modify: `web/src/utils/__tests__/preview.test.ts`
- Reference: `web/src/components/JsonPreview.vue` (highlightJson, manualHighlightJson implementations)

### Steps

- [ ] **Step 1: Write failing test for `highlightJson` and `manualHighlightJson`**

```typescript
describe('highlightJson', () => {
  it('highlights JSON keys', () => {
    const result = highlightJson('{"key": "value"}')
    expect(result).toContain('<span class="json-key">')
  })

  it('highlights string values', () => {
    const result = highlightJson('{"key": "value"}')
    expect(result).toContain('<span class="json-string">')
  })

  it('highlights numbers', () => {
    const result = highlightJson('{"num": 123}')
    expect(result).toContain('<span class="json-number">123</span>')
  })

  it('highlights booleans', () => {
    const result = highlightJson('{"flag": true}')
    expect(result).toContain('<span class="json-boolean">true</span>')
  })

  it('highlights null', () => {
    const result = highlightJson('{"val": null}')
    expect(result).toContain('<span class="json-null">null</span>')
  })

  it('escapes < and > characters', () => {
    const result = highlightJson('{"html": "<b>"}')
    expect(result).toContain('&lt;')
    expect(result).toContain('&gt;')
  })
})

describe('manualHighlightJson', () => {
  it('handles nested JSON objects', () => {
    const result = manualHighlightJson('{"outer": {"inner": "value"}}')
    expect(result).toContain('<span class="json-key">')
  })

  it('handles JSON arrays', () => {
    const result = manualHighlightJson('["a", "b", "c"]')
    expect(result).toContain('<span class="json-string">')
  })
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd web && pnpm vitest run src/utils/__tests__/preview.test.ts`
Expected: FAIL

- [ ] **Step 3: Write `highlightJson` and `manualHighlightJson` from JsonPreview.vue**

```typescript
// web/src/utils/preview.highlight.ts (append)
import hljs from 'highlight.js'

export function highlightJson(json: string): string {
  try {
    return hljs.highlight(json, { language: 'json' }).value
  } catch {
    return manualHighlightJson(json)
  }
}

export function manualHighlightJson(json: string): string {
  json = json
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')

  let result = ''
  let i = 0

  while (i < json.length) {
    if (json[i] === '"') {
      let stringStart = i
      i++
      while (i < json.length) {
        if (json[i] === '\\' && i + 1 < json.length) {
          i += 2
        } else if (json[i] === '"') {
          i++
          break
        } else {
          i++
        }
      }
      const stringContent = json.substring(stringStart, i)

      let j = i
      while (j < json.length && /\s/.test(json[j])) j++
      const isKey = json[j] === ':'

      if (isKey) {
        result += `<span class="json-key">${stringContent}</span>`
      } else {
        result += `<span class="json-string">${stringContent}</span>`
      }
    }
    else if (json[i] === '-' || (json[i] >= '0' && json[i] <= '9')) {
      let numStart = i
      if (json[i] === '-') i++
      while (i < json.length && /[\d.eE+-]/.test(json[i])) i++
      result += `<span class="json-number">${json.substring(numStart, i)}</span>`
    }
    else if (json.substring(i, i + 4) === 'true') {
      result += '<span class="json-boolean">true</span>'
      i += 4
    }
    else if (json.substring(i, i + 5) === 'false') {
      result += '<span class="json-boolean">false</span>'
      i += 5
    }
    else if (json.substring(i, i + 4) === 'null') {
      result += '<span class="json-null">null</span>'
      i += 4
    }
    else {
      result += json[i]
      i++
    }
  }

  return result
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd web && pnpm vitest run src/utils/__tests__/preview.test.ts`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add web/src/utils/preview.highlight.ts web/src/utils/__tests__/preview.test.ts
git commit -m "feat(preview): extract highlightJson and manualHighlightJson as pure utils"
```

---

## Task 4: Phase 1 — Extract `highlightMarkdownSource` and `escapeHtml` Utils

**Files:**
- Modify: `web/src/utils/preview.highlight.ts`
- Modify: `web/src/utils/__tests__/preview.test.ts`
- Reference: `web/src/components/MarkdownPreview.vue` (`highlightSourceCode` method — rename to `highlightMarkdownSource`)

### Steps

- [ ] **Step 1: Write failing test for `highlightMarkdownSource`**

```typescript
describe('highlightMarkdownSource', () => {
  it('highlights headings', () => {
    const result = highlightMarkdownSource('# Hello')
    expect(result).toContain('<span class="md-header">#</span>')
    expect(result).toContain('<span class="md-header-text">Hello</span>')
  })

  it('highlights bold text', () => {
    const result = highlightMarkdownSource('**bold**')
    expect(result).toContain('<span class="md-bold">')
  })

  it('highlights italic text', () => {
    const result = highlightMarkdownSource('*italic*')
    expect(result).toContain('<span class="md-italic">')
  })

  it('highlights inline code', () => {
    const result = highlightMarkdownSource('`code`')
    expect(result).toContain('<code class="source-inline-code">')
  })

  it('protects code blocks from being highlighted', () => {
    const result = highlightMarkdownSource('```js\nconsole.log("hi")\n```')
    expect(result).toContain('<div class="source-code-block">')
    expect(result).not.toContain('<span class="md-header">')
  })

  it('highlights links', () => {
    const result = highlightMarkdownSource('[link](http://example.com)')
    expect(result).toContain('<span class="md-link-text">')
    expect(result).toContain('<span class="md-link-url">')
  })

  it('highlights list markers', () => {
    const result = highlightMarkdownSource('- item 1')
    expect(result).toContain('<span class="md-list">')
  })

  it('escapes HTML entities', () => {
    const result = highlightMarkdownSource('<div>')
    expect(result).toContain('&lt;')
    expect(result).toContain('&gt;')
  })
})

describe('escapeHtml', () => {
  it('escapes &', () => {
    expect(escapeHtml('&amp;')).toBe('&amp;amp;')
  })
  it('escapes <', () => {
    expect(escapeHtml('<div>')).toBe('&lt;div&gt;')
  })
  it('escapes >', () => {
    expect(escapeHtml('a > b')).toBe('a &gt; b')
  })
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd web && pnpm vitest run src/utils/__tests__/preview.test.ts`
Expected: FAIL

- [ ] **Step 3: Write `highlightMarkdownSource` from MarkdownPreview.vue `highlightSourceCode` method**

```typescript
// web/src/utils/preview.highlight.ts (append)
import hljs from 'highlight.js'

export function escapeHtml(text: string): string {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
}

export function highlightMarkdownSource(source: string): string {
  let result = escapeHtml(source)

  const codeBlocks: { placeholder: string; html: string }[] = []

  result = result.replace(/```(\w*)\n([\s\S]*?)```/g, (_match, lang, code) => {
    let highlightedCode: string
    if (lang && hljs.getLanguage(lang)) {
      try {
        highlightedCode = hljs.highlight(code.trim(), { language: lang }).value
      } catch {
        highlightedCode = hljs.highlightAuto(code.trim()).value
      }
    } else {
      highlightedCode = hljs.highlightAuto(code.trim()).value
    }
    const placeholder = `__CODE_BLOCK_${codeBlocks.length}__`
    codeBlocks.push({
      placeholder,
      html: `<div class="source-code-block"><code class="language-${lang || 'text'}">${highlightedCode}</code></div>`
    })
    return placeholder
  })

  result = result.replace(/`([^`\n]+)`/g, '<code class="source-inline-code">$1</code>')

  for (const block of codeBlocks) {
    result = result.replace(block.placeholder, block.html)
  }

  result = result.replace(/^(#{1,6})\s(.*)$/gm, '<span class="md-header">$1</span> <span class="md-header-text">$2</span>')
  result = result.replace(/\*\*([^*]+)\*\*/g, '<span class="md-bold">$1</span>')
  result = result.replace(/(?<!\*)\*([^*]+)\*(?!\*)/g, '<span class="md-italic">$1</span>')
  result = result.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<span class="md-link-text">$1</span> <span class="md-link-url">($2)</span>')
  result = result.replace(/^(\s*)([-*+])(\s)/gm, '$1<span class="md-list">$2</span>$3')
  result = result.replace(/^(---)$/gm, '<span class="md-hr">$1</span>')
  result = result.replace(/^(&gt;\s?.*)$/gm, '<span class="md-quote">$1</span>')

  return result
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd web && pnpm vitest run src/utils/__tests__/preview.test.ts`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add web/src/utils/preview.highlight.ts web/src/utils/__tests__/preview.test.ts
git commit -m "feat(preview): extract highlightMarkdownSource and escapeHtml as pure utils"
```

---

## Task 5: Phase 2 — Extract Shared CSS to `preview-shared.css`

**Files:**
- Create: `web/src/styles/preview-shared.css`
- Reference: CSS from RssXmlPreview.vue, JsonPreview.vue, MarkdownPreview.vue (all duplicated .code-content styles)

### Steps

- [ ] **Step 1: Create `web/src/styles/preview-shared.css`**

```css
/* ============================================================
   Shared Preview Components Styles
   Light mode base + Dark mode overrides
   ============================================================ */

.code-content {
  color: #334155;
  font-size: 0.75rem;
  line-height: 1.6;
}

.code-content .code-line {
  display: flex;
  line-height: 1.6;
}

.code-content .code-line-number {
  flex-shrink: 0;
  width: 3rem;
  text-align: right;
  padding-right: 1rem;
  user-select: none;
  color: #94a3b8;
}

.code-content .code-line-content {
  flex: 1;
  user-select: text;
  color: #1e293b;
}

/* JSON */
.code-content .json-key { color: #059669; font-weight: 500; }
.code-content .json-string { color: #dc2626; }
.code-content .json-number { color: #7c3aed; }
.code-content .json-boolean { color: #d97706; font-weight: 500; }
.code-content .json-null { color: #6b7280; font-style: italic; }

/* XML */
.code-content .xml-tag-bracket { color: #6366f1; }
.code-content .xml-tag-name { color: #0369a1; font-weight: 600; }
.code-content .xml-attr-name { color: #059669; }
.code-content .xml-attr-value { color: #dc2626; }
.code-content .xml-cdata { color: #7c3aed; font-style: italic; }
.code-content .xml-comment { color: #6b7280; font-style: italic; }
.code-content .xml-pi { color: #d97706; }

/* Markdown source */
.code-content .md-header { color: #0369a1; font-weight: 600; }
.code-content .md-header-text { color: #0f172a; font-weight: 600; }
.code-content .md-bold { font-weight: 700; color: #1e293b; }
.code-content .md-italic { font-style: italic; color: #475569; }
.code-content .md-link-text { color: #0369a1; text-decoration: underline; }
.code-content .md-link-url { color: #059669; }
.code-content .md-list { color: #6366f1; font-weight: 600; }
.code-content .md-hr { color: #94a3b8; }
.code-content .md-quote { color: #6b7280; font-weight: 600; }
.code-content .source-inline-code {
  background: #f1f5f9; padding: 0.125rem 0.25rem;
  border-radius: 0.25rem; color: #dc2626;
}
.code-content .source-code-block {
  margin: 0.5rem 0; padding: 0.75rem; background: #f8fafc;
  border-radius: 0.375rem; overflow-x: auto; border: 1px solid #e2e8f0;
}
.code-content .source-code-block code {
  font-size: 0.7rem; line-height: 1.5;
}

/* Highlight.js theme overrides */
.code-content .hljs-attr { color: #059669; font-weight: 500; }
.code-content .hljs-string { color: #dc2626; }
.code-content .hljs-number { color: #7c3aed; }
.code-content .hljs-literal { color: #d97706; font-weight: 500; }
.code-content .hljs-punctuation { color: #64748b; }
.code-content .hljs { background: transparent; }

/* Dark mode */
.dark .code-content { color: #e2e8f0; }
.dark .code-content .code-line-number { color: #64748b; }
.dark .code-content .code-line-content { color: #e2e8f0; }
.dark .code-content .json-key { color: #34d399; }
.dark .code-content .json-string { color: #fb7185; }
.dark .code-content .json-number { color: #a78bfa; }
.dark .code-content .json-boolean { color: #fbbf24; }
.dark .code-content .json-null { color: #64748b; }
.dark .code-content .xml-tag-bracket { color: #818cf8; }
.dark .code-content .xml-tag-name { color: #38bdf8; }
.dark .code-content .xml-attr-name { color: #34d399; }
.dark .code-content .xml-attr-value { color: #fb7185; }
.dark .code-content .xml-cdata { color: #a78bfa; }
.dark .code-content .xml-comment { color: #64748b; }
.dark .code-content .xml-pi { color: #fbbf24; }
.dark .code-content .md-header { color: #38bdf8; }
.dark .code-content .md-header-text { color: #f1f5f9; }
.dark .code-content .md-bold { color: #f1f5f9; }
.dark .code-content .md-italic { color: #cbd5e1; }
.dark .code-content .md-link-text { color: #38bdf8; }
.dark .code-content .md-link-url { color: #34d399; }
.dark .code-content .md-list { color: #a5b4fc; }
.dark .code-content .md-hr { color: #64748b; }
.dark .code-content .md-quote { color: #9ca3af; }
.dark .code-content .source-inline-code { background: #1e293b; color: #fb7185; }
.dark .code-content .source-code-block { background: #0f172a; border-color: #334155; }
.dark .code-content .hljs-attr { color: #34d399; }
.dark .code-content .hljs-string { color: #fb7185; }
.dark .code-content .hljs-number { color: #a78bfa; }
.dark .code-content .hljs-literal { color: #fbbf24; }
.dark .code-content .hljs-punctuation { color: #94a3b8; }
```

- [ ] **Step 2: Commit**

```bash
git add web/src/styles/preview-shared.css
git commit -m "feat(preview): extract shared CSS to preview-shared.css"
```

---

## Task 6: Phase 3 — Create `PreviewContainer.vue` and Refactored `RssXmlPreview.vue`

**Files:**
- Create: `web/src/components/preview/PreviewContainer.vue`
- Create: `web/src/components/preview/RssXmlPreview.vue`
- Modify: Import paths in callers (via grep find after creation)

### Steps

- [ ] **Step 1: Create `PreviewContainer.vue`**

```vue
<script setup lang="ts">
import DOMPurify from 'dompurify'
import { computed } from 'vue'

const props = defineProps<{
  content: string
  allowedTags?: string[]
}>()

const sanitizedContent = computed(() => {
  if (!props.content) return ''
  return DOMPurify.sanitize(props.content, {
    ADD_TAGS: props.allowedTags ?? ['span'],
    ADD_ATTR: ['class'],
  })
})
</script>

<template>
  <div
    class="text-xs font-mono whitespace-pre code-content"
    v-html="sanitizedContent"
  />
</template>

<style>
@import '@/styles/preview-shared.css';
</style>
```

- [ ] **Step 2: Create refactored `RssXmlPreview.vue` in `components/preview/`**

```vue
<script setup lang="ts">
import { computed } from 'vue'
import { cleanContent, addLineNumbers } from '@/utils/preview'
import { highlightXml } from '@/utils/preview.highlight'
import PreviewContainer from './PreviewContainer.vue'

const props = defineProps<{ content: string }>()

function formatXml(xml: string): string {
  let formatted = ''
  let indent = 0
  const indentSize = 2

  xml = xml.replace(/>\s+</g, '><').trim()
  const tokens = xml.split(/(<[^>]+>)/g).filter((t) => t.trim())

  for (const token of tokens) {
    if (token.startsWith('</')) {
      indent = Math.max(0, indent - 1)
      formatted += ' '.repeat(indent * indentSize) + token + '\n'
    } else if (token.startsWith('<')) {
      formatted += ' '.repeat(indent * indentSize) + token + '\n'
      if (!token.startsWith('<?') && !token.startsWith('<!') && !token.endsWith('/>')) {
        indent++
      }
    } else if (token.trim()) {
      formatted += ' '.repeat(indent * indentSize) + token + '\n'
    }
  }

  return formatted.trim()
}

const rendered = computed(() => {
  if (!props.content) return ''
  const cleaned = cleanContent(props.content)
  const formatted = formatXml(cleaned)
  const highlighted = highlightXml(formatted)
  return addLineNumbers(highlighted)
})
</script>

<template>
  <PreviewContainer :content="rendered" />
</template>
```

- [ ] **Step 3: Find all imports of old `RssXmlPreview.vue` and update to new path**

Run: `grep -rn "RssXmlPreview" web/src --include="*.vue" --include="*.ts" | grep -v preview/`

- [ ] **Step 4: Run tests**

Run: `cd web && pnpm vitest run src/utils/__tests__/preview.test.ts`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add web/src/components/preview/PreviewContainer.vue web/src/components/preview/RssXmlPreview.vue
git commit -m "feat(preview): extract PreviewContainer and refactor RssXmlPreview"
```

---

## Task 7: Phase 3 — Refactor `JsonPreview.vue` → `components/preview/JsonPreview.vue`

**Files:**
- Create: `web/src/components/preview/JsonPreview.vue`

### Steps

- [ ] **Step 1: Create refactored `JsonPreview.vue`**

```vue
<script setup lang="ts">
import { computed } from 'vue'
import { addLineNumbers } from '@/utils/preview'
import { highlightJson } from '@/utils/preview.highlight'
import PreviewContainer from './PreviewContainer.vue'

const props = defineProps<{ content: unknown[] | null }>()

const rendered = computed(() => {
  if (!props.content) return ''
  const formatted = JSON.stringify(props.content, null, 2)
  const highlighted = highlightJson(formatted)
  return addLineNumbers(highlighted)
})
</script>

<template>
  <PreviewContainer :content="rendered" />
</template>
```

- [ ] **Step 2: Update import paths**

Run: `grep -rn "JsonPreview" web/src --include="*.vue" --include="*.ts" | grep -v preview/`

- [ ] **Step 3: Commit**

```bash
git add web/src/components/preview/JsonPreview.vue
git commit -m "feat(preview): refactor JsonPreview to use shared utils"
```

---

## Task 8: Phase 4 — Refactor `MarkdownPreview.vue` → `components/preview/MarkdownPreview.vue`

**Files:**
- Create: `web/src/components/preview/MarkdownPreview.vue`

### Steps

- [ ] **Step 1: Create refactored `MarkdownPreview.vue`**

```vue
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
import PreviewContainer from './PreviewContainer.vue'

const props = defineProps<{ content: string }>()

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
          return hljs.highlightAuto(code).value
        }
      }
      return hljs.highlightAuto(code).value
    },
  }),
  { gfm: true, breaks: true }
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

function cleanMarkdownContent(content: string): string {
  if (!content) return ''
  let cleaned = content.trim()
  if ((cleaned.startsWith('"') && cleaned.endsWith('"')) ||
      (cleaned.startsWith("'") && cleaned.endsWith("'"))) {
    const inner = cleaned.slice(1, -1).trim()
    if (!inner.startsWith('#') && !inner.startsWith('-') && !inner.startsWith('*')) {
      cleaned = inner
    }
  }
  return cleaned
}

const sanitizedHtml = computed(() => {
  if (!renderedHtml.value) return ''
  return DOMPurify.sanitize(renderedHtml.value)
})

const sanitizedSource = computed(() => {
  if (!props.content) return ''
  const cleaned = cleanMarkdownContent(props.content)
  const highlighted = highlightMarkdownSource(cleaned)
  const withLineNumbers = addLineNumbers(highlighted)
  return DOMPurify.sanitize(withLineNumbers, { ADD_TAGS: ['span', 'div', 'code'] })
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
        @click="viewMode ='preview'"
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
      <div class="text-xs font-mono whitespace-pre code-content" v-html="sanitizedSource" />
    </div>

    <div v-else class="p-4 max-h-[40vh] overflow-auto prose prose-slate dark:prose-invert max-w-none bg-white dark:bg-slate-950">
      <div v-html="sanitizedHtml" />
    </div>
  </div>
</template>
```

- [ ] **Step 2: Update import paths**

Run: `grep -rn "MarkdownPreview" web/src --include="*.vue" --include="*.ts" | grep -v preview/`

- [ ] **Step 3: Run tests**

Run: `cd web && pnpm vitest run src/utils/__tests__/preview.test.ts`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add web/src/components/preview/MarkdownPreview.vue
git commit -m "feat(preview): refactor MarkdownPreview to use shared utils"
```

---

## Task 9: Phase 5 — Component Unit Tests

**Files:**
- Create: `web/src/components/preview/__tests__/PreviewContainer.test.ts`
- Create: `web/src/components/preview/__tests__/RssXmlPreview.test.ts`
- Create: `web/src/components/preview/__tests__/JsonPreview.test.ts`
- Create: `web/src/components/preview/__tests__/MarkdownPreview.test.ts`

### Steps

- [ ] **Step 1: Write `PreviewContainer.test.ts`**

```typescript
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import PreviewContainer from '../PreviewContainer.vue'

describe('PreviewContainer', () => {
  it('renders content with v-html', () => {
    const wrapper = mount(PreviewContainer, {
      props: { content: '<span class="xml-tag-name">test</span>' }
    })
    expect(wrapper.find('.code-content').exists()).toBe(true)
    expect(wrapper.html()).toContain('test')
  })

  it('sanitizes dangerous content (no script tags)', () => {
    const wrapper = mount(PreviewContainer, {
      props: { content: '<script>alert(1)</script><span>safe</span>' }
    })
    expect(wrapper.html()).not.toContain('script')
    expect(wrapper.html()).toContain('safe')
  })

  it('allows additional tags when specified', () => {
    const wrapper = mount(PreviewContainer, {
      props: { content: '<div>test</div>', allowedTags: ['span', 'div'] }
    })
    expect(wrapper.html()).toContain('<div>test</div>')
  })

  it('returns empty for empty content', () => {
    const wrapper = mount(PreviewContainer, {
      props: { content: '' }
    })
    expect(wrapper.find('.code-content').text()).toBe('')
  })
})
```

- [ ] **Step 2: Write component tests for RssXmlPreview, JsonPreview, MarkdownPreview** (test integration of shared utils)

- [ ] **Step 3: Run component tests**

Run: `cd web && pnpm vitest run src/components/preview/__tests__/`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add web/src/components/preview/__tests__/
git commit -m "test(preview): add component unit tests"
```

---

## Task 10: Phase 6 — E2E BDD Tests

**Files:**
- Create: `web/e2e/preview-components.spec.ts`

### Steps

- [ ] **Step 1: Write E2E tests**

```typescript
import { test, expect } from '@playwright/test'

test.describe('Preview Components — RSS/XML/JSON/Markdown', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/history')
    await page.waitForLoadState('networkidle')
  })

  test.describe('RSS/XML Preview', () => {
    test('XML content is syntax highlighted with xml-* classes', async ({ page }) => {
      // Navigate to history, open preview dialog
      // Switch to RSS tab
      await expect(page.locator('.xml-tag-name').first()).toBeVisible()
    })

    test('XML content has line numbers', async ({ page }) => {
      await expect(page.locator('.code-line-number').first()).toBeVisible()
    })
  })

  test.describe('JSON Preview', () => {
    test('JSON content is syntax highlighted with json-* classes', async ({ page }) => {
      await expect(page.locator('.json-key').first()).toBeVisible()
    })

    test('JSON content has line numbers', async ({ page }) => {
      await expect(page.locator('.code-line-number').first()).toBeVisible()
    })
  })

  test.describe('Markdown Preview', () => {
    test('default view is preview mode (rendered HTML)', async ({ page }) => {
      await expect(page.locator('.prose').first()).toBeVisible()
    })

    test('can switch to source view', async ({ page }) => {
      await page.click('button:has-text("Source")')
      await expect(page.locator('.md-header').first()).toBeVisible()
    })

    test('can switch back to preview view', async ({ page }) => {
      await page.click('button:has-text("Preview")')
      await expect(page.locator('.prose').first()).toBeVisible()
    })
  })
})
```

- [ ] **Step 2: Run E2E tests**

Run: `cd web && pnpm test:e2e`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add web/e2e/preview-components.spec.ts
git commit -m "test(preview): add E2E BDD tests for preview components"
```

---

## Task 11: Phase 7 & 8 — Full E2E Suite and Delete Old Files

### Steps

- [ ] **Step 1: Run full E2E suite**

Run: `cd web && pnpm test:e2e`
Expected: ALL PASS (if any failures, fix before proceeding)

- [ ] **Step 2: Delete old files**

```bash
rm web/src/components/RssXmlPreview.vue
rm web/src/components/JsonPreview.vue
rm web/src/components/MarkdownPreview.vue
```

- [ ] **Step 3: Update all import paths that referenced old locations**

Run: `grep -rn "from '@/components/RssXmlPreview'" web/src --include="*.vue" --include="*.ts"`
Run: `grep -rn "from '@/components/JsonPreview'" web/src --include="*.vue" --include="*.ts"`
Run: `grep -rn "from '@/components/MarkdownPreview'" web/src --include="*.vue" --include="*.ts"`
Update each to use `components/preview/` path

- [ ] **Step 4: Run full test suite**

Run: `cd web && pnpm test:run && pnpm test:e2e`
Expected: ALL PASS

- [ ] **Step 5: Final commit**

```bash
git add -A
git commit -m "refactor(preview): complete migration to components/preview/, delete old files"
```

---

## Spec Coverage Check

| Spec Section | Task |
|---|---|
| Phase 1: `utils/preview.ts` (`cleanContent`, `addLineNumbers`) | Task 1 |
| Phase 1: `utils/preview.highlight.ts` (highlight functions) | Tasks 2, 3, 4 |
| Phase 2: `styles/preview-shared.css` | Task 5 |
| Phase 3: `PreviewContainer.vue` + `RssXmlPreview.vue` | Task 6 |
| Phase 3: `JsonPreview.vue` | Task 7 |
| Phase 4: `MarkdownPreview.vue` | Task 8 |
| Component unit tests | Task 9 |
| E2E BDD tests | Task 10 |
| Delete old files | Task 11 |