# FeatureFlagsDialog UI/UX 改進計劃

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 改進 FeatureFlagsDialog 的 3 個 UI/UX 問題：卡片寬度、Toggle 呈現、與 Cascade Warning 改為獨立 Dialog

**Architecture:**
- Toggle 組件改用更大、更清晰的自定義樣式，取代目前的窄小滑塊
- FeatureFlagsDialog 內的卡片加入左右 margin，縮減視覺寬度
- Cascade Warning 從 inline 提示改為 ConfirmDialog 獨立彈窗

**Tech Stack:** Vue 3 + TypeScript + Tailwind CSS + Playwright E2E

---

## Task 1: Toggle 組件視覺改進

**Files:**
- Modify: `web/src/components/ui/Switch.vue`
- Test: `web/e2e/feature-flags-dialog.spec.ts`

- [ ] **Step 1: Write E2E test for toggle visibility**

```typescript
// web/e2e/feature-flags-dialog.spec.ts
test('toggle has clear on/off visual distinction', async ({ page }) => {
  await page.goto('/')
  await page.getByRole('button', { name: /feature flags/i }).click()
  const toggle = page.locator('[role="switch"]').first()
  // OFF state - knob should be left, track should be neutral
  await expect(toggle).toHaveClass(/bg-neutral-300/)
  // Click to turn ON
  await toggle.click()
  // ON state - knob right, track primary colored
  await expect(toggle).toHaveClass(/bg-primary-600/)
})
```

- [ ] **Step 2: Run test to verify current toggle passes basic state**

Run: `cd web && pnpm test:e2e --grep "toggle has clear"`
Expected: PASS (existing toggle already has bg change)

- [ ] **Step 3: Modify Toggle.vue for horizontal capsule style**

```vue
<!-- web/src/components/ui/Toggle.vue -->
<script setup lang="ts">
const props = defineProps<{
  modelValue: boolean
  disabled?: boolean
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
}>()

function toggle() {
  if (!props.disabled) {
    emit('update:modelValue', !props.modelValue)
  }
}
</script>

<template>
  <button
    type="button"
    role="switch"
    class="relative inline-flex h-8 w-16 items-center rounded-full transition-all duration-300 focus:outline-none focus:ring-4 focus:ring-primary-500/30 focus:ring-offset-2"
    :class="[
      modelValue
        ? 'bg-primary-600 shadow-lg shadow-primary-500/40'
        : 'bg-neutral-300 dark:bg-neutral-600',
      disabled && 'opacity-50 cursor-not-allowed'
    ]"
    :disabled="disabled"
    :aria-checked="modelValue"
    @click="toggle"
  >
    <!-- OFF label (visible when OFF) -->
    <span
      class="absolute left-2 text-xs font-semibold text-white/70 transition-opacity duration-300"
      :class="modelValue ? 'opacity-0' : 'opacity-100'"
    >
      OFF
    </span>
    <!-- ON label (visible when ON) -->
    <span
      class="absolute right-2 text-xs font-semibold text-white transition-opacity duration-300"
      :class="modelValue ? 'opacity-100' : 'opacity-0'"
    >
      ON
    </span>
    <!-- Knob - slides left (OFF) or right (ON) -->
    <span
      class="inline-block h-6 w-6 transform rounded-full bg-white shadow-md transition-transform duration-300"
      :class="modelValue ? 'translate-x-8' : 'translate-x-1'"
    />
  </button>
</template>
```

- [ ] **Step 4: Run E2E test to verify toggle improvement**

Run: `cd web && pnpm test:e2e --grep "toggle has clear"`
Expected: PASS with visible ON/OFF labels, horizontal capsule shape

- [ ] **Step 5: Run unit tests for Toggle**

Run: `cd web && pnpm test:run src/components/ui/Toggle.test.ts`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add web/src/components/ui/Toggle.vue web/e2e/feature-flags-dialog.spec.ts
git commit -m "feat(toggle): horizontal capsule style with ON/OFF labels"
```

---

## Task 2: FeatureFlagsDialog 卡片寬度調整

**Files:**
- Modify: `web/src/components/FeatureFlagsDialog.vue`
- Test: `web/e2e/feature-flags-dialog.spec.ts`

- [ ] **Step 1: Write E2E test for card width**

```typescript
test('feature flag cards have proper horizontal margin', async ({ page }) => {
  await page.goto('/')
  await page.getByRole('button', { name: /feature flags/i }).click()
  const cards = page.locator('.space-y-3 > div')
  const firstCard = cards.first()
  const dialog = page.locator('[role="dialog"]')
  const dialogBox = dialog.locator('[class*="max-w"]')
  // Cards should not touch dialog edges - get bounding boxes
  const cardBox = await firstCard.boundingBox()
  const dialogBoxInfo = await dialogBox.boundingBox()
  // Card width should be narrower than dialog by at least 16px margin
  expect(cardBox.width).toBeLessThan(dialogBoxInfo.width - 32)
})
```

- [ ] **Step 2: Run test to verify current cards are too wide**

Run: `cd web && pnpm test:e2e --grep "card width"`
Expected: FAIL (cards currently span full dialog width)

- [ ] **Step 3: Modify FeatureFlagsDialog.vue - wrap content with horizontal padding**

Add `px-2` to the container div:

```vue
<div class="px-2 space-y-3">
  <!-- All the toggle cards -->
</div>
```

- [ ] **Step 4: Run E2E test to verify card width**

Run: `cd web && pnpm test:e2e --grep "card width"`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add web/src/components/FeatureFlagsDialog.vue
git commit -m "fix(feature-flags): add horizontal padding to card container"
```

---

## Task 3: Cascade Warning 改為獨立 ConfirmDialog

**Files:**
- Modify: `web/src/components/FeatureFlagsDialog.vue`
- Create: `web/src/components/ui/CascadeWarningDialog.vue` (new component)
- Test: `web/e2e/feature-flags-dialog.spec.ts`

- [ ] **Step 1: Write E2E tests for cascade warning dialog behavior**

```typescript
test('disabling groups with active schedules shows confirm dialog', async ({ page }) => {
  await page.goto('/')
  await page.getByRole('button', { name: /feature flags/i }).click()
  const groupsToggle = page.locator('[role="switch"]').first()
  const groupsToggleChecked = await groupsToggle.getAttribute('aria-checked')
  if (groupsToggleChecked === 'false') {
    await groupsToggle.click()
  }
  await groupsToggle.click()
  const confirmDialog = page.getByRole('dialog')
  await expect(confirmDialog).toBeVisible()
  await expect(confirmDialog).toContainText(/disable.*schedules/i)
})

test('cascade warning cancel restores groups to ON', async ({ page }) => {
  await page.goto('/')
  await page.getByRole('button', { name: /feature flags/i }).click()
  const groupsToggle = page.locator('[role="switch"]').first()
  await groupsToggle.click()
  await page.getByRole('button', { name: /cancel/i }).last().click()
  await expect(groupsToggle).toHaveAttribute('aria-checked', 'true')
})

test('cascade warning confirm previews schedule disabled', async ({ page }) => {
  await page.goto('/')
  await page.getByRole('button', { name: /feature flags/i }).click()
  const groupsToggle = page.locator('[role="switch"]').first()
  await groupsToggle.click()
  await page.getByRole('button', { name: /confirm/i }).first().click()
  const scheduleToggle = page.locator('[role="switch"]').nth(1)
  await expect(scheduleToggle).toHaveAttribute('aria-checked', 'false')
})
```

- [ ] **Step 2: Run tests - expect all to FAIL**

Run: `cd web && pnpm test:e2e --grep "cascade"`
Expected: FAIL (no CascadeWarningDialog component yet, warning is inline)

- [ ] **Step 3: Create CascadeWarningDialog component**

```vue
<!-- web/src/components/ui/CascadeWarningDialog.vue -->
<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import { AlertTriangle } from 'lucide-vue-next'
import Dialog from '@/components/ui/Dialog.vue'
import Button from '@/components/ui/Button.vue'

const { t } = useI18n()

defineProps<{
  open: boolean
}>()

const emit = defineEmits<{
  (e: 'update:open', value: boolean): void
  (e: 'confirm'): void
  (e: 'cancel'): void
}>()

function handleConfirm() {
  emit('confirm')
}

function handleCancel() {
  emit('cancel')
}

function handleClose() {
  emit('update:open', false)
}
</script>

<template>
  <Dialog :open="open" size="sm" @update:open="handleClose">
    <template #header>
      <div class="flex items-center gap-2 text-lg font-semibold text-amber-800 dark:text-amber-200">
        <AlertTriangle class="h-5 w-5" />
        <span>{{ t('featureFlags.cascadeWarningTitle') }}</span>
      </div>
    </template>

    <div class="py-4">
      <p class="text-sm text-neutral-600 dark:text-neutral-300">
        {{ t('featureFlags.cascadeWarningMessage') }}
      </p>
    </div>

    <template #footer>
      <div class="flex justify-end gap-2">
        <Button variant="outline" @click="handleCancel">
          {{ t('featureFlags.cascadeWarningCancel') }}
        </Button>
        <Button variant="default" @click="handleConfirm">
          {{ t('featureFlags.cascadeWarningConfirm') }}
        </Button>
      </div>
    </template>
  </Dialog>
</template>
```

- [ ] **Step 4: Add i18n keys for cascade warning message**

```json
// web/src/locales/en.json
{
  "featureFlags": {
    "cascadeWarningMessage": "Disabling groups will also disable schedule updates. Groups can be re-enabled anytime, but schedules will need to be manually re-enabled. Continue?",
    ...
  }
}

// web/src/locales/zh.json
{
  "featureFlags": {
    "cascadeWarningMessage": "停用群組功能將同時停用排程更新。群組功能可隨時重新啟用，但排程需要手動重新啟用。是否繼續？",
    ...
  }
}
```

- [ ] **Step 5: Modify FeatureFlagsDialog.vue to use cascade dialog**

```vue
<script setup lang="ts">
// Add new import
import CascadeWarningDialog from '@/components/ui/CascadeWarningDialog.vue'

// Replace inline cascade warning div with:
<CascadeWarningDialog
  :open="showCascadeWarning"
  @update:open="showCascadeWarning = $event"
  @confirm="handleCascadeConfirm"
  @cancel="handleCascadeCancel"
/>
```

And update the functions:

```typescript
function handleCascadeConfirm() {
  localSchedulesEnabled.value = false
  localSourceGroupSchedulesEnabled.value = false
  showCascadeWarning.value = false
}

function handleCascadeCancel() {
  localGroupsEnabled.value = true
  showCascadeWarning.value = false
}
```

- [ ] **Step 6: Run E2E tests to verify cascade dialog behavior**

Run: `cd web && pnpm test:e2e --grep "cascade"`
Expected: PASS (all 3 cascade tests)

- [ ] **Step 7: Commit**

```bash
git add web/src/components/ui/CascadeWarningDialog.vue web/src/components/FeatureFlagsDialog.vue web/src/locales/en.json web/src/locales/zh.json web/e2e/feature-flags-dialog.spec.ts
git commit -m "feat(feature-flags): convert cascade warning to separate ConfirmDialog"
```

---

## Task 4: 整合測試與驗證

**Files:**
- Test: `web/e2e/feature-flags-dialog.spec.ts`

- [ ] **Step 1: Run full E2E test suite for feature flags dialog**

Run: `cd web && pnpm test:e2e --grep "feature flag|toggle|cascade"`
Expected: All PASS

- [ ] **Step 2: Run unit tests**

Run: `cd web && pnpm test:run`
Expected: All PASS

- [ ] **Step 3: Verify frontend builds**

Run: `cd web && pnpm build`
Expected: Built successfully

- [ ] **Step 4: Docker rebuild and deploy**

Run: `cd <repo-root> && docker compose --profile full build && docker compose --profile full up -d`
Expected: All containers healthy

- [ ] **Step 5: Final manual verification**

| Check | Expected Result |
|-------|-----------------|
| Toggle ON state | Shows "ON" label on right, blue track, knob on right |
| Toggle OFF state | Shows "OFF" label on left, gray track, knob on left |
| Toggle shape | Horizontal capsule (w-16 x h-8), not square/round |
| Card width | Cards narrower than dialog, ~16px margin |
| Cascade warning | Separate dialog appears, not inline |
| Cancel cascade | Groups returns to ON |
| Confirm cascade | Schedules preview OFF, dialog closes |

---

## 5. 檔案變更清單

| 檔案 | 變更類型 |
|------|----------|
| `web/src/components/ui/Switch.vue` | 修改 — 改為橫向膠囊形（w-16×h-8）、新增 OFF/ON 標籤 |
| `web/src/components/ui/CascadeWarningDialog.vue` | 新增 — 獨立確認 Dialog |
| `web/src/components/FeatureFlagsDialog.vue` | 修改 — 移除 inline warning、使用 cascade dialog、加入 padding |
| `web/src/locales/en.json` | 修改 — 新增 cascadeWarningMessage |
| `web/src/locales/zh.json` | 修改 — 新增 cascadeWarningMessage |
| `web/e2e/feature-flags-dialog.spec.ts` | 新增/修改 — E2E 測試 |

---

## 6. 預期產出

1. Toggle 改為橫向膠囊形（16 寬 x 8 高），左右有 OFF/ON 文字標示，滑塊左右滑動
2. Feature Flags Dialog 內的卡片有左右 margin，不會太寬
3. 停用群組時跳出獨立 ConfirmDialog，詢問用戶確認
4. 所有測試通過（單元測試 + E2E 測試）
5. Docker images 更新並驗證正常運作