# Feature Toggle Control Panel — Specification

**Version:** 1.1  
**Status:** Draft (pending review)  
**Target:** RSS-collection v0.18.1 (starting point for implementation)  
**Last Updated:** 2026-05-12

---

## 1. Overview

A hidden control panel revealed by **10 consecutive taps** on the RSS icon in the **Settings page header**. Users can toggle three application features:

1. **Group Visibility** (`group_visibility`) — Show/hide the group sidebar panel in Sources page
2. **Scheduled Updates** (`timer`) — Enable/disable the background scheduler for feed fetching
3. **Share Link** (`share_link`) — Enable/disable the share/copy link functionality in article views

State is persisted per-user (if authenticated) or per-session (if anonymous) in the database.

---

## 2. Differentiating from Existing Debug Feature

The project already has a debug dialog triggered by **10 taps on the RSS icon on the Feed page** (implemented in `MainLayout.vue` as `handleFeedIconClick`). This new feature:

| Aspect | Existing Debug Feature | New Feature Toggle Panel |
|--------|----------------------|--------------------------|
| Page | Feed page (`/`) | Settings page (`/settings`) |
| Trigger | RSS icon in header | RSS icon in Settings page header |
| Count | 10 taps | 10 taps |
| Timeout | 2 seconds | 3 seconds (resets on each tap) |
| Result | Opens `DebugDialog` | Opens `FeatureTogglePanel` |

**Important:** Both features coexist. Tapping the RSS icon on the **Feed page** opens `DebugDialog`; tapping on the **Settings page** opens `FeatureTogglePanel`. They are orthogonal and do not interfere.

---

## 3. Data Model

### 3.1 Database Table: `feature_toggles`

Create new model file: `src/models/feature_toggle.py`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | Integer | PK, autoincrement | Primary key |
| `user_id` | String(64) | nullable, index | Authenticated user ID (null for anonymous) |
| `session_id` | String(128) | nullable, index | Anonymous session identifier |
| `toggle_key` | String(64) | NOT NULL | One of: `group_visibility`, `timer`, `share_link` |
| `enabled` | Boolean | NOT NULL, default=False | Toggle state |
| `created_at` | DateTime | NOT NULL | Creation timestamp (UTC) |
| `updated_at` | DateTime | NOT NULL | Last update timestamp (UTC) |

**Unique constraint:** `(user_id, session_id, toggle_key)` — only one row per toggle per user/session.

**Identity Resolution:**
- If user is authenticated → use `user_id`
- If anonymous → use `session_id`
- Never mix the two in the same row

### 3.2 Alembic Migration

Create migration file: `alembic/versions/xxxx_add_feature_toggles.py`

Migration must:
- Create the `feature_toggles` table
- Insert 3 default rows (all disabled) for any existing authenticated users
- For anonymous users, defaults are derived at query time (no rows needed)

---

## 4. Backend Architecture

### 4.1 New Files

| File | Purpose |
|------|---------|
| `src/models/feature_toggle.py` | SQLAlchemy ORM model |
| `src/schemas/feature_toggle.py` | Pydantic request/response schemas |
| `src/services/feature_toggle_service.py` | Business logic (get_toggles, upsert_toggle) |
| `src/api/routes/feature_toggles.py` | FastAPI route handlers |

### 4.2 API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/feature-toggles` | Fetch all toggles for current user/session |
| `PATCH` | `/api/feature-toggles/{toggle_key}` | Update a single toggle |

#### GET /api/feature-toggles

**Response 200:**
```json
{
  "toggles": [
    { "key": "group_visibility", "enabled": true },
    { "key": "timer", "enabled": false },
    { "key": "share_link", "enabled": true }
  ]
}
```

**Logic:**
- If authenticated: query by `user_id`
- If anonymous: query by `session_id` (from cookie/header)
- Missing keys (no DB row) default to `enabled: false`

#### PATCH /api/feature-toggles/{toggle_key}

**Request body:**
```json
{ "enabled": true }
```

**Response 200:**
```json
{ "key": "share_link", "enabled": true }
```

**Response 404:** if `toggle_key` is not one of the three valid keys.

### 4.3 Router Registration

Add to `src/main.py`:
```python
from src.api.routes import feature_toggles
app.include_router(feature_toggles.router, prefix="/api")
```

---

## 5. Frontend Architecture

### 5.1 New Files

| File | Purpose |
|------|---------|
| `web/src/composables/useFeatureToggle.ts` | Click counter logic + panel visibility + API calls |
| `web/src/components/FeatureTogglePanel.vue` | Panel UI with 3 toggle switches |
| `web/src/api/feature-toggles.ts` | API client for the two endpoints |

### 5.2 Component Architecture

#### useFeatureToggle Composable

```typescript
// Signature
function useFeatureToggle(): {
  clickCount: Ref<number>
  isRevealed: Ref<boolean>
  toggles: Ref<FeatureToggle[]>
  isLoading: Ref<boolean>
  error: Ref<string | null>
  handleIconClick: () => void   // call this from the RSS icon click handler
  toggleFeature: (key: string, enabled: boolean) => Promise<void>
}
```

**Click Counter Logic:**
- `handleIconClick` is called on each RSS icon click
- Counter increments by 1 per call
- After each call, a 3-second timeout is reset (clearing any prior timeout)
- After **10 clicks** within the 3-second window, `isRevealed` becomes `true`
- Counter resets to 0 after the 3-second timeout fires with count < 10
- When `isRevealed = true`, counter stops incrementing until panel is dismissed

**API Integration:**
- On composable init (Settings page mount): call `GET /api/feature-toggles`
- On toggle change: call `PATCH /api/feature-toggles/{key}`

#### FeatureTogglePanel Component

**Props:** `modelValue: boolean` (v-model for visibility)  
**Emits:** `update:modelValue`

**UI Structure:**
```
┌──────────────────────────────────────────┐
│ Feature Toggles                     [X]  │
├──────────────────────────────────────────┤
│  Group Visibility          [ Toggle ON ] │
│  Scheduled Updates         [ Toggle OFF] │
│  Share Link                [ Toggle ON ] │
└──────────────────────────────────────────┘
```

- Position: appears directly below the RSS icon in Settings page header (or as a dropdown panel)
- Each row: label (left) + toggle switch (right)
- Close button dismisses panel and resets `isRevealed = false`
- Uses existing Tailwind + component library styling
- Dark mode support required

### 5.3 Integration with SettingsPage.vue

In `SettingsPage.vue`:
1. Import and initialize `useFeatureToggle()` composable
2. Add click handler to the RSS icon in the Settings header
3. Mount `<FeatureTogglePanel v-model:open="isRevealed" />` when `isRevealed = true`

**Implementation approach:**  
The RSS icon click handler should be in the Settings page itself (not in MainLayout) to keep concerns separated. The existing MainLayout's `handleFeedIconClick` remains untouched — it only handles clicks on the Feed page.

### 5.4 i18n Keys

Add to `web/src/locales/en.json` and `web/src/locales/zh.json`:

```json
{
  "settings": {
    "feature_toggles": {
      "title": "Feature Toggles",
      "group_visibility": "Group Visibility",
      "timer": "Scheduled Updates",
      "share_link": "Share Link"
    }
  }
}
```

**Note on translation display:** Per user preference, translations should show only the translated text without the original key prefix (e.g., "群組顯示" not "SETTINGS.FEATURE_TOGGLES.GROUP_VISIBILITY — 群組顯示").

---

## 6. Interaction Flow

### 6.1 Reveal Panel (Happy Path)

1. User navigates to Settings page (`/settings`)
2. User taps RSS icon in the Settings header 10 times within 3 seconds
3. `FeatureTogglePanel` fades in below the RSS icon
4. Panel shows current toggle states (loaded from API)
5. User toggles one or more features
6. Each toggle change fires a PATCH request and updates DB
7. User clicks X or navigates away → panel hides

### 6.2 Timeout Behavior

- User taps 5 times, then pauses for 4 seconds → counter resets to 0 (did not reach 10)
- User taps 9 times, then navigates away → counter resets on page leave

### 6.3 Persistence

- Toggle values persist across page reloads and browser restarts
- Anonymous users' toggles are tied to `session_id` (stored in httpOnly cookie or localStorage)

---

## 7. File Changes Summary

### Backend (Python)

| File | Action | Notes |
|------|--------|-------|
| `src/models/feature_toggle.py` | Create | New ORM model |
| `src/models/__init__.py` | Modify | Export `FeatureToggle` |
| `src/schemas/feature_toggle.py` | Create | Pydantic schemas |
| `src/services/feature_toggle_service.py` | Create | Business logic |
| `src/api/routes/feature_toggles.py` | Create | FastAPI routes |
| `src/api/routes/__init__.py` | Modify | Register new router |
| `src/main.py` | Modify | Include new router |
| `alembic/versions/xxxx_add_feature_toggles.py` | Create | Migration |
| `tests/test_feature_toggles.py` | Create | Backend unit tests |

### Frontend (Vue/TypeScript)

| File | Action | Notes |
|------|--------|-------|
| `web/src/api/feature-toggles.ts` | Create | API client |
| `web/src/composables/useFeatureToggle.ts` | Create | Logic + state |
| `web/src/components/FeatureTogglePanel.vue` | Create | UI component |
| `web/src/pages/SettingsPage.vue` | Modify | Add click handler + panel |
| `web/src/locales/en.json` | Modify | Add i18n keys |
| `web/src/locales/zh.json` | Modify | Add i18n keys |
| `web/src/__tests__/useFeatureToggle.test.ts` | Create | Frontend unit tests |

---

## 8. TDD + BDD Test Strategy

### 8.1 Unit Tests (TDD — write first, must fail before implementation)

**Backend (`tests/`):**
- `test_feature_toggle_repo_upsert_insert` — first call inserts row
- `test_feature_toggle_repo_upsert_update` — second call updates existing row
- `test_feature_toggle_service_get_all_defaults` — missing keys return `enabled=false`
- `test_feature_toggle_endpoint_get` — returns all 3 toggles
- `test_feature_toggle_endpoint_patch_valid` — updates and returns toggle
- `test_feature_toggle_endpoint_patch_invalid_key` — returns 404

**Frontend (`web/src/__tests__/`):**
- `useFeatureToggle.test.ts`:
  - `clickCount increments on handleIconClick`
  - `counter resets after 3s of inactivity`
  - `isRevealed becomes true after 10 clicks`
  - `API get called on init`
  - `PATCH called when toggleFeature invoked`

### 8.2 BDD / E2E Tests (Playwright)

File: `web/e2e/feature-toggles.spec.ts`

| Scenario | Steps |
|----------|-------|
| `panel hidden by default` | Navigate to Settings; assert panel NOT visible |
| `reveal panel by 10 taps` | Tap RSS icon 10x within 3s; assert panel visible |
| `toggle persists after reload` | Toggle "Group Visibility" ON; reload page; assert still ON |
| `timeout resets counter` | Tap 5x; wait 4s; tap 5 more; assert panel NOT revealed (counter reset) |

---

## 9. Acceptance Criteria

- [ ] Panel reveals after exactly **10 taps** on the Settings page RSS icon within a **3-second** window
- [ ] Fewer than 10 taps with 3+ seconds gap does NOT reveal the panel
- [ ] Panel shows three labeled toggles: Group Visibility, Scheduled Updates, Share Link
- [ ] Toggling any switch calls the API and persists to DB
- [ ] On reload, panel reflects saved toggle values (not defaults)
- [ ] All existing functionality (Feed page DebugDialog, other features) is unaffected
- [ ] i18n strings display translated text only (no key prefix)
- [ ] All code edits are performed via Claude Code using prompt that includes `use context7`
- [ ] TDD: all unit tests written first and fail before implementation
- [ ] BDD: Playwright E2E scenarios pass end-to-end

---

## 10. Development Workflow

1. **Create this spec** (current step) → save to `docs/spec/improve/feature-toggle-panel.md`
2. **User reviews spec** — no code changes yet
3. **Write TDD unit tests** — all must fail initially
4. **Write BDD E2E tests** — all must fail initially
5. **Implement backend** — models, migrations, service, routes
6. **Implement frontend** — composable, component, page integration
7. **Run full test suite** — all tests must pass
8. **User verifies** — manual testing on running application

**Important:** All implementation work must be done using Claude Code with `use context7` appended to the prompt. Do not implement features directly.