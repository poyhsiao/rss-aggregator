# Implementation Plan: History Delete Feature

## Overview

Implement the history delete feature with two main capabilities:
1. Delete all history records
2. Delete history records by group

## Implementation Steps

### Phase 1: Backend (Python/FastAPI)

#### Step 1.1: Add Schema
**File:** `src/schemas/history.py`
- Add `DeleteHistoryResponse` schema

#### Step 1.2: Add Service Methods
**File:** `src/services/history_service.py`
- Add `delete_all_history()` method
- Add `delete_history_by_group(group_id: int)` method

#### Step 1.3: Add API Endpoints
**File:** `src/api/routes/history.py`
- Add `DELETE /history` endpoint
- Add query parameter `group_id` support

#### Verification
- Run existing tests: `pytest tests/ -k history`
- Test new endpoints manually with curl

---

### Phase 2: Frontend (Vue/TypeScript)

#### Step 2.1: Add Type Definition
**File:** `web/src/types/history.ts`
- Add `DeleteHistoryResponse` type

#### Step 2.2: Add API Functions
**File:** `web/src/api/history.ts`
- Add `deleteAllHistory()` function
- Add `deleteHistoryByGroup(groupId: number)` function

#### Step 2.3: Add "Delete All" to History Page
**File:** `web/src/pages/HistoryPage.vue`
- Add delete button in page header
- Use existing `useConfirm` composable
- Add i18n keys if needed:
  - `history.deleteAll`
  - `history.deleteAllConfirm`

#### Step 2.4: Add "Delete by Group" to Sources Page
**File:** `web/src/pages/SourcesPage.vue`
- Add delete option to each group card
- Use existing `useConfirm` composable
- Add i18n keys if needed:
  - `sources.deleteGroupHistory`
  - `sources.deleteGroupHistoryConfirm`

#### Verification
- Run frontend tests: `pnpm test`
- Run E2E tests: `pnpm test:e2e`

---

### Phase 3: Integration Testing

1. Test delete all from History page
2. Test delete by group from Sources page
3. Verify data is properly deleted
4. Verify error handling works correctly

---

## Dependencies

- Backend depends on: None (using existing patterns)
- Frontend depends on: `useConfirm` composable (already exists)

## Notes

- Follow existing code patterns in each file
- Use proper error handling
- Add appropriate i18n keys
- Test both success and error scenarios