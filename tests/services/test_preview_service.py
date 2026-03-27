"""Tests for PreviewService."""

import hashlib
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import PreviewContent
from src.services.preview_service import PreviewService


def compute_url_hash(url: str) -> str:
    return hashlib.sha256(url.encode()).hexdigest()


@pytest_asyncio.fixture
async def preview_service(db_session: AsyncSession) -> PreviewService:
    return PreviewService(db_session)


class TestGetByUrlHash:
    @pytest.mark.asyncio
    async def test_returns_none_when_not_found(
        self, preview_service: PreviewService
    ) -> None:
        result = await preview_service.get_by_url_hash("nonexistent_hash")
        assert result is None

    @pytest.mark.asyncio
    async def test_returns_preview_when_found(
        self, preview_service: PreviewService, db_session: AsyncSession
    ) -> None:
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


class TestUpsert:
    @pytest.mark.asyncio
    async def test_creates_new_record(
        self, preview_service: PreviewService
    ) -> None:
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
        url = "https://example.com/article"

        first = await preview_service.upsert(url, "# Original", "Original")

        second = await preview_service.upsert(url, "# Updated", "Updated")

        assert second.id == first.id
        assert second.markdown_content == "# Updated"
        assert second.title == "Updated"

    @pytest.mark.asyncio
    async def test_url_hash_is_consistent(
        self, preview_service: PreviewService
    ) -> None:
        url = "https://example.com/article"

        result = await preview_service.upsert(url, "# Content")

        expected_hash = compute_url_hash(url)
        assert result.url_hash == expected_hash


class TestGetByUrl:
    @pytest.mark.asyncio
    async def test_returns_preview_by_url(
        self, preview_service: PreviewService
    ) -> None:
        url = "https://example.com/article"
        await preview_service.upsert(url, "# Test", "Test")

        result = await preview_service.get_by_url(url)
        assert result is not None
        assert result.url == url

    @pytest.mark.asyncio
    async def test_returns_none_for_unknown_url(
        self, preview_service: PreviewService
    ) -> None:
        result = await preview_service.get_by_url("https://unknown.com/article")
        assert result is None


class TestFetchMarkdownFromService:
    @pytest.mark.asyncio
    async def test_fetches_markdown_content(
        self, preview_service: PreviewService
    ) -> None:
        mock_response = AsyncMock()
        mock_response.json = lambda: {
            "success": True,
            "url": "https://example.com/article",
            "title": "Test Article",
            "content": "# Test Article\n\nContent here.",
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

            result = await preview_service.fetch_markdown_from_service(
                "https://example.com/article"
            )

            assert result.content == "# Test Article\n\nContent here."
            assert result.title == "Test Article"

    @pytest.mark.asyncio
    async def test_sends_correct_request_body(
        self, preview_service: PreviewService
    ) -> None:
        mock_response = AsyncMock()
        mock_response.json = lambda: {
            "success": True,
            "url": "https://example.com/test",
            "title": "Content",
            "content": "# Content",
            "timestamp": "2024-01-01T00:00:00Z",
            "method": "Cloudflare Workers AI",
            "duration_ms": 50,
            "tokens": 10,
        }
        mock_response.raise_for_status = lambda: None

        with patch("httpx.AsyncClient") as mock_client:
            mock_post = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value.post = mock_post

            await preview_service.fetch_markdown_from_service(
                "https://example.com/test"
            )

            call_args = mock_post.call_args
            assert call_args.args[0] == "https://markdown.new/"
            assert call_args.kwargs["json"] == {"url": "https://example.com/test", "retain_images": True}
            assert "headers" in call_args.kwargs

    @pytest.mark.asyncio
    async def test_raises_on_unsuccessful_response(
        self, preview_service: PreviewService
    ) -> None:
        mock_response = AsyncMock()
        mock_response.json = lambda: {
            "success": False,
            "url": "https://example.com/fail",
            "title": None,
            "content": "",
            "timestamp": "2024-01-01T00:00:00Z",
            "method": "error",
            "duration_ms": 0,
            "tokens": 0,
        }
        mock_response.raise_for_status = lambda: None

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            with pytest.raises(ValueError, match="markdown.new API error"):
                await preview_service.fetch_markdown_from_service(
                    "https://example.com/fail"
                )


class TestFetchAndCache:
    @pytest.mark.asyncio
    async def test_fetches_and_caches_content(
        self, preview_service: PreviewService
    ) -> None:
        mock_response = AsyncMock()
        mock_response.json = lambda: {
            "success": True,
            "url": "https://example.com/new-article",
            "title": "New Article",
            "content": "# New Article\n\nThis is the content.",
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

            result = await preview_service.fetch_and_cache(
                "https://example.com/new-article"
            )

            assert result.url == "https://example.com/new-article"
            assert result.markdown_content == "# New Article\n\nThis is the content."
            assert result.title == "New Article"
            assert result.id is not None

    @pytest.mark.asyncio
    async def test_returns_cached_content_without_fetching(
        self, preview_service: PreviewService
    ) -> None:
        url = "https://example.com/article"
        cached = await preview_service.upsert(url, "# Cached", "Cached")

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

            result = await preview_service.fetch_and_cache(url)

            assert result.markdown_content == "# Cached"
            assert result.title == "Cached"
            mock_post.assert_not_called()

    @pytest.mark.asyncio
    async def test_extracts_title_from_content_if_missing(
        self, preview_service: PreviewService
    ) -> None:
        mock_response = AsyncMock()
        mock_response.json = lambda: {
            "success": True,
            "url": "https://example.com/no-title",
            "title": None,
            "content": "# Extracted Title\n\nContent without API title.",
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

            result = await preview_service.fetch_and_cache(
                "https://example.com/no-title"
            )

            assert result.title == "Extracted Title"


class TestExtractTitle:
    def test_extracts_from_h1(self) -> None:
        markdown = "# My Article Title\n\nContent here."
        result = PreviewService._extract_title(markdown)
        assert result == "My Article Title"

    def test_extracts_from_frontmatter(self) -> None:
        markdown = "---\ntitle: Frontmatter Title\n---\n\n# H1 Title\n\nContent."
        result = PreviewService._extract_title(markdown)
        assert result == "Frontmatter Title"

    def test_returns_none_when_no_title(self) -> None:
        markdown = "Just some content without title."
        result = PreviewService._extract_title(markdown)
        assert result is None