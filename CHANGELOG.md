# Changelog

All notable changes to this project will be documented in this file.

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