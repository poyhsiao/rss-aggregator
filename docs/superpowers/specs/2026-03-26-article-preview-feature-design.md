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

**Props**:
- `open: boolean` - Dialog visibility
- `url: string` - Article URL to preview
- `title?: string` - Article title (optional)

**Features**:
1. Check cache before fetching
2. Call markdown.new API if not cached
3. Save result to backend
4. Display MarkdownPreview with source/preview toggle
5. Handle loading and error states

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

| Scenario | HTTP Status | Frontend Handling |
|---------|------------|-------------------|
| URL cache not found | 404 | Continue to call markdown.new |
| markdown.new rate limit | 429 | Show "Preview service temporarily unavailable, please try again later" with "Open Original" button |
| markdown.new network error | - | Show "Network error, please check your connection" |
| markdown.new conversion failed | - | Show "Unable to convert this page" with "Open Original" button |
| Backend save failed | 500 | Log error, preview still displays (but not cached) |
| Page requires login/paywall | - | Show "This page requires login" with "Open Original" button |

### Error Handling Pattern

```typescript
async function fetchPreview(url: string): Promise<PreviewResult> {
  // 1. Check cache
  const cached = await getCachedPreview(url);
  if (cached) return { source: 'cache', ...cached };
  
  // 2. Call markdown.new
  try {
    const markdown = await fetchMarkdownNew(url);
    // 3. Save cache (failure doesn't affect preview)
    await savePreview(url, markdown).catch(e => console.warn('Cache save failed:', e));
    return { source: 'api', ...markdown };
  } catch (error) {
    if (error.status === 429) {
      throw new RateLimitError('Preview service temporarily unavailable');
    }
    throw new PreviewError('Unable to preview this page');
  }
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
    ├── Should display preview button on Feed page
    ├── Should display preview dialog when clicking preview button
    ├── Should display Markdown content in preview dialog
    ├── Should support source/preview toggle
    ├── Should display preview button in History page expanded items
    └── Should handle preview errors and show appropriate messages
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