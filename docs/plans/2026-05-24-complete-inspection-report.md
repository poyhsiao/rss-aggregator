# RSS Aggregator — 完整檢查報告與優化建議

**檢查日期:** 2026-05-24  
**檢查範圍:** `http://localhost:8080` 前端 + 後端 API  
**後端位置:** `/Users/kimhsiao/git/pic.net.tw/RSS-collection`  
**Frontend:** `web/` (Vue 3 + TypeScript + Tailwind + Pinia + Vue Router + i18n)  
**Backend:** `src/` (FastAPI + SQLAlchemy + aiosqlite)  
**後端 API 前綴:** `/api/v1/`  
**預設監聽:** `http://127.0.0.1:51085`  

---

## 1. 運行環境現況

### 1.1 目前服務狀態

| 服務 | 狀態 | 備註 |
|------|------|------|
| Frontend (Vite preview) | `localhost:8080` | Proxy `/api` → `localhost:51085` |
| Backend (uvicorn) | `localhost:51085` | 無法直接存取，需透過 Vite proxy |
| 資料庫 | SQLite `data/rss.db` | 正常，10 個 RSS 來源已設定 |

### 1.2 API 端點測試摘要

| 端點 | 結果 | 說明 |
|------|------|------|
| `GET /api/v1/feed` | 無回應 | 可能需要參數或認證 |
| `GET /api/v1/sources` | 正常 | 回傳 10 個來源 |
| `GET /api/v1/history/batches` | 正常 | 1 個批次，142 篇文章 |
| `GET /api/v1/keys` | 正常 | 15 支 API Key |
| `GET /api/v1/logs` | 正常 | 有 fetch 成功/失敗記錄 |
| `GET /api/v1/stats` | 正常 | 每日統計資料 |
| `GET /health` | 正常 | `{"status":"ok","require_api_key":false}` |
| `GET /docs` (Swagger) | 正常 | OpenAPI 文件可存取 |

### 1.3 `/history` 頁面按鈕現況確認

**發現：「刪除全部」與「刷新」按鈕程式碼已正確實作為 `<Button>` 元件：**

```vue
<!-- 程式碼 (HistoryPage.vue, lines 221-234) -->
<Button
  v-if="selectedGroupId === null && batches.length > 0"
  variant="outline"
  size="sm"
  :disabled="deletingAll"
  @click="confirmDeleteAll"
>
  <Trash2 class="h-4 w-4 text-red-500" />
  <span class="ml-1.5">{{ t("history.delete_all") }}</span>
</Button>
<Button @click="fetchBatches">
  <RefreshCw class="h-4 w-4 text-green-500" />
  <span class="ml-1.5">{{ t("common.refresh") }}</span>
</Button>
```

按鈕使用 `<Button>` 元件（有 `variant`、`size`、`disabled` 等 prop），符合規範。如果呈現異常，可能是 CSS 樣式問題或 Vite 構建問題，具體需透過瀏覽器 DevTools 檢查。

---

## 2. 前端問題清單

### 2.1 安全性問題 (CRITICAL)

| # | 檔案 | 問題 | 說明 |
|---|------|------|------|
| F-C1 | `web/src/api/feed.ts` (L115-133) | `getFeed` 使用 raw `fetch` 而非 axios 實例 | 繞過了認證攔截器、API Key 處理與操作日誌記錄。應改用集中的 `api` client。 |

### 2.2 i18n 違規 (HIGH)

| # | 檔案 | 行號 | 問題 |
|---|------|------|------|
| F-H1 | `web/src/pages/SetupWizard.vue` | 185-186 | `<option value="en">English</option>` / `<option value="zh">中文</option>` 為硬編碼文字，應使用 `{{ t('setup.language_en') }}` |
| F-H2 | `web/src/stores/settings.ts` | L1-11 | 預設語言 `'zh'` 與 AGENTS.md 宣告的「Default language is English」不一致 |

### 2.3 無障礙存取性缺失 (HIGH)

| # | 檔案 | 行號 | 問題 |
|---|------|------|------|
| F-A1 | `web/src/components/LogCard.vue` | 129 | 展開/摺疊按鈕缺少 `aria-expanded` 屬性 |
| F-A2 | `web/src/pages/HistoryPage.vue` | 377-390 | 批次展開/摺疊按鈕缺少 `aria-expanded` + `aria-controls` |
| F-A3 | `web/src/components/ui/ConfirmDialog.vue` | 114-130 | 對話框按鈕缺少 `type="button"` 可能導致表單送出問題；缺少 `aria-label` |
| F-A4 | `web/src/components/ui/Button.vue` | 48 | 元件未傳遞 `aria-label` prop 到底層 `<button>` |
| F-A5 | `web/src/components/ui/Dialog.vue` | 55 | `aria-labelledby` 綁定的 `resolvedTitleId` 可能與標題元素 `id` 不匹配 |

### 2.4 Console.log 偵錯殘留 (MEDIUM)

| # | 檔案 | 行號 | 說明 |
|---|------|------|------|
| F-D1 | `web/src/router/index.ts` | 58-98 | 多處 `[DEBUG Router]` console.log，應移除 |
| F-D2 | `web/src/main.ts` | 11-23 | 多處 `[DEBUG]` console.log，應移除 |
| F-D3 | `web/src/api/preview.ts` | 60-96 | 多處 `[PREVIEW]` console.log/console.warn |
| F-D4 | `web/src/api/logs.ts` | 14, 16 | `[API] getLogs` console.log |
| F-D5 | `web/src/pages/SettingsPage.vue` | 154 | `[SettingsPage] Error fetching logs` console.error |
| F-D6 | `web/src/pages/LogsPage.vue` | 28 | `[LogsPage] Error fetching logs` console.error |

### 2.5 翻譯檔案不完整 (MEDIUM)

| # | 檔案 | 問題 |
|---|------|------|
| F-T1 | `web/src/locales/en.json` + `zh.json` | 缺少 `setup.language_en`、`setup.language_zh`（SetupWizard 有引用但未定義） |
| F-T2 | `web/src/locales/en.json` + `zh.json` | 缺少 `common.collapse`、`common.expand`（SourcesPage.vue 有引用） |

### 2.6 按鈕缺少 tooltip/label (MEDIUM)

| # | 檔案 | 行號 | 問題 |
|---|------|------|------|
| F-B1 | `web/src/pages/SettingsPage.vue` | 438-444 | Desktop 重啟按鈕缺少 `:title` 屬性 |

### 2.7 CSS/樣式殘留 (LOW)

| # | 檔案 | 行號 | 問題 |
|---|------|------|------|
| F-S1 | `web/src/pages/HistoryPage.vue` | 499-518 | `.preview-dialog-enter-active` 等動畫 class 為已移除預覽對話框的殘留樣式；`.rounded-2xl` 與實際的 `.rounded-xl` 不一致 |

### 2.8 元件一致性问题 (LOW)

| # | 檔案 | 說明 |
|---|------|------|
| F-C2 | `web/src/components/SourceDialog.vue` + `KeyDialog.vue` | `defineProps` 使用方式不一致（一個有介面，一個用 inline type） |
| F-C3 | `web/src/components/ui/Tooltip.vue` | 存在但未在整個 codebase 中一致使用 |

---

## 3. 後端問題清單

### 3.1 安全性問題 (CRITICAL)

| # | 檔案 | 問題 | 說明 |
|---|------|------|------|
| B-C1 | `src/api/routes/previews.py` (L14-78) | Previews API 端點**完全沒有 API Key 認證保護** | 以下端點全部公開無保護：<br>`DELETE /api/v1/previews`<br>`POST /api/v1/previews/fetch`<br>`GET /api/v1/previews/{url_hash}`<br>`GET /api/v1/previews?url=...`<br>`POST /api/v1/previews`<br>其他受保護路由皆使用 `_: str = Depends(require_api_key)`，但這些沒有。 |
| B-C2 | `src/api/routes/previews.py` (L30-34) | 無認證的 SSRF 風險 | 可被濫用於任意 URL 抓取，建議加入 rate limiting 或認證 |

### 3.2 高嚴重性問題 (HIGH)

| # | 檔案 | 問題 | 說明 |
|---|------|------|------|
| B-H1 | `src/main.py` (L79-85) | CORS `allow_credentials=True` 與 `allow_origins=["*"]` 不相容 | 當 `allow_credentials=True` 時，瀏覽器會拒絕 `allow_origins=["*"]`。`.env` 中 `ALLOWED_ORIGINS=` 為空，會預設為 `["*"]`，造成 CORS 失效。 |
| B-H2 | `src/api/routes/backup.py` (L28) | 備份檔案名稱版本號寫死 `0.10.0` | 實際 App 版本為 `0.21.2`，備份檔名會使用錯誤版本 |
| B-H3 | `src/services/backup_service.py` (L39) | 備份服務版本號 `__version__ = "0.20.0"` | 落後於實際版本 |
| B-H4 | `src/scheduler/fetch_scheduler.py` (L25-29) | `FetchScheduler.start()` 只做 `logger.info`，**沒有實際啟動任何循環** | `_run_loop()` 是在 `ScheduleScheduler` 中呼叫的。當 `SCHEDULER_ENABLED=true` 但沒有 schedules 時，FetchScheduler 不會執行任何間隔抓取。 |
| B-H5 | `src/services/fetch_service.py` (L190) | 只 catch `httpx.HTTPError`，不 catch `asyncio.TimeoutError` | `asyncio.TimeoutError` 不是 `httpx.HTTPError` 的子類，網路超時可能導致未處理的 500 錯誤 |
| B-H6 | `src/services/rate_limiter.py` (L5, 22, 33) | 使用 `threading.Lock` 而非 `asyncio.Lock` | 在 async 上下文中使用同步鎖會阻塞 event loop，影響效能 |

### 3.3 中等嚴重性問題 (MEDIUM)

| # | 檔案 | 問題 | 說明 |
|---|------|------|------|
| B-M1 | `src/main.py` | 缺少全域例外處理器 | 無 `app.add_exception_handler()`，未處理例外會產生通用 500 回應，格式不一致 |
| B-M2 | `src/services/backup_service.py` (L184-193) | `_get_config()` 中 `timezone` 和 `language` 為硬編碼值 | 應從 `src/config.py` 的設定讀取 |
| B-M3 | `src/services/history_service.py` (L296-303) | `commit()` 後緊接 `refresh()` | 若 refresh 失敗，函式已回傳不完整資料；建議先 refresh 再 commit |
| B-M4 | `src/api/routes/schedule.py` (L11) | Router prefix 包含路徑參數 `{group_id}` 但又在 handler 參數重複接收 | 冗余設計，path 為 `/source-groups/{group_id}/schedules` |
| B-M5 | `src/main.py` (L99) | `groups_router` 以 `/groups` prefix 註冊，是 `/source-groups` 的別名 | 造成重複路由，可能維護困難 |
| B-M6 | `src/services/backup_service.py` (L431-607) | 廣泛的 `except Exception` 捕捉，錯誤處理不夠細粒度 | `ValueError` 在 L603 被捕捉，但其他例外可能未妥善處理 |

### 3.4 低嚴重性問題 (LOW)

| # | 檔案 | 問題 | 說明 |
|---|------|------|------|
| B-L1 | `.env` (L34) | `ALLOWED_ORIGINS=` 為空 | 搭配 `allow_credentials=True` 時會預設允許所有 origin，但邏輯上不安全 |
| B-L2 | `src/main.py` | 無全域 request timeout 中介層 | 長時間執行中的請求可能無限期掛起 |
| B-L3 | `src/services/rate_limiter.py` | 每個 worker 有自己的 rate limit 狀態（記憶體，非共享） | 多 worker 部署時各自獨立計數 |
| B-L4 | `src/services/source_service.py` (L99-100) | `commit()` 後 `refresh()`，並發請求可能讀到過時資料 | 建議優化 session 管理策略 |
| B-L5 | `src/models/` (多處) | `FeedItem.published_at`、`source_id`、`batch_id` 等常用查詢欄位可能缺少 explicit index | 可能影響查詢效能 |

---

## 4. 架構與配置問題

### 4.1 Port 配置複雜性

| 問題 | 說明 |
|------|------|
| Vite preview proxy 指向 `127.0.0.1:51085` | 當前後端在 port `51085`，但前端在 `8080`，透過 Vite proxy 串接。架構上合理但增加了除錯複雜度。 |
| 環境變數 `.env` vs `web/.env` | 兩處都有 API URL 設定，需確認 `VITE_API_PROXY_TARGET` 是否正確指向 `51085` |

### 4.2 API 路徑不一致

| 位置 | 路徑 |
|------|------|
| Backend routes | `/api/v1/...` |
| Frontend API clients | 假設使用 `/api/...` (Vite proxy 轉發) |
| Vite preview config | `/api` → `http://127.0.0.1:51085` (缺少 `/v1`) |

**需確認：** Vite proxy 是否正確轉發 `/api/v1/` 請求。建議檢查 `web/vite.config.ts` 的 proxy 設定。

---

## 5. 優先處理順序建議

### 第一優先 (立即修復 — 安全性)
1. **B-C1**: 為 `src/api/routes/previews.py` 所有端點加入 API Key 認證
2. **B-C2**: 加入 rate limiting 防止 Previews API 被濫用
3. **F-C1**: `feed.ts` 改用集中的 axios client

### 第二優先 (高嚴重性)
4. **B-H1**: 修正 CORS 配置（設定明確的 `ALLOWED_ORIGINS`）
5. **B-H2 + B-H3**: 修正備份版本號
6. **B-H4**: `FetchScheduler.start()` 實際啟動循環
7. **B-H5**: 加入 `asyncio.TimeoutError` 處理
8. **B-H6**: `threading.Lock` 改為 `asyncio.Lock`

### 第三優先 (清理)
9. 移除所有 `console.log` 偵錯殘留（F-D1 ~ F-D6）
10. 補齊 i18n 缺失翻譯（F-T1, F-T2）
11. 修正 SetupWizard 硬編碼文字（F-H1）
12. 加入無障礙屬性（F-A1 ~ F-A5）

---

## 6. 驗證方式

### 前端檢查（需手動透過瀏覽器 DevTools）
1. 開啟 Edge/Chrome，導航至 `http://localhost:8080/history`
2. 檢查右上角「刪除全部」「刷新」按鈕是否為 `<button>` 元素
3. 點擊按鈕是否有視覺回饋（hover/active 狀態）
4. 測試刪除功能是否正常運作

### 後端 API 測試
```bash
# 健康檢查
curl http://localhost:51085/health

# 來源列表
curl http://localhost:51085/api/v1/sources

# 歷史批次
curl http://localhost:51085/api/v1/history/batches

# Previews API（驗證是否真的無認證）
curl -X DELETE http://localhost:51085/api/v1/previews
```

### Playwright E2E 測試
```bash
cd /Users/kimhsiao/git/pic.net.tw/RSS-collection/web
pnpm test:e2e
```

---

*本報告由 Hermes Agent 自動產生*
*檢查方法：程式碼靜態分析 + API 端點測試 + 子代理並行 code review*