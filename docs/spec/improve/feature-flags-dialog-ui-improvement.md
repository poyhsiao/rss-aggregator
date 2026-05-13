# FeatureFlagsDialog UI/UX 改善方案

## 目標
改善 FeatureFlagsDialog 的使用者介面和體驗，解決以下問題：
1. 關閉按鈕（X）難以識別
2. Dialog 內容過於緊湊
3. Toggle 開關不夠明顯
4. 整體呈現不夠友善

---

## 1. Dialog.vue 改善

### 1.1 尺寸調整
- **最大寬度**：從 `max-w-4xl` 調整為 `max-w-3xl`，在中等螢幕上更舒適
- **最小寬度**：從 `min-w-[320px] md:min-w-[400px]` 調整為 `min-w-[380px] md:min-w-[480px]`

### 1.2 Header 區域
- **標題大小**：從 `text-xl` 調整為 `text-2xl`
- **標題粗細**：保持 `font-bold`
- **關閉按鈕**：
  - 尺寸：`p-3`（更大的點擊區域）
  - 圖標：`w-7 h-7`
  - 背景：使用 hover 效果 `hover:bg-neutral-100 dark:hover:bg-neutral-700`
  - 位置：Header 右側，絕對定位

### 1.3 Content 區域
- **Padding**：從 `p-8` 調整為 `p-10`
- **間距**：卡片間距從 `space-y-6` 調整為 `space-y-8`

### 1.4 Footer 區域
- **Padding**：從 `py-5` 調整為 `py-6`
- **按鈕**：Confirm 按鈕 `min-w-[200px] px-10 py-3.5`

---

## 2. FeatureFlagsDialog.vue 改善

### 2.1 關閉按鈕（最關鍵）
```vue
<!-- Header 內的關閉按鈕 -->
<button
  type="button"
  class="absolute right-0 top-0 p-4 rounded-tr-2xl text-neutral-400 hover:text-neutral-700 hover:bg-neutral-50 dark:hover:text-neutral-200 dark:hover:bg-neutral-700/50 transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-primary-500 rounded-bl-lg"
  @click="handleClose"
  title="關閉"
>
  <svg class="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M6 18L18 6M6 6l12 12" />
  </svg>
</button>
```

**改善重點**：
- 使用 `absolute` 定位在右上角
- 更大的 padding `p-4`
- 更大的圖標 `w-7 h-7`
- 清晰的 hover 效果
- `rounded-tr-2xl` 配合 Dialog 的圓角

### 2.2 Feature 卡片設計

#### Groups Feature 卡片
```vue
<div class="relative flex items-start justify-between gap-8 p-6 rounded-2xl bg-gradient-to-br from-primary-50 to-primary-100/50 dark:from-primary-900/30 dark:to-primary-800/20 border border-primary-200 dark:border-primary-800 shadow-sm">
  <!-- 左側：圖標和文字 -->
  <div class="flex items-start gap-4">
    <div class="flex-shrink-0 w-14 h-14 rounded-2xl bg-primary-500/10 dark:bg-primary-500/20 flex items-center justify-center">
      <span class="text-3xl">👥</span>
    </div>
    <div class="flex-1 min-w-0 pt-2">
      <div class="text-lg font-bold text-neutral-900 dark:text-neutral-100 mb-2">
        {{ t('featureFlags.groupsEnabled') }}
      </div>
      <div class="text-sm text-neutral-500 dark:text-neutral-400 leading-relaxed">
        {{ t('featureFlags.groupsEnabledDesc') }}
      </div>
    </div>
  </div>
  
  <!-- 右側：Toggle -->
  <div class="flex-shrink-0 pt-2">
    <Toggle v-model="localGroupsEnabled" />
  </div>
</div>
```

#### Schedules Feature 卡片（當 Groups 關閉時）
```vue
<div 
  class="relative flex items-start justify-between gap-8 p-6 rounded-2xl border-2 border-dashed transition-all duration-300"
  :class="localGroupsEnabled 
    ? 'bg-gradient-to-br from-primary-50 to-primary-100/50 dark:from-primary-900/30 dark:to-primary-800/20 border-primary-200 dark:border-primary-800' 
    : 'bg-neutral-100/50 dark:bg-neutral-800/50 border-neutral-300 dark:border-neutral-600 opacity-60'"
>
  <!-- 當禁用時顯示提示 -->
  <div v-if="!localGroupsEnabled" class="absolute inset-0 flex items-center justify-center">
    <div class="text-sm text-neutral-400 dark:text-neutral-500 font-medium">
      {{ t('featureFlags.schedulesDisabledHint') }}
    </div>
  </div>
  
  <!-- 當啟用時正常顯示內容 -->
  <template v-else>
    <!-- 內容與 Groups 卡片類似 -->
  </template>
</div>
```

### 2.3 Toggle 開關設計（新建 Toggle.vue 元件）

```vue
<!-- components/ui/Toggle.vue -->
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
    class="relative inline-flex h-10 w-18 items-center rounded-full transition-all duration-300 focus:outline-none focus:ring-4 focus:ring-primary-500/30 focus:ring-offset-2"
    :class="[
      modelValue ? 'bg-primary-600 shadow-lg shadow-primary-500/40' : 'bg-neutral-300 dark:bg-neutral-600',
      disabled && 'opacity-50 cursor-not-allowed'
    ]"
    :disabled="disabled"
    @click="toggle"
  >
    <span
      class="inline-block h-8 w-8 transform rounded-full bg-white shadow-lg transition-transform duration-300"
      :class="modelValue ? 'translate-x-9' : 'translate-x-1'"
    />
  </button>
</template>
```

**尺寸**：
- 外框：`h-10 w-18`（高度 40px，寬度 72px）
- 內部圓球：`h-8 w-8`（直徑 32px）
- 位移：`translate-x-9` 或 `translate-x-1`

### 2.4 Cascade Warning 警告框

```vue
<div
  v-if="showCascadeWarning"
  class="p-6 rounded-2xl border-2 border-amber-400 dark:border-amber-500 bg-gradient-to-br from-amber-50 to-orange-50 dark:from-amber-950/50 dark:to-orange-950/50 shadow-lg"
>
  <div class="flex items-start gap-5">
    <div class="flex-shrink-0 w-12 h-12 rounded-full bg-amber-100 dark:bg-amber-900/50 flex items-center justify-center">
      <span class="text-2xl">⚠️</span>
    </div>
    <div class="flex-1 min-w-0">
      <div class="text-base font-bold text-amber-900 dark:text-amber-100 mb-3">
        {{ t('featureFlags.cascadeWarningTitle') }}
      </div>
      <div class="flex gap-4">
        <button
          type="button"
          class="px-6 py-3 text-sm font-semibold rounded-xl bg-amber-600 hover:bg-amber-700 text-white shadow-lg shadow-amber-500/30 transition-all focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2"
          @click="handleCascadeConfirm"
        >
          {{ t('featureFlags.cascadeWarningConfirm') }}
        </button>
        <button
          type="button"
          class="px-6 py-3 text-sm font-semibold rounded-xl bg-neutral-200 hover:bg-neutral-300 dark:bg-neutral-700 dark:hover:bg-neutral-600 text-neutral-700 dark:text-neutral-200 transition-all focus:outline-none focus:ring-2 focus:ring-neutral-400 focus:ring-offset-2"
          @click="handleCascadeCancel"
        >
          {{ t('featureFlags.cascadeWarningCancel') }}
        </button>
      </div>
    </div>
  </div>
</div>
```

### 2.5 Confirm 按鈕

```vue
<div class="flex justify-center pt-6 pb-2">
  <button
    type="button"
    class="min-w-[200px] px-10 py-3.5 text-base font-bold rounded-xl bg-primary-600 hover:bg-primary-700 text-white shadow-lg shadow-primary-500/30 transition-all duration-200 focus:outline-none focus:ring-4 focus:ring-primary-500/30 focus:ring-offset-2"
    @click="handleConfirm"
  >
    {{ t('featureFlags.confirm') }}
  </button>
</div>
```

---

## 3. 預期效果

### 3.1 關閉按鈕
- **位置**：右上角，絕對定位
- **尺寸**：48x48px 點擊區域，28x28px 圖標
- **顏色**：平時 `text-neutral-400`，hover 時 `text-neutral-700`
- **背景**：hover 時顯示淺灰色背景

### 3.2 Dialog 尺寸
- 最大寬度：`max-w-3xl`（約 768px）
- 最小寬度：380px（mobile）/ 480px（desktop）
- 內容區域 padding：40px
- 卡片間距：32px

### 3.3 Toggle 開關
- 外框：40px 高 × 72px 寬
- 圓球：32px 直徑
- 開啟時：Primary 顏色 + 陰影
- 關閉時：中性灰顏色

### 3.4 Feature 卡片
- Padding：24px
- 圓角：16px
- 背景：漸層效果
- 圖標：56x56px 圓角方塊

---

## 4. 受影響的檔案

| 檔案 | 改動類型 |
|------|----------|
| `web/src/components/ui/Dialog.vue` | 修改 |
| `web/src/components/ui/Toggle.vue` | 新建 |
| `web/src/components/FeatureFlagsDialog.vue` | 重寫 |
| `web/src/components/FeatureFlagsDialog.vue`（i18n） | 修改（如果需要） |

---

## 5. 驗證方式

### 5.1 手動測試
1. 在設定頁面，連續點擊左上角 RSS icon 10 次
2. 確認 FeatureFlagsDialog 正確開啟
3. 確認關閉按鈕（X）在右上角清晰可見
4. 確認 Toggle 開關可以正常操作
5. 確認 Cascade Warning 正確顯示

### 5.2 E2E 測試
- 更新 `web/e2e/feature-flags.spec.ts`
- 新增測試：驗證關閉按鈕可見性和點擊
- 新增測試：驗證 Dialog 尺寸和響應式設計
- 新增測試：驗證 Toggle 開關的視覺效果
