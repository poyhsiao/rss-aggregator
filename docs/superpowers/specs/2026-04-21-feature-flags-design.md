# Feature Flags System Design

## Date
2026-04-21

## Status
Proposed

## Context

Users requested a feature flags/toggles system to control visibility and access to three existing features:
1. **群組設定功能 (Group Settings)** - Toggle to show/manage groups
2. **定時更新功能 (Scheduled Updates)** - Toggle to show/operate scheduled updates
3. **分享連結功能 (Share Links)** - Toggle for preview functionality in share links

All features are **default OFF** - completely hidden until explicitly enabled via the Settings Dialog.

## Trigger Mechanism

| Dialog | Trigger Location | Trigger Action |
|--------|-----------------|----------------|
| DebugDialog | Feed Page | Click logo 10 times |
| **SettingsDialog** | **Settings Page** | **Click logo 10 times** |

The click counter logic in `MainLayout.vue` will be updated to include Settings page:
```typescript
const handleLogoClick = () => {
  if (route.path === '/feed' || route.path === '/settings') {
    clickCount.value++
    // ...
  }
}
```

## Data Model

### Feature Flags (localStorage + Backend API)

```typescript
interface FeatureFlags {
  groupSettingsEnabled: boolean  // default: false
  scheduledUpdatesEnabled: boolean  // default: false
  shareLinksEnabled: boolean  // default: false
}
```

### API Endpoints (Backend)

| Method | Endpoint | Description |
|--------|---------|-------------|
| GET | `/settings/feature-flags` | Get all feature flags |
| PATCH | `/settings/feature-flags` | Update feature flags |

Request/Response:
```json
// GET /settings/feature-flags
{
  "group_settings_enabled": false,
  "scheduled_updates_enabled": false,
  "share_links_enabled": false
}

// PATCH /settings/feature-flags
{
  "group_settings_enabled": true
}
```

### Frontend Store (Pinia)

```typescript
// stores/featureFlags.ts
interface FeatureFlagsState {
  flags: FeatureFlags
  loaded: boolean
  loading: boolean
}
```

**Hybrid Loading Strategy**:
1. Immediately load from `localStorage` (fast, offline-first)
2. Async sync to Backend API
3. On API success, update `localStorage`
4. On API failure, keep localStorage value (eventual consistency)

## UI Components

### 1. FeatureFlagsDialog.vue

Location: `web/src/components/FeatureFlagsDialog.vue`

Structure:
```
┌─────────────────────────────────────┐
│  Feature Flags              [X]     │
├─────────────────────────────────────┤
│  ☑ Group Settings                   │
│    Show/hide source groups UI       │
│                                     │
│  ☐ Scheduled Updates                │
│    Enable scheduled fetching        │
│                                     │
│  ☐ Share Links                      │
│    Enable article sharing           │
├─────────────────────────────────────┤
│                    [Cancel] [Save]  │
└─────────────────────────────────────┘
```

Behavior:
- Changes apply immediately on save (no cancel rollback needed for visibility toggles)
- Dialog closes after save

### 2. Integration Points

#### Groups Visibility (groupSettingsEnabled)
- **Location**: `SourcesPage.vue`
- **Current**: Groups UI always visible
- **Change**: Wrap Groups section with `v-if="featureFlagsStore.flags.groupSettingsEnabled"`

#### Scheduled Updates (scheduledUpdatesEnabled)
- **Location**: Group edit form or inline schedule toggle
- **Current**: Schedule section always visible when editing a group
- **Change**: Wrap schedule section with `v-if="featureFlagsStore.flags.scheduledUpdatesEnabled"`

#### Share Links (shareLinksEnabled)
- **Location**: Article list item actions
- **Current**: Share button always visible
- **Change**: Wrap share action with `v-if="featureFlagsStore.flags.shareLinksEnabled"`

## Technical Implementation

### Backend Changes

1. **New Model**: `src/models/feature_flag.py`
```python
class FeatureFlag(Base):
    __tablename__ = "feature_flags"

    user_id: int = Column(Integer, primary_key=True)
    group_settings_enabled: bool = Column(Boolean, default=False)
    scheduled_updates_enabled: bool = Column(Boolean, default=False)
    share_links_enabled: bool = Column(Boolean, default=False)
```

2. **New API Route**: `src/api/routes/feature_flags.py`
   - GET `/settings/feature-flags` - returns user's flags (creates defaults if not exist)
   - PATCH `/settings/feature-flags` - updates flags

3. **Database Migration**: Add `feature_flags` table

### Frontend Changes

1. **New Store**: `web/src/stores/featureFlags.ts`
   - Pinia store with hybrid loading
   - `localStorage` for immediate access
   - API sync for persistence

2. **New Component**: `web/src/components/FeatureFlagsDialog.vue`

3. **Store Integration**: `web/src/stores/settings.ts`
   - Add featureFlags store to Settings store
   - Or create independent store if no coupling needed

4. **Component Integration**:
   - Update `MainLayout.vue` to add Settings page to click trigger
   - Update `SourcesPage.vue` to add `v-if` guards
   - Update article list/share components as needed

### File Changes Summary

| File | Change Type |
|------|-------------|
| `src/models/feature_flag.py` | New |
| `src/api/routes/feature_flags.py` | New |
| `src/database.py` | Update - add model |
| `alembic/versions/` | Migration |
| `web/src/stores/featureFlags.ts` | New |
| `web/src/components/FeatureFlagsDialog.vue` | New |
| `web/src/layouts/MainLayout.vue` | Modify - add settings trigger |
| `web/src/pages/SettingsPage.vue` | Modify - add dialog trigger |
| `web/src/pages/SourcesPage.vue` | Modify - add v-if guards |
| `web/src/components/article/*.vue` | Modify - add v-if guards for share |

## Testing Strategy (TDD)

### Unit Tests

1. **Backend**:
   - `tests/api/test_feature_flags.py`: API endpoint tests
   - `tests/models/test_feature_flag.py`: Model tests

2. **Frontend**:
   - `web/src/stores/__tests__/featureFlags.test.ts`: Store tests
   - `web/src/components/__tests__/FeatureFlagsDialog.test.ts`: Dialog tests

### E2E Tests (Playwright)

1. **Dialog Trigger**: Settings page → 10 clicks → Dialog appears
2. **Toggle Flow**: Enable flag → Navigate to feature → Feature visible → Disable → Feature hidden
3. **Persistence**: Enable flag → Reload → Flag still enabled

## Implementation Order

1. Backend: Feature flag model + API endpoints + migration
2. Frontend: Store with hybrid loading
3. Frontend: Dialog component
4. Frontend: Integration (MainLayout trigger, SourcesPage guards)
5. Frontend: Share links guards
6. Tests: Unit + E2E

## Open Questions

- [x] Trigger location (Settings page only)
- [x] Default state (all OFF)
- [x] Visibility approach (v-if guards)
- [x] Persistence (Hybrid: localStorage + Backend API)
- [ ] ~~Need user authentication for Backend API?~~ (Backend uses mock user for MVP, or assumes single-user)

## Related Documents

- `docs/superpowers/specs/2026-04-02-source-group-scheduled-update-design.md`
- `docs/superpowers/specs/2026-03-26-article-preview-feature-design.md`
