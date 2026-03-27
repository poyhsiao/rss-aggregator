"""SQLAlchemy base model with soft delete support."""

from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    MappedAsDataclass,
    mapped_column,
)

from src.utils.time import now


class Base(MappedAsDataclass, DeclarativeBase, kw_only=True):
    """SQLAlchemy declarative base for all models."""

    pass


class TimestampMixin(MappedAsDataclass, kw_only=True):
    """Mixin for created_at, updated_at, and deleted_at timestamps.

    Note: Must inherit from MappedAsDataclass to avoid SQLAlchemy 2.1 deprecation warning
    when used with dataclass models.
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default_factory=now, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default_factory=now, nullable=False, onupdate=now
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True, default=None
    )

    def soft_delete(self) -> None:
        """Mark this record as deleted."""
        self.deleted_at = now()
