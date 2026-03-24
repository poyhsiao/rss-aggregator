# Log Feature Enhancement Design

## Overview

Enhance the frontend log functionality to provide comprehensive operation tracking with improved UI/UX.

## Requirements

1. Record all API operations in frontend logs
2. Display action names (not just log_type)
3. Click card to expand detailed information
4. Copy error message button in detail view
5. Separate display for frontend operation logs and backend system logs
6. TDD development workflow with proper testing

## Architecture

### Data Flow

```
User Action → API Call → Response Interceptor → Log Store → LogsPage Display
                ↓
            Success/Error
                ↓
         Record to Operation Log
```

### Component Structure

```
LogsPage.vue
├── TabNav (System Logs | Operation Logs)
├── SystemLogsTab (existing backend logs)
│   └── LogCard (expandable)
└── OperationLogsTab (new frontend logs)
    └── LogCard (expandable)
```

## Data Structures

### Operation Log Type

```typescript
interface OperationLog {
  id: string
  timestamp: string
  action: LogAction
  status: 'success' | 'error'
  message: string
  details: {
    target?: string      // Target name (e.g., source name)
    targetId?: number    // Target ID
    request?: unknown    // Request data (sanitized)
    response?: unknown   // Response data
    error?: string       // Error message for copy
  }
}

type LogAction = 
  | 'create_source' 
  | 'update_source' 
  | 'delete_source'
  | 'create_key' 
  | 'delete_key' 
  | 'refresh_source' 
  | 'refresh_all'
```

### Extended Error Log Type (Backend)

```typescript
interface ErrorLog {
  id: number
  source_id: number | null
  status: 'success' | 'error'
  log_type: string
  message: string
  items_count: number | null
  created_at: string
  // New fields for expanded view
  details?: string       // Raw error details
  request_data?: string  // Request payload
}
```

## Implementation Plan

### Phase 1: Core Infrastructure (TDD)

1. **Log Store** (`web/src/stores/log.ts`)
   - Pinia store for operation logs
   - Actions: addLog, clearLogs, getLogs
   - Persist to localStorage (max 100 entries)

2. **Type Definitions** (`web/src/types/log.ts`)
   - OperationLog interface
   - LogAction type

3. **Unit Tests** (`web/src/stores/__tests__/log.test.ts`)
   - Test addLog functionality
   - Test clearLogs functionality
   - Test localStorage persistence
   - Test max entries limit

### Phase 2: API Integration

1. **Response Interceptor** (`web/src/api/index.ts`)
   - Intercept all API responses
   - Record operations to log store
   - Sanitize sensitive data (API keys)

2. **Unit Tests** (`web/src/api/__tests__/index.test.ts`)
   - Test success logging
   - Test error logging
   - Test data sanitization

### Phase 3: UI Components

1. **LogCard Component** (`web/src/components/LogCard.vue`)
   - Collapsible card design
   - Status indicators (success/error)
   - Copy error message button
   - Responsive layout

2. **LogsPage Refactor** (`web/src/pages/LogsPage.vue`)
   - Add Tab navigation
   - Separate System Logs and Operation Logs
   - Use LogCard for both tabs

3. **E2E Tests** (`web/e2e/logs.spec.ts`)
   - Test tab switching
   - Test card expand/collapse
   - Test copy error message
   - Test on both web and Tauri app

### Phase 4: i18n Updates

1. **Add Translations** (`web/src/locales/*.json`)
   - Action names in zh and en
   - Tab labels
   - UI strings for expanded view

## Testing Strategy

### Unit Tests

| Component | Test File | Coverage |
|-----------|-----------|----------|
| Log Store | `stores/__tests__/log.test.ts` | addLog, clearLogs, persistence |
| API Interceptor | `api/__tests__/index.test.ts` | logging, sanitization |

### E2E Tests

| Scenario | Test File | Environment |
|----------|-----------|-------------|
| Tab Navigation | `e2e/logs.spec.ts` | Web + Tauri |
| Card Expand/Collapse | `e2e/logs.spec.ts` | Web + Tauri |
| Copy Error Message | `e2e/logs.spec.ts` | Web + Tauri |
| Operation Logging | `e2e/logs.spec.ts` | Web + Tauri |

### Tauri/macOS Considerations

- Use `@tauri-apps/api` for clipboard operations
- Test with `cargo tauri dev` on macOS
- Ensure proper window focus handling

## Files to Create/Modify

### New Files

- `web/src/stores/log.ts` - Log store
- `web/src/stores/__tests__/log.test.ts` - Store tests
- `web/src/components/LogCard.vue` - Reusable log card
- `web/src/api/__tests__/index.test.ts` - API tests
- `web/e2e/logs.spec.ts` - E2E tests

### Modified Files

- `web/src/types/log.ts` - Add OperationLog type
- `web/src/api/index.ts` - Add logging interceptor
- `web/src/pages/LogsPage.vue` - Add tabs, use LogCard
- `web/src/locales/zh.json` - Add translations
- `web/src/locales/en.json` - Add translations

## Success Criteria

1. ✅ All API operations logged in frontend
2. ✅ Frontend and backend logs displayed in separate tabs
3. ✅ Cards expand/collapse to show details
4. ✅ Copy error message button works
5. ✅ Unit tests pass with >80% coverage
6. ✅ E2E tests pass on web and Tauri
7. ✅ i18n complete for zh and en
8. ✅ Works correctly on macOS Tauri app

## Timeline

- Phase 1: Core Infrastructure - 2 hours
- Phase 2: API Integration - 1 hour
- Phase 3: UI Components - 3 hours
- Phase 4: i18n Updates - 30 minutes

**Total Estimated: 6.5 hours**