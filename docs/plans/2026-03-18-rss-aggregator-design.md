# RSS Aggregator Design Document

Date: 2026-03-18

## Overview

RSS Aggregator is a service that aggregates multiple RSS/Atom feeds, providing a unified RSS output with filtering, sorting, and time-based options.

## Requirements Summary

| Item | Decision |
|------|----------|
| Use Case | Personal use + Public API service |
| Access Control | API Key + Rate Limiting |
| Source Management | Persistent storage (SQLite) |
| Fetch Strategy | Scheduled fetching + Manual refresh |
| Fetch Frequency | Customizable per source |
| Error Handling | Simple retry N times |
| API Prefix | `/api/v1` (`/health` excluded) |
| Auth Scope | All endpoints require API Key |
| Keyword Filter | OR logic |
| Default Sort | Time descending (newest first) |
| Tech Stack | Python 3.12 + FastAPI + SQLite + uv |
| Deployment | Docker / Docker Compose / Cloud Run |

## Project Structure

```
rss-aggregator/
├── src/
│   ├── api/                    # API Layer
│   │   ├── __init__.py
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── feed.py         # /feed endpoint
│   │   │   ├── sources.py      # /sources endpoints
│   │   │   ├── keys.py         # /keys endpoints
│   │   │   ├── stats.py        # /stats endpoint
│   │   │   └── logs.py         # /logs endpoint
│   │   ├── deps.py             # Dependency injection
│   │   └── middleware.py       # Middleware
│   │
│   ├── services/               # Service Layer
│   │   ├── __init__.py
│   │   ├── feed_service.py     # RSS aggregation logic
│   │   ├── source_service.py   # Source management
│   │   ├── fetch_service.py    # RSS fetching
│   │   ├── auth_service.py     # API Key validation
│   │   └── rate_limit.py       # Rate Limiting
│   │
│   ├── models/                 # Data Models
│   │   ├── __init__.py
│   │   ├── source.py           # RSS source
│   │   ├── api_key.py          # API Key
│   │   └── feed_item.py        # RSS item
│   │
│   ├── db/                     # Database Layer
│   │   ├── __init__.py
│   │   ├── database.py         # SQLite connection
│   │   └── migrations/
│   │
│   ├── scheduler/              # Scheduler
│   │   ├── __init__.py
│   │   └── fetch_scheduler.py
│   │
│   └── config.py               # Configuration
│
├── tests/
├── Dockerfile
├── docker-compose.yml
├── cloudbuild.yaml
├── pyproject.toml
└── README.md
```

## Database Schema

### sources

```sql
CREATE TABLE sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    url TEXT NOT NULL UNIQUE,
    fetch_interval INTEGER DEFAULT 900,
    is_active BOOLEAN DEFAULT TRUE,
    last_fetched_at DATETIME,
    last_error TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    deleted_at DATETIME
);
```

### api_keys

```sql
CREATE TABLE api_keys (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT NOT NULL UNIQUE,
    name TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    deleted_at DATETIME
);
```

### feed_items

```sql
CREATE TABLE feed_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    link TEXT NOT NULL,
    description TEXT,
    published_at DATETIME,
    fetched_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    deleted_at DATETIME,
    FOREIGN KEY (source_id) REFERENCES sources(id)
);
```

### error_logs

```sql
CREATE TABLE error_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id INTEGER,
    error_type TEXT NOT NULL,
    error_message TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    deleted_at DATETIME,
    FOREIGN KEY (source_id) REFERENCES sources(id)
);
```

### stats

```sql
CREATE TABLE stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE NOT NULL UNIQUE,
    total_requests INTEGER DEFAULT 0,
    successful_fetches INTEGER DEFAULT 0,
    failed_fetches INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    deleted_at DATETIME
);
```

## API Endpoints

### Health Check (No Auth)

```
GET /health
Response 200: { "status": "ok" }
```

### Feed

```
GET /api/v1/feed
Headers: X-API-Key: <api_key>

Query Parameters:
  - sort_by: "published_at" | "source" (default: published_at)
  - sort_order: "asc" | "desc" (default: desc)
  - valid_time: integer (hours, optional)
  - keywords: string (semicolon-separated, optional)

Response 200: RSS XML
Response 401: { "detail": "Invalid API key" }
Response 429: { "detail": "Rate limit exceeded" }
```

### Sources

```
GET /api/v1/sources
POST /api/v1/sources
PUT /api/v1/sources/{id}
DELETE /api/v1/sources/{id}
POST /api/v1/sources/batch
POST /api/v1/sources/{id}/refresh
POST /api/v1/refresh
```

### API Keys

```
GET /api/v1/keys
POST /api/v1/keys
DELETE /api/v1/keys/{id}
```

### Stats & Logs

```
GET /api/v1/stats?days=7
GET /api/v1/logs?limit=100&source_id=1
```

### Error Responses

- Undefined path → 404 (empty body)
- Auth failure → 401 `{ "detail": "Invalid API key" }`
- Rate limit → 429 `{ "detail": "Rate limit exceeded" }`

## Environment Variables

```bash
# Application
APP_NAME=rss-aggregator
APP_ENV=development
APP_DEBUG=true
APP_HOST=0.0.0.0
APP_PORT=8000

# Database
DATABASE_URL=sqlite:///./data/rss.db

# API Key
DEFAULT_API_KEY=your-default-api-key-here

# Rate Limiting
RATE_LIMIT_REQUESTS=60
RATE_LIMIT_WINDOW=60

# RSS Fetching
DEFAULT_FETCH_INTERVAL=900
FETCH_TIMEOUT=30
FETCH_RETRY_COUNT=3
FETCH_RETRY_DELAY=5
MAX_FEED_ITEMS=1000

# Scheduler
SCHEDULER_ENABLED=true
SCHEDULER_INTERVAL=60

# Default Sources (optional)
# Format: name|url|fetch_interval;name2|url2|fetch_interval
DEFAULT_SOURCES=TechNews|https://example.com/rss.xml|900
```

## Docker Configuration

### Dockerfile

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY pyproject.toml uv.lock* ./
RUN uv sync --frozen --no-dev

COPY src/ ./src/
COPY alembic.ini ./
COPY alembic/ ./alembic/

RUN mkdir -p /app/data

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### docker-compose.yml

```yaml
version: "3.8"

services:
  rss-aggregator:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: rss-aggregator
    restart: unless-stopped
    ports:
      - "${APP_PORT:-8000}:8000"
    volumes:
      - ./data:/app/data
      - ./.env:/app/.env:ro
    environment:
      - APP_ENV=${APP_ENV:-production}
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s
```

### cloudbuild.yaml

```yaml
steps:
  - name: "gcr.io/cloud-builders/docker"
    args:
      - "build"
      - "-t"
      - "gcr.io/$PROJECT_ID/rss-aggregator:$COMMIT_SHA"
      - "-t"
      - "gcr.io/$PROJECT_ID/rss-aggregator:latest"
      - "."

  - name: "gcr.io/cloud-builders/docker"
    args: ["push", "gcr.io/$PROJECT_ID/rss-aggregator:$COMMIT_SHA"]

  - name: "gcr.io/cloud-builders/docker"
    args: ["push", "gcr.io/$PROJECT_ID/rss-aggregator:latest"]

  - name: "gcr.io/cloud-builders/gcloud"
    args:
      - "run"
      - "deploy"
      - "rss-aggregator"
      - "--image=gcr.io/$PROJECT_ID/rss-aggregator:$COMMIT_SHA"
      - "--region=asia-east1"
      - "--platform=managed"
      - "--allow-unauthenticated"
      - "--set-env-vars=APP_ENV=production"
      - "--memory=512Mi"
      - "--cpu=1"
      - "--min-instances=1"
      - "--max-instances=10"

images:
  - "gcr.io/$PROJECT_ID/rss-aggregator:$COMMIT_SHA"
  - "gcr.io/$PROJECT_ID/rss-aggregator:latest"
```

## Error Handling

### Error Types

```python
class RSSAggregatorError(Exception):
    """Base exception"""
    pass

class FetchError(RSSAggregatorError):
    """RSS fetch failed"""
    def __init__(self, url: str, reason: str):
        self.url = url
        self.reason = reason

class ParseError(RSSAggregatorError):
    """RSS parse failed"""
    def __init__(self, url: str, reason: str):
        self.url = url
        self.reason = reason

class RateLimitExceeded(RSSAggregatorError):
    """Rate limit exceeded"""
    pass

class InvalidAPIKey(RSSAggregatorError):
    """Invalid API key"""
    pass

class SourceNotFoundError(RSSAggregatorError):
    """Source not found"""
    pass
```

### Retry Logic

```
RSS Fetch Retry Flow:

1. Fetch URL
2. On failure:
   - If retry_count < N:
     - Wait RETRY_DELAY seconds
     - Retry
   - If retry_count >= N:
     - Log error to error_logs
     - Skip this source
```

## Scheduler Design

### Flow

```
Scheduler Loop (every SCHEDULER_INTERVAL seconds):

1. Query all active sources (is_active=true, deleted_at IS NULL)
2. Calculate which sources need fetching:
   - current_time - last_fetched_at >= fetch_interval
3. Add to task queue
4. Execute fetch tasks concurrently (with semaphore)
```

### Implementation

```python
class FetchScheduler:
    def __init__(
        self,
        fetch_service: FetchService,
        check_interval: int = 60,
        max_concurrent: int = 5,
    ):
        self.fetch_service = fetch_service
        self.check_interval = check_interval
        self.max_concurrent = max_concurrent
        self._running = False

    async def start(self) -> None:
        self._running = True
        asyncio.create_task(self._run_loop())

    async def stop(self) -> None:
        self._running = False

    async def refresh_source(self, source_id: int) -> None:
        """Manual refresh single source"""
        pass

    async def refresh_all(self) -> None:
        """Manual refresh all sources"""
        pass
```

## Rate Limiting

### Strategy

- Algorithm: Sliding Window
- Storage: In-memory (suitable for single instance)
- Configuration: Via environment variables

### Headers

```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 30
Retry-After: 30  (on 429)
```

## Feed Aggregation

### Filtering

1. **Time Range**: `valid_time` parameter (hours)
2. **Keywords**: OR logic, semicolon-separated, matches title only

### Sorting

- `published_at`: By publish time
- `source`: By source name
- Default: `published_at DESC`

### Output Format

Standard RSS 2.0 XML with `<source>` element for each item.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>RSS Aggregator</title>
    <link>https://github.com/your-repo/rss-aggregator</link>
    <description>Aggregated RSS Feed</description>
    <language>zh-tw</language>
    <lastBuildDate>Wed, 18 Mar 2026 10:00:00 GMT</lastBuildDate>
    
    <item>
      <title>Title</title>
      <link>https://example.com/article</link>
      <description>Summary...</description>
      <pubDate>Wed, 18 Mar 2026 09:30:00 GMT</pubDate>
      <source url="https://source.com/rss.xml">Source Name</source>
    </item>
  </channel>
</rss>
```

## Next Steps

1. Set up development environment
2. Implement core features
3. Write tests
4. Deploy to Cloud Run