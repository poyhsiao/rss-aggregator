# History Query Feature Design

## Overview

Add a history query feature that allows users to search previously fetched RSS feed items based on date range and source names. Results are displayed with pagination in a UI consistent with the existing FeedPage.

## Requirements

### Functional Requirements

1. **Date Range Filtering**
   - Quick selection buttons: Last 7 days, Last 30 days, This month, Last month
   - Custom date range: Start date and end date inputs
   - Both filters are optional

2. **Source Name Filtering**
   - Display available sources as clickable tag buttons
   - Support multi-select
   - Provide "Select All" and "Clear" shortcuts

3. **Search Results**
   - Display as card list (same style as FeedPage)
   - Each card shows: source name, published time, title, description
   - Clickable to open original link

4. **Pagination**
   - Traditional pagination with page numbers
   - 20 items per page
   - Display total count and current page info

### Non-Functional Requirements

- API response time < 500ms for typical queries
- Support up to 10,000+ historical items
- Mobile-responsive UI
- Support i18n (English, Chinese Traditional)

## UI Design

### Page Structure

New page: `HistoryPage.vue`

```
┌─────────────────────────────────────────────────────┐
│ Header: 📜 History                                   │
├─────────────────────────────────────────────────────┤
│ Filter Section                                       │
│ ┌─────────────────────────────────────────────────┐ │
│ │ Quick: [Last 7 Days] [Last 30 Days] [This Month]│ │
│ │        [Last Month]                              │ │
│ │                                                  │ │
│ │ Date Range: [Start Date] ~ [End Date]           │ │
│ │                                                  │ │
│ │ Sources: [Select All] [Clear]                   │ │
│ │          [Source A] [Source B] [Source C] ...   │ │
│ │                                                  │ │
│ │ [Search Button]                                  │ │
│ └─────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────┤
│ Results Section                                      │
│ ┌─────────────────────────────────────────────────┐ │
│ │ Total: 150 items                                 │ │
│ │                                                  │ │
│ │ ┌─────────────────────────────────────────────┐ │ │
│ │ │ Source A • 2024-01-15                        │ │ │
│ │ │ Title of the feed item                       │ │ │
│ │ │ Description text...                          │ │ │
│ │ └─────────────────────────────────────────────┘ │ │
│ │ ...more cards...                                 │ │
│ └─────────────────────────────────────────────────┘ │
│                                                      │
│ Pagination: [<] 1 2 3 ... 8 [>]                     │
└─────────────────────────────────────────────────────┘
```

### Navigation

- Add "History" link to sidebar (desktop)
- Add "History" link to bottom navigation (mobile)
- Icon: `History` from lucide-vue-next

## API Design

### New Endpoint

```
GET /api/v1/history
```

### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `start_date` | string | No | Start date (ISO 8601, e.g., `2024-01-01`) |
| `end_date` | string | No | End date (ISO 8601, e.g., `2024-01-31`) |
| `source_ids` | string | No | Source IDs (comma-separated, e.g., `1,2,3`) |
| `keywords` | string | No | Keywords (semicolon-separated) |
| `sort_by` | string | No | Sort field (`published_at` or `fetched_at`, default: `fetched_at`) |
| `sort_order` | string | No | Sort direction (`asc` or `desc`, default: `desc`) |
| `page` | int | No | Page number (default: 1) |
| `page_size` | int | No | Items per page (default: 20, max: 100) |

### Response

```json
{
  "items": [
    {
      "id": 1,
      "source_id": 1,
      "source": "Source Name",
      "title": "Title",
      "link": "https://...",
      "description": "Description",
      "published_at": "2024-01-15T10:00:00",
      "fetched_at": "2024-01-15T12:00:00"
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total_items": 150,
    "total_pages": 8
  }
}
```

### Timezone Handling

- All dates are interpreted in `app_timezone` (default: `Asia/Taipei`)
- No timezone parameter from frontend
- Server uses configured timezone for date parsing

## Database Query Logic

### Filter Conditions

1. **Date Range**
   - `start_date`: `fetched_at >= start_date 00:00:00`
   - `end_date`: `fetched_at <= end_date 23:59:59`
   - Both can be used independently or together

2. **Source IDs**
   - `source_id IN (id1, id2, ...)`

3. **Keywords**
   - Same as FeedService: `title ILIKE '%keyword%'`
   - Multiple keywords with OR condition

4. **Soft Delete**
   - `FeedItem.deleted_at IS NULL`
   - `Source.deleted_at IS NULL`
   - `Source.is_active == True`

### Sorting

- Default: `fetched_at DESC`
- Options: `published_at`, `fetched_at`
- Directions: `asc`, `desc`

### Pagination

- Use SQLAlchemy `offset()` and `limit()`
- Count total items for pagination info

## File Structure

### Backend (Python)

| File | Description |
|------|-------------|
| `src/api/routes/history.py` | New route file |
| `src/services/history_service.py` | New service for history queries |

### Frontend (Vue/TypeScript)

| File | Description |
|------|-------------|
| `web/src/pages/HistoryPage.vue` | Main history page |
| `web/src/components/DateRangePicker.vue` | Date range picker with quick buttons |
| `web/src/components/SourceTags.vue` | Source tag selector |
| `web/src/components/Pagination.vue` | Pagination component |
| `web/src/api/history.ts` | History API module |
| `web/src/types/history.ts` | TypeScript types |

### Modified Files

| File | Changes |
|------|---------|
| `src/api/routes/__init__.py` | Include history router |
| `web/src/layouts/MainLayout.vue` | Add History nav link |
| `web/src/router/index.ts` | Add `/history` route |
| `web/src/locales/en.json` | Add i18n keys |
| `web/src/locales/zh-TW.json` | Add i18n keys |

## i18n Keys

```json
{
  "nav": {
    "history": "History"
  },
  "history": {
    "title": "History",
    "filter": {
      "title": "Filter",
      "start_date": "Start Date",
      "end_date": "End Date",
      "source": "Source",
      "select_all": "Select All",
      "clear": "Clear",
      "search": "Search"
    },
    "quick": {
      "last_7_days": "Last 7 Days",
      "last_30_days": "Last 30 Days",
      "this_month": "This Month",
      "last_month": "Last Month"
    },
    "result": {
      "total": "Total {count} items",
      "page": "Page {current} of {total}"
    },
    "empty": "No results found",
    "no_sources": "No sources available"
  }
}
```

## Implementation Order

1. **Backend**
   - Create `HistoryService` with query logic
   - Create `/api/v1/history` endpoint
   - Add unit tests

2. **Frontend Components**
   - Create `Pagination.vue` component
   - Create `DateRangePicker.vue` component
   - Create `SourceTags.vue` component

3. **Frontend Page**
   - Create `HistoryPage.vue`
   - Create `history.ts` API module
   - Add routing and navigation

4. **i18n**
   - Add keys to `en.json`
   - Add keys to `zh-TW.json`

5. **Integration**
   - End-to-end testing
   - Mobile responsiveness verification