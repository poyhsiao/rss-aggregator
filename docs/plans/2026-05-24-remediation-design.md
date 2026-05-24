# RSS Aggregator — 優化與修復設計文件

**文件日期:** 2026-05-24
**依據:**
- `docs/plans/2026-05-24-complete-inspection-report.md`（完整檢查報告）
- `docs/plans/2026-05-24-remediation-plan.md`（調整建議文件）
**範圍:** 前端（Vue 3 + TypeScript）+ 後端（FastAPI + Python）
**排除:**
- S-1: Previews API 認證（使用者要求不需此項目）
- S-2: feed.ts raw fetch 改 axios（使用者要求不需此項目）

---

## 1. 執行架構

### 1.1 分 Phase 執行

```
Phase 1: 後端安全性與核心功能修復
Phase 2: 前端 i18n 與無障礙修復
Phase 3: 清理與效能優化
```

每個 Phase 內含多批次（batch），每批次走 TDD 循環：
1. 寫測試（RED）
2. 實作通過測試（GREEN）
3. 重構（IMPROVE）
4. E2E 驗證

---

## 2. 測試策略

| 測試類型 | 工具 | 覆蓋範圍 |
|----------|------|----------|
| 後端單元測試 | `pytest` + `pytest-asyncio` | B-F1 ~ B-F5, B-E1, B-E2, B-P1 |
| 後端整合測試 | `pytest` + TestClient | B-S3, B-E1 |
| 前端單元測試 | `vitest` | F-T1 ~ F-T3, F-A1 |
| 前端 E2E | `Playwright` | 所有視覺/互動變更 |

---

## 3. 執行項目清單（共 18 項）

### Phase 1: 後端安全性與核心功能修復

| ID | 原始ID | 檔案 | 變更 | 測試優先 |
|----|--------|------|------|----------|
| B-S3 | S-3 | `src/main.py` + `.env` | CORS 明確設定 origins | Yes |
| B-F1 | F-1 | `src/scheduler/fetch_scheduler.py` | `start()` 啟動實際循環 | Yes |
| B-F2 | F-2 | `src/services/fetch_service.py` | 加 `asyncio.TimeoutError` catch | Yes |
| B-F3 | F-3 | `src/services/rate_limiter.py` | `threading.Lock` → `asyncio.Lock` | Yes |
| B-F4 | F-4 | `src/api/routes/backup.py` + `backup_service.py` | 版本號動態讀取 | Yes |
| B-F5 | F-5 | `src/scheduler/fetch_scheduler.py` | 獨立循環不依賴 schedule | Yes |
| B-E1 | E-1 | `src/main.py` | 加全域 exception handler | Yes |
| B-E2 | E-2 | `src/services/backup_service.py` | 細粒度化 try/except | No |

### Phase 2: 前端 i18n 與無障礙修復

| ID | 原始ID | 檔案 | 變更 | 測試優先 |
|----|--------|------|------|----------|
| F-T1 | T-1 | `web/src/pages/SetupWizard.vue` | 硬編碼改 i18n key | Yes |
| F-T2 | T-2 | `web/src/locales/*.json` | 補齊缺失翻譯 | No |
| F-T3 | T-3 | `web/src/stores/settings.ts` | 預設語言改 `en` | Yes |
| F-A1 | A-1 | 多個元件/頁面 | 加 `aria-*` 屬性 | No |

### Phase 3: 清理與效能優化

| ID | 原始ID | 檔案 | 變更 | 測試優先 |
|----|--------|------|------|----------|
| F-D1 | D-1 | 多個前端檔案 | 移除 console.log | No |
| F-S1 | S-1 | `web/src/pages/SettingsPage.vue` | 加 tooltip | No |
| F-S2 | S-2 | `web/src/pages/HistoryPage.vue` | 移除殘留動畫 class | No |
| F-C2 | C-2 | `SourceDialog.vue` + `KeyDialog.vue` | defineProps 介面一致性 | No |
| B-P1 | P-1 | `src/models/feed_item.py` | 加 DB index | Yes |

---

## 4. 詳細修改點（對應 remediation-plan.md）

### B-S3: CORS 配置不安全 [HIGH]

**位置:** `src/main.py` (L79-85) + `.env` (L34)

**問題:** `allow_credentials=True` 搭配 `allow_origins=["*"]` 會被瀏覽器拒絕。

**修改點 (`.env`):**
```env
ALLOWED_ORIGINS=http://localhost:8080,http://localhost:3001
```

**修改點 (`src/main.py`):**
```python
origins = settings.allowed_origins.split(",") if settings.allowed_origins else []
if not origins:
    raise ValueError("ALLOWED_ORIGINS must be set when allow_credentials=True")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### B-F1 + B-F5: FetchScheduler 獨立循環 [HIGH]

**位置:** `src/scheduler/fetch_scheduler.py` (L25-29)

**問題:** `start()` 只做 `logger.info`，沒有啟動實際的循環。當無 schedule 時也不會抓取。

**修改點:**
```python
async def start(self) -> None:
    """Start the fetch scheduler (called on app startup)."""
    logger.info("Fetch scheduler started")
    asyncio.create_task(self._periodic_fetch())
    logger.info("Background fetch loop started")

async def _periodic_fetch(self) -> None:
    """Periodically fetch all active sources."""
    while True:
        try:
            await self._check_and_fetch()
        except Exception as e:
            logger.error(f"Periodic fetch error: {e}")
        await asyncio.sleep(self.interval_seconds)
```

### B-F2: asyncio.TimeoutError 未處理 [HIGH]

**位置:** `src/services/fetch_service.py` (L190)

**問題:** 只 catch `httpx.HTTPError`，`asyncio.TimeoutError` 會向上傳播成 500。

**修改點:**
```python
# 改動後
except (httpx.HTTPError, asyncio.TimeoutError) as e:
    logger.warning(f"Fetch attempt {attempt + 1} failed: {e}")
```

### B-F3: threading.Lock 應改為 asyncio.Lock [HIGH]

**位置:** `src/services/rate_limiter.py` (L5, 22, 33)

**修改點:**
```python
# 改動後
import asyncio
self._lock = asyncio.Lock()
```

### B-F4: 備份版本號寫死 [HIGH]

**位置:** `src/api/routes/backup.py` (L28) + `src/services/backup_service.py` (L39)

**修改點:** 從 `src/config.py` 的設定動態讀取版本號。

### B-E1: 加入全域例外處理器 [MEDIUM]

**位置:** `src/main.py`

**修改點:**
```python
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "type": type(exc).__name__}
    )
```

### B-E2: backup_service 錯誤處理細粒度化 [MEDIUM]

**位置:** `src/services/backup_service.py` (L431-607)

將廣泛的 `except Exception` 拆分為特定例外類型處理。

### B-P1: 資料庫 Index 建議 [LOW]

**位置:** `src/models/feed_item.py`

**修改點:**
```python
__table_args__ = (
    Index("ix_feed_item_published_at", "published_at"),
    Index("ix_feed_item_source_id", "source_id"),
    Index("ix_feed_item_batch_id", "batch_id"),
)
```

### F-T1: SetupWizard 硬編碼語言選項 [HIGH]

**位置:** `web/src/pages/SetupWizard.vue` (L185-186)

**修改點:**
```vue
<!-- 改動後 -->
<option value="en">{{ t('setup.language_en') }}</option>
<option value="zh">{{ t('setup.language_zh') }}</option>
```

### F-T2: 缺少翻譯 key [MEDIUM]

**位置:** `web/src/locales/en.json` + `zh.json`

需補齊：
```json
{
  "setup": { "language_en": "English", "language_zh": "中文" },
  "common": { "collapse": "Collapse", "expand": "Expand" }
}
```

### F-T3: settings store 預設語言不一致 [MEDIUM]

**位置:** `web/src/stores/settings.ts` (L1-11)

**修改點:** 預設改為 `'en'`（與 AGENTS.md 一致）。

### F-A1: 按鈕 aria 屬性缺失 [MEDIUM]

需在以下位置加入 `aria-expanded` / `aria-label` / `aria-controls`：
- `web/src/components/LogCard.vue` (L129)
- `web/src/pages/HistoryPage.vue` (L377-390)
- `web/src/components/ui/ConfirmDialog.vue` (L114-130)
- `web/src/components/ui/Button.vue` (L48)

### F-D1: console.log 殘留清除 [MEDIUM]

需移除以下檔案的 console.log：
- `web/src/router/index.ts` (L58-98)
- `web/src/main.ts` (L11-23)
- `web/src/api/preview.ts` (L60-96)
- `web/src/api/logs.ts` (L14, 16)
- `web/src/pages/SettingsPage.vue` (L154)
- `web/src/pages/LogsPage.vue` (L28)

### F-S1: SettingsPage 重啟按鈕缺少 tooltip [MEDIUM]

**位置:** `web/src/pages/SettingsPage.vue` (L438-444)

### F-S2: HistoryPage 殘留動畫樣式 [LOW]

**位置:** `web/src/pages/HistoryPage.vue` (L499-518)

移除 `.preview-dialog-enter-active` 等已無對應元件的動畫 class。

### F-C2: SourceDialog / KeyDialog props 介面不一致 [LOW]

**修改點:** 統一使用 `defineProps<{ ... }>()` 或建立共用的 interface。

---

## 5. Commit 切割規劃

預計 10 個有意義的 commit：

```
fix(backend): resolve CORS configuration with explicit origins
fix(backend): implement async lock in rate limiter
fix(backend): add asyncio.TimeoutError handling in fetch service
fix(backend): correct backup version number from config
fix(backend): start periodic fetch loop in FetchScheduler
fix(backend): add global exception handler
refactor(backend): granular error handling in backup service
fix(frontend): complete i18n translations and fix hardcoded text
fix(frontend): add accessibility aria attributes to interactive elements
chore: remove debug console.log statements from frontend
perf(backend): add database indexes on feed_item columns
fix(frontend): add tooltip to SettingsPage restart button
fix(frontend): remove unused animation classes from HistoryPage
refactor(frontend): unify SourceDialog and KeyDialog props interface
```

---

## 6. 驗收標準

- [ ] 所有後端單元測試通過（`pytest`）
- [ ] 所有前端單元測試通過（`vitest`）
- [ ] 所有 E2E 測試通過（`Playwright`）
- [ ] 無 CRITICAL/HIGH 問題殘留
- [ ] 每個 commit 獨立可驗證
- [ ] i18n 完整（無硬編碼文字）
- [ ] 無障礙屬性完整（aria-*）

---

*本設計文件由 brainstorming 產生*