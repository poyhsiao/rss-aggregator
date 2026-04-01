"""RSS Source model."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from src.models.feed_item import FeedItem
    from src.models.source_group import SourceGroup


class Source(Base, TimestampMixin):
    """RSS feed source configuration."""

    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, init=False)
    name: Mapped[str] = mapped_column(String(255))
    url: Mapped[str] = mapped_column(String(2048), index=True)
    is_active: Mapped[bool] = mapped_column(default=True)
    last_fetched_at: Mapped[datetime | None] = mapped_column(default=None)
    last_error: Mapped[str | None] = mapped_column(Text, default=None)

    __table_args__ = (
        # Uniqueness enforced via partial indexes: uq_sources_url_active, uq_sources_name_active
    )

    feed_items: Mapped[list[FeedItem]] = relationship(
        "FeedItem", back_populates="source", cascade="all, delete-orphan", init=False
    )

    groups: Mapped[list[SourceGroup]] = relationship(
        "SourceGroup",
        secondary="source_group_members",
        back_populates="sources",
        init=False,
    )

    def __repr__(self) -> str:
        return f"<Source(id={self.id}, name={self.name}, url={self.url})>"