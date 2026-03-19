# RSS Aggregator Frontend Requirements

Date: 2026-03-19

## Project Overview

Build a Vue 3 frontend web application for the RSS Aggregator backend API. The application should provide a clean, minimalist user interface for managing RSS feeds, viewing aggregated articles, and monitoring system statistics.

## Functional Requirements

### FR-001: Authentication

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-001-1 | Users must enter an API Key before accessing the application | High |
| FR-001-2 | System should validate API Key by calling backend API | High |
| FR-001-3 | Valid API Key should be stored in localStorage for persistence | High |
| FR-001-4 | Invalid API Key should show error message and allow retry | High |
| FR-001-5 | System should clear stored API Key on 401 response | Medium |
| FR-001-6 | Auth dialog should support password mode to hide API Key | Medium |

### FR-002: Feed Reader

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-002-1 | Display aggregated RSS articles in card-based list | High |
| FR-002-2 | Each card shows title, summary, source, published time | High |
| FR-002-3 | Support filtering by time range (hours) | Medium |
| FR-002-4 | Support filtering by keywords (semicolon-separated, OR logic) | Medium |
| FR-002-5 | Support sorting by published time (asc/desc) | Medium |
| FR-002-6 | Support sorting by source name (asc/desc) | Low |
| FR-002-7 | Click article card opens link in new tab | High |
| FR-002-8 | Show empty state when no articles available | Medium |

### FR-003: Sources Management

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-003-1 | Display list of all RSS sources | High |
| FR-003-2 | Show source status (active/inactive) | Medium |
| FR-003-3 | Show last fetched time per source | Low |
| FR-003-4 | Show last error message if any | Low |
| FR-003-5 | Create new source with name, URL, fetch interval | High |
| FR-003-6 | Delete source with confirmation | High |
| FR-003-7 | Manual refresh individual source | Medium |
| FR-003-8 | Manual refresh all sources | Low |

### FR-004: API Keys Management

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-004-1 | Display list of API keys with masked display | Medium |
| FR-004-2 | Show key name and active status | Medium |
| FR-004-3 | Create new API key | Medium |
| FR-004-4 | Delete API key with confirmation | Medium |

### FR-005: Statistics

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-005-1 | Display total requests count | Medium |
| FR-005-2 | Display successful fetches count | Medium |
| FR-005-3 | Display failed fetches count | Medium |
| FR-005-4 | Show daily trend chart for last N days | Low |
| FR-005-5 | Support configurable date range | Low |

### FR-006: Error Logs

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-006-1 | Display list of error logs | Medium |
| FR-006-2 | Show error type, message, and timestamp | Medium |
| FR-006-3 | Filter logs by source | Low |
| FR-006-4 | Pagination for large log lists | Low |
| FR-006-5 | Show empty state when no errors | Medium |

### FR-007: User Interface

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-007-1 | Responsive design for mobile and desktop | High |
| FR-007-2 | Desktop: Left sidebar navigation | High |
| FR-007-3 | Mobile: Bottom navigation bar | High |
| FR-007-4 | Support dark/light theme toggle | Medium |
| FR-007-5 | Detect and follow system theme preference | Medium |
| FR-007-6 | Support Chinese/English language toggle | Medium |
| FR-007-7 | Clean & minimalist visual style | High |

### FR-008: PWA

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-008-1 | Installable on mobile and desktop | Medium |
| FR-008-2 | App icon and splash screen | Medium |
| FR-008-3 | Theme color configuration | Low |

## Non-Functional Requirements

### NFR-001: Performance

| ID | Requirement | Metric |
|----|-------------|--------|
| NFR-001-1 | Initial page load time | < 3 seconds |
| NFR-001-2 | Route navigation time | < 300ms |
| NFR-001-3 | API response handling | < 100ms UI update |

### NFR-002: Compatibility

| ID | Requirement | Details |
|----|-------------|---------|
| NFR-002-1 | Browser support | Chrome, Firefox, Safari, Edge (latest 2 versions) |
| NFR-002-2 | Mobile support | iOS Safari, Android Chrome |
| NFR-002-3 | Screen sizes | 320px - 2560px |

### NFR-003: Accessibility

| ID | Requirement | Priority |
|----|-------------|----------|
| NFR-003-1 | Keyboard navigation support | Medium |
| NFR-003-2 | Proper ARIA labels | Medium |
| NFR-003-3 | Color contrast ratio > 4.5:1 | Medium |

### NFR-004: Code Quality

| ID | Requirement | Priority |
|----|-------------|----------|
| NFR-004-1 | TypeScript strict mode enabled | High |
| NFR-004-2 | ESLint configuration | High |
| NFR-004-3 | No `any` type usage | Medium |
| NFR-004-4 | Proper error handling | High |
| NFR-004-5 | Modular component structure | High |

### NFR-005: Security

| ID | Requirement | Priority |
|----|-------------|----------|
| NFR-005-1 | HTTPS only in production | High |
| NFR-005-2 | API Key masked in UI | Medium |
| NFR-005-3 | No sensitive data in URL | High |

## Constraints

### Technical Constraints

- Must use Vue 3 with Composition API
- Must use TypeScript
- Must use Tailwind CSS for styling
- Must use shadcn/ui components (via radix-vue)
- All dependencies must have MIT/BSD/Apache license
- Must follow existing project structure (Monorepo)

### Design Constraints

- Visual style: Clean & Minimalist
- Primary color: Soft green
- Border radius: Large (rounded-lg/2xl)
- Emoji icons: Use open-source emoji (no custom icons initially)

## Acceptance Criteria

### Authentication

- [ ] User can enter API Key in modal dialog
- [ ] Invalid key shows error message
- [ ] Valid key grants access to application
- [ ] Key persists across page reloads
- [ ] 401 response clears key and shows dialog

### Navigation

- [ ] All 5 pages accessible from navigation
- [ ] Active page highlighted in navigation
- [ ] Mobile shows bottom nav, desktop shows sidebar

### Feed Page

- [ ] Articles displayed in card format
- [ ] Sorting and filtering work correctly
- [ ] Empty state shown when no articles

### Sources Page

- [ ] CRUD operations work correctly
- [ ] Manual refresh triggers API call

### Theme & Language

- [ ] Dark/light theme toggles correctly
- [ ] System theme preference detected
- [ ] Language toggle changes all UI text

### Responsive

- [ ] Layout adapts to mobile/desktop
- [ ] All features accessible on mobile