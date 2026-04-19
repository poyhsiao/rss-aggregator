"""Tests for feed format API routes."""

from typing import AsyncGenerator as AsyncGen

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.api.deps import get_session, require_api_key
from src.main import app
from src.models import Base, Source, FeedItem
from src.services.auth_service import AuthService
from src.utils.time import now
from datetime import timedelta

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def test_engine():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False, future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def test_session(test_engine) -> AsyncGen[AsyncSession, None]:
    async_session_maker = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )
    async with async_session_maker() as session:
        yield session


@pytest_asyncio.fixture
async def async_client(test_session: AsyncSession) -> AsyncGen[AsyncClient, None]:
    async def override_get_session() -> AsyncGen[AsyncSession, None]:
        yield test_session

    async def override_require_api_key() -> str:
        return "test-api-key"

    app.dependency_overrides[get_session] = override_get_session
    app.dependency_overrides[require_api_key] = override_require_api_key

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def seed_data(test_session: AsyncSession):
    """Seed test data: source, group, and feed items."""
    from src.models import SourceGroup, SourceGroupMember
    source = Source(name="Tech News", url="https://tech.com/feed.xml")
    test_session.add(source)
    await test_session.flush()

    group = SourceGroup(name="Tech")
    test_session.add(group)
    await test_session.flush()

    # Add source to group
    from src.models import SourceGroupMember
    association = SourceGroupMember(source_id=source.id, group_id=group.id)
    test_session.add(association)

    current_time = now()
    items = [
        FeedItem(
            source_id=source.id,
            title="Python 3.13 Released",
            link="https://tech.com/python-3.13",
            description="New Python version",
            published_at=current_time - timedelta(hours=1),
        ),
        FeedItem(
            source_id=source.id,
            title="AI Breakthrough",
            link="https://tech.com/ai",
            description="AI news",
            published_at=current_time - timedelta(hours=2),
        ),
    ]
    test_session.add_all(items)
    await test_session.commit()
    return {"source": source, "group": group, "items": items}


class TestFeedFormatRoutes:
    @pytest.mark.asyncio
    async def test_feed_rss_format_returns_xml(
        self, async_client: AsyncClient, seed_data
    ) -> None:
        """GET /feed/rss returns RSS XML."""
        resp = await async_client.get("/api/v1/feed/rss")
        assert resp.status_code == 200
        assert "application/xml" in resp.headers["content-type"]
        assert "<?xml version=" in resp.text
        assert "<rss version=" in resp.text
        assert "Python 3.13 Released" in resp.text

    @pytest.mark.asyncio
    async def test_feed_json_format_returns_json(
        self, async_client: AsyncClient, seed_data
    ) -> None:
        """GET /feed/json returns JSON."""
        resp = await async_client.get("/api/v1/feed/json")
        assert resp.status_code == 200
        assert "application/json" in resp.headers["content-type"]
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == 2
        assert data[0]["title"] == "Python 3.13 Released"

    @pytest.mark.asyncio
    async def test_feed_markdown_format_returns_markdown(
        self, async_client: AsyncClient, seed_data
    ) -> None:
        """GET /feed/markdown returns Markdown."""
        resp = await async_client.get("/api/v1/feed/markdown")
        assert resp.status_code == 200
        assert "text/markdown" in resp.headers["content-type"]
        assert "# Python 3.13 Released" in resp.text
        assert "https://tech.com/python-3.13" in resp.text

    @pytest.mark.asyncio
    async def test_feed_invalid_format_returns_422(
        self, async_client: AsyncClient
    ) -> None:
        """GET /feed/invalid returns 422."""
        resp = await async_client.get("/api/v1/feed/invalid")
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_feed_format_with_query_params(
        self, async_client: AsyncClient, seed_data
    ) -> None:
        """GET /feed/json?sort_by=source passes query params."""
        resp = await async_client.get(
            "/api/v1/feed/json",
            params={"sort_by": "source", "sort_order": "asc"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_feed_format_requires_auth(
        self, test_session: AsyncSession, monkeypatch
    ) -> None:
        """Without API key returns 401."""
        # Force REQUIRE_API_KEY to True for this test
        from src.config import get_settings
        import os
        os.environ["REQUIRE_API_KEY"] = "true"

        # Force settings reload
        get_settings.cache_clear()

        # Create a new client without auth override
        async def override_get_session() -> AsyncGen[AsyncSession, None]:
            yield test_session

        app.dependency_overrides[get_session] = override_get_session
        # Do NOT override require_api_key

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/v1/feed/rss")
            assert resp.status_code == 401

        app.dependency_overrides.clear()

        # Cleanup
        os.environ.pop("REQUIRE_API_KEY", None)
        get_settings.cache_clear()


class TestSourceFeedFormatRoutes:
    """Tests for /sources/{source_id}/{format} endpoints."""

    @pytest.mark.asyncio
    async def test_source_feed_rss_format_returns_xml(
        self, async_client: AsyncClient, seed_data
    ) -> None:
        """GET /sources/{id}/rss returns RSS XML."""
        source_id = seed_data["source"].id
        resp = await async_client.get(f"/api/v1/sources/{source_id}/rss")
        assert resp.status_code == 200
        assert "application/xml" in resp.headers["content-type"]
        assert "<?xml version=" in resp.text
        assert "<rss version=" in resp.text
        assert "Python 3.13 Released" in resp.text

    @pytest.mark.asyncio
    async def test_source_feed_json_format_returns_json(
        self, async_client: AsyncClient, seed_data
    ) -> None:
        """GET /sources/{id}/json returns JSON."""
        source_id = seed_data["source"].id
        resp = await async_client.get(f"/api/v1/sources/{source_id}/json")
        assert resp.status_code == 200
        assert "application/json" in resp.headers["content-type"]
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == 2
        assert data[0]["title"] == "Python 3.13 Released"

    @pytest.mark.asyncio
    async def test_source_feed_markdown_format_returns_markdown(
        self, async_client: AsyncClient, seed_data
    ) -> None:
        """GET /sources/{id}/markdown returns Markdown."""
        source_id = seed_data["source"].id
        resp = await async_client.get(f"/api/v1/sources/{source_id}/markdown")
        assert resp.status_code == 200
        assert "text/markdown" in resp.headers["content-type"]
        assert "# Python 3.13 Released" in resp.text
        assert "https://tech.com/python-3.13" in resp.text

    @pytest.mark.asyncio
    async def test_source_feed_invalid_format_returns_422(
        self, async_client: AsyncClient, seed_data
    ) -> None:
        """GET /sources/{id}/invalid returns 422."""
        source_id = seed_data["source"].id
        resp = await async_client.get(f"/api/v1/sources/{source_id}/invalid")
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_source_feed_invalid_source_returns_404(
        self, async_client: AsyncClient
    ) -> None:
        """GET /sources/99999/rss returns 404 for non-existent source."""
        resp = await async_client.get("/api/v1/sources/99999/rss")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_source_feed_format_with_query_params(
        self, async_client: AsyncClient, seed_data
    ) -> None:
        """GET /sources/{id}/json?sort_by=source passes query params."""
        source_id = seed_data["source"].id
        resp = await async_client.get(
            f"/api/v1/sources/{source_id}/json",
            params={"sort_by": "source", "sort_order": "asc"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)


class TestGroupFeedFormatRoutes:
    """Tests for /groups/{group_id}/{format} endpoints."""

    @pytest.mark.asyncio
    async def test_group_feed_rss_format_returns_xml(
        self, async_client: AsyncClient, seed_data
    ) -> None:
        """GET /groups/{id}/rss returns RSS XML."""
        group_id = seed_data["group"].id
        resp = await async_client.get(f"/api/v1/groups/{group_id}/rss")
        assert resp.status_code == 200
        assert "application/xml" in resp.headers["content-type"]
        assert "<?xml version=" in resp.text
        assert "<rss version=" in resp.text

    @pytest.mark.asyncio
    async def test_group_feed_json_format_returns_json(
        self, async_client: AsyncClient, seed_data
    ) -> None:
        """GET /groups/{id}/json returns JSON."""
        group_id = seed_data["group"].id
        resp = await async_client.get(f"/api/v1/groups/{group_id}/json")
        assert resp.status_code == 200
        assert "application/json" in resp.headers["content-type"]
        data = resp.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_group_feed_markdown_format_returns_markdown(
        self, async_client: AsyncClient, seed_data
    ) -> None:
        """GET /groups/{id}/markdown returns Markdown."""
        group_id = seed_data["group"].id
        resp = await async_client.get(f"/api/v1/groups/{group_id}/markdown")
        assert resp.status_code == 200
        assert "text/markdown" in resp.headers["content-type"]

    @pytest.mark.asyncio
    async def test_group_feed_invalid_format_returns_422(
        self, async_client: AsyncClient, seed_data
    ) -> None:
        """GET /groups/{id}/invalid returns 422."""
        group_id = seed_data["group"].id
        resp = await async_client.get(f"/api/v1/groups/{group_id}/invalid")
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_group_feed_invalid_group_returns_404(
        self, async_client: AsyncClient
    ) -> None:
        """GET /groups/99999/rss returns 404 for non-existent group."""
        resp = await async_client.get("/api/v1/groups/99999/rss")
        assert resp.status_code == 404
