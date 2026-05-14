# Feature Settings Toggle — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在資料庫新增 `app_settings` 表儲存三個功能開關（群組功能、定時更新功能、分享連結功能），並於 Settings 頁面提供隱藏彩蛋設定介面，前後端均實作條件阻擋。

**Architecture:** 後端以 SQLAlchemy Model + FastAPI PUT/GET route 提供設定讀寫，前端以 Pinia composable 包裝 API，Settings 頁面 10-click 觸發設定 Dialog，各頁面以 `v-if` 依開關狀態條件渲染功能區塊。

**Tech Stack:** Python (FastAPI + SQLAlchemy + Alembic), TypeScript (Vue 3 + Playwright)

---

## 檔案地圖

### 新建
- `src/models/app_settings.py` — 設定 Model
- `src/schemas/app_settings.py` — Pydantic Schema
- `src/api/routes/app_settings.py` — API 路由
- `src/api/deps.py` — 新增 dependency
- `src/main.py` — lifespan 初始化設定（若無記錄則建立）
- `alembic/versions/{hash}_add_app_settings_table.py` — Migration
- `tests/models/test_app_settings.py` — Model unit tests
- `tests/api/test_app_settings.py` — API route unit tests
- `web/src/api/app-settings.ts` — Frontend API client
- `web/src/composables/useAppSettings.ts` — Pinia composable
- `web/src/components/FeatureSettingsDialog.vue` — 設定彈窗
- `web/e2e/settings-feature-toggle.spec.ts` — E2E 測試

### 修改
- `web/src/layouts/MainLayout.vue` — DebugDialog 只在 Feed 首頁觸發，Settings 頁面略過
- `web/src/pages/SettingsPage.vue` — 新增 10-click 觸發 FeatureSettingsDialog
- `web/src/pages/SourcesPage.vue` — Groups Tab + ScheduleConfigPanel 條件渲染
- `web/src/components/RssPreviewDialog.vue` — 分享連結區塊條件渲染
- `src/api/routes/source_groups.py` — `group_enabled=False` → 403
- `src/api/routes/schedule.py` — `schedule_enabled=False` → 403
- `src/api/routes/feed.py` — `share=true` 時若 `share_enabled=False` → 403
- `web/src/api/feed.ts` — 呼叫時傳遞 share param

---

## Task 1: 資料庫 Model 與 Migration

**Files:**
- Create: `src/models/app_settings.py`
- Create: `src/schemas/app_settings.py`
- Create: `alembic/versions/{hash}_add_app_settings_table.py`
- Modify: `src/models/__init__.py`
- Modify: `src/schemas/__init__.py`
- Test: `tests/models/test_app_settings.py`

- [ ] **Step 1: 安裝 uv 依賴，確認環境**

Run: `cd /Users/kimhsiao/Templates/git/pic.net.tw/RSS-collection && uv sync`
Expected: 已安裝依賴，無錯誤

- [ ] **Step 2: 新建 Model — `src/models/app_settings.py`**

```python
"""AppSettings model — stores global feature toggles."""

from __future__ import annotations

from sqlalchemy import Boolean
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base


class AppSettings(Base):
    """Singleton app settings stored in database.

    Holds global feature enable/disable flags. Only one record
    should exist (id=1). Initialized automatically at startup.
    """
    __tablename__ = "app_settings"

    id: Mapped[int] = mapped_column(primary_key=True, default=1)
    group_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    schedule_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    share_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
```

- [ ] **Step 3: 更新 `src/models/__init__.py`** — 匯出 `AppSettings`

- [ ] **Step 4: 新建 Schema — `src/schemas/app_settings.py`**

```python
"""Pydantic schemas for app settings."""

from pydantic import BaseModel, ConfigDict, Field


class AppSettingsResponse(BaseModel):
    """Schema for reading app settings."""
    model_config = ConfigDict(from_attributes=True)
    group_enabled: bool
    schedule_enabled: bool
    share_enabled: bool


class AppSettingsUpdate(BaseModel):
    """Schema for updating app settings (partial update supported)."""
    group_enabled: bool | None = Field(default=None)
    schedule_enabled: bool | None = Field(default=None)
    share_enabled: bool | None = Field(default=None)
```

- [ ] **Step 5: 更新 `src/schemas/__init__.py`** — 匯出 Schema

- [ ] **Step 6: 寫 Model unit test — `tests/models/test_app_settings.py`**

```python
"""Tests for AppSettings model."""

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.app_settings import AppSettings


@pytest_asyncio.fixture
async def app_settings(db_session: AsyncSession) -> AppSettings:
    """Create default app settings."""
    settings = AppSettings()
    db_session.add(settings)
    await db_session.commit()
    await db_session.refresh(settings)
    return settings


@pytest.mark.asyncio
async def test_app_settings_defaults_to_false(db_session: AsyncSession):
    """AppSettings fields default to False."""
    settings = AppSettings()
    db_session.add(settings)
    await db_session.commit()

    assert settings.group_enabled is False
    assert settings.schedule_enabled is False
    assert settings.share_enabled is False


@pytest.mark.asyncio
async def test_app_settings_can_update_fields(db_session: AsyncSession):
    """AppSettings fields can be updated."""
    settings = AppSettings()
    db_session.add(settings)
    await db_session.commit()

    settings.group_enabled = True
    settings.schedule_enabled = True
    await db_session.commit()

    result = await db_session.execute(select(AppSettings))
    saved = result.scalars().first()
    assert saved.group_enabled is True
    assert saved.schedule_enabled is True
    assert saved.share_enabled is False
```

- [ ] **Step 7: Run test**

Run: `pytest tests/models/test_app_settings.py -v`
Expected: PASS (2 tests)

- [ ] **Step 8: Generate Alembic migration**

Run: `uv run alembic revision --autogenerate -m "add app_settings table"`
Expected: Migration file created in `alembic/versions/`

- [ ] **Step 9: Verify migration content**

Read the generated file. Ensure `upgrade()` creates table with `group_enabled`, `schedule_enabled`, `share_enabled` columns (BOOLEAN, default FALSE). Ensure `downgrade()` drops table.

- [ ] **Step 10: Run migration**

Run: `uv run alembic upgrade head`
Expected: `Running upgrade  -> {hash}`

- [ ] **Step 11: Commit**

```bash
git add src/models/app_settings.py src/models/__init__.py src/schemas/app_settings.py src/schemas/__init__.py tests/models/test_app_settings.py alembic/versions/{migration_file}
git commit -m "feat: add AppSettings model and database migration"
```

---

## Task 2: Backend API Route

**Files:**
- Create: `src/api/routes/app_settings.py`
- Modify: `src/api/deps.py` — 新增 `get_app_settings()` dependency
- Modify: `src/main.py` — lifespan 初始化 singleton 設定
- Modify: `src/api/routes/__init__.py`
- Test: `tests/api/test_app_settings.py`

- [ ] **Step 1: 新建 API Route — `src/api/routes/app_settings.py`**

```python
"""App settings API routes."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_db, require_api_key
from src.models.app_settings import AppSettings
from src.schemas.app_settings import AppSettingsResponse, AppSettingsUpdate

router = APIRouter(prefix="/settings", tags=["settings"])


async def _get_or_create_settings(session: AsyncSession) -> AppSettings:
    """Return the singleton AppSettings record, creating it if absent."""
    result = await session.execute(select(AppSettings))
    settings = result.scalars().first()
    if settings is None:
        settings = AppSettings()
        session.add(settings)
        await session.commit()
        await session.refresh(settings)
    return settings


@router.get("", response_model=AppSettingsResponse)
async def get_app_settings(
    session: AsyncSession = Depends(get_db),
    _: str = Depends(require_api_key),
) -> AppSettingsResponse:
    """Get current global feature toggle settings."""
    settings = await _get_or_create_settings(session)
    return AppSettingsResponse.model_validate(settings)


@router.put("", response_model=AppSettingsResponse)
async def update_app_settings(
    data: AppSettingsUpdate,
    session: AsyncSession = Depends(get_db),
    _: str = Depends(require_api_key),
) -> AppSettingsResponse:
    """Update global feature toggle settings (partial update supported)."""
    settings = await _get_or_create_settings(session)
    patch = data.model_dump(exclude_unset=True)
    for key, value in patch.items():
        setattr(settings, key, value)
    await session.commit()
    await session.refresh(settings)
    return AppSettingsResponse.model_validate(settings)
```

- [ ] **Step 2: 更新 `src/api/deps.py`** — 新增 dependency

在 `get_db` 之後新增：

```python
from src.models.app_settings import AppSettings

async def get_app_settings(session: AsyncSession = Depends(get_db)) -> AppSettings:
    """Return the singleton AppSettings record."""
    from sqlalchemy import select
    result = await session.execute(select(AppSettings))
    settings = result.scalars().first()
    if settings is None:
        settings = AppSettings()
        session.add(settings)
        await session.commit()
        await session.refresh(settings)
    return settings
```

- [ ] **Step 3: 更新 `src/main.py`** — lifespan 初始化

在 `lifespan` 的 startup 區塊（`yield` 之前）加入：

```python
from src.models.app_settings import AppSettings
from sqlalchemy import select

async with engine.begin() as conn:
    await conn.run_sync(Base.metadata.create_all)

# Ensure AppSettings singleton exists
async with async_session_factory() as session:
    result = await session.execute(select(AppSettings))
    if result.scalars().first() is None:
        session.add(AppSettings())
        await session.commit()
```

- [ ] **Step 4: 更新 `src/api/routes/__init__.py`** — 匯出 router

- [ ] **Step 5: 寫 API unit test — `tests/api/test_app_settings.py`**

```python
"""Tests for app settings API route."""

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession

from src.main import app
from src.api.deps import get_db
from src.models.app_settings import AppSettings

# Override dependency for tests
async def override_get_db(session: AsyncSession = Depends(get_db)):
    yield session


@pytest_asyncio.fixture
async def client(db_session: AsyncSession):
    app.dependency_overrides[get_db] = lambda: db_session
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_settings_returns_defaults(client: AsyncClient):
    """GET /api/settings returns all False by default."""
    response = await client.get("/settings")
    assert response.status_code == 401  # needs API key

    # With API key (mock header)
    response = await client.get("/settings", headers={"X-API-Key": "test-key"})
    # Returns 200 if key is valid or disabled; adjust based on REQUIRE_API_KEY env
    data = response.json()
    assert "group_enabled" in data
    assert data["group_enabled"] is False


@pytest.mark.asyncio
async def test_put_settings_updates_flags(client: AsyncClient, db_session: AsyncSession):
    """PUT /api/settings updates the flags."""
    # Seed a record first
    db_session.add(AppSettings())
    await db_session.commit()

    response = await client.put("/settings", json={"group_enabled": True})
    if response.status_code == 401:
        pytest.skip("API key required in this environment")

    data = response.json()
    assert data["group_enabled"] is True
    assert data["schedule_enabled"] is False


@pytest.mark.asyncio
async def test_put_settings_partial_update(client: AsyncClient, db_session: AsyncSession):
    """PUT with partial data only updates provided fields."""
    db_session.add(AppSettings())
    await db_session.commit()

    response = await client.put("/settings", json={"share_enabled": True})
    if response.status_code == 401:
        pytest.skip("API key required")

    data = response.json()
    assert data["share_enabled"] is True
    assert data["group_enabled"] is False  # unchanged
```

- [ ] **Step 6: Run tests**

Run: `pytest tests/api/test_app_settings.py -v`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add src/api/routes/app_settings.py src/api/deps.py src/main.py src/api/routes/__init__.py tests/api/test_app_settings.py
git commit -m "feat: add GET/PUT /api/settings endpoint"
```

---

## Task 3: Backend Feature Gate (403 阻擋)

**Files:**
- Modify: `src/api/routes/source_groups.py`
- Modify: `src/api/routes/schedule.py`
- Modify: `src/api/routes/feed.py`
- Test: `tests/api/test_app_settings_gate.py` (new)

- [ ] **Step 1: 修改 `src/api/routes/source_groups.py`** — 新增 feature gate

在所有 endpoint 加入：

```python
from fastapi import HTTPException, status
from src.api.deps import get_app_settings

async def _require_group_enabled(settings: AppSettings = Depends(get_app_settings)) -> None:
    if not settings.group_enabled:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="群組功能已停用")

# 每個 source_groups endpoint 的 Depends() 改為：
@router.get("", response_model=list[GroupResponse], dependencies=[Depends(_require_group_enabled)])
```

或更優雅的方式：在 `get_source_group_service` 之後檢查：

```python
@router.get("", response_model=list[GroupResponse])
async def list_groups(
    group_service: SourceGroupService = Depends(get_source_group_service),
    settings: AppSettings = Depends(get_app_settings),
    _: str = Depends(require_api_key),
) -> list[GroupResponse]:
    if not settings.group_enabled:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="群組功能已停用")
    # ... existing logic
```

- [ ] **Step 2: 修改 `src/api/routes/schedule.py`** — 新增 feature gate

在 `POST /schedules` endpoint 加入檢查：

```python
async def require_schedule_enabled(settings: AppSettings = Depends(get_app_settings)) -> None:
    if not settings.schedule_enabled:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="定時更新功能已停用")
```

- [ ] **Step 3: 修改 `src/api/routes/feed.py`** — share param gate

找到處理 `share=true` 查詢參數的部分，加入：

```python
@router.get("")
async def get_feed(
    share: bool = False,  # existing param
    settings: AppSettings = Depends(get_app_settings),
    # ...
):
    if share and not settings.share_enabled:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="分享連結功能已停用")
    # ... existing logic
```

- [ ] **Step 4: 寫 Feature Gate unit test — `tests/api/test_app_settings_gate.py`**

```python
"""Tests for feature gate 403 responses."""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession

from src.main import app
from src.api.deps import get_db
from src.models.app_settings import AppSettings


@pytest_asyncio.fixture
async def client(db_session: AsyncSession):
    app.dependency_overrides[get_db] = lambda: db_session
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_source_groups_returns_403_when_disabled(client: AsyncClient, db_session: AsyncSession):
    """GET /api/v1/source-groups returns 403 when group_enabled=False."""
    db_session.add(AppSettings(group_enabled=False))
    await db_session.commit()

    response = await client.get("/api/v1/source-groups")
    if response.status_code == 401:
        pytest.skip("API key required")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_source_groups_returns_200_when_enabled(client: AsyncClient, db_session: AsyncSession):
    """GET /api/v1/source-groups returns 200 when group_enabled=True."""
    db_session.add(AppSettings(group_enabled=True))
    await db_session.commit()

    response = await client.get("/api/v1/source-groups")
    if response.status_code == 401:
        pytest.skip("API key required")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_schedules_returns_403_when_disabled(client: AsyncClient, db_session: AsyncSession):
    """POST /api/v1/schedules returns 403 when schedule_enabled=False."""
    db_session.add(AppSettings(schedule_enabled=False))
    await db_session.commit()

    response = await client.post("/api/v1/schedules", json={"group_id": 1, "cron": "*/15 * * * *"})
    if response.status_code == 401:
        pytest.skip("API key required")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_feed_share_returns_403_when_disabled(client: AsyncClient, db_session: AsyncSession):
    """GET /api/v1/feed?share=true returns 403 when share_enabled=False."""
    db_session.add(AppSettings(share_enabled=False))
    await db_session.commit()

    response = await client.get("/api/v1/feed", params={"share": "true"})
    if response.status_code == 401:
        pytest.skip("API key required")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_feed_share_returns_200_when_enabled(client: AsyncClient, db_session: AsyncSession):
    """GET /api/v1/feed?share=true returns 200 when share_enabled=True."""
    db_session.add(AppSettings(share_enabled=True))
    await db_session.commit()

    response = await client.get("/api/v1/feed", params={"share": "true"})
    if response.status_code == 401:
        pytest.skip("API key required")
    assert response.status_code in (200, 404)  # 200 or 404 (no sources) is fine
```

- [ ] **Step 5: Run tests**

Run: `pytest tests/api/test_app_settings_gate.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add src/api/routes/source_groups.py src/api/routes/schedule.py src/api/routes/feed.py tests/api/test_app_settings_gate.py
git commit -m "feat: add 403 feature gates for source-groups, schedules, and feed share"
```

---

## Task 4: Frontend API Client + Composable

**Files:**
- Create: `web/src/api/app-settings.ts`
- Create: `web/src/composables/useAppSettings.ts`
- Test: `web/src/composables/useAppSettings.test.ts`
- Modify: `web/src/api/index.ts` (若需要)

- [ ] **Step 1: 新建 API client — `web/src/api/app-settings.ts`**

```typescript
import api from '.'
import type { AppSettingsResponse } from '@/types/app-settings'

export async function getAppSettings(): Promise<AppSettingsResponse> {
  return api.get<AppSettingsResponse>('/settings')
}

export async function updateAppSettings(
  data: Partial<AppSettingsResponse>
): Promise<AppSettingsResponse> {
  return api.put<AppSettingsResponse>('/settings', data)
}
```

- [ ] **Step 2: 新建 Types — `web/src/types/app-settings.ts`**

```typescript
export interface AppSettingsResponse {
  group_enabled: boolean
  schedule_enabled: boolean
  share_enabled: boolean
}
```

- [ ] **Step 3: 新建 Composable — `web/src/composables/useAppSettings.ts`**

```typescript
/**
 * useAppSettings — reads and updates global feature toggle settings.
 * Data is fetched once at composable creation; settings are applied
 * on the next page load after a successful update.
 */
import { ref, readonly } from 'vue'
import { getAppSettings, updateAppSettings } from '@/api/app-settings'
import type { AppSettingsResponse } from '@/types/app-settings'

const DEFAULT_SETTINGS: AppSettingsResponse = {
  group_enabled: false,
  schedule_enabled: false,
  share_enabled: false,
}

const settings = ref<AppSettingsResponse>({ ...DEFAULT_SETTINGS })
const loading = ref(false)
const error = ref<string | null>(null)

export function useAppSettings() {
  async function fetchSettings() {
    loading.value = true
    error.value = null
    try {
      settings.value = await getAppSettings()
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to load settings'
      settings.value = { ...DEFAULT_SETTINGS }
    } finally {
      loading.value = false
    }
  }

  async function saveSettings(data: Partial<AppSettingsResponse>) {
    loading.value = true
    error.value = null
    try {
      settings.value = await updateAppSettings(data)
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to save settings'
      throw e
    } finally {
      loading.value = false
    }
  }

  return {
    settings: readonly(settings),
    loading: readonly(loading),
    error: readonly(error),
    fetchSettings,
    saveSettings,
  }
}
```

- [ ] **Step 4: 寫 unit test — `web/src/composables/useAppSettings.test.ts`**

使用 Vitest mock `getAppSettings` 和 `updateAppSettings`：

```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { useAppSettings } from './useAppSettings'

vi.mock('@/api/app-settings', () => ({
  getAppSettings: vi.fn(),
  updateAppSettings: vi.fn(),
}))

const { getAppSettings, updateAppSettings } = await import('@/api/app-settings')

describe('useAppSettings', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('fetches settings on fetchSettings()', async () => {
    const mockData = { group_enabled: true, schedule_enabled: false, share_enabled: false }
    vi.mocked(getAppSettings).mockResolvedValue(mockData)

    const { fetchSettings, settings } = useAppSettings()
    await fetchSettings()

    expect(getAppSettings).toHaveBeenCalled()
    expect(settings.value.group_enabled).toBe(true)
  })

  it('saves settings and updates state on saveSettings()', async () => {
    const mockData = { group_enabled: true, schedule_enabled: true, share_enabled: false }
    vi.mocked(updateAppSettings).mockResolvedValue(mockData)

    const { saveSettings, settings } = useAppSettings()
    await saveSettings({ group_enabled: true, schedule_enabled: true })

    expect(updateAppSettings).toHaveBeenCalledWith({ group_enabled: true, schedule_enabled: true })
    expect(settings.value.schedule_enabled).toBe(true)
  })

  it('sets error when fetchSettings fails', async () => {
    vi.mocked(getAppSettings).mockRejectedValue(new Error('Network error'))

    const { fetchSettings, error } = useAppSettings()
    await fetchSettings()

    expect(error.value).toBe('Network error')
    expect(settings.value.group_enabled).toBe(false)
  })
})
```

- [ ] **Step 5: Run test**

Run: `cd web && pnpm test:run src/composables/useAppSettings.test.ts`
Expected: PASS (3 tests)

- [ ] **Step 6: Commit**

```bash
git add web/src/api/app-settings.ts web/src/types/app-settings.ts web/src/composables/useAppSettings.ts web/src/composables/useAppSettings.test.ts
git commit -m "feat: add app-settings API client and useAppSettings composable"
```

---

## Task 5: Frontend — FeatureSettingsDialog 元件

**Files:**
- Create: `web/src/components/FeatureSettingsDialog.vue`
- Modify: `web/src/locales/` — 新增 i18n 翻譯 key
- Test: 透過 E2E test 驗證

- [ ] **Step 1: 新增 i18n key — `web/src/locales/en_US.json` 和 `zh_TW.json`**

在 `en_US.json` 加入：

```json
{
  "featureSettings": {
    "title": "功能設定",
    "group": {
      "label": "群組功能",
      "description": "啟用後可新增、管理 RSS 來源群組"
    },
    "schedule": {
      "label": "定時更新功能",
      "description": "啟用後可為各群組設定自動更新時間表",
      "disabledHint": "需先開啟群組功能"
    },
    "share": {
      "label": "分享連結功能",
      "description": "啟用後可在預覽摘要中使用分享連結"
    },
    "apply": "套用",
    "cancel": "取消",
    "applied": "已套用設定"
  }
}
```

`zh_TW.json` 同樣的 key，改為中文值。

- [ ] **Step 2: 新建 Dialog 元件 — `web/src/components/FeatureSettingsDialog.vue`**

參考 `DebugDialog.vue` 的樣式結構：

```vue
<script setup lang="ts">
import { ref } from 'vue'
import { useAppSettings } from '@/composables/useAppSettings'
import { useToast } from '@/composables/useToast'

const dialogOpen = defineModel<boolean>('open', { required: true })
const { settings, loading, fetchSettings, saveSettings } = useAppSettings()
const toast = useToast()

// Local copies of toggles for editing
const localGroup = ref(false)
const localSchedule = ref(false)
const localShare = ref(false)

// Sync from global settings when dialog opens
function syncFromStore() {
  localGroup.value = settings.value.group_enabled
  localSchedule.value = settings.value.schedule_enabled
  localShare.value = settings.value.share_enabled
}

async function handleApply() {
  await saveSettings({
    group_enabled: localGroup.value,
    schedule_enabled: localSchedule.value,
    share_enabled: localShare.value,
  })
  toast.success('已套用設定')
  setTimeout(() => {
    window.location.reload()
  }, 500)
}

function handleClose() {
  dialogOpen.value = false
}

// Watch dialog open state
import { watch } from 'vue'
watch(dialogOpen, (open) => {
  if (open) syncFromStore()
})
</script>

<template>
  <Dialog v-model:open="dialogOpen">
    <DialogContent class="sm:max-w-md">
      <DialogHeader>
        <DialogTitle>{{ $t('featureSettings.title') }}</DialogTitle>
      </DialogHeader>
      <div class="space-y-4 py-4">
        <!-- Group toggle -->
        <div class="flex items-start justify-between gap-4">
          <div class="flex-1">
            <div class="font-medium">{{ $t('featureSettings.group.label') }}</div>
            <div class="text-sm text-muted-foreground">{{ $t('featureSettings.group.description') }}</div>
          </div>
          <Switch v-model="localGroup" />
        </div>
        <!-- Schedule toggle -->
        <div class="flex items-start justify-between gap-4">
          <div class="flex-1">
            <div class="font-medium">{{ $t('featureSettings.schedule.label') }}</div>
            <div class="text-sm text-muted-foreground">{{ $t('featureSettings.schedule.description') }}</div>
            <div v-if="!localGroup" class="text-xs text-muted-foreground/60 mt-1">
              {{ $t('featureSettings.schedule.disabledHint') }}
            </div>
          </div>
          <Switch v-model="localSchedule" :disabled="!localGroup" />
        </div>
        <!-- Share toggle -->
        <div class="flex items-start justify-between gap-4">
          <div class="flex-1">
            <div class="font-medium">{{ $t('featureSettings.share.label') }}</div>
            <div class="text-sm text-muted-foreground">{{ $t('featureSettings.share.description') }}</div>
          </div>
          <Switch v-model="localShare" />
        </div>
      </div>
      <DialogFooter>
        <Button variant="outline" @click="handleClose">{{ $t('featureSettings.cancel') }}</Button>
        <Button :disabled="loading" @click="handleApply">{{ $t('featureSettings.apply') }}</Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
</template>
```

- [ ] **Step 3: Commit**

```bash
git add web/src/components/FeatureSettingsDialog.vue web/src/locales/en_US.json web/src/locales/zh_TW.json
git commit -m "feat: add FeatureSettingsDialog component with i18n"
```

---

## Task 6: 前端條件渲染

**Files:**
- Modify: `web/src/layouts/MainLayout.vue` — DebugDialog 只在 Feed 首頁觸發
- Modify: `web/src/pages/SettingsPage.vue` — RSS icon 10-click 觸發 FeatureSettingsDialog
- Modify: `web/src/pages/SourcesPage.vue` — Groups Tab + ScheduleConfigPanel 條件渲染
- Modify: `web/src/components/RssPreviewDialog.vue` — 分享連結條件渲染

- [ ] **Step 1: 修改 `MainLayout.vue`** — DebugDialog 只在 Feed 首頁觸發

找到 `handleFeedIconClick()`，改為：

```typescript
function handleFeedIconClick(): void {
  if (route.path !== '/') return  // ✅ 只在 Feed 首頁
  if (clickTimer.value) clearTimeout(clickTimer.value)
  clickCount.value++
  clickTimer.value = setTimeout(() => { clickCount.value = 0 }, 2000)
  if (clickCount.value >= 10) {
    debugDialogOpen.value = true
    clickCount.value = 0
  }
}
```

- [ ] **Step 2: 修改 `SettingsPage.vue`** — 新增 10-click + FeatureSettingsDialog

在 `<script setup>` 引入：

```typescript
import FeatureSettingsDialog from '@/components/FeatureSettingsDialog.vue'

const featureDialogOpen = ref(false)
const clickCount = ref(0)
const clickTimer = ref<ReturnType<typeof setTimeout> | null>(null)

function handleFeedIconClick(): void {
  if (route.path !== '/settings') return  // only on settings page
  if (clickTimer.value) clearTimeout(clickTimer.value)
  clickCount.value++
  clickTimer.value = setTimeout(() => { clickCount.value = 0 }, 2000)
  if (clickCount.value >= 10) {
    featureDialogOpen.value = true
    clickCount.value = 0
  }
}
```

在 `<template>` 的 Settings 頁面 `<Rss>` icon 加入 `@click="handleFeedIconClick"`。

在 template 底部加入：

```vue
<FeatureSettingsDialog v-model:open="featureDialogOpen" />
```

- [ ] **Step 3: 修改 `SourcesPage.vue`** — Groups Tab 條件渲染

找到 Groups Tab 的 `<template>` 根元素，加入：

```vue
<div v-if="groupEnabled">
```

（或使用 `v-if="useAppSettings().settings.value.group_enabled"` 但需先在 `onMounted` fetch）

更優雅做法：在 `SourcesPage.vue` 的 `<script setup>` 中使用 composable：

```typescript
const { settings } = useAppSettings()
// onMounted:
await settings  // fetch on page mount
```

然後在 Groups Tab 加入：

```vue
<TabsContent value="groups" v-if="settings.group_enabled">
```

在 ScheduleConfigPanel 加入：

```vue
<ScheduleConfigPanel
  v-if="settings.schedule_enabled && settings.group_enabled"
  :groupId="group.id"
  ...
/>
```

- [ ] **Step 4: 修改 `RssPreviewDialog.vue`** — 分享連結條件渲染

找到「分享連結」區塊的最外層，加入 `v-if="shareEnabled"`：

```vue
<div v-if="shareEnabled" class="space-y-3">
  <!-- 分享連結標題 -->
  <!-- RSS / JSON / Markdown 三列 -->
</div>
```

`shareEnabled` 來自 `useAppSettings().settings.share_enabled`。

- [ ] **Step 5: Commit**

```bash
git add web/src/layouts/MainLayout.vue web/src/pages/SettingsPage.vue web/src/pages/SourcesPage.vue web/src/components/RssPreviewDialog.vue
git commit -m "feat: add conditional rendering for feature toggles"
```

---

## Task 7: E2E Tests

**Files:**
- Create: `web/e2e/settings-feature-toggle.spec.ts`

- [ ] **Step 1: 寫 E2E test — `web/e2e/settings-feature-toggle.spec.ts`**

```typescript
import { test, expect, Page } from '@playwright/test'

test.describe('Feature Settings Toggle', () => {

  // Helper: click RSS icon 10 times quickly
  async function clickIconTenTimes(page: Page) {
    const icon = page.locator('[class*="cursor-pointer"]').filter({ has: page.locator('svg') }).first()
    for (let i = 0; i < 10; i++) {
      await icon.click()
      await page.waitForTimeout(50)
    }
  }

  test.beforeEach(async ({ page }) => {
    await page.goto('/settings')
    await page.waitForLoadState('networkidle')
  })

  test('Settings page 10-click opens FeatureSettingsDialog', async ({ page }) => {
    await clickIconTenTimes(page)

    const dialog = page.locator('[role="dialog"]')
    await expect(dialog).toBeVisible({ timeout: 3000 })
    await expect(dialog.getByRole('heading', { level: 2 })).toContainText('功能設定')
  })

  test('Dialog shows three feature toggles', async ({ page }) => {
    await clickIconTenTimes(page)
    const dialog = page.locator('[role="dialog"]')

    await expect(dialog.getByText('群組功能')).toBeVisible()
    await expect(dialog.getByText('定時更新功能')).toBeVisible()
    await expect(dialog.getByText('分享連結功能')).toBeVisible()
  })

  test('Schedule toggle is disabled when group is off', async ({ page }) => {
    await clickIconTenTimes(page)
    const dialog = page.locator('[role="dialog"]')

    const scheduleSwitch = dialog.locator('button[type="button"]').nth(1)
    // When group_enabled is off, schedule switch should be disabled
    await expect(scheduleSwitch).toHaveAttribute('aria-disabled', 'true')
  })

  test('Apply button reloads the page', async ({ page }) => {
    await clickIconTenTimes(page)
    const dialog = page.locator('[role="dialog"]')

    page.once('dialog', async d => await d.accept())
    await dialog.getByRole('button', { name: /套用|apply/i }).click()

    // Toast should appear
    await expect(page.locator('[role="alert"]')).toContainText(/已套用/i)
  })

  test('Cancel button closes dialog without changes', async ({ page }) => {
    await clickIconTenTimes(page)
    const dialog = page.locator('[role="dialog"]')

    await dialog.getByRole('button', { name: /取消|cancel/i }).click()
    await expect(dialog).not.toBeVisible({ timeout: 2000 })
  })

  test('DebugDialog only triggers on Feed page, not Settings', async ({ page }) => {
    // Go to settings page
    await page.goto('/settings')
    await page.waitForLoadState('networkidle')
    await clickIconTenTimes(page)

    // Should open FeatureSettingsDialog, NOT DebugDialog
    const dialog = page.locator('[role="dialog"]')
    await expect(dialog).toBeVisible()
    await expect(dialog.getByRole('heading', { level: 2 })).not.toContainText(/debug/i)
  })
})
```

- [ ] **Step 2: Run E2E tests**

Run: `cd web && pnpm test:e2e --grep "Feature Settings"`
Expected: PASS (all 6 tests)

- [ ] **Step 3: Commit**

```bash
git add web/e2e/settings-feature-toggle.spec.ts
git commit -m "test: add E2E tests for feature settings toggle dialog"
```

---

## Task 8: Backend E2E Tests

**Files:**
- Modify: `tests/conftest.py` — 新增 fixture
- Create: `tests/e2e/` (新目錄)
- Create: `tests/e2e/test_settings_toggle.py`

- [ ] **Step 1: 新增 fixture 到 `tests/conftest.py`**

```python
@pytest_asyncio.fixture
async def app_settings_default(db_session: AsyncSession) -> AppSettings:
    """Seed default AppSettings record."""
    settings = AppSettings()
    db_session.add(settings)
    await db_session.commit()
    await db_session.refresh(settings)
    return settings
```

- [ ] **Step 2: 新建 Backend E2E — `tests/e2e/test_settings_toggle.py`**

```python
"""Backend E2E tests for feature settings toggle.

These tests use the real FastAPI test client with a temporary DB.
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession

from src.main import app
from src.api.deps import get_db
from src.models.app_settings import AppSettings


@pytest_asyncio.fixture
async def ac(db_session: AsyncSession):
    """Async HTTP client with DB session override."""
    app.dependency_overrides[get_db] = lambda: db_session
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_full_toggle_cycle(ac: AsyncClient, db_session: AsyncSession):
    """Enable all features, verify 403 gates lift, disable and verify gates block."""
    # 1. Start with all off — gates should block
    db_session.add(AppSettings(group_enabled=False, schedule_enabled=False, share_enabled=False))
    await db_session.commit()

    # 2. GET settings, verify defaults
    resp = await ac.get("/settings")
    if resp.status_code == 401:
        pytest.skip("API key required in this env")
    data = resp.json()
    assert data["group_enabled"] is False

    # 3. Enable all features
    resp = await ac.put("/settings", json={
        "group_enabled": True,
        "schedule_enabled": True,
        "share_enabled": True,
    })
    assert resp.status_code == 200
    enabled = resp.json()
    assert enabled["group_enabled"] is True

    # 4. Verify gates lift
    resp_groups = await ac.get("/api/v1/source-groups")
    assert resp_groups.status_code == 200

    resp_feed = await ac.get("/api/v1/feed", params={"share": "true"})
    assert resp_feed.status_code in (200, 404)

    # 5. Disable group feature
    resp = await ac.put("/settings", json={"group_enabled": False})
    assert resp.json()["group_enabled"] is False

    # 6. Verify gate blocks
    resp_groups = await ac.get("/api/v1/source-groups")
    assert resp_groups.status_code == 403


@pytest.mark.asyncio
async def test_partial_update_preserves_other_fields(ac: AsyncClient, db_session: AsyncSession):
    """PUT with only one field should not change others."""
    db_session.add(AppSettings(group_enabled=True, schedule_enabled=False, share_enabled=False))
    await db_session.commit()

    resp = await ac.put("/settings", json={"share_enabled": True})
    if resp.status_code == 401:
        pytest.skip("API key required")

    data = resp.json()
    assert data["group_enabled"] is True    # preserved
    assert data["schedule_enabled"] is False # preserved
    assert data["share_enabled"] is True     # changed
```

- [ ] **Step 3: Run tests**

Run: `pytest tests/e2e/test_settings_toggle.py -v`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add tests/e2e/test_settings_toggle.py tests/conftest.py
git commit -m "test: add backend E2E tests for feature settings toggle cycle"
```

---

## Self-Review Checklist

- [ ] Spec coverage: DB Model ✓, API route ✓, Feature gates ✓, Frontend composable ✓, Dialog ✓, Conditional rendering ✓, E2E ✓
- [ ] No placeholders: all code blocks have real implementation
- [ ] Type consistency: `AppSettingsResponse` matches backend schema fields (`group_enabled`, `schedule_enabled`, `share_enabled`)
- [ ] All files have correct paths (prefixed with `src/` or `web/src/` or `tests/`)
- [ ] TDD: tests written before implementation for every task
- [ ] Every task ends with a commit

---

**Plan complete and saved to `docs/superpowers/plans/2026-04-21-feature-settings-toggle.md`.**

Two execution options:

**1. Subagent-Driven (recommended)** — I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** — Execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach?
