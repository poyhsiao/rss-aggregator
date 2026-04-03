"""Fetch batch model for tracking fetch operations."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base
from src.utils.time import now

if TYPE_CHECKING:
    from src.models.feed_item import FeedItem


class FetchBatch(Base):
    __tablename__ = "fetch_batches"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, init=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default_factory=now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default_factory=now, nullable=False, onupdate=func.now())
    items_count: Mapped[int] = mapped_column(Integer, default=0)
    sources: Mapped[str] = mapped_column(Text, default="")
    groups: Mapped[str] = mapped_column(Text, default="")
    notes: Mapped[str | None] = mapped_column(String(500), default=None)

    feed_items: Mapped[list[FeedItem]] = relationship(
        "FeedItem", back_populates="batch", cascade="all, delete-orphan", init=False
    )

    def __repr__(self) -> str:
        return f"<FetchBatch(id={self.id}, items_count={self.items_count})>"
