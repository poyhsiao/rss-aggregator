# Code Review Fixes Design

**Date**: 2026-03-21
**Author**: Code Review Agent
**Status**: Approved

## Overview

修复代码审查发现的 14 个问题，分 3 个批次提交。

## Issues Summary

| 批次 | 名称 | 问题数 | 优先级 |
|------|------|--------|--------|
| 1 | 安全修复 | 2 | 高 |
| 2 | 中优先级修复 | 5 | 中 |
| 3 | 低优先级修复 | 7 | 低 |

## Batch 1: Security Fixes

### Issue 1: CORS Configuration Open to All Origins

**Severity**: High
**Files**: `src/config.py`, `src/main.py`

**Current Problem**:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    ...
)
```

**Solution**: Add environment variable to control allowed origins

```python
# config.py - add new setting
allowed_origins: str = ""  # Comma-separated list of allowed origins

# main.py - use environment variable
origins = settings.allowed_origins.split(",") if settings.allowed_origins else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)
```

### Issue 2: v-html XSS Risk

**Severity**: High
**Files**: `web/package.json`, `web/src/components/RssPreviewDialog.vue`

**Current Problem**: Using `v-html` without sanitization on lines 624, 632, 638

**Solution**: Add DOMPurify for HTML sanitization

```typescript
// Install dependency
// pnpm add dompurify
// pnpm add -D @types/dompurify

// In component
import DOMPurify from 'dompurify'

// Before rendering
const sanitizedContent = computed(() => 
  DOMPurify.sanitize(formattedContent.value)
)
```

## Batch 2: Medium Priority Fixes

### Issue 3: API Key Stored in localStorage

**Severity**: Medium
**Files**: `web/src/stores/auth.ts`

**Solution**: Use sessionStorage instead of localStorage for shorter session lifetime

```typescript
// Simple replacement
sessionStorage.setItem(STORAGE_KEY, key)
const stored = sessionStorage.getItem(STORAGE_KEY)
sessionStorage.removeItem(STORAGE_KEY)
```

### Issue 4: Debug Mode Enabled by Default

**Severity**: Medium
**Files**: `src/config.py`

**Solution**: Change default to False

```python
app_debug: bool = False
```

### Issue 5: Docker Container Running as Root

**Severity**: Medium
**Files**: `Dockerfile`

**Solution**: Add non-root user

```dockerfile
RUN adduser --disabled-password --gecos '' appuser && \
    chown -R appuser:appuser /app
USER appuser
```

### Issue 6: Broad Exception Handling

**Severity**: Medium
**Files**: `src/services/fetch_service.py`, `src/db/database.py`

**Solution**: Catch specific exception types

```python
# fetch_service.py
except (httpx.HTTPError, httpx.TimeoutException) as e:
    # Handle HTTP errors
except ValueError as e:
    # Handle parsing errors

# database.py - keep as is (needs to catch all for rollback)
# Add comment explaining intent
except Exception:
    await session.rollback()
    raise  # Re-raise, don't swallow
```

### Issue 7: feedparser Type Issues

**Severity**: Medium
**Files**: `src/services/fetch_service.py`

**Solution**: Add type guards

```python
# Parse link with type check
raw_link = entry.get("link", "")
if isinstance(raw_link, str):
    item["link"] = self._clean_google_url(raw_link)
else:
    item["link"] = ""

# Parse date with try/except
if hasattr(entry, "published_parsed") and entry.published_parsed:
    try:
        item["published_at"] = datetime(*entry.published_parsed[:6])
    except (TypeError, ValueError, IndexError):
        item["published_at"] = None
```

## Batch 3: Low Priority Fixes

### Issue 8: Console Statements in Production

**Severity**: Low
**Files**: `web/src/components/RssPreviewDialog.vue`, `web/src/main.ts`

**Solution**: 
- Remove console.error from RssPreviewDialog.vue (use toast or silent handling)
- Keep service worker error catch in main.ts (this is appropriate)

### Issue 9: TypeScript any Type

**Severity**: Low
**Files**: `web/src/components/KeyDialog.vue`

**Solution**: Use proper type narrowing

```typescript
} catch (error: unknown) {
  if (error instanceof Error) {
    toast.error(error.message)
  } else {
    toast.error(t('common.error'))
  }
}
```

### Issue 10: Large Component - RssPreviewDialog.vue

**Severity**: Low
**Files**: Multiple new files + `web/src/components/RssPreviewDialog.vue`

**Solution**: Split into smaller components

**New Files**:
| File | Lines | Responsibility |
|------|-------|----------------|
| `web/src/components/feed-preview/JsonPreview.vue` | ~150 | JSON formatting, syntax highlighting |
| `web/src/components/feed-preview/MarkdownPreview.vue` | ~100 | Markdown rendering, sanitization |
| `web/src/components/feed-preview/RssXmlPreview.vue` | ~80 | XML display, copy functionality |
| `web/src/composables/useFeedCache.ts` | ~50 | Data caching logic |

**Refactored RssPreviewDialog.vue**: ~200 lines (container, state management, API calls)

### Issue 11: Empty 404 Handler

**Severity**: Low
**Files**: `src/main.py`

**Solution**: Return JSON error response

```python
from fastapi.responses import JSONResponse

@app.exception_handler(404)
async def not_found_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=404,
        content={"detail": "Not Found", "path": request.url.path}
    )
```

### Issue 12: source_id Parameter Mismatch

**Severity**: Low
**Files**: `src/api/routes/feed.py` or `src/services/feed_service.py`

**Solution**: Investigate and fix the mismatch between API route call and service method signature

### Issue 13: Circular Model Imports

**Severity**: Low
**Files**: `src/models/source.py`, `src/models/feed_item.py`

**Solution**: Add future annotations

```python
# Add at top of both files
from __future__ import annotations
```

### Issue 14: Tailwind CSS LSP Warnings

**Severity**: Low
**Files**: N/A (tooling issue)

**Solution**: Document in project README or add `.vscode/settings.json`:

```json
{
  "css.validate": false,
  "tailwindCSS.validate": true
}
```

## Implementation Order

1. **Batch 1 (Security)** - Commit immediately after testing
2. **Batch 2 (Medium)** - Commit after batch 1 is merged
3. **Batch 3 (Low)** - Commit after batch 2 is merged

## Testing Requirements

- **Batch 1**: Test CORS with specific origins, test XSS sanitization
- **Batch 2**: Test API key storage, Docker container, error handling
- **Batch 3**: Test component rendering, API responses, type safety

## Rollback Plan

Each batch is a separate PR, allowing independent rollback if issues arise.