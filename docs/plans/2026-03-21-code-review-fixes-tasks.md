# Code Review Fixes Tasks

**Date**: 2026-03-21
**Author**: Code Review Agent
**Status**: Ready for Implementation

## Batch 1: Security Fixes

### 1.1 CORS Configuration
- [ ] Add `allowed_origins` setting to `src/config.py`
- [ ] Update `src/main.py` to use environment variable for CORS origins
- [ ] Update `.env.example` with `ALLOWED_ORIGINS` documentation
- [ ] Test CORS with specific origin
- [ ] Run `uv run pytest` to verify no regressions

### 1.2 XSS Prevention with DOMPurify
- [ ] Install `dompurify` and `@types/dompurify` in `web/`
- [ ] Import DOMPurify in `web/src/components/RssPreviewDialog.vue`
- [ ] Create `sanitizedContent` computed property
- [ ] Replace `v-html="formattedContent"` with `v-html="sanitizedContent"`
- [ ] Create `sanitizedMarkdown` computed property
- [ ] Replace `v-html="markdownHtml"` with `v-html="sanitizedMarkdown"`
- [ ] Run `pnpm build` to verify build succeeds
- [ ] Test RSS preview functionality

---

## Batch 2: Medium Priority Fixes

### 2.1 API Key Storage
- [ ] Replace `localStorage` with `sessionStorage` in `web/src/stores/auth.ts`
- [ ] Test login/logout flow

### 2.2 Debug Mode Default
- [ ] Change `app_debug: bool = True` to `app_debug: bool = False` in `src/config.py`
- [ ] Verify no debug output in default mode

### 2.3 Docker Non-Root User
- [ ] Add non-root user creation in `Dockerfile`
- [ ] Set proper ownership on `/app/data` directory
- [ ] Add `USER appuser` directive
- [ ] Test container starts successfully
- [ ] Verify process runs as appuser

### 2.4 Exception Handling
- [ ] Update `src/services/fetch_service.py` line 53: catch specific exceptions
- [ ] Update `src/services/fetch_service.py` line 136: catch specific exceptions
- [ ] Add comment to `src/db/database.py` explaining exception handling intent
- [ ] Run `uv run pytest` to verify error handling works

### 2.5 feedparser Type Guards
- [ ] Add type guard for `entry.get("link")` in `src/services/fetch_service.py`
- [ ] Add try/except for `datetime(*entry.published_parsed[:6])`
- [ ] Add try/except for `datetime(*entry.updated_parsed[:6])`
- [ ] Run `uv run mypy src/` to verify type safety
- [ ] Run `uv run pytest` to verify functionality

---

## Batch 3: Low Priority Fixes

### 3.1 Console Statements
- [ ] Remove `console.error` from `web/src/components/RssPreviewDialog.vue` line 351
- [ ] Remove `console.error` from `web/src/components/RssPreviewDialog.vue` line 365
- [ ] Remove `console.error` from `web/src/components/RssPreviewDialog.vue` line 385
- [ ] Remove `console.error` from `web/src/components/RssPreviewDialog.vue` line 436
- [ ] Keep `console.error` in `web/src/main.ts` (service worker error handling)
- [ ] Run `pnpm build` to verify

### 3.2 TypeScript any Type
- [ ] Change `catch (error: any)` to `catch (error: unknown)` in `web/src/components/KeyDialog.vue`
- [ ] Add type narrowing for error handling
- [ ] Run `pnpm typecheck` to verify

### 3.3 RssPreviewDialog Component Split
- [ ] Create `web/src/components/feed-preview/` directory
- [ ] Create `web/src/composables/useFeedCache.ts`
- [ ] Create `web/src/components/feed-preview/JsonPreview.vue`
- [ ] Create `web/src/components/feed-preview/MarkdownPreview.vue`
- [ ] Create `web/src/components/feed-preview/RssXmlPreview.vue`
- [ ] Refactor `web/src/components/RssPreviewDialog.vue` to use new components
- [ ] Run `pnpm typecheck` to verify
- [ ] Run `pnpm build` to verify
- [ ] Test all preview modes (RSS, JSON, Markdown)

### 3.4 404 Handler
- [ ] Update `src/main.py` 404 handler to return JSON
- [ ] Import `JSONResponse` from fastapi.responses
- [ ] Test 404 response format

### 3.5 source_id Parameter Fix
- [ ] Investigate `src/api/routes/feed.py` source_id usage
- [ ] Check `src/services/feed_service.py` method signature
- [ ] Fix mismatch (either add parameter or remove call)
- [ ] Run `uv run pytest` to verify

### 3.6 Circular Model Imports
- [ ] Add `from __future__ import annotations` to `src/models/source.py`
- [ ] Add `from __future__ import annotations` to `src/models/feed_item.py`
- [ ] Run `uv run mypy src/` to verify

### 3.7 Tailwind CSS LSP (Optional)
- [ ] Create or update `.vscode/settings.json` with CSS validation settings
- [ ] Document in README if needed

---

## Verification Checklist

### After Each Batch
- [ ] All tests pass (`uv run pytest` for backend, `pnpm build` for frontend)
- [ ] No new LSP errors introduced
- [ ] Manual testing of affected functionality

### Final Verification
- [ ] Run full test suite
- [ ] Build frontend successfully
- [ ] Docker container builds and runs
- [ ] All 14 issues resolved

---

## Commit Messages

- Batch 1: `fix(security): add CORS origin control and XSS prevention`
- Batch 2: `fix: improve security and type safety`
- Batch 3: `refactor: code quality improvements and component split`