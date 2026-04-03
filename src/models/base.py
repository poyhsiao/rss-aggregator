"""SQLAlchemy base model."""

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
    """Mixin for created_at and updated_at timestamps."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default_factory=now, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default_factory=now, nullable=False, onupdate=now
    )
