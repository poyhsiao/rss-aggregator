# RSS Aggregator Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a FastAPI-based RSS aggregator service with source management, scheduled fetching, filtering, and API key authentication.

**Architecture:** Monolithic FastAPI application with layered architecture (API → Services → Models → DB), background scheduler using asyncio, SQLite for persistence, and in-memory rate limiting.

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy 2.0 (async), SQLite, uv, httpx, feedparser

---

## Phase 1: Project Setup

### Task 1: Initialize Project with uv

**Files:**
- Create: `pyproject.toml`
- Create: `.python-version`
- Create: `.env.example`

**Step 1: Initialize uv project**

Run:
```bash
uv init --name rss-aggregator
```

Expected: Creates `pyproject.toml` with basic project info

**Step 2: Set Python version**

Run:
```bash
echo "3.12" > .python-version
```

**Step 3: Add dependencies**

Run:
```bash
uv add fastapi uvicorn[standard] sqlalchemy aiosqlite alembic feedparser httpx pydantic-settings python-multipart
```

Expected: Dependencies added to `pyproject.toml`

**Step 4: Add dev dependencies**

Run:
```bash
uv add --dev pytest pytest-asyncio pytest-cov ruff mypy httpx
```

Expected: Dev dependencies added

**Step 5: Create .env.example**

```bash
# Application
APP_NAME=rss-aggregator
APP_ENV=development
APP_DEBUG=true
APP_HOST=0.0.0.0
APP_PORT=8000

# Database
DATABASE_URL=sqlite+aiosqlite:///./data/rss.db

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
DEFAULT_SOURCES=
```

**Step 6: Commit**

```bash
git add pyproject.toml uv.lock .python-version .env.example
git commit -m "chore: initialize project with uv and dependencies"
```

---

### Task 2: Create Project Directory Structure

**Files:**
- Create: `src/__init__.py`
- Create: `src/api/__init__.py`
- Create: `src/api/routes/__init__.py`
- Create: `src/services/__init__.py`
- Create: `src/models/__init__.py`
- Create: `src/db/__init__.py`
- Create: `src/scheduler/__init__.py`
- Create: `tests/__init__.py`
- Create: `data/.gitkeep`

**Step 1: Create directories**

Run:
```bash
mkdir -p src/api/routes src/services src/models src/db src/scheduler tests data
```

**Step 2: Create __init__.py files**

Run:
```bash
touch src/__init__.py
touch src/api/__init__.py
touch src/api/routes/__init__.py
touch src/services/__init__.py
touch src/models/__init__.py
touch src/db/__init__.py
touch src/scheduler/__init__.py
touch tests/__init__.py
touch data/.gitkeep
```

**Step 3: Commit**

```bash
git add src/ tests/ data/
git commit -m "chore: create project directory structure"
```

---

### Task 3: Create Configuration Module

**Files:**
- Create: `src/config.py`

**Step 1: Write the config module**

```python
# src/config.py
"""Application configuration using Pydantic Settings."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Application
    app_name: str = "rss-aggregator"
    app_env: str = "development"
    app_debug: bool = True
    app_host: str = "0.0.0.0"
    app_port: int = 8000

    # Database
    database_url: str = "sqlite+aiosqlite:///./data/rss.db"

    # API Key
    default_api_key: str = ""

    # Rate Limiting
    rate_limit_requests: int = 60
    rate_limit_window: int = 60

    # RSS Fetching
    default_fetch_interval: int = 900
    fetch_timeout: int = 30
    fetch_retry_count: int = 3
    fetch_retry_delay: int = 5
    max_feed_items: int = 1000

    # Scheduler
    scheduler_enabled: bool = True
    scheduler_interval: int = 60

    # Default Sources
    default_sources: str = ""

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
```

**Step 2: Commit**

```bash
git add src/config.py
git commit -m "feat: add configuration module with pydantic-settings"
```

---

### Task 4: Create Base Model with Soft Delete

**Files:**
- Create: `src/models/base.py`
- Create: `tests/models/test_base.py`

**Step 1: Write the test**

```python
# tests/models/test_base.py
"""Tests for base model functionality."""

from src.models.base import Base, TimestampMixin


def test_timestamp_mixin_has_required_fields():
    """Test that TimestampMixin has all required timestamp fields."""
    mixin = TimestampMixin()
    assert hasattr(mixin, "created_at")
    assert hasattr(mixin, "updated_at")
    assert hasattr(mixin, "deleted_at")


def test_base_is_declarative_base():
    """Test that Base is a valid declarative base."""
    assert hasattr(Base, "metadata")
    assert hasattr(Base, "registry")
```

**Step 2: Run test to verify it fails**

Run:
```bash
uv run pytest tests/models/test_base.py -v
```

Expected: FAIL - Module not found

**Step 3: Write minimal implementation**

```python
# src/models/base.py
"""SQLAlchemy base model with soft delete support."""

from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """SQLAlchemy declarative base for all models."""

    pass


class TimestampMixin:
    """Mixin for created_at, updated_at, and deleted_at timestamps."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True, default=None
    )

    def soft_delete(self) -> None:
        """Mark this record as deleted."""
        self.deleted_at = datetime.utcnow()
```

**Step 4: Run test to verify it passes**

Run:
```bash
uv run pytest tests/models/test_base.py -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add src/models/base.py tests/models/test_base.py
git commit -m "feat: add base model with soft delete support"
```

---

## Phase 2: Data Models

### Task 5: Create Source Model

**Files:**
- Create: `src/models/source.py`
- Create: `tests/models/test_source.py`

**Step 1: Write the test**

```python
# tests/models/test_source.py
"""Tests for Source model."""

from src.models.source import Source


def test_source_model_has_required_fields():
    """Test that Source model has all required fields."""
    source = Source(
        name="Test Source",
        url="https://example.com/feed.xml",
        fetch_interval=900,
    )
    assert source.name == "Test Source"
    assert source.url == "https://example.com/feed.xml"
    assert source.fetch_interval == 900
    assert source.is_active is True
    assert source.last_fetched_at is None
    assert source.last_error is None


def test_source_default_values():
    """Test that Source model has correct default values."""
    source = Source(
        name="Test",
        url="https://example.com/feed.xml",
    )
    assert source.fetch_interval == 900
    assert source.is_active is True
```

**Step 2: Run test to verify it fails**

Run:
```bash
uv run pytest tests/models/test_source.py -v
```

Expected: FAIL - Module not found

**Step 3: Write minimal implementation**

```python
# src/models/source.py
"""RSS Source model."""

from datetime import datetime

from sqlalchemy import Boolean, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base, TimestampMixin


class Source(Base, TimestampMixin):
    """RSS feed source configuration."""

    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    url: Mapped[str] = mapped_column(String(2048), nullable=False, unique=True)
    fetch_interval: Mapped[int] = mapped_column(Integer, nullable=False, default=900)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    last_fetched_at: Mapped[datetime | None] = mapped_column(nullable=True, default=None)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)

    # Relationships
    feed_items: Mapped[list["FeedItem"]] = relationship(
        "FeedItem", back_populates="source", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Source(id={self.id}, name={self.name}, url={self.url})>"
```

**Step 4: Run test to verify it passes**

Run:
```bash
uv run pytest tests/models/test_source.py -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add src/models/source.py tests/models/test_source.py
git commit -m "feat: add Source model"
```

---

### Task 6: Create APIKey Model

**Files:**
- Create: `src/models/api_key.py`
- Create: `tests/models/test_api_key.py`

**Step 1: Write the test**

```python
# tests/models/test_api_key.py
"""Tests for APIKey model."""

from src.models.api_key import APIKey


def test_api_key_model_has_required_fields():
    """Test that APIKey model has all required fields."""
    api_key = APIKey(
        key="test-api-key-12345",
        name="Test Key",
    )
    assert api_key.key == "test-api-key-12345"
    assert api_key.name == "Test Key"
    assert api_key.is_active is True


def test_api_key_name_is_optional():
    """Test that APIKey name is optional."""
    api_key = APIKey(key="test-key")
    assert api_key.name is None
```

**Step 2: Run test to verify it fails**

Run:
```bash
uv run pytest tests/models/test_api_key.py -v
```

Expected: FAIL - Module not found

**Step 3: Write minimal implementation**

```python
# src/models/api_key.py
"""API Key model for authentication."""

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, TimestampMixin


class APIKey(Base, TimestampMixin):
    """API key for authentication."""

    __tablename__ = "api_keys"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    key: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True, default=None)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    def __repr__(self) -> str:
        return f"<APIKey(id={self.id}, name={self.name})>"
```

**Step 4: Run test to verify it passes**

Run:
```bash
uv run pytest tests/models/test_api_key.py -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add src/models/api_key.py tests/models/test_api_key.py
git commit -m "feat: add APIKey model"
```

---

### Task 7: Create FeedItem Model

**Files:**
- Create: `src/models/feed_item.py`
- Create: `tests/models/test_feed_item.py`

**Step 1: Write the test**

```python
# tests/models/test_feed_item.py
"""Tests for FeedItem model."""

from datetime import datetime

from src.models.feed_item import FeedItem


def test_feed_item_model_has_required_fields():
    """Test that FeedItem model has all required fields."""
    item = FeedItem(
        source_id=1,
        title="Test Article",
        link="https://example.com/article/1",
        description="This is a test article",
        published_at=datetime(2026, 3, 18, 10, 0, 0),
    )
    assert item.source_id == 1
    assert item.title == "Test Article"
    assert item.link == "https://example.com/article/1"
    assert item.description == "This is a test article"


def test_feed_item_optional_fields():
    """Test that FeedItem optional fields can be None."""
    item = FeedItem(
        source_id=1,
        title="Test",
        link="https://example.com/test",
    )
    assert item.description is None
    assert item.published_at is None
```

**Step 2: Run test to verify it fails**

Run:
```bash
uv run pytest tests/models/test_feed_item.py -v
```

Expected: FAIL - Module not found

**Step 3: Write minimal implementation**

```python
# src/models/feed_item.py
"""FeedItem model for cached RSS items."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base, TimestampMixin


class FeedItem(Base, TimestampMixin):
    """Cached RSS feed item."""

    __tablename__ = "feed_items"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    source_id: Mapped[int] = mapped_column(Integer, ForeignKey("sources.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    link: Mapped[str] = mapped_column(String(2048), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    published_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, default=None)
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=func.now()
    )

    # Relationships
    source: Mapped["Source"] = relationship("Source", back_populates="feed_items")

    def __repr__(self) -> str:
        return f"<FeedItem(id={self.id}, title={self.title[:30]}...)>"
```

**Step 4: Run test to verify it passes**

Run:
```bash
uv run pytest tests/models/test_feed_item.py -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add src/models/feed_item.py tests/models/test_feed_item.py
git commit -m "feat: add FeedItem model"
```

---

### Task 8: Create ErrorLog Model

**Files:**
- Create: `src/models/error_log.py`
- Create: `tests/models/test_error_log.py`

**Step 1: Write the test**

```python
# tests/models/test_error_log.py
"""Tests for ErrorLog model."""

from src.models.error_log import ErrorLog


def test_error_log_model_has_required_fields():
    """Test that ErrorLog model has all required fields."""
    log = ErrorLog(
        error_type="HTTPError",
        error_message="Connection timeout",
    )
    assert log.error_type == "HTTPError"
    assert log.error_message == "Connection timeout"
    assert log.source_id is None


def test_error_log_with_source():
    """Test that ErrorLog can be associated with a source."""
    log = ErrorLog(
        source_id=1,
        error_type="ParseError",
        error_message="Invalid RSS format",
    )
    assert log.source_id == 1
```

**Step 2: Run test to verify it fails**

Run:
```bash
uv run pytest tests/models/test_error_log.py -v
```

Expected: FAIL - Module not found

**Step 3: Write minimal implementation**

```python
# src/models/error_log.py
"""ErrorLog model for tracking errors."""

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base, TimestampMixin


class ErrorLog(Base, TimestampMixin):
    """Error log for tracking fetch and parse errors."""

    __tablename__ = "error_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    source_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("sources.id"), nullable=True, default=None
    )
    error_type: Mapped[str] = mapped_column(String(100), nullable=False)
    error_message: Mapped[str] = mapped_column(Text, nullable=False)

    # Relationships
    source: Mapped["Source | None"] = relationship("Source")

    def __repr__(self) -> str:
        return f"<ErrorLog(id={self.id}, type={self.error_type})>"
```

**Step 4: Run test to verify it passes**

Run:
```bash
uv run pytest tests/models/test_error_log.py -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add src/models/error_log.py tests/models/test_error_log.py
git commit -m "feat: add ErrorLog model"
```

---

### Task 9: Create Stats Model

**Files:**
- Create: `src/models/stats.py`
- Create: `tests/models/test_stats.py`

**Step 1: Write the test**

```python
# tests/models/test_stats.py
"""Tests for Stats model."""

from datetime import date

from src.models.stats import Stats


def test_stats_model_has_required_fields():
    """Test that Stats model has all required fields."""
    stats = Stats(
        date=date(2026, 3, 18),
        total_requests=100,
        successful_fetches=50,
        failed_fetches=2,
    )
    assert stats.date == date(2026, 3, 18)
    assert stats.total_requests == 100
    assert stats.successful_fetches == 50
    assert stats.failed_fetches == 2


def test_stats_default_values():
    """Test that Stats model has correct default values."""
    stats = Stats(date=date(2026, 3, 18))
    assert stats.total_requests == 0
    assert stats.successful_fetches == 0
    assert stats.failed_fetches == 0
```

**Step 2: Run test to verify it fails**

Run:
```bash
uv run pytest tests/models/test_stats.py -v
```

Expected: FAIL - Module not found

**Step 3: Write minimal implementation**

```python
# src/models/stats.py
"""Stats model for daily statistics."""

from datetime import date

from sqlalchemy import Date, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, TimestampMixin


class Stats(Base, TimestampMixin):
    """Daily statistics for monitoring."""

    __tablename__ = "stats"
    __table_args__ = (UniqueConstraint("date", name="uq_stats_date"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    total_requests: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    successful_fetches: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failed_fetches: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    def __repr__(self) -> str:
        return f"<Stats(date={self.date}, requests={self.total_requests})>"
```

**Step 4: Run test to verify it passes**

Run:
```bash
uv run pytest tests/models/test_stats.py -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add src/models/stats.py tests/models/test_stats.py
git commit -m "feat: add Stats model"
```

---

### Task 10: Update Models __init__.py

**Files:**
- Modify: `src/models/__init__.py`

**Step 1: Update __init__.py**

```python
# src/models/__init__.py
"""Data models for RSS Aggregator."""

from src.models.api_key import APIKey
from src.models.base import Base, TimestampMixin
from src.models.error_log import ErrorLog
from src.models.feed_item import FeedItem
from src.models.source import Source
from src.models.stats import Stats

__all__ = [
    "Base",
    "TimestampMixin",
    "Source",
    "APIKey",
    "FeedItem",
    "ErrorLog",
    "Stats",
]
```

**Step 2: Run all model tests**

Run:
```bash
uv run pytest tests/models/ -v
```

Expected: All PASS

**Step 3: Commit**

```bash
git add src/models/__init__.py
git commit -m "chore: export all models from __init__.py"
```

---

## Phase 3: Database Layer

### Task 11: Create Database Engine and Session

**Files:**
- Create: `src/db/database.py`
- Modify: `tests/conftest.py`

**Step 1: Write the test**

```python
# tests/db/test_database.py
"""Tests for database configuration."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.database import async_session_factory, engine


@pytest.mark.asyncio
async def test_async_session_factory():
    """Test that async session factory creates valid sessions."""
    async with async_session_factory() as session:
        assert isinstance(session, AsyncSession)


@pytest.mark.asyncio
async def test_engine_is_async():
    """Test that engine is async."""
    assert engine.name == "sqlite"
```

**Step 2: Run test to verify it fails**

Run:
```bash
uv run pytest tests/db/test_database.py -v
```

Expected: FAIL - Module not found

**Step 3: Write minimal implementation**

```python
# src/db/database.py
"""Database configuration and session management."""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.config import settings

# Create async engine
engine = create_async_engine(
    settings.database_url,
    echo=settings.app_debug,
    future=True,
)

# Create session factory
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting async database sessions."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
```

**Step 4: Update pytest conftest.py**

```python
# tests/conftest.py
"""Pytest configuration and fixtures."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.database import async_session_factory, engine
from src.models import Base


@pytest.fixture
def anyio_backend():
    """Use asyncio as the async backend."""
    return "asyncio"


@pytest.fixture
async def db_session():
    """Create a test database session."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_factory() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
```

**Step 5: Run test to verify it passes**

Run:
```bash
uv run pytest tests/db/test_database.py -v
```

Expected: PASS

**Step 6: Commit**

```bash
git add src/db/database.py tests/db/test_database.py tests/conftest.py
git commit -m "feat: add async database engine and session factory"
```

---

### Task 12: Set Up Alembic Migrations

**Files:**
- Create: `alembic.ini`
- Create: `alembic/env.py`
- Create: `alembic/script.py.mako`

**Step 1: Initialize Alembic**

Run:
```bash
uv run alembic init alembic
```

Expected: Creates alembic directory and alembic.ini

**Step 2: Update alembic/env.py for async**

```python
# alembic/env.py
"""Alembic environment configuration for async migrations."""

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from src.config import settings
from src.models import Base  # noqa: F401

config = context.config

# Set database URL from settings
config.set_main_option("sqlalchemy.url", settings.database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Run migrations with connection."""
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations in async mode."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

**Step 3: Create initial migration**

Run:
```bash
uv run alembic revision --autogenerate -m "Initial schema"
```

Expected: Creates migration file in alembic/versions/

**Step 4: Commit**

```bash
git add alembic.ini alembic/
git commit -m "chore: set up alembic migrations for async sqlite"
```

---

## Phase 4: Services

### Task 13: Create AuthService

**Files:**
- Create: `src/services/auth_service.py`
- Create: `tests/services/test_auth_service.py`

**Step 1: Write the test**

```python
# tests/services/test_auth_service.py
"""Tests for AuthService."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import APIKey
from src.services.auth_service import AuthService


@pytest.fixture
async def auth_service(db_session: AsyncSession) -> AuthService:
    """Create AuthService instance."""
    return AuthService(db_session)


@pytest.fixture
async def test_api_key(db_session: AsyncSession) -> APIKey:
    """Create a test API key."""
    api_key = APIKey(key="test-key-12345", name="Test Key")
    db_session.add(api_key)
    await db_session.commit()
    return api_key


@pytest.mark.asyncio
async def test_validate_key_returns_true_for_valid_key(
    auth_service: AuthService, test_api_key: APIKey
):
    """Test that validate_key returns True for valid key."""
    result = await auth_service.validate_key("test-key-12345")
    assert result is True


@pytest.mark.asyncio
async def test_validate_key_returns_false_for_invalid_key(
    auth_service: AuthService,
):
    """Test that validate_key returns False for invalid key."""
    result = await auth_service.validate_key("invalid-key")
    assert result is False


@pytest.mark.asyncio
async def test_validate_key_returns_false_for_deleted_key(
    auth_service: AuthService, db_session: AsyncSession, test_api_key: APIKey
):
    """Test that validate_key returns False for deleted key."""
    test_api_key.soft_delete()
    await db_session.commit()

    result = await auth_service.validate_key("test-key-12345")
    assert result is False


@pytest.mark.asyncio
async def test_validate_key_returns_false_for_inactive_key(
    auth_service: AuthService, db_session: AsyncSession, test_api_key: APIKey
):
    """Test that validate_key returns False for inactive key."""
    test_api_key.is_active = False
    await db_session.commit()

    result = await auth_service.validate_key("test-key-12345")
    assert result is False
```

**Step 2: Run test to verify it fails**

Run:
```bash
uv run pytest tests/services/test_auth_service.py -v
```

Expected: FAIL - Module not found

**Step 3: Write minimal implementation**

```python
# src/services/auth_service.py
"""Authentication service for API key validation."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import APIKey


class AuthService:
    """Service for validating API keys."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def validate_key(self, api_key: str) -> bool:
        """Validate an API key.

        Args:
            api_key: The API key to validate.

        Returns:
            True if the key is valid, False otherwise.
        """
        result = await self.session.execute(
            select(APIKey).where(
                APIKey.key == api_key,
                APIKey.is_active == True,
                APIKey.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none() is not None
```

**Step 4: Run test to verify it passes**

Run:
```bash
uv run pytest tests/services/test_auth_service.py -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add src/services/auth_service.py tests/services/test_auth_service.py
git commit -m "feat: add AuthService for API key validation"
```

---

### Task 14: Create RateLimiter

**Files:**
- Create: `src/services/rate_limiter.py`
- Create: `tests/services/test_rate_limiter.py`

**Step 1: Write the test**

```python
# tests/services/test_rate_limiter.py
"""Tests for RateLimiter."""

import time

from src.services.rate_limiter import RateLimiter


def test_rate_limiter_allows_requests_within_limit():
    """Test that requests within limit are allowed."""
    limiter = RateLimiter(max_requests=5, window_seconds=60)

    for _ in range(5):
        assert limiter.is_allowed("test-key") is True


def test_rate_limiter_blocks_requests_over_limit():
    """Test that requests over limit are blocked."""
    limiter = RateLimiter(max_requests=3, window_seconds=60)

    for _ in range(3):
        limiter.is_allowed("test-key")

    assert limiter.is_allowed("test-key") is False


def test_rate_limiter_get_remaining():
    """Test that get_remaining returns correct count."""
    limiter = RateLimiter(max_requests=5, window_seconds=60)

    assert limiter.get_remaining("test-key") == 5
    limiter.is_allowed("test-key")
    assert limiter.get_remaining("test-key") == 4


def test_rate_limiter_different_keys_independent():
    """Test that different keys have independent limits."""
    limiter = RateLimiter(max_requests=2, window_seconds=60)

    limiter.is_allowed("key-1")
    limiter.is_allowed("key-1")
    assert limiter.is_allowed("key-1") is False

    assert limiter.is_allowed("key-2") is True
    assert limiter.is_allowed("key-2") is True


def test_rate_limiter_window_expires():
    """Test that rate limit resets after window expires."""
    limiter = RateLimiter(max_requests=2, window_seconds=1)

    limiter.is_allowed("test-key")
    limiter.is_allowed("test-key")
    assert limiter.is_allowed("test-key") is False

    time.sleep(1.1)
    assert limiter.is_allowed("test-key") is True
```

**Step 2: Run test to verify it fails**

Run:
```bash
uv run pytest tests/services/test_rate_limiter.py -v
```

Expected: FAIL - Module not found

**Step 3: Write minimal implementation**

```python
# src/services/rate_limiter.py
"""Rate limiting service using sliding window algorithm."""

import time
from collections import defaultdict
from threading import Lock
from typing import Dict, List


class RateLimiter:
    """In-memory rate limiter using sliding window algorithm."""

    def __init__(self, max_requests: int = 60, window_seconds: int = 60):
        """Initialize rate limiter.

        Args:
            max_requests: Maximum requests allowed in the window.
            window_seconds: Time window in seconds.
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: Dict[str, List[float]] = defaultdict(list)
        self._lock = Lock()

    def is_allowed(self, key: str) -> bool:
        """Check if a request is allowed for the given key.

        Args:
            key: The key to check (e.g., API key).

        Returns:
            True if the request is allowed, False if rate limited.
        """
        with self._lock:
            now = time.time()
            window_start = now - self.window_seconds

            # Remove expired requests
            self._requests[key] = [
                req_time
                for req_time in self._requests[key]
                if req_time > window_start
            ]

            # Check if limit exceeded
            if len(self._requests[key]) >= self.max_requests:
                return False

            # Record this request
            self._requests[key].append(now)
            return True

    def get_remaining(self, key: str) -> int:
        """Get remaining requests for a key.

        Args:
            key: The key to check.

        Returns:
            Number of remaining requests in the current window.
        """
        with self._lock:
            now = time.time()
            window_start = now - self.window_seconds

            valid_requests = [
                req_time
                for req_time in self._requests.get(key, [])
                if req_time > window_start
            ]

            return max(0, self.max_requests - len(valid_requests))

    def get_reset_time(self, key: str) -> float:
        """Get seconds until rate limit resets.

        Args:
            key: The key to check.

        Returns:
            Seconds until the rate limit window resets.
        """
        with self._lock:
            requests = self._requests.get(key, [])
            if not requests:
                return 0.0

            oldest = min(requests)
            reset_time = oldest + self.window_seconds - time.time()
            return max(0.0, reset_time)
```

**Step 4: Run test to verify it passes**

Run:
```bash
uv run pytest tests/services/test_rate_limiter.py -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add src/services/rate_limiter.py tests/services/test_rate_limiter.py
git commit -m "feat: add RateLimiter with sliding window algorithm"
```

---

**[計畫繼續於 Part 2 - 包含剩餘服務、API、排程器和部署任務]**

由於計畫文件很長，剩餘部分包含：
- Task 15-17: SourceService, FetchService, FeedService
- Task 18: FetchScheduler
- Task 19-26: API Layer (所有端點)
- Task 27-29: Testing
- Task 30-35: Deployment

**請問是否要我繼續生成完整的計畫文件？**