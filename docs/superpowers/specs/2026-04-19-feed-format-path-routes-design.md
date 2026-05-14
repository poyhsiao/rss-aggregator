# Feed Format Path-Based Routes Design

**Date:** 2026-04-19
**Status:** Approved
**Author:** Kim Hsiao

## Overview

Add path-based format selection to feed API endpoints, replacing query-parameter format selection with clean RESTful paths. Display the generated API paths in all preview feed dialogs so external systems can directly consume RSS/JSON/Markdown content via predictable URLs.

## Requirements

1. New path-based endpoints for feed format selection (`/feed/{format}`, `/sources/{id}/{format}`, `/groups/{id}/{format}`)
2. Preview feed dialogs must display copyable API paths for RSS, JSON, and Markdown
3. All development follows TDD (Red → Green → Improve)
4. API endpoints require E2E tests; other code requires unit tests
5. All UI strings use i18n keys — no hardcoded text
6. Existing endpoints (`/feed`, `/sources/{id}/feed`) remain unchanged

## API Design

### New Endpoints

| Endpoint | Purpose | Example |
|----------|---------|---------|
| `GET /feed/{format}` | Global feed by format | `/feed/rss`, `/feed/json`, `/feed/markdown` |
| `GET /sources/{source_id}/{format}` | Source feed by format | `/sources/3/json` |
| `GET /groups/{group_id}/{format}` | Group feed by format | `/groups/2/markdown` |

### Path Parameters

- `format` — Required, values: `rss`, `json`, `markdown`
- FastAPI validation: `Path(..., pattern="^(rss|json|markdown)$")`
- Invalid format returns HTTP 422

### Query Parameters (unchanged from existing)

**Global feed** (`/feed/{format}`): `sort_by`, `sort_order`, `valid_time`, `keywords`, `group_id`, `source_id`

**Source feed** (`/sources/{source_id}/{format}`): `sort_by`, `sort_order`, `valid_time`, `keywords`

**Group feed** (`/groups/{group_id}/{format}`): `sort_by`, `sort_order`, `valid_time`, `keywords`

### Existing Endpoints (unchanged)

- `GET /feed` — keeps `format` query parameter, defaults to `rss`
- `GET /sources/{source_id}/feed` — keeps `format` query parameter, defaults to `rss`

### Authentication

Same as existing: `X-API-Key` header or `api_key` query parameter. Enforced when `REQUIRE_API_KEY=true`.

### Service Layer

New route handlers call existing `feed_service.get_formatted_feed()`. Zero business logic duplication.

### Stdio Router

Add three parallel handlers mirroring the FastAPI routes:

- `_handle_get_feed_format()` — `GET /api/v1/feed/{format}`
- `_handle_get_source_feed_format()` — `GET /api/v1/sources/{source_id}/{format}`
- `_handle_get_group_feed_format()` — `GET /api/v1/groups/{group_id}/{format}`

## Frontend Design

### RssPreviewDialog Changes

Add an API paths display section above the format selector (RSS / JSON / Markdown segmented buttons).

**Layout:**

```
┌─────────────────────────────────────────┐
│ API Paths                               │
│ RSS   /api/v1/feed/rss?source_id=1  [📋]│
│ JSON  /api/v1/feed/json?source_id=1 [📋]│
│ MD    /api/v1/feed/markdown?source_id=1[📋]│
├─────────────────────────────────────────┤
│ [RSS] [JSON] [Markdown]  ← format tabs  │
│ ... content preview ...                  │
└─────────────────────────────────────────┘
```

**Each path row contains:**

- Format label (RSS / JSON / Markdown)
- Full API path (path-based format, with non-default query parameters only)
- Copy button (copies full URL including host to clipboard)

**Path generation logic:**

- Global: `/api/v1/feed/{format}?sort_by=...`
- Source: `/api/v1/sources/{source_id}/{format}?sort_by=...`
- Group: `/api/v1/groups/{group_id}/{format}?sort_by=...`
- Only include query parameters with non-default values (avoid verbose URLs)
- Full URL includes host (e.g., `http://localhost:8000/api/v1/feed/rss`)

**Environment handling:**

- Web: base URL from `window.__VITE_API_BASE_URL__` or `/api/v1`
- Tauri (desktop): display `http://localhost:{port}/api/v1/...` (actual accessible URL, not `app://localhost`)

### New Utility Function

`buildFeedPathUrl(params)` in `web/src/api/feed.ts`:

- Generates path-based feed URLs
- Takes `FeedParams` + `format` as input
- Returns full URL string
- Filters out default-valued query parameters
- Handles Tauri vs Web base URL

### i18n Keys

New keys in both `en.json` and `zh.json`:

| Key | English | 中文 |
|-----|---------|------|
| `feed.api_paths` | API Paths | API 路徑 |
| `feed.copy_path` | Copy path | 複製路徑 |
| `feed.path_copied` | Path copied | 路徑已複製 |

## Testing Strategy

### Backend Unit Tests (pytest)

| Test File | Coverage |
|-----------|----------|
| `test_feed_route.py` | `/feed/{format}` — correct format output, invalid format → 422, query params filter correctly, auth check |
| `test_source_feed_route.py` | `/sources/{id}/{format}` — correct output, invalid source_id → 404, invalid format → 422 |
| `test_group_feed_route.py` | `/groups/{id}/{format}` — correct output, invalid group_id → 404, invalid format → 422 |
| `test_stdio_router.py` | Three new stdio handlers — correct routing, parameter parsing, error handling |

### Backend E2E Tests (Playwright)

| Test File | Coverage |
|-----------|----------|
| `feed-format-routes.spec.ts` | Verify `/feed/rss`, `/feed/json`, `/feed/markdown` return correct content-type and content; verify `/sources/{id}/{format}` and `/groups/{id}/{format}`; invalid format → 404 |

### Frontend Unit Tests (Vitest)

| Test File | Coverage |
|-----------|----------|
| `feed-api.test.ts` | `buildFeedPathUrl()` — correct URL generation, non-default query params only, Tauri vs Web base URL |
| `RssPreviewDialog.test.ts` | API paths section exists, three format paths displayed correctly, copy button functionality |

### Frontend E2E Tests (Playwright)

| Test File | Coverage |
|-----------|----------|
| `preview-api-paths.spec.ts` | Open preview dialog → paths visible, switch format → paths update, copy button → clipboard content correct |

### TDD Workflow

Every feature follows Red → Green → Improve:

1. Write test first, confirm it fails
2. Write minimal implementation, confirm test passes
3. Refactor, confirm tests still pass
4. Verify coverage >= 80%

## Implementation Notes

- New route handlers are thin — they extract `format` from the path and delegate to `feed_service.get_formatted_feed()`
- The `group_id` query parameter on `/feed/{format}` remains for backward compatibility, but the new `/groups/{group_id}/{format}` endpoint is the preferred path
- The RssPreviewDialog API paths section uses the same styling patterns as existing dialog components (radix-vue + Tailwind)
- Copy-to-clipboard uses the existing pattern from the Keys page (if any) or `navigator.clipboard.writeText()`
