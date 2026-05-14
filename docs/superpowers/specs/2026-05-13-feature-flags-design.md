# Feature Flags System Design

## Overview

Implement a feature flag system to control two features on the Sources page:
1. **Groups Feature** (`groups_enabled`) - Controls visibility of group-related UI
2. **Group Schedules Feature** (`group_schedules_enabled`) - Controls visibility of scheduled update UI for groups

**Trigger**: Settings 頁面（`/settings`）左上角的 RSS icon，連續點擊 10 次，彈出功能控制彈窗。

---

## Architecture

### Store (`web/src/stores/featureFlags.ts`)

```typescript
import { defineStore } from 'pinia'
import { ref, watch } from 'vue'

export const useFeatureFlagsStore = defineStore('featureFlags', () => {
  const groupsEnabled = ref<boolean>(
    localStorage.getItem('ff_groups_enabled') !== 'false'
  )
  const groupSchedulesEnabled = ref<boolean>(
    localStorage.getItem('ff_group_schedules_enabled') !== 'false'
  )

  watch(groupsEnabled, (val) => {
    localStorage.setItem('ff_groups_enabled', String(val))
    if (!val) {
      groupSchedulesEnabled.value = false
      localStorage.setItem('ff_group_schedules_enabled', 'false')
    }
  })

  watch(groupSchedulesEnabled, (val) => {
    localStorage.setItem('ff_group_schedules_enabled', String(val))
  })

  return { groupsEnabled, groupSchedulesEnabled }
})
```

**Key point**: Store handles only state persistence and the cascade of `group_schedules_enabled → false` when `groups_enabled` is disabled. The confirmation UI logic belongs to the Dialog component.

### Cascade Confirmation Flow (Approach A)

When user turns OFF `groups_enabled`:

1. User toggles Groups switch OFF
2. Inline warning block expands immediately within the dialog:
   ```
   ⚠️ 停用群組功能也將停用排程更新
       [確認]  [取消]
   ```
3. **Confirm** → `groupsEnabled = false` commits, schedules auto-disabled by store watcher, dialog closes
4. **Cancel** → Groups switch snaps back to ON, warning block hides
5. If user closes dialog via `×` while warning is visible → treated as Cancel (Groups stays ON)

---

## Components

### 1. FeatureFlagsDialog.vue (`web/src/components/FeatureFlagsDialog.vue`)

**Props/emits**: `defineProps<{ open: boolean }>() + emit('update:open', value)`

**Internal state**:
- `showCascadeWarning = ref(false)` — controls inline warning visibility
- `pendingGroupsValue = ref<boolean | null>(null)` — holds the pending toggle value during confirmation

**Trigger**: Settings page RSS icon 10-clicks handled in MainLayout.vue (independent from Feed page DebugDialog trigger).

### 2. MainLayout.vue — Settings page trigger

Add to existing `<script setup>`:
```typescript
const settingsClickCount = ref(0)
const settingsClickTimer = ref<ReturnType<typeof setTimeout> | null>(null)
const featureFlagsDialogOpen = ref(false)

function handleSettingsIconClick(): void {
  if (route.path !== '/settings') return
  if (settingsClickTimer.value) clearTimeout(settingsClickTimer.value)
  settingsClickCount.value++
  settingsClickTimer.value = setTimeout(() => { settingsClickCount.value = 0 }, 2000)
  if (settingsClickCount.value >= 10) {
    featureFlagsDialogOpen.value = true
    settingsClickCount.value = 0
    clearTimeout(settingsClickTimer.value)
    settingsClickTimer.value = null
  }
}
```

Template update:
```vue
<Rss class="h-6 w-6 cursor-pointer select-none"
     @click="route.path === '/' ? handleFeedIconClick() : route.path === '/settings' ? handleSettingsIconClick() : null" />
<FeatureFlagsDialog v-model:open="featureFlagsDialogOpen" />
```

---

## Visibility Conditions

| Component | Condition | Location |
|-----------|-----------|----------|
| Groups tab | `v-if="featureFlagsStore.groupsEnabled"` | SourcesPage tab navigation |
| Group filter chips | `v-if="featureFlagsStore.groupsEnabled"` | FeedPage, HistoryPage |
| Group badges (member_count) | `v-if="featureFlagsStore.groupsEnabled"` | SourcesPage group cards |
| ScheduleConfigPanel | `v-if="featureFlagsStore.groupSchedulesEnabled"` | SourcesPage group expanded section |

---

## i18n Keys

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
    "schedulesDisabledHint": "Requires Groups Feature to be enabled",
    "cascadeWarningTitle": "Disabling groups will also disable schedules",
    "cascadeWarningConfirm": "Confirm",
    "cascadeWarningCancel": "Cancel"
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
    "schedulesDisabledHint": "需要先啟用群組功能",
    "cascadeWarningTitle": "停用群組功能也將停用排程更新",
    "cascadeWarningConfirm": "確認",
    "cascadeWarningCancel": "取消"
  }
}
```

---

## File Changes

| File | Action |
|------|--------|
| `web/src/stores/featureFlags.ts` | Create |
| `web/src/components/FeatureFlagsDialog.vue` | Create |
| `web/src/layouts/MainLayout.vue` | Modify — add Settings page trigger |
| `web/src/pages/SourcesPage.vue` | Modify — add v-if conditions |
| `web/src/pages/HistoryPage.vue` | Modify — add v-if conditions |
| `web/src/locales/en.json` | Modify — add i18n keys |
| `web/src/locales/zh.json` | Modify — add i18n keys |
| `web/e2e/group-features.spec.ts` | Modify — add E2E tests for feature flags |

---

## Edge Cases

1. **localStorage manipulation**: If user manually edits localStorage to invalid state (`schedules=true`, `groups=false`), store initialization corrects it via dependency rule.
2. **Concurrent flag changes**: Toggle groups OFF while dialog is open → warning shows immediately.
3. **Navigation during dialog**: Dialog remains open if user navigates between pages.
4. **Closing dialog during warning**: `×` button → Cancel behavior, Groups stays ON.

---

## Testing

### E2E (`web/e2e/feature-flags.spec.ts`)
1. **Trigger Test**: Click Settings RSS icon 10 times → dialog opens
2. **Default State**: Both flags ON by default on fresh browser
3. **Cascade Cancel**: Turn OFF Groups → warning shows → Cancel → Groups stays ON
4. **Cascade Confirm**: Turn OFF Groups → warning shows → Confirm → Groups OFF, Schedules auto-disabled
5. **Dependency Test**: Groups OFF → Schedules cannot be enabled independently
6. **Visibility Test**: Groups OFF → Groups tab hidden in SourcesPage
7. **Persistence**: Changes persist after page reload