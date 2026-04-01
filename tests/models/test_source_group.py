"""Tests for SourceGroup and SourceGroupMember models."""

import pytest
from sqlalchemy import select

from src.models import Source, SourceGroup, SourceGroupMember


@pytest.mark.asyncio
async def test_create_source_group(db_session):
    group = SourceGroup(name="Tech")
    db_session.add(group)
    await db_session.commit()
    await db_session.refresh(group)
    assert group.id is not None
    assert group.name == "Tech"


@pytest.mark.asyncio
async def test_source_group_unique_name(db_session):
    db_session.add(SourceGroup(name="Tech"))
    await db_session.commit()
    db_session.add(SourceGroup(name="Tech"))
    with pytest.raises(Exception):
        await db_session.commit()


@pytest.mark.asyncio
async def test_source_group_many_to_many(db_session):
    g1 = SourceGroup(name="Tech")
    g2 = SourceGroup(name="News")
    db_session.add_all([g1, g2])
    await db_session.commit()
    await db_session.refresh(g1)
    await db_session.refresh(g2)

    s = Source(name="Feed", url="https://example.com/rss")
    db_session.add(s)
    await db_session.commit()
    await db_session.refresh(s)

    m1 = SourceGroupMember(source_id=s.id, group_id=g1.id)
    m2 = SourceGroupMember(source_id=s.id, group_id=g2.id)
    db_session.add_all([m1, m2])
    await db_session.commit()

    result = await db_session.execute(
        select(SourceGroup)
        .join(SourceGroupMember, SourceGroup.id == SourceGroupMember.group_id)
        .where(SourceGroupMember.source_id == s.id)
    )
    groups = list(result.scalars().all())
    assert len(groups) == 2


@pytest.mark.asyncio
async def test_cascade_delete_group(db_session):
    group = SourceGroup(name="Temp")
    db_session.add(group)
    await db_session.commit()
    await db_session.refresh(group)

    source = Source(name="Feed", url="https://example.com/rss")
    db_session.add(source)
    await db_session.commit()
    await db_session.refresh(source)

    member = SourceGroupMember(source_id=source.id, group_id=group.id)
    db_session.add(member)
    await db_session.commit()

    await db_session.delete(group)
    await db_session.commit()

    result = await db_session.execute(select(Source).where(Source.id == source.id))
    assert result.scalar_one_or_none() is not None

    result = await db_session.execute(select(SourceGroupMember))
    assert len(list(result.scalars().all())) == 0
