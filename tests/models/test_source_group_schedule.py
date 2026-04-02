"""Tests for SourceGroupSchedule model."""

import pytest
from sqlalchemy import select

from src.models import SourceGroup, SourceGroupSchedule


@pytest.mark.asyncio
async def test_create_schedule(db_session):
    """SourceGroupSchedule model should exist with correct fields."""
    # Create a group first
    group = SourceGroup(name="Test Group")
    db_session.add(group)
    await db_session.commit()
    await db_session.refresh(group)

    schedule = SourceGroupSchedule(
        group_id=group.id,
        cron_expression="0 * * * *",
    )
    db_session.add(schedule)
    await db_session.commit()
    await db_session.refresh(schedule)

    assert schedule.id is not None
    assert schedule.group_id == group.id
    assert schedule.cron_expression == "0 * * * *"
    assert schedule.is_enabled is True
    assert schedule.next_run_at is None


@pytest.mark.asyncio
async def test_schedule_default_values(db_session):
    """Schedule should have correct default values."""
    group = SourceGroup(name="Test")
    db_session.add(group)
    await db_session.commit()
    await db_session.refresh(group)

    schedule = SourceGroupSchedule(
        group_id=group.id,
        cron_expression="*/15 * * * *",
    )
    db_session.add(schedule)
    await db_session.commit()
    await db_session.refresh(schedule)

    assert schedule.is_enabled is True
    assert schedule.created_at is not None
    assert schedule.updated_at is not None


@pytest.mark.asyncio
async def test_schedule_relation(db_session):
    schedule = SourceGroupSchedule(
        group_id=1,
        cron_expression="0 * * * *",
    )
    assert schedule.cron_expression == "0 * * * *"
    assert schedule.group_id == 1


@pytest.mark.asyncio
async def test_schedule_is_enabled_toggle(db_session):
    """Schedule should toggle is_enabled correctly."""
    group = SourceGroup(name="Test")
    db_session.add(group)
    await db_session.commit()
    await db_session.refresh(group)

    schedule = SourceGroupSchedule(
        group_id=group.id,
        cron_expression="0 * * * *",
        is_enabled=True,
    )
    db_session.add(schedule)
    await db_session.commit()

    # Toggle off
    schedule.is_enabled = False
    await db_session.commit()
    await db_session.refresh(schedule)
    assert schedule.is_enabled is False

    # Toggle back on
    schedule.is_enabled = True
    await db_session.commit()
    await db_session.refresh(schedule)
    assert schedule.is_enabled is True