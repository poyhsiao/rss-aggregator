# RSS Aggregator - Task List

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a FastAPI-based RSS aggregator service with source management, scheduled fetching, filtering, and API key authentication.

**Architecture:** Monolithic FastAPI application with layered architecture (API → Services → Models → DB), background scheduler using asyncio, SQLite for persistence, and in-memory rate limiting.

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy 2.0 (async), SQLite, uv, httpx, feedparser

---

## Phase 1: Project Setup

### Task 1: Initialize Project with uv
- [ ] Create `pyproject.toml` with uv init
- [ ] Create `.python-version` file (3.12)
- [ ] Add dependencies: fastapi, uvicorn, sqlalchemy, aiosqlite, alembic, feedparser, httpx, pydantic-settings, python-multipart
- [ ] Add dev dependencies: pytest, pytest-asyncio, pytest-cov, ruff, mypy, httpx
- [ ] Create `.env.example` with all configuration options
- [ ] Commit: `chore: initialize project with uv and dependencies`

### Task 2: Create Project Directory Structure
- [ ] Create directories: `src/api/routes`, `src/services`, `src/models`, `src/db`, `src/scheduler`, `tests`, `data`
- [ ] Create `__init__.py` files in all Python directories
- [ ] Create `data/.gitkeep`
- [ ] Commit: `chore: create project directory structure`

### Task 3: Create Configuration Module
- [ ] Create `src/config.py` with Pydantic Settings
- [ ] Define Settings class with all environment variables
- [ ] Add `get_settings()` cached function
- [ ] Commit: `feat: add configuration module with pydantic-settings`

### Task 4: Create Base Model with Soft Delete
- [ ] Write test: `tests/models/test_base.py`
- [ ] Create `src/models/base.py` with Base and TimestampMixin
- [ ] Implement soft_delete() method
- [ ] Run tests, verify pass
- [ ] Commit: `feat: add base model with soft delete support`

---

## Phase 2: Data Models

### Task 5: Create Source Model
- [ ] Write test: `tests/models/test_source.py`
- [ ] Create `src/models/source.py` with Source model
- [ ] Fields: id, name, url, fetch_interval, is_active, last_fetched_at, last_error
- [ ] Run tests, verify pass
- [ ] Commit: `feat: add Source model`

### Task 6: Create APIKey Model
- [ ] Write test: `tests/models/test_api_key.py`
- [ ] Create `src/models/api_key.py` with APIKey model
- [ ] Fields: id, key, name, is_active
- [ ] Run tests, verify pass
- [ ] Commit: `feat: add APIKey model`

### Task 7: Create FeedItem Model
- [ ] Write test: `tests/models/test_feed_item.py`
- [ ] Create `src/models/feed_item.py` with FeedItem model
- [ ] Fields: id, source_id, title, link, description, published_at, fetched_at
- [ ] Add relationship to Source
- [ ] Run tests, verify pass
- [ ] Commit: `feat: add FeedItem model`

### Task 8: Create ErrorLog Model
- [ ] Write test: `tests/models/test_error_log.py`
- [ ] Create `src/models/error_log.py` with ErrorLog model
- [ ] Fields: id, source_id, error_type, error_message
- [ ] Run tests, verify pass
- [ ] Commit: `feat: add ErrorLog model`

### Task 9: Create Stats Model
- [ ] Write test: `tests/models/test_stats.py`
- [ ] Create `src/models/stats.py` with Stats model
- [ ] Fields: id, date, total_requests, successful_fetches, failed_fetches
- [ ] Run tests, verify pass
- [ ] Commit: `feat: add Stats model`

### Task 10: Update Models __init__.py
- [ ] Export all models from `src/models/__init__.py`
- [ ] Run all model tests
- [ ] Commit: `chore: export all models from __init__.py`

---

## Phase 3: Database Layer

### Task 11: Create Database Engine and Session
- [ ] Write test: `tests/db/test_database.py`
- [ ] Create `src/db/database.py` with async engine and session factory
- [ ] Create `get_session()` dependency
- [ ] Update `tests/conftest.py` with db_session fixture
- [ ] Run tests, verify pass
- [ ] Commit: `feat: add async database engine and session factory`

### Task 12: Set Up Alembic Migrations
- [ ] Run `uv run alembic init alembic`
- [ ] Update `alembic/env.py` for async SQLite
- [ ] Create initial migration: `uv run alembic revision --autogenerate -m "Initial schema"`
- [ ] Commit: `chore: set up alembic migrations for async sqlite`

---

## Phase 4: Services

### Task 13: Create AuthService
- [ ] Write test: `tests/services/test_auth_service.py`
- [ ] Create `src/services/auth_service.py` with AuthService class
- [ ] Implement `validate_key()` method
- [ ] Run tests, verify pass
- [ ] Commit: `feat: add AuthService for API key validation`

### Task 14: Create RateLimiter
- [ ] Write test: `tests/services/test_rate_limiter.py`
- [ ] Create `src/services/rate_limiter.py` with RateLimiter class
- [ ] Implement sliding window algorithm
- [ ] Methods: `is_allowed()`, `get_remaining()`, `get_reset_time()`
- [ ] Run tests, verify pass
- [ ] Commit: `feat: add RateLimiter with sliding window algorithm`

### Task 15: Create SourceService
- [ ] Write test: `tests/services/test_source_service.py`
- [ ] Create `src/services/source_service.py` with SourceService class
- [ ] CRUD operations: create, get, update, delete (soft delete)
- [ ] Method: `get_active_sources()`
- [ ] Run tests, verify pass
- [ ] Commit: `feat: add SourceService for RSS source management`

### Task 16: Create FetchService
- [ ] Write test: `tests/services/test_fetch_service.py`
- [ ] Create `src/services/fetch_service.py` with FetchService class
- [ ] Implement RSS parsing with feedparser
- [ ] Implement retry logic for fetching
- [ ] Methods: `parse_rss()`, `fetch_source()`, `fetch_all()`
- [ ] Run tests, verify pass
- [ ] Commit: `feat: add FetchService for RSS fetching and parsing`

### Task 17: Create FeedService
- [ ] Write test: `tests/services/test_feed_service.py`
- [ ] Create `src/services/feed_service.py` with FeedService class
- [ ] Implement filtering by time and keywords (OR logic)
- [ ] Implement sorting (published_at, source)
- [ ] Generate RSS 2.0 XML output
- [ ] Run tests, verify pass
- [ ] Commit: `feat: add FeedService for RSS aggregation`

---

## Phase 5: Scheduler

### Task 18: Create FetchScheduler
- [ ] Write test: `tests/scheduler/test_fetch_scheduler.py`
- [ ] Create `src/scheduler/fetch_scheduler.py` with FetchScheduler class
- [ ] Implement background loop with check interval
- [ ] Implement concurrency control with semaphore
- [ ] Methods: `start()`, `stop()`, `refresh_source()`, `refresh_all()`
- [ ] Run tests, verify pass
- [ ] Commit: `feat: add FetchScheduler for periodic RSS fetching`

---

## Phase 6: API Layer

### Task 19: Create Dependency Injection Module
- [ ] Create `src/api/deps.py`
- [ ] Implement service dependencies
- [ ] Implement `require_api_key()` with rate limiting
- [ ] Commit: `feat: add dependency injection module`

### Task 20: Create Health Endpoint
- [ ] Create `src/api/routes/health.py`
- [ ] Implement `GET /health` endpoint (no auth required)
- [ ] Commit: `feat: add health check endpoint`

### Task 21: Create Feed Routes
- [ ] Create `src/api/routes/feed.py`
- [ ] Implement `GET /api/v1/feed` endpoint
- [ ] Query params: sort_by, sort_order, valid_time, keywords
- [ ] Return RSS XML response
- [ ] Commit: `feat: add feed routes`

### Task 22: Create Source Routes
- [ ] Create `src/api/routes/sources.py`
- [ ] Implement CRUD endpoints for sources
- [ ] Endpoints: GET, POST, PUT, DELETE, batch create, refresh
- [ ] Commit: `feat: add source management routes`

### Task 23: Create API Key Routes
- [ ] Create `src/api/routes/keys.py`
- [ ] Implement CRUD endpoints for API keys
- [ ] Auto-generate secure API keys
- [ ] Commit: `feat: add API key management routes`

### Task 24: Create Stats and Logs Routes
- [ ] Create `src/api/routes/stats.py`
- [ ] Implement `GET /api/v1/stats` endpoint
- [ ] Create `src/api/routes/logs.py`
- [ ] Implement `GET /api/v1/logs` endpoint
- [ ] Commit: `feat: add stats and logs routes`

### Task 25: Create Main Application
- [ ] Create `src/main.py` with FastAPI app
- [ ] Implement lifespan context manager for scheduler
- [ ] Register all routers with `/api/v1` prefix
- [ ] Add 404 handler (empty response)
- [ ] Update `src/api/routes/__init__.py`
- [ ] Commit: `feat: create main FastAPI application`

### Task 26: Run Application and Verify
- [ ] Run database migrations: `uv run alembic upgrade head`
- [ ] Start the application: `uv run uvicorn src.main:app --reload`
- [ ] Test health endpoint: `curl http://localhost:8000/health`
- [ ] Commit: `feat: complete RSS aggregator implementation`

---

## Phase 7: Deployment

### Task 27: Create Dockerfile
- [ ] Create `Dockerfile` based on python:3.12-slim
- [ ] Install uv for dependency management
- [ ] Run migrations on container start
- [ ] Commit: `feat: add Dockerfile`

### Task 28: Create docker-compose.yml
- [ ] Create `docker-compose.yml`
- [ ] Configure volume for data persistence
- [ ] Add healthcheck
- [ ] Commit: `feat: add docker-compose.yml`

### Task 29: Create cloudbuild.yaml
- [ ] Create `cloudbuild.yaml` for Cloud Run deployment
- [ ] Configure build and deploy steps
- [ ] Set resource limits (512Mi memory, 1 CPU)
- [ ] Commit: `feat: add cloudbuild.yaml for Cloud Run deployment`

### Task 30: Create README.md
- [ ] Create `README.md` with project overview
- [ ] Include quick start guide
- [ ] Document API endpoints
- [ ] List configuration options
- [ ] Commit: `docs: add README.md`

### Task 31: Create .gitignore
- [ ] Create `.gitignore` for Python, uv, IDE, env, database, logs, testing
- [ ] Commit: `chore: add .gitignore`

---

## Summary

| Phase | Tasks | Description |
|-------|-------|-------------|
| Phase 1 | 1-4 | Project Setup |
| Phase 2 | 5-10 | Data Models |
| Phase 3 | 11-12 | Database Layer |
| Phase 4 | 13-17 | Services |
| Phase 5 | 18 | Scheduler |
| Phase 6 | 19-26 | API Layer |
| Phase 7 | 27-31 | Deployment |

**Total: 31 Tasks**

---

## Execution Handoff

**Two execution options:**

**1. Subagent-Driven (this session)** - I dispatch fresh subagent per task, review between tasks, fast iteration

**2. Parallel Session (separate)** - Open new session with executing-plans, batch execution with checkpoints

**Which approach?**

**If Subagent-Driven chosen:**
- **REQUIRED SUB-SKILL:** Use superpowers:subagent-driven-development
- Stay in this session
- Fresh subagent per task + code review

**If Parallel Session chosen:**
- Guide them to open new session in worktree
- **REQUIRED SUB-SKILL:** New session uses superpowers:executing-plans