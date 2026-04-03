"""Preview content model for cached article previews."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base
from src.utils.time import now

if TYPE_CHECKING:
    pass


class PreviewContent(Base):
    """Cached markdown preview content for URLs."""

    __tablename__ = "preview_contents"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, init=False)
    url: Mapped[str] = mapped_column(String(2048), unique=True, index=True)
    url_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    markdown_content: Mapped[str] = mapped_column(Text)
    title: Mapped[str | None] = mapped_column(String(500), default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime, default_factory=now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default_factory=now, nullable=False, onupdate=func.now())

    def __repr__(self) -> str:
        return f"<PreviewContent(id={self.id}, url={self.url[:50]}...)>"