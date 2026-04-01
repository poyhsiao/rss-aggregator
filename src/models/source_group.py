"""SourceGroup and SourceGroupMember models."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from src.models.source import Source


class SourceGroup(Base, TimestampMixin):
    """Source grouping for organization."""

    __tablename__ = "source_groups"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, init=False)
    name: Mapped[str] = mapped_column(String(255), unique=True)

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
