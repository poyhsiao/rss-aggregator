"""Tests for BackupService serialization methods."""

from datetime import datetime, date
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.services.backup_service import BackupService


def create_mock_column(name: str) -> MagicMock:
    """Create a mock column with a name attribute."""
    col = MagicMock()
    col.name = name
    return col


def create_mock_source() -> MagicMock:
    """Create a mock Source model."""
    mock_source = MagicMock()
    mock_source.__table__ = MagicMock()
    mock_source.__table__.columns = [
        create_mock_column("id"),
        create_mock_column("name"),
        create_mock_column("url"),
        create_mock_column("fetch_interval"),
        create_mock_column("is_active"),
        create_mock_column("last_fetched_at"),
        create_mock_column("last_error"),
        create_mock_column("created_at"),
        create_mock_column("updated_at"),
    ]
    mock_source.id = 1
    mock_source.name = "Test Source"
    mock_source.url = "https://example.com/rss.xml"
    mock_source.fetch_interval = 3600
    mock_source.is_active = True
    mock_source.last_fetched_at = datetime(2026, 3, 27, 10, 0, 0)
    mock_source.last_error = None
    mock_source.created_at = datetime(2026, 3, 27, 10, 0, 0)
    mock_source.updated_at = datetime(2026, 3, 27, 10, 0, 0)
    return mock_source


def create_mock_feed_item() -> MagicMock:
    """Create a mock FeedItem model."""
    mock_item = MagicMock()
    mock_item.__table__ = MagicMock()
    mock_item.__table__.columns = [
        create_mock_column("id"),
        create_mock_column("source_id"),
        create_mock_column("title"),
        create_mock_column("link"),
        create_mock_column("batch_id"),
        create_mock_column("description"),
        create_mock_column("published_at"),
        create_mock_column("fetched_at"),
        create_mock_column("created_at"),
        create_mock_column("updated_at"),
    ]
    mock_item.id = 1
    mock_item.source_id = 1
    mock_item.title = "Test Article"
    mock_item.link = "https://example.com/article"
    mock_item.batch_id = None
    mock_item.description = "Test description"
    mock_item.published_at = datetime(2026, 3, 27, 10, 0, 0)
    mock_item.fetched_at = datetime(2026, 3, 27, 10, 0, 0)
    mock_item.created_at = datetime(2026, 3, 27, 10, 0, 0)
    mock_item.updated_at = datetime(2026, 3, 27, 10, 0, 0)
    return mock_item


def create_mock_api_key() -> MagicMock:
    """Create a mock APIKey model."""
    mock_key = MagicMock()
    mock_key.__table__ = MagicMock()
    mock_key.__table__.columns = [
        create_mock_column("id"),
        create_mock_column("key"),
        create_mock_column("name"),
        create_mock_column("is_active"),
        create_mock_column("created_at"),
        create_mock_column("updated_at"),
    ]
    mock_key.id = 1
    mock_key.key = "test-api-key-123"
    mock_key.name = "Test Key"
    mock_key.is_active = True
    mock_key.created_at = datetime(2026, 3, 27, 10, 0, 0)
    mock_key.updated_at = datetime(2026, 3, 27, 10, 0, 0)
    return mock_key


def create_mock_fetch_log() -> MagicMock:
    """Create a mock FetchLog model."""
    mock_log = MagicMock()
    mock_log.__table__ = MagicMock()
    mock_log.__table__.columns = [
        create_mock_column("id"),
        create_mock_column("log_type"),
        create_mock_column("message"),
        create_mock_column("source_id"),
        create_mock_column("status"),
        create_mock_column("items_count"),
        create_mock_column("created_at"),
        create_mock_column("updated_at"),
    ]
    mock_log.id = 1
    mock_log.log_type = "fetch"
    mock_log.message = "Successfully fetched 10 items"
    mock_log.source_id = 1
    mock_log.status = "success"
    mock_log.items_count = 10
    mock_log.created_at = datetime(2026, 3, 27, 10, 0, 0)
    mock_log.updated_at = datetime(2026, 3, 27, 10, 0, 0)
    return mock_log


def create_mock_preview_content() -> MagicMock:
    """Create a mock PreviewContent model."""
    mock_preview = MagicMock()
    mock_preview.__table__ = MagicMock()
    mock_preview.__table__.columns = [
        create_mock_column("id"),
        create_mock_column("url"),
        create_mock_column("url_hash"),
        create_mock_column("markdown_content"),
        create_mock_column("title"),
        create_mock_column("created_at"),
        create_mock_column("updated_at"),
    ]
    mock_preview.id = 1
    mock_preview.url = "https://example.com/article"
    mock_preview.url_hash = "abc123"
    mock_preview.markdown_content = "# Test Article\nContent here"
    mock_preview.title = "Test Article"
    mock_preview.created_at = datetime(2026, 3, 27, 10, 0, 0)
    mock_preview.updated_at = datetime(2026, 3, 27, 10, 0, 0)
    return mock_preview


def create_mock_fetch_batch() -> MagicMock:
    """Create a mock FetchBatch model."""
    mock_batch = MagicMock()
    mock_batch.__table__ = MagicMock()
    mock_batch.__table__.columns = [
        create_mock_column("id"),
        create_mock_column("items_count"),
        create_mock_column("sources"),
        create_mock_column("notes"),
        create_mock_column("created_at"),
        create_mock_column("updated_at"),
    ]
    mock_batch.id = 1
    mock_batch.items_count = 10
    mock_batch.sources = "source1,source2"
    mock_batch.notes = "Test batch"
    mock_batch.created_at = datetime(2026, 3, 27, 10, 0, 0)
    mock_batch.updated_at = datetime(2026, 3, 27, 10, 0, 0)
    return mock_batch


def create_mock_stats() -> MagicMock:
    """Create a mock Stats model."""
    mock_stat = MagicMock()
    mock_stat.__table__ = MagicMock()
    mock_stat.__table__.columns = [
        create_mock_column("id"),
        create_mock_column("date"),
        create_mock_column("total_requests"),
        create_mock_column("successful_fetches"),
        create_mock_column("failed_fetches"),
        create_mock_column("created_at"),
        create_mock_column("updated_at"),
    ]
    mock_stat.id = 1
    mock_stat.date = date(2026, 3, 27)
    mock_stat.total_requests = 100
    mock_stat.successful_fetches = 95
    mock_stat.failed_fetches = 5
    mock_stat.created_at = datetime(2026, 3, 27, 10, 0, 0)
    mock_stat.updated_at = datetime(2026, 3, 27, 10, 0, 0)
    return mock_stat


class TestBackupServiceSerialize:
    """Test cases for BackupService serialization."""

    @pytest.fixture
    def mock_db(self) -> MagicMock:
        """Create mock database session."""
        return MagicMock()

    @pytest.fixture
    def backup_service(self, mock_db: MagicMock) -> BackupService:
        """Create BackupService instance."""
        return BackupService(mock_db)

    @pytest.mark.asyncio
    async def test_serialize_empty_database(self, backup_service: BackupService) -> None:
        """Test serializing empty database."""
        with patch.object(backup_service, "_get_all_sources", return_value=[]):
            with patch.object(backup_service, "_get_all_feed_items", return_value=[]):
                with patch.object(backup_service, "_get_all_api_keys", return_value=[]):
                    with patch.object(
                        backup_service, "_get_all_preview_contents", return_value=[]
                    ):
                        with patch.object(
                            backup_service, "_get_all_fetch_batches", return_value=[]
                        ):
                            with patch.object(
                                backup_service, "_get_all_fetch_logs", return_value=[]
                            ):
                                with patch.object(
                                    backup_service, "_get_all_stats", return_value=[]
                                ):
                                    result = await backup_service._serialize_data()

                                    assert result["sources"] == []
                                    assert result["feed_items"] == []
                                    assert result["api_keys"] == []

    @pytest.mark.asyncio
    async def test_serialize_sources(self, backup_service: BackupService) -> None:
        """Test serializing sources."""
        mock_source = create_mock_source()

        with patch.object(
            backup_service, "_get_all_sources", return_value=[mock_source]
        ):
            with patch.object(backup_service, "_get_all_feed_items", return_value=[]):
                with patch.object(backup_service, "_get_all_api_keys", return_value=[]):
                    with patch.object(
                        backup_service, "_get_all_preview_contents", return_value=[]
                    ):
                        with patch.object(
                            backup_service, "_get_all_fetch_batches", return_value=[]
                        ):
                            with patch.object(
                                backup_service, "_get_all_fetch_logs", return_value=[]
                            ):
                                with patch.object(
                                    backup_service, "_get_all_stats", return_value=[]
                                ):
                                    result = await backup_service._serialize_data()

                                    assert len(result["sources"]) == 1
                                    assert result["sources"][0]["name"] == "Test Source"
                                    assert (
                                        result["sources"][0]["url"]
                                        == "https://example.com/rss.xml"
                                    )

    @pytest.mark.asyncio
    async def test_serialize_feed_items(self, backup_service: BackupService) -> None:
        """Test serializing feed items."""
        mock_item = create_mock_feed_item()

        with patch.object(backup_service, "_get_all_sources", return_value=[]):
            with patch.object(
                backup_service, "_get_all_feed_items", return_value=[mock_item]
            ):
                with patch.object(backup_service, "_get_all_api_keys", return_value=[]):
                    with patch.object(
                        backup_service, "_get_all_preview_contents", return_value=[]
                    ):
                        with patch.object(
                            backup_service, "_get_all_fetch_batches", return_value=[]
                        ):
                            with patch.object(
                                backup_service, "_get_all_fetch_logs", return_value=[]
                            ):
                                with patch.object(
                                    backup_service, "_get_all_stats", return_value=[]
                                ):
                                    result = await backup_service._serialize_data()

                                    assert len(result["feed_items"]) == 1
                                    assert result["feed_items"][0]["title"] == "Test Article"

    @pytest.mark.asyncio
    async def test_serialize_api_keys(self, backup_service: BackupService) -> None:
        """Test serializing API keys."""
        mock_key = create_mock_api_key()

        with patch.object(backup_service, "_get_all_sources", return_value=[]):
            with patch.object(backup_service, "_get_all_feed_items", return_value=[]):
                with patch.object(
                    backup_service, "_get_all_api_keys", return_value=[mock_key]
                ):
                    with patch.object(
                        backup_service, "_get_all_preview_contents", return_value=[]
                    ):
                        with patch.object(
                            backup_service, "_get_all_fetch_batches", return_value=[]
                        ):
                            with patch.object(
                                backup_service, "_get_all_fetch_logs", return_value=[]
                            ):
                                with patch.object(
                                    backup_service, "_get_all_stats", return_value=[]
                                ):
                                    result = await backup_service._serialize_data()

                                    assert len(result["api_keys"]) == 1
                                    assert result["api_keys"][0]["name"] == "Test Key"

    @pytest.mark.asyncio
    async def test_serialize_fetch_logs(self, backup_service: BackupService) -> None:
        """Test serializing fetch logs."""
        mock_log = create_mock_fetch_log()

        with patch.object(backup_service, "_get_all_sources", return_value=[]):
            with patch.object(backup_service, "_get_all_feed_items", return_value=[]):
                with patch.object(backup_service, "_get_all_api_keys", return_value=[]):
                    with patch.object(
                        backup_service, "_get_all_preview_contents", return_value=[]
                    ):
                        with patch.object(
                            backup_service, "_get_all_fetch_batches", return_value=[]
                        ):
                            with patch.object(
                                backup_service, "_get_all_fetch_logs", return_value=[mock_log]
                            ):
                                with patch.object(
                                    backup_service, "_get_all_stats", return_value=[]
                                ):
                                    result = await backup_service._serialize_data()

                                    assert len(result["fetch_logs"]) == 1
                                    assert result["fetch_logs"][0]["status"] == "success"

    @pytest.mark.asyncio
    async def test_serialize_preview_contents(
        self, backup_service: BackupService
    ) -> None:
        """Test serializing preview contents."""
        mock_preview = create_mock_preview_content()

        with patch.object(backup_service, "_get_all_sources", return_value=[]):
            with patch.object(backup_service, "_get_all_feed_items", return_value=[]):
                with patch.object(backup_service, "_get_all_api_keys", return_value=[]):
                    with patch.object(
                        backup_service,
                        "_get_all_preview_contents",
                        return_value=[mock_preview],
                    ):
                        with patch.object(
                            backup_service, "_get_all_fetch_batches", return_value=[]
                        ):
                            with patch.object(
                                backup_service, "_get_all_fetch_logs", return_value=[]
                            ):
                                with patch.object(
                                    backup_service, "_get_all_stats", return_value=[]
                                ):
                                    result = await backup_service._serialize_data()

                                    assert len(result["preview_contents"]) == 1
                                    assert (
                                        result["preview_contents"][0]["title"]
                                        == "Test Article"
                                    )

    @pytest.mark.asyncio
    async def test_serialize_fetch_batches(self, backup_service: BackupService) -> None:
        """Test serializing fetch batches."""
        mock_batch = create_mock_fetch_batch()

        with patch.object(backup_service, "_get_all_sources", return_value=[]):
            with patch.object(backup_service, "_get_all_feed_items", return_value=[]):
                with patch.object(backup_service, "_get_all_api_keys", return_value=[]):
                    with patch.object(
                        backup_service, "_get_all_preview_contents", return_value=[]
                    ):
                        with patch.object(
                            backup_service,
                            "_get_all_fetch_batches",
                            return_value=[mock_batch],
                        ):
                            with patch.object(
                                backup_service, "_get_all_fetch_logs", return_value=[]
                            ):
                                with patch.object(
                                    backup_service, "_get_all_stats", return_value=[]
                                ):
                                    result = await backup_service._serialize_data()

                                    assert len(result["fetch_batches"]) == 1
                                    assert result["fetch_batches"][0]["items_count"] == 10

    @pytest.mark.asyncio
    async def test_serialize_stats(self, backup_service: BackupService) -> None:
        """Test serializing stats."""
        mock_stat = create_mock_stats()

        with patch.object(backup_service, "_get_all_sources", return_value=[]):
            with patch.object(backup_service, "_get_all_feed_items", return_value=[]):
                with patch.object(backup_service, "_get_all_api_keys", return_value=[]):
                    with patch.object(
                        backup_service, "_get_all_preview_contents", return_value=[]
                    ):
                        with patch.object(
                            backup_service, "_get_all_fetch_batches", return_value=[]
                        ):
                            with patch.object(
                                backup_service, "_get_all_fetch_logs", return_value=[]
                            ):
                                with patch.object(
                                    backup_service,
                                    "_get_all_stats",
                                    return_value=[mock_stat],
                                ):
                                    result = await backup_service._serialize_data()

                                    assert len(result["stats"]) == 1
                                    assert result["stats"][0]["total_requests"] == 100

    def test_serialize_model_datetime(self, backup_service: BackupService) -> None:
        """Test _serialize_model with datetime field."""
        mock_obj = MagicMock()
        mock_obj.__table__ = MagicMock()
        mock_obj.__table__.columns = [create_mock_column("created_at")]
        mock_obj.created_at = datetime(2026, 3, 27, 10, 0, 0)

        result = backup_service._serialize_model(mock_obj)

        assert "created_at" in result
        assert result["created_at"] == "2026-03-27T10:00:00"

    def test_serialize_model_date(self, backup_service: BackupService) -> None:
        """Test _serialize_model with date field."""
        mock_obj = MagicMock()
        mock_obj.__table__ = MagicMock()
        mock_obj.__table__.columns = [create_mock_column("date")]
        mock_obj.date = date(2026, 3, 27)

        result = backup_service._serialize_model(mock_obj)

        assert "date" in result
        assert result["date"] == "2026-03-27"

    def test_serialize_model_none_value(self, backup_service: BackupService) -> None:
        """Test _serialize_model with None value."""
        mock_obj = MagicMock()
        mock_obj.__table__ = MagicMock()
        mock_obj.__table__.columns = [create_mock_column("last_error")]
        mock_obj.last_error = None

        result = backup_service._serialize_model(mock_obj)

        assert "last_error" in result
        assert result["last_error"] is None