"""Tests for database initialization with FetchBatch table.

TDD RED-GREEN cycle:
1. RED: Test fails when fetch_batches table doesn't exist
2. GREEN: After fixing database initialization
"""

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.database import async_session_factory, engine
from src.models import Base, FetchBatch
from src.services.history_service import HistoryService


class TestDatabaseInitialization:
    """Tests for database table initialization."""

    @pytest.mark.asyncio
    async def test_fetch_batches_table_exists_after_init(self, db_session: AsyncSession):
        """Test that fetch_batches table is created during initialization.

        This test verifies that all required tables exist after
        Base.metadata.create_all is called.
        """
        result = await db_session.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name='fetch_batches'")
        )
        table_exists = result.fetchone() is not None

        assert table_exists, "fetch_batches table should exist after database initialization"

    @pytest.mark.asyncio
    async def test_history_service_can_query_batches(self, db_session: AsyncSession):
        """Test that HistoryService can query fetch_batches table."""
        history_service = HistoryService(db_session)

        result = await history_service.get_history_batches()

        assert result is not None
        assert hasattr(result, "batches")
        assert hasattr(result, "total_batches")
        assert hasattr(result, "total_items")

    @pytest.mark.asyncio
    async def test_feed_items_has_batch_id_column(self, db_session: AsyncSession):
        """Test that feed_items table has batch_id column."""
        result = await db_session.execute(
            text("PRAGMA table_info(feed_items)")
        )
        columns = {row[1] for row in result.fetchall()}

        assert "batch_id" in columns, "feed_items table should have batch_id column"

    @pytest.mark.asyncio
    async def test_can_create_fetch_batch(self, db_session: AsyncSession):
        """Test that FetchBatch can be created and persisted."""
        batch = FetchBatch(items_count=0, sources="[]")
        db_session.add(batch)
        await db_session.commit()

        result = await db_session.execute(
            text("SELECT id, items_count, sources FROM fetch_batches")
        )
        batches = result.fetchall()

        assert len(batches) == 1
        assert batches[0][1] == 0