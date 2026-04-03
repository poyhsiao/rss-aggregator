"""SourceGroup and SourceGroupMember models."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base
from src.utils.time import now

if TYPE_CHECKING:
    from src.models.source import Source


class SourceGroup(Base):
    """Source grouping for organization."""

    __tablename__ = "source_groups"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, init=False)
    name: Mapped[str] = mapped_column(String(255), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default_factory=now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default_factory=now, nullable=False, onupdate=func.now())

    sources: Mapped[list[Source]] = relationship(
        "Source",
        secondary="source_group_members",
        back_populates="groups",
        init=False,
    )

    def __repr__(self) -> str:
        return f"<SourceGroup(id={self.id}, name={self.name})>"


class SourceGroupMember(Base):
    """Junction table for many-to-many Source and SourceGroup."""

    __tablename__ = "source_group_members"

    source_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("sources.id", ondelete="CASCADE"), primary_key=True
    )
    group_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("source_groups.id", ondelete="CASCADE"), primary_key=True
    )
