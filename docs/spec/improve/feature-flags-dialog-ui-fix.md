# FeatureFlagsDialog UI Fix Specification

## Issue Summary

**Problem**: FeatureFlagsDialog appears too small, making buttons and controls hidden/not accessible.

**Root Cause**:
- Dialog uses `size="lg"` which has max-width of `32rem` (512px)
- Content has multiple rows (2 toggles + cascade warning + footer) which overflow vertically
- On smaller viewports, content clips outside the visible area

---

## UI Fix Requirements

### 1. Increase Dialog Width
- Change from `size="lg"` to `size="xl"` (or `2xl` for better spacing)
- Provide minimum width constraint to ensure readability

### 2. Improve Internal Layout
- Optimize vertical spacing between elements
- Ensure footer is always visible
- Make toggle switches more compact but accessible

### 3. Responsive Behavior
- On mobile (< 640px), dialog should use almost full width with proper padding
- Content should scroll properly if needed

---

## Changes to Apply

### File: `web/src/components/FeatureFlagsDialog.vue`

| Change | Before | After |
|--------|--------|-------|
| Dialog size | `size="lg"` | `size="xl"` |
| Container padding | `p-4` | `p-6` (consistent with other dialogs) |
| Toggle row spacing | `gap-3` | `gap-4` (more breathing room) |
| Footer button | `size="sm"` | Default size, centered |

### File: `web/src/components/ui/Dialog.vue`

| Change | Before | After |
|--------|--------|-------|
| Mobile width | `w-full` (implicit) | `w-full` with `min-w-[320px]` |
| Content overflow | `overflow-auto` | `overflow-y-auto` (vertical only) |

---

## Testing Requirements

### E2E Tests (`web/e2e/feature-flags.spec.ts`)

1. **Dialog Opens Correctly**: Verify dialog is visible and centered
2. **Dialog Size**: Verify dialog has adequate width (at least 400px)
3. **Content Visibility**: Verify all toggles and buttons are visible without scrolling on standard viewports
4. **Footer Button Accessible**: Verify confirm button is always reachable
5. **Responsive**: Verify dialog adapts properly on mobile viewport (375px width)

### BDD Scenarios

```gherkin
Scenario: Feature flags dialog is properly sized
  Given user is on the Settings page
  When user clicks the RSS icon 10 times
  Then the FeatureFlagsDialog opens
  And the dialog width is at least 400px
  And all toggle switches are visible
  And the confirm button is visible and clickable

Scenario: Dialog handles cascade warning without overflow
  Given the FeatureFlagsDialog is open
  When user toggles off Groups Feature
  Then the cascade warning appears
  And both confirm/cancel buttons are visible
  And no horizontal scrollbar appears
```

---

## Implementation Steps

1. Update `FeatureFlagsDialog.vue` - change size to `xl`
2. Update `Dialog.vue` - add minimum width constraint
3. Run E2E tests to verify fix
4. Verify with Docker deployment

---

## Files to Modify

| File | Changes |
|------|---------|
| `web/src/components/FeatureFlagsDialog.vue` | Change `size="lg"` to `size="xl"` |
| `web/src/components/ui/Dialog.vue` | Add `min-w-[360px]` for better sizing |