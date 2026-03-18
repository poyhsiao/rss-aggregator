"""SQLAlchemy base model with soft delete support."""

from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """SQLAlchemy declarative base for all models."""

    pass


class TimestampMixin:
    """Mixin for created_at, updated_at, and deleted_at timestamps."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True, default=None
    )

    def soft_delete(self) -> None:
        """Mark this record as deleted."""
        self.deleted_at = datetime.utcnow()