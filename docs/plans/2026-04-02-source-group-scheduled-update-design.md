# Source Group Scheduled Update — Design Document

> Date: 2026-04-02
> Status: Pending Approval
> Author: Kimhsiao

## Problem Statement

目前 Source Group 只能透過手動方式觸發更新（`/source-groups/{id}/refresh`），缺少自動排程功能。使用者希望能像 cron 一樣設定定時自動更新，但不需要學習複雜的 cron 語法。

## Goals

1. **定時自動更新** — 讓每個 Group 可以設定多組排程，時間到自動更新該群組的所有 Sources
2. **直覺 UI** — 圖形化勾選方式設定時間，不需要理解 cron syntax
3. **快捷設定** — 支援常用間隔（每15分鐘、每天等）快速設定
4. **下次執行時間** — 讓使用者能看到下次什麼時候會執行

## Non-Goals

- 不實作日曆檢視（calendar view）
- 不實作巢狀排程（cron chains）
- 不實作 per-source 排程（僅 per-group）
- 不實作排程執行歷史紀錄（除了 fetch batch）

## Architecture Decisions

### Decision 1: Cron Expression Storage

**Chosen:** 存儲完整的 cron expression 字串（如 `25,27 11,12 * * 3,6`）

**Alternatives considered:**
- 存儲 JSON 結構（`{minutes: [], hours: [], weekdays: []}`）— rejected：增加複雜度，需要額外翻譯
- 存儲 minutes/hours/weekdays 分開的欄位 — rejected：查詢和修改困難

**Reasoning:** Cron expression 是標準格式，便於擴展和外部工具整合。

### Decision 2: Scheduler Implementation

**Chosen:** 新建獨立的 `ScheduleScheduler` class，與現有 `FetchScheduler` 分離

**Alternatives considered:**
- 擴展現有 FetchScheduler — rejected：職責會變得太複雜
- 每分鐘輪詢資料庫所有排程 — rejected：效能太差

**Reasoning:**
- ScheduleScheduler 專責排程管理，職責單一
- 使用 croniter 計算下次執行時間，精確且高效
- 每分鐘檢查一次，執行精確到分鐘

### Decision 3: UI Mode Toggle

**Chosen:** Radio button 切換 Quick/Detailed 模式，選擇一個停用另一個

**Alternatives considered:**
- 兩者皆可同時使用 — rejected：邏輯衝突，使用者困惑
- Tabs 切換 — rejected：Radio 更直覺，表達「二選一」

**Reasoning:** 明確的互斥關係，避免設定衝突。

### Decision 4: Duplicate Detection

**Chosen:** 儲存前檢查 cron expression 是否與現有排程完全相同

**Alternatives considered:**
- 允許重複執行 — rejected：浪費資源，可能造成問題
- 允許但標記 warning — rejected：不是預期行為

**Reasoning:** 簡單明確的檢查邏輯，使用者容易理解。

## Data Model

### source_group_schedules

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | Integer | PK, auto-increment | Primary key |
| group_id | Integer | FK → source_groups.id, ON DELETE CASCADE | Reference to group |
| cron_expression | String(100) | NOT NULL, CHECK format | Cron expression |
| is_enabled | Boolean | DEFAULT true | Enable/disable flag |
| next_run_at | DateTime | NULL | Next execution time |
| created_at | DateTime | NOT NULL | Creation timestamp |
| updated_at | DateTime | NOT NULL | Last update timestamp |

### Indexes

```sql
CREATE INDEX idx_schedules_is_enabled ON source_group_schedules(is_enabled);
CREATE UNIQUE INDEX idx_schedules_group_cron ON source_group_schedules(group_id, cron_expression);
```

## API Design

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/source-groups/{group_id}/schedules` | List all schedules for a group |
| POST | `/api/v1/source-groups/{group_id}/schedules` | Create new schedule |
| PUT | `/api/v1/source-groups/{group_id}/schedules/{id}` | Update schedule |
| DELETE | `/api/v1/source-groups/{group_id}/schedules/{id}` | Delete schedule |
| PATCH | `/api/v1/source-groups/{group_id}/schedules/{id}/toggle` | Toggle enable/disable |

### Schemas

#### ScheduleResponse
```json
{
  "id": 1,
  "group_id": 1,
  "cron_expression": "25,27 11,12 * * 3,6",
  "is_enabled": true,
  "next_run_at": "2026-04-03T11:25:00",
  "created_at": "2026-04-02T10:00:00",
  "updated_at": "2026-04-02T10:00:00"
}
```

#### ScheduleCreate
```json
{
  "cron_expression": "25,27 11,12 * * 3,6"
}
```

#### ScheduleUpdate
```json
{
  "cron_expression": "30 8 * * *"
}
```

## Cron Expression Format

Standard 5-field cron: `minute hour day month weekday`

| Field | Range | Example |
|-------|-------|---------|
| minute | 0-59 | `25,27` or `*` or `*/15` |
| hour | 0-23 | `11,12` or `*` or `*/3` |
| day | 1-31 | `*` (not used) |
| month | 1-12 | `*` (not used) |
| weekday | 0-6 | `3,6` (Wed, Sat) |

### Quick Settings Mapping

| Quick Setting | Cron Expression | Description |
|---------------|-----------------|-------------|
| 每 15 分鐘 | `*/15 * * * *` | Every 15 minutes |
| 每 30 分鐘 | `*/30 * * * *` | Every 30 minutes |
| 每 1 小時 | `0 * * * *` | Every hour at :00 |
| 每 3 小時 | `0 */3 * * *` | Every 3 hours at :00 |
| 每 6 小時 | `0 */6 * * *` | Every 6 hours at :00 |
| 每 12 小時 | `0 */12 * * *` | Every 12 hours at :00 |
| 每天 | `30 8 * * *` | Daily at 08:30 |

## Human-Readable Preview

### Translation Rules

1. **Minutes**
   - `*` → 每分鐘
   - `*/N` → 每 N 分鐘
   - `M,N` → M、N 分

2. **Hours**
   - `*` → 每小時
   - `*/N` → 每 N 小時
   - `H1,H2` → H1點、H2點

3. **Weekdays**
   - `*` → 每天
   - `0` → 週日
   - `1` → 週一
   - `2` → 週二
   - `3` → 週三
   - `4` → 週四
   - `5` → 週五
   - `6` → 週六

### Examples

| Cron Expression | Preview |
|-----------------|---------|
| `25,27 11,12 * * 3,6` | 每週三、六 11:13, 11:27, 12:13, 12:27 |
| `30 8 * * *` | 每天 08:30 |
| `*/15 * * * *` | 每 15 分鐘 |
| `0 */3 * * *` | 每 3 小時 |

## Scheduler Implementation

### ScheduleScheduler Class

```python
class ScheduleScheduler:
    """Scheduler for executing source group schedules."""

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        fetch_scheduler: FetchScheduler,
    ) -> None:
        self.session_factory = session_factory
        self.fetch_scheduler = fetch_scheduler
        self._running = False
        self._task: asyncio.Task | None = None

    async def start(self) -> None:
        """Start the scheduler."""
        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info("Schedule scheduler started")

    async def _run_loop(self) -> None:
        """Main loop - check every minute."""
        while self._running:
            await self._check_and_execute()
            await asyncio.sleep(60)

    async def _check_and_execute(self) -> None:
        """Check and execute due schedules."""
        from src.models import SourceGroupSchedule
        from croniter import croniter

        async with self.session_factory() as session:
            # Find enabled schedules that are due
            now = get_now()
            result = await session.execute(
                select(SourceGroupSchedule).where(
                    SourceGroupSchedule.is_enabled == True,
                    SourceGroupSchedule.next_run_at <= now,
                )
            )
            schedules = list(result.scalars().all())

            for schedule in schedules:
                await self._execute_schedule(schedule)

    async def _execute_schedule(self, schedule: SourceGroupSchedule) -> None:
        """Execute a single schedule - refresh the group."""
        await self.fetch_scheduler.refresh_group(schedule.group_id)
        
        # Update next_run_at
        schedule.next_run_at = self._calculate_next_run(schedule.cron_expression)
        await session.commit()
```

### Next Run Calculation

```python
def calculate_next_run(cron_expression: str, from_time: datetime | None = None) -> datetime:
    """Calculate next run time from cron expression."""
    from croniter import croniter
    
    base_time = from_time or get_now()
    cron = croniter(cron_expression, base_time)
    return cron.get_next(datetime)
```

## UI Design

### Layout in SourcesPage - Groups Tab

```
┌─────────────────────────────────────────────────────────┐
│ 📁 群組名稱                    [刷新] [預覽] [編輯] [刪除] ▼ │
├─────────────────────────────────────────────────────────┤
│ 成員數: 5                                                     │
├─────────────────────────────────────────────────────────┤
│ ⚙️ 定時更新 (collapsible)                                   │
├─────────────────────────────────────────────────────────┤
│ ○ 快捷設定    ○ 詳細設定                                    │
├─────────────────────────────────────────────────────────┤
│ [快捷選項 ▼]                                                │
│   └ 每 15 分鐘 / 每 30 分鐘 / 每 1 小時 / 每 3 小時 /      │
│     每 6 小時 / 每 12 小時 / 每天 (08:30)                   │
├─────────────────────────────────────────────────────────┤
│ 詳细設定（非快捷模式時啟用）:                                │
│   分鐘: [■13 □27 □其他...]                                  │
│   小時: [■11 □12 □其他...]                                  │
│   星期: [■3(週三) □6(週六)]                                 │
│                                                         │
│   預覽: 每週三、六 11:13、11:27、12:13、12:27              │
├─────────────────────────────────────────────────────────┤
│ [+ 新增排程]  [儲存]                                        │
├─────────────────────────────────────────────────────────┤
│ 已設定排程:                                                  │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ 🕐 每週三、六 11:13, 12:27  │ 04/03 11:25 下次執行  │ │
│ │    [開啟/關閉] [編輯] [刪除]                          │ │
│ └─────────────────────────────────────────────────────┘ │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ 🕐 每天 08:30               │ 04/03 08:30 下次執行  │ │
│ │    [關閉] [編輯] [刪除]                              │ │
│ └─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

### Component Structure

- `ScheduleConfigPanel.vue` - Main component for schedule settings
  - `ScheduleModeToggle.vue` - Radio toggle for Quick/Detailed
  - `ScheduleQuickSettings.vue` - Dropdown for quick settings
  - `ScheduleDetailedSettings.vue` - Multi-select checkboxes
  - `SchedulePreview.vue` - Human-readable preview
  - `ScheduleList.vue` - List of configured schedules
    - `ScheduleItem.vue` - Individual schedule display with toggle/edit/delete

## Validation Rules

### Cron Expression Validation

```python
def validate_cron_expression(cron: str) -> bool:
    """Validate cron expression format."""
    from croniter import croniter
    from datetime import datetime
    
    try:
        # Must have exactly 5 fields
        parts = cron.split()
        if len(parts) != 5:
            return False
        
        # Must be valid croniter expression
        croniter(cron, datetime.now())
        return True
    except (ValueError, KeyError):
        return False
```

### Duplicate Check

```python
async def check_duplicate_schedule(
    session: AsyncSession,
    group_id: int,
    cron_expression: str,
    exclude_id: int | None = None,
) -> bool:
    """Check for duplicate cron expression in same group."""
    query = select(SourceGroupSchedule).where(
        SourceGroupSchedule.group_id == group_id,
        SourceGroupSchedule.cron_expression == cron_expression,
    )
    if exclude_id:
        query = query.where(SourceGroupSchedule.id != exclude_id)
    
    result = await session.execute(query)
    return result.scalar_one_or_none() is not None
```

## Dependencies

### Python Packages

- `croniter>=1.4.0` - Cron expression parsing and next run calculation

### Installation

```bash
uv add croniter
```

## Testing Strategy

### Unit Tests

1. **test_cron_validation** - Validate cron expression format
2. **test_calculate_next_run** - Next run time calculation
3. **test_human_readable_preview** - Preview generation
4. **test_schedule_crud** - Create, read, update, delete operations
5. **test_duplicate_detection** - Duplicate schedule detection

### Integration Tests

1. **test_create_schedule_api** - POST /schedules
2. **test_list_schedules_api** - GET /schedules
3. **test_update_schedule_api** - PUT /schedules/{id}
4. **test_delete_schedule_api** - DELETE /schedules/{id}
5. **test_toggle_schedule_api** - PATCH /schedules/{id}/toggle
6. **test_duplicate_rejection** - Duplicate cron rejection

### E2E Tests (Playwright)

1. **test_quick_settings_workflow** - Select quick setting, save, verify
2. **test_detailed_settings_workflow** - Configure detailed, save, verify
3. **test_mode_toggle_disables_opposite** - Toggle disables other panel
4. **test_schedule_list_displays_correctly** - List shows schedules
5. **test_enable_disable_toggle** - Toggle changes state
6. **test_edit_schedule** - Edit existing schedule
7. **test_delete_schedule** - Delete schedule with confirmation

## Out of Scope

- Calendar view visualization
- Nested schedules / cron chains
- Per-source schedules
- Schedule execution history beyond fetch batch
- Multi-timezone support (use app timezone only)