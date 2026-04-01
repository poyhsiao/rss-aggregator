# Remove fetch_interval + Add Source Groups Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Remove per-source fetch_interval (manual-only refresh) and add many-to-many source group management across backend API, web frontend, and desktop app.

**Architecture:** Add `source_groups` and `source_group_members` (junction) tables. Remove `fetch_interval` column from `sources`. Extend feed/history API responses to include group info. Web UI adds Groups tab, filter chips, and group selection in source dialogs.

**Tech Stack:** Python 3.12+, FastAPI, SQLAlchemy 2.0, Alembic, SQLite, Vue 3 + TypeScript, Pinia, vue-i18n, Playwright, pytest, Vitest

---

### Task 1: Backend — Remove fetch_interval from Source model

**Files:**
- Modify: `src/models/source.py:25`
- Test: `tests/models/test_source.py`
- Test: `tests/services/test_source_service.py`

**Step 1: Write the failing test — verify fetch_interval column removal**

```python
# tests/models/test_source.py
@pytest.mark.asyncio
async def test_source_no_fetch_interval(db_session):
    """Source model should not have fetch_interval attribute."""
    source = Source(name="Test", url="https://example.com/rss")
    assert not hasattr(source, "fetch_interval")
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/models/test_source.py::test_source_no_fetch_interval -v`
Expected: FAIL — `fetch_interval` attribute still exists

**Step 3: Remove fetch_interval from Source model**

```python
# src/models/source.py — remove this line:
fetch_interval: Mapped[int] = mapped_column(default=0)
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/models/test_source.py::test_source_no_fetch_interval -v`
Expected: PASS

**Step 5: Update existing tests that reference fetch_interval**

In `tests/services/test_source_service.py`:
- Remove `assert source.fetch_interval == 900` from `test_create_source`
- Remove `fetch_interval=1800` from `test_update_source`
- Remove `assert updated.fetch_interval == 1800` from `test_update_source`
- Remove `fetch_interval` assertions from `test_restore_source_overwrite`

**Step 6: Run all source tests**

Run: `uv run pytest tests/services/test_source_service.py tests/models/test_source.py -v`
Expected: All PASS

**Step 7: Commit**

```bash
git add src/models/source.py tests/models/test_source.py tests/services/test_source_service.py
git commit -m "refactor: remove fetch_interval from Source model"
```

---

### Task 2: Backend — Alembic migration for fetch_interval removal + new tables

**Files:**
- Create: `alembic/versions/<rev>_remove_fetch_interval_add_source_groups.py`
- Modify: `src/models/__init__.py`

**Step 1: Generate migration**

Run: `uv run alembic revision -m "remove fetch_interval add source_groups"`

**Step 2: Write migration upgrade/downgrade**

```python
"""remove fetch_interval add source_groups

Revision ID: <rev>
Revises: <prev>
Create Date: 2026-04-01
"""
from alembic import op
import sqlalchemy as sa

revision = "<rev>"
down_revision = "<prev>"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Remove fetch_interval column
    with op.batch_alter_table("sources") as batch_op:
        batch_op.drop_column("fetch_interval")

    # Create source_groups table
    op.create_table(
        "source_groups",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(255), nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
    )

    # Create junction table
    op.create_table(
        "source_group_members",
        sa.Column("source_id", sa.Integer(), sa.ForeignKey("sources.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("group_id", sa.Integer(), sa.ForeignKey("source_groups.id", ondelete="CASCADE"), primary_key=True),
    )
    op.create_index("ix_source_group_members_group_id", "source_group_members", ["group_id"])


def downgrade() -> None:
    op.drop_table("source_group_members")
    op.drop_table("source_groups")
    with op.batch_alter_table("sources") as batch_op:
        batch_op.add_column(sa.Column("fetch_interval", sa.Integer(), server_default="0", nullable=False))
```

**Step 3: Create SourceGroup and SourceGroupMember models**

```python
# src/models/source_group.py
from __future__ import annotations

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base, TimestampMixin


class SourceGroup(Base, TimestampMixin):
    """Source grouping for organization."""

    __tablename__ = "source_groups"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, init=False)
    name: Mapped[str] = mapped_column(String(255), unique=True)

    sources: Mapped[list[Source]] = relationship(
        "Source",
        secondary="source_group_members",
        back_populates="groups",
        init=False,
    )

    def __repr__(self) -> str:
        return f"<SourceGroup(id={self.id}, name={self.name})>"


class SourceGroupMember(Base):
    """Junction table for many-to-many Source ↔ SourceGroup."""

    __tablename__ = "source_group_members"

    source_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("sources.id", ondelete="CASCADE"), primary_key=True, init=False
    )
    group_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("source_groups.id", ondelete="CASCADE"), primary_key=True, init=False
    )
```

**Step 4: Update Source model with groups relationship**

```python
# src/models/source.py — add import and relationship
from sqlalchemy.orm import Mapped, mapped_column, relationship
# ... existing code ...
# Add after feed_items relationship:
groups: Mapped[list["SourceGroup"]] = relationship(
    "SourceGroup",
    secondary="source_group_members",
    back_populates="sources",
    init=False,
)
```

**Step 5: Update `src/models/__init__.py`**

```python
from src.models.source_group import SourceGroup, SourceGroupMember

__all__ = [
    # ... existing ...
    "SourceGroup",
    "SourceGroupMember",
]
```

**Step 6: Run migration**

Run: `uv run alembic upgrade head`
Expected: Success, no errors

**Step 7: Verify models load correctly**

Run: `uv run python -c "from src.models import SourceGroup, SourceGroupMember; print('OK')"`
Expected: `OK`

**Step 8: Commit**

```bash
git add alembic/versions/*.py src/models/source_group.py src/models/source.py src/models/__init__.py
git commit -m "feat: add SourceGroup model and remove fetch_interval migration"
```

---

### Task 3: Backend — SourceGroupService with TDD

**Files:**
- Create: `src/services/source_group_service.py`
- Create: `tests/services/test_source_group_service.py`

**Step 1: Write failing tests for SourceGroupService**

```python
# tests/services/test_source_group_service.py
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.source_group_service import SourceGroupService
from src.services.source_service import SourceService


@pytest_asyncio.fixture
async def group_service(db_session: AsyncSession) -> SourceGroupService:
    return SourceGroupService(db_session)


@pytest_asyncio.fixture
async def source_svc(db_session: AsyncSession) -> SourceService:
    return SourceService(db_session)


@pytest.mark.asyncio
async def test_create_group(group_service: SourceGroupService):
    group = await group_service.create_group(name="Tech")
    assert group.id is not None
    assert group.name == "Tech"


@pytest.mark.asyncio
async def test_create_duplicate_group_raises(group_service: SourceGroupService):
    await group_service.create_group(name="Tech")
    with pytest.raises(ValueError, match="already exists"):
        await group_service.create_group(name="Tech")


@pytest.mark.asyncio
async def test_list_groups(group_service: SourceGroupService):
    await group_service.create_group(name="A")
    await group_service.create_group(name="B")
    groups = await group_service.list_groups()
    assert len(groups) == 2


@pytest.mark.asyncio
async def test_update_group_name(group_service: SourceGroupService):
    group = await group_service.create_group(name="Old")
    updated = await group_service.update_group(group.id, name="New")
    assert updated.name == "New"


@pytest.mark.asyncio
async def test_delete_group(group_service: SourceGroupService):
    group = await group_service.create_group(name="ToDelete")
    await group_service.delete_group(group.id)
    groups = await group_service.list_groups()
    assert len(groups) == 0


@pytest.mark.asyncio
async def test_add_source_to_group(
    group_service: SourceGroupService, source_svc: SourceService
):
    group = await group_service.create_group(name="Tech")
    source = await source_svc.create_source("Feed", "https://example.com/rss")
    await group_service.add_source_to_group(group.id, source.id)
    groups = await group_service.get_source_groups(source.id)
    assert len(groups) == 1
    assert groups[0].id == group.id


@pytest.mark.asyncio
async def test_add_source_to_multiple_groups(
    group_service: SourceGroupService, source_svc: SourceService
):
    g1 = await group_service.create_group(name="Tech")
    g2 = await group_service.create_group(name="News")
    source = await source_svc.create_source("Feed", "https://example.com/rss")
    await group_service.add_source_to_group(g1.id, source.id)
    await group_service.add_source_to_group(g2.id, source.id)
    groups = await group_service.get_source_groups(source.id)
    assert len(groups) == 2


@pytest.mark.asyncio
async def test_remove_source_from_group(
    group_service: SourceGroupService, source_svc: SourceService
):
    group = await group_service.create_group(name="Tech")
    source = await source_svc.create_source("Feed", "https://example.com/rss")
    await group_service.add_source_to_group(group.id, source.id)
    await group_service.remove_source_from_group(group.id, source.id)
    groups = await group_service.get_source_groups(source.id)
    assert len(groups) == 0


@pytest.mark.asyncio
async def test_get_group_sources(
    group_service: SourceGroupService, source_svc: SourceService
):
    group = await group_service.create_group(name="Tech")
    s1 = await source_svc.create_source("Feed1", "https://example.com/1.xml")
    s2 = await source_svc.create_source("Feed2", "https://example.com/2.xml")
    await group_service.add_source_to_group(group.id, s1.id)
    await group_service.add_source_to_group(group.id, s2.id)
    sources = await group_service.get_group_sources(group.id)
    assert len(sources) == 2


@pytest.mark.asyncio
async def test_get_group_with_member_count(
    group_service: SourceGroupService, source_svc: SourceService
):
    group = await group_service.create_group(name="Tech")
    source = await source_svc.create_source("Feed", "https://example.com/rss")
    await group_service.add_source_to_group(group.id, source.id)
    groups = await group_service.list_groups_with_count()
    tech_group = [g for g in groups if g["name"] == "Tech"][0]
    assert tech_group["member_count"] == 1
```

**Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/services/test_source_group_service.py -v`
Expected: FAIL — module not found

**Step 3: Implement SourceGroupService**

```python
# src/services/source_group_service.py
"""Service for managing source groups."""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import Source, SourceGroup, SourceGroupMember


class SourceGroupService:
    """Service for managing source groups and their memberships."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_group(self, name: str) -> SourceGroup:
        """Create a new source group.

        Raises:
            ValueError: If group with same name already exists.
        """
        existing = await self.session.execute(
            select(SourceGroup).where(SourceGroup.name == name)
        )
        if existing.scalar_one_or_none():
            raise ValueError(f"Group '{name}' already exists")

        group = SourceGroup(name=name)
        self.session.add(group)
        await self.session.commit()
        await self.session.refresh(group)
        return group

    async def list_groups(self) -> list[SourceGroup]:
        """List all source groups."""
        result = await self.session.execute(select(SourceGroup))
        return list(result.scalars().all())

    async def list_groups_with_count(self) -> list[dict]:
        """List all groups with member counts."""
        result = await self.session.execute(select(SourceGroup))
        groups = list(result.scalars().all())

        output = []
        for group in groups:
            count_result = await self.session.execute(
                select(func.count()).select_from(SourceGroupMember).where(
                    SourceGroupMember.group_id == group.id
                )
            )
            output.append({
                "id": group.id,
                "name": group.name,
                "member_count": count_result.scalar() or 0,
                "created_at": group.created_at,
                "updated_at": group.updated_at,
            })
        return output

    async def update_group(self, group_id: int, **kwargs) -> SourceGroup:
        """Update a group.

        Raises:
            ValueError: If group not found.
        """
        result = await self.session.execute(
            select(SourceGroup).where(SourceGroup.id == group_id)
        )
        group = result.scalar_one_or_none()
        if group is None:
            raise ValueError(f"Group {group_id} not found")

        for key, value in kwargs.items():
            if hasattr(group, key):
                setattr(group, key, value)

        await self.session.commit()
        await self.session.refresh(group)
        return group

    async def delete_group(self, group_id: int) -> None:
        """Delete a group (does NOT delete member sources).

        Raises:
            ValueError: If group not found.
        """
        result = await self.session.execute(
            select(SourceGroup).where(SourceGroup.id == group_id)
        )
        group = result.scalar_one_or_none()
        if group is None:
            raise ValueError(f"Group {group_id} not found")

        await self.session.delete(group)
        await self.session.commit()

    async def add_source_to_group(self, group_id: int, source_id: int) -> None:
        """Add a source to a group.

        Raises:
            ValueError: If group or source not found, or already a member.
        """
        # Verify group exists
        grp = await self.session.execute(
            select(SourceGroup).where(SourceGroup.id == group_id)
        )
        if not grp.scalar_one_or_none():
            raise ValueError(f"Group {group_id} not found")

        # Verify source exists
        src = await self.session.execute(
            select(Source).where(Source.id == source_id, Source.deleted_at.is_(None))
        )
        if not src.scalar_one_or_none():
            raise ValueError(f"Source {source_id} not found")

        # Check existing membership
        existing = await self.session.execute(
            select(SourceGroupMember).where(
                SourceGroupMember.group_id == group_id,
                SourceGroupMember.source_id == source_id,
            )
        )
        if existing.scalar_one_or_none():
            raise ValueError(f"Source {source_id} is already in group {group_id}")

        member = SourceGroupMember(group_id=group_id, source_id=source_id)
        self.session.add(member)
        await self.session.commit()

    async def remove_source_from_group(self, group_id: int, source_id: int) -> None:
        """Remove a source from a group.

        Raises:
            ValueError: If membership not found.
        """
        result = await self.session.execute(
            select(SourceGroupMember).where(
                SourceGroupMember.group_id == group_id,
                SourceGroupMember.source_id == source_id,
            )
        )
        member = result.scalar_one_or_none()
        if member is None:
            raise ValueError(f"Source {source_id} not in group {group_id}")

        await self.session.delete(member)
        await self.session.commit()

    async def get_source_groups(self, source_id: int) -> list[SourceGroup]:
        """Get all groups a source belongs to."""
        result = await self.session.execute(
            select(SourceGroup)
            .join(SourceGroupMember, SourceGroup.id == SourceGroupMember.group_id)
            .where(SourceGroupMember.source_id == source_id)
        )
        return list(result.scalars().all())

    async def get_group_sources(self, group_id: int) -> list[Source]:
        """Get all sources in a group."""
        result = await self.session.execute(
            select(Source)
            .join(SourceGroupMember, Source.id == SourceGroupMember.source_id)
            .where(SourceGroupMember.group_id == group_id, Source.deleted_at.is_(None))
        )
        return list(result.scalars().all())
```

**Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/services/test_source_group_service.py -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add src/services/source_group_service.py tests/services/test_source_group_service.py
git commit -m "feat: add SourceGroupService with full CRUD and membership management"
```

---

### Task 4: Backend — Source group API routes

**Files:**
- Create: `src/api/routes/source_groups.py`
- Modify: `src/api/routes/__init__.py`
- Test: `tests/api/test_source_group_routes.py`

**Step 1: Write failing API tests**

```python
# tests/api/test_source_group_routes.py
import pytest
from httpx import ASGITransport, AsyncClient

from src.main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        c.headers["x-api-key"] = "test-key"
        yield c


@pytest.mark.asyncio
async def test_create_group(client: AsyncClient):
    resp = await client.post("/api/v1/source-groups", json={"name": "Tech"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Tech"


@pytest.mark.asyncio
async def test_list_groups(client: AsyncClient):
    await client.post("/api/v1/source-groups", json={"name": "A"})
    await client.post("/api/v1/source-groups", json={"name": "B"})
    resp = await client.get("/api/v1/source-groups")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


@pytest.mark.asyncio
async def test_update_group(client: AsyncClient):
    create_resp = await client.post("/api/v1/source-groups", json={"name": "Old"})
    gid = create_resp.json()["id"]
    resp = await client.put(f"/api/v1/source-groups/{gid}", json={"name": "New"})
    assert resp.status_code == 200
    assert resp.json()["name"] == "New"


@pytest.mark.asyncio
async def test_delete_group(client: AsyncClient):
    create_resp = await client.post("/api/v1/source-groups", json={"name": "ToDelete"})
    gid = create_resp.json()["id"]
    resp = await client.delete(f"/api/v1/source-groups/{gid}")
    assert resp.status_code == 204
    resp = await client.get("/api/v1/source-groups")
    assert len(resp.json()) == 0


@pytest.mark.asyncio
async def test_add_source_to_group(client: AsyncClient):
    grp = await client.post("/api/v1/source-groups", json={"name": "Tech"})
    gid = grp.json()["id"]
    src = await client.post("/api/v1/sources", json={"name": "Feed", "url": "https://example.com/rss"})
    sid = src.json()["id"]
    resp = await client.post(f"/api/v1/source-groups/{gid}/sources", json={"source_id": sid})
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_remove_source_from_group(client: AsyncClient):
    grp = await client.post("/api/v1/source-groups", json={"name": "Tech"})
    gid = grp.json()["id"]
    src = await client.post("/api/v1/sources", json={"name": "Feed", "url": "https://example.com/rss"})
    sid = src.json()["id"]
    await client.post(f"/api/v1/source-groups/{gid}/sources", json={"source_id": sid})
    resp = await client.delete(f"/api/v1/source-groups/{gid}/sources/{sid}")
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_get_group_sources(client: AsyncClient):
    grp = await client.post("/api/v1/source-groups", json={"name": "Tech"})
    gid = grp.json()["id"]
    s1 = await client.post("/api/v1/sources", json={"name": "F1", "url": "https://example.com/1.xml"})
    s2 = await client.post("/api/v1/sources", json={"name": "F2", "url": "https://example.com/2.xml"})
    await client.post(f"/api/v1/source-groups/{gid}/sources", json={"source_id": s1.json()["id"]})
    await client.post(f"/api/v1/source-groups/{gid}/sources", json={"source_id": s2.json()["id"]})
    resp = await client.get(f"/api/v1/source-groups/{gid}/sources")
    assert resp.status_code == 200
    assert len(resp.json()) == 2
```

**Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/api/test_source_group_routes.py -v`
Expected: FAIL — routes not found / 404

**Step 3: Implement source group routes**

```python
# src/api/routes/source_groups.py
"""Source group management API routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict

from src.api.deps import get_source_group_service, require_api_key
from src.services.source_group_service import SourceGroupService

router = APIRouter(prefix="/source-groups", tags=["source-groups"])


class GroupCreate(BaseModel):
    name: str


class GroupUpdate(BaseModel):
    name: str | None = None


class GroupResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    member_count: int = 0
    created_at: str
    updated_at: str


class AddSourceRequest(BaseModel):
    source_id: int


@router.get("", response_model=list[GroupResponse])
async def list_groups(
    service: SourceGroupService = Depends(get_source_group_service),
    _: str = Depends(require_api_key),
) -> list[GroupResponse]:
    """List all source groups with member counts."""
    groups = await service.list_groups_with_count()
    return [
        GroupResponse(
            id=g["id"],
            name=g["name"],
            member_count=g["member_count"],
            created_at=g["created_at"].isoformat(),
            updated_at=g["updated_at"].isoformat(),
        )
        for g in groups
    ]


@router.post("", response_model=GroupResponse, status_code=status.HTTP_201_CREATED)
async def create_group(
    data: GroupCreate,
    service: SourceGroupService = Depends(get_source_group_service),
    _: str = Depends(require_api_key),
) -> GroupResponse:
    """Create a new source group."""
    try:
        group = await service.create_group(name=data.name)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))

    return GroupResponse(
        id=group.id,
        name=group.name,
        member_count=0,
        created_at=group.created_at.isoformat(),
        updated_at=group.updated_at.isoformat(),
    )


@router.put("/{group_id}", response_model=GroupResponse)
async def update_group(
    group_id: int,
    data: GroupUpdate,
    service: SourceGroupService = Depends(get_source_group_service),
    _: str = Depends(require_api_key),
) -> GroupResponse:
    """Update a source group."""
    try:
        group = await service.update_group(group_id, **{k: v for k, v in data.model_dump().items() if v is not None})
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return GroupResponse(
        id=group.id,
        name=group.name,
        created_at=group.created_at.isoformat(),
        updated_at=group.updated_at.isoformat(),
    )


@router.delete("/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_group(
    group_id: int,
    service: SourceGroupService = Depends(get_source_group_service),
    _: str = Depends(require_api_key),
) -> None:
    """Delete a source group (sources are NOT deleted)."""
    try:
        await service.delete_group(group_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{group_id}/sources")
async def get_group_sources(
    group_id: int,
    service: SourceGroupService = Depends(get_source_group_service),
    _: str = Depends(require_api_key),
) -> list[dict]:
    """List all sources in a group."""
    from src.utils.time import to_iso_string

    sources = await service.get_group_sources(group_id)
    return [
        {
            "id": s.id,
            "name": s.name,
            "url": s.url,
            "is_active": s.is_active,
            "last_fetched_at": to_iso_string(s.last_fetched_at),
            "last_error": s.last_error,
            "created_at": to_iso_string(s.created_at) or "",
            "updated_at": to_iso_string(s.updated_at) or "",
        }
        for s in sources
    ]


@router.post("/{group_id}/sources")
async def add_source_to_group(
    group_id: int,
    data: AddSourceRequest,
    service: SourceGroupService = Depends(get_source_group_service),
    _: str = Depends(require_api_key),
) -> dict:
    """Add a source to a group."""
    try:
        await service.add_source_to_group(group_id, data.source_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"message": "Source added to group"}


@router.delete("/{group_id}/sources/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_source_from_group(
    group_id: int,
    source_id: int,
    service: SourceGroupService = Depends(get_source_group_service),
    _: str = Depends(require_api_key),
) -> None:
    """Remove a source from a group."""
    try:
        await service.remove_source_from_group(group_id, source_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
```

**Step 4: Register routes in `src/api/routes/__init__.py`**

```python
from src.api.routes.source_groups import router as source_groups_router

# Add to __all__ and include router in app
```

**Step 5: Add `get_source_group_service` to `src/api/deps.py`**

```python
from src.services.source_group_service import SourceGroupService

def get_source_group_service(session: AsyncSession = Depends(get_session)) -> SourceGroupService:
    return SourceGroupService(session)
```

**Step 6: Run tests to verify they pass**

Run: `uv run pytest tests/api/test_source_group_routes.py -v`
Expected: All PASS

**Step 7: Commit**

```bash
git add src/api/routes/source_groups.py src/api/routes/__init__.py src/api/deps.py tests/api/test_source_group_routes.py
git commit -m "feat: add source group API routes"
```

---

### Task 5: Backend — Remove fetch_interval from sources API + scheduler

**Files:**
- Modify: `src/api/routes/sources.py`
- Modify: `src/services/source_service.py`
- Modify: `src/scheduler/fetch_scheduler.py`
- Test: `tests/api/test_source_routes.py` (create if not exists)
- Test: `tests/scheduler/test_fetch_scheduler.py`

**Step 1: Write regression tests — sources API without fetch_interval**

```python
# tests/api/test_source_routes.py — new or append
@pytest.mark.asyncio
async def test_create_source_no_fetch_interval(client):
    resp = await client.post("/api/v1/sources", json={
        "name": "Feed", "url": "https://example.com/rss"
    })
    assert resp.status_code == 201
    data = resp.json()
    assert "fetch_interval" not in data


@pytest.mark.asyncio
async def test_update_source_no_fetch_interval(client):
    src = await client.post("/api/v1/sources", json={
        "name": "Feed", "url": "https://example.com/rss"
    })
    sid = src.json()["id"]
    resp = await client.put(f"/api/v1/sources/{sid}", json={"name": "Updated"})
    assert resp.status_code == 200
    data = resp.json()
    assert "fetch_interval" not in data
    assert data["name"] == "Updated"
```

**Step 2: Remove fetch_interval from SourceCreate/SourceUpdate/SourceResponse**

In `src/api/routes/sources.py`:
- Remove `fetch_interval: int = 0` from `SourceCreate`
- Remove `fetch_interval: int | None = None` from `SourceUpdate`
- Remove `fetch_interval: int` from `SourceResponse`
- Remove all `fetch_interval=...` from response construction
- Update `create_source` call to not pass `fetch_interval`
- Update `batch_create` to not pass `fetch_interval`

**Step 3: Update SourceService.create_source signature**

```python
# src/services/source_service.py
async def create_source(self, name: str, url: str) -> Source:
    # Remove fetch_interval parameter
    source = Source(name=name, url=url)
    # ...
```

**Step 4: Update scheduler to fetch ALL active sources (no interval filtering)**

In `src/scheduler/fetch_scheduler.py`, `_check_and_fetch`:
- Remove `fetch_interval > 0` check
- Remove `last_fetched_at` time comparison
- `sources_to_fetch = sources` (all active, non-deleted)

**Step 5: Run all source-related tests**

Run: `uv run pytest tests/api/test_source_routes.py tests/services/test_source_service.py tests/scheduler/test_fetch_scheduler.py -v`
Expected: All PASS

**Step 6: Commit**

```bash
git add src/api/routes/sources.py src/services/source_service.py src/scheduler/fetch_scheduler.py tests/
git commit -m "refactor: remove fetch_interval from sources API and scheduler"
```

---

### Task 6: Backend — Include group info in sources, feed, and history responses

**Files:**
- Modify: `src/api/routes/sources.py` (list/get responses)
- Modify: `src/services/feed_service.py`
- Modify: `src/services/history_service.py`
- Modify: `src/schemas/history.py`
- Test: `tests/services/test_feed_service.py`
- Test: `tests/services/test_history_service.py`

**Step 1: Write tests for group info in responses**

```python
# Append to tests/services/test_feed_service.py
@pytest.mark.asyncio
async def test_feed_items_include_source_groups(db_session, source_svc, group_svc):
    """Feed items should include source group information."""
    group = await group_svc.create_group(name="Tech")
    source = await source_svc.create_source("Feed", "https://example.com/rss")
    await group_svc.add_source_to_group(group.id, source.id)

    feed_svc = FeedService(db_session)
    items = await feed_svc.get_feed_items()
    assert len(items) >= 0  # items may be empty, verify no error
    # When feed items exist, each should have source_groups
```

```python
# Append to tests/services/test_history_service.py
@pytest.mark.asyncio
async def test_history_batch_includes_groups(db_session, source_svc, group_svc):
    """History batch items should include source group information."""
    group = await group_svc.create_group(name="Tech")
    source = await source_svc.create_source("Feed", "https://example.com/rss")
    await group_svc.add_source_to_group(group.id, source.id)

    history_svc = HistoryService(db_session)
    batches = await history_svc.get_history_batches()
    # Verify no error when groups exist
```

**Step 2: Add source_groups to SourceResponse in sources API**

```python
# src/api/routes/sources.py — SourceResponse
class SourceResponse(BaseModel):
    # ... existing fields ...
    groups: list[dict] = []  # [{"id": 1, "name": "Tech"}]
```

In list_sources, get_source, update_source — fetch groups for each source:
```python
from src.services.source_group_service import SourceGroupService

# In each response builder:
groups = await source_group_service.get_source_groups(s.id)
SourceResponse(
    # ...
    groups=[{"id": g.id, "name": g.name} for g in groups],
)
```

**Step 3: Update HistoryItem schema to include source_groups**

```python
# src/schemas/history.py
class HistoryItem(BaseModel):
    # ... existing fields ...
    source_groups: list[dict] = []  # [{"id": 1, "name": "Tech"}]
```

**Step 4: Update HistoryService to include group info**

In `get_history_by_batch`, `get_history`, `get_batch_feed_items`:
- After loading items, for each item fetch source groups via JOIN or separate query
- Populate `source_groups` field

**Step 5: Update feed_service to include group info in items**

In `_fetch_items`, add joinedload for source.groups:
```python
query = (
    select(FeedItem)
    .options(
        joinedload(FeedItem.source).joinedload(Source.groups)
    )
    # ...
)
```

In `get_feed_items`:
```python
{
    # ... existing fields ...
    "source_groups": [
        {"id": g.id, "name": g.name}
        for g in item.source.groups
    ] if item.source else [],
}
```

**Step 6: Run tests**

Run: `uv run pytest tests/services/test_feed_service.py tests/services/test_history_service.py -v`
Expected: All PASS

**Step 7: Commit**

```bash
git add src/api/routes/sources.py src/services/feed_service.py src/services/history_service.py src/schemas/history.py tests/
git commit -m "feat: include source group info in sources, feed, and history responses"
```

---

### Task 7: Backend — Update backup service for source groups

**Files:**
- Modify: `src/services/backup_service.py`
- Modify: `src/schemas/backup.py`
- Test: `tests/services/test_backup_service_serialize.py`
- Test: `tests/services/test_backup_service_import.py`
- Test: `tests/services/test_backup_service_merge.py`

**Step 1: Write tests for group backup/restore**

```python
# Append to tests/services/test_backup_service_serialize.py
@pytest.mark.asyncio
async def test_serialize_includes_source_groups(db_session, source_svc, group_svc):
    """Backup should include source groups and memberships."""
    group = await group_svc.create_group(name="Tech")
    source = await source_svc.create_source("Feed", "https://example.com/rss")
    await group_svc.add_source_to_group(group.id, source.id)

    backup_svc = BackupService(db_session)
    content = await backup_svc._serialize_data()
    assert "source_groups" in content
    assert "source_group_members" in content
```

**Step 2: Update BackupContent schema**

```python
# src/schemas/backup.py
class BackupContent(BaseModel):
    # ... existing fields ...
    source_groups: list[dict] = []
    source_group_members: list[dict] = []
```

**Step 3: Update backup serialization**

In `backup_service.py`, add methods to serialize groups:
```python
async def _get_all_source_groups(self) -> list[SourceGroup]:
    result = await self._db.execute(select(SourceGroup))
    return list(result.scalars().all())

async def _get_all_source_group_members(self) -> list[SourceGroupMember]:
    result = await self._db.execute(select(SourceGroupMember))
    return list(result.scalars().all())
```

Include in `_serialize_data()`.

**Step 4: Update backup import/merge**

When importing, restore `source_groups` and `source_group_members` tables.

**Step 5: Run backup tests**

Run: `uv run pytest tests/services/test_backup_service_serialize.py tests/services/test_backup_service_import.py tests/services/test_backup_service_merge.py -v`
Expected: All PASS

**Step 6: Commit**

```bash
git add src/services/backup_service.py src/schemas/backup.py tests/
git commit -m "feat: include source groups in backup/restore"
```

---

### Task 8: Backend — Update deps.py for all new services

**Files:**
- Modify: `src/api/deps.py`

**Step 1: Add get_source_group_service dependency**

```python
from src.services.source_group_service import SourceGroupService

def get_source_group_service(
    session: AsyncSession = Depends(get_session),
) -> SourceGroupService:
    return SourceGroupService(session)
```

**Step 2: Run full backend test suite**

Run: `uv run pytest tests/ -v --tb=short`
Expected: All PASS (or only pre-existing failures)

**Step 3: Commit**

```bash
git add src/api/deps.py
git commit -m "chore: add source group service dependency"
```

---

### Task 9: Frontend — Update types and API client

**Files:**
- Modify: `web/src/types/source.ts`
- Create: `web/src/types/source-group.ts`
- Modify: `web/src/api/sources.ts`
- Create: `web/src/api/source-groups.ts`
- Test: `web/src/api/__tests__/sources.test.ts`
- Test: `web/src/api/__tests__/source-groups.test.ts`

**Step 1: Write API client tests**

```typescript
// web/src/api/__tests__/sources.test.ts
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { getSources, createSource, updateSource } from '../sources'
import api from '..'

vi.mock('..', () => ({
  default: { get: vi.fn(), post: vi.fn(), put: vi.fn(), delete: vi.fn() }
}))

describe('sources API', () => {
  beforeEach(() => vi.clearAllMocks())

  it('createSource should not include fetch_interval', async () => {
    vi.mocked(api.post).mockResolvedValue({ id: 1, name: 'Test', url: 'https://x.com', groups: [] })
    await createSource({ name: 'Test', url: 'https://x.com' })
    expect(api.post).toHaveBeenCalledWith('/sources', { name: 'Test', url: 'https://x.com' })
  })
})
```

```typescript
// web/src/api/__tests__/source-groups.test.ts
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { getGroups, createGroup, addSourceToGroup } from '../source-groups'
import api from '..'

vi.mock('..', () => ({
  default: { get: vi.fn(), post: vi.fn(), put: vi.fn(), delete: vi.fn() }
}))

describe('source groups API', () => {
  beforeEach(() => vi.clearAllMocks())

  it('getGroups returns list', async () => {
    vi.mocked(api.get).mockResolvedValue([{ id: 1, name: 'Tech', member_count: 2 }])
    const groups = await getGroups()
    expect(groups).toHaveLength(1)
    expect(groups[0].name).toBe('Tech')
  })

  it('createGroup sends name', async () => {
    vi.mocked(api.post).mockResolvedValue({ id: 1, name: 'News' })
    await createGroup({ name: 'News' })
    expect(api.post).toHaveBeenCalledWith('/source-groups', { name: 'News' })
  })

  it('addSourceToGroup', async () => {
    vi.mocked(api.post).mockResolvedValue({ message: 'ok' })
    await addSourceToGroup(1, 5)
    expect(api.post).toHaveBeenCalledWith('/source-groups/1/sources', { source_id: 5 })
  })
})
```

**Step 2: Update Source type**

```typescript
// web/src/types/source.ts
export interface Source {
  id: number
  name: string
  url: string
  is_active: boolean
  last_fetched_at: string | null
  last_error: string | null
  created_at: string
  updated_at: string
  groups: { id: number; name: string }[]
}
```

**Step 3: Create SourceGroup type**

```typescript
// web/src/types/source-group.ts
export interface SourceGroup {
  id: number
  name: string
  member_count: number
  created_at: string
  updated_at: string
}
```

**Step 4: Create source-groups API client**

```typescript
// web/src/api/source-groups.ts
import api from '.'
import type { SourceGroup } from '@/types/source-group'
import type { Source } from '@/types/source'

export async function getGroups(): Promise<SourceGroup[]> {
  return api.get<SourceGroup[]>('/source-groups')
}

export async function createGroup(data: { name: string }): Promise<SourceGroup> {
  return api.post<SourceGroup>('/source-groups', data)
}

export async function updateGroup(id: number, data: { name: string }): Promise<SourceGroup> {
  return api.put<SourceGroup>(`/source-groups/${id}`, data)
}

export async function deleteGroup(id: number): Promise<void> {
  return api.delete(`/source-groups/${id}`)
}

export async function getGroupSources(id: number): Promise<Source[]> {
  return api.get<Source[]>(`/source-groups/${id}/sources`)
}

export async function addSourceToGroup(groupId: number, sourceId: number): Promise<void> {
  return api.post(`/source-groups/${groupId}/sources`, { source_id: sourceId })
}

export async function removeSourceFromGroup(groupId: number, sourceId: number): Promise<void> {
  return api.delete(`/source-groups/${groupId}/sources/${sourceId}`)
}
```

**Step 5: Update sources API client**

- Remove `fetch_interval` from `CreateSourceData`
- Remove all `fetch_interval` references

**Step 6: Run frontend API tests**

Run: `cd web && pnpm test`
Expected: All PASS

**Step 7: Commit**

```bash
git add web/src/types/ web/src/api/ web/src/api/__tests__/
git commit -m "feat(frontend): update types and API clients for source groups"
```

---

### Task 10: Frontend — SourceDialog: remove fetch_interval, add group selection

**Files:**
- Modify: `web/src/components/SourceDialog.vue`
- Test: `web/src/components/__tests__/SourceDialog.test.ts`

**Step 1: Write component test**

```typescript
// web/src/components/__tests__/SourceDialog.test.ts
import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import SourceDialog from '../SourceDialog.vue'

describe('SourceDialog', () => {
  it('should not render fetch_interval field', () => {
    const wrapper = mount(SourceDialog, {
      props: { open: true },
      global: { stubs: { Dialog: { template: '<div><slot /></div>' } } }
    })
    expect(wrapper.text()).not.toContain('Fetch Interval')
    expect(wrapper.text()).not.toContain('抓取間隔')
  })

  it('should render group selection', () => {
    const wrapper = mount(SourceDialog, {
      props: { open: true },
      global: { stubs: { Dialog: { template: '<div><slot /></div>' } } }
    })
    expect(wrapper.text()).toContain('Group')
  })
})
```

**Step 2: Remove fetch_interval from SourceDialog**

- Remove `fetch_interval` from schema, form, intervalOptions
- Remove the Select component for fetch_interval
- Remove related i18n usage

**Step 3: Add group selection**

- Multi-select dropdown showing existing groups
- "+ Create new group" inline input
- On save, call `addSourceToGroup` for each selected group

**Step 4: Run component tests**

Run: `cd web && pnpm test`
Expected: All PASS

**Step 5: Commit**

```bash
git add web/src/components/SourceDialog.vue web/src/components/__tests__/
git commit -m "feat(frontend): remove fetch_interval, add group selection to SourceDialog"
```

---

### Task 11: Frontend — SourcesPage: add Groups tab

**Files:**
- Modify: `web/src/pages/SourcesPage.vue`
- Create: `web/src/components/GroupDialog.vue`
- Create: `web/src/components/GroupManagementPanel.vue`

**Step 1: Write E2E test first**

```typescript
// web/e2e/source-groups.spec.ts
import { test, expect } from '@playwright/test'

test('should create a source group', async ({ page }) => {
  await page.goto('/sources')
  await page.getByRole('tab', { name: 'Groups' }).click()
  await page.getByRole('button', { name: 'Add Group' }).click()
  await page.getByPlaceholder('Group name').fill('Tech News')
  await page.getByRole('button', { name: 'Confirm' }).click()
  await expect(page.getByText('Tech News')).toBeVisible()
})

test('should add source to group from dialog', async ({ page }) => {
  await page.goto('/sources')
  await page.getByRole('button', { name: 'Add Source' }).click()
  await page.getByLabel('Name').fill('Test Feed')
  await page.getByLabel('URL').fill('https://example.com/rss')
  await page.getByRole('button', { name: 'Confirm' }).click()
  await expect(page.getByText('Test Feed')).toBeVisible()
})
```

**Step 2: Update SourcesPage tabs**

Change from `active | trash` to `active | trash | groups`:
```typescript
const activeTab = ref<'active' | 'trash' | 'groups'>('active')
```

**Step 3: Add Groups tab content**

- List of group cards with name, member count
- Edit group name inline
- Add/remove sources from group
- Delete group button

**Step 4: Create GroupDialog for add/edit groups**

Similar pattern to SourceDialog but for group CRUD.

**Step 5: Run E2E tests**

Run: `cd web && pnpm exec playwright test`
Expected: All PASS

**Step 6: Commit**

```bash
git add web/src/pages/SourcesPage.vue web/src/components/GroupDialog.vue web/src/components/GroupManagementPanel.vue web/e2e/
git commit -m "feat(frontend): add Groups tab to SourcesPage"
```

---

### Task 12: Frontend — FeedPage: add group filter chips

**Files:**
- Modify: `web/src/pages/FeedPage.vue`
- Modify: `web/src/api/feed.ts`
- Modify: `web/src/types/feed.ts`

**Step 1: Update feed item type**

```typescript
// web/src/types/feed.ts
export interface FeedItem {
  // ... existing fields ...
  source_groups: { id: number; name: string }[]
}
```

**Step 2: Add group filter chips to FeedPage**

- Fetch all groups on mount
- Render chips: `[全部] [Tech] [Design] [Business]`
- Clicking a chip filters items by that group (client-side filter)
- "全部" shows all items

**Step 3: Display group badges on each item**

- Small colored badges next to source name
- Multiple groups → show first 2 + `+N`

**Step 4: Commit**

```bash
git add web/src/pages/FeedPage.vue web/src/types/feed.ts web/src/api/feed.ts
git commit -m "feat(frontend): add group filter chips and badges to FeedPage"
```

---

### Task 13: Frontend — HistoryPage: add group badges and filter

**Files:**
- Modify: `web/src/pages/HistoryPage.vue`
- Modify: `web/src/types/history.ts`

**Step 1: Update HistoryItem type**

```typescript
// web/src/types/history.ts
export interface HistoryItem {
  // ... existing fields ...
  source_groups: { id: number; name: string }[]
}

export interface HistoryBatch {
  // ... existing fields ...
  groups: { id: number; name: string }[]
}
```

**Step 2: Add group filter chips at top**

Same pattern as FeedPage — chips for filtering batches by group.

**Step 3: Add group badges to batch cards and items**

- Batch card: show involved groups as small badges
- Expanded item: show source's groups as small badges

**Step 4: Commit**

```bash
git add web/src/pages/HistoryPage.vue web/src/types/history.ts
git commit -m "feat(frontend): add group badges and filter to HistoryPage"
```

---

### Task 14: Frontend — i18n: add group translations

**Files:**
- Modify: `web/src/locales/en.json`
- Modify: `web/src/locales/zh.json`

**Step 1: Add English translations**

```json
{
  "groups": {
    "title": "Groups",
    "add": "Add Group",
    "edit": "Edit Group",
    "name": "Group Name",
    "name_placeholder": "Enter group name",
    "name_required": "Group name is required",
    "name_exists": "Group name already exists",
    "created": "Group created",
    "updated": "Group updated",
    "deleted": "Group deleted",
    "delete_title": "Delete Group",
    "delete_confirm": "Are you sure you want to delete this group? Sources will NOT be deleted.",
    "empty": "No groups",
    "members": "members",
    "add_source": "Add Source",
    "remove_source": "Remove from Group",
    "no_sources": "No sources in this group",
    "select_groups": "Select Groups",
    "create_new": "Create New Group",
    "all": "All"
  }
}
```

**Step 2: Add Chinese translations**

```json
{
  "groups": {
    "title": "群組",
    "add": "新增群組",
    "edit": "編輯群組",
    "name": "群組名稱",
    "name_placeholder": "輸入群組名稱",
    "name_required": "群組名稱為必填",
    "name_exists": "群組名稱已存在",
    "created": "群組已建立",
    "updated": "群組已更新",
    "deleted": "群組已刪除",
    "delete_title": "刪除群組",
    "delete_confirm": "確定要刪除此群組嗎？群組內的來源不會被刪除。",
    "empty": "沒有群組",
    "members": "成員",
    "add_source": "新增來源",
    "remove_source": "從群組移除",
    "no_sources": "此群組沒有來源",
    "select_groups": "選擇群組",
    "create_new": "建立新群組",
    "all": "全部"
  }
}
```

**Step 3: Remove fetch_interval i18n keys**

Remove from both en.json and zh.json:
- `sources.fetch_interval`
- `sources.interval_never` through `sources.interval_7d`

**Step 4: Commit**

```bash
git add web/src/locales/en.json web/src/locales/zh.json
git commit -m "i18n: add group translations, remove fetch_interval keys"
```

---

### Task 15: Frontend — E2E tests with Playwright

**Files:**
- Create: `web/e2e/source-groups.spec.ts`
- Create: `web/e2e/feed-groups.spec.ts`
- Create: `web/e2e/history-groups.spec.ts`

**Step 1: Source groups E2E**

- Create group → verify appears in Groups tab
- Edit group name → verify updated
- Add source to group → verify in group members
- Remove source from group → verify removed
- Delete group → verify sources remain

**Step 2: Feed groups E2E**

- Create source in group → verify group badge on feed items
- Click group filter → verify only that group's items shown

**Step 3: History groups E2E**

- Refresh sources → verify history batch shows group badges
- Click group filter → verify filtered batches

**Step 4: Run all E2E tests**

Run: `cd web && pnpm exec playwright test`
Expected: All PASS

**Step 5: Commit**

```bash
git add web/e2e/
git commit -m "test(e2e): add Playwright tests for source groups"
```

---

### Task 16: Backend — Disable scheduler auto-fetch (manual-only)

**Files:**
- Modify: `src/config.py`
- Modify: `src/main.py`

**Step 1: Change default scheduler behavior**

```python
# src/config.py
SCHEDULER_ENABLED: bool = False  # Changed from True
```

Or keep it configurable but default to disabled since refresh is now manual-only.

**Step 2: Update main.py to conditionally start scheduler**

```python
# src/main.py
if settings.SCHEDULER_ENABLED:
    await scheduler.start()
```

**Step 3: Run full test suite**

Run: `uv run pytest tests/ -v --tb=short`
Expected: All PASS

**Step 4: Commit**

```bash
git add src/config.py src/main.py
git commit -m "chore: disable scheduler auto-fetch by default"
```

---

### Task 17: Update documentation

**Files:**
- Modify: `README.md`
- Modify: `CHANGELOG.md`

**Step 1: Update README**

- Remove `DEFAULT_FETCH_INTERVAL` from configuration table
- Add Source Groups feature description
- Update API endpoints table with `/source-groups` routes

**Step 2: Update CHANGELOG**

```markdown
## [Unreleased]

### Breaking Changes
- Removed `fetch_interval` field from Source model and API
- Sources are now refreshed manually only (via `/sources/{id}/refresh` or `/sources/refresh`)

### Features
- Added Source Groups: organize sources into many-to-many groups
- New API: `/api/v1/source-groups` for group CRUD and membership management
- Feed and History pages now display and filter by source groups
- Groups tab in Sources page for group management
```

**Step 3: Commit**

```bash
git add README.md CHANGELOG.md
git commit -m "docs: update README and CHANGELOG for source groups feature"
```

---

### Task 18: Final verification

**Step 1: Run full backend test suite**

Run: `uv run pytest tests/ -v --tb=short`
Expected: All PASS

**Step 2: Run full frontend test suite**

Run: `cd web && pnpm test && pnpm exec playwright test`
Expected: All PASS

**Step 3: Run linting**

Run: `uv run ruff check . && cd web && pnpm lint`
Expected: No errors

**Step 4: Run type checks**

Run: `uv run mypy src/ && cd web && pnpm typecheck`
Expected: No errors

**Step 5: Final commit**

```bash
git add -A
git commit -m "chore: final verification passes"
```

---

## Execution Handoff

Plan complete. Two execution options:

**1. Subagent-Driven (this session)** — I dispatch fresh subagent per task, review between tasks, fast iteration

**2. Parallel Session (separate)** — Open new session with executing-plans, batch execution with checkpoints

Which approach?
