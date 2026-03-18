"""ErrorLog model for tracking errors."""

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base, TimestampMixin


class ErrorLog(Base, TimestampMixin):
    """Error log for tracking fetch and parse errors."""

    __tablename__ = "error_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, init=False)
    source_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("sources.id"), default=None
    )
    error_type: Mapped[str] = mapped_column(String(100))
    error_message: Mapped[str] = mapped_column(Text)

    source: Mapped["Source | None"] = relationship("Source", init=False)

    def __repr__(self) -> str:
        return f"<ErrorLog(id={self.id}, type={self.error_type})>"