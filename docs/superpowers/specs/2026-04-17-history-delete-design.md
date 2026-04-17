# History Delete Feature Design

## Overview

Add functionality to delete all history records or delete history by group. Includes backend API enhancements and frontend UI updates.

## API Design

### New Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| DELETE | `/history` | Delete all history records |
| DELETE | `/history?group_id={id}` | Delete history records for specified group |

### Request Parameters

- `group_id` (optional): If provided, only delete history records for that group; if not provided, delete all

### Response

```typescript
interface DeleteHistoryResponse {
  success: boolean
  deleted_count: number  // Number of items deleted
}
```

### Error Handling

- Return 404 if group_id doesn't exist
- Return 500 if deletion fails

## Frontend Design

### History Page

- Add "Delete All" button at page top (danger variant)
- Show confirmation dialog using existing `useConfirm` composable
- After confirmation, call API and show Toast notification on success

### Sources Page

- Add "Delete History" option to each group card (icon button or menu item)
- Show confirmation dialog with group name
- Call `/history?group_id={id}` API on confirmation

### Confirmation Dialog Content

**Delete All:**
```
Title: 刪除所有歷史記錄？
Message: 此操作將刪除所有歷史記錄，無法復原。確定要繼續嗎？
Confirm: 刪除全部
Cancel: 取消
```

**Delete by Group:**
```
Title: 刪除 {Group 名稱} 的歷史記錄？
Message: 將刪除該 Group 所有來源的歷史記錄，無法復原。確定要繼續嗎？
Confirm: 刪除
Cancel: 取消
```

## Implementation Notes

1. Use existing `useConfirm` composable for confirmation dialogs
2. Follow existing API patterns in the codebase
3. Add proper error handling and user feedback
4. Ensure i18n support for all UI text

## Files to Modify

### Backend (Python/FastAPI)
- `src/api/routes/history.py` - Add new DELETE endpoints
- `src/services/history_service.py` - Add delete logic
- `src/schemas/history.py` - Add DeleteHistoryResponse schema

### Frontend (Vue/TypeScript)
- `web/src/api/history.ts` - Add delete API functions
- `web/src/types/history.ts` - Add DeleteHistoryResponse type
- `web/src/pages/HistoryPage.vue` - Add "Delete All" button
- `web/src/pages/SourcesPage.vue` - Add per-group delete option
- Add i18n keys if needed