# Requirements Specification: Source Group Scheduled Update

> Date: 2026-04-02
> Status: Pending Approval
> Author: Kimhsiao

## 1. Overview

This specification defines the requirements for adding scheduled update functionality to source groups. Users can configure cron-like schedules for automatic feed refreshing with an intuitive UI that abstracts the cron syntax.

## 2. User Stories

### US-1: Quick Schedule Setup

**As a** user,
**I want** to set up a schedule using predefined intervals,
**So that** I can quickly configure automatic updates without understanding cron syntax.

**Acceptance Criteria:**
- [ ] AC-1.1: Quick settings dropdown shows: every 15 min, 30 min, 1 hour, 3 hours, 6 hours, 12 hours, daily
- [ ] AC-1.2: Selecting a quick setting auto-generates the cron expression
- [ ] AC-1.3: Daily default is 08:30 AM
- [ ] AC-1.4: Quick setting selection clears detailed settings

### US-2: Detailed Schedule Setup

**As a** user,
**I want** to configure detailed schedule with minute, hour, and weekday selections,
**So that** I can create custom schedules like "every Wednesday and Saturday at 11:13 and 12:27".

**Acceptance Criteria:**
- [ ] AC-2.1: Minutes selector shows 0-59 with checkboxes, supports multi-select
- [ ] AC-2.2: Hours selector shows 0-23 with checkboxes, supports multi-select
- [ ] AC-2.3: Weekday selector shows Sun-Sat with checkboxes, supports multi-select
- [ ] AC-2.4: Selecting detailed settings clears quick settings
- [ ] AC-2.5: Human-readable preview updates in real-time

### US-3: Multiple Schedules Per Group

**As a** user,
**I want** to create multiple schedules for the same group,
**So that** I can have different update frequencies for different times.

**Acceptance Criteria:**
- [ ] AC-3.1: Maximum 10 schedules per group
- [ ] AC-3.2: Each schedule shows cron expression
- [ ] AC-3.3: Each schedule shows next run time
- [ ] AC-3.4: User can view list of all schedules in a group
- [ ] AC-3.5: User can add new schedule to existing schedules

### US-4: Enable/Disable Schedules

**As a** user,
**I want** to temporarily disable a schedule without deleting it,
**So that** I can pause automatic updates without re-creating the schedule later.

**Acceptance Criteria:**
- [ ] AC-4.1: Each schedule has an enable/disable toggle
- [ ] AC-4.2: Disabled schedules do not execute
- [ ] AC-4.3: Toggle persists in database
- [ ] AC-4.4: UI reflects current enabled/disabled state

### US-5: Schedule Validation

**As a** user,
**I want** to be prevented from creating duplicate schedules,
**So that** I don't accidentally set up conflicting update times.

**Acceptance Criteria:**
- [ ] AC-5.1: Cannot save schedule with same cron expression as existing schedule in same group
- [ ] AC-5.2: Cannot save schedule with overlapping time slots in same group
- [ ] AC-5.3: Error message clearly explains the conflict
- [ ] AC-5.4: Max 10 schedules per group - shows error when exceeded

### US-6: View Next Run Time

**As a** user,
**I want** to see when a schedule will next execute,
**So that** I can verify my configuration is correct.

**Acceptance Criteria:**
- [ ] AC-6.1: Next run time displayed for each schedule
- [ ] AC-6.2: Next run time updates when schedule is modified
- [ ] AC-6.3: Next run time updates after schedule executes
- [ ] AC-6.4: If schedule is disabled, next run time shows "—"

### US-7: Edit and Delete Schedules

**As a** user,
**I want** to modify or remove existing schedules,
**So that** I can adjust my automation setup as needed.

**Acceptance Criteria:**
- [ ] AC-7.1: User can edit existing schedule (change cron expression)
- [ ] AC-7.2: User can delete a schedule with confirmation
- [ ] AC-7.3: After edit, next run time recalculates
- [ ] AC-7.4: After delete, schedule no longer executes

### US-8: Schedule Execution

**As a** user,
**I want** the system to automatically refresh all sources in a group when a schedule triggers,
**So that** I don't need to manually trigger updates.

**Acceptance Criteria:**
- [ ] AC-8.1: When schedule triggers, refresh all sources in the group
- [ ] AC-8.2: Schedule execution happens at correct time
- [ ] AC-8.3: Execution creates a fetch batch record
- [ ] AC-8.4: After execution, next run time recalculates

## 3. Technical Requirements

### 3.1 Database

- [ ] TR-1.1: New table `source_group_schedules` with cron_expression, is_enabled, next_run_at
- [ ] TR-1.2: Foreign key to source_groups with ON DELETE CASCADE
- [ ] TR-1.3: Unique constraint on (group_id, cron_expression)
- [ ] TR-1.4: Alembic migration with upgrade and downgrade
- [ ] TR-1.5: Index on is_enabled for scheduler query performance

### 3.2 Backend API

- [ ] TR-2.1: GET `/api/v1/source-groups/{group_id}/schedules` - list all schedules
- [ ] TR-2.2: POST `/api/v1/source-groups/{group_id}/schedules` - create schedule
- [ ] TR-2.3: PUT `/api/v1/source-groups/{group_id}/schedules/{id}` - update schedule
- [ ] TR-2.4: DELETE `/api/v1/source-groups/{group_id}/schedules/{id}` - delete schedule
- [ ] TR-2.5: PATCH `/api/v1/source-groups/{group_id}/schedules/{id}/toggle` - toggle enable/disable
- [ ] TR-2.6: Validate cron expression format before saving
- [ ] TR-2.7: Check for duplicate cron expression in same group before saving

### 3.3 Scheduler

- [ ] TR-3.1: New ScheduleScheduler class that loads enabled schedules
- [ ] TR-3.2: Use croniter library for next run time calculation
- [ ] TR-3.3: Check every minute if any schedule should execute
- [ ] TR-3.4: Execute group refresh via existing FetchScheduler.refresh_group()
- [ ] TR-3.5: Update next_run_at after execution

### 3.4 Frontend

- [ ] TR-4.1: Schedule settings UI in Groups tab
- [ ] TR-4.2: Radio toggle between Quick and Detailed modes
- [ ] TR-4.3: Quick settings dropdown with predefined intervals
- [ ] TR-4.4: Detailed settings with multi-select checkboxes
- [ ] TR-4.5: Human-readable preview display
- [ ] TR-4.6: Schedule list with next run time and toggle
- [ ] TR-4.7: Edit and delete schedule functionality
- [ ] TR-4.8: i18n support for English and Chinese Traditional

### 3.5 Testing

- [ ] TR-5.1: Backend unit tests for cron expression parsing and validation
- [ ] TR-5.2: Backend unit tests for schedule CRUD operations
- [ ] TR-5.3: Backend unit tests for duplicate detection
- [ ] TR-5.4: Backend integration tests for all API endpoints
- [ ] TR-5.5: Playwright E2E tests for quick settings workflow
- [ ] TR-5.6: Playwright E2E tests for detailed settings workflow
- [ ] TR-5.7: Playwright E2E tests for enable/disable toggle
- [ ] TR-5.8: Playwright E2E tests for edit and delete

### 3.6 TDD Compliance

- [ ] TR-6.1: All backend features follow test-first approach
- [ ] TR-6.2: All frontend features follow test-first approach
- [ ] TR-6.3: Tests must fail before implementation
- [ ] TR-6.4: Implementation must be minimal to pass tests

## 4. Non-Functional Requirements

- [ ] NFR-1: API response time < 200ms for schedule list endpoint
- [ ] NFR-2: Scheduler tick must not miss scheduled executions
- [ ] NFR-3: All new code follows existing codebase conventions
- [ ] NFR-4: Zero type errors in TypeScript frontend
- [ ] NFR-5: All tests pass before merge

## 5. Out of Scope

- Calendar view of schedule triggers
- Nested schedules (cron chains)
- Per-source schedules (only per-group)
- Schedule execution history/log beyond fetch batch

## 6. Success Criteria

- [ ] All acceptance criteria above are met
- [ ] Full test suite passes (backend + frontend + E2E)
- [ ] No regressions in existing functionality
- [ ] Documentation (README, CHANGELOG) updated