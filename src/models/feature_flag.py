"""Feature flag model for feature toggles."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base
from src.utils.time import now


class FeatureFlag(Base):
    """Feature flag for toggling features on/off."""

    __tablename__ = "feature_flags"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, init=False)
    key: Mapped[str] = mapped_column(String(255), unique=True)
    enabled: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(default_factory=now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(default_factory=now, nullable=False)

    def __repr__(self) -> str:
        return f"<FeatureFlag(key={self.key}, enabled={self.enabled})>"