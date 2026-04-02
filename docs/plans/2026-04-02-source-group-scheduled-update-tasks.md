# Source Group Scheduled Update — Task Index

> Date: 2026-04-02
> Status: Not Started

## Document Index

| Document | Path | Status |
|----------|------|--------|
| Requirements | `docs/plans/2026-04-02-source-group-scheduled-update-requirements.md` | ✅ Written |
| Design | `docs/plans/2026-04-02-source-group-scheduled-update-design.md` | ✅ Written |

## Task Summary

| Task | Description | Phase | Status |
|------|-------------|-------|--------|
| 1 | Install croniter dependency | Backend Deps | ⬜ |
| 2 | Create SourceGroupSchedule model | Backend Model | ⬜ |
| 3 | Alembic migration for schedules table | Backend Migration | ⬜ |
| 4 | Create SourceGroupScheduleService | Backend Service | ⬜ |
| 5 | Create schedule API routes | Backend API | ⬜ |
| 6 | Create ScheduleScheduler class | Backend Scheduler | ⬜ |
| 7 | Add croniter to scheduler startup | Backend Infra | ⬜ |
| 8 | Update deps.py for new services | Backend Infra | ⬜ |
| 9 | Add schedule types and API client | Frontend Types | ⬜ |
| 10 | Create ScheduleConfigPanel component | Frontend Component | ⬜ |
| 11 | Create schedule-related i18n keys | Frontend i18n | ⬜ |
| 12 | Integrate schedule UI in SourcesPage | Frontend Page | ⬜ |
| 13 | Unit tests for cron validation | Backend Test | ⬜ |
| 14 | Unit tests for schedule service | Backend Test | ⬜ |
| 15 | Playwright E2E tests | Frontend E2E | ⬜ |
| 16 | Update documentation (README, CHANGELOG) | Docs | ⬜ |
| 17 | Final verification | QA | ⬜ |

## Requirements Coverage

| Requirement | Covered By Tasks |
|-------------|-----------------|
| US-1: Quick Schedule Setup | Tasks 9, 10, 11, 12 |
| US-2: Detailed Schedule Setup | Tasks 9, 10, 11, 12 |
| US-3: Multiple Schedules Per Group | Tasks 2, 3, 4, 5 |
| US-4: Enable/Disable Schedules | Tasks 4, 5, 6, 12 |
| US-5: Schedule Validation | Tasks 4, 5 |
| US-6: View Next Run Time | Tasks 2, 4, 6, 10, 12 |
| US-7: Edit and Delete Schedules | Tasks 4, 5, 12 |
| US-8: Schedule Execution | Tasks 6, 7 |
| TR-1: Database | Tasks 2, 3 |
| TR-2: Backend API | Tasks 4, 5, 6, 8 |
| TR-3: Frontend | Tasks 9, 10, 11, 12 |
| TR-4: Testing | Tasks 13, 14, 15 |
| TR-5: TDD | All tasks follow test-first pattern |

---

## Implementation Tasks

### Task 1: Backend — Install croniter dependency

**Files:**
- Modify: `pyproject.toml`

**Step 1: Add croniter to dependencies**

```bash
uv add croniter
```

**Step 2: Commit**

```bash
git add pyproject.toml
git commit -m "chore: add croniter for cron expression parsing"
```

---

### Task 2: Backend — Create SourceGroupSchedule model

**Files:**
- Create: `src/models/source_group_schedule.py`
- Modify: `src/models/__init__.py`

**Step 1: Write the failing test — verify SourceGroupSchedule model**

```python
# tests/models/test_source_group_schedule.py
import pytest
from src.models.source_group_schedule import SourceGroupSchedule

@pytest.mark.asyncio
async def test_source_group_schedule_model_exists():
    """SourceGroupSchedule model should exist with correct fields."""
    schedule = SourceGroupSchedule(
        group_id=1,
        cron_expression="0 * * * *",
    )
    assert schedule.cron_expression == "0 * * * *"
    assert schedule.is_enabled is True
    assert schedule.next_run_at is None
```

**Step 2: Run test to verify it fails**

```bash
uv run pytest tests/models/test_source_group_schedule.py::test_source_group_schedule_model_exists -v
```
Expected: FAIL — Module not found

**Step 3: Create SourceGroupSchedule model**

```python
# src/models/source_group_schedule.py
"""SourceGroupSchedule model."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    pass


class SourceGroupSchedule(Base, TimestampMixin):
    """Scheduled update for source group."""

    __tablename__ = "source_group_schedules"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, init=False)
    group_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("source_groups.id", ondelete="CASCADE"), nullable=False
    )
    cron_expression: Mapped[str] = mapped_column(String(100), nullable=False)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    next_run_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    def __repr__(self) -> str:
        return f"<SourceGroupSchedule(id={self.id}, group_id={self.group_id}, cron={self.cron_expression})>"
```

**Step 4: Export in __init__.py**

```python
# src/models/__init__.py
from src.models.source_group_schedule import SourceGroupSchedule

__all__ = [
    # ... existing exports
    "SourceGroupSchedule",
]
```

**Step 5: Run test to verify it passes**

```bash
uv run pytest tests/models/test_source_group_schedule.py::test_source_group_schedule_model_exists -v
```
Expected: PASS

**Step 6: Commit**

```bash
git add src/models/ tests/models/
git commit -m "feat: add SourceGroupSchedule model"
```

---

### Task 3: Backend — Alembic migration for schedules table

**Files:**
- Create: `alembic/versions/<rev>_add_source_group_schedules.py`

**Step 1: Generate migration**

```bash
uv run alembic revision -m "add source_group_schedules table"
```

**Step 2: Write migration upgrade/downgrade**

```python
# alembic/versions/<rev>_add_source_group_schedules.py
"""add source_group_schedules table

Revision ID: <rev>
Revises: <prev_rev>
Create Date: 2026-04-02

"""
from alembic import op
import sqlalchemy as sa

revision = '<rev>'
down_revision = '<prev_rev>'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'source_group_schedules',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('group_id', sa.Integer(), nullable=False),
        sa.Column('cron_expression', sa.String(100), nullable=False),
        sa.Column('is_enabled', sa.Boolean(), default=True, nullable=False),
        sa.Column('next_run_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['group_id'], ['source_groups.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_schedules_is_enabled', 'source_group_schedules', ['is_enabled'])


def downgrade() -> None:
    op.drop_index('idx_schedules_is_enabled', table_name='source_group_schedules')
    op.drop_table('source_group_schedules')
```

**Step 3: Run migration**

```bash
uv run alembic upgrade head
```

**Step 4: Commit**

```bash
git add alembic/versions/
git commit -m "feat: add source_group_schedules table"
```

---

### Task 4: Backend — Create SourceGroupScheduleService

**Files:**
- Create: `src/services/source_group_schedule_service.py`

**Step 1: Write tests for service CRUD operations**

```python
# tests/services/test_source_group_schedule_service.py
import pytest
from src.models import SourceGroup, SourceGroupSchedule
from src.services.source_group_schedule_service import SourceGroupScheduleService


@pytest.mark.asyncio
async def test_create_schedule(db_session):
    """Should create a new schedule."""
    service = SourceGroupScheduleService(db_session)
    
    # Create a group first
    group = SourceGroup(name="Test Group")
    db_session.add(group)
    await db_session.flush()
    
    schedule = await service.create_schedule(
        group_id=group.id,
        cron_expression="0 * * * *",
    )
    
    assert schedule.id is not None
    assert schedule.cron_expression == "0 * * * *"
    assert schedule.is_enabled is True


@pytest.mark.asyncio
async def test_duplicate_cron_rejected(db_session):
    """Should reject duplicate cron expression in same group."""
    service = SourceGroupScheduleService(db_session)
    
    group = SourceGroup(name="Test Group")
    db_session.add(group)
    await db_session.flush()
    
    await service.create_schedule(group_id=group.id, cron_expression="0 * * * *")
    
    with pytest.raises(ValueError, match="duplicate"):
        await service.create_schedule(group_id=group.id, cron_expression="0 * * * *")
```

**Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/services/test_source_group_schedule_service.py -v
```
Expected: FAIL — Module not found

**Step 3: Implement SourceGroupScheduleService**

```python
# src/services/source_group_schedule_service.py
"""Source group schedule service."""

from datetime import datetime
from typing import List

from croniter import croniter
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import SourceGroupSchedule
from src.utils.time import now as get_now


class DuplicateScheduleError(ValueError):
    """Raised when duplicate schedule is detected."""
    pass


class SourceGroupScheduleService:
    """Service for managing source group schedules."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_schedule(
        self,
        group_id: int,
        cron_expression: str,
    ) -> SourceGroupSchedule:
        """Create a new schedule for a group."""
        # Validate cron expression
        if not self._validate_cron(cron_expression):
            raise ValueError("Invalid cron expression")
        
        # Check for duplicate
        existing = await self._check_duplicate(group_id, cron_expression)
        if existing:
            raise DuplicateScheduleError(
                f"Duplicate schedule with same cron expression already exists"
            )
        
        # Check max limit (10 per group)
        count_result = await self.session.execute(
            select(SourceGroupSchedule).where(
                SourceGroupSchedule.group_id == group_id
            )
        )
        existing_count = len(list(count_result.scalars().all()))
        if existing_count >= 10:
            raise ValueError("Maximum 10 schedules per group")
        
        schedule = SourceGroupSchedule(
            group_id=group_id,
            cron_expression=cron_expression,
        )
        self.session.add(schedule)
        await self.session.flush()
        
        # Calculate next run time
        schedule.next_run_at = self._calculate_next_run(cron_expression)
        
        await self.session.commit()
        await self.session.refresh(schedule)
        return schedule

    async def list_schedules(self, group_id: int) -> List[SourceGroupSchedule]:
        """List all schedules for a group."""
        result = await self.session.execute(
            select(SourceGroupSchedule).where(
                SourceGroupSchedule.group_id == group_id
            )
        )
        return list(result.scalars().all())

    async def get_schedule(self, schedule_id: int) -> SourceGroupSchedule | None:
        """Get a schedule by ID."""
        result = await self.session.execute(
            select(SourceGroupSchedule).where(
                SourceGroupSchedule.id == schedule_id
            )
        )
        return result.scalar_one_or_none()

    async def update_schedule(
        self,
        schedule_id: int,
        cron_expression: str,
    ) -> SourceGroupSchedule:
        """Update a schedule's cron expression."""
        schedule = await self.get_schedule(schedule_id)
        if not schedule:
            raise ValueError("Schedule not found")
        
        if not self._validate_cron(cron_expression):
            raise ValueError("Invalid cron expression")
        
        # Check for duplicate (excluding current)
        existing = await self._check_duplicate(schedule.group_id, cron_expression, schedule_id)
        if existing:
            raise DuplicateScheduleError("Duplicate schedule exists")
        
        schedule.cron_expression = cron_expression
        schedule.next_run_at = self._calculate_next_run(cron_expression)
        
        await self.session.commit()
        await self.session.refresh(schedule)
        return schedule

    async def delete_schedule(self, schedule_id: int) -> None:
        """Delete a schedule."""
        schedule = await self.get_schedule(schedule_id)
        if not schedule:
            raise ValueError("Schedule not found")
        
        await self.session.delete(schedule)
        await self.session.commit()

    async def toggle_schedule(self, schedule_id: int) -> SourceGroupSchedule:
        """Toggle a schedule's enabled status."""
        schedule = await self.get_schedule(schedule_id)
        if not schedule:
            raise ValueError("Schedule not found")
        
        schedule.is_enabled = not schedule.is_enabled
        
        # Recalculate next run
        if schedule.is_enabled:
            schedule.next_run_at = self._calculate_next_run(schedule.cron_expression)
        else:
            schedule.next_run_at = None
        
        await self.session.commit()
        await self.session.refresh(schedule)
        return schedule

    def _validate_cron(self, cron: str) -> bool:
        """Validate cron expression format."""
        try:
            parts = cron.split()
            if len(parts) != 5:
                return False
            croniter(cron, get_now())
            return True
        except (ValueError, KeyError):
            return False

    async def _check_duplicate(
        self,
        group_id: int,
        cron_expression: str,
        exclude_id: int | None = None,
    ) -> SourceGroupSchedule | None:
        """Check for duplicate cron expression."""
        query = select(SourceGroupSchedule).where(
            SourceGroupSchedule.group_id == group_id,
            SourceGroupSchedule.cron_expression == cron_expression,
        )
        if exclude_id:
            query = query.where(SourceGroupSchedule.id != exclude_id)
        
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    def _calculate_next_run(self, cron_expression: str) -> datetime:
        """Calculate next run time from cron expression."""
        cron = croniter(cron_expression, get_now())
        return cron.get_next(datetime)
```

**Step 4: Run tests to verify they pass**

```bash
uv run pytest tests/services/test_source_group_schedule_service.py -v
```
Expected: PASS

**Step 5: Commit**

```bash
git add src/services/ tests/services/
git commit -m "feat: add SourceGroupScheduleService with CRUD operations"
```

---

### Task 5: Backend — Create schedule API routes

**Files:**
- Create: `src/api/routes/schedule.py`
- Modify: `src/main.py`

**Step 1: Write tests for API endpoints**

```python
# tests/api/test_schedules.py
import pytest
from httpx import AsyncClient
from src.main import app


@pytest.mark.asyncio
async def test_create_schedule_authenticated(db_session, api_key):
    """Should create schedule with valid API key."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/source-groups/1/schedules",
            json={"cron_expression": "0 * * * *"},
            headers={"X-API-Key": api_key},
        )
        assert response.status_code in (201, 400)  # 400 if group doesn't exist
```

**Step 2: Implement API routes**

```python
# src/api/routes/schedule.py
"""Source group schedule API routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigConfig

from src.api.deps import get_schedule_service, require_api_key
from src.services.source_group_schedule_service import (
    DuplicateScheduleError,
    SourceGroupScheduleService,
)
from src.utils.time import to_iso_string

router = APIRouter(prefix="/source-groups/{group_id}/schedules", tags=["schedules"])


class ScheduleCreate(BaseModel):
    cron_expression: str


class ScheduleUpdate(BaseModel):
    cron_expression: str


class ScheduleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    group_id: int
    cron_expression: str
    is_enabled: bool
    next_run_at: str | None
    created_at: str
    updated_at: str


@router.get("", response_model=list[ScheduleResponse])
async def list_schedules(
    group_id: int,
    service: SourceGroupScheduleService = Depends(get_schedule_service),
    _: str = Depends(require_api_key),
) -> list[ScheduleResponse]:
    schedules = await service.list_schedules(group_id)
    return [
        ScheduleResponse(
            id=s.id,
            group_id=s.group_id,
            cron_expression=s.cron_expression,
            is_enabled=s.is_enabled,
            next_run_at=to_iso_string(s.next_run_at),
            created_at=s.created_at.isoformat(),
            updated_at=s.updated_at.isoformat(),
        )
        for s in schedules
    ]


@router.post("", response_model=ScheduleResponse, status_code=status.HTTP_201_CREATED)
async def create_schedule(
    group_id: int,
    data: ScheduleCreate,
    service: SourceGroupScheduleService = Depends(get_schedule_service),
    _: str = Depends(require_api_key),
) -> ScheduleResponse:
    try:
        schedule = await service.create_schedule(
            group_id=group_id,
            cron_expression=data.cron_expression,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    return ScheduleResponse(
        id=schedule.id,
        group_id=schedule.group_id,
        cron_expression=schedule.cron_expression,
        is_enabled=schedule.is_enabled,
        next_run_at=to_iso_string(schedule.next_run_at),
        created_at=schedule.created_at.isoformat(),
        updated_at=schedule.updated_at.isoformat(),
    )


@router.put("/{schedule_id}", response_model=ScheduleResponse)
async def update_schedule(
    group_id: int,
    schedule_id: int,
    data: ScheduleUpdate,
    service: SourceGroupScheduleService = Depends(get_schedule_service),
    _: str = Depends(require_api_key),
) -> ScheduleResponse:
    try:
        schedule = await service.update_schedule(
            schedule_id=schedule_id,
            cron_expression=data.cron_expression,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=404 if "not found" in str(e) else 400,
            detail=str(e),
        )
    
    return ScheduleResponse(
        id=schedule.id,
        group_id=schedule.group_id,
        cron_expression=schedule.cron_expression,
        is_enabled=schedule.is_enabled,
        next_run_at=to_iso_string(schedule.next_run_at),
        created_at=schedule.created_at.isoformat(),
        updated_at=schedule.updated_at.isoformat(),
    )


@router.delete("/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_schedule(
    group_id: int,
    schedule_id: int,
    service: SourceGroupScheduleService = Depends(get_schedule_service),
    _: str = Depends(require_api_key),
) -> None:
    try:
        await service.delete_schedule(schedule_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.patch("/{schedule_id}/toggle", response_model=ScheduleResponse)
async def toggle_schedule(
    group_id: int,
    schedule_id: int,
    service: SourceGroupScheduleService = Depends(get_schedule_service),
    _: str = Depends(require_api_key),
) -> ScheduleResponse:
    try:
        schedule = await service.toggle_schedule(schedule_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    
    return ScheduleResponse(
        id=schedule.id,
        group_id=schedule.group_id,
        cron_expression=schedule.cron_expression,
        is_enabled=schedule.is_enabled,
        next_run_at=to_iso_string(schedule.next_run_at),
        created_at=schedule.created_at.isoformat(),
        updated_at=schedule.updated_at.isoformat(),
    )
```

**Step 3: Register router in main.py**

```python
# src/main.py
from src.api.routes import schedule

app.include_router(schedule.router)
```

**Step 4: Commit**

```bash
git add src/api/routes/schedule.py src/main.py
git commit -m "feat: add schedule API routes"
```

---

### Task 6: Backend — Create ScheduleScheduler class

**Files:**
- Create: `src/scheduler/schedule_scheduler.py`

**Step 1: Implement ScheduleScheduler**

```python
# src/scheduler/schedule_scheduler.py
"""Scheduler for executing source group schedules."""

import asyncio
import logging
from datetime import datetime

from croniter import croniter
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.config import settings
from src.utils.time import now as get_now

logger = logging.getLogger(__name__)


class ScheduleScheduler:
    """Scheduler for executing source group schedules."""

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        fetch_scheduler,  # FetchScheduler instance
    ) -> None:
        self.session_factory = session_factory
        self.fetch_scheduler = fetch_scheduler
        self._running = False
        self._task: asyncio.Task | None = None

    async def start(self) -> None:
        if self._running:
            return

        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info("Schedule scheduler started")

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Schedule scheduler stopped")

    async def _run_loop(self) -> None:
        while self._running:
            try:
                await self._check_and_execute()
            except Exception as e:
                logger.error(f"Schedule scheduler error: {e}")

            await asyncio.sleep(60)  # Check every minute

    async def _check_and_execute(self) -> None:
        from src.models import SourceGroupSchedule

        async with self.session_factory() as session:
            now = get_now()
            result = await session.execute(
                select(SourceGroupSchedule).where(
                    SourceGroupSchedule.is_enabled == True,  # noqa: E712
                    SourceGroupSchedule.next_run_at <= now,
                )
            )
            schedules = list(result.scalars().all())

            for schedule in schedules:
                await self._execute_schedule(schedule, session)

    async def _execute_schedule(self, schedule, session) -> None:
        from src.models import SourceGroupSchedule

        try:
            logger.info(f"Executing schedule {schedule.id} for group {schedule.group_id}")
            await self.fetch_scheduler.refresh_group(schedule.group_id)
        except Exception as e:
            logger.error(f"Failed to execute schedule {schedule.id}: {e}")

        # Update next run time
        schedule.next_run_at = self._calculate_next_run(schedule.cron_expression)
        await session.commit()

    def _calculate_next_run(self, cron_expression: str) -> datetime:
        """Calculate next run time from cron expression."""
        cron = croniter(cron_expression, get_now())
        return cron.get_next(datetime)
```

**Step 2: Commit**

```bash
git add src/scheduler/schedule_scheduler.py
git commit -m "feat: add ScheduleScheduler for automatic execution"
```

---

### Task 7: Backend — Add croniter to scheduler startup

**Files:**
- Modify: `src/main.py`

**Step 1: Integrate ScheduleScheduler in main.py**

```python
# src/main.py - in lifespan startup
from src.scheduler.schedule_scheduler import ScheduleScheduler

# In startup function:
schedule_scheduler = ScheduleScheduler(
    session_factory,
    fetch_scheduler,  # Pass existing fetch_scheduler
)
await schedule_scheduler.start()

# In shutdown function:
await schedule_scheduler.stop()
```

**Step 2: Commit**

```bash
git commit -m "feat: integrate ScheduleScheduler in app lifecycle"
```

---

### Task 8: Backend — Update deps.py for new services

**Files:**
- Modify: `src/api/deps.py`

**Step 1: Add dependency injection**

```python
# src/api/deps.py
from src.services.source_group_schedule_service import SourceGroupScheduleService

async def get_schedule_service(session: AsyncSession = Depends(get_db)) -> SourceGroupScheduleService:
    return SourceGroupScheduleService(session)
```

**Step 2: Commit**

```bash
git add src/api/deps.py
git commit -m "chore: add schedule service dependency injection"
```

---

### Task 9: Frontend — Add schedule types and API client

**Files:**
- Create: `src/types/schedule.ts`
- Modify: `src/api/source-groups.ts`

**Step 1: Add TypeScript types**

```typescript
// src/types/schedule.ts
export interface Schedule {
  id: number
  group_id: number
  cron_expression: string
  is_enabled: boolean
  next_run_at: string | null
  created_at: string
  updated_at: string
}

export interface ScheduleCreate {
  cron_expression: string
}
```

**Step 2: Add API functions**

```typescript
// src/api/schedules.ts
import type { Schedule, ScheduleCreate } from '@/types/schedule'
import { apiClient } from './api-client'

export const getSchedules = async (groupId: number): Promise<Schedule[]> => {
  const response = await apiClient.get(`/source-groups/${groupId}/schedules`)
  return response.data
}

export const createSchedule = async (groupId: number, data: ScheduleCreate): Promise<Schedule> => {
  const response = await apiClient.post(`/source-groups/${groupId}/schedules`, data)
  return response.data
}

export const updateSchedule = async (groupId: number, scheduleId: number, data: ScheduleCreate): Promise<Schedule> => {
  const response = await apiClient.put(`/source-groups/${groupId}/schedules/${scheduleId}`, data)
  return response.data
}

export const deleteSchedule = async (groupId: number, scheduleId: number): Promise<void> => {
  await apiClient.delete(`/source-groups/${groupId}/schedules/${scheduleId}`)
}

export const toggleSchedule = async (groupId: number, scheduleId: number): Promise<Schedule> => {
  const response = await apiClient.patch(`/source-groups/${groupId}/schedules/${scheduleId}/toggle`)
  return response.data
}
```

**Step 3: Commit**

```bash
git add src/types/schedule.ts src/api/schedules.ts
git commit -m "feat: add schedule types and API client"
```

---

### Task 10: Frontend — Create ScheduleConfigPanel component

**Files:**
- Create: `src/components/ScheduleConfigPanel.vue`
- Create: `src/components/ScheduleItem.vue`
- Create: `src/components/ui/Checkbox.vue` (if needed)

**Step 1: Build ScheduleConfigPanel with TDD**

Write Playwright test first:

```typescript
// tests/e2e/schedule.spec.ts
import { test, expect } from '@playwright/test'

test('quick settings workflow', async ({ page }) => {
  await page.goto('/sources')
  await page.click('text=Groups')
  await page.click('text=我的群組')
  await page.click('text=定時更新')
  
  // Select quick setting
  await page.click('text=快捷設定')
  await page.selectOption('[data-testid="quick-select"]', '0 * * * *')
  
  // Save
  await page.click('text=儲存')
  
  // Verify saved
  await expect(page.locator('text=每 1 小時')).toBeVisible()
})
```

**Step 2: Implement component**

Build the Vue component with:
- Mode toggle (Quick/Detailed radio)
- Quick settings dropdown
- Detailed settings with multi-select checkboxes
- Human-readable preview
- Schedule list display

**Step 3: Commit**

```bash
git add src/components/ScheduleConfigPanel.vue src/components/ScheduleItem.vue
git commit -m "feat: add ScheduleConfigPanel component"
```

---

### Task 11: Frontend — Create schedule-related i18n keys

**Files:**
- Modify: `src/locales/en.json`, `src/locales/zh-TW.json`

**Step 1: Add translations**

```json
// en.json
{
  "schedule": {
    "title": "Scheduled Update",
    "quick": "Quick Settings",
    "detailed": "Detailed Settings",
    "quick_options": {
      "every_15min": "Every 15 minutes",
      "every_30min": "Every 30 minutes",
      "every_1hour": "Every 1 hour",
      "every_3hours": "Every 3 hours",
      "every_6hours": "Every 6 hours",
      "every_12hours": "Every 12 hours",
      "daily": "Daily (08:30)"
    },
    "minutes": "Minutes",
    "hours": "Hours",
    "weekdays": "Weekdays",
    "preview": "Preview",
    "next_run": "Next run",
    "add": "Add Schedule",
    "save": "Save",
    "edit": "Edit",
    "delete": "Delete",
    "enabled": "Enabled",
    "disabled": "Disabled",
    "max_reached": "Maximum 10 schedules per group",
    "duplicate": "Duplicate schedule detected",
    "weekdays_options": {
      "0": "Sun",
      "1": "Mon",
      "2": "Tue",
      "3": "Wed",
      "4": "Thu",
      "5": "Fri",
      "6": "Sat"
    }
  }
}
```

**Step 2: Commit**

```bash
git add src/locales/en.json src/locales/zh-TW.json
git commit -m "feat: add schedule i18n translations"
```

---

### Task 12: Frontend — Integrate schedule UI in SourcesPage

**Files:**
- Modify: `src/pages/SourcesPage.vue`

**Step 1: Add ScheduleConfigPanel to Groups tab**

```vue
<!-- In SourcesPage.vue - Groups tab -->
<ScheduleConfigPanel
  v-if="expandedGroupId === group.id"
  :group-id="group.id"
  @saved="handleScheduleSaved"
/>
```

**Step 2: Commit**

```bash
git add src/pages/SourcesPage.vue
git commit -m "feat: integrate schedule UI in SourcesPage"
```

---

### Task 13: Backend — Unit tests for cron validation

**Files:**
- Create: `tests/test_cron_validation.py`

**Step 1: Write tests**

```python
# tests/test_cron_validation.py
import pytest
from src.services.source_group_schedule_service import SourceGroupScheduleService


def test_valid_cron_expressions():
    """Valid cron expressions should pass validation."""
    service = SourceGroupScheduleService(None)  # session not needed for validation
    
    assert service._validate_cron("0 * * * *") is True
    assert service._validate_cron("*/15 * * * *") is True
    assert service._validate_cron("30 8 * * *") is True
    assert service._validate_cron("25,27 11,12 * * 3,6") is True


def test_invalid_cron_expressions():
    """Invalid cron expressions should fail validation."""
    service = SourceGroupScheduleService(None)
    
    assert service._validate_cron("invalid") is False
    assert service._validate_cron("60 * * * *") is False  # minute > 59
    assert service._validate_cron("* * * * * *") is False  # too many fields
```

**Step 2: Commit**

```bash
git add tests/test_cron_validation.py
git commit -m "test: add cron validation unit tests"
```

---

### Task 14: Backend — Unit tests for schedule service

**Step 1: Additional service tests**

Add tests for:
- Update schedule
- Delete schedule  
- Toggle schedule
- Next run time calculation

**Step 2: Commit**

```bash
git add tests/services/test_source_group_schedule_service.py
git commit -m "test: add schedule service unit tests"
```

---

### Task 15: Frontend — Playwright E2E tests

**Files:**
- Create: `tests/e2e/schedule.spec.ts`

**Step 1: Write E2E tests**

```typescript
import { test, expect } from '@playwright/test'

test.describe('Schedule Management', () => {
  test('quick settings workflow', async ({ page }) => {
    // Navigate to Sources > Groups > Select Group > Schedule
    await page.goto('/sources')
    await page.click('button:has-text("Groups")')
    await page.click('text=我的群組')
    await page.click('text=定時更新')
    
    // Select quick setting
    await page.click('label:has-text("快捷設定")')
    await page.selectOption('[data-testid="quick-select"]', '*/15 * * * *')
    
    // Save
    await page.click('button:has-text("儲存")')
    
    // Verify
    await expect(page.locator('text=每 15 分鐘')).toBeVisible()
  })

  test('detailed settings workflow', async ({ page }) => {
    await page.goto('/sources')
    await page.click('button:has-text("Groups")')
    await page.click('text=我的群組')
    await page.click('text=定時更新')
    
    // Select detailed
    await page.click('label:has-text("詳細設定")')
    
    // Select minutes
    await page.click('[data-testid="minute-13"]')
    await page.click('[data-testid="minute-27"]')
    
    // Select hours
    await page.click('[data-testid="hour-11"]')
    await page.click('[data-testid="hour-12"]')
    
    // Select weekdays
    await page.click('[data-testid="weekday-3"]')
    await page.click('[data-testid="weekday-6"]')
    
    // Verify preview
    await expect(page.locator('text=每週三、六 11:13, 11:27')).toBeVisible()
    
    // Save
    await page.click('button:has-text("儲存")')
  })

  test('enable/disable toggle', async ({ page }) => {
    await page.goto('/sources')
    // ... create a schedule first
    
    // Toggle
    await page.click('[data-testid="toggle-schedule"]')
    
    // Verify disabled state
    await expect(page.locator('text=已停用')).toBeVisible()
  })
})
```

**Step 2: Commit**

```bash
git add tests/e2e/schedule.spec.ts
git commit -m "test: add schedule E2E tests"
```

---

### Task 16: Update documentation (README, CHANGELOG)

**Files:**
- Modify: `README.md`, `CHANGELOG.md`

**Step 1: Update README**

Add section about scheduled update feature.

**Step 2: Update CHANGELOG**

Add entry for new feature.

**Step 3: Commit**

```bash
git add README.md CHANGELOG.md
git commit -m "docs: update documentation for scheduled update feature"
```

---

### Task 17: Final verification

**Step 1: Run full test suite**

```bash
# Backend tests
uv run pytest tests/ -v

# Frontend tests
cd web && pnpm test

# E2E tests
cd web && pnpm test:e2e
```

**Step 2: Build and deploy**

```bash
# Docker
docker compose build
docker compose up -d

# Desktop app
./scripts/build-all.sh release
```

**Step 3: Verify feature works**

- Create a group with sources
- Add a schedule (quick or detailed)
- Verify next run time displays
- Wait for schedule to execute
- Verify group sources were refreshed

**Step 4: Commit**

```bash
git commit -m "chore: final verification complete"
```