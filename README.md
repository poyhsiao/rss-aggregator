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

## Quick Start

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

### Docker

```bash
docker-compose up
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/api/v1/feed` | GET | Get aggregated RSS feed |
| `/api/v1/sources` | GET, POST | List/create sources |
| `/api/v1/sources/{id}` | GET, PUT, DELETE | Manage source |
| `/api/v1/keys` | GET, POST | List/create API keys |
| `/api/v1/stats` | GET | Get daily statistics |
| `/api/v1/logs` | GET | Get error logs |

### Feed Endpoint Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
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
| `SCHEDULER_INTERVAL` | Fetch interval in seconds | `60` |
| `DEFAULT_SOURCES` | Comma-separated RSS URLs | - |

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