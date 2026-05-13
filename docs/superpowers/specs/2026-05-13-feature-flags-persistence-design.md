# Feature Flags 持久化設計規格書

## 1. 概述

### 現況分析
- **現有機制**：Feature flags 僅儲存於 localStorage，關閉瀏覽器後會重置
- **現有 UI**：已具備 `FeatureFlagsDialog.vue`（emoji + 2xl size）、`FeatureFlagsStore`
- **備份機制**：Settings 頁面 Export/Import Backup
- **觸發方式**：Settings 頁面左上角 RSS icon 連續點擊 10 下

### 目標
1. **資料庫持久化**：將 feature flags 存入後端資料庫
2. **跨瀏覽器同步**：透过 Export/Import Backup 同步 feature flags
3. **UI 風格調整**：FeatureFlagsDialog 改用 DebugDialog 緊湊樣式
4. **完整測試覆蓋**：TDD + BDD，後端 pytest + 前端 Playwright E2E

---

## 2. 功能需求矩陣

| 功能 | Feature Flag Key | 預設值 | 關閉時行為 |
|------|-----------------|--------|-----------|
| 群組功能 | `groups_enabled` | `true` (開啟) | 見下方「UI 隱藏範圍」 |
| 群組定時更新功能 | `group_schedules_enabled` | `true` (開啟) | 隱藏 ScheduleConfigPanel、schedules badge |
| 來源頁面群組定時更新 | `source_group_schedules_enabled` | `true` (開啟) | 隱藏 ScheduleConfigPanel（來源頁面群組 tab） |

### UI 隱藏範圍

| 頁面 | 元素 | 條件 |
|------|------|------|
| **SourcesPage.vue** | Groups Tab | `groupsEnabled === false` |
| **SourcesPage.vue** | 群組成員 badge | `groupsEnabled === false` |
| **SourcesPage.vue** | schedules badge | `groupSchedulesEnabled === false` |
| **SourcesPage.vue** | 刪除群組歷史按鈕 | `groupsEnabled === false` |
| **SourcesPage.vue** | ScheduleConfigPanel | `!isTauri() && sourceGroupSchedulesEnabled === false` |
| **FeedPage.vue** | 群組篩選 chips | `groupsEnabled === false` |
| **FeedPage.vue** | 項目上的群組 badge | `groupsEnabled === false` |
| **HistoryPage.vue** | 群組篩選下拉選單/群組過濾器 | `groupsEnabled === false` |
| **HistoryPage.vue** | Batch 中的群組資訊 | `groupsEnabled === false` |

### 相依性規則

```
群組功能關閉 → 
  - 群組定時更新自動關閉
  - 來源頁面群組定時更新自動關閉
  - 所有群組相關 UI 隱藏

群組功能開啟 → 可獨立控制群組定時更新、來源頁面群組定時更新
```

### Icon 點擊觸發設定

- **位置**：SettingsPage.vue 左上角 RSS icon
- **條件**：3 秒內連續點擊 10 下
- **行為**：直接彈出 FeatureFlagsDialog（不顯示任何提示）

---

## 3. 架構設計

```
┌─────────────────────────────────────────────────────┐
│  Frontend                                             │
│  ┌──────────────────┐    ┌───────────────────────┐ │
│  │ FeatureFlagsStore│◄──►│ /api/feature-flags    │ │
│  │ (localStorage    │    │ (GET/PUT)              │ │
│  │  + API sync)     │    └───────────────────────┘ │
│  └──────────────────┘                                │
│         ▲                                           │
│         │ watch                                    │
│  ┌──────┴────────┐    ┌───────────────────────┐ │
│  │FeatureFlagsDialog│   │ backup_service.py     │ │
│  │ (compact UI)   │    │ (export/import FF)    │ │
│  └─────────────────┘    └───────────────────────┘ │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│  Backend                                             │
│  ┌────────────────┐    ┌───────────────────────┐ │
│  │ FeatureFlag    │───►│ alembic migration      │ │
│  │ (SQLAlchemy)   │    │ (feature_flags table) │ │
│  └────────────────┘    └───────────────────────┘ │
│         │                                           │
│  ┌──────┴────────────────────────────┐            │
│  │ src/api/routes/feature_flags.py    │            │
│  │ GET /api/feature-flags             │            │
│  │ PUT /api/feature-flags             │            │
│  └────────────────────────────────────┘            │
└─────────────────────────────────────────────────────┘
```

---

## 4. API 設計

### 4.1 Feature Flags Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/feature-flags` | 取得所有 feature flags |
| PUT | `/api/feature-flags` | 批量更新 feature flags |

**Request/Response:**
```json
// GET /api/feature-flags
{
  "groups_enabled": true,
  "group_schedules_enabled": true,
  "source_group_schedules_enabled": true
}

// PUT /api/feature-flags
{
  "groups_enabled": false,
  "group_schedules_enabled": true,
  "source_group_schedules_enabled": false
}
```

### 4.2 Backup Export/Import

Export 時 feature_flags 一起打包：
```json
{
  "version": "1.0",
  "exported_at": "2026-05-13T12:00:00Z",
  "sources": [...],
  "groups": [...],
  "feature_flags": {
    "groups_enabled": "true",
    "group_schedules_enabled": "true",
    "source_group_schedules_enabled": "true"
  }
}
```

---

## 5. 後端實作

### 5.1 FeatureFlag Model

**檔案**：`src/models/feature_flag.py`

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

### 5.2 FeatureFlag Service

**檔案**：`src/services/feature_flag_service.py`

提供 CRUD 操作，支援 upsert 邏輯。

### 5.3 API Routes

**檔案**：`src/api/routes/feature_flags.py`

- `GET /api/feature-flags` — 取得所有 flags
- `PUT /api/feature-flags` — 批量更新 flags

### 5.4 Backup Service 修改

**檔案**：`src/services/backup_service.py`

- `export_backup()`: 加入 `feature_flags` 欄位
- `import_backup()`: 處理 `feature_flags` 的還原

### 5.5 Database Migration

**檔案**：`alembic/versions/xxx_add_feature_flags.py`

```python
"""Add feature_flags table.

Revision ID: xxx
Revises: xxx
Create Date: xxx
"""
from alembic import op
import sqlalchemy as sa

revision = 'xxx'
down_revision = 'xxx'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'feature_flags',
        sa.Column('key', sa.String(100), primary_key=True),
        sa.Column('value', sa.String(50), nullable=False, default='true'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    
    # Insert default values
    op.execute("""
        INSERT INTO feature_flags (key, value) VALUES 
        ('groups_enabled', 'true'),
        ('group_schedules_enabled', 'true'),
        ('source_group_schedules_enabled', 'true')
    """)


def downgrade() -> None:
    op.drop_table('feature_flags')
```

---

## 6. 前端實作

### 6.1 Feature Flags API Client

**檔案**：`web/src/api/feature-flags.ts`（新建）

```typescript
export async function getFeatureFlags(): Promise<Record<string, boolean>>
export async function updateFeatureFlags(flags: Record<string, boolean>): Promise<void>
```

### 6.2 FeatureFlagsStore 變更

**檔案**：`web/src/stores/featureFlags.ts`

**變更要點**：
1. 初始載入時，從後端 API 取得 feature flags
2. 變更時，同步更新 localStorage 與後端 API
3. 保留 fallback 機制（網路失敗時使用 localStorage）

```typescript
watch(groupsEnabled, (val) => {
  localStorage.setItem('ff_groups_enabled', String(val))
  api.updateFeatureFlags({ groups_enabled: val })
  if (!val) {
    groupSchedulesEnabled.value = false
    localStorage.setItem('ff_group_schedules_enabled', 'false')
    api.updateFeatureFlags({ group_schedules_enabled: false })
  }
})
```

### 6.3 FeatureFlagsDialog.vue（UI 重新設計）

**設計原則**：參考 DebugDialog.vue 的緊湊樣式

**DebugDialog 參考樣式**：
- Dialog size: `lg`（max-w-xl, ~36rem）
- Header: `p-6` padding，icon + title + close button
- Content: `p-6` padding，`space-y-3` 間距
- 卡片: `p-3 bg-neutral-100 dark:bg-neutral-700 rounded-lg`
- 最小寬度: `min-w-[380px] md:min-w-[480px]`

**FeatureFlagsDialog 新設計**：

```vue
<Dialog :open="open" size="lg" @update:open="handleClose">
  <!-- Header -->
  <div class="flex items-center justify-between mb-4">
    <div class="flex items-center gap-2">
      <SettingsIcon class="h-5 w-5 text-primary-600" />
      <h2 class="text-lg font-semibold">{{ t('featureFlags.title') }}</h2>
    </div>
    <Button variant="ghost" size="icon" @click="close">
      <X class="h-4 w-4" />
    </Button>
  </div>

  <!-- Content -->
  <div class="space-y-3 text-sm">
    <!-- Groups Feature Toggle -->
    <div class="flex items-center justify-between p-3 bg-neutral-100 dark:bg-neutral-700 rounded-lg">
      <div class="flex items-center gap-3">
        <Users class="h-4 w-4 text-neutral-500" />
        <div>
          <p class="font-medium">{{ t('featureFlags.groupsEnabled') }}</p>
          <p class="text-xs text-neutral-500">{{ t('featureFlags.groupsEnabledDesc') }}</p>
        </div>
      </div>
      <Toggle v-model="localGroupsEnabled" @update:model-value="handleGroupsToggle" />
    </div>

    <!-- Cascade Warning -->
    <div v-if="showCascadeWarning" class="p-3 bg-amber-50 dark:bg-amber-950/50 border border-amber-300 dark:border-amber-700 rounded-lg">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-2">
          <AlertTriangle class="h-4 w-4 text-amber-600" />
          <span class="text-sm">{{ t('featureFlags.cascadeWarningTitle') }}</span>
        </div>
        <div class="flex gap-2">
          <Button size="sm" variant="outline" @click="handleCascadeCancel">
            {{ t('featureFlags.cascadeWarningCancel') }}
          </Button>
          <Button size="sm" @click="handleCascadeConfirm">
            {{ t('featureFlags.cascadeWarningConfirm') }}
          </Button>
        </div>
      </div>
    </div>

    <!-- Group Schedules Toggle -->
    <div 
      class="flex items-center justify-between p-3 rounded-lg"
      :class="localGroupsEnabled 
        ? 'bg-neutral-100 dark:bg-neutral-700' 
        : 'bg-neutral-50 dark:bg-neutral-800 opacity-60'"
    >
      <div class="flex items-center gap-3">
        <Clock class="h-4 w-4 text-neutral-400" />
        <div>
          <p class="font-medium text-neutral-500">{{ t('featureFlags.groupSchedulesEnabled') }}</p>
        </div>
      </div>
      <Toggle 
        v-model="localSchedulesEnabled" 
        @update:model-value="handleSchedulesToggle"
        :disabled="!localGroupsEnabled"
      />
    </div>

    <!-- Source Group Schedules Toggle -->
    <div 
      class="flex items-center justify-between p-3 rounded-lg"
      :class="localGroupsEnabled 
        ? 'bg-neutral-100 dark:bg-neutral-700' 
        : 'bg-neutral-50 dark:bg-neutral-800 opacity-60'"
    >
      <div class="flex items-center gap-3">
        <CalendarClock class="h-4 w-4 text-neutral-400" />
        <div>
          <p class="font-medium text-neutral-500">{{ t('featureFlags.sourceGroupSchedulesEnabled') }}</p>
        </div>
      </div>
      <Toggle 
        v-model="localSourceGroupSchedulesEnabled" 
        @update:model-value="handleSourceGroupSchedulesToggle"
        :disabled="!localGroupsEnabled"
      />
    </div>
  </div>

  <!-- Footer -->
  <template #footer>
    <div class="flex justify-end gap-2">
      <Button variant="outline" @click="handleClose">
        {{ t('common.cancel') }}
      </Button>
      <Button @click="handleConfirm">
        {{ t('featureFlags.confirm') }}
      </Button>
    </div>
  </template>
</Dialog>
```

### 6.4 UI 隱藏實作

#### SourcesPage.vue

```vue
<!-- Groups Tab 按鈕 -->
<button v-if="featureFlagsStore.groupsEnabled" ...>

<!-- 群組 sources badge -->
<Badge v-if="featureFlagsStore.groupsEnabled" ...>

<!-- schedules badge -->
<Badge v-if="featureFlagsStore.groupSchedulesEnabled && group.schedule_count" ...>

<!-- ScheduleConfigPanel -->
<ScheduleConfigPanel 
  v-if="!isTauri() && featureFlagsStore.sourceGroupSchedulesEnabled" 
  :group-id="group.id" 
/>
```

#### FeedPage.vue

```vue
<!-- 群組篩選 chips -->
<div v-if="featureFlagsStore.groupsEnabled && groups.length > 0" ...>

<!-- 項目上的群組 badge -->
<template v-if="featureFlagsStore.groupsEnabled && item.source_groups?.length">
  ...
</template>
```

#### HistoryPage.vue

```vue
<!-- 群組篩選下拉選單 -->
<select v-if="featureFlagsStore.groupsEnabled" ...>

<!-- Batch 中的群組資訊 -->
<template v-if="featureFlagsStore.groupsEnabled">
  ...
</template>
```

---

## 7. 測試策略

### 7.1 測試層次

| 層次 | 工具 | 測試內容 |
|------|------|----------|
| **Unit** | pytest | FeatureFlag model CRUD, service logic |
| **Integration** | pytest | backup export/import with feature_flags |
| **E2E API** | Playwright | GET/PUT /api/feature-flags |
| **E2E UI** | Playwright | 觸發 → toggle → confirm → 驗證 UI 隱藏 |

### 7.2 後端測試案例

#### Model Tests
```python
def test_feature_flag_create():
    """建立新的 feature flag"""
    
def test_feature_flag_read():
    """讀取所有 feature flags"""
    
def test_feature_flag_update():
    """更新單一 flag"""

def test_feature_flag_upsert():
    """不存在的 flag 自动建立，已存在的 flag 更新"""
```

#### Service Tests
```python
def test_get_all_feature_flags():
    """取得所有 flags，包含預設值"""
    
def test_update_feature_flags_batch():
    """批量更新 flags"""
    
def test_cascade_disable_schedules_when_groups_disabled():
    """關閉群組功能時，連動關閉排程功能"""
```

#### Backup Integration Tests
```python
def test_export_includes_feature_flags():
    """Export backup 包含 feature_flags 欄位"""
    
def test_import_restores_feature_flags():
    """Import backup 還原 feature_flags"""
```

### 7.3 前端 E2E 測試案例

#### API E2E Tests
```typescript
test('GET /api/feature-flags returns all flags', async ({ page }) => {
  const response = await api.getFeatureFlags()
  expect(response.groups_enabled).toBe(true)
})

test('PUT /api/feature-flags updates flags', async ({ page }) => {
  await api.updateFeatureFlags({ groups_enabled: false })
  const updated = await api.getFeatureFlags()
  expect(updated.groups_enabled).toBe(false)
})
```

#### UI E2E Tests
```typescript
test('opens feature flags dialog after 10 icon clicks', async ({ page }) => {
  // Click RSS icon 10 times
  // Verify dialog appears
})

test('dialog uses DebugDialog compact style', async ({ page }) => {
  // Verify size="lg"
  // Verify lucide icons (not emoji)
  // Verify p-3 rounded-lg cards
})

test('disabling groups hides all group-related UI', async ({ page }) => {
  // Open dialog, disable groups
  // Navigate to Sources/Feed/History
  // Verify UI elements are hidden
})

test('feature flags persisted to database', async ({ page }) => {
  // Change flags, reload page
  // Verify changes persisted
})

test('cascade warning when disabling groups', async ({ page }) => {
  // Toggle groups OFF
  // Verify warning appears
  // Verify Confirm/Cancel behavior
})
```

---

## 8. 受影響檔案清單

### 後端

| 檔案 | 變更類型 |
|------|----------|
| `src/models/feature_flag.py` | 新建 |
| `src/models/__init__.py` | 修改（匯出 FeatureFlag） |
| `src/services/feature_flag_service.py` | 新建 |
| `src/api/routes/feature_flags.py` | 新建 |
| `src/api/__init__.py` | 修改（註冊路由） |
| `src/services/backup_service.py` | 修改 |
| `alembic/versions/xxx_add_feature_flags.py` | 新建 |
| `tests/` | 新增測試 |

### 前端

| 檔案 | 變更類型 |
|------|----------|
| `web/src/api/feature-flags.ts` | 新建 |
| `web/src/stores/featureFlags.ts` | 修改 |
| `web/src/components/FeatureFlagsDialog.vue` | 修改 |
| `web/src/pages/SettingsPage.vue` | 修改 |
| `web/src/pages/SourcesPage.vue` | 修改 |
| `web/src/pages/FeedPage.vue` | 修改 |
| `web/src/pages/HistoryPage.vue` | 修改 |
| `web/src/locales/en.json` | 修改 |
| `web/src/locales/zh.json` | 修改 |
| `web/e2e/feature-flags.spec.ts` | 修改 |

---

## 9. 開發流程（TDD）

### Phase 1: 後端 Model & API（RED → GREEN）

1. 撰寫 `tests/test_feature_flag_model.py`
2. 撰寫 `tests/test_feature_flag_service.py`
3. 撰寫 `tests/test_feature_flag_api.py`
4. 撰寫 `tests/test_backup_with_feature_flags.py`
5. 實作 FeatureFlag model + migration
6. 實作 FeatureFlagService
7. 實作 API routes
8. 修改 backup_service

### Phase 2: 前端 Store & API Client（RED → GREEN）

1. 撰寫 `web/e2e/feature-flags-api.spec.ts`
2. 實作 `web/src/api/feature-flags.ts`
3. 修改 `web/src/stores/featureFlags.ts` 同步邏輯

### Phase 3: UI 實作（RED → GREEN）

1. 撰寫 `web/e2e/feature-flags-dialog.spec.ts`
2. 實作 FeatureFlagsDialog 緊湊樣式
3. 實作 UI 隱藏邏輯（SourcesPage, FeedPage, HistoryPage）
4. 新增 i18n keys

### Phase 4: 驗證

1. 執行所有後端測試（pytest）
2. 執行所有 E2E 測試（Playwright）
3. 手動驗證

---

## 10. 風險與考量

1. **Migration 先後順序**：需確認現有 alembic head 位置
2. **Backup 版本相容性**：新舊版本的 backup 格式需要處理
3. **網路失敗 fallback**：前端需妥善處理 API 失敗的情況（localStorage fallback）
4. **群組資料的保留**：關閉群組功能不應刪除群組資料
5. **Tauri 環境差異**：ScheduleConfigPanel 只在非 Tauri 環境顯示