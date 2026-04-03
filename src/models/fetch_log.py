"""FetchLog model for tracking fetch operations."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base
from src.utils.time import now

if TYPE_CHECKING:
    from src.models.source import Source


class FetchLog(Base):
    """Log for tracking fetch operations (success and error)."""

    __tablename__ = "fetch_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, init=False)
    log_type: Mapped[str] = mapped_column(String(100))
    message: Mapped[str] = mapped_column(Text)
    source_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("sources.id"), default=None
    )
    status: Mapped[str] = mapped_column(String(20), default="error")
    items_count: Mapped[int | None] = mapped_column(Integer, default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime, default_factory=now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default_factory=now, nullable=False, onupdate=func.now())
    source: Mapped["Source"] = relationship("Source", init=False)

    def __repr__(self) -> str:
        return f"<FetchLog(id={self.id}, status={self.status}, type={self.log_type})>"