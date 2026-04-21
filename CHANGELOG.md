# Changelog

All notable changes to this project will be documented in this file.

## [v0.19.2] - 2026-04-21

### Fixed

- Backend scheduler: scheduled updates now controlled **only** by feature flags (`feature_schedules`, `feature_groups`), ignoring `SCHEDULER_ENABLED` env var
  - Removed `if settings.scheduler_enabled:` guards around `schedule_scheduler.start()` / `stop()` in lifespan
  - Schedulers always start; execution gating is handled entirely inside `_check_and_execute()` via feature flags

## [v0.19.0] - 2026-04-21

### Features

- **Feature Flags System** - Toggle visibility of Groups, Schedules, and Share Links features
  - Feature gates control UI visibility for Groups, Schedules, and Share Links
  - Settings dialog triggered by 10 consecutive clicks on the site icon
  - Dual storage: localStorage (instant) + Backend API (multi-device sync)
  - New API endpoints: `GET/PUT /api/v1/feature-flags`
  - Frontend store: `useFeatureFlagsStore` with reactive feature toggles

### Fixed

- Feature Flags: store.init() no longer overwrites localStorage user preferences on every page navigation
  - localStorage now takes priority over API values on load (preserves user's toggle state)
  - API values merge on top without saving back to localStorage
  - Removed redundant saveCurrentFlags() call from init()
- Feature Flags: Hide group filter badges/chips in Feed and History pages when feature_groups is OFF

### Changed

- OpenAPI/Swagger version updated to 0.19.0

## [v0.18.2] - 2026-04-19

### Features

- New history batch feed export API: `/history/batches/{batch_id}/{format}` endpoint supports RSS, JSON, Markdown, and preview formats
- Added "preview" format output that renders feed items with markdown content
- Unified preview dialog experience across Feed, Sources, and History pages

### Fixed

- Fixed JSON formatter lazy loading issue with source_groups relationship
- Docker deployment verified and working

### Changed

- OpenAPI/Swagger version updated to 0.18.2
- RssPreviewDialog: Share links now in expandable bottom section (click to expand)
- HistoryPage now uses RssPreviewDialog component consistent with other pages

## [v0.18.1] - 2026-04-17

### Fixed

- Unified database migration: All deployment environments now automatically update database schema on startup using Alembic
- Docker: Entry point runs `alembic upgrade head` automatically
- Local Dev: Added Alembic migration to application lifespan (main.py)
- Desktop App: Now uses Alembic instead of duplicate migration logic

### Changed

- OpenAPI/Swagger version updated to 0.18.1

## [v0.18.0] - 2026-04-17

### Fixed

- FetchScheduler no longer auto-fetches every minute - only manual trigger and cron-based schedule triggering work now

### Changed

- OpenAPI/Swagger version updated to 0.18.0

## [v0.17.0] - 2026-04-10

### Fixed

- Sources are now only auto-fetched if their group has an enabled SourceGroupSchedule (was fetching all active sources unconditionally)
- ScheduleScheduler now only starts/stops when `SCHEDULER_ENABLED=true` (was starting unconditionally)

### Changed

- OpenAPI/Swagger version updated to 0.17.0

## [v0.16.0] - 2026-04-03

### Breaking Changes

- Removed `deleted_at` and `soft_delete()` from APIKey, FetchLog, Stats, FetchBatch, PreviewContent, SourceGroup, SourceGroupSchedule models — these are now hard-deleted
- `TimestampMixin` no longer includes `deleted_at` or `soft_delete()` method
- API key deletion is now permanent (was previously soft-deleted)
- `fetch_interval` field removed from Source model and API
- Scheduler is disabled by default (`scheduler_enabled: False`)

### Features

- Source Group Scheduled Updates: cron-based automatic fetching per group
- New API: `/api/v1/schedules` for schedule CRUD and toggle operations
- Schedule quick options: Every 15min, 30min, 1hr, 3hr, 6hr, 12hr, daily at 08:30
- Schedule detailed mode: Custom minutes, hours, and weekdays via MultiSelect dropdown
- Maximum 10 schedules per group with duplicate schedule detection
- Enable/disable schedule toggle with next run time display
- ScheduleConfigPanel component with modern MultiSelect UI (radix-vue Popover)
- Human-readable cron expression display using cronstrue (zh-TW and en)
- Schedule count badge displayed on group items
- FeedItem soft-delete preserved: old feed items retained for history preservation
- FetchBatch stores groups JSON for persistent group tagging in history
- History page shows all batches with correct group tags and timestamps
- Group filter in history uses batch.groups JSON for accurate filtering
- TooltipButton component for tap-friendly help tooltips (mobile-friendly)
- Mobile RWD improvements: group names wrap, action buttons always visible, 40px+ touch targets
- `mobile-web-app-capable` meta tag added for PWA support

### Fixed

- Schedule scheduler now starts regardless of `scheduler_enabled` setting
- `deleted_at` column missing in `source_group_schedules` migration
- `updated_at` column missing in `fetch_batches` model
- `deleted_at` column missing in `feed_items` migration
- History page group filter now shows all matching batches (not just latest)
- History batch items now include soft-deleted FeedItems for full history
- Weekday labels in schedule MultiSelect now update on language switch
- Duplicate JSON parsing code consolidated into `_parse_json_list` helper
- Group name overflow on mobile now wraps instead of breaking layout

### Removed

- `fetch_interval` field from Source model, API, and all UI components
- `deleted_at` and `soft_delete()` from non-Source models (APIKey, FetchLog, Stats, FetchBatch, PreviewContent, SourceGroup, SourceGroupSchedule)

## v0.14.0 - 2026-04-02

### Added

- Group-specific feed filtering: Feed page now filters by selected group via API `group_id` parameter
- History page group filtering: History batches now filter by selected group via API `group_id` parameter
- Source group refresh: Each group item has a refresh button that only updates sources in that group
- Group preview feed: Each group item has a preview button that shows only that group's feed
- Stdio router now supports all source-groups and trash API endpoints for desktop app
- Group refresh fallback: When scheduler is disabled, group refresh uses direct fetch service
- E2E tests for group-specific refresh, preview, and history filtering

### Fixed

- Feed page "Refresh" button respects selected group (only refreshes group sources)
- Feed page "Preview Feed" respects selected group (only shows group's feed)
- Source group preview now passes `group_id` to API (was showing all feeds)
- Stdio router missing `group_id` parameter in feed, history, and refresh handlers
- Stdio router silently failing group refresh when scheduler is disabled
- All emoji replaced with Lucide icons across all Vue pages and components
- Icon colors standardized: Edit=blue, Preview=purple, Refresh=green, Delete=red
- Group name editing now uses inline editing (like History page) instead of dialog
- Source page tab counts now preload on mount

### Changed

- OpenAPI/Swagger version updated to 0.14.0
- Backup service version updated to 0.14.0
- Desktop app version updated to 0.14.0

## v0.13.0 - 2026-04-02

### Fixed

- Feed page "Refresh" button translation key fixed (now uses `feed.refresh` lowercase)
- Source page tab counts now preload on mount (active/trash/groups all show correct counts)
- Group expand now uses ChevronDown/ChevronUp arrow button instead of clicking entire name row
- "Add source" dropdown option now disabled (label only, not selectable)
- Removed duplicate "Add Group" button in groups tab
- Added Refresh and Preview action buttons to each group item

### Changed

- Replaced ALL emoji with Lucide icons across all Vue pages and components
- Updated e2e test selectors to use icon-based selectors instead of emoji
- Group header action order: Refresh | Preview | Edit | Delete | Expand

## v0.12.1 - 2026-03-30

### Fixed

- History page news titles causing horizontal overflow on mobile devices
- News titles now use `line-clamp-2` for better mobile readability
- Source and date metadata no longer compressed on mobile viewports
- Added `leading-snug` for improved line height in news titles

### Added

- Comprehensive E2E tests for History page RWD (history-rwd.spec.ts)
- Mobile viewport testing (375x667)
- Tablet viewport testing (768x1024)
- Desktop viewport testing (1280x720)
- Horizontal overflow detection tests
- Line clamping validation tests
- Long title handling tests

### Files Modified

- `web/src/pages/HistoryPage.vue` - Fixed RWD issues with news titles
- `web/e2e/history-rwd.spec.ts` - New E2E test suite for RWD validation

## v0.12.0 - 2026-03-28

### Added

- **UI Components**: New Skeleton, EmptyState, and Tooltip components
- **Animations**: Page transitions, card hover effects, and toast animations
- **Design System**: Enhanced color palette with accent and semantic colors
- **Animation Utilities**: Comprehensive CSS animations with accessibility support

### Changed

- **Icon System**: Replaced navigation emoji icons with Lucide Icons for visual consistency
- **Color System**: Added accent (orange) and semantic colors (success, warning, error)
- **Shadows**: New soft shadow variants (soft, soft-md, soft-lg)
- **MainLayout**: Navigation now uses Lucide icons (Rss, History, Radio, Settings)
- **FeedPage**: Header icon replaced with Rss icon
- **SourcesPage**: Header icon replaced with Radio icon, status indicators (🟢/🔴) preserved as emoji

### Files Modified

- `web/tailwind.config.js` - Enhanced design tokens
- `web/src/styles/main.css` - Animation classes and utilities
- `web/src/styles/animations.css` - Keyframe animations (new)
- `web/src/App.vue` - Page transitions
- `web/src/layouts/MainLayout.vue` - Lucide icons
- `web/src/pages/FeedPage.vue` - Rss icon
- `web/src/pages/SourcesPage.vue` - Radio icon
- `web/src/components/ui/Card.vue` - Hover effects
- `web/src/components/ui/ToastItem.vue` - Slide animations

### New Components

- `web/src/components/ui/Skeleton.vue` - Loading skeleton with variants
- `web/src/components/ui/EmptyState.vue` - Empty state display
- `web/src/components/ui/Tooltip.vue` - Accessible tooltip using radix-vue

## v0.11.1 - 2026-03-28

### Fixed

- SQLAlchemy 2.1 deprecation warning by making `TimestampMixin` inherit from `MappedAsDataclass`
- Pydantic v2 deprecation warning by updating `class Config` to `model_config = ConfigDict(from_attributes=True)` in keys, sources, and trash routes
- pytest-asyncio configuration by adding `asyncio_mode = "auto"` in `pyproject.toml`
- Preview service tests to correctly validate request parameters including headers
- "Clear all previews" button error in Tauri app by handling `204 No Content` response in `tauriFetch`

### Changed

- Test assertions updated to match actual caching behavior (cached content is returned without re-fetching)

## v0.11.0 - 2026-03-27

### Added

- Backup and restore functionality with encrypted ZIP format (AES encryption via pyzipper)
- `GET /api/v1/backup/export` endpoint for exporting database backup
- `POST /api/v1/backup/import` endpoint for importing backup with merge support
- `POST /api/v1/backup/preview` endpoint for previewing backup contents
- `BackupService` for backup/export operations with encryption
- `BackupPasswordProvider` for password management from environment variable
- Backup schemas: `ExportOptions`, `ImportResult`, `BackupPreview`, `BackupCounts`, `ImportSummary`
- `BackupManager.vue` component in Settings page
- Tauri backup commands with native file dialogs: `export_backup`, `import_backup`, `preview_backup`
- i18n translations for backup feature (English and Chinese)
- E2E tests for backup functionality
- 52 unit tests for backup service

### Changed

- Backup filename format: `rss-backup-v{version}-{date}.zip`
- Password from environment variable `BACKUP_PASSWORD` (default: `kimhsiao`)
- Merge mode on restore: backup takes priority, existing data preserved but same records overwritten

## v0.10.0 - 2026-03-27

### Added

- Trash management feature with soft-delete and restore functionality
- `GET /api/v1/trash` endpoint for listing trashed sources
- `POST /api/v1/trash/{id}/restore` endpoint for restoring sources with conflict handling
- `DELETE /api/v1/trash/{id}` endpoint for permanent deletion
- `DELETE /api/v1/trash` endpoint for clearing all trash items
- Partial unique indexes for sources (name, url) to allow same name/url after soft-delete
- Database migration for partial unique indexes using `WHERE deleted_at IS NULL`
- Trash tab in Sources page with restore and permanent delete actions
- Restore conflict dialog with options to overwrite or keep existing source
- E2E tests for trash restore functionality

### Changed

- Source deletion now soft-deletes instead of hard-delete (moves to trash)
- Improved error handling for restore conflicts with specific error messages
- Frontend API now properly handles 409 conflict responses with `RestoreConflictError`

### Fixed

- LSP errors in `trash.py` where `trash` variable could be None
- Frontend API paths for `clearTrash` and `permanentDeleteSource` to match backend routes
- Browser cache inconsistency issues with Service Worker and nginx configuration
- Scheduler not available error when `SCHEDULER_ENABLED=false` by always creating scheduler instance
- SQLite migration issues with unique constraint removal

## v0.9.3 - 2026-03-27

### Fixed

- Article preview in Tauri desktop app now works correctly by using Tauri command to fetch directly from markdown.new API
- Skip cache lookup in Tauri environment to avoid sidecar network limitations
- Handle 500 errors in cache lookup as "not found" instead of throwing errors

## v0.9.2 - 2026-03-27

### Fixed

- Article preview in Tauri desktop app now works correctly
- Changed from async to blocking approach for preview fetching in protocol handler
- Added comprehensive debug logging to trace preview request flow
- Preview requests now handled synchronously using `tauri::async_runtime::block_on`
- Added `src-tauri/src/preview/mod.rs` module for article preview handling

## v0.9.1 - 2026-03-26

### Fixed

- Article preview error handling in Tauri desktop app
- Error messages from Python backend are now properly propagated to frontend
- Rust JSON-RPC client now includes `data.detail` in error messages for better debugging

## v0.9.0 - 2026-03-26

### Added

- Article Quick Preview feature for Feed and History pages
- `GET /api/v1/previews/{url_hash}` endpoint for cached preview retrieval
- `GET /api/v1/previews?url=...` endpoint for preview by URL
- `POST /api/v1/previews` endpoint for creating/updating preview content
- `PreviewContent` SQLAlchemy model with SHA-256 URL hashing
- `PreviewService` for preview content management
- `ArticlePreviewDialog.vue` component with markdown rendering
- `useArticlePreview` composable for preview state management
- URL normalizer utility with SHA-256 hashing
- Eye icon button on Feed page items for quick preview
- Eye and ExternalLink icons on History page items
- i18n keys for preview feature (English and Chinese)
- E2E tests for article preview functionality

### Changed

- Preview content is cached in database per-URL for faster subsequent loads
- Uses markdown.new API for content fetching with `retain_images: true`

## v0.8.0 - 2026-03-24

### Added

- Batch CRUD operations for fetch history management
- `PATCH /api/v1/history/batches/{id}/name` endpoint for renaming batches
- `DELETE /api/v1/history/batches/{id}` endpoint for deleting batches
- `UpdateBatchNameRequest` and `DeleteBatchResponse` schemas
- `get_batch_display_name` utility for friendly batch names in UI
- Inline batch name editing in History page
- Batch deletion with confirmation dialog in History page

### Changed

- `refresh_source` now creates FetchBatch for history tracking
- Improved History page UI with batch management actions

### Fixed

- Test file naming conflict (renamed `scripts/test_history_query.py` to `scripts/demo_history_query.py`)
- SQLite locking issues in stdio tests

## v0.7.0 - 2026-03-24

### Added

- History query feature with date range filtering
- `/api/v1/history` endpoint for fetching history records
- HistoryService for history data management
- HistoryPage component with date range picker and pagination
- DateRangePicker component for date selection
- Pagination component for list navigation
- SourceTags component for displaying source tags
- ConfirmDialog component for user confirmations
- `useConfirm` composable for dialog management
- `fetch_batches` table for tracking fetch batch operations
- `batch_id` field in `fetch_logs` and `feed_items` tables
- E2E testing setup with Playwright

### Changed

- Refactored fetch service with batch tracking
- Improved error handling in history queries

## v0.6.2 - 2026-03-23

### Fixed

- CI/CD: Remove `--name` option from pyinstaller command (spec file already defines name)
- CI/CD: Update pnpm-lock.yaml to sync with package.json (remove deprecated dotenv)
- CI/CD: Add `tauri` script to root package.json
- CI/CD: Install root npm dependencies for tauri cli
- CI/CD: Rename sidecar binary with target triple suffix for Tauri compatibility
- CI/CD: Separate build steps for tag push vs manual trigger to prevent release creation errors

## v0.6.1 - 2026-03-23

### Changed

- Split Dockerfile into separate Dockerfile.api and Dockerfile.web for better build optimization
- Improved docker-compose.yml with profile support (api, web, full)
- Added custom nginx configuration for SPA routing and API proxy
- Added favicon.ico generation for web app

## v0.6.0 - 2026-03-21

### Added

- Desktop application support for Windows, macOS (Intel & Apple Silicon), and Linux
- Tauri v2 integration with JSON-RPC over stdio communication
- First-run setup wizard with language and timezone configuration
- Portable data storage (`./data/` directory)
- Database import/export functionality
- PyInstaller sidecar build pipeline
- GitHub Actions CI/CD for multi-platform builds

### Changed

- Frontend now detects environment (web vs desktop) automatically
- Settings page shows desktop-specific features when running in Tauri
- Router redirects to setup wizard on first run

### Technical

- Added `src/stdio/` module for JSON-RPC stdio communication
- Added `src-tauri/` for Tauri application
- Added `scripts/` for build automation
- Sidecar process management with stdin/stdout pipes
- Protocol interceptor for `app://localhost` requests

## v0.5.1 - 2026-03-21

### Changed

- Updated `.gitignore` with comprehensive ignore patterns
- Removed build artifacts from git tracking (`__pycache__/*.pyc`, `*.tsbuildinfo`)

## v0.5.0 - 2026-03-21

### Added

- Configurable CORS with `ALLOWED_ORIGINS` environment variable
- XSS protection with DOMPurify in all preview components (RSS, JSON, Markdown)
- Dedicated preview components: `JsonPreview.vue`, `MarkdownPreview.vue`, `RssXmlPreview.vue`
- `useFeedCache` composable for centralized feed caching logic
- Biome configuration for Tailwind CSS linting

### Changed

- API key storage changed from `localStorage` to `sessionStorage` for better security
- Docker container now runs as non-root user (`appuser`)
- Debug mode default changed to `false` for production safety
- 404 responses now return JSON format instead of empty body
- MarkdownPreview: fixed header with independent scrollable content area
- Error handling in catch blocks now logs errors for debugging

### Fixed

- SQLAlchemy `soft_delete` event handler compatibility with SQLAlchemy 2.0+
- `source_id` parameter inconsistency in feed service
- Test timezone handling using unified `now()` utility
- Model default value test expectations (`fetch_interval`: 900 → 0)
- Circular import issues in models using `TYPE_CHECKING`
- Double scrollbar in Markdown preview dialog
- Markdown preview showing in RSS/JSON tabs

### Security

- CORS policy now configurable via environment variable
- XSS protection added to all `v-html` render points
- API keys no longer persist across browser sessions
- Docker container runs with minimal privileges

## v0.4.0 - 2026-03-21

### Added

- Configurable timezone support with `APP_TIMEZONE` environment variable (default: Asia/Taipei)
- Multiple fetch interval options: Never, 1h, 3h, 6h, 12h, 24h, 3 days, 7 days
- Complete i18n support for time formatting (relative time display)
- `time` translation keys for Chinese and English locales
- `app.name` translation key for application name

### Changed

- Default `fetch_interval` changed from 900 (15 min) to 0 (no auto-update)
- Sources with `fetch_interval=0` are now skipped by the scheduler
- Time formatting now respects locale settings (English/Chinese)
- Date display now uses locale-specific format

### Fixed

- Docker container name conflict error
- SQLAlchemy SAWarning for nullable column detection
- Python `datetime.utcnow()` deprecation warning
- Hardcoded Chinese text in time formatting (`formatDate` function)
- Missing i18n for application name in MainLayout
- Missing i18n for "items" text in LogsPage

## v0.3.0 - 2026-03-21

### Added

- Unified formatter module for RSS/JSON/Markdown output formats
- `format` parameter to `/api/v1/feed` endpoint (supports `rss`, `json`, `markdown`)
- `/api/v1/sources/{id}/feed` endpoint for source-specific feed preview
- Syntax highlighting for RSS (XML), JSON, and Markdown in preview dialog
- Responsive button layout on Feed page (icon-only on mobile)
- Active state highlighting for bottom navigation
- CORS middleware for cross-origin frontend access

### Changed

- Default feed format changed from JSON to RSS
- Feed preview dialog now supports wider layout (2xl)
- Improved Chinese/English translations for navigation and page titles
- Code preview area now supports both light and dark modes
- JSON syntax highlighting with proper key/value distinction

### Fixed

- Button text wrapping on small screens
- Feed preview dialog height overflow
- Code content not selectable in preview dialog

## v0.2.0 - 2026-03-20

### Added

- Custom API Key feature with validation (16-255 chars, alphanumeric/hyphens/underscores)
- "Refresh All" button for Sources and Feed pages
- PWA support with Service Worker
- RWD (Responsive Web Design) support for all pages
- Smart URL truncation for mobile displays
- Copy button for API keys
- Created/Updated timestamps for Sources

### Changed

- Feed endpoint now returns JSON instead of XML for better frontend compatibility
- Fixed timezone handling (added UTC 'Z' suffix to ISO timestamps)
- Fixed Logs page to display error content correctly
- All buttons now have proper icons (Lucide)
- All buttons now have proper tooltips with i18n support
- Improved error log display with color coding (success/error)

### Fixed

- Feed page "invalid data" error
- Timezone offset showing "8 hours ago" instead of correct time
- Logs page showing empty content
- RWD layout issues on mobile devices

## v0.1.0 - 2026-03-18

### Added

- Initial release
- RSS/Atom feed aggregation
- Source management API
- Scheduled background fetching
- API key authentication
- Rate limiting
- Feed filtering by time range and keywords
- Feed sorting by publication time or source name
- Daily statistics tracking
- Error log API
- Docker support
- Google Alert URL cleaning
- Feed deduplication by link