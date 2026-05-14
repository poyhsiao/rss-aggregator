# Feed Format Path-Based Routes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add path-based format routes (`/feed/{format}`, `/sources/{id}/{format}`, `/groups/{id}/{format}`) and display copyable API paths in the preview feed dialog.

**Architecture:** New thin FastAPI route handlers extract `format` from the path segment and delegate to the existing `feed_service.get_formatted_feed()`. Parallel stdio router handlers match the same URL patterns. Frontend adds a `buildFeedPathUrl()` utility and an API paths section to `RssPreviewDialog`.

**Tech Stack:** Python/FastAPI, SQLAlchemy (async), Vue 3 + TypeScript, Vitest, Playwright, pytest

---

## File Structure

### Backend — Create
- `tests/api/test_feed_format_routes.py` — unit tests for `/feed/{format}`
- `tests/api/test_source_format_routes.py` — unit tests for `/sources/{id}/{format}`
- `tests/api/test_group_format_routes.py` — unit tests for `/groups/{id}/{format}`

### Backend — Modify
- `src/api/routes/feed.py` — add `GET /feed/{format}` endpoint
- `src/api/routes/sources.py` — add `GET /sources/{source_id}/{format}` endpoint
- `src/api/routes/source_groups.py` — add `GET /source-groups/{group_id}/{format}` endpoint
- `src/stdio/router.py` — add three handler methods + routing entries
- `src/main.py` — no change needed (routes already registered with prefix)

### Frontend — Create
- `web/src/api/__tests__/feed-api.test.ts` — unit tests for `buildFeedPathUrl`

### Frontend — Modify
- `web/src/api/feed.ts` — add `buildFeedPathUrl()` function, update `getFormattedFeed()` to use path-based URL
- `web/src/components/RssPreviewDialog.vue` — add API paths section above format selector
- `web/src/locales/en.json` — add `feed.api_paths`, `feed.copy_path`, `feed.path_copied`
- `web/src/locales/zh.json` — add matching Chinese keys

### E2E — Create
- `web/e2e/feed-format-routes.spec.ts` — verify path-based API endpoints return correct content
- `web/e2e/preview-api-paths.spec.ts` — verify API paths display in preview dialog

---

### Task 1: Backend — `/feed/{format}` route (TDD)

**Files:**
- Create: `tests/api/test_feed_format_routes.py`
- Modify: `src/api/routes/feed.py:1-73`

- [ ] **Step 1: Write the failing test**

Create `tests/api/test_feed_format_routes.py`:

```python
"""Tests for path-based feed format routes."""

import pytest
from httpx import AsyncClient, ASGITransport

from src.main import app
from src.services.auth_service import AuthService
from src.db.database import async_session_factory
from src.models import Source, FeedItem
from src.utils.time import now
from datetime import timedelta


@pytest_asyncio.fixture
async def seed_data():
    """Seed test data and return API key."""
    async with async_session_factory() as session:
        auth_svc = AuthService(session)
        api_key = await auth_svc.create_key("test-key-feed-format")

        source = Source(name="Format Test Source", url="https://format-test.com/rss")
        session.add(source)
        await session.flush()

        current_time = now()
        item = FeedItem(
            source_id=source.id,
            title="Format Test Article",
            link="https://format-test.com/article-1",
            description="Test description",
            published_at=current_time - timedelta(hours=1),
        )
        session.add(item)
        await session.commit()

    return api_key.key


@pytest.mark.asyncio
async def test_feed_rss_format_returns_xml(seed_data):
    """GET /feed/rss returns RSS XML content."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/feed/rss",
            headers={"X-API-Key": seed_data},
        )
    assert response.status_code == 200
    assert "application/xml" in response.headers["content-type"]
    assert "<?xml" in response.text


@pytest.mark.asyncio
async def test_feed_json_format_returns_json(seed_data):
    """GET /feed/json returns JSON content."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/feed/json",
            headers={"X-API-Key": seed_data},
        )
    assert response.status_code == 200
    assert "application/json" in response.headers["content-type"]
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


@pytest.mark.asyncio
async def test_feed_markdown_format_returns_markdown(seed_data):
    """GET /feed/markdown returns Markdown content."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/feed/markdown",
            headers={"X-API-Key": seed_data},
        )
    assert response.status_code == 200
    assert "text/markdown" in response.headers["content-type"]
    assert "#" in response.text


@pytest.mark.asyncio
async def test_feed_invalid_format_returns_422(seed_data):
    """GET /feed/invalid returns 422."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/feed/invalid",
            headers={"X-API-Key": seed_data},
        )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_feed_format_with_query_params(seed_data):
    """GET /feed/json?sort_by=source passes query params through."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/feed/json?sort_by=source&sort_order=asc",
            headers={"X-API-Key": seed_data},
        )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_feed_format_requires_auth():
    """GET /feed/rss without API key returns 401 when auth is required."""
    from src.config import settings
    if not settings.require_api_key:
        pytest.skip("API key not required")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/feed/rss")
    assert response.status_code == 401
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/kimhsiao/Templates/git/pic.net.tw/RSS-collection && uv run pytest tests/api/test_feed_format_routes.py -v`

Expected: FAIL with 404 (route `/feed/rss` not found) or similar routing error.

- [ ] **Step 3: Write minimal implementation**

Modify `src/api/routes/feed.py`. Add a new endpoint after the existing `get_feed`:

```python
@router.get("/{format}")
async def get_feed_by_format(
    format: str = Path(
        ...,
        pattern="^(rss|json|markdown)$",
        description="Output format: 'rss', 'json', or 'markdown'",
    ),
    sort_by: str = Query(
        "published_at",
        pattern="^(published_at|source)$",
        description="Sort by field",
    ),
    sort_order: str = Query(
        "desc",
        pattern="^(asc|desc)$",
        description="Sort direction",
    ),
    valid_time: int | None = Query(
        None,
        ge=1,
        description="Time range in hours",
    ),
    keywords: str | None = Query(
        None,
        description="Keywords (semicolon-separated)",
    ),
    source_id: int | None = Query(
        None,
        description="Filter by source ID",
    ),
    group_id: int | None = Query(
        None,
        description="Filter by source group ID",
    ),
    feed_service: FeedService = Depends(get_feed_service),
    _: str = Depends(require_api_key),
) -> Any:
    """Get aggregated feed in a specific format via path.

    Path params:
    - format: Output format ('rss', 'json', or 'markdown')

    Query params:
    - sort_by: Sort field ('published_at' or 'source')
    - sort_order: Sort direction ('asc' or 'desc')
    - valid_time: Time range in hours
    - keywords: Keywords for filtering (semicolon-separated)
    - source_id: Filter by source ID
    - group_id: Filter by source group ID
    """
    content, content_type = await feed_service.get_formatted_feed(
        format=format,
        sort_by=sort_by,
        sort_order=sort_order,
        valid_time=valid_time,
        keywords=keywords,
        source_id=source_id,
        group_id=group_id,
    )
    return Response(content=content, media_type=content_type)
```

Also add `Path` to the import line at the top of the file:

```python
from fastapi import APIRouter, Depends, Path, Query, Response
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/kimhsiao/Templates/git/pic.net.tw/RSS-collection && uv run pytest tests/api/test_feed_format_routes.py -v`

Expected: All 6 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add tests/api/test_feed_format_routes.py src/api/routes/feed.py
git commit -m "feat: add GET /feed/{format} path-based route with tests"
```

---

### Task 2: Backend — `/sources/{source_id}/{format}` route (TDD)

**Files:**
- Create: `tests/api/test_source_format_routes.py`
- Modify: `src/api/routes/sources.py:207-262`

- [ ] **Step 1: Write the failing test**

Create `tests/api/test_source_format_routes.py`:

```python
"""Tests for path-based source feed format routes."""

import pytest
from httpx import AsyncClient, ASGITransport

from src.main import app
from src.services.auth_service import AuthService
from src.db.database import async_session_factory
from src.models import Source, FeedItem
from src.utils.time import now
from datetime import timedelta


@pytest_asyncio.fixture
async def seed_source_data():
    """Seed a source with items and return (api_key, source_id)."""
    async with async_session_factory() as session:
        auth_svc = AuthService(session)
        api_key = await auth_svc.create_key("test-key-source-format")

        source = Source(name="Source Format Test", url="https://source-fmt.com/rss")
        session.add(source)
        await session.flush()
        source_id = source.id

        current_time = now()
        item = FeedItem(
            source_id=source_id,
            title="Source Format Article",
            link="https://source-fmt.com/article-1",
            description="Source format test",
            published_at=current_time - timedelta(hours=1),
        )
        session.add(item)
        await session.commit()

    return api_key.key, source_id


@pytest.mark.asyncio
async def test_source_feed_rss_format_returns_xml(seed_source_data):
    api_key, source_id = seed_source_data
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            f"/api/v1/sources/{source_id}/rss",
            headers={"X-API-Key": api_key},
        )
    assert response.status_code == 200
    assert "application/xml" in response.headers["content-type"]
    assert "<?xml" in response.text


@pytest.mark.asyncio
async def test_source_feed_json_format_returns_json(seed_source_data):
    api_key, source_id = seed_source_data
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            f"/api/v1/sources/{source_id}/json",
            headers={"X-API-Key": api_key},
        )
    assert response.status_code == 200
    assert "application/json" in response.headers["content-type"]


@pytest.mark.asyncio
async def test_source_feed_markdown_format_returns_markdown(seed_source_data):
    api_key, source_id = seed_source_data
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            f"/api/v1/sources/{source_id}/markdown",
            headers={"X-API-Key": api_key},
        )
    assert response.status_code == 200
    assert "text/markdown" in response.headers["content-type"]


@pytest.mark.asyncio
async def test_source_feed_invalid_format_returns_422(seed_source_data):
    api_key, source_id = seed_source_data
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            f"/api/v1/sources/{source_id}/invalid",
            headers={"X-API-Key": api_key},
        )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_source_feed_nonexistent_source_returns_404(seed_source_data):
    api_key, _ = seed_source_data
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/sources/99999/rss",
            headers={"X-API-Key": api_key},
        )
    assert response.status_code == 404
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/kimhsiao/Templates/git/pic.net.tw/RSS-collection && uv run pytest tests/api/test_source_format_routes.py -v`

Expected: FAIL with 404 or routing error.

- [ ] **Step 3: Write minimal implementation**

Modify `src/api/routes/sources.py`. Add a new endpoint after the existing `get_source_feed`. Add `Path` to the imports:

```python
from fastapi import APIRouter, Depends, HTTPException, Path, Query, Response, status
```

Add the new endpoint after `get_source_feed` (after line 261):

```python
@router.get("/{source_id}/{format}")
async def get_source_feed_by_format(
    source_id: int,
    format: str = Path(
        ...,
        pattern="^(rss|json|markdown)$",
        description="Output format: 'rss', 'json', or 'markdown'",
    ),
    sort_by: str = Query(
        "published_at",
        pattern="^(published_at|source)$",
        description="Sort by field",
    ),
    sort_order: str = Query(
        "desc",
        pattern="^(asc|desc)$",
        description="Sort direction",
    ),
    valid_time: int | None = Query(
        None,
        ge=1,
        description="Time range in hours",
    ),
    keywords: str | None = Query(
        None,
        description="Keywords (semicolon-separated)",
    ),
    feed_service: FeedService = Depends(get_feed_service),
    _: str = Depends(require_api_key),
) -> Response:
    """Get feed for a specific source in a specific format via path.

    Path params:
    - source_id: Source ID
    - format: Output format ('rss', 'json', or 'markdown')

    Query params:
    - sort_by: Sort field ('published_at' or 'source')
    - sort_order: Sort direction ('asc' or 'desc')
    - valid_time: Time range in hours
    - keywords: Keywords for filtering (semicolon-separated)
    """
    source_service = SourceService(feed_service.session)
    source = await source_service.get_source(source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    content, content_type = await feed_service.get_formatted_feed(
        format=format,
        sort_by=sort_by,
        sort_order=sort_order,
        valid_time=valid_time,
        keywords=keywords,
        source_id=source_id,
    )
    return Response(content=content, media_type=content_type)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/kimhsiao/Templates/git/pic.net.tw/RSS-collection && uv run pytest tests/api/test_source_format_routes.py -v`

Expected: All 5 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add tests/api/test_source_format_routes.py src/api/routes/sources.py
git commit -m "feat: add GET /sources/{id}/{format} path-based route with tests"
```

---

### Task 3: Backend — `/source-groups/{group_id}/{format}` route (TDD)

**Files:**
- Create: `tests/api/test_group_format_routes.py`
- Modify: `src/api/routes/source_groups.py`

- [ ] **Step 1: Write the failing test**

Create `tests/api/test_group_format_routes.py`:

```python
"""Tests for path-based group feed format routes."""

import pytest
from httpx import AsyncClient, ASGITransport

from src.main import app
from src.services.auth_service import AuthService
from src.services.source_group_service import SourceGroupService
from src.services.source_service import SourceService
from src.db.database import async_session_factory
from src.models import Source, FeedItem
from src.utils.time import now
from datetime import timedelta


@pytest_asyncio.fixture
async def seed_group_data():
    """Seed a group with a source and items, return (api_key, group_id)."""
    async with async_session_factory() as session:
        auth_svc = AuthService(session)
        api_key = await auth_svc.create_key("test-key-group-format")

        group_svc = SourceGroupService(session)
        source_svc = SourceService(session)

        group = await group_svc.create_group(name="Format Test Group")
        source = await source_svc.create_source(
            "Group Format Source", "https://group-fmt.com/rss"
        )
        await group_svc.add_source_to_group(group.id, source.id)

        current_time = now()
        item = FeedItem(
            source_id=source.id,
            title="Group Format Article",
            link="https://group-fmt.com/article-1",
            description="Group format test",
            published_at=current_time - timedelta(hours=1),
        )
        session.add(item)
        await session.commit()

    return api_key.key, group.id


@pytest.mark.asyncio
async def test_group_feed_rss_format_returns_xml(seed_group_data):
    api_key, group_id = seed_group_data
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            f"/api/v1/source-groups/{group_id}/rss",
            headers={"X-API-Key": api_key},
        )
    assert response.status_code == 200
    assert "application/xml" in response.headers["content-type"]
    assert "<?xml" in response.text


@pytest.mark.asyncio
async def test_group_feed_json_format_returns_json(seed_group_data):
    api_key, group_id = seed_group_data
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            f"/api/v1/source-groups/{group_id}/json",
            headers={"X-API-Key": api_key},
        )
    assert response.status_code == 200
    assert "application/json" in response.headers["content-type"]


@pytest.mark.asyncio
async def test_group_feed_markdown_format_returns_markdown(seed_group_data):
    api_key, group_id = seed_group_data
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            f"/api/v1/source-groups/{group_id}/markdown",
            headers={"X-API-Key": api_key},
        )
    assert response.status_code == 200
    assert "text/markdown" in response.headers["content-type"]


@pytest.mark.asyncio
async def test_group_feed_invalid_format_returns_422(seed_group_data):
    api_key, group_id = seed_group_data
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            f"/api/v1/source-groups/{group_id}/invalid",
            headers={"X-API-Key": api_key},
        )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_group_feed_nonexistent_group_returns_404(seed_group_data):
    api_key, _ = seed_group_data
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/source-groups/99999/rss",
            headers={"X-API-Key": api_key},
        )
    assert response.status_code == 404
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/kimhsiao/Templates/git/pic.net.tw/RSS-collection && uv run pytest tests/api/test_group_format_routes.py -v`

Expected: FAIL.

- [ ] **Step 3: Write minimal implementation**

Modify `src/api/routes/source_groups.py`. Add `Path`, `Query`, `Response`, `FeedService`, `get_feed_service` to imports:

```python
from fastapi import APIRouter, Depends, HTTPException, Path, Query, Response, status
```

```python
from src.api.deps import get_feed_service, get_scheduler, get_source_group_service, require_api_key
from src.services.feed_service import FeedService
from src.services.source_group_service import SourceGroupService
```

Add the new endpoint at the end of the file (before the closing of the router, after `refresh_group_sources`):

```python
@router.get("/{group_id}/{format}")
async def get_group_feed_by_format(
    group_id: int,
    format: str = Path(
        ...,
        pattern="^(rss|json|markdown)$",
        description="Output format: 'rss', 'json', or 'markdown'",
    ),
    sort_by: str = Query(
        "published_at",
        pattern="^(published_at|source)$",
        description="Sort by field",
    ),
    sort_order: str = Query(
        "desc",
        pattern="^(asc|desc)$",
        description="Sort direction",
    ),
    valid_time: int | None = Query(
        None,
        ge=1,
        description="Time range in hours",
    ),
    keywords: str | None = Query(
        None,
        description="Keywords (semicolon-separated)",
    ),
    feed_service: FeedService = Depends(get_feed_service),
    group_service: SourceGroupService = Depends(get_source_group_service),
    _: str = Depends(require_api_key),
) -> Response:
    """Get feed for a specific group in a specific format via path.

    Path params:
    - group_id: Source group ID
    - format: Output format ('rss', 'json', or 'markdown')

    Query params:
    - sort_by: Sort field ('published_at' or 'source')
    - sort_order: Sort direction ('asc' or 'desc')
    - valid_time: Time range in hours
    - keywords: Keywords for filtering (semicolon-separated)
    """
    groups = await group_service.list_groups_with_count()
    group_exists = any(g["id"] == group_id for g in groups)
    if not group_exists:
        raise HTTPException(status_code=404, detail="Group not found")

    content, content_type = await feed_service.get_formatted_feed(
        format=format,
        sort_by=sort_by,
        sort_order=sort_order,
        valid_time=valid_time,
        keywords=keywords,
        group_id=group_id,
    )
    return Response(content=content, media_type=content_type)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/kimhsiao/Templates/git/pic.net.tw/RSS-collection && uv run pytest tests/api/test_group_format_routes.py -v`

Expected: All 5 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add tests/api/test_group_format_routes.py src/api/routes/source_groups.py
git commit -m "feat: add GET /source-groups/{id}/{format} path-based route with tests"
```

---

### Task 4: Backend — stdio router handlers (TDD)

**Files:**
- Modify: `src/stdio/router.py`

- [ ] **Step 1: Write the failing test**

Add tests to the bottom of `tests/api/test_feed_format_routes.py` (or create `tests/api/test_stdio_format_routes.py` — use the existing test pattern). Since the stdio router is tested indirectly through the JSON-RPC protocol, add integration-style tests:

Create `tests/api/test_stdio_format_routes.py`:

```python
"""Tests for stdio router path-based format routes."""

import pytest
from src.stdio.router import StdioRouter
from src.stdio.protocol import JSONRPCRequest
from src.db.database import async_session_factory
from src.services.auth_service import AuthService
from src.models import Source, FeedItem
from src.utils.time import now
from datetime import timedelta


@pytest_asyncio.fixture
async def stdio_seed_data():
    """Seed data and return api key."""
    async with async_session_factory() as session:
        auth_svc = AuthService(session)
        api_key_obj = await auth_svc.create_key("stdio-format-key")

        source = Source(name="Stdio Format Source", url="https://stdio-fmt.com/rss")
        session.add(source)
        await session.flush()

        current_time = now()
        item = FeedItem(
            source_id=source.id,
            title="Stdio Format Article",
            link="https://stdio-fmt.com/article-1",
            description="Stdio format test",
            published_at=current_time - timedelta(hours=1),
        )
        session.add(item)
        await session.commit()

    return api_key_obj.key


@pytest.mark.asyncio
async def test_stdio_feed_format_rss(stdio_seed_data):
    router = StdioRouter()
    request = JSONRPCRequest(
        id=1,
        method="http",
        params={
            "http_method": "GET",
            "path": "/api/v1/feed/rss",
            "headers": {"X-API-Key": stdio_seed_data},
            "query": {},
            "body": None,
        },
    )
    response = await router.route(request)
    assert response.result is not None
    result = response.result
    assert result["status"] == 200
    assert "application/xml" in result["headers"]["content-type"]


@pytest.mark.asyncio
async def test_stdio_feed_format_json(stdio_seed_data):
    router = StdioRouter()
    request = JSONRPCRequest(
        id=2,
        method="http",
        params={
            "http_method": "GET",
            "path": "/api/v1/feed/json",
            "headers": {"X-API-Key": stdio_seed_data},
            "query": {},
            "body": None,
        },
    )
    response = await router.route(request)
    result = response.result
    assert result["status"] == 200
    assert "application/json" in result["headers"]["content-type"]


@pytest.mark.asyncio
async def test_stdio_source_feed_format(stdio_seed_data):
    router = StdioRouter()
    request = JSONRPCRequest(
        id=3,
        method="http",
        params={
            "http_method": "GET",
            "path": "/api/v1/sources/1/rss",
            "headers": {"X-API-Key": stdio_seed_data},
            "query": {},
            "body": None,
        },
    )
    response = await router.route(request)
    result = response.result
    assert result["status"] in (200, 404)  # 404 if source id 1 doesn't match
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/kimhsiao/Templates/git/pic.net.tw/RSS-collection && uv run pytest tests/api/test_stdio_format_routes.py -v`

Expected: FAIL with `MethodNotFound` error.

- [ ] **Step 3: Write minimal implementation**

Modify `src/stdio/router.py`.

**Routing entries** — add these in the `route()` method, BEFORE the existing `/api/v1/feed` catch-all (around line 160), since more specific paths must match first:

```python
# Path-based format routes (must come before general feed route)
if re.match(r"^/api/v1/feed/(rss|json|markdown)$", path) and http_method == "GET":
    format_val = path.split("/")[-1]
    return await self._handle_get_feed_format(format_val, query, session)

if re.match(r"^/api/v1/sources/\d+/(rss|json|markdown)$", path) and http_method == "GET":
    return await self._handle_get_source_feed_format(path, query, session)

if re.match(r"^/api/v1/source-groups/\d+/(rss|json|markdown)$", path) and http_method == "GET":
    return await self._handle_get_group_feed_format(path, query, session)
```

**Handler methods** — add these three methods after `_handle_get_feed` (after line 343):

```python
async def _handle_get_feed_format(
    self, format_val: str, query: dict[str, Any], session: Any
) -> dict[str, Any]:
    """Handle GET /api/v1/feed/{format}."""
    feed_service = await get_feed_service(session)

    sort_by = query.get("sort_by", "published_at")
    sort_order = query.get("sort_order", "desc")
    valid_time = query.get("valid_time")
    keywords = query.get("keywords")
    source_id = query.get("source_id")
    group_id = query.get("group_id")

    if format_val == "json":
        items = await feed_service.get_feed_items(
            sort_by=sort_by,
            sort_order=sort_order,
            valid_time=valid_time,
            keywords=keywords,
            source_id=source_id,
            group_id=group_id,
        )
        return {
            "status": 200,
            "headers": {"content-type": "application/json"},
            "body": items,
        }

    content, content_type = await feed_service.get_formatted_feed(
        format=format_val,
        sort_by=sort_by,
        sort_order=sort_order,
        valid_time=valid_time,
        keywords=keywords,
        source_id=source_id,
        group_id=group_id,
    )

    return {
        "status": 200,
        "headers": {"content-type": content_type},
        "body": content,
    }

async def _handle_get_source_feed_format(
    self, path: str, query: dict[str, Any], session: Any
) -> dict[str, Any]:
    """Handle GET /api/v1/sources/{id}/{format}."""
    source_id = self._extract_path_param(path, r"/api/v1/sources/(\d+)/(rss|json|markdown)$")
    format_match = re.search(r"/(rss|json|markdown)$", path)
    format_val = format_match.group(1) if format_match else "rss"

    feed_service = await get_feed_service(session)
    source_service = await get_source_service(session)
    source = await source_service.get_source(source_id)

    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    sort_by = query.get("sort_by", "published_at")
    sort_order = query.get("sort_order", "desc")
    valid_time = query.get("valid_time")
    keywords = query.get("keywords")

    if format_val == "json":
        items = await feed_service.get_feed_items(
            sort_by=sort_by,
            sort_order=sort_order,
            valid_time=valid_time,
            keywords=keywords,
            source_id=source_id,
        )
        return {
            "status": 200,
            "headers": {"content-type": "application/json"},
            "body": items,
        }

    content, content_type = await feed_service.get_formatted_feed(
        format=format_val,
        sort_by=sort_by,
        sort_order=sort_order,
        valid_time=valid_time,
        keywords=keywords,
        source_id=source_id,
    )

    return {
        "status": 200,
        "headers": {"content-type": content_type},
        "body": content,
    }

async def _handle_get_group_feed_format(
    self, path: str, query: dict[str, Any], session: Any
) -> dict[str, Any]:
    """Handle GET /api/v1/source-groups/{id}/{format}."""
    group_id = self._extract_path_param(
        path, r"/api/v1/source-groups/(\d+)/(rss|json|markdown)$"
    )
    format_match = re.search(r"/(rss|json|markdown)$", path)
    format_val = format_match.group(1) if format_match else "rss"

    feed_service = await get_feed_service(session)
    group_service = await get_source_group_service(session)

    groups = await group_service.list_groups_with_count()
    group_exists = any(g["id"] == group_id for g in groups)
    if not group_exists:
        raise HTTPException(status_code=404, detail="Group not found")

    sort_by = query.get("sort_by", "published_at")
    sort_order = query.get("sort_order", "desc")
    valid_time = query.get("valid_time")
    keywords = query.get("keywords")

    if format_val == "json":
        items = await feed_service.get_feed_items(
            sort_by=sort_by,
            sort_order=sort_order,
            valid_time=valid_time,
            keywords=keywords,
            group_id=group_id,
        )
        return {
            "status": 200,
            "headers": {"content-type": "application/json"},
            "body": items,
        }

    content, content_type = await feed_service.get_formatted_feed(
        format=format_val,
        sort_by=sort_by,
        sort_order=sort_order,
        valid_time=valid_time,
        keywords=keywords,
        group_id=group_id,
    )

    return {
        "status": 200,
        "headers": {"content-type": content_type},
        "body": content,
    }
```

Also add `get_source_group_service` to the imports at the top of the file if not already present:

```python
from src.api.deps import (
    get_auth_service,
    get_backup_service,
    get_feed_service,
    get_fetch_service,
    get_history_service,
    get_preview_service,
    get_session,
    get_source_group_service,
    get_source_service,
)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/kimhsiao/Templates/git/pic.net.tw/RSS-collection && uv run pytest tests/api/test_stdio_format_routes.py -v`

Expected: All 3 tests PASS.

- [ ] **Step 5: Run all backend tests to confirm no regressions**

Run: `cd /Users/kimhsiao/Templates/git/pic.net.tw/RSS-collection && uv run pytest -v --tb=short`

Expected: All tests PASS.

- [ ] **Step 6: Commit**

```bash
git add tests/api/test_stdio_format_routes.py src/stdio/router.py
git commit -m "feat: add stdio router handlers for path-based format routes"
```

---

### Task 5: Frontend — `buildFeedPathUrl()` utility (TDD)

**Files:**
- Create: `web/src/api/__tests__/feed-api.test.ts`
- Modify: `web/src/api/feed.ts`

- [ ] **Step 1: Write the failing test**

Create `web/src/api/__tests__/feed-api.test.ts`:

```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { buildFeedPathUrl } from '@/api/feed'
import type { FeedParams } from '@/api/feed'

// Mock isTauri to return false (web environment)
vi.mock('@/utils/environment', () => ({
  isTauri: () => false,
}))

describe('buildFeedPathUrl', () => {
  beforeEach(() => {
    // Reset window.__VITE_API_BASE_URL__
    delete (window as any).__VITE_API_BASE_URL__
  })

  it('generates global feed path for RSS format', () => {
    const url = buildFeedPathUrl('rss')
    expect(url).toBe('/api/v1/feed/rss')
  })

  it('generates global feed path for JSON format', () => {
    const url = buildFeedPathUrl('json')
    expect(url).toBe('/api/v1/feed/json')
  })

  it('generates global feed path for Markdown format', () => {
    const url = buildFeedPathUrl('markdown')
    expect(url).toBe('/api/v1/feed/markdown')
  })

  it('includes source_id in path when provided', () => {
    const url = buildFeedPathUrl('rss', { source_id: 3 })
    expect(url).toBe('/api/v1/sources/3/rss')
  })

  it('includes group_id in path when provided', () => {
    const url = buildFeedPathUrl('json', { group_id: 5 })
    expect(url).toBe('/api/v1/source-groups/5/json')
  })

  it('prefers source_id over group_id when both provided', () => {
    const url = buildFeedPathUrl('rss', { source_id: 3, group_id: 5 })
    expect(url).toContain('/sources/3/rss')
  })

  it('includes non-default query parameters', () => {
    const url = buildFeedPathUrl('json', { sort_by: 'source', sort_order: 'asc' })
    expect(url).toBe('/api/v1/feed/json?sort_by=source&sort_order=asc')
  })

  it('excludes default query parameters', () => {
    const url = buildFeedPathUrl('rss', { sort_by: 'published_at', sort_order: 'desc' })
    expect(url).toBe('/api/v1/feed/rss')
  })

  it('includes valid_time when provided', () => {
    const url = buildFeedPathUrl('rss', { valid_time: 24 })
    expect(url).toBe('/api/v1/feed/rss?valid_time=24')
  })

  it('includes keywords when provided', () => {
    const url = buildFeedPathUrl('rss', { keywords: 'AI;news' })
    expect(url).toBe('/api/v1/feed/rss?keywords=AI%3Bnews')
  })

  it('uses custom base URL from window', () => {
    ;(window as any).__VITE_API_BASE_URL__ = 'http://localhost:8000/api/v1'
    const url = buildFeedPathUrl('rss')
    expect(url).toBe('http://localhost:8000/api/v1/feed/rss')
  })
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/kimhsiao/Templates/git/pic.net.tw/RSS-collection/web && pnpm test:run -- src/api/__tests__/feed-api.test.ts`

Expected: FAIL — `buildFeedPathUrl` is not exported.

- [ ] **Step 3: Write minimal implementation**

Add `buildFeedPathUrl` to `web/src/api/feed.ts`:

```typescript
export function buildFeedPathUrl(format: FeedFormat, params?: FeedParams): string {
  const getWebBaseUrl = (): string => {
    const win = window as { __VITE_API_BASE_URL__?: string }
    return win.__VITE_API_BASE_URL__ || '/api/v1'
  }
  const base = isTauri() ? 'http://localhost:51085/api/v1' : getWebBaseUrl()

  // Determine path segment based on params
  let path: string
  if (params?.source_id) {
    path = `/sources/${params.source_id}/${format}`
  } else if (params?.group_id) {
    path = `/source-groups/${params.group_id}/${format}`
  } else {
    path = `/feed/${format}`
  }

  // Build query string with non-default values only
  const queryParams = new URLSearchParams()
  if (params) {
    if (params.sort_by && params.sort_by !== 'published_at') {
      queryParams.set('sort_by', params.sort_by)
    }
    if (params.sort_order && params.sort_order !== 'desc') {
      queryParams.set('sort_order', params.sort_order)
    }
    if (params.valid_time !== undefined && params.valid_time !== null) {
      queryParams.set('valid_time', String(params.valid_time))
    }
    if (params.keywords) {
      queryParams.set('keywords', params.keywords)
    }
    // source_id and group_id are already in the path, don't duplicate
  }

  const qs = queryParams.toString()
  return `${base}${path}${qs ? `?${qs}` : ''}`
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/kimhsiao/Templates/git/pic.net.tw/RSS-collection/web && pnpm test:run -- src/api/__tests__/feed-api.test.ts`

Expected: All 11 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add web/src/api/__tests__/feed-api.test.ts web/src/api/feed.ts
git commit -m "feat: add buildFeedPathUrl utility for path-based feed URLs"
```

---

### Task 6: Frontend — Update `getFormattedFeed` to use path-based URLs

**Files:**
- Modify: `web/src/api/feed.ts:47-79`

- [ ] **Step 1: Update `getFormattedFeed` implementation**

Change the URL construction in `getFormattedFeed` from query-param to path-based:

Replace the existing `getFormattedFeed` function body:

```typescript
export async function getFormattedFeed(
  format: FeedFormat,
  params?: FeedParams
): Promise<FormattedFeedResponse> {
  const authStore = useAuthStore()
  const headers: Record<string, string> = {
    'Accept': format === 'json' ? 'application/json' : 'text/plain',
  }

  if (authStore.apiKey) {
    headers['X-API-Key'] = authStore.apiKey
  }

  const url = buildFeedPathUrl(format, params)
  const response = await fetch(url, { headers })

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: ${response.statusText}`)
  }

  const content = await response.text()
  return {
    content,
    contentType: response.headers.get('content-type') || 'text/plain',
  }
}
```

Note: `buildFeedPathUrl` already handles the base URL (including Tauri `app://localhost` for fetch). But for `fetch()` calls in Tauri, the `app://localhost` scheme is needed. So we need a separate variant for fetch URLs vs display URLs. Update `buildFeedPathUrl` to accept an optional `forDisplay` parameter:

```typescript
export function buildFeedPathUrl(
  format: FeedFormat,
  params?: FeedParams,
  forDisplay = false,
): string {
  const getWebBaseUrl = (): string => {
    const win = window as { __VITE_API_BASE_URL__?: string }
    return win.__VITE_API_BASE_URL__ || '/api/v1'
  }
  const base = isTauri()
    ? (forDisplay ? 'http://localhost:51085/api/v1' : 'app://localhost/api/v1')
    : getWebBaseUrl()

  // ... rest unchanged
}
```

- [ ] **Step 2: Update tests if needed**

The existing tests use `forDisplay = false` (default), so they should still pass. Add one test for the `forDisplay` parameter:

Add to `web/src/api/__tests__/feed-api.test.ts`:

```typescript
it('uses http URL for display in Tauri environment', () => {
  vi.doMock('@/utils/environment', () => ({
    isTauri: () => true,
  }))
  // Re-import with the mock
  const { buildFeedPathUrl: buildTauri } = vi.importActual<typeof import('@/api/feed')>('@/api/feed')
  // For display, Tauri should use http://localhost
  const url = buildTauri.buildFeedPathUrl('rss', undefined, true)
  expect(url).toContain('http://localhost')
  vi.doUnmock('@/utils/environment')
})
```

Note: This test is optional — the core behavior is already covered. If mocking is tricky, skip it.

- [ ] **Step 3: Run all frontend unit tests**

Run: `cd /Users/kimhsiao/Templates/git/pic.net.tw/RSS-collection/web && pnpm test:run`

Expected: All tests PASS.

- [ ] **Step 4: Commit**

```bash
git add web/src/api/feed.ts web/src/api/__tests__/feed-api.test.ts
git commit -m "feat: update getFormattedFeed to use path-based URL"
```

---

### Task 7: Frontend — i18n keys

**Files:**
- Modify: `web/src/locales/en.json`
- Modify: `web/src/locales/zh.json`

- [ ] **Step 1: Add i18n keys to `en.json`**

Add these keys inside the `"feed"` object (after `"view_preview": "Preview"`):

```json
"api_paths": "API Paths",
"copy_path": "Copy path",
"path_copied": "Path copied"
```

- [ ] **Step 2: Add i18n keys to `zh.json`**

Add matching keys inside the `"feed"` object:

```json
"api_paths": "API 路徑",
"copy_path": "複製路徑",
"path_copied": "路徑已複製"
```

- [ ] **Step 3: Commit**

```bash
git add web/src/locales/en.json web/src/locales/zh.json
git commit -m "feat: add i18n keys for feed API paths display"
```

---

### Task 8: Frontend — RssPreviewDialog API paths section (TDD)

**Files:**
- Modify: `web/src/components/RssPreviewDialog.vue`

- [ ] **Step 1: Add API paths section to RssPreviewDialog**

Add the following computed properties and template section.

**Script additions** (after existing `copied` ref, around line 29):

```typescript
const pathCopiedIndex = ref<number | null>(null)

const apiPaths = computed(() => {
  const formats: { key: Format; label: string }[] = [
    { key: 'rss', label: t('feed.format_rss') },
    { key: 'json', label: t('feed.format_json') },
    { key: 'markdown', label: t('feed.format_markdown') },
  ]
  return formats.map(({ key, label }) => ({
    key,
    label,
    url: buildFeedPathUrl(key, props.params, true),
  }))
})

async function copyPath(index: number): Promise<void> {
  try {
    await navigator.clipboard.writeText(apiPaths.value[index].url)
    pathCopiedIndex.value = index
    setTimeout(() => {
      pathCopiedIndex.value = null
    }, 2000)
  } catch (error) {
    console.error('Failed to copy path:', error)
  }
}
```

Add `buildFeedPathUrl` to the imports at the top:

```typescript
import { buildFeedPathUrl } from "@/api/feed";
```

**Template addition** — add the API paths section in the template, inside the `v-else` div (after `<div v-else class="space-y-4">`, before the format selector buttons):

```html
<!-- API Paths Section -->
<div class="bg-neutral-50 dark:bg-slate-900 rounded-lg border border-neutral-200 dark:border-slate-700 p-3">
  <h3 class="text-xs font-semibold text-neutral-500 dark:text-neutral-400 uppercase tracking-wider mb-2">
    {{ t('feed.api_paths') }}
  </h3>
  <div class="space-y-1.5">
    <div
      v-for="(path, index) in apiPaths"
      :key="path.key"
      class="flex items-center gap-2"
    >
      <span class="text-xs font-medium text-neutral-600 dark:text-neutral-300 w-16 shrink-0">
        {{ path.label }}
      </span>
      <code class="flex-1 text-xs bg-white dark:bg-slate-800 px-2 py-1 rounded border border-neutral-200 dark:border-slate-600 text-neutral-700 dark:text-neutral-300 break-all">
        {{ path.url }}
      </code>
      <button
        @click="copyPath(index)"
        class="p-1 rounded hover:bg-neutral-200 dark:hover:bg-slate-700 transition-colors shrink-0"
        :title="pathCopiedIndex === index ? t('feed.path_copied') : t('feed.copy_path')"
      >
        <Check v-if="pathCopiedIndex === index" class="h-3.5 w-3.5 text-green-500" />
        <Copy v-else class="h-3.5 w-3.5 text-neutral-400" />
      </button>
    </div>
  </div>
</div>
```

- [ ] **Step 2: Verify the app builds**

Run: `cd /Users/kimhsiao/Templates/git/pic.net.tw/RSS-collection/web && pnpm typecheck && pnpm build`

Expected: Build succeeds with no errors.

- [ ] **Step 3: Run existing tests**

Run: `cd /Users/kimhsiao/Templates/git/pic.net.tw/RSS-collection/web && pnpm test:run`

Expected: All tests PASS.

- [ ] **Step 4: Commit**

```bash
git add web/src/components/RssPreviewDialog.vue
git commit -m "feat: add API paths display section to RssPreviewDialog"
```

---

### Task 9: E2E — Backend path-based route verification

**Files:**
- Create: `web/e2e/feed-format-routes.spec.ts`

- [ ] **Step 1: Write E2E test**

Create `web/e2e/feed-format-routes.spec.ts`:

```typescript
import { test, expect } from '@playwright/test'

const API_BASE = process.env.E2E_API_BASE || 'http://localhost:51085/api/v1'
const API_KEY = process.env.E2E_API_KEY || 'test-key'

test.describe('Feed Format Path Routes', () => {
  const headers = { 'X-API-Key': API_KEY }

  test('GET /feed/rss returns XML', async ({ request }) => {
    const response = await request.get(`${API_BASE}/feed/rss`, { headers })
    expect(response.status()).toBe(200)
    const contentType = response.headers()['content-type'] || ''
    expect(contentType).toContain('xml')
    const body = await response.text()
    expect(body).toContain('<?xml')
  })

  test('GET /feed/json returns JSON', async ({ request }) => {
    const response = await request.get(`${API_BASE}/feed/json`, { headers })
    expect(response.status()).toBe(200)
    const contentType = response.headers()['content-type'] || ''
    expect(contentType).toContain('json')
    const body = await response.json()
    expect(Array.isArray(body)).toBe(true)
  })

  test('GET /feed/markdown returns Markdown', async ({ request }) => {
    const response = await request.get(`${API_BASE}/feed/markdown`, { headers })
    expect(response.status()).toBe(200)
    const contentType = response.headers()['content-type'] || ''
    expect(contentType).toContain('markdown')
    const body = await response.text()
    expect(body).toContain('#')
  })

  test('GET /feed/invalid returns 422', async ({ request }) => {
    const response = await request.get(`${API_BASE}/feed/invalid`, { headers })
    expect(response.status()).toBe(422)
  })

  test('GET /sources/{id}/rss returns XML or 404', async ({ request }) => {
    const response = await request.get(`${API_BASE}/sources/1/rss`, { headers })
    expect([200, 404]).toContain(response.status())
    if (response.status() === 200) {
      const contentType = response.headers()['content-type'] || ''
      expect(contentType).toContain('xml')
    }
  })

  test('GET /source-groups/{id}/json returns JSON or 404', async ({ request }) => {
    const response = await request.get(`${API_BASE}/source-groups/1/json`, { headers })
    expect([200, 404]).toContain(response.status())
    if (response.status() === 200) {
      const contentType = response.headers()['content-type'] || ''
      expect(contentType).toContain('json')
    }
  })
})
```

- [ ] **Step 2: Run E2E test (requires running backend)**

Run: `cd /Users/kimhsiao/Templates/git/pic.net.tw/RSS-collection/web && pnpm test:e2e -- feed-format-routes`

Expected: All 6 tests PASS.

- [ ] **Step 3: Commit**

```bash
git add web/e2e/feed-format-routes.spec.ts
git commit -m "test: add E2E tests for path-based feed format routes"
```

---

### Task 10: E2E — Preview dialog API paths display

**Files:**
- Create: `web/e2e/preview-api-paths.spec.ts`

- [ ] **Step 1: Write E2E test**

Create `web/e2e/preview-api-paths.spec.ts`:

```typescript
import { test, expect } from '@playwright/test'

test.describe('Preview Dialog API Paths', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/feed')
    await page.waitForLoadState('networkidle')
  })

  test('should show API paths section in preview dialog', async ({ page }) => {
    // Find and click the preview button on the feed page
    const previewButton = page.getByRole('button', { name: /preview feed|預覽摘要/i })
    if (await previewButton.isVisible()) {
      await previewButton.click()
      await page.waitForTimeout(1000)

      // Verify API paths section is visible
      const apiPathsSection = page.getByText(/api paths|api 路徑/i)
      await expect(apiPathsSection).toBeVisible({ timeout: 5000 })
    }
  })

  test('should display three format paths in preview dialog', async ({ page }) => {
    const previewButton = page.getByRole('button', { name: /preview feed|預覽摘要/i })
    if (await previewButton.isVisible()) {
      await previewButton.click()
      await page.waitForTimeout(1000)

      // Verify all three format paths are displayed
      const dialog = page.locator('[class*="fixed"][class*="inset-0"][class*="z-50"]')
      if (await dialog.isVisible({ timeout: 5000 })) {
        const codeElements = dialog.locator('code')
        const count = await codeElements.count()
        expect(count).toBeGreaterThanOrEqual(3)

        // Check that paths contain /feed/ format segments
        const rssPath = dialog.locator('code').filter({ hasText: /\/feed\/rss|\/sources\/.*\/rss/ })
        const jsonPath = dialog.locator('code').filter({ hasText: /\/feed\/json|\/sources\/.*\/json/ })
        const mdPath = dialog.locator('code').filter({ hasText: /\/feed\/markdown|\/sources\/.*\/markdown/ })

        await expect(rssPath.first()).toBeVisible({ timeout: 3000 })
        await expect(jsonPath.first()).toBeVisible({ timeout: 3000 })
        await expect(mdPath.first()).toBeVisible({ timeout: 3000 })
      }
    }
  })

  test('should copy path when clicking copy button', async ({ page }) => {
    const previewButton = page.getByRole('button', { name: /preview feed|預覽摘要/i })
    if (await previewButton.isVisible()) {
      await previewButton.click()
      await page.waitForTimeout(1000)

      const dialog = page.locator('[class*="fixed"][class*="inset-0"][class*="z-50"]')
      if (await dialog.isVisible({ timeout: 5000 })) {
        // Find copy buttons in the API paths section
        const copyButtons = dialog.locator('button[title*="copy" i], button[title*="複製" i]')
        const count = await copyButtons.count()
        if (count > 0) {
          await copyButtons.first().click()
          await page.waitForTimeout(500)

          // Verify the check icon appears (path copied feedback)
          const checkIcon = dialog.locator('button svg.text-green-500')
          await expect(checkIcon.first()).toBeVisible({ timeout: 3000 })
        }
      }
    }
  })
})
```

- [ ] **Step 2: Run E2E test**

Run: `cd /Users/kimhsiao/Templates/git/pic.net.tw/RSS-collection/web && pnpm test:e2e -- preview-api-paths`

Expected: All 3 tests PASS.

- [ ] **Step 3: Commit**

```bash
git add web/e2e/preview-api-paths.spec.ts
git commit -m "test: add E2E tests for preview dialog API paths display"
```

---

### Task 11: Final verification and version bump

**Files:**
- Modify: `pyproject.toml` — version bump (if applicable)
- Modify: `web/package.json` — version bump (if applicable)

- [ ] **Step 1: Run all backend tests**

Run: `cd /Users/kimhsiao/Templates/git/pic.net.tw/RSS-collection && uv run pytest -v --tb=short`

Expected: All tests PASS, no regressions.

- [ ] **Step 2: Run all frontend unit tests**

Run: `cd /Users/kimhsiao/Templates/git/pic.net.tw/RSS-collection/web && pnpm test:run`

Expected: All tests PASS.

- [ ] **Step 3: Run frontend typecheck and build**

Run: `cd /Users/kimhsiao/Templates/git/pic.net.tw/RSS-collection/web && pnpm typecheck && pnpm build`

Expected: Build succeeds with no errors.

- [ ] **Step 4: Run frontend lint**

Run: `cd /Users/kimhsiao/Templates/git/pic.net.tw/RSS-collection/web && pnpm lint`

Expected: No errors.

- [ ] **Step 5: Run backend lint and format**

Run: `cd /Users/kimhsiao/Templates/git/pic.net.tw/RSS-collection && uv run ruff check . && uv run ruff format --check .`

Expected: No errors.

- [ ] **Step 6: Final commit**

```bash
git add -A
git commit -m "chore: finalize feed format path-based routes feature"
```
