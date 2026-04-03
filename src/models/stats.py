"""Stats model for daily statistics."""

from datetime import date, datetime

from sqlalchemy import Date, DateTime, Integer, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base
from src.utils.time import now


class Stats(Base):
    """Daily statistics for monitoring."""

    __tablename__ = "stats"
    __table_args__ = (UniqueConstraint("date", name="uq_stats_date"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, init=False)
    date: Mapped[date] = mapped_column(Date)
    total_requests: Mapped[int] = mapped_column(Integer, default=0)
    successful_fetches: Mapped[int] = mapped_column(Integer, default=0)
    failed_fetches: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default_factory=now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default_factory=now, nullable=False, onupdate=func.now())

    def __repr__(self) -> str:
        return f"<Stats(date={self.date}, requests={self.total_requests})>"