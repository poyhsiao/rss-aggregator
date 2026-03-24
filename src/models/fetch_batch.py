from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from src.models.feed_item import FeedItem


class FetchBatch(Base, TimestampMixin):
    __tablename__ = "fetch_batches"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, init=False)
    items_count: Mapped[int] = mapped_column(Integer, default=0)
    sources: Mapped[str] = mapped_column(Text, default="")
    notes: Mapped[str | None] = mapped_column(String(500), default=None)

    feed_items: Mapped[list[FeedItem]] = relationship(
        "FeedItem", back_populates="batch", cascade="all, delete-orphan", init=False
    )

    def __repr__(self) -> str:
        return f"<FetchBatch(id={self.id}, items_count={self.items_count})>"