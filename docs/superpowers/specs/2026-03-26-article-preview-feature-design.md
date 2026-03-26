# Article Quick Preview Feature Design

**Date**: 2026-03-26
**Author**: Kimhsiao
**Status**: Draft

## Overview

This document describes the design for adding a quick preview feature to the RSS Aggregator. Users can preview article content using the markdown.new service without leaving the application. The feature will be available on both the Feed page and the History page.

## Goals

1. Allow users to quickly preview article content in a dialog
2. Cache preview content in the database for faster subsequent access
3. Provide source/preview toggle in the preview dialog
4. Support both "Quick Preview" and "Open in New Tab" options
5. Implement using TDD methodology

## Non-Goals

- Real-time content sync or updates
- Offline preview support
- Custom preview settings per user
- Preview content expiration/TTL

## Architecture

### System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (Vue 3)                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  FeedPage.vue / HistoryPage.vue                                  │
│       │                                                          │
│       ▼                                                          │
│  ┌─────────────────────────────────────┐                        │
│  │   ArticlePreviewDialog.vue          │                        │
│  │   - Check local cache               │                        │
│  │   - Call markdown.new API           │                        │
│  │   - Save to backend                 │                        │
│  │   - Display Markdown preview        │                        │
│  └─────────────────────────────────────┘                        │
│       │                                                          │
│       │ HTTP                                                     │
│       ▼                                                          │
├─────────────────────────────────────────────────────────────────┤
│                     Backend (FastAPI)                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  /api/v1/previews                                                 │
│  - GET  /{url_hash}  → Get cached content                        │
│  - POST /           → Save preview content                       │
│                                                                   │
│  PreviewContent Model                                             │
│  - id, url, url_hash, markdown_content, title                    │
│  - created_at, updated_at                                        │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

### Design Decision: Frontend Direct Call

**Chosen approach**: Frontend directly calls markdown.new API, backend only handles caching.

**Rationale**:
1. Simpler implementation, backend only needs CRUD API
2. Rate limiting per user IP (fairer for multi-user scenarios)
3. Caching ensures each URL is converted only once
4. Consistent with existing useFeedCache architecture pattern

## External API Contract

### markdown.new API

**Endpoint**: `POST https://markdown.new/`

**Request Headers**:
```
Content-Type: application/json
```

**Request Body**:
```json
{
  "url": "https://example.com/article",
  "retain_images": true
}
```

**Query Parameter Alternative**:
```
GET https://markdown.new/https://example.com/article?retain_images=true
```

**Response Headers**:
```
Content-Type: text/markdown; charset=utf-8
x-markdown-tokens: 725
x-rate-limit-remaining: 499
```

**Success Response** (200):
```markdown
---
title: Article Title
---

# Article Title

Article content in markdown format...
```

**Error Responses**:
| Status | Description |
|--------|-------------|
| 400 | Invalid URL or malformed request |
| 404 | URL not found or page inaccessible |
| 429 | Rate limit exceeded (500/day/IP) |
| 500 | Internal server error |
| 503 | Service temporarily unavailable |

**Rate Limit**: 500 requests per day per IP address

**Timeout**: 30 seconds

## Size Limits and Validation

### Content Size Limits

| Field | Max Size | Validation |
|-------|----------|------------|
| `url` | 2048 chars | Must be valid HTTP/HTTPS URL |
| `markdown_content` | 10 MB | Truncate if exceeds limit with warning |
| `title` | 500 chars | Extract from markdown frontmatter or first H1 |

### Frontend Validation

```typescript
const MAX_MARKDOWN_SIZE = 10 * 1024 * 1024; // 10 MB

function validateMarkdownContent(content: string): ValidationResult {
  if (content.length > MAX_MARKDOWN_SIZE) {
    return {
      valid: false,
      error: 'Content too large, truncating...',
      truncated: content.slice(0, MAX_MARKDOWN_SIZE)
    };
  }
  return { valid: true, content };
}
```

### Backend Validation

```python
MAX_MARKDOWN_SIZE = 10 * 1024 * 1024  # 10 MB

def validate_preview_content(content: str) -> str:
    if len(content) > MAX_MARKDOWN_SIZE:
        logger.warning(f"Preview content truncated from {len(content)} to {MAX_MARKDOWN_SIZE}")
        return content[:MAX_MARKDOWN_SIZE]
    return content
```

## Race Condition Handling

### Scenario
Two users request preview for the same URL simultaneously:
1. Both check cache → 404 Not Found
2. Both call markdown.new API
3. Both try to save → Second one fails on unique constraint

### Solution: Upsert Pattern

**Backend Service**:
```python
async def save_preview(url: str, markdown_content: str, title: str | None) -> PreviewContent:
    url_hash = compute_url_hash(url)
    
    # Try to get existing record
    existing = await get_preview_by_hash(url_hash)
    if existing:
        # Update existing record
        existing.markdown_content = markdown_content
        existing.title = title
        existing.updated_at = datetime.utcnow()
        await session.commit()
        return existing
    
    # Create new record (handle race condition)
    try:
        preview = PreviewContent(
            url=url,
            url_hash=url_hash,
            markdown_content=markdown_content,
            title=title
        )
        session.add(preview)
        await session.commit()
        return preview
    except IntegrityError:
        # Another request created it first - fetch and return
        await session.rollback()
        return await get_preview_by_hash(url_hash)
```

### Frontend Handling

```typescript
// Even if save fails, preview still works
async function savePreview(url: string, content: string): Promise<void> {
  try {
    await api.post('/api/v1/previews', { url, markdown_content: content });
  } catch (error) {
    // Log but don't fail - cache is optional
    console.warn('Failed to save preview cache:', error);
  }
}
```

## URL Normalization

### Normalization Rules

Before hashing, normalize URLs as follows:

1. **Protocol**: Keep as-is (http/https)
2. **Domain**: Lowercase
3. **Path**: Keep as-is (case-sensitive)
4. **Query Parameters**: Sort alphabetically
5. **Fragment**: Remove (#section)
6. **Trailing Slash**: Remove (unless path is just `/`)

### Implementation

```typescript
function normalizeUrl(url: string): string {
  try {
    const parsed = new URL(url);
    
    // Lowercase domain
    parsed.host = parsed.host.toLowerCase();
    
    // Sort query parameters
    const params = new URLSearchParams(parsed.search);
    const sortedParams = new URLSearchParams([...params.entries()].sort());
    parsed.search = sortedParams.toString();
    
    // Remove fragment
    parsed.hash = '';
    
    // Remove trailing slash (except root)
    if (parsed.pathname !== '/' && parsed.pathname.endsWith('/')) {
      parsed.pathname = parsed.pathname.slice(0, -1);
    }
    
    return parsed.toString();
  } catch {
    throw new Error('Invalid URL');
  }
}

function computeUrlHash(url: string): string {
  const normalized = normalizeUrl(url);
  // SHA-256 hash in hex
  return crypto.subtle.digest('SHA-256', new TextEncoder().encode(normalized))
    .then(buffer => Array.from(new Uint8Array(buffer))
      .map(b => b.toString(16).padStart(2, '0'))
      .join(''));
}
```

### Example

| Original URL | Normalized URL |
|-------------|----------------|
| `https://Example.com/Article?b=2&a=1#section` | `https://example.com/Article?a=1&b=2` |
| `https://example.com/path/` | `https://example.com/path` |
| `https://example.com/` | `https://example.com/` |

## Components

### Backend: PreviewContent Model

**File**: `src/models/preview_content.py`

```python
class PreviewContent(Base, TimestampMixin):
    """Cached markdown preview content for URLs."""
    
    __tablename__ = "preview_contents"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, init=False)
    url: Mapped[str] = mapped_column(String(2048), unique=True, index=True)
    url_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    markdown_content: Mapped[str] = mapped_column(Text)
    title: Mapped[str | None] = mapped_column(String(500), default=None)
```

### Backend: API Endpoints

**File**: `src/api/routes/previews.py`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/previews/{url_hash}` | Get cached preview content |
| POST | `/api/v1/previews` | Save preview content (upsert) |

**Request/Response**:

```json
// GET /api/v1/previews/{url_hash}
// Response 200:
{
  "id": 1,
  "url": "https://example.com/article",
  "url_hash": "abc123...",
  "markdown_content": "# Article Title\n\nContent...",
  "title": "Article Title",
  "created_at": "2026-03-26T10:00:00Z",
  "updated_at": "2026-03-26T10:00:00Z"
}

// Response 404:
{
  "detail": "Preview not found"
}

// POST /api/v1/previews
// Request:
{
  "url": "https://example.com/article",
  "markdown_content": "# Article Title\n\nContent...",
  "title": "Article Title"  // optional
}

// Response 200:
{
  "id": 1,
  "url": "https://example.com/article",
  "url_hash": "abc123...",
  "markdown_content": "# Article Title\n\nContent...",
  "title": "Article Title",
  "created_at": "2026-03-26T10:00:00Z",
  "updated_at": "2026-03-26T10:00:00Z"
}
```

### Frontend: ArticlePreviewDialog Component

**File**: `web/src/components/ArticlePreviewDialog.vue`

#### Component Interface

```typescript
// Props
interface ArticlePreviewDialogProps {
  open: boolean;           // Dialog visibility (v-model)
  url: string;             // Article URL to preview
  title?: string;          // Article title (optional, for display)
}

// Emits
interface ArticlePreviewDialogEmits {
  'update:open': (value: boolean) => void;  // v-model update
  'close': () => void;                       // Dialog closed
}
```

#### Component Features

1. Check cache before fetching
2. Call markdown.new API if not cached
3. Save result to backend
4. Display MarkdownPreview with source/preview toggle
5. Handle loading and error states

#### UI Specifications

| Element | Specification |
|---------|--------------|
| Dialog Size | `max-w-4xl w-full` (max-width: 896px) |
| Dialog Height | `max-h-[80vh]` with scrollable content |
| Dialog Position | Centered on screen |
| Loading State | Skeleton loader with pulse animation |
| Error State | Error message with "Open Original" button |
| Source/Preview Toggle | Tab-style buttons at top of content area |

#### Loading State UI

```
┌─────────────────────────────────────┐
│  Preview                    [X]     │
├─────────────────────────────────────┤
│  ┌─────────────────────────────┐    │
│  │ ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓ │    │
│  │ ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓ │    │
│  │ ▓▓▓▓▓▓▓▓▓▓▓                 │    │
│  │ ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓ │    │
│  └─────────────────────────────┘    │
└─────────────────────────────────────┘
```

#### Dialog Layout

```
┌─────────────────────────────────────┐
│  Preview                    [X]     │
├─────────────────────────────────────┤
│  [Source] [Preview]                 │
├─────────────────────────────────────┤
│                                      │
│  # Article Title                    │
│                                      │
│  Article content in markdown...     │
│  ...                                │
│                                      │
└─────────────────────────────────────┘
```

### Frontend: useArticlePreview Composable

**File**: `web/src/composables/useArticlePreview.ts`

**Responsibilities**:
- Hash URL using SHA-256
- Check cache via API
- Call markdown.new API
- Save preview content
- Handle errors

### Frontend: UI Integration

**FeedPage.vue** and **HistoryPage.vue**:

Add two icon buttons to each news item card:
- 👁 (Eye icon): Quick Preview - Opens ArticlePreviewDialog
- 🔗 (External Link icon): Open in New Tab - Opens original URL

**Button Placement**: Right side or bottom-right of each card

## Backend Service Layer

### PreviewService Interface

**File**: `src/services/preview_service.py`

```python
class PreviewService:
    """Service for managing cached preview content."""
    
    def __init__(self, session: AsyncSession):
        self._session = session
    
    async def get_by_url_hash(self, url_hash: str) -> PreviewContent | None:
        """
        Retrieve cached preview by URL hash.
        
        Args:
            url_hash: SHA-256 hash of normalized URL
            
        Returns:
            PreviewContent if found, None otherwise
        """
        ...
    
    async def get_by_url(self, url: str) -> PreviewContent | None:
        """
        Retrieve cached preview by URL.
        
        Args:
            url: Original article URL
            
        Returns:
            PreviewContent if found, None otherwise
        """
        ...
    
    async def upsert(
        self, 
        url: str, 
        markdown_content: str, 
        title: str | None = None
    ) -> PreviewContent:
        """
        Create or update preview content.
        
        Handles race conditions using upsert pattern:
        1. Check if record exists
        2. If yes, update and return
        3. If no, create new (handle IntegrityError)
        
        Args:
            url: Original article URL
            markdown_content: Markdown content from markdown.new
            title: Optional title extracted from content
            
        Returns:
            Created or updated PreviewContent
        """
        ...
    
    async def delete_by_url(self, url: str) -> bool:
        """
        Delete cached preview by URL.
        
        Args:
            url: Original article URL
            
        Returns:
            True if deleted, False if not found
        """
        ...
```

### Service Layer Error Handling

```python
class PreviewServiceError(Exception):
    """Base error for preview service operations."""
    pass

class PreviewNotFoundError(PreviewServiceError):
    """Raised when preview is not found."""
    pass

class PreviewValidationError(PreviewServiceError):
    """Raised when input validation fails."""
    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message
        super().__init__(f"Validation error: {field} - {message}")
```

## State Management Strategy

### Decision: Local Component State

**Rationale**:
1. Preview state is isolated to individual preview sessions
2. No need to share preview state across components
3. Dialog lifecycle handles state cleanup automatically
4. Simpler than introducing Pinia store for single-use state

### Implementation Pattern

```typescript
// ArticlePreviewDialog.vue - local state
const props = defineProps<ArticlePreviewDialogProps>();
const emit = defineEmits<ArticlePreviewDialogEmits>();

// Local state
const loading = ref(true);
const error = ref<PreviewError | null>(null);
const content = ref<string>('');
const source = ref<'cache' | 'api'>('api');
const mode = ref<'preview' | 'source'>('preview');

// Composable for business logic
const { fetchPreview, savePreview } = useArticlePreview();
```

### Handling Multiple Concurrent Previews

Each dialog instance has its own state. When user opens multiple previews:
1. Each dialog maintains independent loading/error/content state
2. Cache check returns cached content instantly
3. No race conditions because each URL has unique hash

### Frontend In-Memory Cache (Optional Enhancement)

```typescript
// Simple in-memory cache for session
const previewCache = new Map<string, CachedPreview>();

interface CachedPreview {
  content: string;
  title?: string;
  fetchedAt: Date;
}

// Cache invalidation: Clear on page navigation or after 30 minutes
const CACHE_TTL = 30 * 60 * 1000; // 30 minutes

function getCachedPreview(urlHash: string): CachedPreview | null {
  const cached = previewCache.get(urlHash);
  if (cached && Date.now() - cached.fetchedAt.getTime() < CACHE_TTL) {
    return cached;
  }
  previewCache.delete(urlHash);
  return null;
}
```

## Page Integration Details

### FeedPage.vue Integration

```vue
<script setup lang="ts">
import ArticlePreviewDialog from '@/components/ArticlePreviewDialog.vue';
import { Eye, ExternalLink } from 'lucide-vue-next';
import { useI18n } from 'vue-i18n';

const { t } = useI18n();

// Preview dialog state
const previewDialogOpen = ref(false);
const previewUrl = ref('');
const previewTitle = ref('');

function openPreview(item: FeedItem) {
  previewUrl.value = item.link;
  previewTitle.value = item.title;
  previewDialogOpen.value = true;
}

function openInNewTab(url: string) {
  window.open(url, '_blank', 'noopener,noreferrer');
}
</script>

<template>
  <div class="feed-item">
    <!-- Item content -->
    
    <!-- Preview action buttons -->
    <div class="flex gap-2">
      <button
        @click="openPreview(item)"
        class="btn-icon"
        :title="t('preview.quick_preview')"
        :aria-label="t('preview.quick_preview')"
      >
        <Eye class="w-4 h-4" />
      </button>
      <button
        @click="openInNewTab(item.link)"
        class="btn-icon"
        :title="t('preview.open_new_tab')"
        :aria-label="t('preview.open_new_tab')"
      >
        <ExternalLink class="w-4 h-4" />
      </button>
    </div>
  </div>
  
  <!-- Preview dialog -->
  <ArticlePreviewDialog
    v-model:open="previewDialogOpen"
    :url="previewUrl"
    :title="previewTitle"
  />
</template>
```

### HistoryPage.vue Integration

Same pattern as FeedPage, but applied to expanded history items:

```vue
<template>
  <div v-for="batch in historyBatches" :key="batch.id">
    <button @click="toggleBatch(batch.id)">
      {{ batch.name }}
    </button>
    
    <div v-if="expandedBatches.has(batch.id)" class="history-items">
      <div v-for="item in batch.items" :key="item.id" class="history-item">
        <!-- Item content -->
        
        <!-- Preview action buttons (same as FeedPage) -->
        <div class="flex gap-2">
          <button @click="openPreview(item)" :title="t('preview.quick_preview')">
            <Eye class="w-4 h-4" />
          </button>
          <button @click="openInNewTab(item.link)" :title="t('preview.open_new_tab')">
            <ExternalLink class="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  </div>
  
  <ArticlePreviewDialog
    v-model:open="previewDialogOpen"
    :url="previewUrl"
    :title="previewTitle"
  />
</template>
```

### Dialog Lifecycle Management

```typescript
// Dialog automatically cleans up on close
watch(() => props.open, (isOpen) => {
  if (!isOpen) {
    // Cleanup: Cancel any pending requests
    abortController?.abort();
    // Reset state
    loading.value = true;
    error.value = null;
  } else {
    // Open: Fetch content
    fetchContent();
  }
});

// Cleanup on component unmount
onUnmounted(() => {
  abortController?.abort();
});
```

## Data Flow

### Quick Preview Flow

```
User clicks "Quick Preview" button
        │
        ▼
┌───────────────────────────┐
│ Calculate URL SHA-256 hash│
│ (frontend)                │
└───────────────────────────┘
        │
        ▼
┌───────────────────────────┐
│ GET /api/v1/previews/{hash}│
└───────────────────────────┘
        │
        ├─── 200 OK ──────────────────────────┐
        │                                      ▼
        │                           ┌─────────────────────┐
        │                           │ Display cached      │
        │                           │ Markdown preview    │
        │                           └─────────────────────┘
        │
        └─── 404 Not Found ───────────────────┐
                                               ▼
                              ┌─────────────────────────────┐
                              │ POST https://markdown.new/  │
                              │ Body: { url, retain_images: true } │
                              └─────────────────────────────┘
                                               │
                                               ▼
                              ┌─────────────────────────────┐
                              │ POST /api/v1/previews      │
                              │ Body: { url, markdown_content, title } │
                              └─────────────────────────────┘
                                               │
                                               ▼
                              ┌─────────────────────────────┐
                              │ Display Markdown preview   │
                              └─────────────────────────────┘
```

### Open in New Tab Flow

```
User clicks "Open in New Tab" button
        │
        ▼
window.open(item.link, '_blank')
```

## Error Handling

### Error Scenarios

#### Backend API Errors

| Scenario | HTTP Status | Frontend Handling |
|---------|------------|-------------------|
| URL cache not found | 404 | Continue to call markdown.new |
| Backend save failed | 500 | Log error, preview still displays (but not cached) |

#### markdown.new API Errors

| Scenario | HTTP Status | Frontend Handling |
|---------|------------|-------------------|
| Rate limit exceeded | 429 | Show "Preview service temporarily unavailable, please try again later" with "Open Original" button |
| Invalid URL | 400 | Show "Invalid URL, cannot preview" |
| URL not found | 404 | Show "This page does not exist or is inaccessible" with "Open Original" button |
| Server error | 500 | Show "Preview service error, please try again later" with "Open Original" button |
| Service unavailable | 503 | Show "Preview service temporarily unavailable" with "Open Original" button |
| Network timeout | - | Show "Preview request timed out, please try again" |
| Network error | - | Show "Network error, please check your connection" |

#### Content Errors

| Scenario | Frontend Handling |
|---------|-------------------|
| Content too large | Truncate to 10MB, show warning "Content truncated due to size" |
| Requires login/paywall | Show "This page may require login or subscription" with "Open Original" button |
| Empty content | Show "No content could be extracted from this page" |
| Unsupported content type | Show "This content type cannot be previewed" |

### Error Handling Pattern

```typescript
class PreviewError extends Error {
  constructor(
    message: string,
    public type: 'rate_limit' | 'network' | 'conversion' | 'validation',
    public showOriginalButton: boolean = true
  ) {
    super(message);
  }
}

async function fetchPreview(url: string): Promise<PreviewResult> {
  // 1. Check cache
  const cached = await getCachedPreview(url);
  if (cached) return { source: 'cache', ...cached };
  
  // 2. Call markdown.new with timeout
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 30000);
  
  try {
    const response = await fetch('https://markdown.new/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url, retain_images: true }),
      signal: controller.signal
    });
    clearTimeout(timeoutId);
    
    if (response.status === 429) {
      throw new PreviewError(
        'Preview service temporarily unavailable',
        'rate_limit'
      );
    }
    
    if (!response.ok) {
      throw new PreviewError(
        `Preview failed: ${response.statusText}`,
        'conversion'
      );
    }
    
    const markdown = await response.text();
    
    // 3. Save cache (failure doesn't affect preview)
    await savePreview(url, markdown).catch(e => console.warn('Cache save failed:', e));
    
    return { source: 'api', markdown };
    
  } catch (error) {
    if (error.name === 'AbortError') {
      throw new PreviewError('Preview request timed out', 'network');
    }
    if (error instanceof TypeError) {
      throw new PreviewError('Network error, please check your connection', 'network');
    }
    throw error;
  }
}
```

## Error Recovery Strategy

### Retry Logic

| Error Type | Retry? | Backoff | Max Retries |
|-----------|--------|---------|-------------|
| Rate Limit (429) | **NO** | - | 0 |
| Network Error | Yes | Exponential | 2 |
| Server Error (500) | Yes | Exponential | 1 |
| Service Unavailable (503) | Yes | Fixed 5s | 1 |
| Timeout | Yes | Fixed 3s | 1 |
| Validation Error (400) | **NO** | - | 0 |
| Not Found (404) | **NO** | - | 0 |

### Retry Implementation

```typescript
interface RetryConfig {
  maxRetries: number;
  baseDelay: number;  // milliseconds
  maxDelay: number;   // milliseconds
}

const DEFAULT_RETRY_CONFIG: RetryConfig = {
  maxRetries: 2,
  baseDelay: 1000,
  maxDelay: 10000,
};

async function fetchWithRetry(
  url: string,
  config: RetryConfig = DEFAULT_RETRY_CONFIG
): Promise<PreviewResult> {
  let lastError: Error | null = null;
  
  for (let attempt = 0; attempt <= config.maxRetries; attempt++) {
    try {
      return await fetchPreview(url);
    } catch (error) {
      lastError = error;
      
      // Don't retry for non-retryable errors
      if (error instanceof PreviewError) {
        if (error.type === 'rate_limit' || error.type === 'validation') {
          throw error;
        }
      }
      
      // Calculate delay with exponential backoff
      if (attempt < config.maxRetries) {
        const delay = Math.min(
          config.baseDelay * Math.pow(2, attempt),
          config.maxDelay
        );
        await sleep(delay);
      }
    }
  }
  
  throw lastError;
}
```

### Fallback Behavior

When markdown.new is completely unavailable:

1. **Show cached content if available** - Always check cache first
2. **Graceful degradation** - Show error with "Open Original" button
3. **No blocking** - Users can always open original URL
4. **Log for monitoring** - Track failures for service health monitoring

### Partial Content Handling

```typescript
async function handlePartialContent(response: Response): Promise<string> {
  const reader = response.body?.getReader();
  const chunks: Uint8Array[] = [];
  let totalSize = 0;
  
  while (reader) {
    const { done, value } = await reader.read();
    if (done) break;
    
    totalSize += value.length;
    
    // Check size limit during streaming
    if (totalSize > MAX_MARKDOWN_SIZE) {
      console.warn('Content truncated during streaming');
      break;
    }
    
    chunks.push(value);
  }
  
  // Combine chunks
  const combined = new Uint8Array(totalSize);
  let offset = 0;
  for (const chunk of chunks) {
    combined.set(chunk, offset);
    offset += chunk.length;
  }
  
  return new TextDecoder().decode(combined);
}
```

## Database Migration

**File**: `alembic/versions/xxxx_add_preview_contents_table.py`

```python
def upgrade() -> None:
    op.create_table(
        'preview_contents',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('url', sa.String(length=2048), nullable=False),
        sa.Column('url_hash', sa.String(length=64), nullable=False),
        sa.Column('markdown_content', sa.Text(), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('url'),
        sa.UniqueConstraint('url_hash'),
    )
    op.create_index(op.f('ix_preview_contents_url'), 'preview_contents', ['url'], unique=False)
    op.create_index(op.f('ix_preview_contents_url_hash'), 'preview_contents', ['url_hash'], unique=False)

def downgrade() -> None:
    op.drop_index(op.f('ix_preview_contents_url_hash'), table_name='preview_contents')
    op.drop_index(op.f('ix_preview_contents_url'), table_name='preview_contents')
    op.drop_table('preview_contents')
```

## API Documentation

### OpenAPI/Swagger Updates

Update the following files:
- `src/main.py` - Add router for previews
- FastAPI will auto-generate OpenAPI docs at `/docs`

### Redoc Updates

Redoc will automatically reflect the new endpoints.

## Testing Strategy

### TDD Development Order

```
Phase 1: Backend API (pytest)
├── PreviewContent model tests
│   └── tests/models/test_preview_content.py
├── PreviewService service tests
│   └── tests/services/test_preview_service.py
└── API endpoint tests
    └── tests/api/test_preview_routes.py

Phase 2: Frontend Components (Vitest)
├── useArticlePreview composable tests
│   └── web/src/composables/__tests__/useArticlePreview.test.ts
├── ArticlePreviewDialog component tests
│   └── web/src/components/__tests__/ArticlePreviewDialog.test.ts
└── Integration tests
    └── web/src/pages/__tests__/preview.test.ts

Phase 3: E2E Tests (Playwright)
└── web/e2e/preview.spec.ts
```

### E2E Test Scenarios (Given/When/Then)

#### Feed Page Preview

```gherkin
Scenario: Display preview button on Feed page
  Given the user is on the Feed page
  When the page loads with feed items
  Then each feed item should display a preview button (eye icon)
  And each feed item should display an open in new tab button (external link icon)

Scenario: Successful preview from Feed page
  Given the user is on the Feed page
  And a feed item with URL "https://example.com/article" exists
  When the user clicks the preview button for that item
  Then a preview dialog should open
  And the dialog should show a loading indicator
  And after loading, the dialog should display the markdown content
  And the dialog should have source/preview toggle buttons

Scenario: Preview with cached content
  Given the user is on the Feed page
  And a preview for URL "https://example.com/article" already exists in cache
  When the user clicks the preview button for that item
  Then the preview dialog should open
  And the markdown content should display immediately (no loading indicator)
```

#### History Page Preview

```gherkin
Scenario: Display preview button in History expanded items
  Given the user is on the History page
  When the user expands a batch to show its items
  Then each history item should display a preview button (eye icon)
  And each history item should display an open in new tab button

Scenario: Successful preview from History page
  Given the user is on the History page
  And the user has expanded a batch
  When the user clicks the preview button for a history item
  Then a preview dialog should open with the article content
```

#### Error Handling

```gherkin
Scenario: Handle rate limit error
  Given the user clicks preview for an uncached URL
  When the markdown.new API returns a 429 rate limit error
  Then the dialog should display "Preview service temporarily unavailable, please try again later"
  And an "Open Original Page" button should be displayed
  And clicking "Open Original Page" should open the original URL in a new tab

Scenario: Handle network timeout
  Given the user clicks preview for an uncached URL
  When the markdown.new API request times out (30 seconds)
  Then the dialog should display "Preview request timed out, please try again"

Scenario: Handle network error
  Given the user clicks preview for an uncached URL
  When the network request fails (no internet)
  Then the dialog should display "Network error, please check your connection"

Scenario: Handle server error
  Given the user clicks preview for an uncached URL
  When the markdown.new API returns a 500 error
  Then the dialog should display "Preview service error, please try again later"
```

#### Source/Preview Toggle

```gherkin
Scenario: Toggle between source and preview
  Given a preview dialog is open with markdown content
  When the user clicks the "Source" button
  Then the raw markdown source should be displayed with syntax highlighting
  When the user clicks the "Preview" button
  Then the rendered markdown preview should be displayed
```

#### Open in New Tab

```gherkin
Scenario: Open article in new tab
  Given the user is on the Feed page
  When the user clicks the "Open in New Tab" button for a feed item
  Then a new browser tab should open
  And the new tab should navigate to the article's original URL
```

### Coverage Targets

| Layer | Target Coverage |
|------|-----------------|
| Backend Model | 100% |
| Backend Service | 90%+ |
| Backend API | 90%+ |
| Frontend Component | 80%+ |
| E2E | 100% critical flows |

### Test File Locations

```
tests/
├── models/
│   └── test_preview_content.py      # NEW
├── services/
│   └── test_preview_service.py      # NEW
└── api/
    └── test_preview_routes.py       # NEW

web/src/
├── composables/
│   └── __tests__/
│       └── useArticlePreview.test.ts  # NEW
├── components/
│   └── __tests__/
│       └── ArticlePreviewDialog.test.ts  # NEW
└── pages/
    └── __tests__/
        └── preview.test.ts          # NEW

web/e2e/
└── preview.spec.ts                  # NEW
```

### Detailed Test Cases

#### URL Normalization Tests

```typescript
// web/src/utils/__tests__/urlNormalizer.test.ts
describe('normalizeUrl', () => {
  it('should lowercase domain', () => {
    expect(normalizeUrl('https://Example.COM/article'))
      .toBe('https://example.com/article');
  });

  it('should sort query parameters alphabetically', () => {
    expect(normalizeUrl('https://example.com?b=2&a=1'))
      .toBe('https://example.com?a=1&b=2');
  });

  it('should remove fragment', () => {
    expect(normalizeUrl('https://example.com#section'))
      .toBe('https://example.com');
  });

  it('should remove trailing slash except root', () => {
    expect(normalizeUrl('https://example.com/path/'))
      .toBe('https://example.com/path');
    expect(normalizeUrl('https://example.com/'))
      .toBe('https://example.com/');
  });

  it('should throw error for invalid URL', () => {
    expect(() => normalizeUrl('not-a-url')).toThrow('Invalid URL');
  });
});

describe('computeUrlHash', () => {
  it('should return consistent SHA-256 hash', () => {
    const url = 'https://example.com/article';
    const hash1 = await computeUrlHash(url);
    const hash2 = await computeUrlHash(url);
    expect(hash1).toBe(hash2);
    expect(hash1).toHaveLength(64); // SHA-256 hex length
  });

  it('should return same hash for normalized-equivalent URLs', () => {
    const hash1 = await computeUrlHash('https://Example.COM/path?b=2&a=1');
    const hash2 = await computeUrlHash('https://example.com/path?a=1&b=2');
    expect(hash1).toBe(hash2);
  });
});
```

#### Upsert Race Condition Tests

```python
# tests/services/test_preview_service.py
class TestPreviewServiceUpsert:
    @pytest.mark.asyncio
    async def test_upsert_creates_new_record(self, session):
        """Should create new record when URL not in database."""
        service = PreviewService(session)
        
        result = await service.upsert(
            url="https://example.com/article",
            markdown_content="# Test",
            title="Test Article"
        )
        
        assert result.id is not None
        assert result.url == "https://example.com/article"
    
    @pytest.mark.asyncio
    async def test_upsert_updates_existing_record(self, session):
        """Should update existing record when URL already exists."""
        service = PreviewService(session)
        
        # Create initial record
        first = await service.upsert(
            url="https://example.com/article",
            markdown_content="# Original",
            title="Original Title"
        )
        
        # Update with same URL
        second = await service.upsert(
            url="https://example.com/article",
            markdown_content="# Updated",
            title="Updated Title"
        )
        
        assert second.id == first.id
        assert second.markdown_content == "# Updated"
        assert second.title == "Updated Title"
    
    @pytest.mark.asyncio
    async def test_upsert_handles_concurrent_requests(self, session):
        """Should handle concurrent upsert requests without error."""
        service = PreviewService(session)
        url = "https://example.com/concurrent"
        
        # Simulate concurrent requests
        results = await asyncio.gather(
            service.upsert(url, "# Content 1", "Title 1"),
            service.upsert(url, "# Content 2", "Title 2"),
        )
        
        # Both should succeed, return same record
        assert results[0].id == results[1].id
```

#### Content Truncation Tests

```typescript
// web/src/utils/__tests__/contentValidator.test.ts
describe('validateMarkdownContent', () => {
  const MAX_SIZE = 10 * 1024 * 1024; // 10 MB

  it('should return valid for content under limit', () => {
    const content = 'a'.repeat(1024);
    const result = validateMarkdownContent(content);
    expect(result.valid).toBe(true);
  });

  it('should truncate content exceeding limit', () => {
    const content = 'a'.repeat(MAX_SIZE + 1000);
    const result = validateMarkdownContent(content);
    expect(result.valid).toBe(false);
    expect(result.truncated?.length).toBe(MAX_SIZE);
  });
});
```

#### Timeout Warning Tests

```typescript
// web/src/composables/__tests__/useArticlePreview.test.ts
describe('useArticlePreview - timeout handling', () => {
  it('should show warning after 20 seconds', async () => {
    vi.useFakeTimers();
    
    const { showTimeoutWarning, fetchPreview } = useArticlePreview();
    const promise = fetchPreview('https://example.com/slow');
    
    // Advance 20 seconds
    await vi.advanceTimersByTimeAsync(20000);
    
    expect(showTimeoutWarning.value).toBe(true);
    
    vi.useRealTimers();
  });

  it('should abort request after 30 seconds', async () => {
    vi.useFakeTimers();
    
    const { error, fetchPreview } = useArticlePreview();
    const promise = fetchPreview('https://example.com/slow');
    
    // Advance 30 seconds
    await vi.advanceTimersByTimeAsync(30000);
    
    await expect(promise).rejects.toThrow('timed out');
    
    vi.useRealTimers();
  });
});
```

#### Error Recovery Tests

```typescript
// web/src/composables/__tests__/useArticlePreview.test.ts
describe('useArticlePreview - error recovery', () => {
  it('should not retry on rate limit error', async () => {
    mockFetch.mockRejectedValueOnce(
      new PreviewError('Rate limited', 'rate_limit')
    );
    
    const { error, fetchPreview } = useArticlePreview();
    await expect(fetchPreview('https://example.com')).rejects.toThrow();
    
    // Should not retry
    expect(mockFetch).toHaveBeenCalledTimes(1);
  });

  it('should retry on network error with exponential backoff', async () => {
    mockFetch
      .mockRejectedValueOnce(new TypeError('Network error'))
      .mockResolvedValueOnce({ ok: true, text: () => '# Content' });
    
    const { content, fetchPreview } = useArticlePreview();
    await fetchPreview('https://example.com', { retries: 1 });
    
    expect(mockFetch).toHaveBeenCalledTimes(2);
  });
});
```

## Performance Considerations

### API Timeouts

| Operation | Timeout | Handling |
|-----------|---------|----------|
| markdown.new API | 30 seconds | Show timeout error, allow retry |
| Backend cache check | 5 seconds | Proceed to markdown.new on timeout |
| Backend cache save | 10 seconds | Log error, preview still works |

### Loading State UX

1. **Initial Load**: Show skeleton/spinner in dialog
2. **API Call**: Show loading indicator with percentage if possible
3. **Timeout Warning**: At 20 seconds, show "Taking longer than usual..."

### Frontend API Client

**File**: `web/src/api/markdownNewApi.ts`

```typescript
// Separate API client for markdown.new (not using main axios instance)
const MARKDOWN_NEW_TIMEOUT = 30000;

export async function fetchMarkdownContent(url: string): Promise<string> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), MARKDOWN_NEW_TIMEOUT);
  
  try {
    const response = await fetch('https://markdown.new/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url, retain_images: true }),
      signal: controller.signal
    });
    
    clearTimeout(timeoutId);
    
    if (!response.ok) {
      throw new MarkdownNewError(response.status, response.statusText);
    }
    
    return await response.text();
  } catch (error) {
    clearTimeout(timeoutId);
    throw error;
  }
}
```

**Note**: Use native `fetch` API instead of axios to:
- Avoid CORS issues with external service
- Keep markdown.new calls separate from main API client
- Have independent timeout configuration

## Cache Strategy

### Current Design

- **Storage**: SQLite database via PreviewContent model
- **Key**: SHA-256 hash of normalized URL
- **TTL**: None (permanent cache)
- **Invalidation**: Manual only (database operations)

### Cache Behavior

| Scenario | Action |
|---------|--------|
| First request for URL | Fetch from markdown.new, save to cache |
| Subsequent requests | Return cached content |
| Content update needed | Manual database update or delete |

### Notes

- Content changes on original URLs won't be reflected automatically
- Users needing fresh content can use "Open in New Tab" to view the original
- If invalidation becomes needed, see Future Considerations below

### Future Considerations

If cache invalidation becomes necessary:

1. **Add TTL**: `expires_at` column in `preview_contents` table
2. **Refresh Button**: In preview dialog to force re-fetch
3. **Admin Endpoint**: To clear cache by URL pattern or date range
4. **Content Hash**: Store hash of markdown content to detect changes

## Internationalization

### New i18n Keys

Add to `web/src/locales/en.json` and `web/src/locales/zh.json`:

```json
{
  "preview": {
    "title": "Preview",
    "quick_preview": "Quick Preview",
    "open_new_tab": "Open in New Tab",
    "loading": "Loading preview...",
    "rate_limit": "Preview service temporarily unavailable, please try again later",
    "network_error": "Network error, please check your connection",
    "conversion_failed": "Unable to preview this page",
    "requires_login": "This page requires login",
    "open_original": "Open Original Page"
  }
}
```

## Accessibility Specifications

### WCAG 2.1 Compliance Requirements

| Requirement | Implementation |
|-------------|----------------|
| Keyboard Navigation | Tab to focus buttons, Enter/Space to activate |
| Focus Management | Focus trap in dialog, return focus on close |
| ARIA Labels | All buttons have aria-label |
| Screen Reader | Announce loading/error states |
| Color Contrast | Minimum 4.5:1 ratio for text |

### Button Accessibility

```vue
<template>
  <!-- Preview button -->
  <button
    @click="openPreview(item)"
    class="btn-icon"
    :aria-label="t('preview.quick_preview')"
    :title="t('preview.quick_preview')"
    type="button"
  >
    <Eye class="w-4 h-4" aria-hidden="true" />
  </button>
  
  <!-- Open in new tab button -->
  <button
    @click="openInNewTab(item.link)"
    class="btn-icon"
    :aria-label="t('preview.open_new_tab')"
    :title="t('preview.open_new_tab')"
    type="button"
  >
    <ExternalLink class="w-4 h-4" aria-hidden="true" />
  </button>
</template>
```

### Dialog Accessibility

```vue
<template>
  <DialogRoot v-model:open="open">
    <DialogPortal>
      <DialogOverlay 
        class="dialog-overlay"
        @click="close"
      />
      <DialogContent 
        class="dialog-content"
        :aria-labelledby="titleId"
        @escape-key-down="close"
      >
        <DialogTitle :id="titleId">
          {{ t('preview.title') }}
        </DialogTitle>
        
        <!-- Source/Preview toggle -->
        <div role="tablist" :aria-label="t('preview.view_mode')">
          <button
            role="tab"
            :aria-selected="mode === 'preview'"
            @click="mode = 'preview'"
          >
            {{ t('preview.preview_mode') }}
          </button>
          <button
            role="tab"
            :aria-selected="mode === 'source'"
            @click="mode = 'source'"
          >
            {{ t('preview.source_mode') }}
          </button>
        </div>
        
        <!-- Content area -->
        <div 
          role="tabpanel"
          :aria-busy="loading"
          aria-live="polite"
        >
          <template v-if="loading">
            <span class="sr-only">{{ t('preview.loading') }}</span>
            <SkeletonLoader />
          </template>
          <template v-else-if="error">
            <p role="alert">{{ error.message }}</p>
          </template>
          <template v-else>
            <MarkdownPreview :content="content" />
          </template>
        </div>
        
        <DialogClose @click="close">
          <X class="w-4 h-4" aria-hidden="true" />
          <span class="sr-only">{{ t('common.close') }}</span>
        </DialogClose>
      </DialogContent>
    </DialogPortal>
  </DialogRoot>
</template>
```

### Focus Management

```typescript
// Focus trap and return focus on close
const previousActiveElement = ref<HTMLElement | null>(null);

watch(() => props.open, (isOpen) => {
  if (isOpen) {
    // Store previous focus
    previousActiveElement.value = document.activeElement as HTMLElement;
    // Focus first interactive element in dialog
    nextTick(() => {
      const firstButton = dialogRef.value?.querySelector('button');
      firstButton?.focus();
    });
  } else {
    // Return focus
    previousActiveElement.value?.focus();
  }
});
```

## Mobile and Responsive Specifications

### Responsive Breakpoints

| Breakpoint | Dialog Behavior | Toggle Layout |
|------------|-----------------|---------------|
| Mobile (<640px) | Full-screen | Stacked vertically |
| Tablet (640-1024px) | 90% width | Horizontal tabs |
| Desktop (>1024px) | max-w-4xl | Horizontal tabs |

### Mobile Dialog Layout

```
Mobile (<640px) - Full Screen:
┌─────────────────────┐
│ Preview        [X]  │
├─────────────────────┤
│ [Source]            │
│ [Preview]           │
├─────────────────────┤
│                     │
│ # Article Title    │
│                     │
│ Content...         │
│                     │
└─────────────────────┘
```

### Touch Interactions

| Interaction | Implementation |
|-------------|----------------|
| Tap preview button | Open dialog |
| Swipe down on dialog | Close dialog (optional) |
| Pinch to zoom | Enable on markdown preview |
| Long press | Show tooltip |

### Responsive Component Implementation

```vue
<template>
  <DialogContent 
    :class="[
      'dialog-content',
      isMobile ? 'dialog-fullscreen' : 'dialog-centered'
    ]"
  >
    <!-- Source/Preview toggle - responsive layout -->
    <div 
      :class="[
        'toggle-container',
        isMobile ? 'flex-col' : 'flex-row'
      ]"
    >
      <button 
        v-for="tab in tabs" 
        :key="tab.value"
        :class="['toggle-btn', { active: mode === tab.value }]"
        @click="mode = tab.value"
      >
        {{ tab.label }}
      </button>
    </div>
    
    <!-- Content -->
    <div class="content-container overflow-auto">
      <MarkdownPreview 
        :content="content"
        :class="{ 'text-sm': isMobile }"
      />
    </div>
  </DialogContent>
</template>

<script setup>
import { useMediaQuery } from '@vueuse/core';

const isMobile = useMediaQuery('(max-width: 640px)');
</script>
```

### Minimum Supported Screen Size

- **Minimum width**: 320px
- **Minimum height**: 480px
- **Font scaling**: Support system font scaling up to 200%

## Database Maintenance Strategy

### Expected Growth

| Metric | Estimate |
|--------|----------|
| Average preview size | 50 KB |
| Previews per day | 100 (cached) |
| Daily growth | ~5 MB |
| Monthly growth | ~150 MB |
| Yearly growth | ~1.8 GB |

### Cleanup Strategy (Future Implementation)

```python
# Future: Add cleanup job for old previews
async def cleanup_old_previews(session: AsyncSession, days_old: int = 90) -> int:
    """
    Remove previews older than specified days.
    
    Args:
        session: Database session
        days_old: Age threshold in days
        
    Returns:
        Number of deleted records
    """
    cutoff = datetime.utcnow() - timedelta(days=days_old)
    
    result = await session.execute(
        delete(PreviewContent)
        .where(PreviewContent.updated_at < cutoff)
    )
    await session.commit()
    
    return result.rowcount
```

### Soft Delete Behavior

The `deleted_at` column in the migration supports soft delete pattern:

```python
# Soft delete instead of hard delete
async def soft_delete_preview(session: AsyncSession, url_hash: str) -> bool:
    result = await session.execute(
        update(PreviewContent)
        .where(PreviewContent.url_hash == url_hash)
        .values(deleted_at=datetime.utcnow())
    )
    await session.commit()
    return result.rowcount > 0

# Query should filter out soft-deleted records
async def get_active_preview(session: AsyncSession, url_hash: str) -> PreviewContent | None:
    result = await session.execute(
        select(PreviewContent)
        .where(
            PreviewContent.url_hash == url_hash,
            PreviewContent.deleted_at.is_(None)
        )
    )
    return result.scalar_one_or_none()
```

### Database Monitoring Queries

```sql
-- Check preview_contents table size
SELECT 
    COUNT(*) as total_records,
    SUM(LENGTH(markdown_content)) as total_content_bytes,
    AVG(LENGTH(markdown_content)) as avg_content_bytes
FROM preview_contents;

-- Find large previews (>1MB)
SELECT url, LENGTH(markdown_content) as size_bytes
FROM preview_contents
WHERE LENGTH(markdown_content) > 1048576
ORDER BY size_bytes DESC
LIMIT 10;

-- Find old previews not accessed recently
SELECT url, updated_at
FROM preview_contents
WHERE updated_at < datetime('now', '-90 days')
ORDER BY updated_at ASC;
```

## Security Considerations

1. **URL Validation**: Validate URLs before calling markdown.new
2. **Content Sanitization**: Use DOMPurify for displaying markdown content (already in place)
3. **Rate Limiting**: Respect markdown.new rate limits (500/day/IP)
4. **Input Validation**: Validate all inputs on backend API

## Versioning

- **Current Version**: v0.8.0
- **Target Version**: v0.9.0
- Follow semantic versioning (MAJOR.MINOR.PATCH)

## Implementation Checklist

- [ ] Create PreviewContent model
- [ ] Create database migration
- [ ] Create PreviewService
- [ ] Create API endpoints
- [ ] Update OpenAPI/Swagger
- [ ] Create useArticlePreview composable
- [ ] Create ArticlePreviewDialog component
- [ ] Update FeedPage.vue
- [ ] Update HistoryPage.vue
- [ ] Add i18n keys
- [ ] Write backend unit tests
- [ ] Write frontend unit tests
- [ ] Write E2E tests
- [ ] Update CHANGELOG.md
- [ ] Update README.md

## References

- [markdown.new API Documentation](https://markdown.new/)
- Existing Components: `RssPreviewDialog.vue`, `MarkdownPreview.vue`
- Existing Patterns: `useFeedCache.ts`