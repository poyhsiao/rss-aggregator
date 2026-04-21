"""Tests for src/main.py lifespan logic."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.mark.asyncio
async def test_both_schedulers_start_regardless_of_flag():
    mock_scheduler = MagicMock()
    mock_scheduler.start = AsyncMock()
    mock_scheduler.stop = AsyncMock()

    mock_schedule_scheduler = MagicMock()
    mock_schedule_scheduler.start = AsyncMock()
    mock_schedule_scheduler.stop = AsyncMock()

    with patch("src.main.settings") as mock_settings, \
         patch("src.main.FetchScheduler", return_value=mock_scheduler), \
         patch("src.main.ScheduleScheduler", return_value=mock_schedule_scheduler), \
         patch("src.main.set_scheduler"), \
         patch("src.db.database.async_session_factory"):
        mock_settings.scheduler_enabled = False
        mock_settings.scheduler_interval = 60
        mock_settings.allowed_origins = "*"

        from src.main import lifespan, app
        async with lifespan(app):
            pass

        mock_scheduler.start.assert_called_once()
        mock_schedule_scheduler.start.assert_called_once()


@pytest.mark.asyncio
async def test_both_schedulers_stop_regardless_of_flag():
    mock_scheduler = MagicMock()
    mock_scheduler.start = AsyncMock()
    mock_scheduler.stop = AsyncMock()

    mock_schedule_scheduler = MagicMock()
    mock_schedule_scheduler.start = AsyncMock()
    mock_schedule_scheduler.stop = AsyncMock()

    with patch("src.main.settings") as mock_settings, \
         patch("src.main.FetchScheduler", return_value=mock_scheduler), \
         patch("src.main.ScheduleScheduler", return_value=mock_schedule_scheduler), \
         patch("src.main.set_scheduler"), \
         patch("src.db.database.async_session_factory"):
        mock_settings.scheduler_enabled = False
        mock_settings.scheduler_interval = 60
        mock_settings.allowed_origins = "*"

        from src.main import lifespan, app
        async with lifespan(app):
            pass

        mock_schedule_scheduler.stop.assert_called_once()
        mock_scheduler.stop.assert_called_once()


@pytest.mark.asyncio
async def test_both_schedulers_start_when_enabled():
    mock_scheduler = MagicMock()
    mock_scheduler.start = AsyncMock()
    mock_scheduler.stop = AsyncMock()

    mock_schedule_scheduler = MagicMock()
    mock_schedule_scheduler.start = AsyncMock()
    mock_schedule_scheduler.stop = AsyncMock()

    with patch("src.main.settings") as mock_settings, \
         patch("src.main.FetchScheduler", return_value=mock_scheduler), \
         patch("src.main.ScheduleScheduler", return_value=mock_schedule_scheduler), \
         patch("src.main.set_scheduler"), \
         patch("src.db.database.async_session_factory"):
        mock_settings.scheduler_enabled = True
        mock_settings.scheduler_interval = 60
        mock_settings.allowed_origins = "*"

        from src.main import lifespan, app
        async with lifespan(app):
            pass

        mock_scheduler.start.assert_called_once()
        mock_schedule_scheduler.start.assert_called_once()


@pytest.mark.asyncio
async def test_both_schedulers_stop_when_enabled():
    mock_scheduler = MagicMock()
    mock_scheduler.start = AsyncMock()
    mock_scheduler.stop = AsyncMock()

    mock_schedule_scheduler = MagicMock()
    mock_schedule_scheduler.start = AsyncMock()
    mock_schedule_scheduler.stop = AsyncMock()

    with patch("src.main.settings") as mock_settings, \
         patch("src.main.FetchScheduler", return_value=mock_scheduler), \
         patch("src.main.ScheduleScheduler", return_value=mock_schedule_scheduler), \
         patch("src.main.set_scheduler"), \
         patch("src.db.database.async_session_factory"):
        mock_settings.scheduler_enabled = True
        mock_settings.scheduler_interval = 60
        mock_settings.allowed_origins = "*"

        from src.main import lifespan, app
        async with lifespan(app):
            pass

        mock_schedule_scheduler.stop.assert_called_once()
        mock_scheduler.stop.assert_called_once()
