# Feature Flags Persistence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 將 Feature Flags 從 localStorage 擴展到資料庫持久化，並透過 Export/Import Backup 實現跨瀏覽器同步，同時將 UI 改為 DebugDialog 緊湊樣式

**Architecture:** 後端建立 FeatureFlag model + API，前端修改 FeatureFlagsStore 同步 API + 重新設計 Dialog UI，Backup Service 新增 feature_flags 匯入/匯出

**Tech Stack:** Python (FastAPI, SQLAlchemy, pytest), Vue 3 (Pinia, Playwright), Alembic

---

## Phase 1: 後端 Model & API（TDD）

### Task 1: 建立 FeatureFlag Model

**Files:**
- Create: `src/models/feature_flag.py`
- Modify: `src/models/__init__.py`（匯出 FeatureFlag）
- Test: `tests/models/test_feature_flag.py`

- [ ] **Step 1: 寫測試**

Create: `tests/models/test_feature_flag.py`

```python
"""Tests for FeatureFlag model."""

import pytest
from datetime import datetime

from src.models.feature_flag import FeatureFlag


class TestFeatureFlag:
    """Test FeatureFlag model."""

    def test_create_feature_flag(self, db_session):
        """建立新的 feature flag"""
        flag = FeatureFlag(key="groups_enabled", value="true")
        db_session.add(flag)
        db_session.commit()
        
        assert flag.key == "groups_enabled"
        assert flag.value == "true"
        assert flag.updated_at is not None

    def test_read_feature_flag(self, db_session):
        """讀取已存在的 feature flag"""
        flag = FeatureFlag(key="groups_enabled", value="false")
        db_session.add(flag)
        db_session.commit()
        
        result = db_session.get(FeatureFlag, "groups_enabled")
        assert result is not None
        assert result.value == "false"

    def test_feature_flag_repr(self):
        """FeatureFlag __repr__ 格式正確"""
        flag = FeatureFlag(key="groups_enabled", value="true")
        assert repr(flag) == "<FeatureFlag(key=groups_enabled, value=true)>"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/models/test_feature_flag.py -v`
Expected: FAIL — ModuleNotFoundError: No module named 'src.models.feature_flag'

- [ ] **Step 3: Write minimal implementation**

Create: `src/models/feature_flag.py`

```python
"""Feature flag settings model."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base
from src.utils.time import now

if TYPE_CHECKING:
    pass


class FeatureFlag(Base):
    """Feature flag settings for user preferences."""

    __tablename__ = "feature_flags"

    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    value: Mapped[str] = mapped_column(String(50), nullable=False, default="true")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default_factory=now, nullable=False, onupdate=func.now()
    )

    def __repr__(self) -> str:
        return f"<FeatureFlag(key={self.key}, value={self.value})>"
```

Modify: `src/models/__init__.py` — add FeatureFlag to imports and __all__

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/models/test_feature_flag.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/models/feature_flag.py src/models/__init__.py tests/models/test_feature_flag.py
git commit -m "feat(ff): add FeatureFlag model"
```

---

### Task 2: 建立 FeatureFlagService

**Files:**
- Create: `src/services/feature_flag_service.py`
- Test: `tests/services/test_feature_flag_service.py`

- [ ] **Step 1: 寫測試**

Create: `tests/services/test_feature_flag_service.py`

```python
"""Tests for FeatureFlagService."""

import pytest

from src.services.feature_flag_service import FeatureFlagService


class TestFeatureFlagService:
    """Test FeatureFlagService."""

    @pytest.fixture
    def service(self, db_session):
        return FeatureFlagService(db_session)

    @pytest.fixture
    def seed_flags(self, db_session):
        from src.models.feature_flag import FeatureFlag
        flags = [
            FeatureFlag(key="groups_enabled", value="true"),
            FeatureFlag(key="group_schedules_enabled", value="true"),
            FeatureFlag(key="source_group_schedules_enabled", value="true"),
        ]
        db_session.add_all(flags)
        db_session.commit()

    async def test_get_all_feature_flags_default(self, service):
        """取得所有 flags，包含預設值（空資料庫）"""
        result = await service.get_all()
        assert "groups_enabled" in result
        assert "group_schedules_enabled" in result
        assert "source_group_schedules_enabled" in result
        assert result["groups_enabled"] is True

    async def test_get_all_feature_flags_with_data(self, service, seed_flags):
        """從資料庫讀取已存在的 flags"""
        result = await service.get_all()
        assert result["groups_enabled"] is True

    async def test_update_feature_flag(self, service, seed_flags):
        """更新單一 flag"""
        await service.update("groups_enabled", False)
        result = await service.get_all()
        assert result["groups_enabled"] is False

    async def test_update_feature_flags_batch(self, service, seed_flags):
        """批量更新 flags"""
        await service.update_batch({
            "groups_enabled": False,
            "group_schedules_enabled": False,
        })
        result = await service.get_all()
        assert result["groups_enabled"] is False
        assert result["group_schedules_enabled"] is False
        assert result["source_group_schedules_enabled"] is True

    async def test_upsert_new_flag(self, service):
        """不存在的 flag 自動建立"""
        await service.upsert("new_flag", True)
        result = await service.get_all()
        assert result["new_flag"] is True

    async def test_upsert_existing_flag(self, service, seed_flags):
        """已存在的 flag 更新"""
        await service.upsert("groups_enabled", False)
        result = await service.get_all()
        assert result["groups_enabled"] is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/services/test_feature_flag_service.py -v`
Expected: FAIL — ModuleNotFoundError

- [ ] **Step 3: Write minimal implementation**

Create: `src/services/feature_flag_service.py`

```python
"""Feature flag service for managing feature flags."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select, update

from src.models.feature_flag import FeatureFlag

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


DEFAULT_FLAGS = {
    "groups_enabled": True,
    "group_schedules_enabled": True,
    "source_group_schedules_enabled": True,
}


class FeatureFlagService:
    """Service for managing feature flags."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialize FeatureFlagService.

        Args:
            db: AsyncSession for database operations.
        """
        self._db = db

    async def get_all(self) -> dict[str, bool]:
        """Get all feature flags.

        Returns:
            Dictionary mapping flag keys to boolean values.
        """
        result = await self._db.execute(select(FeatureFlag))
        flags = {row.key: row.value for row in result.scalars().all()}
        
        # Merge with defaults for any missing flags
        merged = {}
        for key, default in DEFAULT_FLAGS.items():
            if key in flags:
                merged[key] = flags[key] == "true"
            else:
                merged[key] = default
        return merged

    async def update(self, key: str, value: bool) -> None:
        """Update a single feature flag.

        Args:
            key: Flag key.
            value: New boolean value.
        """
        from src.utils.time import now
        flag = await self._db.get(FeatureFlag, key)
        if flag:
            flag.value = "true" if value else "false"
            flag.updated_at = now()
        else:
            self._db.add(FeatureFlag(key=key, value="true" if value else "false"))
        await self._db.commit()

    async def update_batch(self, flags: dict[str, bool]) -> None:
        """Batch update feature flags.

        Args:
            flags: Dictionary of flag keys to boolean values.
        """
        from src.utils.time import now
        for key, value in flags.items():
            flag = await self._db.get(FeatureFlag, key)
            if flag:
                flag.value = "true" if value else "false"
                flag.updated_at = now()
            else:
                self._db.add(FeatureFlag(key=key, value="true" if value else "false"))
        await self._db.commit()

    async def upsert(self, key: str, value: bool) -> None:
        """Insert or update a feature flag.

        Args:
            key: Flag key.
            value: Boolean value.
        """
        await self.update(key, value)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/services/test_feature_flag_service.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/services/feature_flag_service.py tests/services/test_feature_flag_service.py
git commit -m "feat(ff): add FeatureFlagService"
```

---

### Task 3: 建立 Feature Flags API Routes

**Files:**
- Create: `src/api/routes/feature_flags.py`
- Create: `src/schemas/feature_flag.py`
- Modify: `src/api/__init__.py`（註冊路由）
- Test: `tests/api/test_feature_flags.py`

- [ ] **Step 1: 寫測試**

Create: `tests/api/test_feature_flags.py`

```python
"""Tests for feature flags API."""

import pytest
from httpx import ASGITransport, AsyncClient

from src.main import app


class TestFeatureFlagsAPI:
    """Test feature flags API endpoints."""

    @pytest.fixture
    async def client(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac

    @pytest.fixture
    def auth_headers(self):
        return {"X-API-Key": "test-api-key"}

    async def test_get_feature_flags(self, client, auth_headers):
        """GET /api/feature-flags returns all flags"""
        response = await client.get("/api/feature-flags", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "groups_enabled" in data
        assert "group_schedules_enabled" in data
        assert "source_group_schedules_enabled" in data
        assert isinstance(data["groups_enabled"], bool)

    async def test_put_feature_flags(self, client, auth_headers):
        """PUT /api/feature-flags updates flags"""
        response = await client.put(
            "/api/feature-flags",
            headers=auth_headers,
            json={"groups_enabled": False}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["groups_enabled"] is False

    async def test_put_feature_flags_batch(self, client, auth_headers):
        """PUT /api/feature-flags with multiple flags"""
        response = await client.put(
            "/api/feature-flags",
            headers=auth_headers,
            json={
                "groups_enabled": False,
                "group_schedules_enabled": False,
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["groups_enabled"] is False
        assert data["group_schedules_enabled"] is False

    async def test_get_feature_flags_requires_auth(self, client):
        """GET /api/feature-flags requires API key"""
        response = await client.get("/api/feature-flags")
        assert response.status_code == 401
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/api/test_feature_flags.py -v`
Expected: FAIL — cannot find `/api/feature-flags`

- [ ] **Step 3: Write minimal implementation**

Create: `src/api/routes/feature_flags.py`

```python
"""Feature flags API routes."""

from typing import Any

from fastapi import APIRouter, Depends

from src.api.deps import get_feature_flag_service, require_api_key
from src.schemas.feature_flag import FeatureFlagsResponse, FeatureFlagsUpdate
from src.services.feature_flag_service import FeatureFlagService

router = APIRouter(prefix="/feature-flags", tags=["feature-flags"])


@router.get("", response_model=FeatureFlagsResponse)
async def get_feature_flags(
    service: FeatureFlagService = Depends(get_feature_flag_service),
    _: str = Depends(require_api_key),
) -> FeatureFlagsResponse:
    """Get all feature flags.

    Returns:
        All feature flags with their boolean values.
    """
    flags = await service.get_all()
    return FeatureFlagsResponse(**flags)


@router.put("", response_model=FeatureFlagsResponse)
async def update_feature_flags(
    update: FeatureFlagsUpdate,
    service: FeatureFlagService = Depends(get_feature_flag_service),
    _: str = Depends(require_api_key),
) -> FeatureFlagsResponse:
    """Update one or more feature flags.

    Args:
        update: Feature flags to update.

    Returns:
        Updated feature flags.
    """
    if update.groups_enabled is not None:
        await service.update("groups_enabled", update.groups_enabled)
    if update.group_schedules_enabled is not None:
        await service.update("group_schedules_enabled", update.group_schedules_enabled)
    if update.source_group_schedules_enabled is not None:
        await service.update("source_group_schedules_enabled", update.source_group_schedules_enabled)

    flags = await service.get_all()
    return FeatureFlagsResponse(**flags)
```

Create: `src/schemas/feature_flag.py`

```python
"""Feature flag schemas."""

from typing import Optional

from pydantic import BaseModel


class FeatureFlagsResponse(BaseModel):
    """Response schema for feature flags."""

    groups_enabled: bool = True
    group_schedules_enabled: bool = True
    source_group_schedules_enabled: bool = True


class FeatureFlagsUpdate(BaseModel):
    """Request schema for updating feature flags."""

    groups_enabled: Optional[bool] = None
    group_schedules_enabled: Optional[bool] = None
    source_group_schedules_enabled: Optional[bool] = None
```

Modify: `src/api/__init__.py` — add feature_flags router registration

Modify: `src/api/deps.py` — add get_feature_flag_service dependency

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/api/test_feature_flags.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/api/routes/feature_flags.py src/schemas/feature_flag.py src/api/__init__.py src/api/deps.py tests/api/test_feature_flags.py
git commit -m "feat(ff): add feature flags API routes"
```

---

### Task 4: 建立 Alembic Migration

**Files:**
- Create: `alembic/versions/xxx_add_feature_flags.py`

- [ ] **Step 1: 確認目前 alembic head**

Run: `uv run alembic heads`
Expected: 顯示目前 head revision

- [ ] **Step 2: 建立 migration**

Run: `uv run alembic revision --autogenerate -m "add feature_flags table"`

- [ ] **Step 3: 檢查生成的 migration 檔案**

Read the generated file and verify it contains:
- `op.create_table('feature_flags')` with key, value, updated_at columns
- Insert default values for the 3 flags

- [ ] **Step 4: 執行 migration**

Run: `uv run alembic upgrade head`
Expected: SUCCESS

- [ ] **Step 5: Commit**

```bash
git add alembic/versions/xxx_add_feature_flags.py
git commit -m "feat(ff): add feature_flags table migration"
```

---

### Task 5: 修改 Backup Service 包含 Feature Flags

**Files:**
- Modify: `src/services/backup_service.py`
- Test: `tests/services/test_backup_service_with_feature_flags.py`

- [ ] **Step 1: 寫測試**

Create: `tests/services/test_backup_service_with_feature_flags.py`

```python
"""Tests for backup service with feature flags."""

import pytest
from zipfile import ZipFile
import json

from src.services.backup_service import BackupService
from src.services.feature_flag_service import FeatureFlagService


class TestBackupWithFeatureFlags:
    """Test backup export/import includes feature flags."""

    @pytest.fixture
    async def service(self, db_session):
        return BackupService(db_session)

    @pytest.fixture
    async def ff_service(self, db_session):
        return FeatureFlagService(db_session)

    @pytest.fixture
    async def seed_ff(self, ff_service):
        await ff_service.update("groups_enabled", False)
        await ff_service.update("group_schedules_enabled", False)

    async def test_export_includes_feature_flags(self, service, seed_ff):
        """Export backup 包含 feature_flags 欄位"""
        zip_data = await service.export_backup()
        
        with ZipFile(zip_data) as zf:
            content = zf.read("data.json").decode()
            data = json.loads(content)
            assert "feature_flags" in data
            assert data["feature_flags"]["groups_enabled"] is False
            assert data["feature_flags"]["group_schedules_enabled"] is False

    async def test_import_restores_feature_flags(self, service, ff_service, seed_ff):
        """Import backup 還原 feature_flags"""
        # Export first
        zip_data = await service.export_backup()
        
        # Clear flags
        await ff_service.update_batch({
            "groups_enabled": True,
            "group_schedules_enabled": True,
        })
        
        # Import
        result = await service.import_backup(zip_data)
        assert result.success
        
        # Verify restored
        flags = await ff_service.get_all()
        assert flags["groups_enabled"] is False
        assert flags["group_schedules_enabled"] is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/services/test_backup_service_with_feature_flags.py -v`
Expected: FAIL — feature_flags not in backup

- [ ] **Step 3: Implement export**

Find the `export_backup` method and add `feature_flags` to the data dict:

```python
# Get feature flags
ff_service = FeatureFlagService(self._db)
feature_flags = await ff_service.get_all()

backup_data = {
    "version": __version__,
    "exported_at": now().isoformat(),
    "sources": sources_data,
    "groups": groups_data,
    "feature_flags": {
        "groups_enabled": str(feature_flags["groups_enabled"]).lower(),
        "group_schedules_enabled": str(feature_flags["group_schedules_enabled"]).lower(),
        "source_group_schedules_enabled": str(feature_flags["source_group_schedules_enabled"]).lower(),
    },
}
```

- [ ] **Step 4: Implement import**

Find the `import_backup` method and add `feature_flags` handling:

```python
# Restore feature flags if present
if "feature_flags" in data:
    ff_service = FeatureFlagService(self._db)
    ff_data = data["feature_flags"]
    for key, value in ff_data.items():
        await ff_service.upsert(key, value == "true")
```

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/services/test_backup_service_with_feature_flags.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add src/services/backup_service.py tests/services/test_backup_service_with_feature_flags.py
git commit -m "feat(ff): integrate feature flags into backup export/import"
```

---

## Phase 2: 前端 Store & API Client

### Task 6: 建立 Feature Flags API Client

**Files:**
- Create: `web/src/api/feature-flags.ts`
- Modify: `web/src/api/client.ts`
- Test: `web/e2e/feature-flags-api.spec.ts`

- [ ] **Step 1: 寫 E2E 測試**

Create: `web/e2e/feature-flags-api.spec.ts`

```typescript
import { test, expect } from '@playwright/test'
import { createApiClient } from '@/api/client'

test.describe('Feature Flags API', () => {
  test('GET /api/feature-flags returns all flags', async ({ page }) => {
    const client = createApiClient(page)
    const flags = await client.getFeatureFlags()
    
    expect(flags).toHaveProperty('groups_enabled')
    expect(flags).toHaveProperty('group_schedules_enabled')
    expect(flags).toHaveProperty('source_group_schedules_enabled')
    expect(typeof flags.groups_enabled).toBe('boolean')
  })

  test('PUT /api/feature-flags updates flags', async ({ page }) => {
    const client = createApiClient(page)
    
    await client.updateFeatureFlags({ groups_enabled: false })
    
    const updated = await client.getFeatureFlags()
    expect(updated.groups_enabled).toBe(false)
  })

  test('PUT /api/feature-flags batch update', async ({ page }) => {
    const client = createApiClient(page)
    
    await client.updateFeatureFlags({
      groups_enabled: false,
      group_schedules_enabled: false,
    })
    
    const updated = await client.getFeatureFlags()
    expect(updated.groups_enabled).toBe(false)
    expect(updated.group_schedules_enabled).toBe(false)
  })
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pnpm test:e2e --grep "Feature Flags API"`
Expected: FAIL — cannot find '@/api/feature-flags'

- [ ] **Step 3: Write API client**

Create: `web/src/api/feature-flags.ts`

```typescript
import { apiClient } from './client'

export interface FeatureFlags {
  groups_enabled: boolean
  group_schedules_enabled: boolean
  source_group_schedules_enabled: boolean
}

export async function getFeatureFlags(): Promise<FeatureFlags> {
  const response = await apiClient.get<FeatureFlags>('/feature-flags')
  return response.data
}

export async function updateFeatureFlags(
  flags: Partial<FeatureFlags>
): Promise<FeatureFlags> {
  const response = await apiClient.put<FeatureFlags>('/feature-flags', flags)
  return response.data
}
```

Modify: `web/src/api/client.ts` — add `getFeatureFlags` and `updateFeatureFlags` methods

- [ ] **Step 4: Run test to verify it passes**

Run: `pnpm test:e2e --grep "Feature Flags API"`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add web/src/api/feature-flags.ts web/src/api/client.ts web/e2e/feature-flags-api.spec.ts
git commit -m "feat(ff): add feature flags API client and E2E tests"
```

---

### Task 7: 修改 FeatureFlagsStore 同步 API

**Files:**
- Modify: `web/src/stores/featureFlags.ts`
- Test: `web/src/stores/__tests__/featureFlags.test.ts`

- [ ] **Step 1: 寫測試**

Create: `web/src/stores/__tests__/featureFlags.test.ts`

```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useFeatureFlagsStore } from '../featureFlags'
import * as api from '@/api/feature-flags'

vi.mock('@/api/feature-flags')

describe('FeatureFlagsStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('loads flags from API on init', async () => {
    vi.mocked(api.getFeatureFlags).mockResolvedValue({
      groups_enabled: true,
      group_schedules_enabled: true,
      source_group_schedules_enabled: true,
    })

    const store = useFeatureFlagsStore()
    await store.init()

    expect(api.getFeatureFlags).toHaveBeenCalled()
  })

  it('syncs groupsEnabled change to API', async () => {
    vi.mocked(api.getFeatureFlags).mockResolvedValue({
      groups_enabled: true,
      group_schedules_enabled: true,
      source_group_schedules_enabled: true,
    })
    vi.mocked(api.updateFeatureFlags).mockResolvedValue({
      groups_enabled: false,
      group_schedules_enabled: false,
      source_group_schedules_enabled: true,
    })

    const store = useFeatureFlagsStore()
    await store.init()
    store.groupsEnabled = false

    expect(api.updateFeatureFlags).toHaveBeenCalledWith({ groups_enabled: false })
  })

  it('auto-disables schedules when groups disabled', async () => {
    vi.mocked(api.getFeatureFlags).mockResolvedValue({
      groups_enabled: true,
      group_schedules_enabled: true,
      source_group_schedules_enabled: true,
    })
    vi.mocked(api.updateFeatureFlags).mockResolvedValue({
      groups_enabled: false,
      group_schedules_enabled: false,
      source_group_schedules_enabled: false,
    })

    const store = useFeatureFlagsStore()
    await store.init()
    store.groupsEnabled = false

    expect(store.groupSchedulesEnabled).toBe(false)
    expect(api.updateFeatureFlags).toHaveBeenCalledWith(
      expect.objectContaining({ groups_enabled: false })
    )
  })
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pnpm test -- --grep "FeatureFlagsStore"`
Expected: FAIL — store.init doesn't exist

- [ ] **Step 3: Implement store with API sync**

Modify: `web/src/stores/featureFlags.ts`

```typescript
import { defineStore } from 'pinia'
import { ref, watch } from 'vue'
import { getFeatureFlags, updateFeatureFlags, type FeatureFlags } from '@/api/feature-flags'

export const useFeatureFlagsStore = defineStore('featureFlags', () => {
  const groupsEnabled = ref<boolean>(
    localStorage.getItem('ff_groups_enabled') !== 'false'
  )
  const groupSchedulesEnabled = ref<boolean>(
    localStorage.getItem('ff_group_schedules_enabled') !== 'false'
  )
  const sourceGroupSchedulesEnabled = ref<boolean>(
    localStorage.getItem('ff_source_group_schedules_enabled') !== 'false'
  )

  // Initialize from API (fallback to localStorage)
  async function init() {
    try {
      const flags = await getFeatureFlags()
      groupsEnabled.value = flags.groups_enabled
      groupSchedulesEnabled.value = flags.group_schedules_enabled
      sourceGroupSchedulesEnabled.value = flags.source_group_schedules_enabled
      
      // Sync to localStorage
      localStorage.setItem('ff_groups_enabled', String(groupsEnabled.value))
      localStorage.setItem('ff_group_schedules_enabled', String(groupSchedulesEnabled.value))
      localStorage.setItem('ff_source_group_schedules_enabled', String(sourceGroupSchedulesEnabled.value))
    } catch {
      // Use localStorage values on API failure
    }
  }

  // Sync changes to API and localStorage
  watch(groupsEnabled, async (val) => {
    localStorage.setItem('ff_groups_enabled', String(val))
    try {
      await updateFeatureFlags({ groups_enabled: val })
      if (!val) {
        groupSchedulesEnabled.value = false
        sourceGroupSchedulesEnabled.value = false
        localStorage.setItem('ff_group_schedules_enabled', 'false')
        localStorage.setItem('ff_source_group_schedules_enabled', 'false')
        await updateFeatureFlags({
          group_schedules_enabled: false,
          source_group_schedules_enabled: false,
        })
      }
    } catch {
      // localStorage already updated
    }
  })

  watch(groupSchedulesEnabled, async (val) => {
    localStorage.setItem('ff_group_schedules_enabled', String(val))
    try {
      await updateFeatureFlags({ group_schedules_enabled: val })
    } catch {
      // localStorage already updated
    }
  })

  watch(sourceGroupSchedulesEnabled, async (val) => {
    localStorage.setItem('ff_source_group_schedules_enabled', String(val))
    try {
      await updateFeatureFlags({ source_group_schedules_enabled: val })
    } catch {
      // localStorage already updated
    }
  })

  return {
    groupsEnabled,
    groupSchedulesEnabled,
    sourceGroupSchedulesEnabled,
    init,
  }
})
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pnpm test -- --grep "FeatureFlagsStore"`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add web/src/stores/featureFlags.ts web/src/stores/__tests__/featureFlags.test.ts
git commit -m "feat(ff): sync FeatureFlagsStore with API"
```

---

## Phase 3: UI 實作

### Task 8: 重新設計 FeatureFlagsDialog（DebugDialog 緊湊樣式）

**Files:**
- Modify: `web/src/components/FeatureFlagsDialog.vue`
- Test: `web/e2e/feature-flags-dialog.spec.ts`

- [ ] **Step 1: 寫 E2E 測試**

Create: `web/e2e/feature-flags-dialog.spec.ts`

```typescript
import { test, expect } from '@playwright/test'

test.describe('FeatureFlagsDialog UI', () => {
  async function openDialog(page: any) {
    await page.goto('/settings')
    await page.waitForLoadState('networkidle')
    
    // Click RSS icon 10 times
    const rssIcon = page.locator('header svg[class*="h-6"]').first()
    for (let i = 0; i < 10; i++) {
      await rssIcon.click()
      await page.waitForTimeout(50)
    }
    await expect(page.locator('[role="dialog"]')).toBeVisible()
  }

  test('dialog uses compact style (lg size)', async ({ page }) => {
    await openDialog(page)
    const dialog = page.locator('[role="dialog"]')
    
    // Verify has lg size class (max-w-xl)
    await expect(dialog.locator('.max-w-xl')).toBeVisible()
    
    // Verify no emoji (uses lucide icons)
    const content = await dialog.textContent()
    expect(content).not.toMatch(/[⚙️👥⏰]/)
  })

  test('dialog has three toggles', async ({ page }) => {
    await openDialog(page)
    
    // Find all toggle switches
    const toggles = page.locator('[role="switch"]')
    await expect(toggles).toHaveCount(3)
  })

  test('disabling groups shows cascade warning', async ({ page }) => {
    await openDialog(page)
    
    // Turn OFF groups (first toggle)
    await page.locator('[role="switch"]').first().click()
    
    // Warning should appear
    await expect(page.getByText(/Disabling groups will also disable/i)).toBeVisible()
    
    // Confirm button should work
    await page.getByRole('button', { name: 'Confirm' }).click()
    
    // Dialog should close
    await expect(page.locator('[role="dialog"]')).not.toBeVisible()
  })

  test('third toggle is disabled when groups disabled', async ({ page }) => {
    await openDialog(page)
    
    // Turn OFF groups
    await page.locator('[role="switch"]').first().click()
    await page.getByRole('button', { name: 'Confirm' }).click()
    
    // Reopen dialog
    await openDialog(page)
    
    // Third toggle should be disabled
    const thirdToggle = page.locator('[role="switch"]').nth(2)
    await expect(thirdToggle).toBeDisabled()
  })
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pnpm test:e2e --grep "FeatureFlagsDialog UI"`
Expected: FAIL — dialog still uses emoji and 2xl size

- [ ] **Step 3: Implement compact dialog**

Modify: `web/src/components/FeatureFlagsDialog.vue` — complete redesign per spec:
- `size="lg"` instead of `size="2xl"`
- Lucide icons (Settings, Users, Clock, CalendarClock, AlertTriangle, X)
- `p-3 bg-neutral-100 dark:bg-neutral-700 rounded-lg` cards
- Footer slot with Confirm/Cancel buttons
- Third toggle for source_group_schedules_enabled

- [ ] **Step 4: Run test to verify it passes**

Run: `pnpm test:e2e --grep "FeatureFlagsDialog UI"`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add web/src/components/FeatureFlagsDialog.vue web/e2e/feature-flags-dialog.spec.ts
git commit -m "feat(ff): redesign FeatureFlagsDialog to compact DebugDialog style"
```

---

### Task 9: 實作 UI 隱藏邏輯

**Files:**
- Modify: `web/src/pages/SourcesPage.vue`
- Modify: `web/src/pages/FeedPage.vue`
- Modify: `web/src/pages/HistoryPage.vue`
- Test: `web/e2e/feature-flags-ui-hiding.spec.ts`

- [ ] **Step 1: 寫 E2E 測試**

Create: `web/e2e/feature-flags-ui-hiding.spec.ts`

```typescript
import { test, expect } from '@playwright/test'

test.describe('Feature Flags UI Hiding', () => {
  async function openAndDisableGroups(page: any) {
    await page.goto('/settings')
    await page.waitForLoadState('networkidle')
    
    const rssIcon = page.locator('header svg[class*="h-6"]').first()
    for (let i = 0; i < 10; i++) {
      await rssIcon.click()
      await page.waitForTimeout(50)
    }
    
    await page.locator('[role="switch"]').first().click()
    await page.getByRole('button', { name: 'Confirm' }).click()
    await page.waitForLoadState('networkidle')
  }

  test('SourcesPage hides groups tab when disabled', async ({ page }) => {
    await openAndDisableGroups(page)
    await page.goto('/sources')
    await page.waitForLoadState('networkidle')
    
    // Groups tab should not be visible
    const groupsTab = page.locator('button', { hasText: /groups/i })
    await expect(groupsTab).not.toBeVisible()
  })

  test('FeedPage hides group filter chips when disabled', async ({ page }) => {
    await openAndDisableGroups(page)
    await page.goto('/feed')
    await page.waitForLoadState('networkidle')
    
    // Group filter chips should not be visible
    const groupChips = page.getByTestId('group-filter-chip')
    await expect(groupChips).toHaveCount(0)
  })

  test('HistoryPage hides group filter when disabled', async ({ page }) => {
    await openAndDisableGroups(page)
    await page.goto('/history')
    await page.waitForLoadState('networkidle')
    
    // Group filter should not be visible
    const groupFilter = page.getByTestId('group-filter')
    await expect(groupFilter).not.toBeVisible()
  })
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pnpm test:e2e --grep "Feature Flags UI Hiding"`
Expected: FAIL — elements still visible

- [ ] **Step 3: Add v-if conditions**

Modify each page to add `v-if="featureFlagsStore.groupsEnabled"` or similar conditions per spec.

- [ ] **Step 4: Run test to verify it passes**

Run: `pnpm test:e2e --grep "Feature Flags UI Hiding"`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add web/src/pages/SourcesPage.vue web/src/pages/FeedPage.vue web/src/pages/HistoryPage.vue web/e2e/feature-flags-ui-hiding.spec.ts
git commit -m "feat(ff): hide group-related UI based on feature flags"
```

---

### Task 10: 新增 i18n Keys

**Files:**
- Modify: `web/src/locales/en.json`
- Modify: `web/src/locales/zh.json`

- [ ] **Step 1: Add translations**

Add to `en.json` and `zh.json`:

```json
{
  "featureFlags": {
    "title": "Feature Flags",
    "groupsEnabled": "Groups Feature",
    "groupsEnabledDesc": "Enable/disable group functionality",
    "groupSchedulesEnabled": "Group Schedules",
    "groupSchedulesEnabledDesc": "Enable/disable scheduled updates for groups",
    "sourceGroupSchedulesEnabled": "Source Group Schedules",
    "sourceGroupSchedulesEnabledDesc": "Enable/disable scheduled updates for source groups",
    "confirm": "Confirm",
    "cancel": "Cancel",
    "cascadeWarningTitle": "Disabling groups will also disable schedules",
    "cascadeWarningConfirm": "Confirm",
    "cascadeWarningCancel": "Cancel"
  }
}
```

- [ ] **Step 2: Commit**

```bash
git add web/src/locales/en.json web/src/locales/zh.json
git commit -m "feat(ff): add feature flags i18n translations"
```

---

## Phase 4: 驗證

### Task 11: 執行完整測試

- [ ] **Step 1: Run all backend tests**

Run: `pytest tests/ -v`
Expected: ALL PASS

- [ ] **Step 2: Run all E2E tests**

Run: `pnpm test:e2e`
Expected: ALL PASS

- [ ] **Step 3: Manual verification**

- Open Settings, trigger dialog with 10 icon clicks
- Verify dialog uses lucide icons (no emoji)
- Toggle groups OFF, verify cascade warning
- Navigate to Sources/Feed/History, verify UI hidden
- Export backup, verify feature_flags in zip
- Import backup, verify feature_flags restored

---

## 受影響檔案清單

### 後端（新建）
- `src/models/feature_flag.py`
- `src/services/feature_flag_service.py`
- `src/api/routes/feature_flags.py`
- `src/schemas/feature_flag.py`
- `alembic/versions/xxx_add_feature_flags.py`

### 後端（修改）
- `src/models/__init__.py`
- `src/api/__init__.py`
- `src/api/deps.py`
- `src/services/backup_service.py`

### 前端（新建）
- `web/src/api/feature-flags.ts`
- `web/e2e/feature-flags-api.spec.ts`
- `web/e2e/feature-flags-dialog.spec.ts`
- `web/e2e/feature-flags-ui-hiding.spec.ts`

### 前端（修改）
- `web/src/stores/featureFlags.ts`
- `web/src/components/FeatureFlagsDialog.vue`
- `web/src/pages/SourcesPage.vue`
- `web/src/pages/FeedPage.vue`
- `web/src/pages/HistoryPage.vue`
- `web/src/locales/en.json`
- `web/src/locales/zh.json`

### 測試
- `tests/models/test_feature_flag.py`
- `tests/services/test_feature_flag_service.py`
- `tests/api/test_feature_flags.py`
- `tests/services/test_backup_service_with_feature_flags.py`
- `web/src/stores/__tests__/featureFlags.test.ts`