"""Tests for preview API routes."""

import hashlib
from collections.abc import AsyncGenerator
from typing import AsyncGenerator as AsyncGen
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.api.deps import get_session
from src.main import app
from src.models import Base, PreviewContent


def compute_url_hash(url: str) -> str:
    return hashlib.sha256(url.encode()).hexdigest()


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

    app.dependency_overrides[get_session] = override_get_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()


class TestGetPreviewByUrlHash:
    @pytest.mark.asyncio
    async def test_returns_404_when_not_found(self, async_client: AsyncClient) -> None:
        url_hash = "a" * 64
        response = await async_client.get(f"/api/v1/previews/{url_hash}")

        assert response.status_code == 404
        assert response.json()["detail"] == "Preview not found"

    @pytest.mark.asyncio
    async def test_returns_preview_when_found(
        self, async_client: AsyncClient, test_session: AsyncSession
    ) -> None:
        url = "https://example.com/article"
        url_hash = compute_url_hash(url)

        preview = PreviewContent(
            url=url,
            url_hash=url_hash,
            markdown_content="# Test Article",
            title="Test Article",
        )
        test_session.add(preview)
        await test_session.commit()

        response = await async_client.get(f"/api/v1/previews/{url_hash}")

        assert response.status_code == 200
        data = response.json()
        assert data["url"] == url
        assert data["url_hash"] == url_hash
        assert data["markdown_content"] == "# Test Article"
        assert data["title"] == "Test Article"


class TestFetchAndCachePreview:
    @pytest.mark.asyncio
    async def test_fetches_and_caches_content(
        self, async_client: AsyncClient
    ) -> None:
        mock_response = AsyncMock()
        mock_response.json = lambda: {
            "success": True,
            "url": "https://example.com/fetched",
            "title": "Fetched Article",
            "content": "# Fetched Article\n\nContent from markdown.new.",
            "timestamp": "2024-01-01T00:00:00Z",
            "method": "Cloudflare Workers AI",
            "duration_ms": 100,
            "tokens": 50,
        }
        mock_response.raise_for_status = lambda: None

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            response = await async_client.post(
                "/api/v1/previews/fetch",
                json={"url": "https://example.com/fetched"},
            )

            assert response.status_code == 201
            data = response.json()
            assert data["url"] == "https://example.com/fetched"
            assert data["markdown_content"] == "# Fetched Article\n\nContent from markdown.new."
            assert data["title"] == "Fetched Article"
            assert "id" in data

    @pytest.mark.asyncio
    async def test_requires_url(self, async_client: AsyncClient) -> None:
        response = await async_client.post("/api/v1/previews/fetch", json={})

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_returns_cached_content_without_fetching(
        self, async_client: AsyncClient, test_session: AsyncSession
    ) -> None:
        url = "https://example.com/cached"
        existing = PreviewContent(
            url=url,
            url_hash=compute_url_hash(url),
            markdown_content="# Cached Content",
            title="Cached Title",
        )
        test_session.add(existing)
        await test_session.commit()

        mock_response = AsyncMock()
        mock_response.json = lambda: {
            "success": True,
            "url": url,
            "title": "Should Not Be Used",
            "content": "# Should Not Be Used",
            "timestamp": "2024-01-01T00:00:00Z",
            "method": "Cloudflare Workers AI",
            "duration_ms": 100,
            "tokens": 50,
        }
        mock_response.raise_for_status = lambda: None

        with patch("httpx.AsyncClient") as mock_client:
            mock_post = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value.post = mock_post

            response = await async_client.post(
                "/api/v1/previews/fetch",
                json={"url": url},
            )

            assert response.status_code == 201
            data = response.json()
            assert data["markdown_content"] == "# Cached Content"
            assert data["title"] == "Cached Title"
            mock_post.assert_not_called()


class TestCreatePreview:
    @pytest.mark.asyncio
    async def test_creates_new_preview(self, async_client: AsyncClient) -> None:
        url = "https://example.com/new-article"
        markdown_content = "# New Article\n\nThis is the content."
        title = "New Article"

        response = await async_client.post(
            "/api/v1/previews",
            json={
                "url": url,
                "markdown_content": markdown_content,
                "title": title,
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["url"] == url
        assert data["markdown_content"] == markdown_content
        assert data["title"] == title
        assert data["url_hash"] == compute_url_hash(url)
        assert "id" in data

    @pytest.mark.asyncio
    async def test_updates_existing_preview(self, async_client: AsyncClient) -> None:
        url = "https://example.com/update-article"

        first_response = await async_client.post(
            "/api/v1/previews",
            json={
                "url": url,
                "markdown_content": "# Original",
                "title": "Original",
            },
        )
        assert first_response.status_code == 201
        first_id = first_response.json()["id"]

        second_response = await async_client.post(
            "/api/v1/previews",
            json={
                "url": url,
                "markdown_content": "# Updated",
                "title": "Updated",
            },
        )

        assert second_response.status_code == 201
        data = second_response.json()
        assert data["id"] == first_id
        assert data["markdown_content"] == "# Updated"
        assert data["title"] == "Updated"

    @pytest.mark.asyncio
    async def test_requires_url(self, async_client: AsyncClient) -> None:
        response = await async_client.post(
            "/api/v1/previews",
            json={
                "markdown_content": "# Content",
                "title": "Title",
            },
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_requires_markdown_content(self, async_client: AsyncClient) -> None:
        response = await async_client.post(
            "/api/v1/previews",
            json={
                "url": "https://example.com/article",
                "title": "Title",
            },
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_title_is_optional(self, async_client: AsyncClient) -> None:
        response = await async_client.post(
            "/api/v1/previews",
            json={
                "url": "https://example.com/no-title",
                "markdown_content": "# No Title Article",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["title"] is None


class TestGetPreviewByUrl:
    @pytest.mark.asyncio
    async def test_returns_preview_by_url(
        self, async_client: AsyncClient, test_session: AsyncSession
    ) -> None:
        url = "https://example.com/query-article"

        preview = PreviewContent(
            url=url,
            url_hash=compute_url_hash(url),
            markdown_content="# Query Article",
            title="Query Article",
        )
        test_session.add(preview)
        await test_session.commit()

        response = await async_client.get("/api/v1/previews", params={"url": url})

        assert response.status_code == 200
        data = response.json()
        assert data["url"] == url
        assert data["markdown_content"] == "# Query Article"

    @pytest.mark.asyncio
    async def test_returns_404_for_unknown_url(self, async_client: AsyncClient) -> None:
        response = await async_client.get(
            "/api/v1/previews", params={"url": "https://unknown.com/article"}
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "Preview not found"