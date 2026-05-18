"""Feature flag settings model."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base
from src.utils.time import now


class FeatureFlag(Base):
    """Feature flag settings for user preferences."""

    __tablename__ = "feature_flags"

    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    value: Mapped[str] = mapped_column(String(50), nullable=False, default="true")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default_factory=now, nullable=False, onupdate=func.now()
    )

    def __repr__(self) -> str:
        return f"<FeatureFlag(key={self.key}, value={self.value}, updated_at={self.updated_at})>"