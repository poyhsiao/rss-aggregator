"""AppSettings model — stores global feature toggles."""

from __future__ import annotations

from sqlalchemy import Boolean
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base


class AppSettings(Base):
    """Singleton app settings stored in database.

    Holds global feature enable/disable flags. Only one record
    should exist (id=1). Initialized automatically at startup.
    """
    __tablename__ = "app_settings"

    id: Mapped[int] = mapped_column(primary_key=True, default=1)
    group_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    schedule_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    share_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
