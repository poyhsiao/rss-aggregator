# RSS Aggregator

A FastAPI-based RSS feed aggregator with source management, scheduled fetching, filtering, and API key authentication.

## Features

- Aggregate multiple RSS/Atom feeds into a single output
- Filter by time range and keywords
- Sort by publication time or source name
- Source management via API or environment variables
- Scheduled background fetching
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
| `/api/v1/stats` | GET | Get statistics |
| `/api/v1/logs` | GET | Get error logs |

## Configuration

See `.env.example` for all available configuration options.

## License

MIT