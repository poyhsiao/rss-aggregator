# Feature Flags Dialog 修復規格

> 日期：2026-05-13
> 狀態：待審查

---

## 1. 問題概述

當前 FeatureFlagsDialog 存在以下 4 個問題需要修復：

| # | 問題 | 嚴重性 |
|---|------|--------|
| 1 | `featureFlags.sourceGroupSchedulesEnabled` 及其描述缺少 i18n 翻譯 | 高 |
| 2 | Toggle 元件樣式異常 — 寬度 `w-18` 無效，且左右切換位置計算錯誤 | 高 |
| 3 | 當 `groupsEnabled` 關閉時，FeedPage 的群組過濾 badges 未同步隱藏 | 中 |
| 4 | Cascade warning 邏輯錯誤 — 取消時不應同步 store，且確認行為不符合預期 | 中 |

---

## 2. 修復細節

### 2.1 i18n 翻譯缺失

**問題：** `sourceGroupSchedulesEnabled` 和 `sourceGroupSchedulesEnabledDesc` 未定義於 locale 檔案中。

**修復：** 在 `web/src/locales/en.json` 和 `web/src/locales/zh.json` 的 `featureFlags` 區塊新增：

```json
{
  "sourceGroupSchedulesEnabled": "Source Group Schedules",
  "sourceGroupSchedulesEnabledDesc": "Enable/disable scheduled updates for source groups"
}
```

**影響檔案：**
- `web/src/locales/en.json`
- `web/src/locales/zh.json`

---

### 2.2 Toggle 元件樣式修復

**問題：** `web/src/components/ui/Toggle.vue` 中使用了 `w-18` (非標準 Tailwind 尺寸)，且 `translate-x-9` / `translate-x-1` 的值與實際按鈕尺寸不匹配，導致滑塊位置異常。

**現況分析：**
- 按鈕高度 `h-10` (2.5rem = 40px)
- 內部圓球高度 `h-8` (2rem = 32px)
- 滑塊 translate 值 `translate-x-9` (2.25rem) 和 `translate-x-1` (0.25rem)

**正確邏輯：**
- 當 `modelValue=false` (關閉)：滑塊應在最左側，預設 padding 為 4px (0.25rem)
- 當 `modelValue=true` (開啟)：滑塊應在最右側

**計算：**
- 容器寬度：36px (使用 Tailwind `w-9` = 2.25rem)
- 圓球直徑：32px (h-8 = 2rem)
- 關閉時 translate：`(40 - 32) / 2 = 4px` = `translate-x-1`
- 開啟時 translate：`36 - 32 - 4 = 0px` = `translate-x-0`

**修復方案：** 將 Toggle 改為標準寬度，使用 `w-9 h-10`，並修正 translate 值：

```vue
<template>
  <button
    type="button"
    role="switch"
    class="relative inline-flex h-10 w-9 items-center rounded-full transition-all duration-300 ..."
  >
    <span
      class="inline-block h-8 w-8 transform rounded-full bg-white shadow-lg transition-transform duration-300"
      :class="modelValue ? 'translate-x-0' : 'translate-x-1'"
    />
  </button>
</template>
```

**影響檔案：**
- `web/src/components/ui/Toggle.vue`

---

### 2.3 FeedPage 群組過濾響應 Feature Flag

**問題：** 當 `featureFlagsStore.groupsEnabled` 為 `false` 時，FeedPage 的群組過濾 chips 未隱藏。

**現況：** FeedPage.vue 第 157 行：
```vue
<div v-if="groups.length > 0" class="flex flex-wrap gap-2">
```

**修復：** 加入 `featureFlagsStore.groupsEnabled` 條件：
```vue
<div v-if="featureFlagsStore.groupsEnabled && groups.length > 0" class="flex flex-wrap gap-2">
```

**影響檔案：**
- `web/src/pages/FeedPage.vue` (第 157 行)

---

### 2.4 Cascade Warning 邏輯修正

**問題：** 當前邏輯混亂：
1. 點擊 Groups Toggle 關閉時，直接改變 `localGroupsEnabled`，但未同步 store
2. 點擊 cascade warning 的「取消」時，`handleCascadeCancel` 將 `localGroupsEnabled = true`，但此時 `store.groupsEnabled` 仍為 `true`（從未改過），造成邏輯不一致
3. 點擊 cascade warning 的「確認」時，會同步關閉 groups + schedules + sourceGroupSchedules，但用戶期望是「只停用排程更新」，群組功能應保留

**正確行為：**

| 動作 | 結果 |
|------|------|
| 用戶關閉 Groups Toggle | 彈出 cascade warning dialog，詢問：「關閉群組功能也將停用排程更新，確認？」 |
| 用戶點擊「確認」 | 同步關閉 groupsEnabled + groupSchedulesEnabled + sourceGroupSchedulesEnabled，儲存並關閉 dialog |
| 用戶點擊「取消」 | 恢復 Groups Toggle 為 ON (true)，不儲存任何變更，dialog 保持開啟 |

**修正後的 handleGroupsToggle：**

```typescript
function handleGroupsToggle(val: boolean) {
  if (val) {
    // 開啟群組 — 直接生效，不需詢問
    localGroupsEnabled.value = val
    showCascadeWarning.value = false
  } else {
    // 關閉群組 — 檢查排程是否啟用
    if (store.groupSchedulesEnabled || store.sourceGroupSchedulesEnabled) {
      // 有排程啟用 — 先不變更 local 值，彈出 warning
      localGroupsEnabled.value = val  // 預覽即將關閉
      showCascadeWarning.value = true
    } else {
      // 無排程啟用 — 直接關閉
      localGroupsEnabled.value = val
      showCascadeWarning.value = false
    }
  }
}
```

**修正後的 handleCascadeConfirm：**

```typescript
function handleCascadeConfirm() {
  // 確認關閉群組時，一併停用排程（但不改 store，只修改 local 值）
  localSchedulesEnabled.value = false
  localSourceGroupSchedulesEnabled.value = false
  showCascadeWarning.value = false
  // 不自動關閉 dialog，讓用戶確認後再按「確認」儲存
}
```

**修正後的 handleCascadeCancel：**

```typescript
function handleCascadeCancel() {
  // 恢復群組為 ON，不改變排程（因為從未變過）
  localGroupsEnabled.value = true
  showCascadeWarning.value = false
  // 不改 localSchedulesEnabled / localSourceGroupSchedulesEnabled
}
```

**修正後的 handleConfirm：**

```typescript
function handleConfirm() {
  store.groupsEnabled = localGroupsEnabled.value
  store.groupSchedulesEnabled = localSchedulesEnabled.value
  store.sourceGroupSchedulesEnabled = localSourceGroupSchedulesEnabled.value
  emit('update:open', false)
}
```

**影響檔案：**
- `web/src/components/FeatureFlagsDialog.vue` (第 31-73 行)

---

## 3. 預期結果

修復後：

1. **所有 Toggle 正常顯示** — 標準尺寸，左右切換動畫流暢
2. **所有 i18n 文字正常顯示** — 無論 en/zh locale
3. **群組過濾 chips** — 當 `groupsEnabled=false` 時自動隱藏
4. **Cascade Warning Dialog** — 邏輯正確：
   - 關閉群組時詢問確認
   - 確認後預覽排程關閉，但需再按「確認」才實際儲存
   - 取消時恢復原本狀態

---

## 4. 測試驗證

### 手動測試案例

| # | 操作 | 預期結果 |
|---|------|----------|
| T1 | 開啟 FeatureFlagsDialog，檢查所有三個 toggle 的標題和描述是否正確翻譯 | 所有文字正確顯示 |
| T2 | 點擊 Groups Toggle 關閉（排程皆啟用） | 彈出 cascade warning |
| T3 | 在 cascade warning 中點擊「取消」 | Groups Toggle 恢復 ON，排程保持原狀 |
| T4 | 在 cascade warning 中點擊「確認」 | Groups + Schedules 皆預覽為 OFF，再按「確認」才儲存 |
| T5 | 在 FeedPage，關閉 groupsEnabled，回 FeedPage | 群組過濾 chips 已隱藏 |
| T6 | Toggle 左右切換動畫是否流暢 | 滑塊左右移動平滑 |

---

## 5. 檔案變更清單

| 檔案 | 變更類型 |
|------|----------|
| `web/src/locales/en.json` | 修改 — 新增 `sourceGroupSchedulesEnabled` 翻譯 |
| `web/src/locales/zh.json` | 修改 — 新增 `sourceGroupSchedulesEnabled` 翻譯 |
| `web/src/components/ui/Toggle.vue` | 修改 — 修正寬度和 translate 值 |
| `web/src/pages/FeedPage.vue` | 修改 — 加入 `featureFlagsStore.groupsEnabled` 條件 |
| `web/src/components/FeatureFlagsDialog.vue` | 修改 — 修正 cascade warning 邏輯 |