"""Service for managing source groups."""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import Source, SourceGroup, SourceGroupMember


class SourceGroupService:
    """Service for managing source groups and their memberships."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_group(self, name: str) -> SourceGroup:
        """Create a new source group.

        Raises:
            ValueError: If group with same name already exists.
        """
        existing = await self.session.execute(
            select(SourceGroup).where(SourceGroup.name == name)
        )
        if existing.scalar_one_or_none():
            raise ValueError(f"Group '{name}' already exists")

        group = SourceGroup(name=name)
        self.session.add(group)
        await self.session.commit()
        await self.session.refresh(group)
        return group

    async def list_groups(self) -> list[SourceGroup]:
        """List all source groups."""
        result = await self.session.execute(select(SourceGroup))
        return list(result.scalars().all())

    async def list_groups_with_count(self) -> list[dict]:
        """List all groups with member counts using a single JOIN query."""
        result = await self.session.execute(
            select(
                SourceGroup.id,
                SourceGroup.name,
                SourceGroup.created_at,
                SourceGroup.updated_at,
                func.count(SourceGroupMember.source_id).label("member_count"),
            )
            .outerjoin(SourceGroupMember, SourceGroup.id == SourceGroupMember.group_id)
            .group_by(SourceGroup.id)
        )
        return [
            {
                "id": row.id,
                "name": row.name,
                "member_count": row.member_count,
                "created_at": row.created_at,
                "updated_at": row.updated_at,
            }
            for row in result.all()
        ]

    async def update_group(self, group_id: int, **kwargs) -> SourceGroup:
        """Update a group.

        Raises:
            ValueError: If group not found.
        """
        result = await self.session.execute(
            select(SourceGroup).where(SourceGroup.id == group_id)
        )
        group = result.scalar_one_or_none()
        if group is None:
            raise ValueError(f"Group {group_id} not found")

        for key, value in kwargs.items():
            if hasattr(group, key):
                setattr(group, key, value)

        await self.session.commit()
        await self.session.refresh(group)
        return group

    async def delete_group(self, group_id: int) -> None:
        """Delete a group (does NOT delete member sources).

        Raises:
            ValueError: If group not found.
        """
        result = await self.session.execute(
            select(SourceGroup).where(SourceGroup.id == group_id)
        )
        group = result.scalar_one_or_none()
        if group is None:
            raise ValueError(f"Group {group_id} not found")

        await self.session.delete(group)
        await self.session.commit()

    async def add_source_to_group(self, group_id: int, source_id: int) -> None:
        """Add a source to a group.

        Raises:
            ValueError: If group or source not found, or already a member.
        """
        grp = await self.session.execute(
            select(SourceGroup).where(SourceGroup.id == group_id)
        )
        if not grp.scalar_one_or_none():
            raise ValueError(f"Group {group_id} not found")

        src = await self.session.execute(
            select(Source).where(Source.id == source_id, Source.deleted_at.is_(None))
        )
        if not src.scalar_one_or_none():
            raise ValueError(f"Source {source_id} not found")

        existing = await self.session.execute(
            select(SourceGroupMember).where(
                SourceGroupMember.group_id == group_id,
                SourceGroupMember.source_id == source_id,
            )
        )
        if existing.scalar_one_or_none():
            raise ValueError(f"Source {source_id} is already in group {group_id}")

        member = SourceGroupMember(group_id=group_id, source_id=source_id)
        self.session.add(member)
        await self.session.commit()

    async def remove_source_from_group(self, group_id: int, source_id: int) -> None:
        """Remove a source from a group.

        Raises:
            ValueError: If membership not found.
        """
        result = await self.session.execute(
            select(SourceGroupMember).where(
                SourceGroupMember.group_id == group_id,
                SourceGroupMember.source_id == source_id,
            )
        )
        member = result.scalar_one_or_none()
        if member is None:
            raise ValueError(f"Source {source_id} not in group {group_id}")

        await self.session.delete(member)
        await self.session.commit()

    async def get_source_groups(self, source_id: int) -> list[SourceGroup]:
        """Get all groups a source belongs to."""
        result = await self.session.execute(
            select(SourceGroup)
            .join(SourceGroupMember, SourceGroup.id == SourceGroupMember.group_id)
            .where(SourceGroupMember.source_id == source_id)
        )
        return list(result.scalars().all())

    async def get_group_sources(self, group_id: int) -> list[Source]:
        """Get all sources in a group (excluding soft-deleted)."""
        result = await self.session.execute(
            select(Source)
            .join(SourceGroupMember, Source.id == SourceGroupMember.source_id)
            .where(
                SourceGroupMember.group_id == group_id,
                Source.deleted_at.is_(None),
            )
        )
        return list(result.scalars().all())
