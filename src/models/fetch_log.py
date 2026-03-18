"""FetchLog model for tracking fetch operations."""

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base, TimestampMixin


class FetchLog(Base, TimestampMixin):
    """Log for tracking fetch operations (success and error)."""

    __tablename__ = "fetch_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, init=False)
    source_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("sources.id"), default=None
    )
    status: Mapped[str] = mapped_column(String(20), default="error")
    log_type: Mapped[str] = mapped_column(String(100))
    message: Mapped[str] = mapped_column(Text)
    items_count: Mapped[int | None] = mapped_column(Integer, default=None)

    source: Mapped["Source | None"] = relationship("Source", init=False)

    def __repr__(self) -> str:
        return f"<FetchLog(id={self.id}, status={self.status}, type={self.log_type})>"