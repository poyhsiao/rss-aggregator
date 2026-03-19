# RSS Aggregator Frontend Tasks

Date: 2026-03-19

## Overview

Implementation tasks for the RSS Aggregator Vue 3 frontend application.

---

## Phase 1: Project Setup

### 1.1 Initialize Project

- [ ] Create `web/` directory in project root
- [ ] Initialize Vite + Vue 3 + TypeScript project
- [ ] Configure `vite.config.ts` with path aliases
- [ ] Configure `tsconfig.json` with strict mode
- [ ] Set up ESLint configuration

### 1.2 Install Dependencies

- [ ] Install core dependencies: vue, vue-router, pinia, axios, vue-i18n
- [ ] Install UI dependencies: radix-vue, tailwindcss, lucide-vue-next
- [ ] Install utility dependencies: clsx, tailwind-merge, class-variance-authority
- [ ] Install dev dependencies: typescript, vue-tsc, @types/node

### 1.3 Configure Tailwind CSS

- [ ] Create `tailwind.config.js` with custom colors
- [ ] Configure dark mode: `darkMode: 'class'`
- [ ] Set up PostCSS configuration
- [ ] Create global styles file

---

## Phase 2: Core Infrastructure

### 2.1 API Layer

- [ ] Create `src/api/index.ts` - Axios instance with interceptors
- [ ] Create `src/api/feed.ts` - Feed API functions
- [ ] Create `src/api/sources.ts` - Sources API functions
- [ ] Create `src/api/keys.ts` - Keys API functions
- [ ] Create `src/api/stats.ts` - Stats API functions
- [ ] Create `src/api/logs.ts` - Logs API functions

### 2.2 Type Definitions

- [ ] Create `src/types/feed.ts` - Feed item types
- [ ] Create `src/types/source.ts` - Source types
- [ ] Create `src/types/key.ts` - API key types
- [ ] Create `src/types/stats.ts` - Statistics types
- [ ] Create `src/types/log.ts` - Error log types
- [ ] Create `src/types/api.ts` - Common API response types

### 2.3 Pinia Stores

- [ ] Create `src/stores/auth.ts` - Authentication state and actions
- [ ] Create `src/stores/settings.ts` - User settings (theme, locale)

### 2.4 Composables

- [ ] Create `src/composables/useAuth.ts` - Auth logic
- [ ] Create `src/composables/useTheme.ts` - Theme switching
- [ ] Create `src/composables/useLocale.ts` - Locale management

---

## Phase 3: Router & Layout

### 3.1 Vue Router Setup

- [ ] Create `src/router/index.ts` with routes
- [ ] Configure route guards for authentication
- [ ] Set up 404 fallback route

### 3.2 Layout Component

- [ ] Create `src/layouts/MainLayout.vue`
- [ ] Implement desktop sidebar navigation
- [ ] Implement mobile bottom navigation
- [ ] Implement header with logo and controls

### 3.3 App Entry

- [ ] Update `src/App.vue` with layout structure
- [ ] Initialize Pinia, Router, i18n in `src/main.ts`

---

## Phase 4: i18n Setup

### 4.1 Language Files

- [ ] Create `src/locales/zh.json` - Chinese Traditional
- [ ] Create `src/locales/en.json` - English

### 4.2 i18n Configuration

- [ ] Configure vue-i18n instance
- [ ] Implement language detection logic
- [ ] Implement language persistence

---

## Phase 5: UI Components

### 5.1 shadcn/ui Components

- [ ] Set up radix-vue primitives
- [ ] Create Button component
- [ ] Create Input component
- [ ] Create Select component
- [ ] Create Dialog component
- [ ] Create Card components
- [ ] Create Badge component
- [ ] Create Toast component

### 5.2 Custom Components

- [ ] Create `src/components/common/FeedCard.vue`
- [ ] Create `src/components/common/SourceCard.vue`
- [ ] Create `src/components/common/StatCard.vue`
- [ ] Create `src/components/common/EmptyState.vue`

---

## Phase 6: Authentication

### 6.1 Auth Dialog

- [ ] Create `src/components/AuthDialog.vue`
- [ ] Implement API Key input with validation
- [ ] Implement error message display
- [ ] Implement loading state during verification

### 6.2 Auth Integration

- [ ] Integrate auth check in router guard
- [ ] Show auth dialog when not authenticated
- [ ] Store valid API key in localStorage

---

## Phase 7: Pages Implementation

### 7.1 Feed Page

- [ ] Create `src/pages/FeedPage.vue`
- [ ] Implement article card list
- [ ] Implement sort controls
- [ ] Implement keyword search
- [ ] Implement empty state

### 7.2 Sources Page

- [ ] Create `src/pages/SourcesPage.vue`
- [ ] Implement source list display
- [ ] Implement add source dialog
- [ ] Implement edit source functionality
- [ ] Implement delete source with confirmation
- [ ] Implement manual refresh

### 7.3 Keys Page

- [ ] Create `src/pages/KeysPage.vue`
- [ ] Implement key list display
- [ ] Implement add key dialog
- [ ] Implement delete key with confirmation

### 7.4 Stats Page

- [ ] Create `src/pages/StatsPage.vue`
- [ ] Implement summary cards
- [ ] Implement trend chart (optional)

### 7.5 Logs Page

- [ ] Create `src/pages/LogsPage.vue`
- [ ] Implement error log list
- [ ] Implement empty state

---

## Phase 8: Theme & PWA

### 8.1 Theme System

- [ ] Implement dark/light theme toggle
- [ ] Implement system preference detection
- [ ] Implement theme persistence

### 8.2 PWA Configuration

- [ ] Create `public/manifest.json`
- [ ] Create PWA icons (multiple sizes)
- [ ] Add PWA meta tags to `index.html`
- [ ] Configure theme colors

---

## Phase 9: Final Integration

### 9.1 Error Handling

- [ ] Implement global error handler
- [ ] Implement toast notifications
- [ ] Implement 401 auto-logout

### 9.2 Polish

- [ ] Add loading states to all async operations
- [ ] Add skeleton loading (optional)
- [ ] Test responsive design on various screen sizes
- [ ] Test dark/light theme on all pages
- [ ] Test i18n on all pages

### 9.3 Build & Deploy

- [ ] Test production build
- [ ] Verify all environment variables
- [ ] Update project README with frontend instructions

---

## Dependencies Between Tasks

```
Phase 1 (Setup)
    ↓
Phase 2 (Infrastructure) ← Phase 4 (i18n)
    ↓
Phase 3 (Router/Layout)
    ↓
Phase 5 (UI Components)
    ↓
Phase 6 (Auth) ← Phase 5
    ↓
Phase 7 (Pages) ← Phase 5, Phase 6
    ↓
Phase 8 (Theme/PWA) ← Phase 7
    ↓
Phase 9 (Integration)
```

---

## Estimated Effort

| Phase | Estimated Hours |
|-------|-----------------|
| Phase 1: Setup | 2-3 |
| Phase 2: Infrastructure | 3-4 |
| Phase 3: Router & Layout | 2-3 |
| Phase 4: i18n | 1-2 |
| Phase 5: UI Components | 4-5 |
| Phase 6: Authentication | 2-3 |
| Phase 7: Pages | 6-8 |
| Phase 8: Theme & PWA | 2-3 |
| Phase 9: Integration | 2-3 |
| **Total** | **24-34 hours** |

---

## Priority Order

1. **High Priority**: Phase 1-6 (Core functionality)
2. **Medium Priority**: Phase 7 (Pages implementation)
3. **Low Priority**: Phase 8-9 (Polish and PWA)