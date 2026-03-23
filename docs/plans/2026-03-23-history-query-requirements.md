# History Query Feature - Requirements

## User Story

As a user, I want to search through previously fetched RSS feed items by date range and source names, so that I can find historical content that was aggregated in the past.

## Functional Requirements

### FR-1: Date Range Filtering
- Users can filter items by a custom date range
- Start date and end date are both optional
- Quick selection buttons: Last 7 days, Last 30 days, This month, Last month
- Date range applies to the `fetched_at` field

### FR-2: Source Name Filtering
- Users can filter items by one or more source names
- Sources are displayed as clickable tag buttons
- Support multi-select
- Provide "Select All" and "Clear" shortcuts

### FR-3: Keyword Search
- Users can search by keywords in item titles
- Multiple keywords supported (semicolon-separated)
- Search is optional

### FR-4: Results Display
- Display items in card format (same as FeedPage)
- Each card shows: source name, published date, title, description
- Cards are clickable and open original link in new tab

### FR-5: Pagination
- Results are paginated with 20 items per page
- Display page numbers and navigation controls
- Show total item count

### FR-6: Sorting
- Sort by `fetched_at` (default) or `published_at`
- Sort direction: ascending or descending (default)

## Non-Functional Requirements

### NFR-1: Performance
- API response time < 500ms for typical queries
- Support queries on datasets with 10,000+ items

### NFR-2: Usability
- UI consistent with existing FeedPage design
- Mobile-responsive layout
- Support dark/light theme

### NFR-3: Internationalization
- Support English and Chinese Traditional
- All UI labels use i18n keys

### NFR-4: Compatibility
- No new external dependencies
- Reuse existing patterns and components

## Constraints

- Timezone uses server `app_timezone` setting (no client-side override)
- Maximum 100 items per page
- Soft-deleted items and inactive sources are excluded

## Out of Scope

- Export/download historical data
- Saved search presets
- Calendar view for date selection
- Full-text search (only title search)