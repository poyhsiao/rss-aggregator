"""RSS Source model."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base
from src.utils.time import now

if TYPE_CHECKING:
    from src.models.feed_item import FeedItem
    from src.models.source_group import SourceGroup


class Source(Base):
    """RSS feed source configuration."""

    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, init=False)
    name: Mapped[str] = mapped_column(String(255))
    url: Mapped[str] = mapped_column(String(2048), index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_fetched_at: Mapped[datetime | None] = mapped_column(default=None)
    last_error: Mapped[str | None] = mapped_column(Text, default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime, default_factory=now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default_factory=now, nullable=False, onupdate=func.now())
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, default=None)

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

    def soft_delete(self) -> None:
        self.deleted_at = now()

    def __repr__(self) -> str:
        return f"<Source(id={self.id}, name={self.name}, url={self.url})>"