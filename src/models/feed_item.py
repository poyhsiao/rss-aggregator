"""FeedItem model for cached RSS items."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base, TimestampMixin


class FeedItem(Base, TimestampMixin):
    """Cached RSS feed item."""

    __tablename__ = "feed_items"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, init=False)
    source_id: Mapped[int] = mapped_column(Integer, ForeignKey("sources.id"))
    title: Mapped[str] = mapped_column(String(500))
    link: Mapped[str] = mapped_column(String(2048))
    description: Mapped[str | None] = mapped_column(Text, default=None)
    published_at: Mapped[datetime | None] = mapped_column(DateTime, default=None)
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime, default_factory=func.now
    )

    source: Mapped["Source"] = relationship("Source", back_populates="feed_items", init=False)

    def __repr__(self) -> str:
        return f"<FeedItem(id={self.id}, title={self.title[:30]}...)>"