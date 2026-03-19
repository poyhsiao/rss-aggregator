# RSS Aggregator Frontend Design Document

Date: 2026-03-19

## Overview

A Vue 3 based SaaS web application frontend for the RSS Aggregator backend, featuring clean & minimalist design, responsive layout, PWA support, and i18n support (Chinese/English).

## Technical Stack

| Technology | Version | Purpose |
|------------|---------|---------|
| Vue 3 | ^3.4.0 | Core framework (Composition API) |
| Vite | ^5.2.0 | Build tool |
| Pinia | ^2.1.0 | State management |
| Vue Router | ^4.3.0 | Routing |
| Tailwind CSS | ^3.4.0 | Styling |
| radix-vue | ^1.9.0 | UI component primitives (shadcn/ui) |
| Axios | ^1.6.0 | HTTP client |
| vue-i18n | ^9.10.0 | Internationalization |
| TypeScript | ^5.4.0 | Type safety |

## Project Structure

```
rss-aggregator/
├── src/                      # Backend Python code (existing)
├── web/                      # Frontend Vue 3 application
│   ├── public/
│   │   ├── favicon.ico
│   │   ├── manifest.json     # PWA manifest
│   │   └── icons/            # PWA icons
│   ├── src/
│   │   ├── api/              # API layer
│   │   │   ├── index.ts      # Axios instance config
│   │   │   ├── feed.ts       # Feed API
│   │   │   ├── sources.ts    # Sources API
│   │   │   ├── keys.ts       # Keys API
│   │   │   ├── stats.ts      # Stats API
│   │   │   └── logs.ts       # Logs API
│   │   ├── components/       # Shared UI components
│   │   │   ├── ui/           # shadcn/ui components
│   │   │   └── common/       # Custom shared components
│   │   ├── composables/      # Vue Composables
│   │   │   ├── useAuth.ts    # Authentication logic
│   │   │   └── useTheme.ts   # Theme switching
│   │   ├── layouts/          # Layout components
│   │   │   └── MainLayout.vue
│   │   ├── pages/            # Page components
│   │   │   ├── FeedPage.vue
│   │   │   ├── SourcesPage.vue
│   │   │   ├── KeysPage.vue
│   │   │   ├── StatsPage.vue
│   │   │   └── LogsPage.vue
│   │   ├── stores/           # Pinia Stores
│   │   │   ├── auth.ts       # Authentication state
│   │   │   └── settings.ts   # User settings
│   │   ├── router/           # Vue Router
│   │   │   └── index.ts
│   │   ├── locales/          # i18n language files
│   │   │   ├── zh.json
│   │   │   └── en.json
│   │   ├── styles/           # Global styles
│   │   ├── utils/            # Utility functions
│   │   ├── types/            # TypeScript type definitions
│   │   ├── App.vue
│   │   └── main.ts
│   ├── index.html
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   ├── tsconfig.json
│   └── package.json
├── docs/
├── tests/
└── README.md
```

## Design Tokens

### Color System (Clean & Minimalist Style)

```javascript
// tailwind.config.js - Custom colors
colors: {
  // Primary - Soft green
  primary: {
    50: '#f0fdf4',
    100: '#dcfce7',
    200: '#bbf7d0',
    300: '#86efac',
    400: '#4ade80',
    500: '#22c55e',
    600: '#16a34a',
    700: '#15803d',
    800: '#166534',
    900: '#14532d',
  },
  // Secondary - Soft blue
  secondary: {
    50: '#f0f9ff',
    100: '#e0f2fe',
    200: '#bae6fd',
    300: '#7dd3fc',
    400: '#38bdf8',
    500: '#0ea5e9',
    600: '#0284c7',
  },
  // Neutral - Warm gray
  neutral: {
    50: '#fafafa',
    100: '#f5f5f5',
    200: '#e5e5e5',
    300: '#d4d4d4',
    400: '#a3a3a3',
    500: '#737373',
    600: '#525252',
    700: '#404040',
    800: '#262626',
    900: '#171717',
  },
}
```

### Border Radius

```javascript
borderRadius: {
  'sm': '0.375rem',    // Small elements
  'md': '0.5rem',      // Buttons, inputs
  'lg': '0.75rem',     // Cards
  'xl': '1rem',        // Large cards
  '2xl': '1.5rem',     // Modal
}
```

### Spacing Principles

- Card padding: `p-6` (24px)
- Card gap: `gap-4` or `gap-6` (16px / 24px)
- Page padding: `p-4` (mobile) / `p-8` (desktop)
- Sidebar width: `w-64` (256px)

## Authentication Flow

```
User enters application
       ↓
Check localStorage for API Key
       ↓
    ┌─────────────────┐
    │   Has Key?      │
    └─────────────────┘
       ↓           ↓
      Yes          No
       ↓           ↓
Call API verify   Show Dialog
       ↓           ↓
    ┌─────────┐  Enter Key
    │ Valid?  │     ↓
    └─────────┘  Call API verify
       ↓           ↓
   Yes ↓  No       ↓
   ↓      ↓    ┌─────────┐
Enter App  Clear  │ Success?│
          Key   └─────────┘
           ↓      ↓    ↓
        Show   Store  Show
        Dialog  State  Error
                ↓
             Enter App
```

## Layout Structure

### Desktop (≥768px)

```
┌─────────────────────────────────────────────────────────┐
│  Header (Top bar)                                       │
│  ┌───────────────────────────────────────────────────┐  │
│  │  📰 RSS Aggregator        [🌙/☀️] [EN/中]         │  │
│  └───────────────────────────────────────────────────┘  │
├──────────┬──────────────────────────────────────────────┤
│ Sidebar  │  Main Content                               │
│          │                                              │
│  📰 Feed │  ┌────────────────────────────────────────┐  │
│          │  │                                        │  │
│  📡 Src  │  │         Page Content                   │  │
│          │  │                                        │  │
│  🔑 Keys │  │                                        │  │
│          │  │                                        │  │
│  📊 Stats│  │                                        │  │
│          │  │                                        │  │
│  📝 Logs │  └────────────────────────────────────────┘  │
│          │                                              │
└──────────┴──────────────────────────────────────────────┘
```

### Mobile (<768px)

- Hide sidebar
- Show bottom navigation bar
- Main content fills viewport

## Pages Overview

### 1. Feed Page

- Display aggregated RSS articles in card format
- Filter by time range and keywords
- Sort by time or source
- Each card shows: title, summary, source, published time

### 2. Sources Page

- List all RSS sources with status indicator
- CRUD operations for sources
- Manual refresh button per source

### 3. Keys Page

- Display API keys with masked display
- Create new keys
- Enable/disable keys

### 4. Stats Page

- Summary cards: total requests, successful/failed fetches
- Daily trend chart

### 5. Logs Page

- Error log list with error type and message
- Timestamp for each entry

## API Integration

### Request Interceptor

```typescript
api.interceptors.request.use((config) => {
  const authStore = useAuthStore()
  if (authStore.apiKey) {
    config.headers['X-API-Key'] = authStore.apiKey
  }
  return config
})
```

### Response Interceptor

```typescript
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      const authStore = useAuthStore()
      authStore.logout()
    }
    return Promise.reject(error)
  }
)
```

### Error Handling

| HTTP Status | Action |
|-------------|--------|
| 401 | Clear API Key, show auth dialog |
| 429 | Show "Rate limit exceeded" toast |
| 500 | Show "Server error" toast |
| Network Error | Show "Network error" toast |

## i18n Support

### Supported Languages

- Chinese Traditional (zh)
- English (en)

### Language Detection

1. Check localStorage for saved preference
2. Detect browser language (zh → Chinese, others → English)
3. Default to Chinese Traditional

### File Structure

```
src/locales/
├── zh.json      # Chinese Traditional
└── en.json      # English
```

## Theme Switching

### Implementation

- Tailwind CSS `darkMode: 'class'`
- Toggle `dark` class on `<html>` element

### Theme Detection

1. Check localStorage for saved preference
2. Detect system preference (`prefers-color-scheme`)
3. Default to system preference

### Theme Persistence

- Save user's choice to localStorage
- Saved preference takes priority over system preference

## PWA Configuration

### Features

- Install to home screen
- App icon and splash screen
- Theme color

### manifest.json

```json
{
  "name": "RSS Aggregator",
  "short_name": "RSS Agg",
  "description": "RSS Feed Aggregator Web Application",
  "theme_color": "#22c55e",
  "background_color": "#fafafa",
  "display": "standalone",
  "orientation": "portrait-primary",
  "scope": "/",
  "start_url": "/"
}
```

### Icon Sizes

- 72x72, 96x96, 128x128, 144x144, 152x152, 192x192, 384x384, 512x512

## Dependencies

### Production Dependencies

| Package | Version | License |
|---------|---------|---------|
| vue | ^3.4.0 | MIT |
| vue-router | ^4.3.0 | MIT |
| pinia | ^2.1.0 | MIT |
| axios | ^1.6.0 | MIT |
| vue-i18n | ^9.10.0 | MIT |
| radix-vue | ^1.9.0 | MIT |
| class-variance-authority | ^0.7.0 | MIT |
| clsx | ^2.1.0 | MIT |
| tailwind-merge | ^2.2.0 | MIT |
| lucide-vue-next | ^0.359.0 | ISC |

### Development Dependencies

| Package | Version | License |
|---------|---------|---------|
| @vitejs/plugin-vue | ^5.0.0 | MIT |
| vite | ^5.2.0 | MIT |
| typescript | ^5.4.0 | Apache-2.0 |
| vue-tsc | ^2.0.0 | MIT |
| tailwindcss | ^3.4.0 | MIT |
| postcss | ^8.4.0 | MIT |
| autoprefixer | ^10.4.0 | MIT |
| @types/node | ^20.11.0 | MIT |
| eslint | ^8.57.0 | MIT |

## Design Decisions Summary

| Item | Decision |
|------|----------|
| Project Structure | Monorepo, frontend in `web/` |
| API Key Persistence | Store in localStorage |
| Pages | Feed, Sources, Keys, Stats, Logs (5 pages) |
| Navigation | Single-level navigation |
| Feed Display | Card-based list |
| PWA | Basic PWA (install to desktop) |
| Architecture | Standard SaaS architecture (layered) |
| Visual Style | Clean & Minimalist (soft green, rounded corners, whitespace) |
| Responsive | Desktop sidebar / Mobile bottom nav |