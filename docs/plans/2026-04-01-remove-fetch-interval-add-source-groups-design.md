# Remove fetch_interval + Add Source Groups — Design Document

> Date: 2026-04-01
> Status: Approved
> Author: Kimhsiao

## Problem Statement

目前 RSS Aggregator 的每個 Source 都有獨立的 `fetch_interval`，用於控制自動抓取頻率。這帶來以下問題：
- 使用者不需要 per-source 的抓取頻率控制
- 缺少 Source 的組織方式，無法將多個 Source 分組管理
- Feed 和 History 頁面無法按群組過濾或標記

## Goals

1. **簡化抓取邏輯** — 移除 per-source `fetch_interval`，改為完全手動 refresh
2. **Source 群組管理** — 支援多對多關係，Source 可屬於零或多個群組
3. **群組過濾** — Feed 和 History 頁面可按群組過濾內容

## Non-Goals

- 不實作群組層級的自動抓取排程
- 不實作群組嵌套（sub-groups）
- 不實作群組權限控制

## Architecture Decisions

### Decision 1: Remove fetch_interval entirely

**Chosen:** 完全移除 `fetch_interval`，只保留手動 refresh（`/sources/{id}/refresh` 和 `/sources/refresh`）

**Alternatives considered:**
- 統一全域抓取間隔 —  rejected：增加不必要的設定複雜度
- 保留但停用 — rejected：留下死代碼

### Decision 2: Many-to-many Source ↔ Group relationship

**Chosen:** 多對多關係 + junction table `source_group_members`。Source 可不屬於任何群組。

**Alternatives considered:**
- 一對多（Source 只能屬於一個群組）— rejected：限制太大，同一篇文章可能同時屬於多個分類
- 標籤系統（tags）— rejected：群組有明確的「容器」語意，比標籤更直覺

### Decision 3: Feed page — Group filter chips

**Chosen:** 頂部 filter chips（全部 → 單一群組），不改變現有文章列表結構。

**Alternatives considered:**
- 群組分段顯示 — rejected：多群組 source 的文章會重複顯示
- 左側導航 + 右側內容 — rejected：手機版體驗差

### Decision 4: History page — Group badges + filter chips

**Chosen:** Batch 卡片顯示群組 badge，展開的 item 顯示群組 badge，頂部可過濾。

**Alternatives considered:**
- 按群組分組顯示 items — rejected：多群組 item 只能顯示在一個群組下

## Data Model

### SourceGroup
| Field | Type | Constraints |
|-------|------|-------------|
| id | Integer | PK, auto-increment |
| name | String(255) | UNIQUE, NOT NULL |
| created_at | DateTime | NOT NULL |
| updated_at | DateTime | NOT NULL |
| deleted_at | DateTime | NULL |

### SourceGroupMember (Junction)
| Field | Type | Constraints |
|-------|------|-------------|
| source_id | Integer | FK → sources.id, ON DELETE CASCADE, PK |
| group_id | Integer | FK → source_groups.id, ON DELETE CASCADE, PK |

### Source (Modified)
| Field | Change |
|-------|--------|
| fetch_interval | **REMOVED** |
| groups | **ADDED** — relationship to SourceGroup via junction table |

## API Design

### Source Groups API

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/source-groups` | List all groups with member counts |
| POST | `/api/v1/source-groups` | Create group |
| PUT | `/api/v1/source-groups/{id}` | Update group name |
| DELETE | `/api/v1/source-groups/{id}` | Delete group (sources preserved) |
| GET | `/api/v1/source-groups/{id}/sources` | List sources in group |
| POST | `/api/v1/source-groups/{id}/sources` | Add source to group |
| DELETE | `/api/v1/source-groups/{id}/sources/{source_id}` | Remove source from group |

### Modified Source API

| Field | Change |
|-------|--------|
| SourceResponse | Add `groups: [{id, name}]` |
| SourceCreate | Remove `fetch_interval` |
| SourceUpdate | Remove `fetch_interval` |

### Modified Feed API

Feed items include `source_groups: [{id, name}]` for each item.

### Modified History API

- Batch response includes `groups: [{id, name}]` (aggregated from items)
- Item response includes `source_groups: [{id, name}]`

## UI Design

### Sources Page — Three Tabs

```
🟢 Active (12) | 🗑️ Trash (3) | 📁 Groups (4)
```

**Groups Tab:**
- Group cards with name, member count
- Inline edit group name
- Add/remove sources from group
- Delete group button

### Source Dialog (Add/Edit)

- **Removed:** fetch_interval dropdown
- **Added:** Multi-select group picker with "+ Create new group" inline input

### Feed Page

```
[ 全部 ] [ 科技 ] [ 設計 ] [ 商業 ]  ← Group filter chips
────────────────────────────────────
📰 Article 1  🏷️科技 🏷️設計
📰 Article 2  🏷️科技
```

### History Page

```
[ 全部群組 ▼ ]  ← Group filter
────────────────────────────────────
📁 Batch #42 (15 items) 🏷️科技 🏷️設計  [編輯][預覽][刪除][▼]
```

## Error Handling

- Duplicate group name → 409 Conflict
- Group/source not found → 404
- Source already in group → 400
- Delete group with members → 204 (sources preserved, membership removed via CASCADE)

## Testing Strategy

- **Backend unit tests:** SourceGroupService CRUD + membership
- **Backend API tests:** HTTP endpoints with status code verification
- **Frontend unit tests:** API client mocks, component tests
- **E2E tests:** Playwright — full user journeys
- **Backup/restore tests:** Verify groups survive export/import

## Migration Strategy

1. Alembic migration: DROP COLUMN fetch_interval, CREATE TABLE source_groups, CREATE TABLE source_group_members
2. Downgrade: restore fetch_interval column, drop new tables

## Rollback Plan

If issues arise:
1. `alembic downgrade -1` to restore previous schema
2. Frontend rollback via git revert
