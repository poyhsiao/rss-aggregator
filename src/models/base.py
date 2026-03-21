"""SQLAlchemy base model with soft delete support."""

from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, MappedAsDataclass, attributes, mapped_column

from src.utils.time import now


class Base(MappedAsDataclass, DeclarativeBase, kw_only=True):
    """SQLAlchemy declarative base for all models."""

    pass


class TimestampMixin:
    """Mixin for created_at, updated_at, and deleted_at timestamps."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default_factory=func.now, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default_factory=func.now, nullable=False
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True, default=None
    )

    def soft_delete(self) -> None:
        """Mark this record as deleted without triggering attribute history."""
        # Use set_committed_value to avoid SAWarning during flush operations
        attributes.set_committed_value(self, "deleted_at", now())