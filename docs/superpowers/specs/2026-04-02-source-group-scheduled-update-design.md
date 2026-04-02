# Source Group Scheduled Update Design

## Overview

Add scheduled update functionality for source groups, allowing users to configure cron-like schedules for automatic feed refreshing. Each group can have multiple schedules (max 10) with enable/disable toggle and next run time display.

## Background

Currently, users can manually refresh sources in a group via the API or UI. This feature adds automated scheduled updates with an intuitive UI that abstracts the cron syntax while supporting full cron expressions.

## Requirements

### Functional Requirements

1. **Schedule Management**
   - Each source group can have multiple schedules (max 10)
   - Each schedule has: cron expression, enabled/disabled toggle, next run time
   - Schedules persist in database

2. **Quick Settings**
   - Predefined intervals: every 15 min, 30 min, 1 hour, 3 hours, 6 hours, 12 hours, daily
   - Daily default: 08:30 AM

3. **Detailed Settings**
   - Minutes: 0-59, multi-select
   - Hours: 0-23, multi-select
   - Weekdays: 0-6 (Sun-Sat), multi-select
   - Auto-generate cron expression from selections

4. **Validation**
   - No duplicate schedules in same group (same cron expression or overlapping times)
   - Max 10 schedules per group

5. **Execution**
   - When schedule triggers, refresh all sources in the group
   - Use croniter for next run time calculation

### UI Requirements

1. **Mode Toggle**
   - Radio button: Quick Settings / Detailed Settings
   - Selecting one disables the other

2. **Quick Settings Panel**
   - Dropdown with predefined intervals
   - Cron expression auto-generated

3. **Detailed Settings Panel**
   - Multi-select checkboxes for minutes, hours, weekdays
   - Live preview of human-readable schedule

4. **Schedule List**
   - Show all schedules with next run time
   - Enable/disable toggle per schedule
   - Edit and delete actions per schedule

5. **Naming**
   - Feature name: "定時更新" (Scheduled Update)

## Data Model

### New Table: source_group_schedules

| Column | Type | Description |
|--------|------|-------------|
| id | Integer (PK) | Auto-increment |
| group_id | Integer (FK) | Reference to source_groups |
| cron_expression | String(100) | Cron expression (e.g., "25,27 11,12 * * 3,6") |
| is_enabled | Boolean | Schedule enabled status |
| next_run_at | DateTime | Next execution time (nullable) |
| created_at | DateTime | Creation timestamp |
| updated_at | DateTime | Last update timestamp |

## API Design

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/source-groups/{group_id}/schedules` | List all schedules for a group |
| POST | `/api/v1/source-groups/{group_id}/schedules` | Create new schedule |
| PUT | `/api/v1/source-groups/{group_id}/schedules/{id}` | Update schedule |
| DELETE | `/api/v1/source-groups/{group_id}/schedules/{id}` | Delete schedule |
| PATCH | `/api/v1/source-groups/{group_id}/schedules/{id}/toggle` | Toggle enable/disable |

### Request/Response Schemas

#### POST /api/v1/source-groups/{group_id}/schedules

Request:
```json
{
  "cron_expression": "25,27 11,12 * * 3,6"
}
```

Response:
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

## Scheduler Implementation

### New Component: ScheduleScheduler

- Load all enabled schedules from database on startup
- Use `croniter` library to calculate next run times
- Check every minute if any schedule should execute
- Execute group refresh via existing `FetchScheduler.refresh_group()`

### Cron Expression Format

Standard 5-field cron: `minute hour day month weekday`

| Field | Range | Example |
|-------|-------|---------|
| minute | 0-59 | `25,27` |
| hour | 0-23 | `11,12` |
| day | 1-31 | `*` (any) |
| month | 1-12 | `*` (any) |
| weekday | 0-6 | `3,6` (Wed, Sat) |

### Quick Settings Mapping

| Quick Setting | Cron Expression |
|---------------|-----------------|
| Every 15 min | `*/15 * * * *` |
| Every 30 min | `*/30 * * * *` |
| Every 1 hour | `0 * * * *` |
| Every 3 hours | `0 */3 * * *` |
| Every 6 hours | `0 */6 * * *` |
| Every 12 hours | `0 */12 * * *` |
| Daily (08:30) | `30 8 * * *` |

## Human-Readable Preview

Generate readable text from cron expression:

- `25,27 11,12 * * 3,6` → "每週三、六 11:13, 11:27, 12:13, 12:27"
- `30 8 * * *` → "每天 08:30"

## Validation Rules

1. **Duplicate Check**: Before saving, verify cron expression doesn't match any existing schedule in the same group
2. **Max Limit**: Reject if group already has 10 schedules
3. **Cron Validity**: Validate cron expression format before saving
4. **Next Run Calculation**: Update `next_run_at` on save, toggle, or scheduler tick

## Testing Requirements

### Unit Tests
- Cron expression parsing and validation
- Human-readable preview generation
- Schedule CRUD operations
- Duplicate schedule detection

### E2E Tests (Playwright)
- Quick settings selection and save
- Detailed settings multi-select and save
- Mode toggle disables opposite panel
- Schedule list displays with correct info
- Enable/disable toggle works
- Edit and delete schedule

### Integration
- Schedule triggers group refresh at correct time
- Next run time updates correctly

## Deployment

After implementation:
1. Rebuild Docker images
2. Rebuild macOS desktop app
3. Deploy for user testing