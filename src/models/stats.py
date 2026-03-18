"""Stats model for daily statistics."""

from datetime import date

from sqlalchemy import Date, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, TimestampMixin


class Stats(Base, TimestampMixin):
    """Daily statistics for monitoring."""

    __tablename__ = "stats"
    __table_args__ = (UniqueConstraint("date", name="uq_stats_date"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, init=False)
    date: Mapped[date] = mapped_column(Date)
    total_requests: Mapped[int] = mapped_column(Integer, default=0)
    successful_fetches: Mapped[int] = mapped_column(Integer, default=0)
    failed_fetches: Mapped[int] = mapped_column(Integer, default=0)

    def __repr__(self) -> str:
        return f"<Stats(date={self.date}, requests={self.total_requests})>"