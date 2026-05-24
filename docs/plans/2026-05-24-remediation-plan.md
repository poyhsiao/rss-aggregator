# RSS Aggregator — 調整、優化、改進建議文件

**文件日期:** 2026-05-24  
**依據:** 完整檢查報告 (`2026-05-24-complete-inspection-report.md`)  
**優先順序:** 以安全性 → 高嚴重性 → 清理 排序  

---

## 總覽

本次檢查涵蓋 RSS-collection 專案的前端（Vue 3 + TypeScript + Tailwind）與後端（FastAPI + SQLAlchemy）。發現 **6 項 CRITICAL/HIGH 安全性與功能性問題**，以及多項中低嚴重性問題。所有問題均附有具體修改位置，方便逐項修復。

---

## Part 1：安全性修復

### S-1: Previews API 缺少認證 [CRITICAL]

**位置:** `src/api/routes/previews.py` (全檔)

**問題:** 6 個 Previews 端點完全沒有 API Key 保護，可被任意存取。

**修改點:**
```python
# 在每個端點加入 API Key 依賴
from src.api.dependencies import require_api_key

@router.delete("/previews")
async def delete_all_previews(_: str = Depends(require_api_key)):  # ← 加入這行
    ...

@router.post("/previews/fetch")
async def fetch_and_cache_preview(
    request: FetchPreviewRequest,
    _: str = Depends(require_api_key),  # ← 加入這行
    preview_service: PreviewService = Depends(get_preview_service),
) -> PreviewContentResponse:
    ...
```

**受影響端點:**
- `DELETE /api/v1/previews`
- `POST /api/v1/previews/fetch`
- `GET /api/v1/previews/{url_hash}`
- `GET /api/v1/previews`
- `POST /api/v1/previews`

---

### S-2: feed.ts 使用 raw fetch 繞過認證 [CRITICAL]

**位置:** `web/src/api/feed.ts` (L115-133)

**問題:** `getFeed` 使用 `window.fetch` 而非 axios instance，繞過了 API Key 攔截器。

**修改點 (改動前):**
```typescript
const response = await window.fetch(url, { ... })
```

**修改點 (改動後):**
```typescript
import api from "@/api"  // 改用集中的 axios client
const response = await api.get(url, { params: { ... } })
```

---

### S-3: CORS 配置不安全 [HIGH]

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

---

## Part 2：功能性修復

### F-1: FetchScheduler.start() 無實際作用 [HIGH]

**位置:** `src/scheduler/fetch_scheduler.py` (L25-29)

**問題:** `start()` 只做 `logger.info`，沒有啟動實際的循環。

**修改點:**
```python
async def start(self) -> None:
    """Start the fetch scheduler (called on app startup)."""
    logger.info("Fetch scheduler started")
    # 實際啟動背景任務
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

---

### F-2: asyncio.TimeoutError 未處理 [HIGH]

**位置:** `src/services/fetch_service.py` (L190)

**問題:** 只 catch `httpx.HTTPError`，`asyncio.TimeoutError` 會向上傳播成 500。

**修改點:**
```python
# 改動前
except httpx.HTTPError:
    ...

# 改動後
except (httpx.HTTPError, asyncio.TimeoutError) as e:
    logger.warning(f"Fetch attempt {attempt + 1} failed: {e}")
    if attempt < self.retry_count - 1:
        await asyncio.sleep(self.retry_delay)
    else:
        return None
```

---

### F-3: threading.Lock 應改為 asyncio.Lock [HIGH]

**位置:** `src/services/rate_limiter.py` (L5, 22, 33)

**修改點:**
```python
# 改動前
from threading import Lock
self._lock = Lock()

# 改動後
import asyncio
self._lock = asyncio.Lock()
```

---

### F-4: 備份版本號寫死 [HIGH]

**位置:** `src/api/routes/backup.py` (L28) + `src/services/backup_service.py` (L39)

**修改點:**
```python
# backup.py L28 — 改動前
filename = backup_service._generate_backup_filename("0.10.0")

# 改動後（從 main.py 或 config 讀取）
from src.config import get_settings
settings = get_settings()
filename = backup_service._generate_backup_filename(settings.app_version)
```

```python
# backup_service.py L39 — 改動前
__version__ = "0.20.0"

# 改動後
from src.config import get_settings
__version__ = get_settings().app_version
```

---

### F-5: FetchScheduler 在無 schedule 時不抓取 [HIGH]

**位置:** `src/scheduler/fetch_scheduler.py` + `src/scheduler/schedule_scheduler.py`

**問題:** 當 `SCHEDULER_ENABLED=true` 但沒有任何 schedule 時，`FetchScheduler._check_and_fetch()` 只由 `ScheduleScheduler._run_loop()` 觸發。若無 schedule，永遠不會抓取。

**建議:** `FetchScheduler` 應有自己的獨立循環，不依賴 `ScheduleScheduler`。

---

## Part 3：i18n 與翻譯修復

### T-1: SetupWizard 硬編碼語言選項 [HIGH]

**位置:** `web/src/pages/SetupWizard.vue` (L185-186)

**修改點:**
```vue
<!-- 改動前 -->
<option value="en">English</option>
<option value="zh">中文</option>

<!-- 改動後 -->
<option value="en">{{ t('setup.language_en') }}</option>
<option value="zh">{{ t('setup.language_zh') }}</option>
```

**翻譯檔更新 (`web/src/locales/zh.json`):**
```json
"setup": {
  "language_en": "English",
  "language_zh": "中文"
}
```

---

### T-2: 缺少翻譯 key [MEDIUM]

**位置:** `web/src/locales/en.json` + `zh.json`

需補齊以下 key：
```json
{
  "setup": { "language_en": "English", "language_zh": "中文" },
  "common": { "collapse": "Collapse", "expand": "Expand" }
}
```

---

### T-3: settings store 預設語言不一致 [MEDIUM]

**位置:** `web/src/stores/settings.ts` (L1-11)

**修改點:**
```typescript
// 改動前：預設 'zh'
// 改動後：預設 'en'（與 AGENTS.md 一致）
const locale = ref('en')
```

---

## Part 4：無障礙存取性修復

### A-1: 按鈕 aria 属性缺失

需在以下位置加入 `aria-expanded` / `aria-label` / `aria-controls`：

| 檔案 | 行號 | 屬性 |
|------|------|------|
| `web/src/components/LogCard.vue` | 129 | `aria-expanded` |
| `web/src/pages/HistoryPage.vue` | 377-390 | `aria-expanded`, `aria-controls` |
| `web/src/components/ui/ConfirmDialog.vue` | 114-130 | `type="button"`, `aria-label` |
| `web/src/components/ui/Button.vue` | 48 | 傳遞 `aria-label` prop |

**修改點 (以 LogCard.vue 為例):**
```vue
<!-- 改動前 -->
<button @click="toggleExpand">

<!-- 改動後 -->
<button
  @click="toggleExpand"
  :aria-expanded="expanded"
  aria-controls="log-content"
>
```

---

## Part 5：偵錯程式碼移除

### D-1: console.log 殘留清除

以下檔案需移除或包裝 `console.log`（生產環境不應輸出偵錯資訊）：

| 檔案 | 數量 | 說明 |
|------|------|------|
| `web/src/router/index.ts` | ~40 行 | `[DEBUG Router]` 多處 |
| `web/src/main.ts` | ~13 行 | `[DEBUG]` 多處 |
| `web/src/api/preview.ts` | ~37 行 | `[PREVIEW]` console.warn |
| `web/src/api/logs.ts` | 2 處 | `[API] getLogs` |
| `web/src/pages/SettingsPage.vue` | 1 處 | `console.error` |
| `web/src/pages/LogsPage.vue` | 1 處 | `console.error` |

**建議:** 使用 `src/utils/logger.ts` 統一管理，生產環境自動抑制非錯誤日誌。

---

## Part 6：樣式與一致性修復

### S-1: HistoryPage 殘留動畫樣式 [LOW]

**位置:** `web/src/pages/HistoryPage.vue` (L499-518, `<style scoped>`)

**修改點:** 移除 `.preview-dialog-enter-active`、`.preview-dialog-leave-active` 等已無對應元件的動畫 class。

---

### S-2: SettingsPage 重啟按鈕缺少 tooltip [MEDIUM]

**位置:** `web/src/pages/SettingsPage.vue` (L438-444)

**修改點:**
```vue
<!-- 改動前 -->
<button class="..." @click="handleRestartBackend">

<!-- 改動後 -->
<button
  class="..."
  :title="t('settings.desktop.restart')"
  @click="handleRestartBackend"
>
```

---

### S-3: SourceDialog / KeyDialog props 介面不一致 [LOW]

**修改點:** 統一使用 `defineProps<{ ... }>()` 或建立共用的 `SourceDialogProps` interface。

---

## Part 7：例外處理改進

### E-1: 加入全域例外處理器 [MEDIUM]

**位置:** `src/main.py`

**修改點:**
```python
from fastapi import Request
from fastapi.responses import JSONResponse

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "type": type(exc).__name__}
    )
```

---

### E-2: backup_service 錯誤處理細粒度化 [MEDIUM]

**位置:** `src/services/backup_service.py` (L431-607)

將廣泛的 `except Exception` 拆分為：
- `ValueError` — 版本不相容
- `FileNotFoundError` — 備份檔案不存在
- `json.JSONDecodeError` — 檔案格式錯誤
- `Exception` — 其餘未預期錯誤

---

## Part 8：效能優化

### P-1: 資料庫 Index 建議 [LOW]

在 `src/models/` 中的以下欄位建立 index：

```python
# src/models/feed_item.py
class FeedItem(Base):
    __table_args__ = (
        Index("ix_feed_item_published_at", "published_at"),
        Index("ix_feed_item_source_id", "source_id"),
        Index("ix_feed_item_batch_id", "batch_id"),
    )
```

---

### P-2: Rate Limiter 每 Worker 狀態問題 [LOW]

**說明:** 目前 in-memory rate limiting 在多 worker 部署時各進程獨立計數。

**建議選項:**
1. 使用 Redis 等共享存储（增加維運複雜度）
2. 在文件說明中標記此限制（單 worker 部署不受影響）
3. 使用 FastAPI 的 `RateLimiter` middleware 搭配共享存储

---

## 修改清單總表

| ID | 優先 | 類別 | 檔案 | 修改點 |
|----|------|------|------|--------|
| S-1 | CRITICAL | 安全性 | `src/api/routes/previews.py` | 所有端點加 `require_api_key` |
| S-2 | CRITICAL | 安全性 | `web/src/api/feed.ts` | raw fetch 改 axios |
| S-3 | HIGH | 安全性 | `src/main.py` + `.env` | CORS 明確設定 origins |
| F-1 | HIGH | 功能 | `src/scheduler/fetch_scheduler.py` | `start()` 啟動實際循環 |
| F-2 | HIGH | 功能 | `src/services/fetch_service.py` | 加 `asyncio.TimeoutError` catch |
| F-3 | HIGH | 功能 | `src/services/rate_limiter.py` | `threading.Lock` → `asyncio.Lock` |
| F-4 | HIGH | 功能 | `src/api/routes/backup.py` + `backup_service.py` | 版本號動態讀取 |
| F-5 | HIGH | 功能 | `src/scheduler/fetch_scheduler.py` | 獨立循環不依賴 schedule |
| T-1 | HIGH | i18n | `web/src/pages/SetupWizard.vue` | 硬編碼改 i18n key |
| T-2 | MEDIUM | i18n | `web/src/locales/*.json` | 補齊缺失翻譯 |
| T-3 | MEDIUM | i18n | `web/src/stores/settings.ts` | 預設語言改 `en` |
| A-1 | MEDIUM | 無障礙 | 多個元件/頁面 | 加 `aria-*` 屬性 |
| D-1 | MEDIUM | 清理 | 多個前端檔案 | 移除 console.log |
| S-2 | MEDIUM | 樣式 | `web/src/pages/SettingsPage.vue` | 加 tooltip |
| E-1 | MEDIUM | 錯誤處理 | `src/main.py` | 加全域 exception handler |
| E-2 | MEDIUM | 錯誤處理 | `src/services/backup_service.py` | 細粒度化 try/except |
| S-3 | LOW | 樣式 | `web/src/pages/HistoryPage.vue` | 移除殘留動畫 class |
| P-1 | LOW | 效能 | `src/models/feed_item.py` | 加 DB index |

---

*本建議文件由 Hermes Agent 自動產生*
*共 18 項修改建議，含具體程式碼修改點*