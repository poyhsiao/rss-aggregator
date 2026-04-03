"""FeedItem model for cached RSS items."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base
from src.utils.time import now

if TYPE_CHECKING:
    from src.models.source import Source
    from src.models.fetch_batch import FetchBatch


class FeedItem(Base):
    """Cached RSS feed item."""

    __tablename__ = "feed_items"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, init=False)
    source_id: Mapped[int] = mapped_column(Integer, ForeignKey("sources.id"))
    title: Mapped[str] = mapped_column(String(500))
    link: Mapped[str] = mapped_column(String(2048))
    batch_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("fetch_batches.id"), default=None)
    description: Mapped[str | None] = mapped_column(Text, default=None)
    published_at: Mapped[datetime | None] = mapped_column(DateTime, default=None)
    fetched_at: Mapped[datetime | None] = mapped_column(DateTime, default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime, default_factory=now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default_factory=now, nullable=False, onupdate=func.now())
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, default=None)

    def soft_delete(self) -> None:
        self.deleted_at = now()

    source: Mapped[Source] = relationship("Source", back_populates="feed_items", init=False)
    batch: Mapped[FetchBatch | None] = relationship("FetchBatch", back_populates="feed_items", init=False)

    def __repr__(self) -> str:
        return f"<FeedItem(id={self.id}, title={self.title[:30]}...)>"