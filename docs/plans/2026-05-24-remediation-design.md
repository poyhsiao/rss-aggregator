# RSS Aggregator — 優化與修復設計文件

**文件日期:** 2026-05-24
**依據:** 完整檢查報告 + 調整計劃
**範圍:** 前端（Vue 3 + TypeScript）+ 後端（FastAPI + Python）
**排除:** Previews API 認證（S-1, S-2）

---

## 1. 執行架構

### 1.1 分 Phase 執行

```
Phase 1: 後端安全性與核心功能修復
Phase 2: 前端 i18n 與無障礙修復
Phase 3: 清理與效能優化
```

每個 Phase 內含 2-3 批次（batch），每批次走 TDD 循環：
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

## 3. 執行項目清單（共 16 項）

### Phase 1: 後端安全性與核心功能修復

| ID | 檔案 | 變更 | 測試優先 |
|----|------|------|----------|
| B-S3 | `src/main.py` + `.env` | CORS 明確設定 origins | Yes |
| B-F1 | `src/scheduler/fetch_scheduler.py` | `start()` 啟動實際循環 | Yes |
| B-F2 | `src/services/fetch_service.py` | 加 `asyncio.TimeoutError` catch | Yes |
| B-F3 | `src/services/rate_limiter.py` | `threading.Lock` → `asyncio.Lock` | Yes |
| B-F4 | `src/api/routes/backup.py` + `backup_service.py` | 版本號動態讀取 | Yes |
| B-F5 | `src/scheduler/fetch_scheduler.py` | 獨立循環不依賴 schedule | Yes |
| B-E1 | `src/main.py` | 加全域 exception handler | Yes |
| B-E2 | `src/services/backup_service.py` | 細粒度化 try/except | No |

### Phase 2: 前端 i18n 與無障礙修復

| ID | 檔案 | 變更 | 測試優先 |
|----|------|------|----------|
| F-T1 | `web/src/pages/SetupWizard.vue` | 硬編碼改 i18n key | Yes |
| F-T2 | `web/src/locales/*.json` | 補齊缺失翻譯 | No |
| F-T3 | `web/src/stores/settings.ts` | 預設語言改 `en` | Yes |
| F-A1 | 多個元件/頁面 | 加 `aria-*` 屬性 | No |

### Phase 3: 清理與效能優化

| ID | 檔案 | 變更 | 測試優先 |
|----|------|------|----------|
| F-D1 | 多個前端檔案 | 移除 console.log | No |
| F-S1 | `web/src/pages/SettingsPage.vue` | 加 tooltip | No |
| F-S2 | `web/src/pages/HistoryPage.vue` | 移除殘留動畫 class | No |
| B-P1 | `src/models/feed_item.py` | 加 DB index | Yes |

---

## 4. Commit 切割規劃

預計 6-8 個有意義的 commit：

```
fix(backend): resolve CORS configuration with explicit origins
fix(backend): implement async lock in rate limiter
fix(backend): add asyncio.TimeoutError handling in fetch service
fix(backend): correct backup version number from config
fix(backend): start periodic fetch loop in FetchScheduler
fix(backend): add global exception handler
fix(frontend): complete i18n translations and fix hardcoded text
fix(frontend): add accessibility aria attributes
chore: remove debug console.log statements
perf(backend): add database indexes on feed_item
refactor(backend): granular error handling in backup service
```

---

## 5. 驗收標準

- [ ] 所有後端單元測試通過（`pytest`）
- [ ] 所有前端單元測試通過（`vitest`）
- [ ] 所有 E2E 測試通過（`Playwright`）
- [ ] 無 CRITICAL/HIGH 問題殘留
- [ ] 每個 commit 獨立可驗證

---

*本設計文件由 brainstorming 產生*