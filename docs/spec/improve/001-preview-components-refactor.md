# Preview Components 重構規格書

**文件編號**: 001-preview-components-refactor  
**版本**: v0.1  
**日期**: 2026-05-12  
**作者**: AI Assistant (Hermes)  
**適用版本**: v0.18.0  
**狀態**: 草稿 (待審核)

---

## 1. 背景與目標

### 1.1 現況問題

`web/src/components/` 中有三個獨立的 Preview 元件，各自封裝 RSS/JSON/Markdown 格式的展示邏輯：

| 元件 | 行數 | 定位 |
|------|------|------|
| `RssXmlPreview.vue` | 167 行 | 純展示 XML |
| `JsonPreview.vue` | 179 行 | 純展示 JSON |
| `MarkdownPreview.vue` | 361 行 | 展示 + Source/Preview 切換 |

三個元件存在大量重複：

- **`cleanContent()`** —幾乎完全相同的去引號邏輯，在三個檔案中各有一份
- **`addLineNumbers()`** —行號包裝結構相同（`<div class="code-line">` + 行號 + 內容），各自重複
- **Light/Dark mode CSS** —`.code-content`、`.code-line`、`.code-line-number`、`.code-line-content` 四個 class 的樣式在三個檔案中幾乎一致
- **DOMPurify sanitization** —各自重複相同配置（`RssXmlPreview` 與 `JsonPreview` 甚至完全相同）
- **手動語法亮解** —`RssXmlPreview` 的正則、`JsonPreview` 的狀態機、`MarkdownPreview` 的 placeholder 保護，都是各自為戰

### 1.2 重構目標

1. **消除重複**：提取共用的 utilities、composables、CSS
2. **改善維護性**：修改一次處處生效，不再需要對三個檔案做相同修改
3. **提升可測試性**：將純函式邏輯與 Vue 元件分離，支援 pure unit test
4. **保持 TDD**：從測試驅動重構，每個重構步驟都有對應測試保護
5. **保持 BDD 驗證**：重構完成後，現有的 Playwright E2E 測試仍須通過

### 1.3 適用版本共識

```
v0.18.0 為基準 → 在新 branch 重構 → 確認新舊元件行為一致 → 刪除舊檔 → E2E test suite 通過 → PR merge
```

---

## 2. 現有實作分析

### 2.1 三元件共同點

| 面向 | 共同實踐 |
|------|---------|
| 包裝方式 | 獨立 `.vue` 元件，位於 `components/` |
| 輸出媒介 | `v-html` 渲染 DOMPurify sanitized HTML |
| XSS 防護 | `DOMPurify.sanitize()` + `ADD_TAGS`/`ADD_ATTR` 白名單 |
| 行號顯示 | `addLineNumbers()` → `<div class="code-line"><span class="code-line-number">N</span><span class="code-line-content">...</span></div>` |
| 雙模式亮色 | Light/Dark mode 透過 `.dark .code-content …` CSS class 切換 |
| 容器樣式 | `class="text-xs font-mono whitespace-pre code-content"` |
| 行號樣式 | `flex-shrink:0; width:3rem; text-align:right; user-select:none` |

### 2.2 三元件差異點

| 面向 | RssXmlPreview | JsonPreview | MarkdownPreview |
|------|--------------|-------------|-----------------|
| **功能定位** | 純展示 | 純展示 | 有互動（Source/Preview 切換） |
| **語法亮解** | 手寫正則（tag/attr/CDATA/comment/PI 分段） | 優先 highlight.js，失敗時 manual 狀態機 fallback | Marked + markedHighlight（HTML）；純手寫正則（Source 視圖） |
| **cleanContent** | 檢查是否為被引號包住的非 XML 字串 | 同左 | 額外判斷內層是否為真正 Markdown（`#`/`-`/`*` 開頭） |
| **DOMPurify 允許標籤** | `['span']` | `['span']` | `['pre', 'code', 'span', 'div']` |
| **Max height** | 無 | 無 | `max-h-[40vh]`（由 parent 控制） |
| **依賴** | DOMPurify | DOMPurify, hljs | DOMPurify, hljs, marked, markedHighlight, lucide-vue-next |

### 2.3 現有測試資源

| 類型 | 框架 | 位置 | 現有覆蓋 |
|------|------|------|---------|
| 單元測試 | Vitest | `web/src/components/__tests__/` | `ArticlePreviewDialog.test.ts` (一個參考範例) |
| E2E 測試 | Playwright | `web/e2e/` | 11 支 spec 檔案，無針對 Preview Components 的獨立測試 |

---

## 3. 重構方案

### 3.1 目標資料夾結構

```
web/src/
├── components/
│   └── preview/                    ← 新資料夾
│       ├── PreviewContainer.vue   ← 共用外層容器（行號、scroll、背景）
│       ├── RssXmlPreview.vue      ← 重構：只保留 XML 語法亮解
│       ├── JsonPreview.vue        ← 重構：只保留 JSON 語法亮解
│       ├── MarkdownPreview.vue    ← 重構：Source/Preview 切換 + Markdown 渲染
│       └── __tests__/
│           ├── PreviewContainer.test.ts
│           ├── RssXmlPreview.test.ts
│           ├── JsonPreview.test.ts
│           └── MarkdownPreview.test.ts
├── utils/
│   └── preview.ts                 ← 新共用 pure functions
└── styles/
    └── preview-shared.css         ← 新共用 CSS（由 PreviewContainer.vue scoped @import 載入）
```

### 3.2 階段一：提取共用 Utilities（pure functions，無 Vue 依賴）

#### 3.2.1 `utils/preview.ts`

```typescript
// ─── cleanContent ──────────────────────────────────────────────────────────

/**
 * 移除內容外層包裹的引號（雙引號或單引號）。
 * 條件：整個內容被引號包住，且內層不是以 < 開頭（不是真正的 XML）。
 */
export function cleanContent(content: string): string

// ─── addLineNumbers ─────────────────────────────────────────────────────────

export interface LineNumberOptions {
  maxWidth?: number  // 行號最大位數，預設自動計算
}

export function addLineNumbers(
  content: string,
  options?: LineNumberOptions
): string
// 輸出：<div class="code-line"><span class="code-line-number">N</span><span class="code-line-content">...</span></div>
```

#### 3.2.2 `utils/preview.highlight.ts`

```typescript
// ─── XML 語法亮解 ───────────────────────────────────────────────────────────

export function highlightXml(xml: string): string
// 輸出：HTML 字串，含 <span class="xml-*"> 等 class

// ─── JSON 語法亮解 ─────────────────────────────────────────────────────────

export function highlightJson(json: string): string
// 輸出：HTML 字串，含 <span class="json-*"> 等 class
// 內部優先嘗試 hljs，失敗時 fallback 到 manualHighlightJson

export function manualHighlightJson(json: string): string
// 輸出：HTML 字串，有限狀態機實作

// ─── Markdown Source 亮解 ────────────────────────────────────────────────────

export function highlightMarkdownSource(source: string): string
// 輸出：HTML 字串，含 <span class="md-*"> 等 class
// 使用 placeholder 保護 code block，避免重複處理

// ─── 通用 HTML escape ──────────────────────────────────────────────────────

export function escapeHtml(text: string): string
```

#### 3.2.3 測試驅動驗證（Vitest Unit Tests）

```typescript
// web/src/utils/__tests__/preview.test.ts

describe('cleanContent', () => {
  it('移除雙引號包裝', () => { ... })
  it('移除單引號包裝', () => { ... })
  it('保留真正的 XML 內容', () => { ... })
  it('空白內容回傳空字串', () => { ... })
})

describe('addLineNumbers', () => {
  it('正確計算行號位數', () => { ... })
  it('空行顯示空白內容', () => { ... })
  it('單行內容正確包裝', () => { ... })
  it('輸出 class 結構正確', () => { ... })
})

describe('highlightXml', () => {
  it('亮解 XML tag 名稱', () => { ... })
  it('亮解屬性名稱與值', () => { ... })
  it('亮解 CDATA', () => { ... })
  it('亮解註釋', () => { ... })
  it('亮解處理指令', () => { ... })
})

describe('highlightJson', () => {
  it('亮解 key', () => { ... })
  it('亮解 string value', () => { ... })
  it('亮解 number', () => { ... })
  it('亮解 boolean', () => { ... })
  it('亮解 null', () => { ... })
  it('hljs 失敗時 fallback 到 manualHighlightJson', () => { ... })
})

describe('highlightMarkdownSource', () => {
  it('亮解 heading', () => { ... })
  it('亮解 bold / italic', () => { ... })
  it('亮解 code block（含語言標記）', () => { ... })
  it('亮解 inline code', () => { ... })
  it('亮解 link', () => { ... })
  it('亮解 list marker', () => { ... })
  it('保護 code block 不被其他規則干擾', () => { ... })
})
```

### 3.3 階段二：提取共用 CSS

#### 3.3.1 `web/src/styles/preview-shared.css`

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
.dark .code-content .source-inline-code {
  background: #1e293b; color: #fb7185;
}
.dark .code-content .source-code-block {
  background: #0f172a; border-color: #334155;
}
.dark .code-content .hljs-attr { color: #34d399; }
.dark .code-content .hljs-string { color: #fb7185; }
.dark .code-content .hljs-number { color: #a78bfa; }
.dark .code-content .hljs-literal { color: #fbbf24; }
.dark .code-content .hljs-punctuation { color: #94a3b8; }
```

### 3.4 階段三：重構 Vue 元件

#### 3.4.1 `PreviewContainer.vue`（共用外層容器）

```vue
<!-- 共用行號容器 + scroll + 背景處理 -->
<template>
  <div
    class="text-xs font-mono whitespace-pre code-content"
    v-html="sanitizedContent"
  />
</template>

<script setup lang="ts">
import DOMPurify from 'dompurify'

const props = defineProps<{
  content: string      // 已經過行號包裝的 HTML 字串
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
<style>
@import '@/styles/preview-shared.css';
</style>
```

#### 3.4.2 `RssXmlPreview.vue`（重構後）

```vue
<script setup lang="ts">
import { computed } from 'vue'
import { cleanContent, addLineNumbers, highlightXml } from '@/utils/preview'
import { cleanContent, addLineNumbers, highlightXml } from '@/utils/preview.highlight'
import PreviewContainer from './preview/PreviewContainer.vue'

const props = defineProps<{ content: string }>()

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

#### 3.4.3 `JsonPreview.vue`（重構後）

```vue
<script setup lang="ts">
import { computed } from 'vue'
import { cleanContent, addLineNumbers, highlightJson } from '@/utils/preview.highlight'
import PreviewContainer from './preview/PreviewContainer.vue'

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

#### 3.4.4 `MarkdownPreview.vue`（重構後）

```vue
<!-- 互動功能保留：Source/Preview 切換 -->
<!-- 差異：cleanContent 更複雜（需額外判斷 Markdown 語法），由 utils/preview.markdown.ts 處理 -->
```

### 3.5 階段四：新增 E2E BDD 測試

```typescript
// web/e2e/preview-components.spec.ts

test.describe('Preview Components — RSS/XML/JSON/Markdown', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/history')
    await page.waitForLoadState('networkidle')
  })

  test.describe('History Preview Dialog — Format Tabs', () => {
    // 觸發任意一筆歷史記錄的 Preview Dialog
    // 驗證三個 format tab 都存在且可切換
  })

  test.describe('RSS/XML Preview', () => {
    test('XML content is syntax highlighted', async ({ page }) => {
      // RSS tab → 驗證 .xml-tag-name, .xml-attr-name 等 class 存在
    })
    test('XML content has line numbers', async ({ page }) => {
      // 驗證 .code-line-number 存在
    })
  })

  test.describe('JSON Preview', () => {
    test('JSON content is syntax highlighted', async ({ page }) => {
      // JSON tab → 驗證 .json-key, .json-string 等 class 存在
    })
    test('JSON content has line numbers', async ({ page }) => {
      // 驗證 .code-line-number 存在
    })
  })

  test.describe('Markdown Preview', () => {
    test('Default view is preview mode', async ({ page }) => {
      // Markdown tab → 預設應顯示 rendered HTML（prose class）
    })
    test('Can switch to source view', async ({ page }) => {
      // 點擊 Source tab → 驗證 .md-header 等 class 存在
    })
    test('Can switch back to preview view', async ({ page }) => {
      // 點擊 Preview tab → 驗證返回 HTML 渲染
    })
  })

  test.describe('Copy & Download Actions', () => {
    test('Copy button copies content to clipboard', async ({ page }) => {
      // 點擊 Copy → navigator.clipboard 驗證
    })
    test('Download button triggers download', async ({ page }) => {
      // 點擊 Download → 驗證下載事件觸發
    })
  })
})
```

---

## 4. TDD / BDD 工作流程

### 4.1 TDD 循環（Red → Green → Refactor）

每個重構步驟嚴格遵循：

```
1. 先寫（或更新）unit test → 確認 RED（失敗）
2. 實作重構程式碼 → 確認 GREEN（通過）
3. 如有需要，進一步重構 → 重複 step 1-2
```

### 4.2 BDD 驗證（Playwright E2E）

每次 commit 前，確保：

```bash
cd web && npx playwright test
# 全部通過才可 commit
```

### 4.3 推薦執行順序

```
Phase 1: `web/src/utils/__tests__/preview.test.ts`（pure unit tests）
Phase 2: 重構 RssXmlPreview.vue → `components/preview/RssXmlPreview.vue`（新檔）
Phase 3: 重構 JsonPreview.vue → `components/preview/JsonPreview.vue`（新檔）
Phase 4: 重構 MarkdownPreview.vue → `components/preview/MarkdownPreview.vue`（新檔）
Phase 5: PreviewContainer.test.ts
Phase 6: 新增 E2E: `web/e2e/preview-components.spec.ts`
Phase 7: 執行完整 E2E suite 確認全部通過
Phase 8: 確認重構行為與舊檔一致後，刪除舊檔
```

---

## 5. 風險與緩解

| 風險 | 影響 | 緩解措施 |
|------|------|---------|
| CSS class 名稱衝突 | 破壞其他元件樣式 | 新的 shared CSS 只影響 `.code-content` 範圍內 |
| DOMPurify 設定不一致 | XSS 防護降級 | 共用 `PreviewContainer` 統一管理允許清單 |
| 現有 E2E 測試失敗 | 阻擋 merge | 任何 E2E 失敗須先修復再繼續重構 |
| Markdown Preview 互動複雜 | 重構時引入 bug | MarkdownPreview 的 Source/Preview 切換邏輯單獨測試 |

---

## 6. 預期產出

- [ ] `web/src/utils/preview.ts` — `cleanContent`、`addLineNumbers`
- [ ] `web/src/utils/preview.highlight.ts` — XML/JSON/Markdown 亮解函式
- [ ] `web/src/utils/__tests__/` — 完整的 unit test suite
- [ ] `web/src/styles/preview-shared.css` — 集中化 CSS
- [ ] `web/src/components/preview/PreviewContainer.vue` — 共用容器
- [ ] `web/src/components/preview/RssXmlPreview.vue` — 重構後
- [ ] `web/src/components/preview/JsonPreview.vue` — 重構後
- [ ] `web/src/components/preview/MarkdownPreview.vue` — 重構後
- [ ] `web/src/components/preview/__tests__/` — 元件 unit tests
- [ ] `web/e2e/preview-components.spec.ts` — E2E BDD 測試
- [ ] 全部 E2E test suite 通過

---

## 7. 審核清單（合併前必查）

- [ ] Unit tests: `vitest run` 全部通過
- [ ] E2E tests: `npx playwright test` 全部通過
- [ ] 原始三個元件（RssXmlPreview/JsonPreview/MarkdownPreview）邏輯行為與重構前完全一致
- [ ] CSS 變更沒有破壞其他元件外觀
- [ ] PR 分支從 `v0.18.1` 衍生，差異僅包含重構相關變更
- [ ] 文件已更新（README 或 CHANGELOG 說明重構影響）
