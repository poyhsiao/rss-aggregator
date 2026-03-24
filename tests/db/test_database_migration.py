"""Tests for database migration logic.

TDD RED-GREEN cycle:
1. Test that migration creates missing tables/columns
2. Test that migration is idempotent (can run multiple times)
"""

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, AsyncConnection

from src.stdio.server import StdioServer


class TestDatabaseMigration:
    """Tests for database migration logic."""

    @pytest.mark.asyncio
    async def test_migration_creates_fetch_batches_table(self, db_session: AsyncSession):
        """Test that migration creates fetch_batches table if missing."""
        server = StdioServer()

        async with db_session.begin():
            await server._run_migrations(db_session)

        result = await db_session.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name='fetch_batches'")
        )
        table_exists = result.fetchone() is not None

        assert table_exists, "Migration should create fetch_batches table"

    @pytest.mark.asyncio
    async def test_migration_adds_batch_id_column(self, db_session: AsyncSession):
        """Test that migration adds batch_id column to feed_items if missing."""
        server = StdioServer()

        async with db_session.begin():
            await server._run_migrations(db_session)

        result = await db_session.execute(
            text("PRAGMA table_info(feed_items)")
        )
        columns = {row[1] for row in result.fetchall()}

        assert "batch_id" in columns, "Migration should add batch_id column"

    @pytest.mark.asyncio
    async def test_migration_is_idempotent(self, db_session: AsyncSession):
        """Test that migration can run multiple times without error."""
        server = StdioServer()

        async with db_session.begin():
            await server._run_migrations(db_session)

        async with db_session.begin():
            await server._run_migrations(db_session)

        result = await db_session.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name='fetch_batches'")
        )
        tables = result.fetchall()

        assert len(tables) == 1, "Migration should not create duplicate tables"