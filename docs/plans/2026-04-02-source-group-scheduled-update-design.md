# Source Group Scheduled Update — Design Document

> Date: 2026-04-02
> Status: Pending Approval
> Author: Kimhsiao

## Problem Statement

Currently, Source Groups can only be manually refreshed via API or UI (`/source-groups/{id}/refresh`). Users need automated scheduled updates similar to cron, but without learning complex cron syntax.

## Goals

1. **Automated Scheduled Updates** — Each group can have multiple schedules (max 10), triggering automatic refresh of all sources in the group when the schedule runs
2. **Intuitive UI** — Checkbox-based time selection UI without requiring understanding of cron syntax
3. **Quick Settings** — Predefined intervals (every 15 min, daily, etc.) for quick configuration
4. **Next Run Time** — Display when a schedule will next execute

## Non-Goals

- Calendar view of schedule triggers
- Nested schedules (cron chains)
- Per-source schedules (group-level only)
- Schedule execution history beyond fetch batch

## Architecture Decisions

### Decision 1: Cron Expression Storage

**Chosen:** Store complete cron expression string (e.g., `25,27 11,12 * * 3,6`)

**Alternatives considered:**
- Store JSON structure (`{minutes: [], hours: [], weekdays: []}`) — rejected: adds complexity, requires additional translation
- Store minutes/hours/weekdays as separate columns — rejected: difficult to query and modify

**Reasoning:** Cron expression is a standard format, easy to extend and integrate with external tools.

### Decision 2: Scheduler Implementation

**Chosen:** Create standalone `ScheduleScheduler` class, separate from existing `FetchScheduler`

**Alternatives considered:**
- Extend existing FetchScheduler — rejected: responsibilities would become too complex
- Poll database every minute for all schedules — rejected: poor performance

**Reasoning:**
- ScheduleScheduler is dedicated to schedule management, single responsibility
- Use croniter for precise next run time calculation
- Check every minute, execution precise to the minute

### Decision 3: UI Mode Toggle

**Chosen:** Radio button to toggle Quick/Detailed mode, selecting one disables the other

**Alternatives considered:**
- Allow both to be used simultaneously — rejected: logic conflict, confusing for users
- Tabs to switch — rejected: Radio is more intuitive, expresses "choose one of two"

**Reasoning:** Clear mutual exclusivity, prevents configuration conflicts.

### Decision 4: Duplicate Detection

**Chosen:** Check for duplicate cron expression before saving

**Alternatives considered:**
- Allow duplicates to run — rejected: wastes resources, may cause issues
- Allow but mark warning — rejected: unexpected behavior

**Reasoning:** Simple and clear check logic, easy for users to understand.

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
| Every 15 min | `*/15 * * * *` | Every 15 minutes |
| Every 30 min | `*/30 * * * *` | Every 30 minutes |
| Every 1 hour | `0 * * * *` | Every hour at :00 |
| Every 3 hours | `0 */3 * * *` | Every 3 hours at :00 |
| Every 6 hours | `0 */6 * * *` | Every 6 hours at :00 |
| Every 12 hours | `0 */12 * * *` | Every 12 hours at :00 |
| Daily | `30 8 * * *` | Daily at 08:30 |

## Human-Readable Preview

### Translation Rules

1. **Minutes**
   - `*` → Every minute
   - `*/N` → Every N minutes
   - `M,N` → M, N minutes

2. **Hours**
   - `*` → Every hour
   - `*/N` → Every N hours
   - `H1,H2` → H1, H2 o'clock

3. **Weekdays**
   - `*` → Daily
   - `0` → Sunday
   - `1` → Monday
   - `2` → Tuesday
   - `3` → Wednesday
   - `4` → Thursday
   - `5` → Friday
   - `6` → Saturday

### Examples

| Cron Expression | Preview |
|-----------------|---------|
| `25,27 11,12 * * 3,6` | Every Wed, Sat at 11:13, 11:27, 12:13, 12:27 |
| `30 8 * * *` | Daily at 08:30 |
| `*/15 * * * *` | Every 15 minutes |
| `0 */3 * * *` | Every 3 hours |

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
+-------------------------------------------------------------+
| [Group Name]                 [Refresh] [Preview] [Edit] [Delete] v |
+-------------------------------------------------------------+
| Members: 5                                                      |
+-------------------------------------------------------------+
| [Scheduled Update (collapsible)]                              |
+-------------------------------------------------------------+
| (o) Quick Settings    ( ) Detailed Settings                  |
+-------------------------------------------------------------+
| [Quick Options v]                                             |
|    Every 15 min / Every 30 min / Every 1 hour /              |
|    Every 3 hours / Every 6 hours / Every 12 hours /          |
|    Daily (08:30)                                              |
+-------------------------------------------------------------+
| Detailed Settings (enabled when not in Quick mode):          |
|   Minutes: [x]13 [ ]27 [ ]other...                           |
|   Hours: [x]11 [x]12 [ ]other...                             |
|   Weekdays: [x]3(Wed) [x]6(Sat)                              |
|                                                               |
|   Preview: Every Wed, Sat at 11:13, 11:27, 12:13, 12:27     |
+-------------------------------------------------------------+
| [+ Add Schedule]  [Save]                                      |
+-------------------------------------------------------------+
| Configured Schedules:                                         |
| +---------------------------------------------------------------+
| | [Clock] Every Wed, Sat 11:13, 12:27 | 04/03 11:25 next     | |
| |    [Enable/Disable] [Edit] [Delete]                          | |
| +---------------------------------------------------------------+
| +---------------------------------------------------------------+
| | [Clock] Daily 08:30              | 04/03 08:30 next        | |
| |    [Disable] [Edit] [Delete]                                | |
| +---------------------------------------------------------------+
+-------------------------------------------------------------+
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