# Tasks Document

## Phase 1: Project Setup

- [ ] 1. Initialize project with uv
  - File: `pyproject.toml`, `.python-version`
  - Run `uv init` to create project structure
  - Add dependencies: fastapi, uvicorn, sqlalchemy, aiosqlite, alembic, feedparser, httpx, pydantic-settings
  - Add dev dependencies: pytest, pytest-asyncio, ruff, mypy
  - Purpose: Set up Python project with uv package manager
  - _Requirements: Tech Stack_
  - _Prompt: Role: Python Developer specializing in project setup with uv | Task: Initialize a Python project using uv with pyproject.toml, add all required dependencies for FastAPI, SQLAlchemy, async support, RSS parsing, and development tools | Restrictions: Use Python 3.12, follow uv best practices, include all dependencies from tech.md | Success: Project can be installed with `uv sync`, all imports work_

- [ ] 2. Create project directory structure
  - Files: `src/__init__.py`, `src/api/__init__.py`, `src/services/__init__.py`, `src/models/__init__.py`, `src/db/__init__.py`, `src/scheduler/__init__.py`
  - Create empty `__init__.py` files for package structure
  - Purpose: Establish layered architecture
  - _Requirements: Design Architecture_
  - _Prompt: Role: Python Developer | Task: Create the directory structure for a FastAPI project with layered architecture (api, services, models, db, scheduler) | Restrictions: Follow the structure defined in design.md | Success: All directories exist with proper __init__.py files_

- [ ] 3. Create configuration module
  - File: `src/config.py`
  - Implement Pydantic Settings for environment variables
  - Define all settings from design document
  - Purpose: Centralized configuration management
  - _Leverage: pydantic-settings_
  - _Requirements: 8, 9_
  - _Prompt: Role: Backend Developer specializing in Python configuration | Task: Create a Pydantic Settings class with all environment variables from the design document (APP_*, DATABASE_URL, RATE_LIMIT_*, FETCH_*, SCHEDULER_*, DEFAULT_*) | Restrictions: Use pydantic-settings, provide sensible defaults, validate types | Success: Settings can be imported and used throughout the application_

- [ ] 4. Set up Alembic for database migrations
  - Files: `alembic.ini`, `alembic/env.py`, `alembic/versions/`
  - Initialize Alembic with async SQLite support
  - Purpose: Database migration management
  - _Leverage: SQLAlchemy, aiosqlite_
  - _Requirements: Data Models_
  - _Prompt: Role: Database Engineer specializing in SQLAlchemy and Alembic | Task: Set up Alembic for async SQLite, configure alembic.ini and env.py for async operations | Restrictions: Must support async engine, use SQLAlchemy 2.0 style | Success: `alembic revision --autogenerate` works correctly_

## Phase 2: Data Models

- [ ] 5. Create base model with soft delete
  - File: `src/models/base.py`
  - Implement SQLAlchemy declarative base with created_at, updated_at, deleted_at columns
  - Purpose: Common model functionality
  - _Requirements: Non-Functional - Modularity_
  - _Prompt: Role: Database Developer | Task: Create a SQLAlchemy 2.0 declarative base mixin with created_at, updated_at, and deleted_at columns, including a soft_delete() method | Restrictions: Use SQLAlchemy 2.0 style, async-compatible | Success: All models can inherit this base class_

- [ ] 6. Create Source model
  - File: `src/models/source.py`
  - Implement Source model matching design schema
  - Add relationships and indexes
  - Purpose: Store RSS source configuration
  - _Leverage: src/models/base.py_
  - _Requirements: 2_
  - _Prompt: Role: Database Developer | Task: Create Source SQLAlchemy model with all fields from design.md (id, name, url, fetch_interval, is_active, last_fetched_at, last_error, timestamps) | Restrictions: Inherit from base, add unique constraint on url, add index on is_active | Success: Model can be used in migrations and queries_

- [ ] 7. Create APIKey model
  - File: `src/models/api_key.py`
  - Implement APIKey model matching design schema
  - Purpose: Store API keys for authentication
  - _Leverage: src/models/base.py_
  - _Requirements: 8_
  - _Prompt: Role: Database Developer | Task: Create APIKey SQLAlchemy model with all fields from design.md (id, key, name, is_active, timestamps) | Restrictions: Inherit from base, add unique constraint on key | Success: Model can be used for authentication_

- [ ] 8. Create FeedItem model
  - File: `src/models/feed_item.py`
  - Implement FeedItem model with foreign key to Source
  - Add indexes for efficient querying
  - Purpose: Cache RSS feed items
  - _Leverage: src/models/base.py_
  - _Requirements: 1_
  - _Prompt: Role: Database Developer | Task: Create FeedItem SQLAlchemy model with all fields from design.md (id, source_id, title, link, description, published_at, fetched_at, timestamps), add foreign key to Source, add indexes on source_id and published_at | Restrictions: Inherit from base, cascade delete on source | Success: Model can store and query feed items efficiently_

- [ ] 9. Create ErrorLog and Stats models
  - File: `src/models/error_log.py`, `src/models/stats.py`
  - Implement ErrorLog and Stats models
  - Purpose: Track errors and statistics
  - _Leverage: src/models/base.py_
  - _Requirements: 10_
  - _Prompt: Role: Database Developer | Task: Create ErrorLog and Stats SQLAlchemy models with all fields from design.md, Stats should have unique constraint on date | Restrictions: Inherit from base, follow design schema exactly | Success: Models can track errors and daily statistics_

- [ ] 10. Create initial migration
  - Run: `alembic revision --autogenerate -m "Initial schema"`
  - Generate migration for all models
  - Purpose: Create database tables
  - _Leverage: All models_
  - _Requirements: All Data Models_
  - _Prompt: Role: Database Administrator | Task: Generate initial Alembic migration for all created models | Restrictions: Review generated SQL before applying | Success: Migration creates all tables correctly_

## Phase 3: Database Layer

- [ ] 11. Create database engine and session
  - File: `src/db/database.py`
  - Implement async SQLite engine and session factory
  - Add dependency injection for database sessions
  - Purpose: Database connection management
  - _Leverage: SQLAlchemy async_
  - _Requirements: Data Layer_
  - _Prompt: Role: Backend Developer specializing in async SQLAlchemy | Task: Create async engine, session factory, and get_session dependency for FastAPI | Restrictions: Use SQLAlchemy 2.0 async style, configure connection pooling for SQLite | Success: Database sessions can be injected into routes and services_

## Phase 4: Services

- [ ] 12. Create AuthService
  - File: `src/services/auth_service.py`
  - Implement API key validation
  - Handle inactive and deleted keys
  - Purpose: Authenticate API requests
  - _Leverage: src/models/api_key.py, src/db/database.py_
  - _Requirements: 8_
  - _Prompt: Role: Backend Developer specializing in authentication | Task: Create AuthService with validate_key() method that checks if API key exists, is active, and not deleted | Restrictions: Return boolean, handle soft delete correctly | Success: Service correctly validates API keys_

- [ ] 13. Create RateLimiter
  - File: `src/services/rate_limiter.py`
  - Implement sliding window rate limiting
  - Track requests per API key
  - Purpose: Prevent API abuse
  - _Leverage: src/config.py_
  - _Requirements: 9_
  - _Prompt: Role: Backend Developer specializing in rate limiting | Task: Create RateLimiter class with sliding window algorithm, is_allowed(), get_remaining(), get_reset_time() methods | Restrictions: In-memory storage, thread-safe for async, configurable limits from settings | Success: Rate limiter correctly tracks and limits requests_

- [ ] 14. Create SourceService
  - File: `src/services/source_service.py`
  - Implement CRUD operations for sources
  - Handle soft delete and unique constraints
  - Purpose: Manage RSS sources
  - _Leverage: src/models/source.py, src/db/database.py_
  - _Requirements: 2_
  - _Prompt: Role: Backend Developer | Task: Create SourceService with create_source(), get_sources(), get_source(), update_source(), delete_source() methods, handle URL uniqueness and soft delete | Restrictions: Use async database operations, return Pydantic models | Success: All CRUD operations work correctly_

- [ ] 15. Create FetchService
  - File: `src/services/fetch_service.py`
  - Implement RSS fetching and parsing
  - Handle retries and error logging
  - Purpose: Fetch and parse RSS feeds
  - _Leverage: httpx, feedparser, src/models/source.py, src/models/feed_item.py, src/models/error_log.py_
  - _Requirements: 6_
  - _Prompt: Role: Backend Developer specializing in HTTP clients | Task: Create FetchService with fetch_source() and parse_rss() methods, implement retry logic with configurable attempts, log errors to ErrorLog | Restrictions: Use async httpx, handle malformed feeds gracefully, respect timeout settings | Success: Service can fetch and parse RSS feeds correctly_

- [ ] 16. Create FeedService
  - File: `src/services/feed_service.py`
  - Implement feed aggregation with filtering and sorting
  - Generate RSS 2.0 XML output
  - Purpose: Aggregate and filter RSS items
  - _Leverage: src/models/feed_item.py, src/models/source.py, src/db/database.py_
  - _Requirements: 1, 3, 4, 5_
  - _Prompt: Role: Backend Developer | Task: Create FeedService with get_aggregated_feed() method supporting sort_by, sort_order, valid_time, keywords parameters, implement RSS 2.0 XML generation using xml.etree.ElementTree | Restrictions: Use async database queries, SQL-level filtering for performance, OR logic for keywords | Success: Service returns correct filtered and sorted RSS XML_

- [ ] 17. Create StatsService and LogService
  - File: `src/services/stats_service.py`, `src/services/log_service.py`
  - Implement statistics and log retrieval
  - Purpose: Provide monitoring data
  - _Leverage: src/models/stats.py, src/models/error_log.py_
  - _Requirements: 10_
  - _Prompt: Role: Backend Developer | Task: Create StatsService with get_stats() and increment_*() methods, create LogService with get_logs() method supporting source_id filter | Restrictions: Use async database operations, aggregate by date for stats | Success: Services provide correct monitoring data_

## Phase 5: Scheduler

- [ ] 18. Create FetchScheduler
  - File: `src/scheduler/fetch_scheduler.py`
  - Implement background fetch scheduling
  - Use asyncio for periodic checks
  - Purpose: Periodically fetch RSS sources
  - _Leverage: src/services/fetch_service.py, src/services/source_service.py_
  - _Requirements: 6_
  - _Prompt: Role: Backend Developer specializing in async Python | Task: Create FetchScheduler with start(), stop(), refresh_source(), refresh_all() methods using asyncio, check sources based on fetch_interval, use semaphore for concurrency control | Restrictions: Async-compatible, graceful shutdown, configurable check interval | Success: Scheduler correctly fetches sources at their configured intervals_

## Phase 6: API Layer

- [ ] 19. Create dependency injection module
  - File: `src/api/deps.py`
  - Implement FastAPI dependencies for services, auth, database
  - Purpose: Centralize dependency injection
  - _Leverage: All services, src/db/database.py_
  - _Requirements: Non-Functional - Modularity_
  - _Prompt: Role: FastAPI Developer | Task: Create dependency functions for get_session, get_source_service, get_feed_service, get_auth_service, get_rate_limiter, require_api_key, get_scheduler | Restrictions: Use FastAPI Depends, handle errors gracefully | Success: All dependencies injectable into routes_

- [ ] 20. Create authentication middleware
  - File: `src/api/middleware.py`
  - Implement API key validation middleware
  - Integrate rate limiting
  - Purpose: Protect API endpoints
  - _Leverage: src/services/auth_service.py, src/services/rate_limiter.py_
  - _Requirements: 8, 9_
  - _Prompt: Role: FastAPI Developer | Task: Create middleware that validates X-API-Key header, enforces rate limiting, returns 401 for invalid keys and 429 for rate limit exceeded | Restrictions: Skip /health endpoint, add rate limit headers to responses | Success: Middleware correctly protects endpoints_

- [ ] 21. Create health endpoint
  - File: `src/api/routes/health.py`
  - Implement simple health check
  - Purpose: Service health monitoring
  - _Requirements: Non-Functional - Reliability_
  - _Prompt: Role: Backend Developer | Task: Create GET /health endpoint returning {"status": "ok"} | Restrictions: No authentication required | Success: Endpoint returns 200 with correct response_

- [ ] 22. Create feed routes
  - File: `src/api/routes/feed.py`
  - Implement GET /api/v1/feed endpoint
  - Add query parameter validation
  - Purpose: Serve aggregated RSS feed
  - _Leverage: src/services/feed_service.py, src/api/deps.py_
  - _Requirements: 1, 3, 4, 5_
  - _Prompt: Role: FastAPI Developer | Task: Create GET /api/v1/feed endpoint with sort_by, sort_order, valid_time, keywords query parameters, validate inputs, return RSS XML with application/xml content type | Restrictions: Require API key, add cache headers | Success: Endpoint returns correct RSS feed_

- [ ] 23. Create source routes
  - File: `src/api/routes/sources.py`
  - Implement CRUD endpoints for sources
  - Add batch operations and refresh endpoints
  - Purpose: Manage RSS sources
  - _Leverage: src/services/source_service.py, src/api/deps.py_
  - _Requirements: 2, 7_
  - _Prompt: Role: FastAPI Developer | Task: Create GET, POST /api/v1/sources, PUT, DELETE /api/v1/sources/{id}, POST /api/v1/sources/batch, POST /api/v1/sources/{id}/refresh, POST /api/v1/refresh endpoints | Restrictions: Require API key, validate input with Pydantic, return proper HTTP status codes | Success: All endpoints work correctly_

- [ ] 24. Create API key routes
  - File: `src/api/routes/keys.py`
  - Implement API key management endpoints
  - Purpose: Manage API keys
  - _Requirements: 8_
  - _Prompt: Role: FastAPI Developer | Task: Create GET, POST /api/v1/keys, DELETE /api/v1/keys/{id} endpoints for API key management | Restrictions: Require API key, generate secure random keys | Success: API keys can be created, listed, and deleted_

- [ ] 25. Create stats and logs routes
  - File: `src/api/routes/stats.py`, `src/api/routes/logs.py`
  - Implement statistics and log retrieval endpoints
  - Purpose: Provide monitoring data
  - _Leverage: src/services/stats_service.py, src/services/log_service.py_
  - _Requirements: 10_
  - _Prompt: Role: FastAPI Developer | Task: Create GET /api/v1/stats with days parameter and GET /api/v1/logs with limit and source_id parameters | Restrictions: Require API key, validate parameters | Success: Endpoints return correct data_

- [ ] 26. Create main application
  - File: `src/main.py`
  - Initialize FastAPI app with lifespan
  - Register all routes and middleware
  - Purpose: Application entry point
  - _Leverage: All routes, middleware, scheduler_
  - _Requirements: All_
  - _Prompt: Role: FastAPI Developer | Task: Create FastAPI application with lifespan context manager to start/stop scheduler, register all routers with /api/v1 prefix, add middleware, add 404 handler returning empty response | Restrictions: Use lifespan pattern, configure CORS if needed | Success: Application starts and serves all endpoints_

## Phase 7: Testing

- [ ] 27. Create test fixtures and utilities
  - File: `tests/conftest.py`, `tests/fixtures/`
  - Set up pytest with async support
  - Create test database and client fixtures
  - Purpose: Testing infrastructure
  - _Leverage: pytest-asyncio_
  - _Requirements: Testing Strategy_
  - _Prompt: Role: QA Engineer | Task: Create pytest fixtures for async test client, test database, sample data (sources, feed items, API keys) | Restrictions: Use pytest-asyncio, isolate tests with separate database | Success: Tests can use fixtures for setup_

- [ ] 28. Write unit tests for services
  - File: `tests/services/`
  - Test all service methods with mocked dependencies
  - Purpose: Verify service logic
  - _Leverage: tests/conftest.py_
  - _Requirements: All functional requirements_
  - _Prompt: Role: QA Engineer | Task: Write unit tests for all services (AuthService, RateLimiter, SourceService, FetchService, FeedService, StatsService, LogService) with mocked database and external dependencies | Restrictions: Test success and failure cases, achieve high coverage | Success: All tests pass, services verified_

- [ ] 29. Write integration tests for API
  - File: `tests/api/`
  - Test all endpoints with test database
  - Purpose: Verify API behavior
  - _Leverage: tests/conftest.py_
  - _Requirements: All functional requirements_
  - _Prompt: Role: QA Engineer | Task: Write integration tests for all API endpoints testing request/response, authentication, rate limiting, error handling | Restrictions: Use test database, test edge cases | Success: All endpoints tested and working_

## Phase 8: Deployment

- [ ] 30. Create Dockerfile
  - File: `Dockerfile`
  - Multi-stage build with uv
  - Configure for Cloud Run
  - Purpose: Container deployment
  - _Requirements: Deployment_
  - _Prompt: Role: DevOps Engineer | Task: Create Dockerfile for Python application using uv, multi-stage build for smaller image, expose port 8000 | Restrictions: Use Python 3.12-slim base, install uv, copy source | Success: Image builds and runs correctly_

- [ ] 31. Create docker-compose.yml
  - File: `docker-compose.yml`
  - Configure local development environment
  - Add volume for data persistence
  - Purpose: Local development
  - _Requirements: Deployment_
  - _Prompt: Role: DevOps Engineer | Task: Create docker-compose.yml for local development with rss-aggregator service, volume for SQLite data, environment file support | Restrictions: Include health check, port mapping | Success: Application runs with docker-compose up_

- [ ] 32. Create cloudbuild.yaml
  - File: `cloudbuild.yaml`
  - Configure Cloud Build for CI/CD
  - Deploy to Cloud Run
  - Purpose: Automated deployment
  - _Requirements: Deployment_
  - _Prompt: Role: Cloud Engineer | Task: Create cloudbuild.yaml for Google Cloud Build that builds Docker image, pushes to Container Registry, deploys to Cloud Run | Restrictions: Configure memory, CPU, min instances, environment variables | Success: Pipeline deploys to Cloud Run successfully_

- [ ] 33. Create .env.example
  - File: `.env.example`
  - Document all environment variables
  - Provide sensible defaults
  - Purpose: Configuration documentation
  - _Requirements: Configuration_
  - _Prompt: Role: Backend Developer | Task: Create .env.example with all environment variables from design.md, include comments explaining each variable | Restrictions: Do not include real secrets | Success: Developers can copy and configure_

- [ ] 34. Create README.md
  - File: `README.md`
  - Document installation, usage, API
  - Include examples
  - Purpose: Project documentation
  - _Requirements: Documentation_
  - _Prompt: Role: Technical Writer | Task: Create README.md with project overview, installation instructions (local and Docker), usage examples, API documentation summary, deployment instructions | Restrictions: Keep it concise, use code blocks | Success: New users can understand and run the project_

- [ ] 35. Final integration test
  - Run: All tests, linting, type checking
  - Verify all requirements are met
  - Purpose: Quality assurance
  - _Requirements: All_
  - _Prompt: Role: QA Engineer | Task: Run full test suite, linting with ruff, type checking with mypy, verify all acceptance criteria from requirements.md | Restrictions: Fix any issues found | Success: All tests pass, code quality checks pass_