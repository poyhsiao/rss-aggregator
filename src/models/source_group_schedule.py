from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    pass


class SourceGroupSchedule(Base, TimestampMixin):
    __tablename__ = "source_group_schedules"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, init=False)
    group_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("source_groups.id", ondelete="CASCADE"), nullable=False
    )
    cron_expression: Mapped[str] = mapped_column(String(100), nullable=False)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    next_run_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True, default=None
    )

    def __repr__(self) -> str:
        return f"<SourceGroupSchedule(id={self.id}, group_id={self.group_id}, cron={self.cron_expression})>"