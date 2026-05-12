# Feature Toggle Panel — 設計規格

**版本：** 1.0
**日期：** 2026-05-12
**基於：** `docs/spec/improve/feature-toggle-panel.md`

---

## 1. 概述

隱藏控制面板，透過在 **Settings 頁面** RSS 圖示上 **10 次點擊（3 秒內）** 喚醒。用戶可切換三個功能開關，狀態持久化到資料庫。

| Toggle Key | 行為 |
|------------|------|
| `group_visibility` | 隱藏 Sources 頁面群組側邊欄（含 badge） |
| `timer` | 停用背景排程 feed 抓取（scheduler） |
| `share_link` | 隱藏文章分享/複製連結按鈕及相關 badge |

**與現有 DebugDialog 的關係：** DebugDialog（Feed 頁面 10 點擊）與 FeatureTogglePanel（Settings 頁面 10 點擊）獨立存在，不干擾。

---

## 2. 後端架構

### 2.1 資料模型

**表格：** `feature_toggles`

| 欄位 | 類型 | 約束 |
|------|------|------|
| `id` | Integer | PK, autoincrement |
| `user_id` | String(64) | nullable, index |
| `session_id` | String(128) | nullable, index |
| `toggle_key` | String(64) | NOT NULL |
| `enabled` | Boolean | NOT NULL, default=False |
| `created_at` | DateTime | NOT NULL (UTC) |
| `updated_at` | DateTime | NOT NULL (UTC) |

**唯一約束：** `(user_id, session_id, toggle_key)`

**身份識別：** 已登入用 `user_id`，匿名用 `session_id`。

### 2.2 API 端點

| Method | Path | 描述 |
|--------|------|------|
| `GET` | `/api/feature-toggles` | 取所有 toggles |
| `PATCH` | `/api/feature-toggles/{toggle_key}` | 更新單一 toggle |

**GET /api/feature-toggles**
- 回傳：`{ "toggles": [{ "key": "...", "enabled": true/false }, ...] }`
- 身份識別邏輯：已登入查 `user_id`，匿名查 `session_id`
- 缺少的 key 預設 `enabled: false`

**PATCH /api/feature-toggles/{toggle_key}**
- Body：`{ "enabled": true }`
- 回傳：`{ "key": "...", "enabled": true }`
- 無效 key 回傳 404

### 2.3 檔案結構

| 檔案 | 用途 |
|------|------|
| `src/models/feature_toggle.py` | ORM model |
| `src/schemas/feature_toggle.py` | Pydantic schemas |
| `src/services/feature_toggle_service.py` | 商業邏輯 |
| `src/api/routes/feature_toggles.py` | FastAPI routes |
| `alembic/versions/xxxx_add_feature_toggles.py` | 資料庫遷移 |

---

## 3. 前端架構

### 3.1 檔案結構

| 檔案 | 用途 |
|------|------|
| `web/src/api/feature-toggles.ts` | API client |
| `web/src/composables/useFeatureToggle.ts` | 點擊計數 + 面板可見性 + API |
| `web/src/components/FeatureTogglePanel.vue` | 面板 UI |
| `web/src/pages/SettingsPage.vue` | 整合點擊處理 + 面板掛載 |

### 3.2 useFeatureToggle Composable

```typescript
function useFeatureToggle(): {
  clickCount: Ref<number>
  isRevealed: Ref<boolean>
  toggles: Ref<FeatureToggle[]>
  isLoading: Ref<boolean>
  error: Ref<string | null>
  handleIconClick: () => void
  toggleFeature: (key: string, enabled: boolean) => Promise<void>
}
```

**點擊計數邏輯：**
- 每次 `handleIconClick()` 計數 +1
- 之後重置 3 秒 timeout
- 10 次內喚醒 `isRevealed = true`
- 未達 10 次則 timeout 後歸零

### 3.3 FeatureTogglePanel UI

```
┌──────────────────────────────────────────┐
│ Feature Toggles                     [X]  │
├──────────────────────────────────────────┤
│  Group Visibility          [ Toggle ON ] │
│  Scheduled Updates         [ Toggle OFF] │
│  Share Link                [ Toggle ON ] │
└──────────────────────────────────────────┘
```

- 位置：Settings 頁面 header RSS 圖示下方
- 支援 Dark mode
- i18n 翻譯僅顯示譯文（無 key 前綴）

### 3.4 Toggle 行為綁定

| Toggle | 隱藏目標 |
|--------|----------|
| `group_visibility` | Sources 頁面群組側邊欄（含群組 badge） |
| `timer` | Scheduler 啟動條件：`timer === true` |
| `share_link` | 文章頁 share button + badge |

---

## 4. 測試策略

### 4.1 TDD 單元測試

**後端（`tests/test_feature_toggles.py`）：**
- `test_feature_toggle_repo_upsert_insert` — 首次 upsert 插入
- `test_feature_toggle_repo_upsert_update` — 第二次 upsert 更新
- `test_feature_toggle_service_get_all_defaults` — 缺少的 key 回傳 false
- `test_feature_toggle_endpoint_get` — GET 回傳 3 個 toggles
- `test_feature_toggle_endpoint_patch_valid` — PATCH 更新並回傳
- `test_feature_toggle_endpoint_patch_invalid_key` — 無效 key 回傳 404

**前端（`web/src/__tests__/useFeatureToggle.test.ts`）：**
- `clickCount increments on handleIconClick`
- `counter resets after 3s of inactivity`
- `isRevealed becomes true after 10 clicks`
- `API get called on init`
- `PATCH called when toggleFeature invoked`

### 4.2 BDD E2E 測試（Playwright）

檔案：`web/e2e/feature-toggles.spec.ts`

| 情境 | 步驟 |
|------|------|
| `panel hidden by default` | 導航到 Settings，確認面板未顯示 |
| `reveal panel by 10 taps` | 3 秒內點擊 RSS 圖示 10 次，確認面板顯示 |
| `toggle persists after reload` | 開啟某 toggle，刷新頁面，確認仍開啟 |
| `timeout resets counter` | 點擊 5 次後等待 4 秒，再點擊 5 次，確認面板未喚醒 |

---

## 5. 實作順序

1. 寫 TDD 單元測試（全部失敗）
2. 寫 BDD E2E 測試（全部失敗）
3. 實作後端：model、migration、service、routes
4. 實作前端：composable、component、page 整合
5. 執行全測試套件，確認全部通過

---

## 6. 驗收標準

- [ ] 10 次點擊（3 秒內）喚醒面板
- [ ] 3 秒無活動計數歸零
- [ ] 三個 Toggle 標籤正確
- [ ] Toggle 變更呼叫 API 並寫入資料庫
- [ ] 刷新後 Toggle 狀態保持
- [ ] 現有 DebugDialog 不受影響
- [ ] i18n 僅顯示譯文（無 key 前綴）
- [ ] 所有 TDD 單元測試通過
- [ ] 所有 BDD E2E 測試通過
