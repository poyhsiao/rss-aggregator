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

### Task 15: Create SourceService

**Files:**
- Create: `src/services/source_service.py`
- Create: `tests/services/test_source_service.py`

**Step 1: Write the test**

```python
# tests/services/test_source_service.py
"""Tests for SourceService."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import Source
from src.services.source_service import SourceService


@pytest.fixture
async def source_service(db_session: AsyncSession) -> SourceService:
    """Create SourceService instance."""
    return SourceService(db_session)


@pytest.mark.asyncio
async def test_create_source(source_service: SourceService):
    """Test creating a source."""
    source = await source_service.create_source(
        name="Test Feed",
        url="https://example.com/feed.xml",
        fetch_interval=900,
    )
    assert source.id is not None
    assert source.name == "Test Feed"
    assert source.url == "https://example.com/feed.xml"


@pytest.mark.asyncio
async def test_create_duplicate_url_raises_error(source_service: SourceService):
    """Test that creating duplicate URL raises error."""
    await source_service.create_source(
        name="Feed 1",
        url="https://example.com/feed.xml",
    )
    
    with pytest.raises(ValueError, match="already exists"):
        await source_service.create_source(
            name="Feed 2",
            url="https://example.com/feed.xml",
        )


@pytest.mark.asyncio
async def test_get_sources(source_service: SourceService):
    """Test getting all sources."""
    await source_service.create_source(name="Feed 1", url="https://example.com/1.xml")
    await source_service.create_source(name="Feed 2", url="https://example.com/2.xml")
    
    sources = await source_service.get_sources()
    assert len(sources) == 2


@pytest.mark.asyncio
async def test_get_source_by_id(source_service: SourceService):
    """Test getting source by ID."""
    created = await source_service.create_source(
        name="Test",
        url="https://example.com/feed.xml",
    )
    
    found = await source_service.get_source(created.id)
    assert found is not None
    assert found.name == "Test"


@pytest.mark.asyncio
async def test_update_source(source_service: SourceService):
    """Test updating a source."""
    source = await source_service.create_source(
        name="Original",
        url="https://example.com/feed.xml",
    )
    
    updated = await source_service.update_source(
        source.id,
        name="Updated",
        fetch_interval=1800,
    )
    assert updated.name == "Updated"
    assert updated.fetch_interval == 1800


@pytest.mark.asyncio
async def test_delete_source(source_service: SourceService):
    """Test soft deleting a source."""
    source = await source_service.create_source(
        name="Test",
        url="https://example.com/feed.xml",
    )
    
    await source_service.delete_source(source.id)
    
    # Verify soft delete
    deleted = await source_service.get_source(source.id)
    assert deleted is None
    
    # Verify still in database with deleted_at
    all_sources = await source_service.get_sources(include_deleted=True)
    assert len(all_sources) == 1
    assert all_sources[0].deleted_at is not None
```

**Step 2: Run test to verify it fails**

Run:
```bash
uv run pytest tests/services/test_source_service.py -v
```

Expected: FAIL - Module not found

**Step 3: Write minimal implementation**

```python
# src/services/source_service.py
"""Service for managing RSS sources."""

from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import Source


class SourceService:
    """Service for managing RSS feed sources."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_source(
        self,
        name: str,
        url: str,
        fetch_interval: int = 900,
    ) -> Source:
        """Create a new RSS source.

        Args:
            name: Display name for the source.
            url: RSS feed URL.
            fetch_interval: Fetch interval in seconds.

        Returns:
            Created Source instance.

        Raises:
            ValueError: If URL already exists.
        """
        # Check for duplicate URL
        existing = await self.session.execute(
            select(Source).where(Source.url == url, Source.deleted_at.is_(None))
        )
        if existing.scalar_one_or_none():
            raise ValueError(f"Source with URL {url} already exists")

        source = Source(
            name=name,
            url=url,
            fetch_interval=fetch_interval,
        )
        self.session.add(source)
        await self.session.flush()
        await self.session.refresh(source)
        return source

    async def get_sources(self, include_deleted: bool = False) -> List[Source]:
        """Get all sources.

        Args:
            include_deleted: Include soft-deleted sources.

        Returns:
            List of Source instances.
        """
        query = select(Source)
        if not include_deleted:
            query = query.where(Source.deleted_at.is_(None))
        query = query.order_by(Source.created_at.desc())

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_source(self, source_id: int) -> Source | None:
        """Get a source by ID.

        Args:
            source_id: Source ID.

        Returns:
            Source instance or None if not found.
        """
        result = await self.session.execute(
            select(Source).where(
                Source.id == source_id,
                Source.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def update_source(
        self,
        source_id: int,
        **kwargs,
    ) -> Source:
        """Update a source.

        Args:
            source_id: Source ID.
            **kwargs: Fields to update.

        Returns:
            Updated Source instance.

        Raises:
            ValueError: If source not found.
        """
        source = await self.get_source(source_id)
        if not source:
            raise ValueError(f"Source {source_id} not found")

        for key, value in kwargs.items():
            if hasattr(source, key):
                setattr(source, key, value)

        await self.session.flush()
        await self.session.refresh(source)
        return source

    async def delete_source(self, source_id: int) -> None:
        """Soft delete a source.

        Args:
            source_id: Source ID.

        Raises:
            ValueError: If source not found.
        """
        source = await self.get_source(source_id)
        if not source:
            raise ValueError(f"Source {source_id} not found")

        source.soft_delete()
        await self.session.flush()

    async def get_active_sources(self) -> List[Source]:
        """Get all active sources that need fetching.

        Returns:
            List of active Source instances.
        """
        result = await self.session.execute(
            select(Source).where(
                Source.is_active == True,
                Source.deleted_at.is_(None),
            )
        )
        return list(result.scalars().all())
```

**Step 4: Run test to verify it passes**

Run:
```bash
uv run pytest tests/services/test_source_service.py -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add src/services/source_service.py tests/services/test_source_service.py
git commit -m "feat: add SourceService for RSS source management"
```

---

### Task 16: Create FetchService

**Files:**
- Create: `src/services/fetch_service.py`
- Create: `tests/services/test_fetch_service.py`

**Step 1: Write the test**

```python
# tests/services/test_fetch_service.py
"""Tests for FetchService."""

import pytest
from unittest.mock import AsyncMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import Source, FeedItem
from src.services.fetch_service import FetchService


@pytest.fixture
async def fetch_service(db_session: AsyncSession) -> FetchService:
    """Create FetchService instance."""
    return FetchService(db_session)


@pytest.fixture
async def test_source(db_session: AsyncSession) -> Source:
    """Create a test source."""
    source = Source(name="Test", url="https://example.com/feed.xml")
    db_session.add(source)
    await db_session.commit()
    return source


@pytest.mark.asyncio
async def test_parse_rss_valid_feed(fetch_service: FetchService):
    """Test parsing valid RSS feed."""
    rss_content = """<?xml version="1.0" encoding="UTF-8"?>
    <rss version="2.0">
        <channel>
            <title>Test Feed</title>
            <item>
                <title>Item 1</title>
                <link>https://example.com/1</link>
                <description>Description 1</description>
            </item>
            <item>
                <title>Item 2</title>
                <link>https://example.com/2</link>
            </item>
        </channel>
    </rss>
    """
    
    items = fetch_service.parse_rss(rss_content)
    assert len(items) == 2
    assert items[0]["title"] == "Item 1"
    assert items[0]["link"] == "https://example.com/1"


@pytest.mark.asyncio
async def test_fetch_source_stores_items(
    fetch_service: FetchService, test_source: Source
):
    """Test that fetch_source stores feed items."""
    mock_rss = """<?xml version="1.0"?>
    <rss version="2.0">
        <channel>
            <item>
                <title>Test Item</title>
                <link>https://example.com/item</link>
            </item>
        </channel>
    </rss>
    """
    
    with patch("httpx.AsyncClient.get") as mock_get:
        mock_response = AsyncMock()
        mock_response.text = mock_rss
        mock_response.raise_for_status = AsyncMock()
        mock_get.return_value = mock_response
        
        await fetch_service.fetch_source(test_source)
    
    # Verify item was stored
    items = await fetch_service.session.execute(
        select(FeedItem).where(FeedItem.source_id == test_source.id)
    )
    feed_items = list(items.scalars().all())
    assert len(feed_items) == 1
    assert feed_items[0].title == "Test Item"
```

**Step 2: Run test to verify it fails**

Run:
```bash
uv run pytest tests/services/test_fetch_service.py -v
```

Expected: FAIL - Module not found

**Step 3: Write minimal implementation**

```python
# src/services/fetch_service.py
"""Service for fetching and parsing RSS feeds."""

import asyncio
from datetime import datetime
from typing import List, Dict, Any

import feedparser
import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.models import Source, FeedItem, ErrorLog


class FetchService:
    """Service for fetching and parsing RSS feeds."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.timeout = settings.fetch_timeout
        self.retry_count = settings.fetch_retry_count
        self.retry_delay = settings.fetch_retry_delay

    def parse_rss(self, content: str) -> List[Dict[str, Any]]:
        """Parse RSS/Atom feed content.

        Args:
            content: RSS XML content.

        Returns:
            List of feed items with title, link, description, published_at.
        """
        feed = feedparser.parse(content)
        items = []

        for entry in feed.entries:
            item = {
                "title": entry.get("title", ""),
                "link": entry.get("link", ""),
                "description": entry.get("summary") or entry.get("description"),
            }

            # Parse publication date
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                item["published_at"] = datetime(*entry.published_parsed[:6])
            elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
                item["published_at"] = datetime(*entry.updated_parsed[:6])
            else:
                item["published_at"] = None

            items.append(item)

        return items

    async def fetch_source(self, source: Source) -> List[FeedItem]:
        """Fetch and store RSS feed for a source.

        Args:
            source: Source to fetch.

        Returns:
            List of stored FeedItem instances.
        """
        content = await self._fetch_with_retry(source.url)
        
        if content is None:
            return []

        items = self.parse_rss(content)
        stored_items = []

        # Clear old items for this source
        await self.session.execute(
            select(FeedItem).where(FeedItem.source_id == source.id)
        )
        # Soft delete old items
        old_items = await self.session.execute(
            select(FeedItem).where(FeedItem.source_id == source.id)
        )
        for old_item in old_items.scalars().all():
            old_item.soft_delete()

        # Store new items
        for item_data in items[: settings.max_feed_items]:
            feed_item = FeedItem(
                source_id=source.id,
                title=item_data["title"],
                link=item_data["link"],
                description=item_data["description"],
                published_at=item_data["published_at"],
            )
            self.session.add(feed_item)
            stored_items.append(feed_item)

        # Update source status
        source.last_fetched_at = datetime.utcnow()
        source.last_error = None

        await self.session.flush()
        return stored_items

    async def _fetch_with_retry(self, url: str) -> str | None:
        """Fetch URL with retry logic.

        Args:
            url: URL to fetch.

        Returns:
            Content string or None if all retries failed.
        """
        for attempt in range(self.retry_count):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.get(url)
                    response.raise_for_status()
                    return response.text
            except Exception as e:
                if attempt < self.retry_count - 1:
                    await asyncio.sleep(self.retry_delay)
                else:
                    await self._log_error(url, str(e))
                    return None

    async def _log_error(self, url: str, error_message: str) -> None:
        """Log fetch error.

        Args:
            url: URL that failed.
            error_message: Error message.
        """
        log = ErrorLog(
            error_type="FetchError",
            error_message=f"Failed to fetch {url}: {error_message}",
        )
        self.session.add(log)
        await self.session.flush()

    async def fetch_all(self) -> Dict[int, List[FeedItem]]:
        """Fetch all active sources that need updating.

        Returns:
            Dict mapping source_id to list of fetched items.
        """
        # Get sources that need fetching
        result = await self.session.execute(
            select(Source).where(
                Source.is_active == True,
                Source.deleted_at.is_(None),
            )
        )
        sources = list(result.scalars().all())

        results = {}
        for source in sources:
            items = await self.fetch_source(source)
            results[source.id] = items

        return results
```

**Step 4: Run test to verify it passes**

Run:
```bash
uv run pytest tests/services/test_fetch_service.py -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add src/services/fetch_service.py tests/services/test_fetch_service.py
git commit -m "feat: add FetchService for RSS fetching and parsing"
```

---

### Task 17: Create FeedService

**Files:**
- Create: `src/services/feed_service.py`
- Create: `tests/services/test_feed_service.py`

**Step 1: Write the test**

```python
# tests/services/test_feed_service.py
"""Tests for FeedService."""

import pytest
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import Source, FeedItem
from src.services.feed_service import FeedService
from src.services.source_service import SourceService


@pytest.fixture
async def feed_service(db_session: AsyncSession) -> FeedService:
    """Create FeedService instance."""
    return FeedService(db_session)


@pytest.fixture
async def sample_data(db_session: AsyncSession):
    """Create sample sources and feed items."""
    source1 = Source(name="Tech News", url="https://tech.com/feed.xml")
    source2 = Source(name="World News", url="https://world.com/feed.xml")
    db_session.add_all([source1, source2])
    await db_session.flush()

    now = datetime.utcnow()
    items = [
        FeedItem(
            source_id=source1.id,
            title="Python 3.13 Released",
            link="https://tech.com/python-3.13",
            description="New Python version",
            published_at=now - timedelta(hours=1),
        ),
        FeedItem(
            source_id=source1.id,
            title="AI Breakthrough",
            link="https://tech.com/ai",
            description="AI news",
            published_at=now - timedelta(hours=2),
        ),
        FeedItem(
            source_id=source2.id,
            title="Election Results",
            link="https://world.com/election",
            description="World news",
            published_at=now - timedelta(hours=3),
        ),
    ]
    db_session.add_all(items)
    await db_session.commit()
    return {"sources": [source1, source2], "items": items}


@pytest.mark.asyncio
async def test_get_aggregated_feed_returns_rss_xml(
    feed_service: FeedService, sample_data
):
    """Test that get_aggregated_feed returns valid RSS XML."""
    rss_xml = await feed_service.get_aggregated_feed()
    
    assert "<?xml version=" in rss_xml
    assert "<rss version=" in rss_xml
    assert "<channel>" in rss_xml
    assert "</channel>" in rss_xml
    assert "</rss>" in rss_xml


@pytest.mark.asyncio
async def test_get_aggregated_feed_includes_all_items(
    feed_service: FeedService, sample_data
):
    """Test that feed includes all items."""
    rss_xml = await feed_service.get_aggregated_feed()
    
    assert "Python 3.13 Released" in rss_xml
    assert "AI Breakthrough" in rss_xml
    assert "Election Results" in rss_xml


@pytest.mark.asyncio
async def test_get_aggregated_feed_filters_by_time(
    feed_service: FeedService, sample_data
):
    """Test that valid_time filters items correctly."""
    # Only items from last 2 hours
    rss_xml = await feed_service.get_aggregated_feed(valid_time=2)
    
    assert "Python 3.13 Released" in rss_xml
    assert "AI Breakthrough" in rss_xml
    assert "Election Results" not in rss_xml


@pytest.mark.asyncio
async def test_get_aggregated_feed_filters_by_keywords(
    feed_service: FeedService, sample_data
):
    """Test that keywords filter items correctly."""
    rss_xml = await feed_service.get_aggregated_feed(keywords="Python;AI")
    
    assert "Python 3.13 Released" in rss_xml
    assert "AI Breakthrough" in rss_xml
    assert "Election Results" not in rss_xml


@pytest.mark.asyncio
async def test_get_aggregated_feed_sorts_by_published_at(
    feed_service: FeedService, sample_data
):
    """Test sorting by published_at."""
    rss_xml = await feed_service.get_aggregated_feed(
        sort_by="published_at",
        sort_order="desc",
    )
    
    # Newest first
    python_pos = rss_xml.find("Python 3.13 Released")
    election_pos = rss_xml.find("Election Results")
    assert python_pos < election_pos


@pytest.mark.asyncio
async def test_get_aggregated_feed_sorts_by_source(
    feed_service: FeedService, sample_data
):
    """Test sorting by source name."""
    rss_xml = await feed_service.get_aggregated_feed(
        sort_by="source",
        sort_order="asc",
    )
    
    # Tech News before World News
    python_pos = rss_xml.find("Python 3.13 Released")
    election_pos = rss_xml.find("Election Results")
    assert python_pos < election_pos
```

**Step 2: Run test to verify it fails**

Run:
```bash
uv run pytest tests/services/test_feed_service.py -v
```

Expected: FAIL - Module not found

**Step 3: Write minimal implementation**

```python
# src/services/feed_service.py
"""Service for aggregating and filtering RSS feeds."""

import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.models import FeedItem, Source


class FeedService:
    """Service for aggregating RSS feeds."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_aggregated_feed(
        self,
        sort_by: str = "published_at",
        sort_order: str = "desc",
        valid_time: Optional[int] = None,
        keywords: Optional[str] = None,
    ) -> str:
        """Get aggregated RSS feed.

        Args:
            sort_by: Sort field ("published_at" or "source").
            sort_order: Sort direction ("asc" or "desc").
            valid_time: Time range in hours (None = all items).
            keywords: Semicolon-separated keywords for title filtering.

        Returns:
            RSS 2.0 XML string.
        """
        items = await self._fetch_items(
            sort_by=sort_by,
            sort_order=sort_order,
            valid_time=valid_time,
            keywords=keywords,
        )
        return self._generate_rss_xml(items)

    async def _fetch_items(
        self,
        sort_by: str,
        sort_order: str,
        valid_time: Optional[int],
        keywords: Optional[str],
    ) -> list:
        """Fetch filtered feed items from database."""
        query = (
            select(FeedItem)
            .options(joinedload(FeedItem.source))
            .where(
                FeedItem.deleted_at.is_(None),
                FeedItem.source.has(Source.is_active == True),
                FeedItem.source.has(Source.deleted_at.is_(None)),
            )
        )

        # Time filter
        if valid_time is not None:
            cutoff = datetime.utcnow() - timedelta(hours=valid_time)
            query = query.where(FeedItem.published_at >= cutoff)

        # Keyword filter (OR logic)
        if keywords:
            keyword_list = [k.strip() for k in keywords.split(";") if k.strip()]
            if keyword_list:
                conditions = [
                    FeedItem.title.ilike(f"%{kw}%") for kw in keyword_list
                ]
                from sqlalchemy import or_
                query = query.where(or_(*conditions))

        # Sorting
        if sort_by == "source":
            order_col = Source.name
            query = query.join(Source)
        else:
            order_col = FeedItem.published_at

        if sort_order == "desc":
            query = query.order_by(order_col.desc())
        else:
            query = query.order_by(order_col.asc())

        result = await self.session.execute(query)
        return list(result.unique().scalars().all())

    def _generate_rss_xml(self, items: list) -> str:
        """Generate RSS 2.0 XML from items."""
        rss = ET.Element("rss", version="2.0")
        channel = ET.SubElement(rss, "channel")

        # Channel metadata
        ET.SubElement(channel, "title").text = "RSS Aggregator"
        ET.SubElement(channel, "link").text = "https://github.com/rss-aggregator"
        ET.SubElement(channel, "description").text = "Aggregated RSS Feed"
        ET.SubElement(channel, "language").text = "en-us"
        ET.SubElement(channel, "lastBuildDate").text = datetime.utcnow().strftime(
            "%a, %d %b %Y %H:%M:%S GMT"
        )

        # Items
        for item in items:
            item_elem = ET.SubElement(channel, "item")
            ET.SubElement(item_elem, "title").text = item.title
            ET.SubElement(item_elem, "link").text = item.link
            ET.SubElement(item_elem, "description").text = item.description or ""

            if item.published_at:
                ET.SubElement(item_elem, "pubDate").text = item.published_at.strftime(
                    "%a, %d %b %Y %H:%M:%S GMT"
                )

            if item.source:
                ET.SubElement(
                    item_elem, "source", url=item.source.url
                ).text = item.source.name

        return ET.tostring(rss, encoding="unicode", xml_declaration=True)
```

**Step 4: Run test to verify it passes**

Run:
```bash
uv run pytest tests/services/test_feed_service.py -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add src/services/feed_service.py tests/services/test_feed_service.py
git commit -m "feat: add FeedService for RSS aggregation"
```

---

## Phase 5: Scheduler

### Task 18: Create FetchScheduler

**Files:**
- Create: `src/scheduler/fetch_scheduler.py`
- Create: `tests/scheduler/test_fetch_scheduler.py`

**Step 1: Write the test**

```python
# tests/scheduler/test_fetch_scheduler.py
"""Tests for FetchScheduler."""

import pytest
from unittest.mock import AsyncMock, patch

from src.scheduler.fetch_scheduler import FetchScheduler


@pytest.fixture
def mock_fetch_service():
    """Create mock fetch service."""
    return AsyncMock()


@pytest.fixture
def scheduler(mock_fetch_service) -> FetchScheduler:
    """Create FetchScheduler instance."""
    return FetchScheduler(
        fetch_service=mock_fetch_service,
        check_interval=1,
        max_concurrent=2,
    )


@pytest.mark.asyncio
async def test_scheduler_can_start_and_stop(scheduler: FetchScheduler):
    """Test that scheduler can start and stop."""
    await scheduler.start()
    assert scheduler._running is True
    
    await scheduler.stop()
    assert scheduler._running is False


@pytest.mark.asyncio
async def test_refresh_all_calls_fetch_all(scheduler: FetchScheduler, mock_fetch_service):
    """Test that refresh_all calls fetch_service.fetch_all."""
    await scheduler.refresh_all()
    mock_fetch_service.fetch_all.assert_called_once()


@pytest.mark.asyncio
async def test_refresh_source_calls_fetch_source(scheduler: FetchScheduler, mock_fetch_service):
    """Test that refresh_source calls fetch_service.fetch_source."""
    from src.models import Source
    
    mock_source = Source(name="Test", url="https://example.com/feed.xml")
    mock_fetch_service.get_source.return_value = mock_source
    
    await scheduler.refresh_source(1)
    mock_fetch_service.get_source.assert_called_once_with(1)
    mock_fetch_service.fetch_source.assert_called_once_with(mock_source)
```

**Step 2: Run test to verify it fails**

Run:
```bash
uv run pytest tests/scheduler/test_fetch_scheduler.py -v
```

Expected: FAIL - Module not found

**Step 3: Write minimal implementation**

```python
# src/scheduler/fetch_scheduler.py
"""Scheduler for periodic RSS fetching."""

import asyncio
import logging
from typing import TYPE_CHECKING

from src.config import settings

if TYPE_CHECKING:
    from src.services.fetch_service import FetchService

logger = logging.getLogger(__name__)


class FetchScheduler:
    """Scheduler for periodic RSS feed fetching."""

    def __init__(
        self,
        fetch_service: "FetchService",
        check_interval: int = 60,
        max_concurrent: int = 5,
    ):
        """Initialize scheduler.

        Args:
            fetch_service: Service for fetching feeds.
            check_interval: Seconds between checks.
            max_concurrent: Maximum concurrent fetches.
        """
        self.fetch_service = fetch_service
        self.check_interval = check_interval
        self.max_concurrent = max_concurrent
        self._running = False
        self._task: asyncio.Task | None = None

    async def start(self) -> None:
        """Start the scheduler."""
        if self._running:
            return
        
        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info("Fetch scheduler started")

    async def stop(self) -> None:
        """Stop the scheduler."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Fetch scheduler stopped")

    async def _run_loop(self) -> None:
        """Main scheduler loop."""
        while self._running:
            try:
                await self._check_and_fetch()
            except Exception as e:
                logger.error(f"Scheduler error: {e}")

            await asyncio.sleep(self.check_interval)

    async def _check_and_fetch(self) -> None:
        """Check sources and fetch those that need updating."""
        from datetime import datetime, timedelta
        from sqlalchemy import select
        from src.models import Source

        # Get sources that need fetching
        now = datetime.utcnow()
        result = await self.fetch_service.session.execute(
            select(Source).where(
                Source.is_active == True,
                Source.deleted_at.is_(None),
            )
        )
        sources = list(result.scalars().all())

        sources_to_fetch = [
            s for s in sources
            if s.last_fetched_at is None
            or (now - s.last_fetched_at).total_seconds() >= s.fetch_interval
        ]

        if not sources_to_fetch:
            return

        # Fetch with concurrency control
        semaphore = asyncio.Semaphore(self.max_concurrent)

        async def fetch_with_semaphore(source):
            async with semaphore:
                await self.fetch_service.fetch_source(source)

        tasks = [fetch_with_semaphore(s) for s in sources_to_fetch]
        await asyncio.gather(*tasks, return_exceptions=True)

    async def refresh_source(self, source_id: int) -> None:
        """Manually refresh a specific source.

        Args:
            source_id: Source ID to refresh.
        """
        source = await self.fetch_service.get_source(source_id)
        if source:
            await self.fetch_service.fetch_source(source)

    async def refresh_all(self) -> None:
        """Manually refresh all active sources."""
        await self.fetch_service.fetch_all()
```

**Step 4: Run test to verify it passes**

Run:
```bash
uv run pytest tests/scheduler/test_fetch_scheduler.py -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add src/scheduler/fetch_scheduler.py tests/scheduler/test_fetch_scheduler.py
git commit -m "feat: add FetchScheduler for periodic RSS fetching"
```

---

## Phase 6: API Layer

### Task 19: Create Dependency Injection Module

**Files:**
- Create: `src/api/deps.py`

**Step 1: Write the implementation**

```python
# src/api/deps.py
"""Dependency injection for FastAPI."""

from typing import AsyncGenerator

from fastapi import Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.db.database import get_session
from src.models import APIKey
from src.services.auth_service import AuthService
from src.services.feed_service import FeedService
from src.services.fetch_service import FetchService
from src.services.rate_limiter import RateLimiter
from src.services.source_service import SourceService
from src.scheduler.fetch_scheduler import FetchScheduler


# Global instances
_rate_limiter: RateLimiter | None = None
_scheduler: FetchScheduler | None = None


def get_rate_limiter() -> RateLimiter:
    """Get rate limiter instance."""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter(
            max_requests=settings.rate_limit_requests,
            window_seconds=settings.rate_limit_window,
        )
    return _rate_limiter


def get_scheduler() -> FetchScheduler:
    """Get scheduler instance."""
    return _scheduler


def set_scheduler(scheduler: FetchScheduler) -> None:
    """Set scheduler instance."""
    global _scheduler
    _scheduler = scheduler


async def get_auth_service(
    session: AsyncSession = Depends(get_session),
) -> AuthService:
    """Get AuthService instance."""
    return AuthService(session)


async def get_source_service(
    session: AsyncSession = Depends(get_session),
) -> SourceService:
    """Get SourceService instance."""
    return SourceService(session)


async def get_feed_service(
    session: AsyncSession = Depends(get_session),
) -> FeedService:
    """Get FeedService instance."""
    return FeedService(session)


async def get_fetch_service(
    session: AsyncSession = Depends(get_session),
) -> FetchService:
    """Get FetchService instance."""
    return FetchService(session)


async def require_api_key(
    x_api_key: str = Header(..., alias="X-API-Key"),
    auth_service: AuthService = Depends(get_auth_service),
    rate_limiter: RateLimiter = Depends(get_rate_limiter),
) -> str:
    """Validate API key and check rate limit.

    Args:
        x_api_key: API key from header.
        auth_service: Auth service instance.
        rate_limiter: Rate limiter instance.

    Returns:
        Validated API key.

    Raises:
        HTTPException: If key is invalid or rate limited.
    """
    # Check rate limit first
    if not rate_limiter.is_allowed(x_api_key):
        reset_time = rate_limiter.get_reset_time(x_api_key)
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded",
            headers={
                "X-RateLimit-Limit": str(rate_limiter.max_requests),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(int(reset_time)),
                "Retry-After": str(int(reset_time)),
            },
        )

    # Validate key
    if not await auth_service.validate_key(x_api_key):
        raise HTTPException(
            status_code=401,
            detail="Invalid API key",
        )

    return x_api_key
```

**Step 2: Commit**

```bash
git add src/api/deps.py
git commit -m "feat: add dependency injection module"
```

---

### Task 20: Create Health Endpoint

**Files:**
- Create: `src/api/routes/health.py`

**Step 1: Write the implementation**

```python
# src/api/routes/health.py
"""Health check endpoint."""

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    """Health check endpoint.

    Returns:
        Simple status message.
    """
    return {"status": "ok"}
```

**Step 2: Commit**

```bash
git add src/api/routes/health.py
git commit -m "feat: add health check endpoint"
```

---

### Task 21: Create Feed Routes

**Files:**
- Create: `src/api/routes/feed.py`

**Step 1: Write the implementation**

```python
# src/api/routes/feed.py
"""Feed API routes."""

from typing import Optional

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_feed_service, require_api_key
from src.services.feed_service import FeedService

router = APIRouter(prefix="/feed", tags=["feed"])


@router.get("")
async def get_feed(
    sort_by: str = Query(
        "published_at",
        regex="^(published_at|source)$",
        description="Sort by field",
    ),
    sort_order: str = Query(
        "desc",
        regex="^(asc|desc)$",
        description="Sort direction",
    ),
    valid_time: Optional[int] = Query(
        None,
        ge=1,
        description="Time range in hours",
    ),
    keywords: Optional[str] = Query(
        None,
        description="Keywords (semicolon-separated)",
    ),
    feed_service: FeedService = Depends(get_feed_service),
    _: str = Depends(require_api_key),
):
    """Get aggregated RSS feed.

    Returns RSS 2.0 XML with items from all active sources.
    Supports filtering by time range and keywords, and sorting.
    """
    rss_xml = await feed_service.get_aggregated_feed(
        sort_by=sort_by,
        sort_order=sort_order,
        valid_time=valid_time,
        keywords=keywords,
    )

    return Response(
        content=rss_xml,
        media_type="application/xml",
        headers={
            "Cache-Control": "public, max-age=300",
        },
    )
```

**Step 2: Commit**

```bash
git add src/api/routes/feed.py
git commit -m "feat: add feed routes"
```

---

### Task 22: Create Source Routes

**Files:**
- Create: `src/api/routes/sources.py`

**Step 1: Write the implementation**

```python
# src/api/routes/sources.py
"""Source management API routes."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, HttpUrl
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_scheduler, get_source_service, require_api_key
from src.services.source_service import SourceService

router = APIRouter(prefix="/sources", tags=["sources"])


class SourceCreate(BaseModel):
    """Schema for creating a source."""

    name: str
    url: str
    fetch_interval: int = 900


class SourceUpdate(BaseModel):
    """Schema for updating a source."""

    name: Optional[str] = None
    fetch_interval: Optional[int] = None
    is_active: Optional[bool] = None


class SourceResponse(BaseModel):
    """Schema for source response."""

    id: int
    name: str
    url: str
    fetch_interval: int
    is_active: bool
    last_fetched_at: str | None
    last_error: str | None

    class Config:
        from_attributes = True


class BatchCreate(BaseModel):
    """Schema for batch source creation."""

    sources: List[SourceCreate]


@router.get("", response_model=List[SourceResponse])
async def list_sources(
    source_service: SourceService = Depends(get_source_service),
    _: str = Depends(require_api_key),
):
    """List all sources."""
    sources = await source_service.get_sources()
    return [
        SourceResponse(
            id=s.id,
            name=s.name,
            url=s.url,
            fetch_interval=s.fetch_interval,
            is_active=s.is_active,
            last_fetched_at=s.last_fetched_at.isoformat() if s.last_fetched_at else None,
            last_error=s.last_error,
        )
        for s in sources
    ]


@router.post("", response_model=SourceResponse, status_code=status.HTTP_201_CREATED)
async def create_source(
    data: SourceCreate,
    source_service: SourceService = Depends(get_source_service),
    _: str = Depends(require_api_key),
):
    """Create a new source."""
    try:
        source = await source_service.create_source(
            name=data.name,
            url=data.url,
            fetch_interval=data.fetch_interval,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return SourceResponse(
        id=source.id,
        name=source.name,
        url=source.url,
        fetch_interval=source.fetch_interval,
        is_active=source.is_active,
        last_fetched_at=None,
        last_error=None,
    )


@router.post("/batch", status_code=status.HTTP_201_CREATED)
async def batch_create_sources(
    data: BatchCreate,
    source_service: SourceService = Depends(get_source_service),
    _: str = Depends(require_api_key),
):
    """Batch create sources."""
    created = []
    errors = []

    for source_data in data.sources:
        try:
            source = await source_service.create_source(
                name=source_data.name,
                url=source_data.url,
                fetch_interval=source_data.fetch_interval,
            )
            created.append({"id": source.id, "name": source.name})
        except ValueError as e:
            errors.append({"url": source_data.url, "error": str(e)})

    return {"created": len(created), "sources": created, "errors": errors}


@router.get("/{source_id}", response_model=SourceResponse)
async def get_source(
    source_id: int,
    source_service: SourceService = Depends(get_source_service),
    _: str = Depends(require_api_key),
):
    """Get a specific source."""
    source = await source_service.get_source(source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    return SourceResponse(
        id=source.id,
        name=source.name,
        url=source.url,
        fetch_interval=source.fetch_interval,
        is_active=source.is_active,
        last_fetched_at=source.last_fetched_at.isoformat() if source.last_fetched_at else None,
        last_error=source.last_error,
    )


@router.put("/{source_id}", response_model=SourceResponse)
async def update_source(
    source_id: int,
    data: SourceUpdate,
    source_service: SourceService = Depends(get_source_service),
    _: str = Depends(require_api_key),
):
    """Update a source."""
    try:
        source = await source_service.update_source(
            source_id,
            **{k: v for k, v in data.dict().items() if v is not None},
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return SourceResponse(
        id=source.id,
        name=source.name,
        url=source.url,
        fetch_interval=source.fetch_interval,
        is_active=source.is_active,
        last_fetched_at=source.last_fetched_at.isoformat() if source.last_fetched_at else None,
        last_error=source.last_error,
    )


@router.delete("/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_source(
    source_id: int,
    source_service: SourceService = Depends(get_source_service),
    _: str = Depends(require_api_key),
):
    """Delete a source (soft delete)."""
    try:
        await source_service.delete_source(source_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{source_id}/refresh")
async def refresh_source(
    source_id: int,
    scheduler=Depends(get_scheduler),
    _: str = Depends(require_api_key),
):
    """Trigger refresh for a specific source."""
    if scheduler is None:
        raise HTTPException(status_code=503, detail="Scheduler not available")

    await scheduler.refresh_source(source_id)
    return {"message": "Refresh triggered"}


@router.post("/refresh")
async def refresh_all_sources(
    scheduler=Depends(get_scheduler),
    _: str = Depends(require_api_key),
):
    """Trigger refresh for all sources."""
    if scheduler is None:
        raise HTTPException(status_code=503, detail="Scheduler not available")

    await scheduler.refresh_all()
    return {"message": "All sources refresh triggered"}
```

**Step 2: Commit**

```bash
git add src/api/routes/sources.py
git commit -m "feat: add source management routes"
```

---

### Task 23: Create API Key Routes

**Files:**
- Create: `src/api/routes/keys.py`

**Step 1: Write the implementation**

```python
# src/api/routes/keys.py
"""API key management routes."""

import secrets
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_session, require_api_key
from src.models import APIKey

router = APIRouter(prefix="/keys", tags=["api-keys"])


class APIKeyCreate(BaseModel):
    """Schema for creating an API key."""

    name: str | None = None


class APIKeyResponse(BaseModel):
    """Schema for API key response."""

    id: int
    key: str
    name: str | None
    is_active: bool

    class Config:
        from_attributes = True


@router.get("", response_model=List[APIKeyResponse])
async def list_keys(
    session: AsyncSession = Depends(get_session),
    _: str = Depends(require_api_key),
):
    """List all API keys."""
    result = await session.execute(
        select(APIKey).where(APIKey.deleted_at.is_(None))
    )
    keys = list(result.scalars().all())
    return [APIKeyResponse(id=k.id, key=k.key, name=k.name, is_active=k.is_active) for k in keys]


@router.post("", response_model=APIKeyResponse, status_code=status.HTTP_201_CREATED)
async def create_key(
    data: APIKeyCreate,
    session: AsyncSession = Depends(get_session),
    _: str = Depends(require_api_key),
):
    """Create a new API key."""
    key = secrets.token_urlsafe(32)
    api_key = APIKey(key=key, name=data.name)
    session.add(api_key)
    await session.commit()
    await session.refresh(api_key)

    return APIKeyResponse(
        id=api_key.id,
        key=api_key.key,
        name=api_key.name,
        is_active=api_key.is_active,
    )


@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_key(
    key_id: int,
    session: AsyncSession = Depends(get_session),
    _: str = Depends(require_api_key),
):
    """Delete an API key."""
    result = await session.execute(
        select(APIKey).where(APIKey.id == key_id, APIKey.deleted_at.is_(None))
    )
    api_key = result.scalar_one_or_none()

    if not api_key:
        raise HTTPException(status_code=404, detail="API key not found")

    api_key.soft_delete()
    await session.commit()
```

**Step 2: Commit**

```bash
git add src/api/routes/keys.py
git commit -m "feat: add API key management routes"
```

---

### Task 24: Create Stats and Logs Routes

**Files:**
- Create: `src/api/routes/stats.py`
- Create: `src/api/routes/logs.py`

**Step 1: Write stats implementation**

```python
# src/api/routes/stats.py
"""Statistics API routes."""

from datetime import date, timedelta
from typing import List

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_session, require_api_key
from src.models import Stats

router = APIRouter(prefix="/stats", tags=["stats"])


class StatsResponse(BaseModel):
    """Schema for stats response."""

    date: str
    total_requests: int
    successful_fetches: int
    failed_fetches: int


@router.get("", response_model=List[StatsResponse])
async def get_stats(
    days: int = Query(7, ge=1, le=365),
    session: AsyncSession = Depends(get_session),
    _: str = Depends(require_api_key),
):
    """Get statistics for the last N days."""
    start_date = date.today() - timedelta(days=days)

    result = await session.execute(
        select(Stats)
        .where(Stats.date >= start_date, Stats.deleted_at.is_(None))
        .order_by(Stats.date.desc())
    )
    stats = list(result.scalars().all())

    return [
        StatsResponse(
            date=str(s.date),
            total_requests=s.total_requests,
            successful_fetches=s.successful_fetches,
            failed_fetches=s.failed_fetches,
        )
        for s in stats
    ]
```

**Step 2: Write logs implementation**

```python
# src/api/routes/logs.py
"""Error logs API routes."""

from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_session, require_api_key
from src.models import ErrorLog

router = APIRouter(prefix="/logs", tags=["logs"])


class LogResponse(BaseModel):
    """Schema for log response."""

    id: int
    source_id: int | None
    error_type: str
    error_message: str
    created_at: str


@router.get("", response_model=List[LogResponse])
async def get_logs(
    limit: int = Query(100, ge=1, le=1000),
    source_id: Optional[int] = Query(None),
    session: AsyncSession = Depends(get_session),
    _: str = Depends(require_api_key),
):
    """Get recent error logs."""
    query = select(ErrorLog).where(ErrorLog.deleted_at.is_(None))

    if source_id:
        query = query.where(ErrorLog.source_id == source_id)

    query = query.order_by(ErrorLog.created_at.desc()).limit(limit)

    result = await session.execute(query)
    logs = list(result.scalars().all())

    return [
        LogResponse(
            id=l.id,
            source_id=l.source_id,
            error_type=l.error_type,
            error_message=l.error_message,
            created_at=l.created_at.isoformat(),
        )
        for l in logs
    ]
```

**Step 3: Commit**

```bash
git add src/api/routes/stats.py src/api/routes/logs.py
git commit -m "feat: add stats and logs routes"
```

---

### Task 25: Create Main Application

**Files:**
- Create: `src/main.py`

**Step 1: Write the implementation**

```python
# src/main.py
"""Main FastAPI application."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import Response

from src.api.deps import get_fetch_service, get_rate_limiter, set_scheduler
from src.api.routes import feed, health, keys, logs, sources, stats
from src.config import settings
from src.scheduler.fetch_scheduler import FetchScheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    if settings.scheduler_enabled:
        from src.db.database import async_session_factory
        from src.services.fetch_service import FetchService

        async with async_session_factory() as session:
            fetch_service = FetchService(session)
            scheduler = FetchScheduler(
                fetch_service=fetch_service,
                check_interval=settings.scheduler_interval,
            )
            set_scheduler(scheduler)
            await scheduler.start()

    yield

    # Shutdown
    scheduler = get_scheduler()
    if scheduler:
        await scheduler.stop()


app = FastAPI(
    title="RSS Aggregator",
    description="Aggregate multiple RSS feeds into a single, filterable output",
    version="1.0.0",
    lifespan=lifespan,
)

# Include routers
app.include_router(health.router)
app.include_router(feed.router, prefix="/api/v1")
app.include_router(sources.router, prefix="/api/v1")
app.include_router(keys.router, prefix="/api/v1")
app.include_router(stats.router, prefix="/api/v1")
app.include_router(logs.router, prefix="/api/v1")


@app.exception_handler(404)
async def not_found_handler(request: Request, exc: Exception) -> Response:
    """Handle 404 errors with empty response."""
    return Response(status_code=404)
```

**Step 2: Update routes __init__.py**

```python
# src/api/routes/__init__.py
"""API routes package."""

from src.api.routes import feed, health, keys, logs, sources, stats

__all__ = ["feed", "health", "keys", "logs", "sources", "stats"]
```

**Step 3: Commit**

```bash
git add src/main.py src/api/routes/__init__.py
git commit -m "feat: create main FastAPI application"
```

---

### Task 26: Run Application and Verify

**Step 1: Run database migrations**

Run:
```bash
uv run alembic upgrade head
```

**Step 2: Start the application**

Run:
```bash
uv run uvicorn src.main:app --reload
```

**Step 3: Test health endpoint**

Run:
```bash
curl http://localhost:8000/health
```

Expected: `{"status": "ok"}`

**Step 4: Commit**

```bash
git add -A
git commit -m "feat: complete RSS aggregator implementation"
```

---

## Phase 7: Deployment

### Task 27: Create Dockerfile

**Files:**
- Create: `Dockerfile`

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files
COPY pyproject.toml uv.lock* ./

# Install dependencies
RUN uv sync --frozen --no-dev

# Copy application code
COPY src/ ./src/
COPY alembic.ini ./
COPY alembic/ ./alembic/

# Create data directory
RUN mkdir -p /app/data

# Expose port
EXPOSE 8000

# Run migrations and start server
CMD uv run alembic upgrade head && uv run uvicorn src.main:app --host 0.0.0.0 --port 8000
```

**Commit:**

```bash
git add Dockerfile
git commit -m "feat: add Dockerfile"
```

---

### Task 28: Create docker-compose.yml

**Files:**
- Create: `docker-compose.yml`

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

**Commit:**

```bash
git add docker-compose.yml
git commit -m "feat: add docker-compose.yml"
```

---

### Task 29: Create cloudbuild.yaml

**Files:**
- Create: `cloudbuild.yaml`

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

**Commit:**

```bash
git add cloudbuild.yaml
git commit -m "feat: add cloudbuild.yaml for Cloud Run deployment"
```

---

### Task 30: Create README.md

**Files:**
- Create: `README.md`

```markdown
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
```

**Commit:**

```bash
git add README.md
git commit -m "docs: add README.md"
```

---

### Task 31: Create .gitignore

**Files:**
- Create: `.gitignore`

```
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
.venv/

# uv
.uv/

# IDE
.idea/
.vscode/
*.swp
*.swo

# Environment
.env

# Database
data/
*.db

# Logs
*.log

# Testing
.coverage
htmlcov/
.pytest_cache/
.mypy_cache/

# Build
dist/
build/
*.egg-info/
```

**Commit:**

```bash
git add .gitignore
git commit -m "chore: add .gitignore"
```

---

## Execution Handoff

Plan complete and saved to `docs/plans/2026-03-18-rss-aggregator-implementation.md`.

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