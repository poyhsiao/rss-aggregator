# Feature Flags Implementation Plan

## Overview

Implement a feature flags system for RSS-collection with hybrid localStorage + Backend API storage. Features are toggled via a secret Settings dialog (10 clicks on logo) on the Settings page.

---

## Task Breakdown

### Task 1: Backend - Feature Flag Model & API

**Goal**: Create backend model and REST API for feature flags

**TDD Steps**:
1. [ ] Write failing test: `tests/api/test_feature_flags.py`
   - Test GET /api/feature-flags returns default flags
   - Test PATCH /api/feature-flags updates flags
   - Test flags persist across restarts
2. [ ] Run tests → verify they fail
3. [ ] Implement: `src/models/feature_flag.py` (SQLAlchemy model)
4. [ ] Implement: `src/api/routes/feature_flags.py` (REST API)
5. [ ] Register router in `src/main.py`
6. [ ] Run tests → verify they pass
7. [ ] Commit with message: `feat(api): add feature flags model and API endpoints`

---

### Task 2: Frontend - Feature Flags Store

**Goal**: Create Pinia store with hybrid localStorage + API loading

**TDD Steps**:
1. [ ] Write failing test: `web/src/__tests__/stores/featureFlags.test.ts`
   - Test initial loading state
   - Test toggle updates localStorage immediately
   - Test sync to backend API
   - Test loading from API on init
2. [ ] Run tests → verify they fail
3. [ ] Implement: `web/src/stores/featureFlags.ts`
4. [ ] Run tests → verify they pass
5. [ ] Commit with message: `feat(store): add feature flags store with hybrid sync`

---

### Task 3: Frontend - Feature Flags Dialog Component

**Goal**: Create dialog component for toggling feature flags

**TDD Steps**:
1. [ ] Write failing test: `web/src/__tests__/components/FeatureFlagsDialog.test.ts`
   - Test dialog opens after 10 clicks
   - Test all three toggles render
   - Test toggle changes value
2. [ ] Run tests → verify they fail
3. [ ] Implement: `web/src/components/FeatureFlagsDialog.vue`
4. [ ] Run tests → verify they pass
5. [ ] Commit with message: `feat(ui): add feature flags dialog component`

---

### Task 4: Frontend - Integrate Debug Dialog Trigger

**Goal**: Add Settings page with 10-click trigger for debug dialog

**TDD Steps**:
1. [ ] Write failing test: `web/src/__tests__/components/DebugDialogTrigger.test.ts`
   - Test click counter increments
   - Test dialog opens at 10 clicks
   - Test counter resets after dialog closes
2. [ ] Run tests → verify they fail
3. [ ] Update `web/src/layouts/MainLayout.vue` to add click counter and trigger
4. [ ] Run tests → verify they pass
5. [ ] Commit with message: `feat(ui): add 10-click debug dialog trigger to Settings page`

---

### Task 5: Frontend - Apply Feature Flags to Existing UI

**Goal**: Add v-if guards for Groups, Schedules, and Share Links features

**TDD Steps**:
1. [ ] Write failing e2e test: `web/e2e/feature-gates.spec.ts`
   - Test Groups section hidden when flag is OFF
   - Test Schedules section hidden when flag is OFF
   - Test Share preview hidden when flag is OFF
2. [ ] Run e2e tests → verify they fail
3. [ ] Update `web/src/pages/SourcesPage.vue` - add v-if for Groups section
4. [ ] Update `web/src/components/ScheduleSettings.vue` or related - add v-if for Schedules
5. [ ] Update share link components - add v-if for Share preview
6. [ ] Run e2e tests → verify they pass
7. [ ] Commit with message: `feat(ui): apply feature flag gates to Groups, Schedules, and Share Links`

---

### Task 6: Documentation & Version Bump

**Goal**: Update docs and version after all features complete

**Steps**:
1. [ ] Update `README.md` with feature flags documentation
2. [ ] Update `CHANGELOG.md` with new features
3. [ ] Bump version in relevant files (check `package.json`, `pyproject.toml`)
4. [ ] Commit with message: `docs: update README and CHANGELOG for feature flags`

---

## Dependencies

```
Task 1 (Backend) ──┬── No dependencies
                   │
Task 2 (Store) ───┼── Depends on Task 1 (API must exist)
                   │
Task 3 (Dialog) ───┼── Depends on Task 2 (store must exist)
                   │
Task 4 (Trigger) ──┼── Depends on Task 3 (dialog component)
                   │
Task 5 (Gates) ───┼── Depends on Task 2, 3, 4
                   │
Task 6 (Docs) ────┴── Depends on all previous tasks
```

---

## Test Commands

```bash
# Backend tests
pytest tests/api/test_feature_flags.py -v

# Frontend unit tests
cd web && pnpm test -- src/__tests__/stores/featureFlags.test.ts
pnpm test -- src/__tests__/components/FeatureFlagsDialog.test.ts

# Frontend e2e tests
pnpm exec playwright test e2e/feature-gates.spec.ts

# Full backend test suite
pytest tests/ -v

# Full frontend test suite
cd web && pnpm test
```

---

## File Changes Summary

### New Files

| File | Purpose |
|------|---------|
| `src/models/feature_flag.py` | SQLAlchemy model for feature flags |
| `src/api/routes/feature_flags.py` | REST API routes |
| `tests/api/test_feature_flags.py` | Backend tests |
| `web/src/stores/featureFlags.ts` | Pinia store |
| `web/src/__tests__/stores/featureFlags.test.ts` | Store tests |
| `web/src/components/FeatureFlagsDialog.vue` | Dialog component |
| `web/src/__tests__/components/FeatureFlagsDialog.test.ts` | Dialog tests |
| `web/e2e/feature-gates.spec.ts` | E2E gate tests |

### Modified Files

| File | Changes |
|------|---------|
| `src/main.py` | Register feature_flags router |
| `src/database.py` | Add FeatureFlag model to metadata |
| `web/src/layouts/MainLayout.vue` | Add click counter, trigger Settings page |
| `web/src/pages/SourcesPage.vue` | Add v-if guard for Groups |
| `web/src/components/ScheduleSettings.vue` | Add v-if guard for Schedules |
| `web/src/components/ShareLink*.vue` | Add v-if guard for Share preview |
| `web/src/locales/zh.json` | Add i18n strings |
| `web/src/locales/en.json` | Add i18n strings |

---

## Success Criteria

- [ ] All unit tests pass
- [ ] All e2e tests pass
- [ ] Feature flags dialog appears after 10 clicks on Settings page logo
- [ ] Toggles update localStorage immediately (UI responds instantly)
- [ ] Toggles sync to backend API (persists across devices)
- [ ] Groups section hidden when `feature_groups` is OFF
- [ ] Schedules section hidden when `feature_schedules` is OFF
- [ ] Share preview hidden when `feature_share_links` is OFF
- [ ] All three flags default to OFF
