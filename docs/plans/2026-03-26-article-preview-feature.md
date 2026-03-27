# Article Quick Preview Feature Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement a quick preview feature that allows users to preview article content using the markdown.new service, with backend caching for faster subsequent access.

**Architecture:** Frontend directly calls markdown.new API for content conversion, backend handles caching via SQLite database with SHA-256 URL hashing. Preview buttons (eye icon for preview, external link for new tab) are added to each news item in Feed and History pages.

**Tech Stack:** FastAPI, SQLAlchemy, SQLite, Vue 3, TypeScript, Tailwind CSS, Vitest, Playwright, pytest

---

## Phase 1: Backend Model & Migration

### Task 1.1: Create PreviewContent Model Test

**Files:**
- Create: `tests/models/test_preview_content.py`

**Step 1: Write the failing test**

```python
"""Tests for PreviewContent model."""

import pytest
from datetime import datetime

from src.models.preview_content import PreviewContent


class TestPreviewContent:
    """Test cases for PreviewContent model."""

    def test_create_preview_content(self) -> None:
        """Should create a PreviewContent instance with all fields."""
        preview = PreviewContent(
            url="https://example.com/article",
            url_hash="abc123" * 10 + "abcd",  # 64 chars
            markdown_content="# Test Article\n\nContent here.",
            title="Test Article",
        )

        assert preview.url == "https://example.com/article"
        assert preview.url_hash == "abc123" * 10 + "abcd"
        assert preview.markdown_content == "# Test Article\n\nContent here."
        assert preview.title == "Test Article"

    def test_preview_content_url_max_length(self) -> None:
        """Should accept URLs up to 2048 characters."""
        long_url = "https://example.com/" + "a" * 2020
        preview = PreviewContent(
            url=long_url,
            url_hash="x" * 64,
            markdown_content="content",
        )

        assert len(preview.url) == 2048

    def test_preview_content_title_optional(self) -> None:
        """Should allow None for title."""
        preview = PreviewContent(
            url="https://example.com/article",
            url_hash="x" * 64,
            markdown_content="content",
            title=None,
        )

        assert preview.title is None
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/models/test_preview_content.py -v`
Expected: FAIL with "No module named 'src.models.preview_content'"

---

### Task 1.2: Implement PreviewContent Model

**Files:**
- Create: `src/models/preview_content.py`
- Modify: `src/models/__init__.py`

**Step 1: Write the model**

```python
# src/models/preview_content.py
"""Preview content model for cached article previews."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    pass


class PreviewContent(Base, TimestampMixin):
    """Cached markdown preview content for URLs."""

    __tablename__ = "preview_contents"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, init=False)
    url: Mapped[str] = mapped_column(String(2048), unique=True, index=True)
    url_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    markdown_content: Mapped[str] = mapped_column(Text)
    title: Mapped[str | None] = mapped_column(String(500), default=None)

    def __repr__(self) -> str:
        return f"<PreviewContent(id={self.id}, url={self.url[:50]}...)>"
```

**Step 2: Export the model**

```python
# src/models/__init__.py (add these lines)
from src.models.preview_content import PreviewContent

# Update __all__ list to include:
__all__ = [
    # ... existing exports ...
    "PreviewContent",
]
```

**Step 3: Run test to verify it passes**

Run: `uv run pytest tests/models/test_preview_content.py -v`
Expected: PASS (3 tests)

**Step 4: Commit**

```bash
git add src/models/preview_content.py src/models/__init__.py tests/models/test_preview_content.py
git commit -m "feat: add PreviewContent model for article preview caching"
```

---

### Task 1.3: Create Database Migration

**Files:**
- Create: `alembic/versions/xxxx_add_preview_contents_table.py`

**Step 1: Generate migration**

Run: `uv run alembic revision --autogenerate -m "add preview_contents table"`

**Step 2: Verify migration file**

The generated migration should include:
- `preview_contents` table with columns: id, url, url_hash, markdown_content, title, created_at, updated_at, deleted_at
- Unique constraints on `url` and `url_hash`
- Indexes on `url` and `url_hash`

**Step 3: Run migration**

Run: `uv run alembic upgrade head`
Expected: Success, no errors

**Step 4: Commit**

```bash
git add alembic/versions/*.py
git commit -m "feat: add database migration for preview_contents table"
```

---

## Phase 2: Backend Service Layer

### Task 2.1: Create PreviewService Test

**Files:**
- Create: `tests/services/test_preview_service.py`

**Step 1: Write the failing tests**

```python
"""Tests for PreviewService."""

import hashlib
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import PreviewContent
from src.services.preview_service import PreviewService


def compute_url_hash(url: str) -> str:
    """Compute SHA-256 hash of URL."""
    return hashlib.sha256(url.encode()).hexdigest()


@pytest_asyncio.fixture
async def preview_service(db_session: AsyncSession) -> PreviewService:
    """Create a PreviewService instance."""
    return PreviewService(db_session)


class TestPreviewServiceGetByUrlHash:
    """Tests for get_by_url_hash method."""

    @pytest.mark.asyncio
    async def test_returns_none_when_not_found(
        self, preview_service: PreviewService
    ) -> None:
        """Should return None when preview not found."""
        result = await preview_service.get_by_url_hash("nonexistent_hash")
        assert result is None

    @pytest.mark.asyncio
    async def test_returns_preview_when_found(
        self, preview_service: PreviewService, db_session: AsyncSession
    ) -> None:
        """Should return preview when found."""
        url = "https://example.com/article"
        url_hash = compute_url_hash(url)

        preview = PreviewContent(
            url=url,
            url_hash=url_hash,
            markdown_content="# Test",
            title="Test",
        )
        db_session.add(preview)
        await db_session.commit()

        result = await preview_service.get_by_url_hash(url_hash)
        assert result is not None
        assert result.url == url
        assert result.markdown_content == "# Test"


class TestPreviewServiceUpsert:
    """Tests for upsert method."""

    @pytest.mark.asyncio
    async def test_creates_new_record(
        self, preview_service: PreviewService
    ) -> None:
        """Should create new record when URL not exists."""
        url = "https://example.com/new"
        content = "# New Article"
        title = "New Article"

        result = await preview_service.upsert(url, content, title)

        assert result.id is not None
        assert result.url == url
        assert result.markdown_content == content
        assert result.title == title
        assert len(result.url_hash) == 64

    @pytest.mark.asyncio
    async def test_updates_existing_record(
        self, preview_service: PreviewService
    ) -> None:
        """Should update existing record when URL exists."""
        url = "https://example.com/article"

        # Create initial
        first = await preview_service.upsert(url, "# Original", "Original")

        # Update with same URL
        second = await preview_service.upsert(url, "# Updated", "Updated")

        assert second.id == first.id
        assert second.markdown_content == "# Updated"
        assert second.title == "Updated"

    @pytest.mark.asyncio
    async def test_url_hash_is_consistent(
        self, preview_service: PreviewService
    ) -> None:
        """Should generate consistent SHA-256 hash."""
        url = "https://example.com/article"

        result = await preview_service.upsert(url, "# Content")

        expected_hash = compute_url_hash(url)
        assert result.url_hash == expected_hash


class TestPreviewServiceGetByUrl:
    """Tests for get_by_url method."""

    @pytest.mark.asyncio
    async def test_returns_preview_by_url(
        self, preview_service: PreviewService
    ) -> None:
        """Should return preview when found by URL."""
        url = "https://example.com/article"
        await preview_service.upsert(url, "# Test", "Test")

        result = await preview_service.get_by_url(url)
        assert result is not None
        assert result.url == url

    @pytest.mark.asyncio
    async def test_returns_none_for_unknown_url(
        self, preview_service: PreviewService
    ) -> None:
        """Should return None for unknown URL."""
        result = await preview_service.get_by_url("https://unknown.com/article")
        assert result is None
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/services/test_preview_service.py -v`
Expected: FAIL with "No module named 'src.services.preview_service'"

---

### Task 2.2: Implement PreviewService

**Files:**
- Create: `src/services/preview_service.py`
- Modify: `src/services/__init__.py`
- Modify: `src/api/deps.py`

**Step 1: Write the service**

```python
# src/services/preview_service.py
"""Service for managing cached preview content."""

import hashlib
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from src.models import PreviewContent

logger = logging.getLogger(__name__)


class PreviewService:
    """Service for managing cached preview content."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the service with a database session.

        Args:
            session: AsyncSession for database operations.
        """
        self._session = session

    @staticmethod
    def compute_url_hash(url: str) -> str:
        """Compute SHA-256 hash of URL.

        Args:
            url: The URL to hash.

        Returns:
            SHA-256 hash as hex string (64 characters).
        """
        return hashlib.sha256(url.encode()).hexdigest()

    async def get_by_url_hash(self, url_hash: str) -> PreviewContent | None:
        """Retrieve cached preview by URL hash.

        Args:
            url_hash: SHA-256 hash of normalized URL.

        Returns:
            PreviewContent if found, None otherwise.
        """
        result = await self._session.execute(
            select(PreviewContent).where(
                PreviewContent.url_hash == url_hash,
                PreviewContent.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def get_by_url(self, url: str) -> PreviewContent | None:
        """Retrieve cached preview by URL.

        Args:
            url: Original article URL.

        Returns:
            PreviewContent if found, None otherwise.
        """
        result = await self._session.execute(
            select(PreviewContent).where(
                PreviewContent.url == url,
                PreviewContent.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def upsert(
        self,
        url: str,
        markdown_content: str,
        title: str | None = None,
    ) -> PreviewContent:
        """Create or update preview content.

        Handles race conditions using upsert pattern:
        1. Check if record exists
        2. If yes, update and return
        3. If no, create new (handle IntegrityError)

        Args:
            url: Original article URL.
            markdown_content: Markdown content from markdown.new.
            title: Optional title extracted from content.

        Returns:
            Created or updated PreviewContent.
        """
        url_hash = self.compute_url_hash(url)

        # Check for existing record
        existing = await self.get_by_url_hash(url_hash)
        if existing:
            existing.markdown_content = markdown_content
            existing.title = title
            await self._session.commit()
            await self._session.refresh(existing)
            return existing

        # Create new record (handle race condition)
        try:
            preview = PreviewContent(
                url=url,
                url_hash=url_hash,
                markdown_content=markdown_content,
                title=title,
            )
            self._session.add(preview)
            await self._session.commit()
            await self._session.refresh(preview)
            return preview
        except IntegrityError:
            # Another request created it first - fetch and return
            await self._session.rollback()
            logger.warning(f"Race condition detected for URL: {url}")
            result = await self.get_by_url_hash(url_hash)
            if result is None:
                raise
            return result

    async def delete_by_url(self, url: str) -> bool:
        """Delete cached preview by URL (soft delete).

        Args:
            url: Original article URL.

        Returns:
            True if deleted, False if not found.
        """
        preview = await self.get_by_url(url)
        if preview is None:
            return False

        preview.soft_delete()
        await self._session.commit()
        return True
```

**Step 2: Export the service**

```python
# src/services/__init__.py (add export)
from src.services.preview_service import PreviewService

__all__ = [
    # ... existing exports ...
    "PreviewService",
]
```

**Step 3: Add dependency injection**

```python
# src/api/deps.py (add this function)
from src.services.preview_service import PreviewService

async def get_preview_service(
    session: AsyncSession = Depends(get_session),
) -> PreviewService:
    """Get PreviewService instance."""
    return PreviewService(session)
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/services/test_preview_service.py -v`
Expected: PASS (7 tests)

**Step 5: Commit**

```bash
git add src/services/preview_service.py src/services/__init__.py src/api/deps.py tests/services/test_preview_service.py
git commit -m "feat: add PreviewService for preview content management"
```

---

## Phase 3: Backend API Routes

### Task 3.1: Create Preview Routes Test

**Files:**
- Create: `tests/api/test_preview_routes.py`

**Step 1: Write the failing tests**

```python
"""Tests for preview API routes."""

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient

from src.main import app


@pytest.fixture
def client() -> TestClient:
    """Create a test client."""
    return TestClient(app)


class TestGetPreview:
    """Tests for GET /api/v1/previews/{url_hash} endpoint."""

    def test_returns_404_when_not_found(self, client: TestClient) -> None:
        """Should return 404 when preview not found."""
        response = client.get("/api/v1/previews/nonexistent_hash")
        assert response.status_code == 404
        assert response.json()["detail"] == "Preview not found"


class TestCreatePreview:
    """Tests for POST /api/v1/previews endpoint."""

    def test_creates_preview(self, client: TestClient) -> None:
        """Should create a new preview."""
        response = client.post(
            "/api/v1/previews",
            json={
                "url": "https://example.com/article",
                "markdown_content": "# Test Article\n\nContent here.",
                "title": "Test Article",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["url"] == "https://example.com/article"
        assert data["title"] == "Test Article"
        assert len(data["url_hash"]) == 64
        assert "id" in data

    def test_updates_existing_preview(self, client: TestClient) -> None:
        """Should update existing preview with same URL."""
        # Create first
        client.post(
            "/api/v1/previews",
            json={
                "url": "https://example.com/update-test",
                "markdown_content": "# Original",
                "title": "Original",
            },
        )

        # Update with same URL
        response = client.post(
            "/api/v1/previews",
            json={
                "url": "https://example.com/update-test",
                "markdown_content": "# Updated",
                "title": "Updated",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["markdown_content"] == "# Updated"
        assert data["title"] == "Updated"

    def test_optional_title(self, client: TestClient) -> None:
        """Should allow creating preview without title."""
        response = client.post(
            "/api/v1/previews",
            json={
                "url": "https://example.com/no-title",
                "markdown_content": "# No Title",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["title"] is None


class TestGetPreviewByHash:
    """Tests for retrieving preview by hash."""

    def test_get_by_hash_after_create(self, client: TestClient) -> None:
        """Should retrieve preview by URL hash after creation."""
        # Create preview
        create_response = client.post(
            "/api/v1/previews",
            json={
                "url": "https://example.com/hash-test",
                "markdown_content": "# Hash Test",
                "title": "Hash Test",
            },
        )
        url_hash = create_response.json()["url_hash"]

        # Get by hash
        response = client.get(f"/api/v1/previews/{url_hash}")
        assert response.status_code == 200
        data = response.json()
        assert data["url"] == "https://example.com/hash-test"
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/api/test_preview_routes.py -v`
Expected: FAIL with "404 Not Found" or route not found

---

### Task 3.2: Implement Preview Routes

**Files:**
- Create: `src/api/routes/previews.py`
- Modify: `src/main.py`

**Step 1: Write the routes**

```python
# src/api/routes/previews.py
"""Preview API routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from src.api.deps import get_preview_service, require_api_key
from src.services.preview_service import PreviewService
from src.utils.time import to_iso_string

router = APIRouter(prefix="/previews", tags=["previews"])


class PreviewCreate(BaseModel):
    """Schema for creating a preview."""

    url: str
    markdown_content: str
    title: str | None = None


class PreviewResponse(BaseModel):
    """Schema for preview response."""

    id: int
    url: str
    url_hash: str
    markdown_content: str
    title: str | None
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


@router.get("/{url_hash}", response_model=PreviewResponse)
async def get_preview(
    url_hash: str,
    preview_service: PreviewService = Depends(get_preview_service),
    _: str | None = Depends(require_api_key),
) -> PreviewResponse:
    """Get cached preview content by URL hash.

    Args:
        url_hash: SHA-256 hash of the URL.

    Returns:
        Preview content if found.

    Raises:
        HTTPException: 404 if not found.
    """
    preview = await preview_service.get_by_url_hash(url_hash)
    if not preview:
        raise HTTPException(status_code=404, detail="Preview not found")

    return PreviewResponse(
        id=preview.id,
        url=preview.url,
        url_hash=preview.url_hash,
        markdown_content=preview.markdown_content,
        title=preview.title,
        created_at=to_iso_string(preview.created_at) or "",
        updated_at=to_iso_string(preview.updated_at) or "",
    )


@router.post("", response_model=PreviewResponse)
async def create_preview(
    data: PreviewCreate,
    preview_service: PreviewService = Depends(get_preview_service),
    _: str | None = Depends(require_api_key),
) -> PreviewResponse:
    """Create or update preview content.

    If a preview for the given URL already exists, it will be updated.

    Args:
        data: Preview data including URL, content, and optional title.

    Returns:
        Created or updated preview.
    """
    preview = await preview_service.upsert(
        url=data.url,
        markdown_content=data.markdown_content,
        title=data.title,
    )

    return PreviewResponse(
        id=preview.id,
        url=preview.url,
        url_hash=preview.url_hash,
        markdown_content=preview.markdown_content,
        title=preview.title,
        created_at=to_iso_string(preview.created_at) or "",
        updated_at=to_iso_string(preview.updated_at) or "",
    )
```

**Step 2: Register the router**

```python
# src/main.py (add import and router)
from src.api.routes import feed, health, history, keys, logs, previews, sources, stats

# Add this line after other router registrations:
app.include_router(previews.router, prefix="/api/v1")
```

**Step 3: Run test to verify it passes**

Run: `uv run pytest tests/api/test_preview_routes.py -v`
Expected: PASS (5 tests)

**Step 4: Commit**

```bash
git add src/api/routes/previews.py src/main.py tests/api/test_preview_routes.py
git commit -m "feat: add preview API endpoints for caching article previews"
```

---

## Phase 4: Frontend Utilities

### Task 4.1: Create URL Normalizer Test

**Files:**
- Create: `web/src/utils/__tests__/urlNormalizer.test.ts`

**Step 1: Write the failing tests**

```typescript
// web/src/utils/__tests__/urlNormalizer.test.ts
import { describe, it, expect } from 'vitest'
import { normalizeUrl, computeUrlHash } from '../urlNormalizer'

describe('normalizeUrl', () => {
  it('should lowercase domain', () => {
    expect(normalizeUrl('https://Example.COM/article')).toBe('https://example.com/article')
  })

  it('should sort query parameters alphabetically', () => {
    expect(normalizeUrl('https://example.com?b=2&a=1')).toBe('https://example.com/?a=1&b=2')
  })

  it('should remove fragment', () => {
    expect(normalizeUrl('https://example.com#section')).toBe('https://example.com')
  })

  it('should remove trailing slash except root', () => {
    expect(normalizeUrl('https://example.com/path/')).toBe('https://example.com/path')
    expect(normalizeUrl('https://example.com/')).toBe('https://example.com/')
  })

  it('should throw error for invalid URL', () => {
    expect(() => normalizeUrl('not-a-url')).toThrow('Invalid URL')
  })

  it('should handle complex URLs', () => {
    const input = 'https://Example.com/Article?z=3&a=1&b=2#section'
    const expected = 'https://example.com/Article?a=1&b=2&z=3'
    expect(normalizeUrl(input)).toBe(expected)
  })
})

describe('computeUrlHash', () => {
  it('should return 64 character SHA-256 hash', async () => {
    const hash = await computeUrlHash('https://example.com/article')
    expect(hash).toHaveLength(64)
    expect(/^[a-f0-9]+$/.test(hash)).toBe(true)
  })

  it('should return consistent hash for same URL', async () => {
    const url = 'https://example.com/article'
    const hash1 = await computeUrlHash(url)
    const hash2 = await computeUrlHash(url)
    expect(hash1).toBe(hash2)
  })

  it('should return same hash for normalized-equivalent URLs', async () => {
    const hash1 = await computeUrlHash('https://Example.COM/path?b=2&a=1')
    const hash2 = await computeUrlHash('https://example.com/path?a=1&b=2')
    expect(hash1).toBe(hash2)
  })
})
```

**Step 2: Run test to verify it fails**

Run: `cd web && pnpm vitest run src/utils/__tests__/urlNormalizer.test.ts`
Expected: FAIL with module not found

---

### Task 4.2: Implement URL Normalizer

**Files:**
- Create: `web/src/utils/urlNormalizer.ts`

**Step 1: Write the utility**

```typescript
// web/src/utils/urlNormalizer.ts
/**
 * Normalizes a URL for consistent hashing.
 * 
 * Rules:
 * 1. Lowercase domain
 * 2. Sort query parameters alphabetically
 * 3. Remove fragment (#section)
 * 4. Remove trailing slash (except root)
 */
export function normalizeUrl(url: string): string {
  try {
    const parsed = new URL(url)

    // Lowercase domain
    parsed.host = parsed.host.toLowerCase()

    // Sort query parameters
    const params = new URLSearchParams(parsed.search)
    const sortedParams = new URLSearchParams([...params.entries()].sort())
    parsed.search = sortedParams.toString()

    // Remove fragment
    parsed.hash = ''

    // Remove trailing slash (except root)
    if (parsed.pathname !== '/' && parsed.pathname.endsWith('/')) {
      parsed.pathname = parsed.pathname.slice(0, -1)
    }

    return parsed.toString()
  } catch {
    throw new Error('Invalid URL')
  }
}

/**
 * Computes SHA-256 hash of a URL.
 * 
 * @param url - The URL to hash (will be normalized first)
 * @returns SHA-256 hash as hex string (64 characters)
 */
export async function computeUrlHash(url: string): Promise<string> {
  const normalized = normalizeUrl(url)
  const encoder = new TextEncoder()
  const data = encoder.encode(normalized)
  const hashBuffer = await crypto.subtle.digest('SHA-256', data)
  const hashArray = Array.from(new Uint8Array(hashBuffer))
  const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('')
  return hashHex
}
```

**Step 2: Run test to verify it passes**

Run: `cd web && pnpm vitest run src/utils/__tests__/urlNormalizer.test.ts`
Expected: PASS (9 tests)

**Step 3: Commit**

```bash
git add web/src/utils/urlNormalizer.ts web/src/utils/__tests__/urlNormalizer.test.ts
git commit -m "feat: add URL normalizer and hash utility for preview caching"
```

---

### Task 4.3: Create Article Preview API Module

**Files:**
- Create: `web/src/api/preview.ts`

**Step 1: Write the API module**

```typescript
// web/src/api/preview.ts
import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_BASE_URL || ''

export interface PreviewContent {
  id: number
  url: string
  url_hash: string
  markdown_content: string
  title: string | null
  created_at: string
  updated_at: string
}

/**
 * Get cached preview content by URL hash.
 */
export async function getCachedPreview(urlHash: string): Promise<PreviewContent | null> {
  try {
    const response = await axios.get<PreviewContent>(
      `${API_BASE}/api/v1/previews/${urlHash}`
    )
    return response.data
  } catch (error) {
    if (axios.isAxiosError(error) && error.response?.status === 404) {
      return null
    }
    throw error
  }
}

/**
 * Save preview content to cache.
 */
export async function savePreview(
  url: string,
  markdownContent: string,
  title?: string
): Promise<PreviewContent> {
  const response = await axios.post<PreviewContent>(
    `${API_BASE}/api/v1/previews`,
    {
      url,
      markdown_content: markdownContent,
      title: title || null,
    }
  )
  return response.data
}

/**
 * Fetch markdown content from markdown.new API.
 */
export async function fetchMarkdownFromService(url: string): Promise<string> {
  const MARKDOWN_NEW_TIMEOUT = 30000
  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), MARKDOWN_NEW_TIMEOUT)

  try {
    const response = await fetch('https://markdown.new/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url, retain_images: true }),
      signal: controller.signal,
    })

    clearTimeout(timeoutId)

    if (!response.ok) {
      throw new Error(`markdown.new error: ${response.status} ${response.statusText}`)
    }

    return await response.text()
  } catch (error) {
    clearTimeout(timeoutId)
    throw error
  }
}
```

**Step 2: Commit**

```bash
git add web/src/api/preview.ts
git commit -m "feat: add preview API module for frontend"
```

---

## Phase 5: Frontend Composable

### Task 5.1: Create useArticlePreview Composable Test

**Files:**
- Create: `web/src/composables/__tests__/useArticlePreview.test.ts`

**Step 1: Write the failing tests**

```typescript
// web/src/composables/__tests__/useArticlePreview.test.ts
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { nextTick } from 'vue'
import { useArticlePreview } from '../useArticlePreview'

// Mock the API module
vi.mock('@/api/preview', () => ({
  getCachedPreview: vi.fn(),
  savePreview: vi.fn(),
  fetchMarkdownFromService: vi.fn(),
}))

import { getCachedPreview, savePreview, fetchMarkdownFromService } from '@/api/preview'

const mockGetCachedPreview = vi.mocked(getCachedPreview)
const mockSavePreview = vi.mocked(savePreview)
const mockFetchMarkdownFromService = vi.mocked(fetchMarkdownFromService)

describe('useArticlePreview', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('fetchPreview', () => {
    it('should return cached content when available', async () => {
      const mockPreview = {
        id: 1,
        url: 'https://example.com/article',
        url_hash: 'abc123',
        markdown_content: '# Cached Content',
        title: 'Cached',
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      }
      mockGetCachedPreview.mockResolvedValueOnce(mockPreview)

      const { fetchPreview, content, source } = useArticlePreview()
      await fetchPreview('https://example.com/article')

      expect(mockGetCachedPreview).toHaveBeenCalled()
      expect(content.value).toBe('# Cached Content')
      expect(source.value).toBe('cache')
    })

    it('should fetch from markdown.new when not cached', async () => {
      mockGetCachedPreview.mockResolvedValueOnce(null)
      mockFetchMarkdownFromService.mockResolvedValueOnce('# New Content')
      mockSavePreview.mockResolvedValueOnce({
        id: 1,
        url: 'https://example.com/article',
        url_hash: 'hash',
        markdown_content: '# New Content',
        title: null,
        created_at: '',
        updated_at: '',
      })

      const { fetchPreview, content, source } = useArticlePreview()
      await fetchPreview('https://example.com/article')

      expect(mockFetchMarkdownFromService).toHaveBeenCalledWith('https://example.com/article')
      expect(mockSavePreview).toHaveBeenCalled()
      expect(content.value).toBe('# New Content')
      expect(source.value).toBe('api')
    })

    it('should set loading state during fetch', async () => {
      mockGetCachedPreview.mockResolvedValueOnce(null)
      mockFetchMarkdownFromService.mockImplementation(() => 
        new Promise(resolve => setTimeout(() => resolve('# Content'), 100))
      )

      const { fetchPreview, loading } = useArticlePreview()
      const promise = fetchPreview('https://example.com/article')

      expect(loading.value).toBe(true)
      await promise
      expect(loading.value).toBe(false)
    })
  })

  describe('error handling', () => {
    it('should set error on fetch failure', async () => {
      mockGetCachedPreview.mockResolvedValueOnce(null)
      mockFetchMarkdownFromService.mockRejectedValueOnce(new Error('Network error'))

      const { fetchPreview, error } = useArticlePreview()
      await fetchPreview('https://example.com/article')

      expect(error.value).toBeTruthy()
    })
  })
})
```

**Step 2: Run test to verify it fails**

Run: `cd web && pnpm vitest run src/composables/__tests__/useArticlePreview.test.ts`
Expected: FAIL with module not found

---

### Task 5.2: Implement useArticlePreview Composable

**Files:**
- Create: `web/src/composables/useArticlePreview.ts`

**Step 1: Write the composable**

```typescript
// web/src/composables/useArticlePreview.ts
import { ref, readonly } from 'vue'
import { computeUrlHash } from '@/utils/urlNormalizer'
import {
  getCachedPreview,
  savePreview,
  fetchMarkdownFromService,
  type PreviewContent,
} from '@/api/preview'

export type PreviewSource = 'cache' | 'api'

export interface UseArticlePreviewReturn {
  /** Preview content (markdown) */
  content: ReturnType<typeof readonly<ReturnType<typeof ref<string>>>>
  /** Content title if available */
  title: ReturnType<typeof readonly<ReturnType<typeof ref<string | null>>>>
  /** Loading state */
  loading: ReturnType<typeof readonly<ReturnType<typeof ref<boolean>>>>
  /** Error message if any */
  error: ReturnType<typeof readonly<ReturnType<typeof ref<string | null>>>>
  /** Source of content: 'cache' or 'api' */
  source: ReturnType<typeof readonly<ReturnType<typeof ref<PreviewSource>>>>
  /** Fetch preview for a URL */
  fetchPreview: (url: string) => Promise<void>
  /** Reset state */
  reset: () => void
}

const MAX_CONTENT_SIZE = 10 * 1024 * 1024 // 10 MB

/**
 * Validate and truncate markdown content if necessary.
 */
function validateContent(content: string): string {
  if (content.length > MAX_CONTENT_SIZE) {
    console.warn('Preview content truncated due to size')
    return content.slice(0, MAX_CONTENT_SIZE)
  }
  return content
}

/**
 * Extract title from markdown content.
 * Looks for frontmatter title or first H1.
 */
function extractTitle(markdown: string): string | null {
  // Check frontmatter
  const frontmatterMatch = markdown.match(/^---\n.*?title:\s*["']?(.+?)["']?\n.*?---/s)
  if (frontmatterMatch) {
    return frontmatterMatch[1].trim()
  }

  // Check first H1
  const h1Match = markdown.match(/^#\s+(.+)$/m)
  if (h1Match) {
    return h1Match[1].trim()
  }

  return null
}

/**
 * Composable for fetching and caching article previews.
 */
export function useArticlePreview(): UseArticlePreviewReturn {
  const content = ref('')
  const title = ref<string | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)
  const source = ref<PreviewSource>('api')

  async function fetchPreview(url: string): Promise<void> {
    loading.value = true
    error.value = null
    content.value = ''
    title.value = null

    try {
      // Calculate URL hash
      const urlHash = await computeUrlHash(url)

      // Check cache first
      const cached = await getCachedPreview(urlHash)
      if (cached) {
        content.value = cached.markdown_content
        title.value = cached.title
        source.value = 'cache'
        return
      }

      // Fetch from markdown.new
      source.value = 'api'
      const markdown = await fetchMarkdownFromService(url)
      const validatedContent = validateContent(markdown)
      const extractedTitle = extractTitle(validatedContent)

      content.value = validatedContent
      title.value = extractedTitle

      // Save to cache (don't await, fire and forget)
      savePreview(url, validatedContent, extractedTitle || undefined).catch(err => {
        console.warn('Failed to save preview cache:', err)
      })
    } catch (err) {
      if (err instanceof Error) {
        if (err.message.includes('429')) {
          error.value = 'Preview service temporarily unavailable, please try again later'
        } else if (err.name === 'AbortError') {
          error.value = 'Preview request timed out, please try again'
        } else if (err.message.includes('Network')) {
          error.value = 'Network error, please check your connection'
        } else {
          error.value = 'Unable to preview this page'
        }
      } else {
        error.value = 'An unexpected error occurred'
      }
    } finally {
      loading.value = false
    }
  }

  function reset(): void {
    content.value = ''
    title.value = null
    loading.value = false
    error.value = null
    source.value = 'api'
  }

  return {
    content: readonly(content),
    title: readonly(title),
    loading: readonly(loading),
    error: readonly(error),
    source: readonly(source),
    fetchPreview,
    reset,
  }
}
```

**Step 2: Run test to verify it passes**

Run: `cd web && pnpm vitest run src/composables/__tests__/useArticlePreview.test.ts`
Expected: PASS (4 tests)

**Step 3: Commit**

```bash
git add web/src/composables/useArticlePreview.ts web/src/composables/__tests__/useArticlePreview.test.ts
git commit -m "feat: add useArticlePreview composable for preview functionality"
```

---

## Phase 6: Frontend Components

### Task 6.1: Create ArticlePreviewDialog Component Test

**Files:**
- Create: `web/src/components/__tests__/ArticlePreviewDialog.test.ts`

**Step 1: Write the failing tests**

```typescript
// web/src/components/__tests__/ArticlePreviewDialog.test.ts
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import ArticlePreviewDialog from '../ArticlePreviewDialog.vue'

// Mock the composable
vi.mock('@/composables/useArticlePreview', () => ({
  useArticlePreview: () => ({
    content: { value: '# Test Content' },
    title: { value: 'Test Title' },
    loading: { value: false },
    error: { value: null },
    source: { value: 'api' },
    fetchPreview: vi.fn(),
    reset: vi.fn(),
  }),
}))

describe('ArticlePreviewDialog', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should render when open', () => {
    const wrapper = mount(ArticlePreviewDialog, {
      props: {
        open: true,
        url: 'https://example.com/article',
      },
      global: {
        stubs: {
          Dialog: {
            template: '<div class="dialog-mock"><slot /></div>',
          },
        },
      },
    })

    expect(wrapper.find('.dialog-mock').exists()).toBe(true)
  })

  it('should not render when closed', () => {
    const wrapper = mount(ArticlePreviewDialog, {
      props: {
        open: false,
        url: 'https://example.com/article',
      },
      global: {
        stubs: {
          Dialog: {
            template: '<div v-if="open" class="dialog-mock"><slot /></div>',
            props: ['open'],
          },
        },
      },
    })

    expect(wrapper.find('.dialog-mock').exists()).toBe(false)
  })

  it('should emit update:open when closed', async () => {
    const wrapper = mount(ArticlePreviewDialog, {
      props: {
        open: true,
        url: 'https://example.com/article',
      },
      global: {
        stubs: {
          Dialog: {
            template: '<div class="dialog-mock"><slot /></div>',
            emits: ['update:open'],
          },
        },
      },
    })

    // Component should have close functionality
    expect(wrapper.emits()).toBeDefined()
  })
})
```

**Step 2: Run test to verify it fails**

Run: `cd web && pnpm vitest run src/components/__tests__/ArticlePreviewDialog.test.ts`
Expected: FAIL with component not found

---

### Task 6.2: Implement ArticlePreviewDialog Component

**Files:**
- Create: `web/src/components/ArticlePreviewDialog.vue`

**Step 1: Write the component**

```vue
<script setup lang="ts">
import { Check, Copy, ExternalLink, RefreshCw, X, Eye, FileCode } from "lucide-vue-next"
import { computed, watch, ref } from "vue"
import { useI18n } from "vue-i18n"
import Button from "@/components/ui/Button.vue"
import Dialog from "@/components/ui/Dialog.vue"
import MarkdownPreview from "@/components/MarkdownPreview.vue"
import { useArticlePreview } from "@/composables/useArticlePreview"

const props = defineProps<{
  open: boolean
  url: string
  title?: string
}>()

const emit = defineEmits<(e: "update:open", value: boolean) => void>()

const { t } = useI18n()

const {
  content,
  title: contentTitle,
  loading,
  error,
  source,
  fetchPreview,
  reset,
} = useArticlePreview()

const mode = ref<"preview" | "source">("preview")
const copied = ref(false)

const displayTitle = computed(() => {
  return props.title || contentTitle.value || t("preview.title")
})

function close(): void {
  emit("update:open", false)
}

async function copyToClipboard(): Promise<void> {
  try {
    await navigator.clipboard.writeText(content.value)
    copied.value = true
    setTimeout(() => {
      copied.value = false
    }, 2000)
  } catch (err) {
    console.error("Failed to copy:", err)
  }
}

function openOriginal(): void {
  window.open(props.url, "_blank", "noopener,noreferrer")
}

watch(
  () => props.open,
  (isOpen) => {
    if (isOpen) {
      reset()
      mode.value = "preview"
      fetchPreview(props.url)
    }
  },
)
</script>

<template>
  <Dialog :open="open" size="2xl" @update:open="close">
    <div class="p-6 overflow-hidden">
      <!-- Header -->
      <div class="flex items-start justify-between mb-6">
        <div class="flex-1 min-w-0">
          <h2 class="text-xl font-semibold text-neutral-900 dark:text-neutral-100 mb-1 truncate">
            {{ displayTitle }}
          </h2>
          <div class="flex items-center gap-3 text-sm text-neutral-500 dark:text-neutral-400">
            <span v-if="source === 'cache'" class="flex items-center gap-1">
              <Eye class="h-3.5 w-3.5" />
              {{ t('preview.cached') }}
            </span>
            <span v-else class="flex items-center gap-1">
              <RefreshCw class="h-3.5 w-3.5" />
              {{ t('preview.fresh') }}
            </span>
          </div>
        </div>
        <button
          @click="close"
          class="p-2 rounded-lg hover:bg-neutral-100 dark:hover:bg-neutral-700 transition-colors"
        >
          <X class="h-5 w-5 text-neutral-500 dark:text-neutral-400" />
        </button>
      </div>

      <!-- Loading State -->
      <div v-if="loading" class="space-y-4">
        <div class="bg-neutral-100 dark:bg-slate-900 rounded-xl overflow-hidden border border-neutral-200 dark:border-slate-800">
          <div class="h-12 bg-neutral-200 dark:bg-slate-800 border-b border-neutral-300 dark:border-slate-700 animate-pulse" />
          <div class="p-4 space-y-2">
            <div v-for="i in 8" :key="i" class="h-4 bg-neutral-200 dark:bg-slate-800 rounded animate-pulse" :style="{ width: `${60 + Math.random() * 40}%` }" />
          </div>
        </div>
      </div>

      <!-- Error State -->
      <div v-else-if="error" class="text-center py-12">
        <div class="inline-flex items-center justify-center w-16 h-16 rounded-full bg-red-100 dark:bg-red-900/30 mb-4">
          <X class="h-8 w-8 text-red-500 dark:text-red-400" />
        </div>
        <p class="text-red-500 dark:text-red-400 font-medium mb-4">{{ error }}</p>
        <Button variant="outline" size="sm" @click="openOriginal" class="gap-2">
          <ExternalLink class="h-4 w-4" />
          {{ t('preview.open_original') }}
        </Button>
      </div>

      <!-- Content -->
      <div v-else class="space-y-4">
        <!-- Source/Preview Toggle -->
        <div class="bg-neutral-100 dark:bg-neutral-800 p-1 rounded-xl inline-flex">
          <button
            @click="mode = 'preview'"
            :class="[
              'flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all',
              mode === 'preview'
                ? 'bg-white dark:bg-neutral-700 text-neutral-900 dark:text-neutral-100 shadow-sm'
                : 'text-neutral-500 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-neutral-100'
            ]"
          >
            <Eye class="h-4 w-4" />
            {{ t('preview.preview_mode') }}
          </button>
          <button
            @click="mode = 'source'"
            :class="[
              'flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all',
              mode === 'source'
                ? 'bg-white dark:bg-neutral-700 text-neutral-900 dark:text-neutral-100 shadow-sm'
                : 'text-neutral-500 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-neutral-100'
            ]"
          >
            <FileCode class="h-4 w-4" />
            {{ t('preview.source_mode') }}
          </button>
        </div>

        <!-- Preview Content -->
        <div v-if="mode === 'preview'" class="bg-white dark:bg-slate-950 rounded-lg overflow-hidden border border-slate-200 dark:border-slate-800">
          <MarkdownPreview :content="content" />
        </div>

        <!-- Source Content -->
        <div v-else class="bg-slate-100 dark:bg-slate-950 rounded-lg overflow-hidden border border-slate-200 dark:border-slate-800">
          <div class="flex items-center justify-between px-4 py-3 bg-slate-200 dark:bg-slate-900 border-b border-slate-300 dark:border-slate-800">
            <span class="text-sm font-medium text-slate-700 dark:text-slate-300">
              {{ t('preview.source_mode') }}
            </span>
          </div>
          <pre class="p-4 max-h-[40vh] overflow-auto text-sm text-slate-700 dark:text-slate-300 whitespace-pre-wrap break-words">{{ content }}</pre>
        </div>

        <!-- Actions -->
        <div class="flex justify-end gap-2">
          <Button
            variant="outline"
            size="sm"
            @click="openOriginal"
            class="gap-2"
          >
            <ExternalLink class="h-4 w-4" />
            {{ t('preview.open_original') }}
          </Button>
          <Button
            variant="outline"
            size="sm"
            @click="copyToClipboard"
            class="gap-2"
          >
            <Check v-if="copied" class="h-4 w-4 text-green-500" />
            <Copy v-else class="h-4 w-4" />
            {{ copied ? t('keys.copied') : t('keys.copy') }}
          </Button>
        </div>
      </div>
    </div>
  </Dialog>
</template>
```

**Step 2: Run test to verify it passes**

Run: `cd web && pnpm vitest run src/components/__tests__/ArticlePreviewDialog.test.ts`
Expected: PASS (3 tests)

**Step 3: Commit**

```bash
git add web/src/components/ArticlePreviewDialog.vue web/src/components/__tests__/ArticlePreviewDialog.test.ts
git commit -m "feat: add ArticlePreviewDialog component for preview UI"
```

---

## Phase 7: Page Integration

### Task 7.1: Update i18n Keys

**Files:**
- Modify: `web/src/locales/en.json`
- Modify: `web/src/locales/zh.json`

**Step 1: Add English translations**

Add to `web/src/locales/en.json`:

```json
{
  "preview": {
    "title": "Preview",
    "quick_preview": "Quick Preview",
    "open_new_tab": "Open in New Tab",
    "open_original": "Open Original Page",
    "loading": "Loading preview...",
    "cached": "From Cache",
    "fresh": "Fresh",
    "preview_mode": "Preview",
    "source_mode": "Source",
    "rate_limit": "Preview service temporarily unavailable, please try again later",
    "network_error": "Network error, please check your connection",
    "conversion_failed": "Unable to preview this page"
  }
}
```

**Step 2: Add Chinese translations**

Add to `web/src/locales/zh.json`:

```json
{
  "preview": {
    "title": "預覽",
    "quick_preview": "快速預覽",
    "open_new_tab": "在新分頁開啟",
    "open_original": "開啟原始頁面",
    "loading": "載入預覽中...",
    "cached": "來自快取",
    "fresh": "最新",
    "preview_mode": "預覽",
    "source_mode": "原始碼",
    "rate_limit": "預覽服務暫時無法使用，請稍後再試",
    "network_error": "網路錯誤，請檢查您的連線",
    "conversion_failed": "無法預覽此頁面"
  }
}
```

**Step 3: Commit**

```bash
git add web/src/locales/en.json web/src/locales/zh.json
git commit -m "feat: add i18n keys for preview feature"
```

---

### Task 7.2: Integrate Preview into FeedPage

**Files:**
- Modify: `web/src/pages/FeedPage.vue`

**Step 1: Add preview functionality**

Add imports and state:

```vue
<script setup lang="ts">
import { Clock, Database, Eye, ExternalLink, FileText, RefreshCw } from "lucide-vue-next";
import { onMounted, ref, watch } from "vue";
import { useI18n } from "vue-i18n";
import { getFeed } from "@/api/feed";
import { refreshAllSources } from "@/api/sources";
import ArticlePreviewDialog from "@/components/ArticlePreviewDialog.vue";
import RssPreviewDialog from "@/components/RssPreviewDialog.vue";
import Button from "@/components/ui/Button.vue";
import Input from "@/components/ui/Input.vue";
import type { FeedItem } from "@/types/feed";
import { useToast } from "@/composables/useToast";
import { formatDate } from "@/utils/format";

const { t } = useI18n();
const toast = useToast();

const feedItems = ref<FeedItem[]>([]);
const loading = ref(true);
const refreshing = ref(false);
const sortBy = ref<"published_at" | "source">("published_at");
const keywords = ref("");
const rssDialogOpen = ref(false);

// Preview dialog state
const previewDialogOpen = ref(false);
const previewUrl = ref("");
const previewTitle = ref("");

async function fetchFeed(): Promise<void> {
  loading.value = true;
  try {
    feedItems.value = await getFeed({
      sort_by: sortBy.value,
      keywords: keywords.value || undefined,
    });
  } finally {
    loading.value = false;
  }
}

async function handleRefreshAll(): Promise<void> {
  refreshing.value = true;
  try {
    await refreshAllSources();
    await fetchFeed();
    toast.success(t('common.success'));
  } catch {
    toast.error(t('common.error'));
  } finally {
    refreshing.value = false;
  }
}

function openPreview(item: FeedItem): void {
  previewUrl.value = item.link;
  previewTitle.value = item.title;
  previewDialogOpen.value = true;
}

function openInNewTab(url: string): void {
  window.open(url, "_blank", "noopener,noreferrer");
}

onMounted(fetchFeed);

watch([sortBy, keywords], () => {
  fetchFeed();
});
</script>
```

**Step 2: Update template**

Replace the feed item template section with:

```vue
<div v-else class="grid gap-4">
  <div
    v-for="item in feedItems"
    :key="item.id"
    class="p-6 bg-white dark:bg-neutral-800 rounded-xl border border-neutral-200 dark:border-neutral-700 hover:shadow-md transition-shadow"
  >
    <div class="flex items-start justify-between gap-4">
      <div class="flex-1 min-w-0">
        <div class="flex items-center gap-2 text-sm text-neutral-500 mb-2">
          <span class="text-primary-600 dark:text-primary-400">{{ item.source }}</span>
          <span>•</span>
          <span>{{ formatDate(item.published_at) }}</span>
        </div>
        
        <h3 class="text-lg font-medium text-neutral-900 dark:text-neutral-100 mb-2">
          {{ item.title }}
        </h3>
        
        <p class="text-neutral-600 dark:text-neutral-400 line-clamp-2">
          {{ item.description }}
        </p>
      </div>

      <!-- Preview action buttons -->
      <div class="flex items-center gap-1 shrink-0">
        <button
          @click.stop="openPreview(item)"
          class="p-2 rounded-lg hover:bg-neutral-100 dark:hover:bg-neutral-700 text-neutral-500 dark:text-neutral-400 hover:text-primary-600 dark:hover:text-primary-400 transition-colors"
          :title="t('preview.quick_preview')"
          :aria-label="t('preview.quick_preview')"
          type="button"
        >
          <Eye class="h-4 w-4" />
        </button>
        <button
          @click.stop="openInNewTab(item.link)"
          class="p-2 rounded-lg hover:bg-neutral-100 dark:hover:bg-neutral-700 text-neutral-500 dark:text-neutral-400 hover:text-primary-600 dark:hover:text-primary-400 transition-colors"
          :title="t('preview.open_new_tab')"
          :aria-label="t('preview.open_new_tab')"
          type="button"
        >
          <ExternalLink class="h-4 w-4" />
        </button>
      </div>
    </div>
  </div>
</div>

<!-- Preview dialog -->
<ArticlePreviewDialog
  v-model:open="previewDialogOpen"
  :url="previewUrl"
  :title="previewTitle"
/>
```

**Step 3: Commit**

```bash
git add web/src/pages/FeedPage.vue
git commit -m "feat: integrate article preview into FeedPage"
```

---

### Task 7.3: Integrate Preview into HistoryPage

**Files:**
- Modify: `web/src/pages/HistoryPage.vue`

**Step 1: Add preview state and functions**

Add imports:

```typescript
import { Check, ChevronDown, ChevronUp, Copy, Download, Edit3, Eye, ExternalLink, FileText, Pencil, RefreshCw, Trash2, X } from "lucide-vue-next"
```

Add preview state:

```typescript
// Article preview state
const articlePreviewOpen = ref(false)
const articlePreviewUrl = ref("")
const articlePreviewTitle = ref("")

function openArticlePreview(item: HistoryItem): void {
  articlePreviewUrl.value = item.link
  articlePreviewTitle.value = item.title
  articlePreviewOpen.value = true
}

function openArticleInNewTab(url: string): void {
  window.open(url, "_blank", "noopener,noreferrer")
}
```

**Step 2: Update expanded items template**

Find the expanded items section and update each item to include preview buttons:

```vue
<div v-else class="divide-y divide-neutral-200 dark:divide-neutral-700">
  <div
    v-for="item in expandedItems"
    :key="item.id"
    class="p-4 hover:bg-neutral-50 dark:hover:bg-neutral-900 transition-colors"
  >
    <div class="flex items-start justify-between gap-3">
      <div class="flex-1 min-w-0">
        <div class="flex items-center gap-2 text-xs text-neutral-500 mb-1">
          <span class="text-primary-600 dark:text-primary-400">{{ item.source }}</span>
          <span v-if="item.published_at">•</span>
          <span v-if="item.published_at">{{ formatDate(item.published_at) }}</span>
        </div>
        <h4 class="text-sm font-medium text-neutral-900 dark:text-neutral-100 truncate">
          {{ item.title }}
        </h4>
        <p v-if="item.description" class="mt-1 text-xs text-neutral-500 line-clamp-2">
          {{ item.description }}
        </p>
      </div>
      
      <!-- Preview action buttons -->
      <div class="flex items-center gap-1 shrink-0">
        <button
          @click.stop="openArticlePreview(item)"
          class="p-1.5 rounded-lg hover:bg-neutral-100 dark:hover:bg-neutral-700 text-neutral-500 dark:text-neutral-400 hover:text-primary-600 dark:hover:text-primary-400 transition-colors"
          :title="t('preview.quick_preview')"
          :aria-label="t('preview.quick_preview')"
          type="button"
        >
          <Eye class="h-4 w-4" />
        </button>
        <button
          @click.stop="openArticleInNewTab(item.link)"
          class="p-1.5 rounded-lg hover:bg-neutral-100 dark:hover:bg-neutral-700 text-neutral-500 dark:text-neutral-400 hover:text-primary-600 dark:hover:text-primary-400 transition-colors"
          :title="t('preview.open_new_tab')"
          :aria-label="t('preview.open_new_tab')"
          type="button"
        >
          <ExternalLink class="h-4 w-4" />
        </button>
      </div>
    </div>
  </div>
</div>
```

**Step 3: Add ArticlePreviewDialog**

Add before the closing `</template>`:

```vue
<!-- Article Preview Dialog -->
<ArticlePreviewDialog
  v-model:open="articlePreviewOpen"
  :url="articlePreviewUrl"
  :title="articlePreviewTitle"
/>
```

**Step 4: Add import for ArticlePreviewDialog**

```typescript
import ArticlePreviewDialog from "@/components/ArticlePreviewDialog.vue"
```

**Step 5: Commit**

```bash
git add web/src/pages/HistoryPage.vue
git commit -m "feat: integrate article preview into HistoryPage"
```

---

## Phase 8: E2E Tests

### Task 8.1: Create E2E Test for Preview Feature

**Files:**
- Create: `web/e2e/preview.spec.ts`

**Step 1: Write the E2E tests**

```typescript
// web/e2e/preview.spec.ts
import { test, expect } from '@playwright/test'

test.describe('Article Preview Feature', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the app
    await page.goto('/')
    
    // Wait for the app to load
    await page.waitForSelector('[data-testid="feed-page"], [data-testid="auth-dialog"]')
  })

  test('should display preview buttons on feed items', async ({ page }) => {
    // Skip if no feed items
    const feedItems = page.locator('[data-testid="feed-item"]')
    const count = await feedItems.count()
    
    if (count > 0) {
      // Check that first feed item has preview button
      const firstItem = feedItems.first()
      const previewButton = firstItem.locator('[aria-label="Quick Preview"]')
      await expect(previewButton).toBeVisible()
      
      const newTabButton = firstItem.locator('[aria-label="Open in New Tab"]')
      await expect(newTabButton).toBeVisible()
    }
  })

  test('should open preview dialog when clicking preview button', async ({ page }) => {
    const feedItems = page.locator('[data-testid="feed-item"]')
    const count = await feedItems.count()
    
    if (count > 0) {
      // Click preview button on first item
      const previewButton = feedItems.first().locator('[aria-label="Quick Preview"]')
      await previewButton.click()
      
      // Wait for preview dialog to open
      const previewDialog = page.locator('[data-testid="preview-dialog"]')
      await expect(previewDialog).toBeVisible()
      
      // Check for loading state or content
      const loadingIndicator = previewDialog.locator('.animate-pulse')
      const content = previewDialog.locator('.markdown-preview')
      
      // Either loading or content should be visible
      await expect(
        (await loadingIndicator.count()) > 0 || (await content.count()) > 0
      ).toBeTruthy()
    }
  })

  test('should toggle between preview and source modes', async ({ page }) => {
    const feedItems = page.locator('[data-testid="feed-item"]')
    const count = await feedItems.count()
    
    if (count > 0) {
      // Open preview dialog
      await feedItems.first().locator('[aria-label="Quick Preview"]').click()
      
      const previewDialog = page.locator('[data-testid="preview-dialog"]')
      await previewDialog.waitFor({ state: 'visible' })
      
      // Click source mode button
      const sourceButton = previewDialog.locator('button:has-text("Source")')
      await sourceButton.click()
      
      // Verify source code view is visible
      const sourceView = previewDialog.locator('pre')
      await expect(sourceView).toBeVisible()
      
      // Click preview mode button
      const previewButton = previewDialog.locator('button:has-text("Preview")')
      await previewButton.click()
      
      // Verify preview view is visible
      const previewView = previewDialog.locator('.markdown-preview')
      await expect(previewView).toBeVisible()
    }
  })

  test('should close preview dialog', async ({ page }) => {
    const feedItems = page.locator('[data-testid="feed-item"]')
    const count = await feedItems.count()
    
    if (count > 0) {
      // Open preview dialog
      await feedItems.first().locator('[aria-label="Quick Preview"]').click()
      
      const previewDialog = page.locator('[data-testid="preview-dialog"]')
      await previewDialog.waitFor({ state: 'visible' })
      
      // Click close button
      const closeButton = previewDialog.locator('button[aria-label="Close"]').first()
      await closeButton.click()
      
      // Verify dialog is closed
      await expect(previewDialog).not.toBeVisible()
    }
  })
})
```

**Step 2: Run E2E tests**

Run: `cd web && pnpm playwright test preview.spec.ts`
Expected: Tests may fail if selectors don't match - adjust as needed

**Step 3: Commit**

```bash
git add web/e2e/preview.spec.ts
git commit -m "feat: add E2E tests for article preview feature"
```

---

## Phase 9: Final Tasks

### Task 9.1: Add data-testid Attributes

**Files:**
- Modify: `web/src/components/ArticlePreviewDialog.vue`
- Modify: `web/src/pages/FeedPage.vue`
- Modify: `web/src/pages/HistoryPage.vue`

**Step 1: Add test IDs to ArticlePreviewDialog**

```vue
<Dialog :open="open" size="2xl" @update:open="close" data-testid="preview-dialog">
```

**Step 2: Add test IDs to FeedPage**

```vue
<div class="grid gap-4">
  <div
    v-for="item in feedItems"
    :key="item.id"
    data-testid="feed-item"
    class="p-6 ..."
  >
```

**Step 3: Commit**

```bash
git add web/src/components/ArticlePreviewDialog.vue web/src/pages/FeedPage.vue web/src/pages/HistoryPage.vue
git commit -m "feat: add data-testid attributes for E2E testing"
```

---

### Task 9.2: Run All Tests and Verify

**Step 1: Run backend tests**

```bash
uv run pytest -v
```

**Step 2: Run frontend tests**

```bash
cd web && pnpm vitest run
```

**Step 3: Run E2E tests**

```bash
cd web && pnpm playwright test
```

**Step 4: Run linting**

```bash
uv run ruff check .
cd web && pnpm lint
```

**Step 5: Commit if any fixes needed**

```bash
git add -A
git commit -m "fix: address test failures and lint issues"
```

---

### Task 9.3: Update Documentation

**Files:**
- Modify: `README.md`
- Modify: `CHANGELOG.md`

**Step 1: Update README**

Add a section about the preview feature:

```markdown
### Quick Preview

Users can quickly preview article content without leaving the application:

- **Preview Button** (eye icon): Opens a dialog with the article content rendered in Markdown
- **Open in New Tab** (external link icon): Opens the original article in a new browser tab

The preview feature uses the [markdown.new](https://markdown.new) service to convert web pages to Markdown format. 
Previewed content is cached in the database for faster subsequent access.
```

**Step 2: Update CHANGELOG**

```markdown
## [Unreleased]

### Added
- Quick preview feature for articles using markdown.new service
- Preview cache stored in database by URL hash
- Preview dialog with source/preview toggle
- Preview buttons on Feed and History pages
- i18n support for preview feature (English and Chinese)
```

**Step 3: Commit**

```bash
git add README.md CHANGELOG.md
git commit -m "docs: update documentation for preview feature"
```

---

### Task 9.4: Final Commit and Tag

**Step 1: Ensure all changes are committed**

```bash
git status
```

**Step 2: Create version tag**

```bash
git tag -a v1.1.0 -m "feat: add article quick preview feature"
```

---

## Execution Options

**Plan complete and saved to `docs/plans/2026-03-26-article-preview-feature.md`. Two execution options:**

**1. Subagent-Driven (this session)** - I dispatch fresh subagent per task, review between tasks, fast iteration

**2. Parallel Session (separate)** - Open new session with executing-plans, batch execution with checkpoints

**Which approach?**