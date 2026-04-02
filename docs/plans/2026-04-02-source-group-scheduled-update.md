# Source Group Scheduled Update — Task Index

> Date: 2026-04-02
> Status: Not Started

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add scheduled update functionality to source groups, allowing users to configure cron-like schedules for automatic feed refreshing with an intuitive UI.

**Architecture:** New table `source_group_schedules` for storing cron expressions. New ScheduleScheduler class for execution. Web UI adds schedule configuration panel in Groups tab with Quick/Detailed mode toggle.

**Tech Stack:** Python 3.12+, FastAPI, SQLAlchemy 2.0, Alembic, croniter, Vue 3 + TypeScript, Pinia, vue-i18n, Playwright, pytest

---

## Document Index

| Document | Path | Status |
|----------|------|--------|
| Requirements | `docs/plans/2026-04-02-source-group-scheduled-update-requirements.md` | ✅ Written |
| Design | `docs/plans/2026-04-02-source-group-scheduled-update-design.md` | ✅ Written |
| Implementation Tasks | `docs/plans/2026-04-02-source-group-scheduled-update-tasks.md` | ✅ Written |

## Quick Reference

### Task Overview

| # | Task | Phase |
|---|------|-------|
| 1 | Install croniter dependency | Backend Deps |
| 2 | Create SourceGroupSchedule model | Backend Model |
| 3 | Alembic migration for schedules table | Backend Migration |
| 4 | Create SourceGroupScheduleService | Backend Service |
| 5 | Create schedule API routes | Backend API |
| 6 | Create ScheduleScheduler class | Backend Scheduler |
| 7 | Add scheduler to startup | Backend Infra |
| 8 | Update deps.py | Backend Infra |
| 9 | Add schedule types and API client | Frontend Types |
| 10 | Create ScheduleConfigPanel component | Frontend Component |
| 11 | Add i18n translations | Frontend i18n |
| 12 | Integrate in SourcesPage | Frontend Page |
| 13 | Unit tests for cron validation | Backend Test |
| 14 | Unit tests for schedule service | Backend Test |
| 15 | Playwright E2E tests | Frontend E2E |
| 16 | Update documentation | Docs |
| 17 | Final verification | QA |

### Key Files to Modify/Create

**Backend:**
- `src/models/source_group_schedule.py` (new)
- `src/services/source_group_schedule_service.py` (new)
- `src/api/routes/schedule.py` (new)
- `src/scheduler/schedule_scheduler.py` (new)
- `alembic/versions/<rev>_add_source_group_schedules.py` (new)

**Frontend:**
- `src/types/schedule.ts` (new)
- `src/api/schedules.ts` (new)
- `src/components/ScheduleConfigPanel.vue` (new)
- `src/components/ScheduleItem.vue` (new)
- `src/pages/SourcesPage.vue` (modify)
- `src/locales/en.json` (modify)
- `src/locales/zh-TW.json` (modify)

**Tests:**
- `tests/models/test_source_group_schedule.py` (new)
- `tests/services/test_source_group_schedule_service.py` (new)
- `tests/api/test_schedules.py` (new)
- `tests/test_cron_validation.py` (new)
- `tests/e2e/schedule.spec.ts` (new)

### Dependencies

- `croniter>=1.4.0` (Python)

---

For detailed implementation steps, see `docs/plans/2026-04-02-source-group-scheduled-update-tasks.md`