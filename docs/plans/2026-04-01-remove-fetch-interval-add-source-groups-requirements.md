# Requirements Specification: Remove fetch_interval + Add Source Groups

> Date: 2026-04-01
> Status: Approved
> Author: Kimhsiao

## 1. Overview

This specification defines the requirements for removing the per-source `fetch_interval` feature and adding source group management to the RSS Aggregator project.

## 2. User Stories

### US-1: Manual-Only Source Refresh

**As a** user,
**I want** to manually trigger source refreshes only,
**So that** I have full control over when feeds are fetched.

**Acceptance Criteria:**
- [ ] AC-1.1: Source model no longer has `fetch_interval` field
- [ ] AC-1.2: SourceCreate API does not accept `fetch_interval`
- [ ] AC-1.3: SourceUpdate API does not accept `fetch_interval`
- [ ] AC-1.4: SourceResponse does not include `fetch_interval`
- [ ] AC-1.5: Scheduler does not auto-fetch based on `fetch_interval`
- [ ] AC-1.6: Manual refresh (`/sources/{id}/refresh`) still works
- [ ] AC-1.7: Manual refresh all (`/sources/refresh`) still works
- [ ] AC-1.8: SourceDialog UI does not show fetch_interval field

### US-2: Create and Manage Source Groups

**As a** user,
**I want** to create, rename, and delete source groups,
**So that** I can organize my sources into meaningful categories.

**Acceptance Criteria:**
- [ ] AC-2.1: User can create a group with a unique name
- [ ] AC-2.2: Duplicate group name returns error
- [ ] AC-2.3: User can rename an existing group
- [ ] AC-2.4: User can delete a group (sources are NOT deleted)
- [ ] AC-2.5: Groups tab appears in Sources page
- [ ] AC-2.6: Group list shows member count

### US-3: Assign Sources to Groups

**As a** user,
**I want** to assign sources to one or more groups when creating or editing them,
**So that** a source can appear in multiple categories.

**Acceptance Criteria:**
- [ ] AC-3.1: Source can belong to zero groups
- [ ] AC-3.2: Source can belong to multiple groups
- [ ] AC-3.3: Add Source dialog includes group multi-select
- [ ] AC-3.4: Edit Source dialog shows current group assignments
- [ ] AC-3.5: User can create a new group inline from the source dialog
- [ ] AC-3.6: Group membership is persisted to database

### US-4: Manage Group Members

**As a** user,
**I want** to add and remove sources from groups via the Groups tab,
**So that** I can reorganize sources without editing each one individually.

**Acceptance Criteria:**
- [ ] AC-4.1: Groups tab shows list of all groups
- [ ] AC-4.2: Each group card shows its member sources
- [ ] AC-4.3: User can add a source to a group from the group card
- [ ] AC-4.4: User can remove a source from a group from the group card
- [ ] AC-4.5: Adding duplicate membership returns error

### US-5: Filter Feed by Group

**As a** user,
**I want** to filter feed items by source group,
**So that** I can focus on content from specific categories.

**Acceptance Criteria:**
- [ ] AC-5.1: Feed page shows group filter chips at top
- [ ] AC-5.2: "All" chip shows items from all sources
- [ ] AC-5.3: Clicking a group chip filters to that group's sources only
- [ ] AC-5.4: Each feed item displays its source's group badges
- [ ] AC-5.5: Multi-group source shows multiple badges

### US-6: View Groups in History

**As a** user,
**I want** to see group information in fetch history,
**So that** I can understand which categories were fetched in each batch.

**Acceptance Criteria:**
- [ ] AC-6.1: History batch cards show involved group badges
- [ ] AC-6.2: Expanded batch items show source group badges
- [ ] AC-6.3: History page has group filter chips
- [ ] AC-6.4: Filtering by group shows only batches/items from that group

### US-7: Backup and Restore Groups

**As a** user,
**I want** my source groups to be included in backups,
**So that** I can restore my full configuration including group assignments.

**Acceptance Criteria:**
- [ ] AC-7.1: Export backup includes source_groups table data
- [ ] AC-7.2: Export backup includes source_group_members table data
- [ ] AC-7.3: Import backup restores source_groups
- [ ] AC-7.4: Import backup restores source_group_members
- [ ] AC-7.5: Merge import handles existing groups correctly

## 3. Technical Requirements

### 3.1 Database

- [ ] TR-1.1: New table `source_groups` with unique name constraint
- [ ] TR-1.2: New table `source_group_members` (junction, composite PK)
- [ ] TR-1.3: Remove `fetch_interval` column from `sources` table
- [ ] TR-1.4: Foreign keys with ON DELETE CASCADE for junction table
- [ ] TR-1.5: Alembic migration with upgrade and downgrade paths

### 3.2 Backend API

- [ ] TR-2.1: FastAPI routes for source group CRUD
- [ ] TR-2.2: FastAPI routes for group membership management
- [ ] TR-2.3: SourceResponse includes `groups` field
- [ ] TR-2.4: Feed items include `source_groups` field
- [ ] TR-2.5: History batches and items include group info
- [ ] TR-2.6: All endpoints require API key authentication

### 3.3 Frontend

- [ ] TR-3.1: Vue 3 components for group management
- [ ] TR-3.2: Three-tab Sources page (Active / Trash / Groups)
- [ ] TR-3.3: Group filter chips on Feed and History pages
- [ ] TR-3.4: Group badges on feed items and history items
- [ ] TR-3.5: i18n support for English and Chinese Traditional
- [ ] TR-3.6: Responsive design for desktop and mobile

### 3.4 Testing

- [ ] TR-4.1: Backend unit tests for SourceGroupService
- [ ] TR-4.2: Backend API integration tests for all new endpoints
- [ ] TR-4.3: Frontend API client unit tests
- [ ] TR-4.4: Frontend component tests
- [ ] TR-4.5: Playwright E2E tests for complete user journeys
- [ ] TR-4.6: Backup/restore tests for group data

### 3.5 TDD Compliance

- [ ] TR-5.1: All backend features follow test-first approach
- [ ] TR-5.2: All frontend features follow test-first approach
- [ ] TR-5.3: Tests must fail before implementation
- [ ] TR-5.4: Implementation must be minimal to pass tests

## 4. Non-Functional Requirements

- [ ] NFR-1: API response time < 200ms for group list endpoint
- [ ] NFR-2: No breaking changes to existing source CRUD (backward compatible except fetch_interval removal)
- [ ] NFR-3: All new code follows existing codebase conventions
- [ ] NFR-4: Zero type errors in TypeScript frontend
- [ ] NFR-5: All tests pass before merge

## 5. Out of Scope

- Per-group auto-fetch scheduling
- Nested/hierarchical groups
- Group-level permissions
- Bulk source import with group assignment
- Group color/icon customization

## 6. Success Criteria

- [ ] All acceptance criteria above are met
- [ ] Full test suite passes (backend + frontend + E2E)
- [ ] No regressions in existing functionality
- [ ] Documentation (README, CHANGELOG) updated
