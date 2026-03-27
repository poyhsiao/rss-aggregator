# Trash and Restore Feature Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement trash/restore functionality with partial unique indexes to allow re-adding deleted sources with same name/URL.

**Architecture:** Database partial unique indexes + application layer defensive checks. Restore with conflict detection and user choice.

**Tech Stack:** Python 3.12+, FastAPI, SQLAlchemy, Alembic, Vue 3, TypeScript, vue-i18n

---

## Phase 1: Database Migration

### Task 1.1: Create Migration for Partial Unique Indexes

**Files:**
- Create: `alembic/versions/xxxx_add_partial_unique_indexes.py`

**Step 1: Generate migration file**

Run: `alembic revision -m "add_partial_unique_indexes"`

**Step 2: Write migration content**

```python
"""add_partial_unique_indexes

Revision ID: xxxx
Revises: previous_revision
Create Date: 2026-03-27

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'xxxx'
down_revision: Union[str, Sequence[str], None] = None  # Update with actual previous
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create partial unique indexes for active sources."""
    # Drop existing unconditional unique constraint on url
    op.drop_constraint('sources_url_key', 'sources', type_='unique')
    
    # Create partial unique indexes (only for non-deleted records)
    op.execute("""
        CREATE UNIQUE INDEX uq_sources_url_active 
        ON sources(url) 
        WHERE deleted_at IS NULL
    """)
    
    op.execute("""
        CREATE UNIQUE INDEX uq_sources_name_active 
        ON sources(name) 
        WHERE deleted_at IS NULL
    """)


def downgrade() -> None:
    """Revert to unconditional unique constraint."""
    op.execute("DROP INDEX IF EXISTS uq_sources_name_active")
    op.execute("DROP INDEX IF EXISTS uq_sources_url_active")
    op.create_unique_constraint('sources_url_key', 'sources', ['url'])
```

**Step 3: Run migration**

Run: `alembic upgrade head`
Expected: Migration applies successfully

**Step 4: Commit**

```bash
git add alembic/versions/xxxx_add_partial_unique_indexes.py
git commit -m "feat(db): add partial unique indexes for sources"
```

---

### Task 1.2: Update Source Model

**Files:**
- Modify: `src/models/source.py:24`

**Step 1: Remove unique=True from url field**

Change:
```python
url: Mapped[str] = mapped_column(String(2048), unique=True)
```

To:
```python
url: Mapped[str] = mapped_column(String(2048), index=True)
```

**Step 2: Add table args for documentation**

Add after the field definitions:
```python
__table_args__ = (
    # Note: Uniqueness is enforced via partial indexes created in migration
    # uq_sources_url_active and uq_sources_name_active
)
```

**Step 3: Run tests to verify no regression**

Run: `pytest tests/services/test_source_service.py -v`
Expected: All existing tests pass

**Step 4: Commit**

```bash
git add src/models/source.py
git commit -m "refactor: remove unique constraint from model, rely on partial indexes"
```

---

## Phase 2: Backend Service Layer

### Task 2.1: Add get_trash_sources Method

**Files:**
- Modify: `src/services/source_service.py`
- Test: `tests/services/test_source_service.py`

**Step 1: Write the failing test**

```python
# tests/services/test_source_service.py

@pytest.mark.asyncio
async def test_get_trash_sources(db_session: AsyncSession):
    """Test getting only soft-deleted sources."""
    service = SourceService(db_session)
    
    # Create and delete a source
    source = await service.create_source("Trash Source", "https://trash.com/rss")
    await service.delete_source(source.id)
    
    # Create another active source
    active = await service.create_source("Active Source", "https://active.com/rss")
    
    trash = await service.get_trash_sources()
    
    assert len(trash) == 1
    assert trash[0].name == "Trash Source"
    assert trash[0].deleted_at is not None
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/services/test_source_service.py::test_get_trash_sources -v`
Expected: FAIL with "AttributeError: 'SourceService' object has no attribute 'get_trash_sources'"

**Step 3: Write minimal implementation**

```python
# src/services/source_service.py

async def get_trash_sources(self) -> list[Source]:
    """Get all soft-deleted sources.
    
    Returns:
        List of soft-deleted Source instances.
    """
    result = await self.session.execute(
        select(Source).where(Source.deleted_at.is_not(None))
    )
    return list(result.scalars().all())
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/services/test_source_service.py::test_get_trash_sources -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/services/source_service.py tests/services/test_source_service.py
git commit -m "feat(service): add get_trash_sources method"
```

---

### Task 2.2: Add get_trash_source Method

**Files:**
- Modify: `src/services/source_service.py`
- Test: `tests/services/test_source_service.py`

**Step 1: Write the failing test**

```python
@pytest.mark.asyncio
async def test_get_trash_source(db_session: AsyncSession):
    """Test getting a single trash source by ID."""
    service = SourceService(db_session)
    
    source = await service.create_source("To Delete", "https://delete.com/rss")
    await service.delete_source(source.id)
    
    trash = await service.get_trash_source(source.id)
    
    assert trash is not None
    assert trash.name == "To Delete"
    assert trash.deleted_at is not None
    
    # Non-existent or active source should return None
    active = await service.create_source("Active", "https://active2.com/rss")
    assert await service.get_trash_source(active.id) is None
    assert await service.get_trash_source(9999) is None
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/services/test_source_service.py::test_get_trash_source -v`
Expected: FAIL with "AttributeError"

**Step 3: Write minimal implementation**

```python
async def get_trash_source(self, source_id: int) -> Source | None:
    """Get a single trash source by ID.
    
    Args:
        source_id: ID of the source to retrieve.
        
    Returns:
        Source if found and soft-deleted, None otherwise.
    """
    result = await self.session.execute(
        select(Source).where(
            Source.id == source_id,
            Source.deleted_at.is_not(None)
        )
    )
    return result.scalar_one_or_none()
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/services/test_source_service.py::test_get_trash_source -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/services/source_service.py tests/services/test_source_service.py
git commit -m "feat(service): add get_trash_source method"
```

---

### Task 2.3: Add check_restore_conflict Method

**Files:**
- Modify: `src/services/source_service.py`
- Test: `tests/services/test_source_service.py`

**Step 1: Write the failing tests**

```python
@pytest.mark.asyncio
async def test_check_restore_conflict_none(db_session: AsyncSession):
    """Test no conflict when name and URL are unique."""
    service = SourceService(db_session)
    
    source = await service.create_source("Unique", "https://unique.com/rss")
    await service.delete_source(source.id)
    
    conflict = await service.check_restore_conflict(source.id)
    
    assert conflict is None


@pytest.mark.asyncio
async def test_check_restore_conflict_name(db_session: AsyncSession):
    """Test conflict detection for duplicate name."""
    service = SourceService(db_session)
    
    # Create deleted source
    deleted = await service.create_source("Same Name", "https://deleted.com/rss")
    await service.delete_source(deleted.id)
    
    # Create active source with same name
    await service.create_source("Same Name", "https://different.com/rss")
    
    conflict = await service.check_restore_conflict(deleted.id)
    
    assert conflict is not None
    assert conflict["conflict_type"] == "name"


@pytest.mark.asyncio
async def test_check_restore_conflict_url(db_session: AsyncSession):
    """Test conflict detection for duplicate URL."""
    service = SourceService(db_session)
    
    deleted = await service.create_source("Deleted", "https://same-url.com/rss")
    await service.delete_source(deleted.id)
    
    await service.create_source("Different Name", "https://same-url.com/rss")
    
    conflict = await service.check_restore_conflict(deleted.id)
    
    assert conflict is not None
    assert conflict["conflict_type"] == "url"


@pytest.mark.asyncio
async def test_check_restore_conflict_both(db_session: AsyncSession):
    """Test conflict detection for both name and URL."""
    service = SourceService(db_session)
    
    deleted = await service.create_source("Both Match", "https://both.com/rss")
    await service.delete_source(deleted.id)
    
    await service.create_source("Both Match", "https://both.com/rss")
    
    conflict = await service.check_restore_conflict(deleted.id)
    
    assert conflict is not None
    assert conflict["conflict_type"] == "both"
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/services/test_source_service.py::test_check_restore_conflict -v`
Expected: FAIL with "AttributeError"

**Step 3: Write minimal implementation**

```python
async def check_restore_conflict(self, source_id: int) -> dict | None:
    """Check if restoring would cause a conflict.
    
    Args:
        source_id: ID of the trash source to check.
        
    Returns:
        None if no conflict, or dict with 'existing_item' and 'conflict_type'.
        
    Raises:
        ValueError: If trash item not found.
    """
    trash_source = await self.get_trash_source(source_id)
    if trash_source is None:
        raise ValueError(f"Trash source with id {source_id} not found")
    
    # Check name conflict
    name_conflict = await self.session.execute(
        select(Source).where(
            Source.name == trash_source.name,
            Source.deleted_at.is_(None)
        )
    )
    name_existing = name_conflict.scalar_one_or_none()
    
    # Check URL conflict
    url_conflict = await self.session.execute(
        select(Source).where(
            Source.url == trash_source.url,
            Source.deleted_at.is_(None)
        )
    )
    url_existing = url_conflict.scalar_one_or_none()
    
    existing = name_existing or url_existing
    if existing is None:
        return None
    
    # Determine conflict type
    if name_existing and url_existing:
        conflict_type = "both"
    elif name_existing:
        conflict_type = "name"
    else:
        conflict_type = "url"
    
    return {
        "existing_item": existing,
        "conflict_type": conflict_type
    }
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/services/test_source_service.py::test_check_restore_conflict -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/services/source_service.py tests/services/test_source_service.py
git commit -m "feat(service): add check_restore_conflict method"
```

---

### Task 2.4: Add restore_source Method

**Files:**
- Modify: `src/services/source_service.py`
- Test: `tests/services/test_source_service.py`

**Step 1: Write the failing tests**

```python
@pytest.mark.asyncio
async def test_restore_source_no_conflict(db_session: AsyncSession):
    """Test restoring without conflict."""
    service = SourceService(db_session)
    
    source = await service.create_source("To Restore", "https://restore.com/rss")
    await service.delete_source(source.id)
    
    restored = await service.restore_source(source.id)
    
    assert restored.deleted_at is None
    assert restored.name == "To Restore"


@pytest.mark.asyncio
async def test_restore_source_overwrite(db_session: AsyncSession):
    """Test restoring with overwrite."""
    service = SourceService(db_session)
    
    deleted = await service.create_source("Overwrite", "https://overwrite.com/rss")
    deleted.fetch_interval = 900
    await service.delete_source(deleted.id)
    
    # Create conflicting source
    existing = await service.create_source("Overwrite", "https://overwrite.com/rss")
    existing.fetch_interval = 1800
    
    restored = await service.restore_source(deleted.id, overwrite=True)
    
    assert restored.deleted_at is None
    assert restored.fetch_interval == 900  # Original value preserved
    
    # Existing should now be soft-deleted
    await db_session.refresh(existing)
    assert existing.deleted_at is not None


@pytest.mark.asyncio
async def test_restore_source_not_found(db_session: AsyncSession):
    """Test restoring non-existent trash item."""
    service = SourceService(db_session)
    
    with pytest.raises(ValueError, match="not found"):
        await service.restore_source(9999)
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/services/test_source_service.py::test_restore_source -v`
Expected: FAIL with "AttributeError"

**Step 3: Write minimal implementation**

```python
async def restore_source(self, source_id: int, overwrite: bool = False) -> Source:
    """Restore a soft-deleted source.
    
    Args:
        source_id: ID of the source to restore.
        overwrite: If True, soft-delete conflicting existing sources.
        
    Returns:
        The restored Source instance.
        
    Raises:
        ValueError: If source not found or conflict exists without overwrite.
    """
    trash_source = await self.get_trash_source(source_id)
    if trash_source is None:
        raise ValueError(f"Trash source with id {source_id} not found")
    
    if overwrite:
        # Soft-delete any conflicting sources
        conflict = await self.check_restore_conflict(source_id)
        if conflict:
            conflict["existing_item"].soft_delete()
    else:
        # Check for conflict without overwrite
        conflict = await self.check_restore_conflict(source_id)
        if conflict:
            raise ValueError(
                f"Conflict detected: {conflict['conflict_type']} already exists"
            )
    
    # Restore the source
    trash_source.deleted_at = None
    await self.session.commit()
    await self.session.refresh(trash_source)
    return trash_source
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/services/test_source_service.py::test_restore_source -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/services/source_service.py tests/services/test_source_service.py
git commit -m "feat(service): add restore_source method"
```

---

### Task 2.5: Add permanent_delete_source Method

**Files:**
- Modify: `src/services/source_service.py`
- Test: `tests/services/test_source_service.py`

**Step 1: Write the failing test**

```python
@pytest.mark.asyncio
async def test_permanent_delete_source(db_session: AsyncSession):
    """Test permanently deleting a source."""
    service = SourceService(db_session)
    
    source = await service.create_source("To Perma Delete", "https://perma.com/rss")
    await service.delete_source(source.id)
    source_id = source.id
    
    await service.permanent_delete_source(source_id)
    
    # Should not exist at all
    result = await db_session.execute(
        select(Source).where(Source.id == source_id)
    )
    assert result.scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_permanent_delete_source_not_in_trash(db_session: AsyncSession):
    """Test permanent delete fails for non-trash item."""
    service = SourceService(db_session)
    
    source = await service.create_source("Active", "https://active3.com/rss")
    
    with pytest.raises(ValueError, match="not found"):
        await service.permanent_delete_source(source.id)
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/services/test_source_service.py::test_permanent_delete_source -v`
Expected: FAIL with "AttributeError"

**Step 3: Write minimal implementation**

```python
async def permanent_delete_source(self, source_id: int) -> None:
    """Permanently delete a soft-deleted source.
    
    Args:
        source_id: ID of the source to permanently delete.
        
    Raises:
        ValueError: If source not found or not in trash.
    """
    source = await self.get_trash_source(source_id)
    if source is None:
        raise ValueError(f"Trash source with id {source_id} not found")
    
    await self.session.delete(source)
    await self.session.commit()
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/services/test_source_service.py::test_permanent_delete_source -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/services/source_service.py tests/services/test_source_service.py
git commit -m "feat(service): add permanent_delete_source method"
```

---

### Task 2.6: Add clear_trash Method

**Files:**
- Modify: `src/services/source_service.py`
- Test: `tests/services/test_source_service.py`

**Step 1: Write the failing test**

```python
@pytest.mark.asyncio
async def test_clear_trash(db_session: AsyncSession):
    """Test clearing all trash items."""
    service = SourceService(db_session)
    
    # Create and delete multiple sources
    s1 = await service.create_source("Trash 1", "https://trash1.com/rss")
    s2 = await service.create_source("Trash 2", "https://trash2.com/rss")
    s3 = await service.create_source("Active", "https://active4.com/rss")
    
    await service.delete_source(s1.id)
    await service.delete_source(s2.id)
    
    count = await service.clear_trash()
    
    assert count == 2
    
    trash = await service.get_trash_sources()
    assert len(trash) == 0
    
    # Active source should remain
    active = await service.get_source(s3.id)
    assert active is not None
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/services/test_source_service.py::test_clear_trash -v`
Expected: FAIL with "AttributeError"

**Step 3: Write minimal implementation**

```python
async def clear_trash(self) -> int:
    """Permanently delete all soft-deleted sources.
    
    Returns:
        Number of sources permanently deleted.
    """
    result = await self.session.execute(
        select(Source).where(Source.deleted_at.is_not(None))
    )
    sources = list(result.scalars().all())
    count = len(sources)
    
    for source in sources:
        await self.session.delete(source)
    
    await self.session.commit()
    return count
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/services/test_source_service.py::test_clear_trash -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/services/source_service.py tests/services/test_source_service.py
git commit -m "feat(service): add clear_trash method"
```

---

## Phase 3: Backend API Routes

### Task 3.1: Create Trash Routes File

**Files:**
- Create: `src/api/routes/trash.py`
- Test: `tests/api/test_trash_routes.py`

**Step 1: Write the route file**

```python
"""Trash management API routes."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from src.api.deps import get_source_service, require_api_key
from src.services.source_service import SourceService
from src.utils.time import to_iso_string

router = APIRouter(prefix="/trash", tags=["trash"])


class TrashItemResponse(BaseModel):
    """Schema for trash item response."""
    id: int
    name: str
    url: str
    fetch_interval: int
    is_active: bool
    deleted_at: str
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class RestoreRequest(BaseModel):
    """Schema for restore request."""
    conflict_resolution: str | None = None  # "overwrite" | "keep_existing"


class RestoreResponse(BaseModel):
    """Schema for restore response."""
    id: int
    name: str
    restored: bool


class ConflictResponse(BaseModel):
    """Schema for conflict response."""
    error: str
    message: str
    conflict: dict


@router.get("", response_model=list[TrashItemResponse])
async def list_trash(
    source_service: SourceService = Depends(get_source_service),
    _: str = Depends(require_api_key),
) -> list[TrashItemResponse]:
    """List all trash items."""
    sources = await source_service.get_trash_sources()
    return [
        TrashItemResponse(
            id=s.id,
            name=s.name,
            url=s.url,
            fetch_interval=s.fetch_interval,
            is_active=s.is_active,
            deleted_at=to_iso_string(s.deleted_at) or "",
            created_at=to_iso_string(s.created_at) or "",
            updated_at=to_iso_string(s.updated_at) or "",
        )
        for s in sources
    ]


@router.post("/{source_id}/restore")
async def restore_source(
    source_id: int,
    request: RestoreRequest = None,
    source_service: SourceService = Depends(get_source_service),
    _: str = Depends(require_api_key),
):
    """Restore a trash item.
    
    Returns 409 if conflict detected and no resolution provided.
    """
    request = request or RestoreRequest()
    
    try:
        # Check for conflict
        conflict = await source_service.check_restore_conflict(source_id)
        
        if conflict:
            if request.conflict_resolution == "overwrite":
                source = await source_service.restore_source(source_id, overwrite=True)
                return RestoreResponse(id=source.id, name=source.name, restored=True)
            elif request.conflict_resolution == "keep_existing":
                # Get trash item for response
                trash = await source_service.get_trash_source(source_id)
                return RestoreResponse(id=trash.id, name=trash.name, restored=False)
            else:
                # Return conflict info
                trash = await source_service.get_trash_source(source_id)
                raise HTTPException(
                    status_code=409,
                    detail={
                        "error": "conflict_detected",
                        "message": "A source with this name or URL already exists",
                        "conflict": {
                            "trash_item": {
                                "id": trash.id,
                                "name": trash.name,
                                "url": trash.url,
                            },
                            "existing_item": {
                                "id": conflict["existing_item"].id,
                                "name": conflict["existing_item"].name,
                                "url": conflict["existing_item"].url,
                            },
                            "conflict_type": conflict["conflict_type"],
                        },
                    }
                )
        
        # No conflict, restore directly
        source = await source_service.restore_source(source_id)
        return RestoreResponse(id=source.id, name=source.name, restored=True)
        
    except ValueError as e:
        if "not found" in str(e):
            raise HTTPException(status_code=404, detail="Trash item not found")
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{source_id}")
async def permanent_delete_source(
    source_id: int,
    source_service: SourceService = Depends(get_source_service),
    _: str = Depends(require_api_key),
):
    """Permanently delete a trash item."""
    try:
        await source_service.permanent_delete_source(source_id)
        return {"deleted": True}
    except ValueError as e:
        raise HTTPException(status_code=404, detail="Trash item not found")


@router.delete("")
async def clear_trash(
    source_service: SourceService = Depends(get_source_service),
    _: str = Depends(require_api_key),
):
    """Clear all trash items."""
    count = await source_service.clear_trash()
    return {"deleted_count": count}
```

**Step 2: Register router in __init__.py**

Add to `src/api/routes/__init__.py`:
```python
from src.api.routes.trash import router as trash_router

# Include in app router setup
```

**Step 3: Commit**

```bash
git add src/api/routes/trash.py src/api/routes/__init__.py
git commit -m "feat(api): add trash routes"
```

---

### Task 3.2: Add API Tests

**Files:**
- Create: `tests/api/test_trash_routes.py`

**Step 1: Write API tests**

```python
"""Tests for trash API routes."""

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient

from src.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.mark.asyncio
async def test_list_trash(async_client: AsyncClient, api_key: str):
    """Test listing trash items."""
    # Create and delete a source first
    create_resp = await async_client.post(
        "/api/v1/sources",
        json={"name": "Trash Test", "url": "https://trash-test.com/rss"},
        headers={"X-API-Key": api_key},
    )
    source_id = create_resp.json()["id"]
    
    await async_client.delete(
        f"/api/v1/sources/{source_id}",
        headers={"X-API-Key": api_key},
    )
    
    resp = await async_client.get(
        "/api/v1/trash",
        headers={"X-API-Key": api_key},
    )
    
    assert resp.status_code == 200
    assert len(resp.json()) >= 1
    assert any(s["name"] == "Trash Test" for s in resp.json())


@pytest.mark.asyncio
async def test_restore_no_conflict(async_client: AsyncClient, api_key: str):
    """Test restoring without conflict."""
    # Create, delete, then restore
    create_resp = await async_client.post(
        "/api/v1/sources",
        json={"name": "Restore Test", "url": "https://restore-test.com/rss"},
        headers={"X-API-Key": api_key},
    )
    source_id = create_resp.json()["id"]
    
    await async_client.delete(
        f"/api/v1/sources/{source_id}",
        headers={"X-API-Key": api_key},
    )
    
    resp = await async_client.post(
        f"/api/v1/trash/{source_id}/restore",
        headers={"X-API-Key": api_key},
    )
    
    assert resp.status_code == 200
    assert resp.json()["restored"] is True


@pytest.mark.asyncio
async def test_restore_conflict_returns_409(async_client: AsyncClient, api_key: str):
    """Test restore returns 409 on conflict."""
    # Create and delete
    create_resp = await async_client.post(
        "/api/v1/sources",
        json={"name": "Conflict Test", "url": "https://conflict-test.com/rss"},
        headers={"X-API-Key": api_key},
    )
    source_id = create_resp.json()["id"]
    
    await async_client.delete(
        f"/api/v1/sources/{source_id}",
        headers={"X-API-Key": api_key},
    )
    
    # Create new with same URL
    await async_client.post(
        "/api/v1/sources",
        json={"name": "New Conflict", "url": "https://conflict-test.com/rss"},
        headers={"X-API-Key": api_key},
    )
    
    # Try to restore without resolution
    resp = await async_client.post(
        f"/api/v1/trash/{source_id}/restore",
        headers={"X-API-Key": api_key},
    )
    
    assert resp.status_code == 409
    assert resp.json()["detail"]["error"] == "conflict_detected"


@pytest.mark.asyncio
async def test_permanent_delete(async_client: AsyncClient, api_key: str):
    """Test permanent delete."""
    create_resp = await async_client.post(
        "/api/v1/sources",
        json={"name": "Permanent Delete", "url": "https://permanent.com/rss"},
        headers={"X-API-Key": api_key},
    )
    source_id = create_resp.json()["id"]
    
    await async_client.delete(
        f"/api/v1/sources/{source_id}",
        headers={"X-API-Key": api_key},
    )
    
    resp = await async_client.delete(
        f"/api/v1/trash/{source_id}",
        headers={"X-API-Key": api_key},
    )
    
    assert resp.status_code == 200
    assert resp.json()["deleted"] is True
```

**Step 2: Run tests**

Run: `pytest tests/api/test_trash_routes.py -v`
Expected: All tests pass

**Step 3: Commit**

```bash
git add tests/api/test_trash_routes.py
git commit -m "test(api): add trash routes tests"
```

---

## Phase 4: Frontend Implementation

### Task 4.1: Create Trash API Functions

**Files:**
- Create: `web/src/api/trash.ts`

**Step 1: Write API functions**

```typescript
// web/src/api/trash.ts
import type { Source } from '@/types/source'

const API_BASE = '/api/v1'

export interface TrashItem extends Source {
  deleted_at: string
}

export interface ConflictInfo {
  trash_item: {
    id: number
    name: string
    url: string
  }
  existing_item: {
    id: number
    name: string
    url: string
  }
  conflict_type: 'name' | 'url' | 'both'
}

export async function getTrashItems(): Promise<TrashItem[]> {
  const response = await fetch(`${API_BASE}/trash`, {
    headers: {
      'X-API-Key': localStorage.getItem('apiKey') || '',
    },
  })
  if (!response.ok) throw new Error('Failed to fetch trash items')
  return response.json()
}

export async function restoreSource(
  sourceId: number,
  conflictResolution?: 'overwrite' | 'keep_existing'
): Promise<{ id: number; name: string; restored: boolean }> {
  const response = await fetch(`${API_BASE}/trash/${sourceId}/restore`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-API-Key': localStorage.getItem('apiKey') || '',
    },
    body: JSON.stringify({ conflict_resolution: conflictResolution }),
  })
  
  if (response.status === 409) {
    const error = await response.json()
    const conflictError = new Error('Conflict detected') as Error & { conflict?: ConflictInfo }
    conflictError.conflict = error.detail.conflict
    throw conflictError
  }
  
  if (!response.ok) throw new Error('Failed to restore source')
  return response.json()
}

export async function permanentDeleteSource(sourceId: number): Promise<void> {
  const response = await fetch(`${API_BASE}/trash/${sourceId}`, {
    method: 'DELETE',
    headers: {
      'X-API-Key': localStorage.getItem('apiKey') || '',
    },
  })
  if (!response.ok) throw new Error('Failed to permanently delete source')
}

export async function clearTrash(): Promise<{ deleted_count: number }> {
  const response = await fetch(`${API_BASE}/trash`, {
    method: 'DELETE',
    headers: {
      'X-API-Key': localStorage.getItem('apiKey') || '',
    },
  })
  if (!response.ok) throw new Error('Failed to clear trash')
  return response.json()
}
```

**Step 2: Commit**

```bash
git add web/src/api/trash.ts
git commit -m "feat(frontend): add trash API functions"
```

---

### Task 4.2: Create RestoreConflictDialog Component

**Files:**
- Create: `web/src/components/RestoreConflictDialog.vue`

**Step 1: Write component**

```vue
<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import type { ConflictInfo } from '@/api/trash'
import Button from '@/components/ui/Button.vue'

const props = defineProps<{
  conflict: ConflictInfo
}>()

const emit = defineEmits<{
  overwrite: []
  keepExisting: []
  cancel: []
}>()

const { t } = useI18n()
</script>

<template>
  <div class="space-y-4">
    <p class="text-neutral-600 dark:text-neutral-400">
      {{ t('sources.conflict.message') }}
    </p>
    
    <div class="grid gap-3">
      <div class="p-3 bg-neutral-50 dark:bg-neutral-800 rounded-lg">
        <div class="text-sm font-medium text-neutral-500 dark:text-neutral-400 mb-2">
          {{ t('sources.conflict.existing') }}
        </div>
        <div class="font-medium">{{ conflict.existing_item.name }}</div>
        <div class="text-sm text-neutral-500 truncate">{{ conflict.existing_item.url }}</div>
      </div>
      
      <div class="p-3 bg-neutral-50 dark:bg-neutral-800 rounded-lg border-2 border-amber-200 dark:border-amber-800">
        <div class="text-sm font-medium text-neutral-500 dark:text-neutral-400 mb-2">
          {{ t('sources.conflict.from_trash') }}
        </div>
        <div class="font-medium">{{ conflict.trash_item.name }}</div>
        <div class="text-sm text-neutral-500 truncate">{{ conflict.trash_item.url }}</div>
      </div>
    </div>
    
    <div class="flex flex-wrap gap-2 justify-end pt-2">
      <Button variant="outline" @click="emit('cancel')">
        {{ t('sources.conflict.cancel') }}
      </Button>
      <Button variant="outline" @click="emit('keepExisting')">
        {{ t('sources.conflict.keep_existing') }}
      </Button>
      <Button @click="emit('overwrite')">
        {{ t('sources.conflict.overwrite') }}
      </Button>
    </div>
  </div>
</template>
```

**Step 2: Commit**

```bash
git add web/src/components/RestoreConflictDialog.vue
git commit -m "feat(frontend): add RestoreConflictDialog component"
```

---

### Task 4.3: Update SourcesPage with Tabs

**Files:**
- Modify: `web/src/pages/SourcesPage.vue`

**Step 1: Add tabs and trash functionality**

See design doc for full implementation. Key changes:
- Add tab state: `activeTab = ref<'active' | 'trash'>('active')`
- Add trash-related state
- Add RestoreConflictDialog integration
- Add clear trash functionality

**Step 2: Commit**

```bash
git add web/src/pages/SourcesPage.vue
git commit -m "feat(frontend): add trash tab to SourcesPage"
```

---

### Task 4.4: Add i18n Translations

**Files:**
- Modify: `web/src/locales/en.json`
- Modify: `web/src/locales/zh.json`

**Step 1: Add translations**

As defined in the design doc.

**Step 2: Commit**

```bash
git add web/src/locales/en.json web/src/locales/zh.json
git commit -m "feat(i18n): add trash and conflict translations"
```

---

## Phase 5: Integration

### Task 5.1: Run Full Test Suite

**Step 1: Run all backend tests**

Run: `pytest tests/ -v`
Expected: All tests pass

**Step 2: Commit**

```bash
git commit --allow-empty -m "test: verify all tests pass"
```

---

## Summary

**Files Created:**
- `alembic/versions/xxxx_add_partial_unique_indexes.py`
- `src/api/routes/trash.py`
- `web/src/api/trash.ts`
- `web/src/components/RestoreConflictDialog.vue`
- `tests/api/test_trash_routes.py`

**Files Modified:**
- `src/models/source.py`
- `src/services/source_service.py`
- `src/api/routes/__init__.py`
- `web/src/pages/SourcesPage.vue`
- `web/src/locales/en.json`
- `web/src/locales/zh.json`
- `tests/services/test_source_service.py`