# Remove fetch_interval + Add Source Groups — Task Index

> Date: 2026-04-01
> Status: Not Started

## Document Index

| Document | Path | Status |
|----------|------|--------|
| Requirements | `docs/plans/2026-04-01-remove-fetch-interval-add-source-groups-requirements.md` | ✅ Written |
| Design | `docs/plans/2026-04-01-remove-fetch-interval-add-source-groups-design.md` | ✅ Written |
| Implementation Plan | `docs/plans/2026-04-01-remove-fetch-interval-add-source-groups.md` | ✅ Written |

## Task Summary

| Task | Description | Phase | Status |
|------|-------------|-------|--------|
| 1 | Remove fetch_interval from Source model | Backend Model | ⬜ |
| 2 | Alembic migration + SourceGroup models | Backend Model | ⬜ |
| 3 | SourceGroupService with TDD | Backend Service | ⬜ |
| 4 | Source group API routes | Backend API | ⬜ |
| 5 | Remove fetch_interval from sources API + scheduler | Backend API | ⬜ |
| 6 | Include group info in sources, feed, history responses | Backend API | ⬜ |
| 7 | Update backup service for source groups | Backend Service | ⬜ |
| 8 | Update deps.py for all new services | Backend Infra | ⬜ |
| 9 | Update types and API client | Frontend Types | ⬜ |
| 10 | SourceDialog: remove fetch_interval, add group selection | Frontend Component | ⬜ |
| 11 | SourcesPage: add Groups tab | Frontend Page | ⬜ |
| 12 | FeedPage: add group filter chips | Frontend Page | ⬜ |
| 13 | HistoryPage: add group badges and filter | Frontend Page | ⬜ |
| 14 | i18n: add group translations | Frontend i18n | ⬜ |
| 15 | E2E tests with Playwright | Frontend E2E | ⬜ |
| 16 | Disable scheduler auto-fetch | Backend Config | ⬜ |
| 17 | Update documentation | Docs | ⬜ |
| 18 | Final verification | QA | ⬜ |

## Requirements Coverage

| Requirement | Covered By Tasks |
|-------------|-----------------|
| US-1: Manual-Only Refresh | Tasks 1, 5, 10, 16 |
| US-2: Create/Manage Groups | Tasks 2, 3, 4, 11 |
| US-3: Assign Sources to Groups | Tasks 2, 3, 4, 9, 10 |
| US-4: Manage Group Members | Tasks 3, 4, 11 |
| US-5: Filter Feed by Group | Tasks 6, 9, 12 |
| US-6: View Groups in History | Tasks 6, 9, 13 |
| US-7: Backup/Restore Groups | Task 7 |
| TR-1: Database | Tasks 1, 2 |
| TR-2: Backend API | Tasks 3, 4, 5, 6, 8 |
| TR-3: Frontend | Tasks 9, 10, 11, 12, 13, 14 |
| TR-4: Testing | Tasks 1-15 (all include tests) |
| TR-5: TDD | All tasks follow test-first pattern |
