# RSS Aggregator

A FastAPI-based RSS feed aggregator with source management, scheduled fetching, filtering, and API key authentication.

## Features

- Aggregate multiple RSS/Atom feeds into a single output
- Automatic URL cleaning (removes Google Alert tracking prefixes)
- Duplicate detection by link
- Filter by time range and keywords
- Sort by publication time or source name
- Source management via API or environment variables
- Scheduled background fetching
- Daily statistics tracking
- API key authentication and rate limiting
- **Desktop application support** (Windows, macOS, Linux)

## Installation

### Desktop Application (Recommended)

Download the latest release for your platform:

| Platform | Download |
|----------|----------|
| Windows | `RSS-Aggregator_x.x.x_x64.msi` |
| macOS (Intel) | `RSS-Aggregator_x.x.x_x64.dmg` |
| macOS (Apple Silicon) | `RSS-Aggregator_x.x.x_aarch64.dmg` |
| Linux | `rss-aggregator_x.x.x_amd64.deb` or `.AppImage` |

**Desktop Features:**
- No Docker required
- No TCP port binding
- Portable data storage (`./data/` directory)
- First-run setup wizard
- Import/export database

### Docker

```bash
docker-compose up
```

### Local Development

1. Install dependencies:
   ```bash
   uv sync
   ```

2. Set up environment:
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

3. Run migrations:
   ```bash
   uv run alembic upgrade head
   ```

4. Start the server:
   ```bash
   uv run uvicorn src.main:app --reload
   ```

## Building Desktop Application

### Prerequisites

- Rust 1.70+
- Node.js 18+
- Python 3.12+
- uv (Python package manager)

### Build Commands

```bash
# Development build (frontend + sidecar)
./scripts/build-all.sh dev

# Full release build
./scripts/build-all.sh release

# Build only sidecar
./scripts/build-all.sh sidecar

# Build only frontend
./scripts/build-all.sh frontend
```

### Development Mode

```bash
# Start Tauri development server
cd src-tauri && cargo tauri dev
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/api/v1/feed` | GET | Get aggregated RSS feed |
| `/api/v1/sources` | GET, POST | List/create sources |
| `/api/v1/sources/{id}` | GET, PUT, DELETE | Manage source |
| `/api/v1/sources/{id}/feed` | GET | Get feed for specific source |
| `/api/v1/keys` | GET, POST | List/create API keys |
| `/api/v1/stats` | GET | Get daily statistics |
| `/api/v1/logs` | GET | Get error logs |

### Feed Endpoint Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `format` | string | `rss` | Output format (`rss`, `json`, `markdown`) |
| `sort_by` | string | `published_at` | Sort field (`published_at` or `source`) |
| `sort_order` | string | `desc` | Sort direction (`asc` or `desc`) |
| `valid_time` | int | - | Time range in hours |
| `keywords` | string | - | Semicolon-separated keywords for filtering |

### Stats Endpoint Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `days` | int | `7` | Number of days to retrieve (1-365) |

## URL Cleaning

Google Alert feed URLs are automatically cleaned to remove tracking parameters:

**Before:**
```
https://www.google.com/url?rct=j&sa=t&url=https://example.com/article&ct=ga&...
```

**After:**
```
https://example.com/article
```

## Configuration

See `.env.example` for all available configuration options.

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | SQLite database path | `sqlite+aiosqlite:///./data/rss.db` |
| `REQUIRE_API_KEY` | Enable API key requirement | `true` |
| `DEFAULT_API_KEY` | Default API key | - |
| `SCHEDULER_ENABLED` | Enable background fetching | `true` |
| `SCHEDULER_INTERVAL` | Scheduler check interval in seconds | `60` |
| `APP_TIMEZONE` | Application timezone for time display | `Asia/Taipei` |
| `APP_DEBUG` | Enable debug mode | `false` |
| `ALLOWED_ORIGINS` | CORS allowed origins (comma-separated, empty for all) | `*` |
| `DEFAULT_FETCH_INTERVAL` | Default fetch interval for new sources (seconds) | `0` |
| `DEFAULT_SOURCES` | Comma-separated RSS URLs | - |

## Security

- **XSS Protection**: All user-generated content is sanitized with DOMPurify
- **API Key Storage**: Keys stored in sessionStorage (cleared on browser close)
- **Docker**: Container runs as non-root user
- **CORS**: Configurable allowed origins for production deployments

## Frontend

A Vue 3 web application is available in the `web/` directory.

### Quick Start

```bash
cd web
pnpm install
pnpm dev
```

### Build for Production

```bash
pnpm build
```

### Generate PWA Icons

```bash
pnpm generate-icons
```

### Features

- **API Key Authentication**: Secure access with localStorage persistence
- **5 Pages**: Feed, Sources, Keys, Stats, Logs
- **Dark/Light Theme**: System preference detection with manual toggle
- **i18n**: Chinese/English support
- **PWA**: Installable on desktop and mobile
- **Responsive**: Desktop sidebar + Mobile bottom navigation

### Tech Stack

| Category | Technology |
|----------|------------|
| Framework | Vue 3 + TypeScript |
| Build | Vite |
| Styling | Tailwind CSS |
| State | Pinia |
| Routing | Vue Router |
| i18n | vue-i18n |
| UI Components | radix-vue |
| Charts | Chart.js + vue-chartjs |
| Validation | Zod |
| Icons | Lucide Icons |

### Project Structure

```
web/
├── src/
│   ├── api/           # Axios instance + API modules
│   ├── components/    # UI components + dialogs
│   ├── composables/   # Vue composables (useAuth, useTheme, etc.)
│   ├── locales/       # i18n JSON files
│   ├── pages/         # Route page components
│   ├── stores/        # Pinia stores
│   ├── styles/        # Global CSS
│   └── utils/         # Helper functions
├── public/
│   ├── icons/         # PWA icons (generated)
│   └── manifest.json  # PWA manifest
└── scripts/           # Build scripts
```

### Configuration

Set the API base URL in `.env`:

```bash
VITE_API_BASE_URL=http://localhost:8000
```

## License

Apache-2.0