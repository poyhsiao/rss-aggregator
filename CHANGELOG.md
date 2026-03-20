# Changelog

All notable changes to this project will be documented in this file.

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