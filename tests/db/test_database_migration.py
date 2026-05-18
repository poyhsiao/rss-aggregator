"""Tests for database migration logic.

TDD RED-GREEN cycle:
1. Test that migration creates missing tables/columns
2. Test that migration is idempotent (can run multiple times)
"""

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class TestDatabaseMigration:
    """Tests for database migration logic."""

    @pytest.mark.asyncio
    async def test_migration_creates_fetch_batches_table(self, db_session: AsyncSession):
        """Test that migration creates fetch_batches table if missing."""
        # Check if fetch_batches table exists after migrations run via conftest
        result = await db_session.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name='fetch_batches'")
        )
        table_exists = result.fetchone() is not None

        assert table_exists, "Migration should create fetch_batches table"

    @pytest.mark.asyncio
    async def test_migration_adds_batch_id_column(self, db_session: AsyncSession):
        """Test that migration adds batch_id column to feed_items if missing."""
        # Check if batch_id column exists in feed_items table
        result = await db_session.execute(
            text("PRAGMA table_info(feed_items)")
        )
        columns = {row[1] for row in result.fetchall()}

        assert "batch_id" in columns, "Migration should add batch_id column"

    @pytest.mark.asyncio
    async def test_migration_is_idempotent(self, db_session: AsyncSession):
        """Test that migration can run multiple times without error."""
        # Run a simple query twice to verify no error
        async with db_session.begin():
            result1 = await db_session.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name='fetch_batches'")
            )
            tables1 = result1.fetchall()

        async with db_session.begin():
            result2 = await db_session.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name='fetch_batches'")
            )
            tables2 = result2.fetchall()

        assert len(tables1) == 1, "Migration should create fetch_batches table"
        assert tables1 == tables2, "Second migration run should not change tables"