"""Service for managing cached preview content."""

import hashlib
import logging
from dataclasses import dataclass

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from src.models import PreviewContent

logger = logging.getLogger(__name__)

MARKDOWN_NEW_URL = "https://markdown.new/"
MARKDOWN_NEW_TIMEOUT = 30.0


@dataclass
class MarkdownResult:
    content: str
    title: str | None


class PreviewService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @staticmethod
    def compute_url_hash(url: str) -> str:
        return hashlib.sha256(url.encode()).hexdigest()

    async def get_by_url_hash(self, url_hash: str) -> PreviewContent | None:
        result = await self._session.execute(
            select(PreviewContent).where(
                PreviewContent.url_hash == url_hash,
                PreviewContent.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def get_by_url(self, url: str) -> PreviewContent | None:
        result = await self._session.execute(
            select(PreviewContent).where(
                PreviewContent.url == url,
                PreviewContent.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def fetch_markdown_from_service(self, url: str) -> MarkdownResult:
        """Fetch markdown content from markdown.new service.

        The API returns JSON with:
        - success: bool
        - url: str
        - title: str
        - content: str (markdown content)
        - timestamp: str
        - method: str
        - duration_ms: int
        - tokens: int
        """
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "RSS-Aggregator/1.0",
            "Accept": "application/json",
        }
        try:
            async with httpx.AsyncClient(
                timeout=MARKDOWN_NEW_TIMEOUT,
                follow_redirects=True,
            ) as client:
                logger.info(f"Fetching markdown from {MARKDOWN_NEW_URL} for URL: {url}")
                response = await client.post(
                    MARKDOWN_NEW_URL,
                    json={"url": url, "retain_images": True},
                    headers=headers,
                )
                logger.info(f"Response status: {response.status_code}")
                response.raise_for_status()
                data = response.json()

                if not data.get("success", False):
                    error_msg = data.get("error", "Unknown error")
                    logger.error(f"markdown.new API returned success=false for {url}: {error_msg}")
                    raise ValueError(f"markdown.new API error: {error_msg}")

                return MarkdownResult(
                    content=data.get("content", ""),
                    title=data.get("title"),
                )
        except httpx.TimeoutException as e:
            logger.error(f"Timeout fetching markdown for {url}: {e}")
            raise ValueError(f"Preview service timeout: {e}") from e
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching markdown for {url}: {e}")
            raise ValueError(f"Preview service HTTP error: {e.response.status_code}") from e
        except httpx.RequestError as e:
            logger.error(f"Network error fetching markdown for {url}: {e}")
            raise ValueError(f"Preview service network error: {e}") from e

    async def fetch_and_cache(self, url: str) -> PreviewContent:
        """Fetch markdown from service and cache it."""
        result = await self.fetch_markdown_from_service(url)
        title = result.title or self._extract_title(result.content)
        return await self.upsert(url, result.content, title)

    @staticmethod
    def _extract_title(markdown: str) -> str | None:
        """Extract title from markdown content."""
        import re

        frontmatter_match = re.match(
            r"^---\n.*?title:\s*[\"']?(.+?)[\"']?\n.*?---", markdown, re.DOTALL
        )
        if frontmatter_match:
            return frontmatter_match.group(1).strip()

        h1_match = re.match(r"^#\s+(.+)$", markdown, re.MULTILINE)
        if h1_match:
            return h1_match.group(1).strip()

        return None

    async def upsert(
        self,
        url: str,
        markdown_content: str,
        title: str | None = None,
    ) -> PreviewContent:
        url_hash = self.compute_url_hash(url)

        existing = await self.get_by_url_hash(url_hash)
        if existing:
            existing.markdown_content = markdown_content
            existing.title = title
            await self._session.commit()
            await self._session.refresh(existing)
            return existing

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
            await self._session.rollback()
            logger.warning(f"Race condition detected for URL: {url}")
            result = await self.get_by_url_hash(url_hash)
            if result is None:
                raise
            return result