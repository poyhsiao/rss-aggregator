# Toggle 組件重新設計方案

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 將 Toggle 組件改為 iOS 風格的大尺寸滑塊開關

**Architecture:**
- **iOS-style:** 更大膠囊外觀 (h-11 w-[72px])，圓角 thumb，陰影更深
- 圓潤肥碩的 track，thumb 直徑 40px
- ON/OFF 文字標籤顯示，帶滑入/淡出動畫
- 深度漸層 + inset shadow 營造立體感
- 500ms ease-out 動畫

**Tech Stack:** Vue 3 + TypeScript + Tailwind CSS

---

## Task 1: 建立 iOS-style Switch 組件

**Files:**
- Create: `web/src/components/ui/Switch.vue`
- Modify: `web/src/components/FeatureFlagsDialog.vue` (更新 import)
- Test: `web/src/components/ui/__tests__/Switch.test.ts`

- [ ] **Step 1: 創建 Switch.vue 組件 (iOS-style)**

```vue
<!-- web/src/components/ui/Switch.vue -->
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
    :aria-checked="modelValue"
    :disabled="disabled"
    class="group relative inline-flex h-11 w-[72px] items-center rounded-full transition-all duration-500 ease-out focus:outline-none focus:ring-4 focus:ring-primary-500/30 focus:ring-offset-2"
    :class="[
      modelValue
        ? 'bg-gradient-to-b from-primary-500 to-primary-600 shadow-[inset_0_2px_4px_rgba(0,0,0,0.15),0px_4px_16px_rgba(34,197,94,0.35)]'
        : 'bg-gradient-to-b from-neutral-400 to-neutral-500 shadow-[inset_0_2px_4px_rgba(0,0,0,0.15),0px_4px_12px_rgba(0,0,0,0.2)]',
      disabled && 'opacity-40 cursor-not-allowed'
    ]"
    @click="toggle"
  >
    <!-- Track glow effect when ON -->
    <span
      v-if="modelValue"
      class="absolute inset-0 rounded-full bg-primary-400/20 blur-xl transition-opacity duration-500"
    />

    <!-- Thumb - iOS style: 40px diameter, sits inside track with 5px padding -->
    <span
      class="relative h-10 w-10 rounded-full bg-gradient-to-b from-white to-neutral-100 shadow-[0px_4px_8px_rgba(0,0,0,0.25),0px_2px_4px_rgba(0,0,0,0.15),inset_0px_1px_2px_rgba(255,255,255,1)] transition-all duration-500 ease-out"
      :class="modelValue ? 'translate-x-[38px]' : 'translate-x-[5px]'"
    >
      <!-- Thumb shine/gloss effect -->
      <span class="absolute inset-x-2 top-1.5 h-3 rounded-full bg-gradient-to-b from-white/60 to-transparent opacity-50" />
    </span>

    <!-- OFF label - hidden when ON -->
    <span
      class="absolute left-3 text-[10px] font-semibold tracking-wide text-white/80 transition-all duration-500 ease-out"
      :class="modelValue ? 'opacity-0 -translate-x-2' : 'opacity-100 translate-x-0'"
    >
      OFF
    </span>

    <!-- ON label - visible only when ON -->
    <span
      class="absolute right-3 text-[10px] font-semibold tracking-wide text-white transition-all duration-500 ease-out"
      :class="modelValue ? 'opacity-100 translate-x-0' : 'opacity-0 translate-x-2'"
    >
      ON
    </span>
  </button>
</template>
```

- [ ] **Step 2: 撰寫單元測試**

```typescript
// web/src/components/ui/__tests__/Switch.test.ts
import { mount } from '@vue/test-utils'
import Switch from '../Switch.vue'

describe('Switch', () => {
  it('renders correctly when off', () => {
    const wrapper = mount(Switch, {
      props: { modelValue: false }
    })
    expect(wrapper.attributes('role')).toBe('switch')
    expect(wrapper.attributes('aria-checked')).toBe('false')
  })

  it('renders correctly when on', () => {
    const wrapper = mount(Switch, {
      props: { modelValue: true }
    })
    expect(wrapper.attributes('aria-checked')).toBe('true')
  })

  it('emits update:modelValue when clicked', async () => {
    const wrapper = mount(Switch, {
      props: { modelValue: false }
    })
    await wrapper.trigger('click')
    expect(wrapper.emitted('update:modelValue')).toBeTruthy()
    expect(wrapper.emitted('update:modelValue')[0]).toEqual([true])
  })

  it('does not emit when disabled', async () => {
    const wrapper = mount(Switch, {
      props: { modelValue: false, disabled: true }
    })
    await wrapper.trigger('click')
    expect(wrapper.emitted('update:modelValue')).toBeFalsy()
  })
})
```

- [ ] **Step 3: 運行測試驗證**

Run: `cd web && pnpm test:run src/components/ui/__tests__/Switch.test.ts`
Expected: PASS

- [ ] **Step 4: 更新 FeatureFlagsDialog.vue 的 import**

將 `Toggle` import 替換為 `Switch`:
```typescript
import Switch from '@/components/ui/Switch.vue'
```

並將 template 中所有 `<Toggle` 替換為 `<Switch

- [ ] **Step 5: 提交**

```bash
git add web/src/components/ui/Switch.vue web/src/components/ui/__tests__/Switch.test.ts web/src/components/FeatureFlagsDialog.vue
git commit -m "feat(toggle): replace with iOS-style Switch component"
```

---

## Task 2: E2E 測試驗證

**Files:**
- Modify: `web/e2e/feature-flags-dialog.spec.ts`
- Test: `web/e2e/feature-flags-dialog.spec.ts`

- [ ] **Step 1: 新增 E2E 測試**

```typescript
test('switch has ON/OFF labels visible', async ({ page }) => {
  await page.goto('/')
  await page.getByRole('button', { name: /feature flags/i }).click()
  const switchEl = page.locator('[role="switch"]').first()
  // OFF state - "OFF" label visible
  await expect(switchEl).toContainText('OFF')
  // Click to turn ON
  await switchEl.click()
  // ON state - "ON" label visible
  await expect(switchEl).toContainText('ON')
})
```

- [ ] **Step 2: 運行 E2E 測試**

Run: `cd web && pnpm test:e2e --grep "ON/OFF"`
Expected: PASS

- [ ] **Step 3: 提交**

```bash
git add web/e2e/feature-flags-dialog.spec.ts
git commit -m "test(e2e): add Switch ON/OFF label tests"
```

---

## 5. 預期產出

1. **Switch 組件 (iOS-style)** — 大尺寸膠囊形 toggle，質感升級
   - **Track:** h-11 w-[72px]（44px × 72px），漸層背景 + inset shadow
   - **Thumb:** h-10 w-10（40px 直徑），渐層 + 光澤效果，`translate-x-[38px]`
   - **ON/OFF 標籤：** 文字滑入/淡出動畫，duration-500
   - **陰影：** `shadow-[inset_0_2px_4px_rgba(0,0,0,0.15)]` + 外發光暈
   - **Glow 效果：** ON 時 `bg-primary-400/20 blur-xl` 輝光
   - **動畫：** 500ms ease-out，thumb 滑動更絲滑
2. **單元測試** — 5 個測試案例全部通過
3. **E2E 測試** — ON/OFF 標籤可見性驗證通過
4. **FeatureFlagsDialog** — 使用新的 Switch 組件

---

## 6. 替代方案選項

### Option A: Shadcn-style Switch
- 膠囊形，h-8 w-14，圓角 thumb
- 優點：經典 pattern，SEO 友好
- 缺點：可能太小

### Option B: 雙按鈕樣式
- ON / OFF 兩個按鈕，選中狀態高亮
- 優點：無障礙極佳，點擊直觀
- 缺點：佔用空間較大

### Option C: iOS 風格滑塊 (current spec)
- 更大膠囊 (h-11 w-[72px])，圓角 thumb (40px)，深度漸層陰影
- 優點：觸控友好，視覺效果強烈
- 缺點：佔用空間較大

**Recommendation:** Option C — iOS-style，最大最肥的滑塊開關，觸控友好