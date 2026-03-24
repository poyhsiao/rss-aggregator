# Changelog

All notable changes to this project will be documented in this file.

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