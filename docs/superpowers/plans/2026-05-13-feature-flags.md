# Feature Flags Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement a feature flag system to control Groups and Group Schedules visibility on the Sources page, triggered by 10 clicks on the Settings RSS icon.

**Architecture:** Pinia store for flag state with localStorage persistence; Dialog component for toggle UI with cascade confirmation; visibility conditions via `v-if` on existing components.

**Tech Stack:** Vue 3, Pinia, Tailwind, headless radix Dialog, vue-i18n, Playwright E2E

---

## File Map

```
web/src/
├── stores/
│   └── featureFlags.ts          [NEW] Pinia store with localStorage persistence
├── components/
│   └── FeatureFlagsDialog.vue   [NEW] Feature flags toggle dialog with cascade warning
├── layouts/
│   └── MainLayout.vue           [MODIFY] Add Settings page trigger
├── pages/
│   ├── SourcesPage.vue          [MODIFY] Add v-if for groups tab and badges
│   └── HistoryPage.vue         [MODIFY] Add v-if for group filter
├── locales/
│   ├── en.json                  [MODIFY] Add featureFlags i18n keys
│   └── zh.json                  [MODIFY] Add featureFlags i18n keys
web/e2e/
└── group-features.spec.ts        [MODIFY] Add feature flags E2E tests
```

---

## Task 1: Create featureFlagsStore.ts

**Files:**
- Create: `web/src/stores/featureFlags.ts`

- [ ] **Step 1: Write the store**

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

- [ ] **Step 2: Verify file exists**

Run: `ls web/src/stores/featureFlags.ts`

- [ ] **Step 3: Commit**

```bash
git add web/src/stores/featureFlags.ts
git commit -m "feat(ff): add feature flags store with localStorage persistence"
```

---

## Task 2: Add i18n keys to locale files

**Files:**
- Modify: `web/src/locales/en.json`
- Modify: `web/src/locales/zh.json`

- [ ] **Step 1: Find the last top-level key in en.json**

Run: `grep -n "^[  ]*\"[a-z]+\": {" web/src/locales/en.json | tail -5`

- [ ] **Step 2: Add featureFlags keys to en.json**

Insert after the last entry (before final `}`), adding a comma to the previous entry:
```json
,
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
```

- [ ] **Step 3: Add featureFlags keys to zh.json**

```json
,
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
```

- [ ] **Step 4: Verify JSON syntax**

Run: `cd web && pnpm lint -- --fix src/locales/en.json src/locales/zh.json`

- [ ] **Step 5: Commit**

```bash
git add web/src/locales/en.json web/src/locales/zh.json
git commit -m "feat(i18n): add featureFlags locale keys for en and zh"
```

---

## Task 3: Create FeatureFlagsDialog.vue

**Files:**
- Create: `web/src/components/FeatureFlagsDialog.vue`

- [ ] **Step 1: Write the component**

```vue
<script setup lang="ts">
import { ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import Dialog from '@/components/ui/Dialog.vue'
import Button from '@/components/ui/Button.vue'
import { useFeatureFlagsStore } from '@/stores/featureFlags'

const { t } = useI18n()
const store = useFeatureFlagsStore()

const props = defineProps<{ open: boolean }>()
const emit = defineEmits<{ (e: 'update:open', value: boolean): void }>()

const showCascadeWarning = ref(false)
const pendingGroupsValue = ref<boolean | null>(null)

const localGroupsEnabled = ref(store.groupsEnabled)
const localSchedulesEnabled = ref(store.groupSchedulesEnabled)

watch(() => props.open, (val) => {
  if (val) {
    localGroupsEnabled.value = store.groupsEnabled
    localSchedulesEnabled.value = store.groupSchedulesEnabled
    showCascadeWarning.value = false
    pendingGroupsValue.value = null
  }
})

function handleGroupsToggle(val: boolean) {
  localGroupsEnabled.value = val
  if (!val && store.groupSchedulesEnabled) {
    showCascadeWarning.value = true
    pendingGroupsValue.value = false
  } else {
    showCascadeWarning.value = false
    pendingGroupsValue.value = null
    store.groupsEnabled = val
    localSchedulesEnabled.value = store.groupSchedulesEnabled
  }
}

function handleSchedulesToggle(val: boolean) {
  localSchedulesEnabled.value = val
  store.groupSchedulesEnabled = val
}

function handleCascadeConfirm() {
  store.groupsEnabled = false
  localSchedulesEnabled.value = false
  showCascadeWarning.value = false
  pendingGroupsValue.value = null
  emit('update:open', false)
}

function handleCascadeCancel() {
  localGroupsEnabled.value = true
  showCascadeWarning.value = false
  pendingGroupsValue.value = null
}

function handleConfirm() {
  store.groupsEnabled = localGroupsEnabled.value
  store.groupSchedulesEnabled = localSchedulesEnabled.value
  emit('update:open', false)
}

function handleClose() {
  if (showCascadeWarning.value) {
    handleCascadeCancel()
  }
  emit('update:open', false)
}
</script>

<template>
  <Dialog :open="open" size="sm" @update:open="handleClose">
    <template #header>
      <span class="flex items-center gap-2">
        <span>🔧</span>
        {{ t('featureFlags.title') }}
      </span>
    </template>

    <div class="space-y-4">
      <!-- Groups Feature Toggle -->
      <div class="flex items-start justify-between gap-3">
        <div class="flex-1">
          <div class="font-medium">{{ t('featureFlags.groupsEnabled') }}</div>
          <div class="text-sm text-neutral-500">{{ t('featureFlags.groupsEnabledDesc') }}</div>
        </div>
        <button
          type="button"
          class="relative inline-flex h-6 w-11 items-center rounded-full transition-colors"
          :class="localGroupsEnabled ? 'bg-purple-600' : 'bg-neutral-300 dark:bg-neutral-600'"
          @click="handleGroupsToggle(!localGroupsEnabled)"
        >
          <span
            class="inline-block h-4 w-4 transform rounded-full bg-white transition-transform"
            :class="localGroupsEnabled ? 'translate-x-6' : 'translate-x-1'"
          />
        </button>
      </div>

      <!-- Cascade Warning (inline) -->
      <div
        v-if="showCascadeWarning"
        class="rounded-lg border border-amber-300 dark:border-amber-600 bg-amber-50 dark:bg-amber-950/30 p-3 space-y-3"
      >
        <div class="flex items-start gap-2">
          <span class="text-amber-500 mt-0.5">⚠️</span>
          <div class="text-sm">{{ t('featureFlags.cascadeWarningTitle') }}</div>
        </div>
        <div class="flex gap-2">
          <Button size="sm" @click="handleCascadeConfirm">
            {{ t('featureFlags.cascadeWarningConfirm') }}
          </Button>
          <Button size="sm" variant="secondary" @click="handleCascadeCancel">
            {{ t('featureFlags.cascadeWarningCancel') }}
          </Button>
        </div>
      </div>

      <!-- Group Schedules Toggle -->
      <div class="flex items-start justify-between gap-3">
        <div class="flex-1">
          <div class="font-medium">{{ t('featureFlags.groupSchedulesEnabled') }}</div>
          <div class="text-sm text-neutral-500">
            {{ store.groupsEnabled ? t('featureFlags.groupSchedulesEnabledDesc') : t('featureFlags.schedulesDisabledHint') }}
          </div>
        </div>
        <button
          type="button"
          class="relative inline-flex h-6 w-11 items-center rounded-full transition-colors"
          :class="[
            localSchedulesEnabled
              ? 'bg-purple-600'
              : 'bg-neutral-300 dark:bg-neutral-600',
            !localGroupsEnabled && 'opacity-50 cursor-not-allowed'
          ]"
          :disabled="!localGroupsEnabled"
          @click="localGroupsEnabled && handleSchedulesToggle(!localSchedulesEnabled)"
        >
          <span
            class="inline-block h-4 w-4 transform rounded-full bg-white transition-transform"
            :class="localSchedulesEnabled ? 'translate-x-6' : 'translate-x-1'"
          />
        </button>
      </div>
    </div>

    <template #footer>
      <Button @click="handleConfirm">
        {{ t('featureFlags.confirm') }}
      </Button>
    </template>
  </Dialog>
</template>
```

- [ ] **Step 2: Verify typecheck**

Run: `cd web && pnpm typecheck 2>&1 | grep FeatureFlags`

- [ ] **Step 3: Commit**

```bash
git add web/src/components/FeatureFlagsDialog.vue
git commit -m "feat(ff): add FeatureFlagsDialog with cascade confirmation"
```

---

## Task 4: Modify MainLayout.vue — Add Settings page trigger

**Files:**
- Modify: `web/src/layouts/MainLayout.vue`

- [ ] **Step 1: Read current MainLayout.vue trigger code**

Run: `sed -n '19,55p' web/src/layouts/MainLayout.vue`

- [ ] **Step 2: Add Settings page trigger after existing Feed trigger**

After the closing of `handleFeedIconClick` function (around line 49), add:

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

- [ ] **Step 3: Update the RSS icon click handler**

Find `<Rss class="h-6 w-6 cursor-pointer select-none" @click="handleFeedIconClick" />` and update to:
```vue
<Rss class="h-6 w-6 cursor-pointer select-none"
     @click="route.path === '/' ? handleFeedIconClick() : route.path === '/settings' ? handleSettingsIconClick() : null" />
```

- [ ] **Step 4: Add FeatureFlagsDialog to template**

Find `<DebugDialog v-model:open="debugDialogOpen" />` and add after it:
```vue
<FeatureFlagsDialog v-model:open="featureFlagsDialogOpen" />
```

- [ ] **Step 5: Add store import**

Add import: `import { useFeatureFlagsStore } from '@/stores/featureFlags'`

- [ ] **Step 6: Verify typecheck**

Run: `cd web && pnpm typecheck 2>&1 | grep MainLayout`

- [ ] **Step 7: Commit**

```bash
git add web/src/layouts/MainLayout.vue
git commit -m "feat(ff): add Settings page trigger for FeatureFlagsDialog"
```

---

## Task 5: Modify SourcesPage.vue — Add v-if conditions

**Files:**
- Modify: `web/src/pages/SourcesPage.vue`

- [ ] **Step 1: Add store import and instance**

Add import after existing imports:
```typescript
import { useFeatureFlagsStore } from '@/stores/featureFlags'
```

After `const { t } = useI18n()` (around line 35), add:
```typescript
const featureFlagsStore = useFeatureFlagsStore()
```

- [ ] **Step 2: Wrap groups tab button with v-if**

Find the button around line 440-450 that handles `handleTabChange('groups')`. Wrap with `v-if`:
```vue
<button
  v-if="featureFlagsStore.groupsEnabled"
  type="button"
  ...existing classes...
  @click="handleTabChange('groups')"
>
  {{ t('groups.title') }} ({{ groups.length }})
</button>
```

- [ ] **Step 3: Wrap member_count badge with v-if**

Around line 740, find the Badge for member_count and wrap:
```vue
<Badge v-if="featureFlagsStore.groupsEnabled" variant="secondary">
  {{ group.member_count }} {{ t('groups.sources_badge') }}
</Badge>
```

- [ ] **Step 4: Verify ScheduleConfigPanel visibility**

Check `web/src/components/ScheduleConfigPanel.vue` — if it exists and is used in SourcesPage's group expanded section, ensure it has `v-if="featureFlagsStore.groupSchedulesEnabled"` wrapper.

- [ ] **Step 5: Verify typecheck**

Run: `cd web && pnpm typecheck 2>&1 | grep SourcesPage`

- [ ] **Step 6: Commit**

```bash
git add web/src/pages/SourcesPage.vue
git commit -m "feat(ff): add groupsEnabled visibility conditions to SourcesPage"
```

---

## Task 6: Modify HistoryPage.vue — Add v-if for group filter

**Files:**
- Modify: `web/src/pages/HistoryPage.vue`

- [ ] **Step 1: Add store import and instance**

Add import after existing imports:
```typescript
import { useFeatureFlagsStore } from '@/stores/featureFlags'
```

After `const { t } = useI18n()`, add:
```typescript
const featureFlagsStore = useFeatureFlagsStore()
```

- [ ] **Step 2: Find and wrap group filter section**

Find the group filter section. Run:
```bash
grep -n "selectedGroupId\|group.*filter\|Group.*filter" web/src/pages/HistoryPage.vue | head -10
```

Wrap the group filter row/section with `v-if="featureFlagsStore.groupsEnabled"`.

- [ ] **Step 3: Verify typecheck**

Run: `cd web && pnpm typecheck 2>&1 | grep HistoryPage`

- [ ] **Step 4: Commit**

```bash
git add web/src/pages/HistoryPage.vue
git commit -m "feat(ff): add groupsEnabled visibility to HistoryPage group filter"
```

---

## Task 7: Write E2E tests for feature flags

**Files:**
- Create: `web/e2e/feature-flags.spec.ts`

- [ ] **Step 1: Check existing E2E files**

Run: `ls web/e2e/*.spec.ts | head -5`

- [ ] **Step 2: Write the E2E test file**

```typescript
import { test, expect } from '@playwright/test'

test.describe('Feature Flags', () => {
  test.beforeEach(async ({ page }) => {
    await page.evaluate(() => {
      localStorage.removeItem('ff_groups_enabled')
      localStorage.removeItem('ff_group_schedules_enabled')
    })
    await page.goto('/settings')
  })

  test('trigger dialog by clicking Settings RSS icon 10 times', async ({ page }) => {
    const rssIcon = page.locator('header').locator('svg.h-6.w-6').first()
    for (let i = 0; i < 10; i++) {
      await rssIcon.click()
      await page.waitForTimeout(50)
    }
    await expect(page.locator('text=🔧')).toBeVisible()
  })

  test('cascade cancel — Groups stays ON when Cancel clicked', async ({ page }) => {
    const rssIcon = page.locator('header').locator('svg.h-6.w-6').first()
    for (let i = 0; i < 10; i++) {
      await rssIcon.click()
      await page.waitForTimeout(50)
    }

    // Turn OFF Groups toggle (first toggle button)
    const groupsToggle = page.locator('button.relative.inline-flex.h-6').first()
    await groupsToggle.click()

    // Warning should appear
    await expect(page.locator('text=停用群組功能也將停用排程更新')).toBeVisible()

    // Click Cancel
    await page.locator('button:has-text("取消")').click()

    // Warning should hide, Groups should stay ON
    await expect(page.locator('text=停用群組功能也將停用排程更新')).not.toBeVisible()
  })

  test('cascade confirm — Groups OFF and Schedules auto-disabled', async ({ page }) => {
    const rssIcon = page.locator('header').locator('svg.h-6.w-6').first()
    for (let i = 0; i < 10; i++) {
      await rssIcon.click()
      await page.waitForTimeout(50)
    }

    // Turn OFF Groups toggle
    const groupsToggle = page.locator('button.relative.inline-flex.h-6').first()
    await groupsToggle.click()

    // Click Confirm on warning (first confirm button)
    await page.locator('button:has-text("確認")').first().click()

    // Dialog should close
    await expect(page.locator('text=🔧')).not.toBeVisible()

    // Verify localStorage
    const stored = await page.evaluate(() => ({
      groups: localStorage.getItem('ff_groups_enabled'),
      schedules: localStorage.getItem('ff_group_schedules_enabled')
    }))
    expect(stored.groups).toBe('false')
    expect(stored.schedules).toBe('false')
  })

  test('visibility — Groups tab hidden when groups_enabled is OFF', async ({ page }) => {
    await page.evaluate(() => {
      localStorage.setItem('ff_groups_enabled', 'false')
      localStorage.setItem('ff_group_schedules_enabled', 'false')
    })
    await page.goto('/sources')

    // Groups tab should not be visible
    const groupsTab = page.locator('button', { hasText: 'groups' }).or(page.locator('button', { hasText: '群組' }))
    await expect(groupsTab).not.toBeVisible()
  })

  test('persistence — changes survive page reload', async ({ page }) => {
    const rssIcon = page.locator('header').locator('svg.h-6.w-6').first()
    for (let i = 0; i < 10; i++) {
      await rssIcon.click()
      await page.waitForTimeout(50)
    }

    // Turn OFF Groups
    await page.locator('button.relative.inline-flex.h-6').first().click()
    await page.locator('button:has-text("確認")').first().click()

    // Reload
    await page.reload()
    await page.goto('/sources')

    // Groups tab should still be hidden
    const groupsTab = page.locator('button', { hasText: 'groups' }).or(page.locator('button', { hasText: '群組' }))
    await expect(groupsTab).not.toBeVisible()
  })
})
```

- [ ] **Step 3: Run E2E tests (if test environment is available)**

Run: `cd web && pnpm test:e2e -- --grep "Feature Flags" 2>&1 | head -30`

- [ ] **Step 4: Commit**

```bash
git add web/e2e/feature-flags.spec.ts
git commit -m "test(ff): add E2E tests for feature flags system"
```

---

## Spec Coverage Check

- [x] Store with localStorage persistence — Task 1
- [x] Cascade confirmation flow (Approach A) — Task 3
- [x] Settings page trigger — Task 4
- [x] Groups tab visibility — Task 5
- [x] Group badges visibility — Task 5
- [x] ScheduleConfigPanel visibility — Task 5 (verify in component)
- [x] HistoryPage group filter visibility — Task 6
- [x] i18n keys — Task 2
- [x] E2E tests — Task 7