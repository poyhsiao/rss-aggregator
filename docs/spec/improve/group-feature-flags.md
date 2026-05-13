# Group Feature Flags Specification

## Overview

Implement a feature flag system to control two features on the Sources page:
1. **Groups Feature** (`groups_enabled`) - Controls visibility of group-related UI
2. **Group Schedules Feature** (`group_schedules_enabled`) - Controls visibility of scheduled update UI for groups

**Trigger**: 設定頁面（Settings）左上角的 RSS icon，連續點擊 10 次，彈出功能控制彈窗。

**與現有 DebugDialog 的區別**：
| 項目 | DebugDialog | FeatureFlagsDialog |
|------|-------------|-------------------|
| 觸發位置 | Feed 頁面（`/`） | Settings 頁面（`/settings`） |
| 觸發次數 | 10 次點擊 RSS icon | 10 次點擊 RSS icon |
| 功能目的 | 顯示除錯資訊 | 控制功能開關 |
| 現有狀態 | 已有，維持不變 | 新增 |

---

## Feature Flag Definitions

### Flag: `groups_enabled`
- **Type**: Boolean
- **Default**: `true` (enabled)
- **Storage**: Browser localStorage (frontend-only toggle, no backend persistence required)
- **Purpose**: Controls the overall Groups functionality

### Flag: `group_schedules_enabled`
- **Type**: Boolean
- **Default**: `true` (enabled)
- **Storage**: Browser localStorage
- **Purpose**: Controls scheduled update functionality for groups
- **Dependency**: Can only be `true` when `groups_enabled` is `true`

---

## Dependency Rules

### Rule 1: Cascading Disable
When `groups_enabled` is set to `false`:
- `group_schedules_enabled` must be automatically set to `false`

### Rule 2: Conditional Enable
When `groups_enabled` is set to `true`:
- `group_schedules_enabled` can be independently set to `true` or `false`

### Rule 3: Prevent Invalid State
The UI must prevent the user from enabling `group_schedules_enabled` when `groups_enabled` is `false`.

---

## UI Visibility Rules

### When `groups_enabled` is `false`:
| Component | Visibility | Location |
|----------|------------|----------|
| Groups tab | Hidden | SourcesPage tab navigation |
| Group filter chips | Hidden | FeedPage, HistoryPage |
| Group badges (member_count) | Hidden | SourcesPage group cards |

### When `group_schedules_enabled` is `false`:
| Component | Visibility | Location |
|----------|------------|----------|
| ScheduleConfigPanel | Hidden | SourcesPage group expanded section |

---

## UI Components to Create/Modify

### 1. FeatureFlagsDialog.vue (NEW)
**Location**: `web/src/components/FeatureFlagsDialog.vue`

**Purpose**: Modal dialog for toggling feature flags

**Trigger Mechanism**:
- **獨立觸發**：在 Settings 頁面（`/settings`）左上角的 RSS icon，連續點擊 10 次
- **獨立計數器**：使用 `settingsClickCount`（與 Feed 頁面的 `clickCount` 完全獨立）
- **不相關聯**：此功能與現有的 DebugDialog（Feed 頁面觸發）完全分開，兩者各自獨立運作

**Settings 頁面觸發邏輯**（新增至 MainLayout.vue）：
```typescript
const settingsClickCount = ref(0)
const settingsClickTimer = ref<ReturnType<typeof setTimeout> | null>(null)
const featureFlagsDialogOpen = ref(false)

function handleSettingsIconClick(): void {
  // Only activate on Settings page
  if (route.path !== '/settings') return

  if (settingsClickTimer.value) {
    clearTimeout(settingsClickTimer.value)
  }

  settingsClickCount.value++

  // Reset counter after 2 seconds of no clicks
  settingsClickTimer.value = setTimeout(() => {
    settingsClickCount.value = 0
  }, 2000)

  // Open feature flags dialog after 10 clicks
  if (settingsClickCount.value >= 10) {
    featureFlagsDialogOpen.value = true
    settingsClickCount.value = 0
    if (settingsClickTimer.value) {
      clearTimeout(settingsClickTimer.value)
      settingsClickTimer.value = null
    }
  }
}
```

**注意**：現有的 DebugDialog 邏輯（原第 24-48 行）維持不變，僅用於 Feed 頁面。兩個觸發邏輯各自獨立存在於 MainLayout.vue 中。

**Dialog Content**:
```
┌─────────────────────────────────────────┐
│ 🔧 Feature Flags                    [×] │
├─────────────────────────────────────────┤
│                                         │
│ ○ Groups Feature                        │
│   [Toggle Switch]                       │
│   Enable/disable group functionality    │
│                                         │
│ ○ Group Schedules                      │
│   [Toggle Switch] (disabled if above)  │
│   Enable/disable scheduled updates      │
│                                         │
├─────────────────────────────────────────┤
│                          [Confirm]      │
└─────────────────────────────────────────┘
```

**Behavior**:
- Changes apply immediately on confirm
- Toggle states reflect current localStorage values
- Disabled toggle for `group_schedules_enabled` when `groups_enabled` is OFF

### 2. Modify MainLayout.vue (ADDITION)
**Change**: Add Settings page trigger for FeatureFlagsDialog (existing Feed page trigger for DebugDialog remains unchanged)

**Addition - Settings page click handler**:
```vue
<script setup lang="ts">
// ... existing code ...

// Existing: Feed page trigger for DebugDialog (unchanged)
const clickCount = ref(0)
const clickTimer = ref<ReturnType<typeof setTimeout> | null>(null)
const debugDialogOpen = ref(false)

function handleFeedIconClick(): void {
  if (route.path !== '/') return  // Only Feed page
  // ... unchanged ...
}

// NEW: Settings page trigger for FeatureFlagsDialog
const settingsClickCount = ref(0)
const settingsClickTimer = ref<ReturnType<typeof setTimeout> | null>(null)
const featureFlagsDialogOpen = ref(false)

function handleSettingsIconClick(): void {
  if (route.path !== '/settings') return  // Only Settings page
  // ... similar logic ...
}
</script>

<template>
  <!-- RSS icon click handler depends on current route -->
  <Rss class="h-6 w-6 cursor-pointer select-none"
       @click="route.path === '/' ? handleFeedIconClick() : route.path === '/settings' ? handleSettingsIconClick() : null" />
  <!-- ... -->
  <FeatureFlagsDialog v-model:open="featureFlagsDialogOpen" />
</template>
```

### 3. Modify SourcesPage.vue
**Visibility Condition for Groups Tab**:
```vue
<button
  v-if="featureFlagsStore.groupsEnabled"
  class="..."
  @click="handleTabChange('groups')"
>
  {{ t('groups.title') }} ({{ groups.length }})
</button>
```

**Visibility Condition for Group Cards Badges**:
```vue
<!-- Only show member_count badge when groups_enabled -->
<Badge v-if="featureFlagsStore.groupsEnabled" variant="secondary">
  {{ group.member_count }} {{ t('groups.sources_badge') }}
</Badge>
```

### 4. Modify FeedPage.vue (if group filter chips exist)
**Visibility Condition for Group Filter Chips**:
```vue
<div v-if="featureFlagsStore.groupsEnabled" class="group-filter-chips">
  ...
</div>
```

### 5. Modify HistoryPage.vue
**Visibility Condition for Group Filter Section**:
```vue
<div v-if="featureFlagsStore.groupsEnabled" class="group-filter">
  ...
</div>
```

### 6. Create/use Feature Flags Store
**Location**: `web/src/stores/featureFlags.ts` (NEW)

```typescript
import { defineStore } from 'pinia'
import { ref, watch } from 'vue'

export const useFeatureFlagsStore = defineStore('featureFlags', () => {
  // State
  const groupsEnabled = ref<boolean>(
    localStorage.getItem('ff_groups_enabled') !== 'false'
  )
  const groupSchedulesEnabled = ref<boolean>(
    localStorage.getItem('ff_group_schedules_enabled') !== 'false'
  )

  // Persistence
  watch(groupsEnabled, (val) => {
    localStorage.setItem('ff_groups_enabled', String(val))
    // Cascade: disable schedules if groups disabled
    if (!val) {
      groupSchedulesEnabled.value = false
      localStorage.setItem('ff_group_schedules_enabled', 'false')
    }
  })

  watch(groupSchedulesEnabled, (val) => {
    localStorage.setItem('ff_group_schedules_enabled', String(val))
  })

  return {
    groupsEnabled,
    groupSchedulesEnabled,
  }
})
```

---

## i18n Keys to Add

### English (`web/src/locales/en.json`)
```json
{
  "featureFlags": {
    "title": "Feature Flags",
    "groupsEnabled": "Groups Feature",
    "groupsEnabledDesc": "Enable/disable group functionality",
    "groupSchedulesEnabled": "Group Schedules",
    "groupSchedulesEnabledDesc": "Enable/disable scheduled updates for groups",
    "confirm": "Confirm",
    "schedulesDisabledHint": "Requires Groups Feature to be enabled"
  }
}
```

### Chinese (`web/src/locales/zh.json`)
```json
{
  "featureFlags": {
    "title": "功能開關",
    "groupsEnabled": "群組功能",
    "groupsEnabledDesc": "啟用/停用群組功能",
    "groupSchedulesEnabled": "群組定時更新",
    "groupSchedulesEnabledDesc": "啟用/停用群組的定時更新功能",
    "confirm": "確認",
    "schedulesDisabledHint": "需要先啟用群組功能"
  }
}
```

---

## File Changes Summary

### New Files
| File | Purpose |
|------|---------|
| `web/src/stores/featureFlags.ts` | Feature flags state management |
| `web/src/components/FeatureFlagsDialog.vue` | Feature flags toggle dialog |

### Modified Files
| File | Changes |
|------|---------|
| `web/src/layouts/MainLayout.vue` | Add Settings page click trigger |
| `web/src/pages/SourcesPage.vue` | Add v-if conditions for groups visibility |
| `web/src/pages/HistoryPage.vue` | Add v-if conditions for group filter visibility |
| `web/src/locales/en.json` | Add i18n keys |
| `web/src/locales/zh.json` | Add i18n keys |

---

## Testing Requirements

### E2E Tests (`web/e2e/feature-flags.spec.ts`)
1. **Trigger Test**: Click Settings RSS icon 10 times, dialog opens
2. **Default State Test**: Both flags ON by default on fresh browser
3. **Dependency Test**: Turning OFF Groups cascades to disable Schedules
4. **Visibility Test - Groups OFF**: Groups tab hidden in SourcesPage
5. **Visibility Test - Schedules OFF**: ScheduleConfigPanel hidden
6. **Confirm Persistence**: Changes persist after page reload
7. **BDD Scenario**: Full user flow with given-when-then format

### Backend Tests (`tests/`)
- No backend changes required (frontend-only feature flags)

---

## Implementation Order

1. Create `featureFlagsStore.ts`
2. Create `FeatureFlagsDialog.vue` component
3. Add i18n keys to both locale files
4. Modify `MainLayout.vue` to add Settings page trigger
5. Modify `SourcesPage.vue` to add visibility conditions
6. Modify `HistoryPage.vue` to add visibility conditions
7. Write E2E tests
8. Run full test suite

---

## Edge Cases

1. **localStorage manipulation**: If user manually edits localStorage to invalid state (schedules=true, groups=false), the store initialization should correct this by applying the dependency rule.

2. **Concurrent flag changes**: Toggle groups OFF while dialog is open - schedules should auto-disable visually.

3. **Navigation during dialog**: Dialog should remain open if user navigates between pages.

---

## Non-Functional Requirements

1. **Performance**: No performance impact - flags are simple boolean checks
2. **Accessibility**: Toggle switches should be keyboard navigable
3. **Mobile**: Dialog should be responsive on mobile screens
