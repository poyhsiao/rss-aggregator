# Feed Format Refactor Design

**Date:** 2026-03-20
**Author:** Kimhsiao
**Status:** Draft

## Overview

Refactor the API system to unify format transformation logic and improve the frontend code display component.

## Goals

1. Create a common formatter module for RSS/JSON/Markdown output
2. Support `/api/v1/feed` and `/api/v1/sources/:id/feed` with unified format parameter
3. Change default output format from JSON to RSS
4. Improve frontend UI: simplified borders, repositioned buttons

## API Design

### `/api/v1/feed` Endpoint

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `format` | string | `rss` | Output format: `rss` / `json` / `markdown` |
| `sort_by` | string | `published_at` | Sort field (`published_at` or `source`) |
| `sort_order` | string | `desc` | Sort direction (`asc` or `desc`) |
| `valid_time` | int | - | Time range in hours |
| `keywords` | string | - | Keywords filter (semicolon-separated) |
| `source_id` | int | - | Filter by source ID |

### `/api/v1/sources/:id/feed` Endpoint (NEW)

Same parameters as `/feed`, but automatically filters by the specified source ID.

### Response Formats

| Format | Content-Type | Description |
|--------|--------------|-------------|
| `rss` | `application/xml` | RSS 2.0 XML |
| `json` | `application/json` | FeedItem array |
| `markdown` | `text/markdown` | Extended format with ID, source URL, etc. |

### Error Handling (Lenient Mode)

- Invalid `format` value → Automatically fallback to RSS
- No data → Return empty content in valid format (empty RSS channel / empty JSON array / Markdown with "no data" message)

## Backend Architecture

### Module Structure

```
src/
├── formatters/
│   ├── __init__.py      # Factory function
│   ├── base.py          # BaseFormatter abstract class
│   ├── rss_formatter.py # RSS 2.0 formatter
│   ├── json_formatter.py# JSON formatter
│   └── md_formatter.py  # Markdown formatter (extended)
├── services/
│   └── feed_service.py  # Refactored to use Formatter module
├── api/routes/
│   ├── feed.py          # Updated: `output` → `format`
│   └── sources.py       # New: `/sources/:id/feed` endpoint
```

### Class Design

```python
# src/formatters/base.py
class BaseFormatter(ABC):
    @abstractmethod
    def format(self, items: List[FeedItem]) -> str: pass
    
    @abstractmethod
    def get_content_type(self) -> str: pass

# src/formatters/__init__.py
def get_formatter(format: str) -> BaseFormatter:
    """Factory function with fallback to RSS"""
    ...
```

## Frontend Changes

### Button Layout

```
Before:                          After:
┌──────────────────────┐        ┌──────────────────────┐
│ Header    [Copy]     │        │ Header              │
├──────────────────────┤   →    ├──────────────────────┤
│                      │        │                      │
│   Code Preview       │        │   Code Preview       │
│                      │        │   (no border)        │
├──────────────────────┤        ├──────────────────────┤
│            [Download]│        │        [Copy] [Download]│
└──────────────────────┘        └──────────────────────┘
```

### Style Simplification

```css
/* Before */
border border-slate-700 dark:border-slate-800 rounded-lg p-4

/* After */
bg-slate-900 dark:bg-slate-950 rounded-lg p-4
```

### API Function

```typescript
// web/src/api/feed.ts
export async function getFormattedFeed(
  format: 'rss' | 'json' | 'markdown',
  params?: FeedParams
): Promise<{ content: string; contentType: string }>
```

## Implementation Tasks

### Backend

| # | Task | File |
|---|------|------|
| B1 | Create `formatters/` module structure | `src/formatters/__init__.py` |
| B2 | Implement `BaseFormatter` abstract class | `src/formatters/base.py` |
| B3 | Implement `RssFormatter` (migrate existing logic) | `src/formatters/rss_formatter.py` |
| B4 | Implement `JsonFormatter` | `src/formatters/json_formatter.py` |
| B5 | Implement `MarkdownFormatter` (extended version) | `src/formatters/md_formatter.py` |
| B6 | Refactor `FeedService` to use Formatter module | `src/services/feed_service.py` |
| B7 | Update `/feed` endpoint parameter (`output` → `format`) | `src/api/routes/feed.py` |
| B8 | Add `/sources/:id/feed` endpoint | `src/api/routes/sources.py` |
| B9 | Add unit tests | `tests/test_formatters.py` |

### Frontend

| # | Task | File |
|---|------|------|
| F1 | Add `getFormattedFeed()` API function | `web/src/api/feed.ts` |
| F2 | Refactor `RssPreviewDialog` to use unified API | `web/src/components/RssPreviewDialog.vue` |
| F3 | Remove frontend Markdown generation logic | `web/src/components/RssPreviewDialog.vue` |
| F4 | Update button layout (move copy to bottom) | `web/src/components/RssPreviewDialog.vue` |
| F5 | Simplify border styles | `web/src/components/RssPreviewDialog.vue` |
| F6 | Update i18n messages if needed | `web/src/locales/*.json` |

## Breaking Changes

1. **Default format changed**: JSON → RSS
2. **Parameter renamed**: `output` → `format`
3. **New endpoint**: `/api/v1/sources/:id/feed`

## Notes

- Version upgrade will be done after implementation is complete
- No commit/publish until user confirms final adjustments