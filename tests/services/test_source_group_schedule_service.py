import pytest
from src.models import SourceGroup, SourceGroupSchedule
from src.services.source_group_schedule_service import (
    DuplicateScheduleError,
    SourceGroupScheduleService,
)


@pytest.mark.asyncio
async def test_create_schedule(db_session):
    service = SourceGroupScheduleService(db_session)
    
    group = SourceGroup(name="Test Group")
    db_session.add(group)
    await db_session.flush()
    
    schedule = await service.create_schedule(
        group_id=group.id,
        cron_expression="0 * * * *",
    )
    
    assert schedule.id is not None
    assert schedule.cron_expression == "0 * * * *"
    assert schedule.is_enabled is True
    assert schedule.next_run_at is not None


@pytest.mark.asyncio
async def test_invalid_cron_rejected(db_session):
    service = SourceGroupScheduleService(db_session)
    
    group = SourceGroup(name="Test Group")
    db_session.add(group)
    await db_session.flush()
    
    with pytest.raises(ValueError, match="Invalid cron"):
        await service.create_schedule(group_id=group.id, cron_expression="invalid")


@pytest.mark.asyncio
async def test_duplicate_cron_rejected(db_session):
    service = SourceGroupScheduleService(db_session)
    
    group = SourceGroup(name="Test Group")
    db_session.add(group)
    await db_session.flush()
    
    await service.create_schedule(group_id=group.id, cron_expression="0 * * * *")
    
    with pytest.raises(DuplicateScheduleError):
        await service.create_schedule(group_id=group.id, cron_expression="0 * * * *")


@pytest.mark.asyncio
async def test_list_schedules(db_session):
    service = SourceGroupScheduleService(db_session)
    
    group = SourceGroup(name="Test Group")
    db_session.add(group)
    await db_session.flush()
    
    await service.create_schedule(group_id=group.id, cron_expression="0 * * * *")
    await service.create_schedule(group_id=group.id, cron_expression="*/15 * * * *")
    
    schedules = await service.list_schedules(group.id)
    assert len(schedules) == 2


@pytest.mark.asyncio
async def test_toggle_schedule(db_session):
    service = SourceGroupScheduleService(db_session)
    
    group = SourceGroup(name="Test Group")
    db_session.add(group)
    await db_session.flush()
    
    schedule = await service.create_schedule(group_id=group.id, cron_expression="0 * * * *")
    assert schedule.is_enabled is True
    
    toggled = await service.toggle_schedule(schedule.id)
    assert toggled.is_enabled is False
    assert toggled.next_run_at is None
    
    toggled_again = await service.toggle_schedule(schedule.id)
    assert toggled_again.is_enabled is True
    assert toggled_again.next_run_at is not None