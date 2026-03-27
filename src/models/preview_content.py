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