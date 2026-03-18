# Technology Stack

## Project Type

REST API service with background job scheduling, deployed as a containerized application.

## Core Technologies

### Primary Language(s)

- **Language**: Python 3.12
- **Runtime**: CPython
- **Package Manager**: uv

### Key Dependencies/Libraries

- **FastAPI**: Modern async web framework with automatic API documentation
- **SQLAlchemy**: ORM for database operations
- **Alembic**: Database migration tool
- **feedparser**: RSS/Atom feed parsing
- **httpx**: Async HTTP client for fetching feeds
- **APScheduler**: Background job scheduling
- **Pydantic**: Data validation and settings management

### Application Architecture

Monolithic application with layered architecture:
- **API Layer**: FastAPI routes and middleware
- **Service Layer**: Business logic (feed aggregation, source management)
- **Data Layer**: SQLAlchemy models and database operations
- **Scheduler**: Background tasks for periodic feed fetching

### Data Storage

- **Primary storage**: SQLite (file-based, portable)
- **Caching**: In-memory for rate limiting
- **Data formats**: JSON (API), XML (RSS output)

### External Integrations

- **APIs**: RSS/Atom feeds from external sources
- **Protocols**: HTTP/REST
- **Authentication**: API Key based

## Development Environment

### Build & Development Tools

- **Build System**: Docker
- **Package Management**: uv (pyproject.toml)
- **Development workflow**: Hot reload with uvicorn --reload

### Code Quality Tools

- **Static Analysis**: ruff (linting)
- **Formatting**: ruff format
- **Testing Framework**: pytest with pytest-asyncio
- **Type Checking**: mypy

### Version Control & Collaboration

- **VCS**: Git
- **Branching Strategy**: Feature branches
- **Code Review Process**: Pull requests

## Deployment & Distribution

- **Target Platform(s)**: Cloud Run, Docker containers
- **Distribution Method**: Docker image, Cloud Run deployment
- **Installation Requirements**: Docker, Python 3.12 (for local development)
- **Update Mechanism**: Git commits trigger Cloud Build

## Technical Requirements & Constraints

### Performance Requirements

- **Response Time**: < 500ms for API responses
- **Concurrent Requests**: Support 100+ concurrent requests
- **Memory**: < 512MB for normal operation

### Compatibility Requirements

- **Platform Support**: Linux (Docker), any platform with Python 3.12
- **RSS Formats**: RSS 2.0, RSS 1.0, Atom
- **Standards Compliance**: RSS 2.0 output format

### Security & Compliance

- **Security Requirements**: API Key authentication, rate limiting
- **Input Validation**: URL validation, input sanitization
- **Error Handling**: No sensitive data in error messages

### Scalability & Reliability

- **Expected Load**: Small to medium traffic (personal/team use)
- **Availability Requirements**: 99.9% uptime target
- **Growth Projections**: Horizontal scaling via Cloud Run

## Technical Decisions & Rationale

### Decision Log

1. **SQLite over PostgreSQL**: Simpler deployment, no external service required, sufficient for expected load
2. **FastAPI over Flask**: Native async support, automatic API docs, modern type hints
3. **uv over pip**: Faster dependency resolution, lock file support
4. **Monolithic Architecture**: Simpler deployment, single container, appropriate for scale

## Known Limitations

- **Single Instance Rate Limiting**: In-memory rate limiting doesn't work across multiple instances; consider Redis for multi-instance deployments
- **SQLite Concurrency**: Write concurrency limited; consider PostgreSQL for high write loads
- **No Feed History**: Only stores current feed items; older items are replaced on each fetch