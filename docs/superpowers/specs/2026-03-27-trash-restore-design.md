# Trash and Restore Feature Design

**Date**: 2026-03-27
**Author**: Design Team
**Status**: Approved

---

## Problem Statement

When a source is soft-deleted and then a new source with the same URL is created, the operation fails with a database unique constraint error. This is because:

1. The `url` column has a `unique=True` constraint
2. This constraint applies to ALL rows, including soft-deleted ones (`deleted_at IS NOT NULL`)
3. Soft-deleted records still occupy the unique constraint slot

**Root Cause**: Database unique constraints do not exclude soft-deleted records.

---

## Requirements

| Item | Decision |
|------|----------|
| **Uniqueness** | Both `name` and `url` must be unique (excluding soft-deleted records) |
| **Frontend UI** | Tab switch within Sources page |
| **Restore Conflict** | Smart merge (user chooses: overwrite or keep existing) |
| **Permanent Delete** | Manual delete per item |
| **Clear Trash** | Required |

---

## Solution: Composite Approach

### 1. Database Layer: Partial Unique Indexes

PostgreSQL supports partial indexes with `WHERE` conditions, allowing uniqueness constraints to apply only to non-deleted records.

**Migration**:

```sql
-- Remove existing unconditional unique constraint
DROP INDEX IF EXISTS ix_sources_url;
ALTER TABLE sources DROP CONSTRAINT IF EXISTS sources_url_key;

-- Create partial unique indexes (only for active records)
CREATE UNIQUE INDEX uq_sources_url_active 
ON sources(url) 
WHERE deleted_at IS NULL;

CREATE UNIQUE INDEX uq_sources_name_active 
ON sources(name) 
WHERE deleted_at IS NULL;
```

**Benefits**:
- Soft-deleted records no longer occupy unique constraint slots
- Database-level guarantee of data integrity
- Optimal performance

### 2. Application Layer: Defensive Checks

Keep existing application-level uniqueness checks as defense:

```python
# In SourceService.create_source
existing = await self.session.execute(
    select(Source).where(Source.url == url, Source.deleted_at.is_(None))
)
```

---

## API Design

### New Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/sources/trash` | List trash items |
| `POST` | `/api/v1/sources/trash/{id}/restore` | Restore item (with conflict detection) |
| `DELETE` | `/api/v1/sources/trash/{id}` | Permanently delete single item |
| `DELETE` | `/api/v1/sources/trash` | Clear all trash |

### Restore API Details

**Request**:
```json
POST /api/v1/sources/trash/1/restore
Content-Type: application/json

{
  "conflict_resolution": "overwrite"  // optional: "overwrite" | "keep_existing"
}
```

**Response - Success (200)**:
```json
{
  "id": 1,
  "name": "Tech News",
  "restored": true
}
```

**Response - Conflict (409)**:
```json
{
  "error": "conflict_detected",
  "message": "A source with this name or URL already exists",
  "conflict": {
    "trash_item": {
      "id": 1,
      "name": "Tech News",
      "url": "https://tech.com/rss"
    },
    "existing_item": {
      "id": 5,
      "name": "Tech News",
      "url": "https://tech.com/rss"
    },
    "conflict_type": "both"  // "name" | "url" | "both"
  }
}
```

### Restore Flow

```
User clicks "Restore"
       │
       ▼
Get trash item by ID
       │
   ┌───┴───┐
   │ Found?    │
   └───┬───┘
     ┌─┴─┐
    No   Yes
     │    │
     ▼    ▼
Return 404   Check for conflicts
"Not found"     │
            ┌───┴───┐
            │ Has conflict? │
            └───┬───┘
              ┌─┴─┐
             Yes  No
              │    │
              ▼    ▼
          Return 409   Directly restore
          with conflict info   (set deleted_at = NULL)
              │
              ▼
          User chooses:
          ├── Overwrite → Soft delete existing, restore trash item
          ├── Keep Existing → No action
          └── Cancel → No action
```

### Error Responses

| Status | Error | Description |
|--------|-------|-------------|
| 404 | `"Trash item not found"` | Item ID doesn't exist or is not in trash |
| 409 | `"conflict_detected"` | Name or URL conflict with existing active source |

---

## Service Layer Design

### New Methods in SourceService

```python
class SourceService:
    # Existing methods...
    
    async def get_trash_sources(self) -> list[Source]:
        """Get all soft-deleted sources."""
        
    async def get_trash_source(self, source_id: int) -> Source | None:
        """Get a single trash item by ID."""
        
    async def check_restore_conflict(self, source_id: int) -> dict | None:
        """Check if restoring would cause a conflict.
        
        Returns None if no conflict, or dict with existing_item and conflict_type.
        """
        
    async def restore_source(self, source_id: int, overwrite: bool = False) -> Source:
        """Restore a trash item.
        
        If overwrite=True and conflict exists, soft-delete the existing item first.
        """
        
    async def permanent_delete_source(self, source_id: int) -> None:
        """Permanently delete a trash item."""
        
    async def clear_trash(self) -> int:
        """Clear all trash items. Returns count of deleted items."""
```

---

## Frontend UI Design

### Page Structure

```
SourcesPage.vue
├── Tabs (new)
│   ├── Active Tab (default) - shows non-deleted sources
│   └── Trash Tab - shows deleted sources
│       ├── Empty state
│       ├── Trash list
│       │   ├── Restore button
│       │   └── Delete Permanently button
│       └── Clear All button
```

### New Components

| Component | Purpose |
|-----------|---------|
| `TrashTab.vue` | Trash list within Sources page |
| `RestoreConflictDialog.vue` | Dialog for conflict resolution |
| `api/trash.ts` | API functions for trash operations |

### Conflict Dialog Design

```
┌─────────────────────────────────────────────────────────┐
│  ⚠️ Source Conflict Detected                            │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  A source with the same name or URL already exists:    │
│                                                         │
│  Existing Source:                                       │
│    Name: Tech News                                      │
│    URL: https://tech.com/rss                            │
│                                                         │
│  From Trash:                                            │
│    Name: Tech News                                      │
│    URL: https://tech.com/rss                            │
│                                                         │
│  [Replace with Trash Item]  [Keep Existing]  [Cancel]  │
└─────────────────────────────────────────────────────────┘
```

---

## Internationalization

### English (en.json)

```json
{
  "sources": {
    "tabs": {
      "active": "Active Sources",
      "trash": "Trash"
    },
    "trash": {
      "empty": "Trash is empty",
      "restore": "Restore",
      "delete_permanently": "Delete Permanently",
      "clear_all": "Clear Trash",
      "clear_confirm": "Are you sure you want to permanently delete all items in trash?"
    },
    "conflict": {
      "title": "Source Conflict Detected",
      "message": "A source with the same name or URL already exists",
      "existing": "Existing Source",
      "from_trash": "From Trash",
      "conflict_type": {
        "name": "Name conflict",
        "url": "URL conflict",
        "both": "Name and URL conflict"
      },
      "overwrite": "Replace with Trash Item",
      "keep_existing": "Keep Existing",
      "cancel": "Cancel"
    }
  }
}
```

### Traditional Chinese (zh-TW.json)

```json
{
  "sources": {
    "tabs": {
      "active": "作用中的來源",
      "trash": "垃圾桶"
    },
    "trash": {
      "empty": "垃圾桶是空的",
      "restore": "恢復",
      "delete_permanently": "永久刪除",
      "clear_all": "清空垃圾桶",
      "clear_confirm": "確定要永久刪除垃圾桶中的所有項目嗎？"
    },
    "conflict": {
      "title": "偵測到來源衝突",
      "message": "已存在相同名稱或 URL 的來源",
      "existing": "現有項目",
      "from_trash": "垃圾桶項目",
      "conflict_type": {
        "name": "名稱衝突",
        "url": "URL 衝突",
        "both": "名稱與 URL 衝突"
      },
      "overwrite": "以垃圾桶項目取代",
      "keep_existing": "保留現有項目",
      "cancel": "取消"
    }
  }
}
```

---

## Test Plan

### Backend Unit Tests (`tests/services/test_source_service.py`)

| Test Case | Description |
|-----------|-------------|
| `test_get_trash_sources` | Get trash list |
| `test_get_trash_source` | Get single trash item |
| `test_check_restore_conflict_none` | No conflict case |
| `test_check_restore_conflict_name` | Name conflict |
| `test_check_restore_conflict_url` | URL conflict |
| `test_check_restore_conflict_both` | Name + URL conflict |
| `test_restore_source_no_conflict` | Restore without conflict |
| `test_restore_source_overwrite` | Restore with overwrite |
| `test_permanent_delete_source` | Permanent delete |
| `test_clear_trash` | Clear all trash |

### Backend API Tests (`tests/api/test_trash_routes.py`)

| Test Case | Description |
|-----------|-------------|
| `test_list_trash` | List trash items |
| `test_restore_no_conflict` | Restore without conflict |
| `test_restore_conflict_returns_409` | Conflict returns 409 |
| `test_restore_with_overwrite` | Restore with overwrite |
| `test_permanent_delete` | Permanent delete |
| `test_clear_trash` | Clear all trash |

### Frontend E2E Tests

| Test Case | Description |
|-----------|-------------|
| Switch to Trash Tab | Displays trash list |
| Restore flow | Click restore → handle conflict dialog |
| Permanent delete | Confirm dialog → delete |
| Clear trash | Confirm dialog → clear |

---

## Implementation Order

```
Phase 1: Database Migration
├── Create migration for partial unique indexes
└── Update Source model (remove unique=True from mapped_column)

Phase 2: Backend
├── Add methods to SourceService
├── Add trash API routes
└── Write unit tests

Phase 3: Frontend
├── Add trash API functions
├── Create TrashTab component
├── Create RestoreConflictDialog component
├── Update SourcesPage with tabs
└── Add i18n translations

Phase 4: Integration
└── E2E tests
```

---

## Files to Modify/Create

### Create
- `alembic/versions/xxx_add_partial_unique_indexes.py`
- `src/api/routes/trash.py`
- `web/src/api/trash.ts`
- `web/src/components/TrashTab.vue`
- `web/src/components/RestoreConflictDialog.vue`

### Modify
- `src/models/source.py` - Remove `unique=True` from url
- `src/services/source_service.py` - Add trash methods
- `src/api/routes/__init__.py` - Register trash router
- `web/src/pages/SourcesPage.vue` - Add tabs
- `web/src/locales/en.json` - Add translations
- `web/src/locales/zh.json` - Add translations