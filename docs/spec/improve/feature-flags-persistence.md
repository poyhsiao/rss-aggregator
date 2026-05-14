# Feature Flags 控制功能改善規格書

## 1. 概述

### 現況分析
- **現有機制**：Feature flags 僅儲存於 localStorage，關閉瀏覽器後會重置
- **現有 UI**：已具備 `FeatureFlagsDialog.vue`、`FeatureFlagsStore`
- **Backup 機制**：`backup_service.py` 目前未包含 feature flags
- **觸發方式**：Settings 頁面左上角 RSS icon 連續點擊 10 下

### 調整重點
1. **資料庫持久化**：將 feature flags 存入後端資料庫
2. **跨裝置同步**：透過備份/還原機制同步 feature flags
3. **完整 UI 隱藏**：當群組功能關閉時，需隱藏 Feed、History 中的群組相關 UI
4. **UI 風格調整**：FeatureFlagsDialog 改用 DebugDialog 緊湊樣式
5. **E2E 測試驗證**：使用 Playwright 確保呈現正確

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

## 3. 後端實作

### 3.1 新增 FeatureFlag Model

**檔案**：`src/models/feature_flag.py`（新建）

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

### 3.2 新增 FeatureFlag API Routes

**檔案**：`src/api/routes/feature_flags.py`（新建）

| 方法 | 路徑 | 說明 |
|------|------|------|
| GET | `/api/feature-flags` | 取得所有 feature flags |
| PUT | `/api/feature-flags` | 批量更新 feature flags |

### 3.3 新增 FeatureFlag Service

**檔案**：`src/services/feature_flag_service.py`（新建）

### 3.4 修改 Backup Service

**檔案**：`src/services/backup_service.py`

**新增**：
- 在 export_backup 中加入 feature_flags 資料
- 在 import_backup 中處理 feature_flags 的還原

---

## 4. 前端實作

### 4.1 FeatureFlagsStore 變更

**檔案**：`web/src/stores/featureFlags.ts`

**變更要點**：
1. 初始載入時，從後端 API 取得 feature flags
2. 變更時，同步更新 localStorage 與後端 API
3. 保留 fallback 機制（網路失敗時使用 localStorage）

### 4.2 新增 Feature Flags API Client

**檔案**：`web/src/api/feature-flags.ts`（新建）

```typescript
// 所需函式
export async function getFeatureFlags(): Promise<Record<string, boolean>>
export async function updateFeatureFlags(flags: Record<string, boolean>): Promise<void>
```

### 4.3 FeatureFlagsDialog.vue 變更（UI 重新設計）

**設計原則**：參考 DebugDialog.vue 的緊湊樣式

**DebugDialog 參考樣式**：
- Dialog size: `lg`（max-w-xl, ~36rem）
- Header: `p-6` padding，icon + title + close button
- Content: `p-6` padding，`space-y-3` 間距
- 卡片: `p-3 bg-neutral-100 dark:bg-neutral-700 rounded-lg`
- 最小寬度: `min-w-[380px] md:min-w-[480px]`

**FeatureFlagsDialog 新設計**：

```vue
<!-- 參考 DebugDialog 樣式 -->
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

    <!-- Source Group Schedules Toggle (新增) -->
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

**變更要點**：
1. 使用 `size="lg"` 而非 `size="2xl"`
2. 使用 lucide icons（Settings、Users、Clock、CalendarClock、AlertTriangle、X）而非 emoji
3. 緊湊的 `p-3 rounded-lg` 卡片而非大間距的 `p-6 rounded-2xl`
4. 新增第三個 feature flag（source_group_schedules_enabled）
5. 使用 Dialog 的 footer slot 放置確認/取消按鈕

### 4.4 SettingsPage.vue 變更

**新增 Icon 點擊計數器邏輯**（參考 MainLayout.vue debug dialog 模式）：

```typescript
const iconClickCount = ref(0)
const iconClickTimer = ref<ReturnType<typeof setTimeout> | null>(null)
const showFeatureFlagsDialog = ref(false)

function handleIconClick(): void {
  if (iconClickTimer.value) {
    clearTimeout(iconClickTimer.value)
  }
  
  iconClickCount.value++
  
  iconClickTimer.value = setTimeout(() => {
    iconClickCount.value = 0
  }, 300)
  
  if (iconClickCount.value >= 10) {
    iconClickCount.value = 0
    showFeatureFlagsDialog.value = true
  }
}
```

### 4.5 SourcesPage.vue 變更

**新增條件**：
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

### 4.6 FeedPage.vue 變更

**新增條件**：
```vue
<!-- 群組篩選 chips -->
<div v-if="featureFlagsStore.groupsEnabled && groups.length > 0" ...>

<!-- 項目上的群組 badge -->
<template v-if="featureFlagsStore.groupsEnabled && item.source_groups?.length">
  ...
</template>
```

### 4.7 HistoryPage.vue 變更

**新增條件**：
```vue
<!-- 群組篩選下拉選單 -->
<select v-if="featureFlagsStore.groupsEnabled" ...>

<!-- Batch 中的群組資訊 -->
<template v-if="featureFlagsStore.groupsEnabled">
  ...
</template>
```

---

## 5. 國際化 (i18n) 變更

**檔案**：`web/src/locales/en.json` 與 `zh.json`

**新增翻譯**：
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

---

## 6. 資料庫 Migration

**檔案**：`alembic/versions/xxx_add_feature_flags.py`（新建）

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

## 7. E2E 測試（Playwright）

### 7.1 測試檔案

**檔案**：`web/e2e/feature-flags.spec.ts`（新建）

### 7.2 測試環境設定

```typescript
// web/e2e/feature-flags.spec.ts
import { test, expect } from '@playwright/test'

test.describe('Feature Flags', () => {
  test.beforeEach(async ({ page }) => {
    // Login and navigate to Settings
    await page.goto('/settings')
  })
```

### 7.3 測試案例

#### Case 1: Icon 點擊觸發 Dialog
```typescript
test('opens feature flags dialog after 10 icon clicks', async ({ page }) => {
  const icon = page.locator('[data-testid="settings-icon"]')
  
  // Click 10 times rapidly
  for (let i = 0; i < 10; i++) {
    await icon.click()
    await page.waitForTimeout(30) // ~30ms between clicks
  }
  
  // Dialog should appear
  const dialog = page.locator('[role="dialog"]')
  await expect(dialog).toBeVisible()
  await expect(page.getByText('Feature Flags')).toBeVisible()
})
```

#### Case 2: Dialog 樣式驗證
```typescript
test('dialog matches DebugDialog compact style', async ({ page }) => {
  // Open dialog
  const icon = page.locator('[data-testid="settings-icon"]')
  for (let i = 0; i < 10; i++) {
    await icon.click()
    await page.waitForTimeout(30)
  }
  
  const dialog = page.locator('[role="dialog"]')
  await expect(dialog).toBeVisible()
  
  // Verify compact style - dialog should NOT have 2xl size
  // DebugDialog uses lg which is max-w-xl
  const dialogBox = dialog.locator('.bg-white.dark\\\\:bg-neutral-800')
  await expect(dialogBox).toBeVisible()
  
  // Verify lucide icons are used (not emoji)
  await expect(page.locator('.lucide-settings, [data-testid="settings-icon"]')).toBeVisible()
  await expect(page.locator('.lucide-users')).toBeVisible()
  await expect(page.locator('.lucide-clock')).toBeVisible()
  await expect(page.locator('.lucide-calendar-clock')).toBeVisible()
  
  // Verify NO emoji in the dialog
  const dialogContent = await dialog.textContent()
  expect(dialogContent).not.toMatch(/[^\w\s]/) // Should not contain emoji
})
```

#### Case 3: 群組功能開關與 UI 隱藏
```typescript
test('disabling groups hides all group-related UI', async ({ page }) => {
  // Open dialog and disable groups
  const icon = page.locator('[data-testid="settings-icon"]')
  for (let i = 0; i < 10; i++) {
    await icon.click()
    await page.waitForTimeout(30)
  }
  
  // Find and disable the groups toggle
  const groupsToggle = page.getByRole('switch', { name: /groups/i })
  await groupsToggle.click()
  
  // Cascade warning should appear
  await expect(page.getByText('Disabling groups will also disable schedules')).toBeVisible()
  
  // Confirm
  await page.getByRole('button', { name: 'Confirm' }).click()
  
  // Navigate to Sources page
  await page.goto('/sources')
  
  // Groups tab should not be visible
  const groupsTab = page.getByRole('tab', { name: /groups/i })
  await expect(groupsTab).not.toBeVisible()
  
  // Navigate to Feed page
  await page.goto('/feed')
  
  // Group filter chips should not be visible
  const groupChips = page.getByTestId('group-filter-chip')
  await expect(groupChips).toHaveCount(0)
  
  // Navigate to History page
  await page.goto('/history')
  
  // Group filter should not be visible
  const groupFilter = page.getByTestId('group-filter')
  await expect(groupFilter).not.toBeVisible()
})
```

#### Case 4: 群組功能開啟時可控制排程功能
```typescript
test('can toggle schedules independently when groups enabled', async ({ page }) => {
  // Open dialog
  const icon = page.locator('[data-testid="settings-icon"]')
  for (let i = 0; i < 10; i++) {
    await icon.click()
    await page.waitForTimeout(30)
  }
  
  // Ensure groups is enabled
  const groupsToggle = page.getByRole('switch', { name: /groups/i })
  await expect(groupsToggle).toBeChecked()
  
  // Toggle schedules off
  const schedulesToggle = page.getByRole('switch', { name: /schedules/i }).first()
  await schedulesToggle.click()
  
  // Confirm
  await page.getByRole('button', { name: 'Confirm' }).click()
  
  // Verify schedules badge is hidden on Sources page
  await page.goto('/sources')
  const schedulesBadge = page.getByTestId('schedules-badge')
  await expect(schedulesBadge).toHaveCount(0)
})
```

#### Case 5: 設定同步至資料庫
```typescript
test('feature flags are persisted to database', async ({ page }) => {
  // Open dialog
  const icon = page.locator('[data-testid="settings-icon"]')
  for (let i = 0; i < 10; i++) {
    await icon.click()
    await page.waitForTimeout(30)
  }
  
  // Disable groups
  const groupsToggle = page.getByRole('switch', { name: /groups/i })
  await groupsToggle.click()
  
  // Handle cascade warning if appears
  const cascadeWarning = page.getByText('Disabling groups will also disable schedules')
  if (await cascadeWarning.isVisible()) {
    await page.getByRole('button', { name: 'Confirm' }).click()
  } else {
    await page.getByRole('button', { name: 'Confirm' }).click()
  }
  
  // Reload page
  await page.reload()
  
  // Open dialog again
  for (let i = 0; i < 10; i++) {
    await icon.click()
    await page.waitForTimeout(30)
  }
  
  // Groups should still be disabled
  const groupsToggleAfterReload = page.getByRole('switch', { name: /groups/i })
  await expect(groupsToggleAfterReload).not.toBeChecked()
})
```

#### Case 6: Source Group Schedules Toggle
```typescript
test('source group schedules toggle controls ScheduleConfigPanel visibility', async ({ page }) => {
  // Open dialog
  const icon = page.locator('[data-testid="settings-icon"]')
  for (let i = 0; i < 10; i++) {
    await icon.click()
    await page.waitForTimeout(30)
  }
  
  // Find the third toggle (source group schedules)
  const toggles = page.getByRole('switch')
  await toggles.nth(2).click()
  
  // Confirm
  await page.getByRole('button', { name: 'Confirm' }).click()
  
  // Navigate to Sources page, expand a group
  await page.goto('/sources')
  await page.getByTestId('expand-group-button').first().click()
  
  // ScheduleConfigPanel should not be visible
  const scheduleConfigPanel = page.getByTestId('schedule-config-panel')
  await expect(scheduleConfigPanel).not.toBeVisible()
})
```

### 7.4 測試資料屬性

為確保測試順利，需在相關元件上新增 `data-testid`：

| 元件 | data-testid |
|------|-------------|
| Settings RSS icon | `settings-icon` |
| Groups filter chips | `group-filter-chip` |
| Groups filter | `group-filter` |
| Schedules badge | `schedules-badge` |
| Expand group button | `expand-group-button` |
| Schedule config panel | `schedule-config-panel` |

---

## 8. 受影響檔案清單

### 後端
| 檔案 | 變更類型 |
|------|----------|
| `src/models/feature_flag.py` | 新建 |
| `src/api/routes/feature_flags.py` | 新建 |
| `src/services/feature_flag_service.py` | 新建 |
| `src/services/backup_service.py` | 修改 |
| `src/models/__init__.py` | 修改（匯出 FeatureFlag） |
| `src/api/__init__.py` | 修改（註冊路由） |
| `alembic/versions/xxx_add_feature_flags.py` | 新建 |

### 前端
| 檔案 | 變更類型 |
|------|----------|
| `web/src/stores/featureFlags.ts` | 修改 |
| `web/src/api/feature-flags.ts` | 新建 |
| `web/src/components/FeatureFlagsDialog.vue` | 修改（重新設計 UI） |
| `web/src/pages/SettingsPage.vue` | 修改 |
| `web/src/pages/SourcesPage.vue` | 修改 |
| `web/src/pages/FeedPage.vue` | 修改 |
| `web/src/pages/HistoryPage.vue` | 修改 |
| `web/src/locales/en.json` | 修改 |
| `web/src/locales/zh.json` | 修改 |

### 測試
| 檔案 | 變更類型 |
|------|----------|
| `web/e2e/feature-flags.spec.ts` | 新建 |

---

## 9. 開發流程

### Phase 1: TDD - 測試先行
1. 撰寫 E2E 測試案例
2. 確認測試失败（Red Phase）

### Phase 2: 後端 - Feature Flag Model & API
1. 建立資料庫 Migration
2. 建立 FeatureFlag Model
3. 建立 FeatureFlag Service
4. 建立 API Routes

### Phase 3: Backup Service
1. 修改 backup_service.py 包含 feature flags

### Phase 4: FeatureFlagsStore & API Client
1. 修改 store 以支援後端同步
2. 建立 feature-flags API client

### Phase 5: 前端 UI 調整
1. 修改 FeatureFlagsDialog（DebugDialog 緊湊樣式）
2. 修改 SourcesPage
3. 修改 FeedPage
4. 修改 HistoryPage
5. 修改 SettingsPage（icon 點擊計數器）

### Phase 6: i18n
1. 新增所有翻譯 key

### Phase 7: 驗證
1. 執行所有 E2E 測試
2. 手動驗證所有功能

---

## 10. 風險與考量

1. **Migration 先後順序**：需確認現有 alembic head 位置
2. **Backup 版本相容性**：新舊版本的 backup 格式需要處理
3. **網路失敗 fallback**：前端需妥善處理 API 失敗的情況
4. **群組資料的保留**：關閉群組功能不應刪除群組資料
5. **Tauri 環境差異**：ScheduleConfigPanel 只在非 Tauri 環境顯示
