# Backup and Restore Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement backup, restore, and migration functionality for RSS Aggregator with encrypted JSON backup files.

**Architecture:** Backend BackupService handles serialization, encryption, and merge logic. REST API provides endpoints for Web/Docker. Tauri commands provide native file dialogs for desktop. Frontend adds UI in Settings page.

**Tech Stack:** Python (FastAPI, pyzipper), Rust (Tauri, zip crate), Vue 3 (frontend), SQLite (database)

---

## Phase 1: Backend Service

### Task 1: Add pyzipper dependency

**Files:**
- Modify: `pyproject.toml`

**Step 1: Add pyzipper to dependencies**

Add to `pyproject.toml` dependencies section:

```toml
dependencies = [
    # ... existing dependencies
    "pyzipper>=0.3.6",
]
```

**Step 2: Install dependencies**

Run: `uv sync`
Expected: Dependencies installed successfully

**Step 3: Commit**

```bash
git add pyproject.toml uv.lock
git commit -m "chore: add pyzipper dependency for backup encryption"
```

---

### Task 2: Create BackupPasswordProvider

**Files:**
- Create: `src/services/backup_password_provider.py`
- Create: `tests/services/test_backup_password_provider.py`

**Step 1: Write the failing test**

Create `tests/services/test_backup_password_provider.py`:

```python
"""Tests for BackupPasswordProvider."""

import os
from unittest.mock import patch

import pytest

from src.services.backup_password_provider import BackupPasswordProvider


class TestBackupPasswordProvider:
    """Test cases for BackupPasswordProvider."""

    def test_get_password_from_env(self) -> None:
        """Test password from environment variable."""
        with patch.dict(os.environ, {"BACKUP_PASSWORD": "test_password"}):
            provider = BackupPasswordProvider()
            assert provider.get_password() == "test_password"

    def test_get_password_default(self) -> None:
        """Test default password when env var not set."""
        with patch.dict(os.environ, {}, clear=True):
            # Remove BACKUP_PASSWORD if exists
            os.environ.pop("BACKUP_PASSWORD", None)
            provider = BackupPasswordProvider()
            assert provider.get_password() == "kimhsiao"

    def test_get_password_empty_env_uses_default(self) -> None:
        """Test empty env var uses default password."""
        with patch.dict(os.environ, {"BACKUP_PASSWORD": ""}):
            provider = BackupPasswordProvider()
            assert provider.get_password() == "kimhsiao"
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/services/test_backup_password_provider.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'src.services.backup_password_provider'"

**Step 3: Write minimal implementation**

Create `src/services/backup_password_provider.py`:

```python
"""Password provider for backup encryption."""

import os


class BackupPasswordProvider:
    """Provides password for backup encryption/decryption."""

    DEFAULT_PASSWORD = "kimhsiao"

    def get_password(self) -> str:
        """
        Get backup password from environment or default.
        
        Returns:
            Password string from BACKUP_PASSWORD env var or default.
        """
        password = os.environ.get("BACKUP_PASSWORD", "").strip()
        return password if password else self.DEFAULT_PASSWORD
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/services/test_backup_password_provider.py -v`
Expected: All tests PASS

**Step 5: Commit**

```bash
git add src/services/backup_password_provider.py tests/services/test_backup_password_provider.py
git commit -m "feat(backup): add BackupPasswordProvider with env var support"
```

---

### Task 3: Create backup data schemas

**Files:**
- Create: `src/schemas/backup.py`
- Create: `tests/schemas/test_backup.py`

**Step 1: Write the failing test**

Create `tests/schemas/test_backup.py`:

```python
"""Tests for backup schemas."""

from datetime import datetime

import pytest

from src.schemas.backup import (
    BackupConfig,
    BackupContent,
    BackupCounts,
    BackupPreview,
    ImportSummary,
    ImportResult,
)


class TestBackupSchemas:
    """Test cases for backup schemas."""

    def test_backup_config_defaults(self) -> None:
        """Test BackupConfig with default values."""
        config = BackupConfig()
        assert config.timezone == "Asia/Taipei"
        assert config.language == "zh"

    def test_backup_config_custom(self) -> None:
        """Test BackupConfig with custom values."""
        config = BackupConfig(timezone="UTC", language="en")
        assert config.timezone == "UTC"
        assert config.language == "en"

    def test_backup_counts(self) -> None:
        """Test BackupCounts."""
        counts = BackupCounts(sources=5, feed_items=100, api_keys=1)
        assert counts.sources == 5
        assert counts.feed_items == 100
        assert counts.api_keys == 1

    def test_backup_content(self) -> None:
        """Test BackupContent."""
        content = BackupContent(
            version="0.10.0",
            exported_at="2026-03-27T15:30:00+08:00",
            app_name="RSS-Aggregator",
            data={},
            config=BackupConfig(),
        )
        assert content.version == "0.10.0"
        assert content.app_name == "RSS-Aggregator"

    def test_backup_preview(self) -> None:
        """Test BackupPreview."""
        preview = BackupPreview(
            version="0.10.0",
            exported_at="2026-03-27T15:30:00+08:00",
            counts=BackupCounts(sources=5, feed_items=100, api_keys=1),
            config=BackupConfig(),
        )
        assert preview.version == "0.10.0"
        assert preview.counts.sources == 5

    def test_import_summary(self) -> None:
        """Test ImportSummary."""
        summary = ImportSummary(
            sources_imported=3,
            sources_merged=2,
            feed_items_imported=100,
            api_keys_imported=1,
        )
        assert summary.sources_imported == 3
        assert summary.sources_merged == 2

    def test_import_result_success(self) -> None:
        """Test ImportResult success."""
        result = ImportResult(
            success=True,
            message="Backup imported successfully",
            summary=ImportSummary(
                sources_imported=3,
                sources_merged=2,
                feed_items_imported=100,
                api_keys_imported=1,
            ),
        )
        assert result.success is True
        assert result.message == "Backup imported successfully"
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/schemas/test_backup.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'src.schemas.backup'"

**Step 3: Write minimal implementation**

Create `src/schemas/backup.py`:

```python
"""Schemas for backup and restore functionality."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class BackupConfig(BaseModel):
    """Application configuration in backup."""

    timezone: str = "Asia/Taipei"
    language: str = "zh"


class BackupCounts(BaseModel):
    """Counts of items in backup."""

    sources: int = 0
    feed_items: int = 0
    api_keys: int = 0
    preview_contents: int = 0
    fetch_batches: int = 0
    fetch_logs: int = 0
    stats: int = 0


class BackupContent(BaseModel):
    """Full backup content structure."""

    version: str
    exported_at: str
    app_name: str = "RSS-Aggregator"
    data: dict[str, Any]
    config: BackupConfig


class BackupPreview(BaseModel):
    """Preview of backup without full data."""

    version: str
    exported_at: str
    counts: BackupCounts
    config: BackupConfig


class ExportOptions(BaseModel):
    """Options for backup export."""

    include_feed_items: bool = True
    include_preview_contents: bool = True
    include_logs: bool = False


class ImportSummary(BaseModel):
    """Summary of import operation."""

    sources_imported: int = 0
    sources_merged: int = 0
    feed_items_imported: int = 0
    api_keys_imported: int = 0


class ImportResult(BaseModel):
    """Result of import operation."""

    success: bool
    message: str
    summary: ImportSummary | None = None
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/schemas/test_backup.py -v`
Expected: All tests PASS

**Step 5: Commit**

```bash
git add src/schemas/backup.py tests/schemas/test_backup.py
git commit -m "feat(backup): add backup data schemas"
```

---

### Task 4: Create BackupService - serialization

**Files:**
- Create: `src/services/backup_service.py`
- Create: `tests/services/test_backup_service_serialize.py`

**Step 1: Write the failing test**

Create `tests/services/test_backup_service_serialize.py`:

```python
"""Tests for BackupService serialization."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.services.backup_service import BackupService


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
                    with patch.object(backup_service, "_get_all_preview_contents", return_value=[]):
                        with patch.object(backup_service, "_get_all_fetch_batches", return_value=[]):
                            with patch.object(backup_service, "_get_all_fetch_logs", return_value=[]):
                                with patch.object(backup_service, "_get_all_stats", return_value=[]):
                                    result = await backup_service._serialize_data()
                                    
                                    assert result["sources"] == []
                                    assert result["feed_items"] == []
                                    assert result["api_keys"] == []

    @pytest.mark.asyncio
    async def test_serialize_sources(self, backup_service: BackupService) -> None:
        """Test serializing sources."""
        mock_source = MagicMock()
        mock_source.id = 1
        mock_source.name = "Test Source"
        mock_source.url = "https://example.com/rss.xml"
        mock_source.fetch_interval = 3600
        mock_source.is_active = True
        mock_source.last_fetched_at = None
        mock_source.last_error = None
        mock_source.created_at = datetime(2026, 3, 27, 10, 0, 0)
        mock_source.updated_at = datetime(2026, 3, 27, 10, 0, 0)

        with patch.object(backup_service, "_get_all_sources", return_value=[mock_source]):
            with patch.object(backup_service, "_get_all_feed_items", return_value=[]):
                with patch.object(backup_service, "_get_all_api_keys", return_value=[]):
                    with patch.object(backup_service, "_get_all_preview_contents", return_value=[]):
                        with patch.object(backup_service, "_get_all_fetch_batches", return_value=[]):
                            with patch.object(backup_service, "_get_all_fetch_logs", return_value=[]):
                                with patch.object(backup_service, "_get_all_stats", return_value=[]):
                                    result = await backup_service._serialize_data()
                                    
                                    assert len(result["sources"]) == 1
                                    assert result["sources"][0]["name"] == "Test Source"
                                    assert result["sources"][0]["url"] == "https://example.com/rss.xml"
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/services/test_backup_service_serialize.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'src.services.backup_service'"

**Step 3: Write minimal implementation**

Create `src/services/backup_service.py`:

```python
"""Backup and restore service."""

from __future__ import annotations

import io
import json
import zipfile
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

from sqlalchemy import select

from src.models import APIKey, FeedItem, FetchBatch, FetchLog, PreviewContent, Source, Stats
from src.schemas.backup import BackupConfig, BackupContent, BackupCounts, ExportOptions, ImportResult, ImportSummary
from src.services.backup_password_provider import BackupPasswordProvider

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class BackupService:
    """Service for backup and restore operations."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialize BackupService."""
        self._db = db
        self._password_provider = BackupPasswordProvider()

    async def _get_all_sources(self) -> list[Source]:
        """Get all sources from database."""
        result = await self._db.execute(select(Source))
        return list(result.scalars().all())

    async def _get_all_feed_items(self) -> list[FeedItem]:
        """Get all feed items from database."""
        result = await self._db.execute(select(FeedItem))
        return list(result.scalars().all())

    async def _get_all_api_keys(self) -> list[APIKey]:
        """Get all API keys from database."""
        result = await self._db.execute(select(APIKey))
        return list(result.scalars().all())

    async def _get_all_preview_contents(self) -> list[PreviewContent]:
        """Get all preview contents from database."""
        result = await self._db.execute(select(PreviewContent))
        return list(result.scalars().all())

    async def _get_all_fetch_batches(self) -> list[FetchBatch]:
        """Get all fetch batches from database."""
        result = await self._db.execute(select(FetchBatch))
        return list(result.scalars().all())

    async def _get_all_fetch_logs(self) -> list[FetchLog]:
        """Get all fetch logs from database."""
        result = await self._db.execute(select(FetchLog))
        return list(result.scalars().all())

    async def _get_all_stats(self) -> list[Stats]:
        """Get all stats from database."""
        result = await self._db.execute(select(Stats))
        return list(result.scalars().all())

    def _serialize_model(self, obj: Any) -> dict[str, Any]:
        """Serialize a SQLAlchemy model to dictionary."""
        result = {}
        for column in obj.__table__.columns:
            value = getattr(obj, column.name)
            if isinstance(value, datetime):
                value = value.isoformat()
            result[column.name] = value
        return result

    async def _serialize_data(self) -> dict[str, Any]:
        """Serialize all database data to dictionary."""
        sources = await self._get_all_sources()
        feed_items = await self._get_all_feed_items()
        api_keys = await self._get_all_api_keys()
        preview_contents = await self._get_all_preview_contents()
        fetch_batches = await self._get_all_fetch_batches()
        fetch_logs = await self._get_all_fetch_logs()
        stats = await self._get_all_stats()

        return {
            "sources": [self._serialize_model(s) for s in sources],
            "feed_items": [self._serialize_model(f) for f in feed_items],
            "api_keys": [self._serialize_model(k) for k in api_keys],
            "preview_contents": [self._serialize_model(p) for p in preview_contents],
            "fetch_batches": [self._serialize_model(b) for b in fetch_batches],
            "fetch_logs": [self._serialize_model(l) for l in fetch_logs],
            "stats": [self._serialize_model(s) for s in stats],
        }
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/services/test_backup_service_serialize.py -v`
Expected: All tests PASS

**Step 5: Commit**

```bash
git add src/services/backup_service.py tests/services/test_backup_service_serialize.py
git commit -m "feat(backup): add BackupService serialization methods"
```

---

### Task 5: Create BackupService - encryption

**Files:**
- Modify: `src/services/backup_service.py`
- Create: `tests/services/test_backup_service_encrypt.py`

**Step 1: Write the failing test**

Create `tests/services/test_backup_service_encrypt.py`:

```python
"""Tests for BackupService encryption."""

from unittest.mock import MagicMock

import pytest

from src.services.backup_service import BackupService


class TestBackupServiceEncrypt:
    """Test cases for BackupService encryption."""

    @pytest.fixture
    def mock_db(self) -> MagicMock:
        """Create mock database session."""
        return MagicMock()

    @pytest.fixture
    def backup_service(self, mock_db: MagicMock) -> BackupService:
        """Create BackupService instance."""
        return BackupService(mock_db)

    def test_encrypt_and_decrypt(self, backup_service: BackupService) -> None:
        """Test encrypt and decrypt round-trip."""
        data = b"test data content"
        
        encrypted = backup_service._encrypt_zip(data)
        assert encrypted is not None
        assert encrypted != data
        
        decrypted = backup_service._decrypt_zip(encrypted)
        assert decrypted == data

    def test_encrypt_creates_valid_zip(self, backup_service: BackupService) -> None:
        """Test encrypted output is valid ZIP."""
        import zipfile
        
        data = b"test content for zip"
        encrypted = backup_service._encrypt_zip(data)
        
        # Should be able to open as ZIP
        with zipfile.ZipFile(encrypted, 'r') as zf:
            assert zf.namelist() is not None

    def test_decrypt_with_wrong_password_fails(self, backup_service: BackupService) -> None:
        """Test decryption with wrong password fails."""
        from src.services.backup_password_provider import BackupPasswordProvider
        
        data = b"secret data"
        encrypted = backup_service._encrypt_zip(data)
        
        # Create service with different password
        different_provider = BackupPasswordProvider()
        different_provider.DEFAULT_PASSWORD = "wrong_password"
        
        with pytest.raises(Exception):  # pyzipper raises exception for wrong password
            backup_service._decrypt_zip(encrypted)
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/services/test_backup_service_encrypt.py -v`
Expected: FAIL with "AttributeError: 'BackupService' object has no attribute '_encrypt_zip'"

**Step 3: Write implementation**

Add to `src/services/backup_service.py`:

```python
import io
import zipfile

import pyzipper


class BackupService:
    # ... existing code ...

    def _encrypt_zip(self, data: bytes) -> io.BytesIO:
        """
        Encrypt data into a password-protected ZIP.
        
        Args:
            data: JSON data bytes to encrypt.
            
        Returns:
            BytesIO containing encrypted ZIP.
        """
        password = self._password_provider.get_password().encode()
        buffer = io.BytesIO()
        
        with pyzipper.AESZipFile(buffer, 'w', compression=pyzipper.ZIP_LZMA, encryption=pyzipper.WZ_AES) as zf:
            zf.setpassword(password)
            zf.writestr('backup.json', data)
        
        buffer.seek(0)
        return buffer

    def _decrypt_zip(self, zip_data: io.BytesIO | bytes) -> bytes:
        """
        Decrypt a password-protected ZIP.
        
        Args:
            zip_data: Encrypted ZIP data.
            
        Returns:
            Decrypted JSON data bytes.
            
        Raises:
            ValueError: If decryption fails.
        """
        password = self._password_provider.get_password().encode()
        
        if isinstance(zip_data, bytes):
            zip_data = io.BytesIO(zip_data)
        
        zip_data.seek(0)
        
        try:
            with pyzipper.AESZipFile(zip_data, 'r') as zf:
                zf.setpassword(password)
                return zf.read('backup.json')
        except Exception as e:
            raise ValueError(f"Failed to decrypt backup: {e}") from e
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/services/test_backup_service_encrypt.py -v`
Expected: All tests PASS

**Step 5: Commit**

```bash
git add src/services/backup_service.py tests/services/test_backup_service_encrypt.py
git commit -m "feat(backup): add ZIP encryption/decryption methods"
```

---

### Task 6: Create BackupService - export

**Files:**
- Modify: `src/services/backup_service.py`
- Create: `tests/services/test_backup_service_export.py`

**Step 1: Write the failing test**

Create `tests/services/test_backup_service_export.py`:

```python
"""Tests for BackupService export."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.schemas.backup import ExportOptions
from src.services.backup_service import BackupService


class TestBackupServiceExport:
    """Test cases for BackupService export."""

    @pytest.fixture
    def mock_db(self) -> MagicMock:
        """Create mock database session."""
        return MagicMock()

    @pytest.fixture
    def backup_service(self, backup_service: BackupService) -> BackupService:
        """Create BackupService instance."""
        return BackupService(mock_db)

    @pytest.mark.asyncio
    async def test_export_backup_returns_zip(self, backup_service: BackupService) -> None:
        """Test export_backup returns ZIP data."""
        with patch.object(backup_service, "_serialize_data", return_value={}):
            with patch.object(backup_service, "_get_config", return_value={}):
                result = await backup_service.export_backup(ExportOptions())
                
                assert result is not None
                assert isinstance(result, bytes)

    @pytest.mark.asyncio
    async def test_export_backup_filename_format(self, backup_service: BackupService) -> None:
        """Test export backup filename format."""
        filename = backup_service._generate_backup_filename("0.10.0")
        
        assert filename.startswith("rss-backup-v0.10.0-")
        assert filename.endswith(".zip")

    @pytest.mark.asyncio
    async def test_export_backup_with_options(self, backup_service: BackupService) -> None:
        """Test export with different options."""
        options = ExportOptions(
            include_feed_items=False,
            include_preview_contents=False,
            include_logs=True,
        )
        
        with patch.object(backup_service, "_serialize_data") as mock_serialize:
            mock_serialize.return_value = {
                "sources": [],
                "feed_items": [],
                "api_keys": [],
                "preview_contents": [],
                "fetch_batches": [],
                "fetch_logs": [{"id": 1}],
                "stats": [],
            }
            
            with patch.object(backup_service, "_get_config", return_value={}):
                result = await backup_service.export_backup(options)
                
                assert result is not None
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/services/test_backup_service_export.py -v`
Expected: FAIL with "AttributeError: 'BackupService' object has no attribute 'export_backup'"

**Step 3: Write implementation**

Add to `src/services/backup_service.py`:

```python
import json
from datetime import datetime, timezone


class BackupService:
    # ... existing code ...

    def _get_config(self) -> dict[str, str]:
        """Get application config for backup."""
        # TODO: Read from actual config storage
        return {
            "timezone": "Asia/Taipei",
            "language": "zh",
        }

    def _generate_backup_filename(self, version: str) -> str:
        """Generate backup filename with version and date."""
        date_str = datetime.now().strftime("%Y-%m-%d")
        return f"rss-backup-v{version}-{date_str}.zip"

    async def export_backup(self, options: ExportOptions) -> bytes:
        """
        Export database to encrypted JSON backup.
        
        Args:
            options: Export options.
            
        Returns:
            Encrypted ZIP bytes.
        """
        from src import __version__
        
        data = await self._serialize_data()
        
        # Apply options
        if not options.include_feed_items:
            data["feed_items"] = []
        if not options.include_preview_contents:
            data["preview_contents"] = []
        if not options.include_logs:
            data["fetch_logs"] = []
        
        backup_content = BackupContent(
            version=__version__,
            exported_at=datetime.now(timezone.utc).isoformat(),
            app_name="RSS-Aggregator",
            data=data,
            config=BackupConfig(**self._get_config()),
        )
        
        json_data = backup_content.model_dump_json(indent=2).encode('utf-8')
        encrypted_zip = self._encrypt_zip(json_data)
        
        return encrypted_zip.getvalue()
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/services/test_backup_service_export.py -v`
Expected: All tests PASS

**Step 5: Commit**

```bash
git add src/services/backup_service.py tests/services/test_backup_service_export.py
git commit -m "feat(backup): add export_backup method"
```

---

### Task 7: Create BackupService - merge logic

**Files:**
- Modify: `src/services/backup_service.py`
- Create: `tests/services/test_backup_service_merge.py`

**Step 1: Write the failing test**

Create `tests/services/test_backup_service_merge.py`:

```python
"""Tests for BackupService merge logic."""

from unittest.mock import MagicMock

import pytest

from src.services.backup_service import BackupService


class TestBackupServiceMerge:
    """Test cases for BackupService merge logic."""

    @pytest.fixture
    def mock_db(self) -> MagicMock:
        """Create mock database session."""
        return MagicMock()

    @pytest.fixture
    def backup_service(self, mock_db: MagicMock) -> BackupService:
        """Create BackupService instance."""
        return BackupService(mock_db)

    def test_is_version_compatible_same_major(self, backup_service: BackupService) -> None:
        """Test version compatibility with same major version."""
        assert backup_service._is_version_compatible("0.10.0", "0.11.0") is True
        assert backup_service._is_version_compatible("0.10.0", "0.9.0") is True

    def test_is_version_compatible_different_major(self, backup_service: BackupService) -> None:
        """Test version compatibility with different major version."""
        assert backup_service._is_version_compatible("0.10.0", "1.0.0") is False
        assert backup_service._is_version_compatible("1.0.0", "2.0.0") is False

    def test_merge_sources_by_url(self, backup_service: BackupService) -> None:
        """Test merging sources by URL."""
        existing = [
            {"id": 1, "url": "https://a.com/rss.xml", "name": "A"},
            {"id": 2, "url": "https://b.com/rss.xml", "name": "B"},
        ]
        backup = [
            {"id": 1, "url": "https://a.com/rss.xml", "name": "A Updated"},
            {"id": 3, "url": "https://c.com/rss.xml", "name": "C"},
        ]
        
        result, id_map = backup_service._merge_sources(existing, backup)
        
        assert len(result) == 3
        assert id_map[1] == 1  # Existing ID preserved
        assert id_map[3] == 3  # New source gets new ID

    def test_merge_feed_items_by_link(self, backup_service: BackupService) -> None:
        """Test merging feed items by link."""
        existing = [
            {"id": 1, "link": "https://a.com/1", "title": "Old"},
        ]
        backup = [
            {"id": 1, "link": "https://a.com/1", "title": "Updated"},
            {"id": 2, "link": "https://a.com/2", "title": "New"},
        ]
        source_id_map = {1: 1}
        
        result = backup_service._merge_feed_items(existing, backup, source_id_map)
        
        assert len(result) == 2
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/services/test_backup_service_merge.py -v`
Expected: FAIL with "AttributeError: 'BackupService' object has no attribute '_is_version_compatible'"

**Step 3: Write implementation**

Add to `src/services/backup_service.py`:

```python
from typing import Any


class BackupService:
    # ... existing code ...

    def _is_version_compatible(self, backup_version: str, current_version: str) -> bool:
        """
        Check version compatibility.
        
        Rules:
        - Same major version → Compatible
        - Different major version → Incompatible
        
        Args:
            backup_version: Version from backup file.
            current_version: Current application version.
            
        Returns:
            True if versions are compatible.
        """
        backup_major = backup_version.split('.')[0]
        current_major = current_version.split('.')[0]
        return backup_major == current_major

    def _merge_sources(
        self, 
        existing: list[dict[str, Any]], 
        backup: list[dict[str, Any]]
    ) -> tuple[list[dict[str, Any]], dict[int, int]]:
        """
        Merge sources, keyed by URL.
        
        Args:
            existing: Existing sources from database.
            backup: Sources from backup.
            
        Returns:
            Tuple of (merged sources, old_id -> new_id mapping).
        """
        existing_by_url = {s["url"]: s for s in existing}
        merged = list(existing)
        id_map: dict[int, int] = {}
        
        for source in backup:
            if source["url"] in existing_by_url:
                # Overwrite existing
                existing_source = existing_by_url[source["url"]]
                id_map[source["id"]] = existing_source["id"]
                # Update fields
                for key, value in source.items():
                    if key != "id":
                        existing_source[key] = value
            else:
                # Add new source
                new_id = len(merged) + 1
                new_source = {**source, "id": new_id}
                id_map[source["id"]] = new_id
                merged.append(new_source)
        
        return merged, id_map

    def _merge_feed_items(
        self,
        existing: list[dict[str, Any]],
        backup: list[dict[str, Any]],
        source_id_map: dict[int, int]
    ) -> list[dict[str, Any]]:
        """
        Merge feed items, keyed by link.
        
        Args:
            existing: Existing feed items from database.
            backup: Feed items from backup.
            source_id_map: Mapping of old source IDs to new IDs.
            
        Returns:
            Merged feed items.
        """
        existing_by_link = {f["link"]: f for f in existing}
        merged = list(existing)
        
        for item in backup:
            # Remap source_id
            if item["source_id"] in source_id_map:
                item = {**item, "source_id": source_id_map[item["source_id"]]}
            
            if item["link"] in existing_by_link:
                # Overwrite existing
                existing_item = existing_by_link[item["link"]]
                for key, value in item.items():
                    if key != "id":
                        existing_item[key] = value
            else:
                # Add new item
                new_id = len(merged) + 1
                merged.append({**item, "id": new_id})
        
        return merged

    def _merge_api_keys(
        self,
        existing: list[dict[str, Any]],
        backup: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Merge API keys, keyed by key string."""
        existing_by_key = {k["key"]: k for k in existing}
        merged = list(existing)
        
        for key in backup:
            if key["key"] in existing_by_key:
                existing_key = existing_by_key[key["key"]]
                for k, v in key.items():
                    if k != "id":
                        existing_key[k] = v
            else:
                new_id = len(merged) + 1
                merged.append({**key, "id": new_id})
        
        return merged
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/services/test_backup_service_merge.py -v`
Expected: All tests PASS

**Step 5: Commit**

```bash
git add src/services/backup_service.py tests/services/test_backup_service_merge.py
git commit -m "feat(backup): add merge logic for backup restore"
```

---

## Phase 2: REST API Endpoints

### Task 8: Create backup API routes

**Files:**
- Create: `src/api/routes/backup.py`
- Create: `tests/api/routes/test_backup.py`

**Step 1: Write the failing test**

Create `tests/api/routes/test_backup.py`:

```python
"""Tests for backup API routes."""

from io import BytesIO
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.routes.backup import router
from src.schemas.backup import ImportResult, ImportSummary


class TestBackupRoutes:
    """Test cases for backup API routes."""

    @pytest.fixture
    def app(self) -> FastAPI:
        """Create test FastAPI app."""
        app = FastAPI()
        app.include_router(router, prefix="/api/v1/backup")
        return app

    @pytest.fixture
    def client(self, app: FastAPI) -> TestClient:
        """Create test client."""
        return TestClient(app)

    def test_export_backup_endpoint_exists(self, client: TestClient) -> None:
        """Test export endpoint exists."""
        with patch("src.api.routes.backup.get_backup_service") as mock:
            mock_service = MagicMock()
            mock_service.export_backup = AsyncMock(return_value=b"zip_data")
            mock.return_value = mock_service
            
            response = client.post("/api/v1/backup/export", json={})
            
            assert response.status_code != 404

    def test_import_backup_endpoint_exists(self, client: TestClient) -> None:
        """Test import endpoint exists."""
        with patch("src.api.routes.backup.get_backup_service") as mock:
            mock_service = MagicMock()
            mock_service.import_backup = AsyncMock(
                return_value=ImportResult(
                    success=True,
                    message="OK",
                    summary=ImportSummary()
                )
            )
            mock.return_value = mock_service
            
            zip_file = BytesIO(b"fake_zip")
            response = client.post(
                "/api/v1/backup/import",
                files={"file": ("backup.zip", zip_file, "application/zip")}
            )
            
            assert response.status_code != 404

    def test_preview_backup_endpoint_exists(self, client: TestClient) -> None:
        """Test preview endpoint exists."""
        with patch("src.api.routes.backup.get_backup_service") as mock:
            mock_service = MagicMock()
            mock_service.preview_backup = AsyncMock(return_value={})
            mock.return_value = mock_service
            
            zip_file = BytesIO(b"fake_zip")
            response = client.post(
                "/api/v1/backup/preview",
                files={"file": ("backup.zip", zip_file, "application/zip")}
            )
            
            assert response.status_code != 404
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/api/routes/test_backup.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'src.api.routes.backup'"

**Step 3: Write minimal implementation**

Create `src/api/routes/backup.py`:

```python
"""Backup and restore API routes."""

from io import BytesIO
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import StreamingResponse

from src.api.deps import AsyncSessionDep
from src.schemas.backup import BackupPreview, ExportOptions, ImportResult
from src.services.backup_service import BackupService

router = APIRouter()


async def get_backup_service(db: AsyncSessionDep) -> BackupService:
    """Get BackupService instance."""
    return BackupService(db)


BackupServiceDep = Annotated[BackupService, Depends(get_backup_service)]


@router.post("/export")
async def export_backup(
    service: BackupServiceDep,
    include_feed_items: bool = Form(True),
    include_preview_contents: bool = Form(True),
    include_logs: bool = Form(False),
) -> StreamingResponse:
    """
    Export backup as encrypted ZIP.
    
    Returns encrypted ZIP file with all database content.
    """
    options = ExportOptions(
        include_feed_items=include_feed_items,
        include_preview_contents=include_preview_contents,
        include_logs=include_logs,
    )
    
    zip_data = await service.export_backup(options)
    filename = service._generate_backup_filename(service._get_app_version())
    
    return StreamingResponse(
        BytesIO(zip_data),
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )


@router.post("/import", response_model=ImportResult)
async def import_backup(
    service: BackupServiceDep,
    file: UploadFile = File(...),
) -> ImportResult:
    """
    Import backup from encrypted ZIP.
    
    Merges backup data with existing data.
    """
    content = await file.read()
    result = await service.import_backup(content)
    return result


@router.post("/preview", response_model=BackupPreview)
async def preview_backup(
    service: BackupServiceDep,
    file: UploadFile = File(...),
) -> BackupPreview:
    """
    Preview backup content without importing.
    
    Shows version, counts, and config from backup.
    """
    content = await file.read()
    preview = await service.preview_backup(content)
    return preview
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/api/routes/test_backup.py -v`
Expected: All tests PASS

**Step 5: Commit**

```bash
git add src/api/routes/backup.py tests/api/routes/test_backup.py
git commit -m "feat(api): add backup REST API endpoints"
```

---

### Task 9: Register backup routes in main app

**Files:**
- Modify: `src/main.py`

**Step 1: Add backup router to main app**

Add import and router registration in `src/main.py`:

```python
from src.api.routes import backup

# In router registration section:
app.include_router(backup.router, prefix="/api/v1/backup", tags=["backup"])
```

**Step 2: Verify routes are registered**

Run: `uv run uvicorn src.main:app --reload`
Then check: `curl http://localhost:8000/docs`
Expected: Backup endpoints visible in OpenAPI docs

**Step 3: Commit**

```bash
git add src/main.py
git commit -m "feat(api): register backup routes in main app"
```

---

## Phase 3: Frontend UI

### Task 10: Add backup API client

**Files:**
- Create: `web/src/api/backup.ts`
- Create: `web/src/api/__tests__/backup.test.ts`

**Step 1: Write the failing test**

Create `web/src/api/__tests__/backup.test.ts`:

```typescript
import { describe, it, expect, vi } from 'vitest'
import { exportBackup, importBackup, previewBackup } from '../backup'

describe('backup API', () => {
  it('exportBackup returns blob', async () => {
    const mockBlob = new Blob(['zip data'], { type: 'application/zip' })
    vi.spyOn(global, 'fetch').mockResolvedValueOnce({
      ok: true,
      blob: () => Promise.resolve(mockBlob),
    } as Response)

    const result = await exportBackup({})
    expect(result).toBeInstanceOf(Blob)
  })

  it('importBackup returns result', async () => {
    const mockResult = { success: true, message: 'OK' }
    vi.spyOn(global, 'fetch').mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockResult),
    } as Response)

    const file = new File(['data'], 'backup.zip')
    const result = await importBackup(file)
    expect(result.success).toBe(true)
  })

  it('previewBackup returns preview data', async () => {
    const mockPreview = { version: '0.10.0', counts: {} }
    vi.spyOn(global, 'fetch').mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockPreview),
    } as Response)

    const file = new File(['data'], 'backup.zip')
    const result = await previewBackup(file)
    expect(result.version).toBe('0.10.0')
  })
})
```

**Step 2: Run test to verify it fails**

Run: `cd web && pnpm test src/api/__tests__/backup.test.ts`
Expected: FAIL with "Cannot find module '../backup'"

**Step 3: Write implementation**

Create `web/src/api/backup.ts`:

```typescript
import { apiClient } from './index'

export interface ExportOptions {
  include_feed_items?: boolean
  include_preview_contents?: boolean
  include_logs?: boolean
}

export interface ImportResult {
  success: boolean
  message: string
  summary?: {
    sources_imported: number
    sources_merged: number
    feed_items_imported: number
    api_keys_imported: number
  }
}

export interface BackupPreview {
  version: string
  exported_at: string
  counts: {
    sources: number
    feed_items: number
    api_keys: number
    preview_contents: number
  }
  config: {
    timezone: string
    language: string
  }
}

/**
 * Export backup as encrypted ZIP
 */
export async function exportBackup(options: ExportOptions): Promise<Blob> {
  const formData = new FormData()
  formData.append('include_feed_items', String(options.include_feed_items ?? true))
  formData.append('include_preview_contents', String(options.include_preview_contents ?? true))
  formData.append('include_logs', String(options.include_logs ?? false))

  const response = await apiClient.post('/api/v1/backup/export', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    responseType: 'blob',
  })

  return response.data
}

/**
 * Import backup from encrypted ZIP
 */
export async function importBackup(file: File): Promise<ImportResult> {
  const formData = new FormData()
  formData.append('file', file)

  const response = await apiClient.post('/api/v1/backup/import', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })

  return response.data
}

/**
 * Preview backup content without importing
 */
export async function previewBackup(file: File): Promise<BackupPreview> {
  const formData = new FormData()
  formData.append('file', file)

  const response = await apiClient.post('/api/v1/backup/preview', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })

  return response.data
}
```

**Step 4: Run test to verify it passes**

Run: `cd web && pnpm test src/api/__tests__/backup.test.ts`
Expected: All tests PASS

**Step 5: Commit**

```bash
git add web/src/api/backup.ts web/src/api/__tests__/backup.test.ts
git commit -m "feat(web): add backup API client"
```

---

### Task 11: Add i18n keys for backup

**Files:**
- Modify: `web/src/locales/en.json`
- Modify: `web/src/locales/zh.json`

**Step 1: Add English translations**

Add to `web/src/locales/en.json`:

```json
{
  "settings": {
    "data_management": "Data Management",
    "export_backup": "Export Backup",
    "import_backup": "Import Backup",
    "include_feed_items": "Include RSS Items",
    "include_preview_contents": "Include Article Previews",
    "include_logs": "Include Fetch Logs",
    "choose_file": "Choose File",
    "confirm_import": "Confirm Import",
    "backup_preview": "Backup Preview",
    "version": "Version",
    "exported_at": "Exported At",
    "sources_count": "Sources",
    "items_count": "Items",
    "api_keys_count": "API Keys",
    "export_success": "Backup exported successfully",
    "import_success": "Backup imported successfully",
    "import_summary": "Sources: {imported} imported, {merged} merged",
    "backup_file": "Backup File",
    "no_file_selected": "No file selected"
  }
}
```

**Step 2: Add Chinese translations**

Add to `web/src/locales/zh.json`:

```json
{
  "settings": {
    "data_management": "資料管理",
    "export_backup": "匯出備份",
    "import_backup": "匯入備份",
    "include_feed_items": "包含 RSS 項目",
    "include_preview_contents": "包含文章預覽快取",
    "include_logs": "包含抓取日誌",
    "choose_file": "選擇檔案",
    "confirm_import": "確認匯入",
    "backup_preview": "備份預覽",
    "version": "版本",
    "exported_at": "匯出時間",
    "sources_count": "來源數量",
    "items_count": "項目數量",
    "api_keys_count": "API 金鑰",
    "export_success": "備份匯出成功",
    "import_success": "備份匯入成功",
    "import_summary": "來源：匯入 {imported} 個，合併 {merged} 個",
    "backup_file": "備份檔案",
    "no_file_selected": "未選擇檔案"
  }
}
```

**Step 3: Commit**

```bash
git add web/src/locales/en.json web/src/locales/zh.json
git commit -m "feat(web): add i18n keys for backup feature"
```

---

### Task 12: Add backup UI component

**Files:**
- Create: `web/src/components/BackupManager.vue`
- Create: `web/src/components/__tests__/BackupManager.test.ts`

**Step 1: Write the failing test**

Create `web/src/components/__tests__/BackupManager.test.ts`:

```typescript
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import BackupManager from '../BackupManager.vue'

describe('BackupManager', () => {
  it('renders export button', () => {
    const wrapper = mount(BackupManager)
    expect(wrapper.text()).toContain('Export Backup')
  })

  it('renders import button', () => {
    const wrapper = mount(BackupManager)
    expect(wrapper.text()).toContain('Import Backup')
  })

  it('has export options checkboxes', () => {
    const wrapper = mount(BackupManager)
    const checkboxes = wrapper.findAll('input[type="checkbox"]')
    expect(checkboxes.length).toBeGreaterThan(0)
  })
})
```

**Step 2: Run test to verify it fails**

Run: `cd web && pnpm test src/components/__tests__/BackupManager.test.ts`
Expected: FAIL with "Cannot find component"

**Step 3: Write implementation**

Create `web/src/components/BackupManager.vue`:

```vue
<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { Download, Upload, FileJson } from 'lucide-vue-next'
import { exportBackup, importBackup, previewBackup, type BackupPreview } from '@/api/backup'
import { useToast } from '@/composables/useToast'

const { t } = useI18n()
const toast = useToast()

// Export options
const includeFeedItems = ref(true)
const includePreviewContents = ref(true)
const includeLogs = ref(false)

// Import state
const selectedFile = ref<File | null>(null)
const preview = ref<BackupPreview | null>(null)
const isExporting = ref(false)
const isImporting = ref(false)

async function handleExport() {
  isExporting.value = true
  try {
    const blob = await exportBackup({
      include_feed_items: includeFeedItems.value,
      include_preview_contents: includePreviewContents.value,
      include_logs: includeLogs.value,
    })
    
    // Download file
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `rss-backup-${new Date().toISOString().split('T')[0]}.zip`
    a.click()
    URL.revokeObjectURL(url)
    
    toast.success(t('settings.export_success'))
  } catch (error) {
    toast.error('Export failed')
  } finally {
    isExporting.value = false
  }
}

async function handleFileSelect(event: Event) {
  const target = event.target as HTMLInputElement
  if (target.files?.[0]) {
    selectedFile.value = target.files[0]
    // Auto-preview
    try {
      preview.value = await previewBackup(selectedFile.value)
    } catch (error) {
      toast.error('Failed to read backup file')
    }
  }
}

async function handleImport() {
  if (!selectedFile.value) return
  
  isImporting.value = true
  try {
    const result = await importBackup(selectedFile.value)
    if (result.success) {
      toast.success(t('settings.import_success'))
      selectedFile.value = null
      preview.value = null
    }
  } catch (error) {
    toast.error('Import failed')
  } finally {
    isImporting.value = false
  }
}
</script>

<template>
  <div class="space-y-6">
    <!-- Export Section -->
    <div class="space-y-4">
      <h3 class="text-lg font-semibold">{{ t('settings.export_backup') }}</h3>
      
      <div class="space-y-2">
        <label class="flex items-center gap-2">
          <input type="checkbox" v-model="includeFeedItems" />
          <span>{{ t('settings.include_feed_items') }}</span>
        </label>
        
        <label class="flex items-center gap-2">
          <input type="checkbox" v-model="includePreviewContents" />
          <span>{{ t('settings.include_preview_contents') }}</span>
        </label>
        
        <label class="flex items-center gap-2">
          <input type="checkbox" v-model="includeLogs" />
          <span>{{ t('settings.include_logs') }}</span>
        </label>
      </div>
      
      <button
        @click="handleExport"
        :disabled="isExporting"
        class="flex items-center gap-2 px-4 py-2 bg-primary text-white rounded hover:bg-primary/90 disabled:opacity-50"
      >
        <Download class="w-4 h-4" />
        {{ isExporting ? 'Exporting...' : t('settings.export_backup') }}
      </button>
    </div>
    
    <!-- Divider -->
    <hr class="border-border" />
    
    <!-- Import Section -->
    <div class="space-y-4">
      <h3 class="text-lg font-semibold">{{ t('settings.import_backup') }}</h3>
      
      <div>
        <label class="flex items-center gap-2 px-4 py-2 border rounded cursor-pointer hover:bg-muted">
          <Upload class="w-4 h-4" />
          <span>{{ t('settings.choose_file') }}</span>
          <input
            type="file"
            accept=".zip"
            @change="handleFileSelect"
            class="hidden"
          />
        </label>
        
        <p v-if="selectedFile" class="mt-2 text-sm text-muted-foreground">
          {{ t('settings.backup_file') }}: {{ selectedFile.name }}
        </p>
      </div>
      
      <!-- Preview -->
      <div v-if="preview" class="p-4 border rounded bg-muted/50">
        <h4 class="font-medium mb-2">{{ t('settings.backup_preview') }}</h4>
        <dl class="text-sm space-y-1">
          <div class="flex justify-between">
            <dt class="text-muted-foreground">{{ t('settings.version') }}</dt>
            <dd>{{ preview.version }}</dd>
          </div>
          <div class="flex justify-between">
            <dt class="text-muted-foreground">{{ t('settings.exported_at') }}</dt>
            <dd>{{ new Date(preview.exported_at).toLocaleString() }}</dd>
          </div>
          <div class="flex justify-between">
            <dt class="text-muted-foreground">{{ t('settings.sources_count') }}</dt>
            <dd>{{ preview.counts.sources }}</dd>
          </div>
          <div class="flex justify-between">
            <dt class="text-muted-foreground">{{ t('settings.items_count') }}</dt>
            <dd>{{ preview.counts.feed_items }}</dd>
          </div>
        </dl>
      </div>
      
      <button
        @click="handleImport"
        :disabled="!selectedFile || isImporting"
        class="flex items-center gap-2 px-4 py-2 bg-primary text-white rounded hover:bg-primary/90 disabled:opacity-50"
      >
        <FileJson class="w-4 h-4" />
        {{ isImporting ? 'Importing...' : t('settings.confirm_import') }}
      </button>
    </div>
  </div>
</template>
```

**Step 4: Run test to verify it passes**

Run: `cd web && pnpm test src/components/__tests__/BackupManager.test.ts`
Expected: All tests PASS

**Step 5: Commit**

```bash
git add web/src/components/BackupManager.vue web/src/components/__tests__/BackupManager.test.ts
git commit -m "feat(web): add BackupManager component"
```

---

### Task 13: Integrate BackupManager into Settings page

**Files:**
- Modify: `web/src/pages/SettingsPage.vue`

**Step 1: Add BackupManager to Settings page**

Add import and component to Settings page:

```vue
<script setup lang="ts">
import BackupManager from '@/components/BackupManager.vue'
// ... existing imports
</script>

<template>
  <div class="space-y-8">
    <!-- Existing settings sections -->
    
    <!-- Data Management Section -->
    <section class="space-y-4">
      <h2 class="text-xl font-bold">{{ t('settings.data_management') }}</h2>
      <BackupManager />
    </section>
  </div>
</template>
```

**Step 2: Verify UI renders**

Run: `cd web && pnpm dev`
Navigate to Settings page
Expected: Data Management section visible with backup controls

**Step 3: Commit**

```bash
git add web/src/pages/SettingsPage.vue
git commit -m "feat(web): integrate BackupManager into Settings page"
```

---

## Phase 4: Tauri Commands (Desktop)

### Task 14: Add Tauri export_backup command

**Files:**
- Modify: `src-tauri/src/commands.rs`
- Modify: `src-tauri/src/lib.rs`

**Step 1: Add export_backup command**

Add to `src-tauri/src/commands.rs`:

```rust
use tauri::api::dialog::blocking::FileDialogBuilder;

#[derive(Serialize)]
pub struct ExportBackupResult {
    pub path: String,
}

#[command]
pub async fn export_backup(
    app: AppHandle,
    include_feed_items: bool,
    include_preview_contents: bool,
    include_logs: bool,
) -> Result<ExportBackupResult, String> {
    // Generate default filename
    let version = env!("CARGO_PKG_VERSION");
    let date = chrono::Local::now().format("%Y-%m-%d");
    let default_name = format!("rss-backup-v{}-{}.zip", version, date);
    
    // Open save dialog
    let path = FileDialogBuilder::new()
        .set_file_name(&default_name)
        .add_filter("Backup", &["zip"])
        .save_file()
        .ok_or("No file selected")?;
    
    // Call backend API to get backup data
    let client = reqwest::Client::new();
    let form = reqwest::multipart::Form::new()
        .text("include_feed_items", include_feed_items.to_string())
        .text("include_preview_contents", include_preview_contents.to_string())
        .text("include_logs", include_logs.to_string());
    
    let response = client
        .post("http://127.0.0.1:8000/api/v1/backup/export")
        .multipart(form)
        .send()
        .await
        .map_err(|e| format!("Failed to call backend: {}", e))?;
    
    let bytes = response.bytes().await
        .map_err(|e| format!("Failed to read response: {}", e))?;
    
    // Write to file
    std::fs::write(&path, bytes)
        .map_err(|e| format!("Failed to write file: {}", e))?;
    
    Ok(ExportBackupResult {
        path: path.to_string_lossy().to_string(),
    })
}
```

**Step 2: Register command in lib.rs**

Add to `src-tauri/src/lib.rs`:

```rust
.invoke_handler(tauri::generate_handler![
    // ... existing commands
    commands::export_backup,
    commands::import_backup,
    commands::preview_backup,
])
```

**Step 3: Add required dependencies**

Add to `src-tauri/Cargo.toml`:

```toml
[dependencies]
chrono = "0.4"
reqwest = { version = "0.11", features = ["multipart"] }
zip = "0.6"
```

**Step 4: Commit**

```bash
git add src-tauri/src/commands.rs src-tauri/src/lib.rs src-tauri/Cargo.toml
git commit -m "feat(tauri): add export_backup command"
```

---

### Task 15: Add Tauri import_backup command

**Files:**
- Modify: `src-tauri/src/commands.rs`

**Step 1: Add import_backup command**

Add to `src-tauri/src/commands.rs`:

```rust
#[derive(Serialize, Deserialize)]
pub struct ImportSummary {
    pub sources_imported: i32,
    pub sources_merged: i32,
    pub feed_items_imported: i32,
    pub api_keys_imported: i32,
}

#[derive(Serialize, Deserialize)]
pub struct ImportResult {
    pub success: bool,
    pub message: String,
    pub summary: Option<ImportSummary>,
}

#[command]
pub async fn import_backup(
    app: AppHandle,
) -> Result<ImportResult, String> {
    // Open file dialog
    let path = FileDialogBuilder::new()
        .add_filter("Backup", &["zip"])
        .pick_file()
        .ok_or("No file selected")?;
    
    // Read file
    let bytes = std::fs::read(&path)
        .map_err(|e| format!("Failed to read file: {}", e))?;
    
    // Send to backend
    let client = reqwest::Client::new();
    let file_part = reqwest::multipart::Part::bytes(bytes)
        .file_name(path.file_name().unwrap().to_string_lossy().to_string())
        .mime_str("application/zip")
        .map_err(|e| format!("Failed to create multipart: {}", e))?;
    
    let form = reqwest::multipart::Form::new()
        .part("file", file_part);
    
    let response = client
        .post("http://127.0.0.1:8000/api/v1/backup/import")
        .multipart(form)
        .send()
        .await
        .map_err(|e| format!("Failed to call backend: {}", e))?;
    
    let result: ImportResult = response.json().await
        .map_err(|e| format!("Failed to parse response: {}", e))?;
    
    Ok(result)
}
```

**Step 2: Commit**

```bash
git add src-tauri/src/commands.rs
git commit -m "feat(tauri): add import_backup command"
```

---

### Task 16: Add Tauri preview_backup command

**Files:**
- Modify: `src-tauri/src/commands.rs`

**Step 1: Add preview_backup command**

Add to `src-tauri/src/commands.rs`:

```rust
#[derive(Serialize, Deserialize)]
pub struct BackupPreview {
    pub version: String,
    pub exported_at: String,
    pub counts: BackupCounts,
    pub config: BackupConfig,
}

#[derive(Serialize, Deserialize)]
pub struct BackupCounts {
    pub sources: i32,
    pub feed_items: i32,
    pub api_keys: i32,
    pub preview_contents: i32,
}

#[derive(Serialize, Deserialize)]
pub struct BackupConfig {
    pub timezone: String,
    pub language: String,
}

#[command]
pub async fn preview_backup(
    app: AppHandle,
) -> Result<BackupPreview, String> {
    // Open file dialog
    let path = FileDialogBuilder::new()
        .add_filter("Backup", &["zip"])
        .pick_file()
        .ok_or("No file selected")?;
    
    // Read file
    let bytes = std::fs::read(&path)
        .map_err(|e| format!("Failed to read file: {}", e))?;
    
    // Send to backend
    let client = reqwest::Client::new();
    let file_part = reqwest::multipart::Part::bytes(bytes)
        .file_name(path.file_name().unwrap().to_string_lossy().to_string())
        .mime_str("application/zip")
        .map_err(|e| format!("Failed to create multipart: {}", e))?;
    
    let form = reqwest::multipart::Form::new()
        .part("file", file_part);
    
    let response = client
        .post("http://127.0.0.1:8000/api/v1/backup/preview")
        .multipart(form)
        .send()
        .await
        .map_err(|e| format!("Failed to call backend: {}", e))?;
    
    let preview: BackupPreview = response.json().await
        .map_err(|e| format!("Failed to parse response: {}", e))?;
    
    Ok(preview)
}
```

**Step 2: Commit**

```bash
git add src-tauri/src/commands.rs
git commit -m "feat(tauri): add preview_backup command"
```

---

### Task 17: Update frontend to use Tauri commands on desktop

**Files:**
- Modify: `web/src/components/BackupManager.vue`
- Modify: `web/src/utils/environment.ts`

**Step 1: Add desktop detection**

Add to `web/src/utils/environment.ts`:

```typescript
export function isDesktop(): boolean {
  return typeof window !== 'undefined' && '__TAURI__' in window
}
```

**Step 2: Update BackupManager for Tauri**

Update `web/src/components/BackupManager.vue`:

```vue
<script setup lang="ts">
import { isDesktop } from '@/utils/environment'

// Add Tauri imports conditionally
let tauriInvoke: any = null
if (isDesktop()) {
  tauriInvoke = (await import('@tauri-apps/api/tauri')).invoke
}

async function handleExport() {
  isExporting.value = true
  try {
    if (isDesktop() && tauriInvoke) {
      // Desktop: use Tauri command
      const result = await tauriInvoke('export_backup', {
        includeFeedItems: includeFeedItems.value,
        includePreviewContents: includePreviewContents.value,
        includeLogs: includeLogs.value,
      })
      toast.success(`${t('settings.export_success')}: ${result.path}`)
    } else {
      // Web: use REST API
      const blob = await exportBackup({
        include_feed_items: includeFeedItems.value,
        include_preview_contents: includePreviewContents.value,
        include_logs: includeLogs.value,
      })
      
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `rss-backup-${new Date().toISOString().split('T')[0]}.zip`
      a.click()
      URL.revokeObjectURL(url)
      
      toast.success(t('settings.export_success'))
    }
  } catch (error) {
    toast.error('Export failed')
  } finally {
    isExporting.value = false
  }
}

// Similar updates for import and preview...
</script>
```

**Step 3: Commit**

```bash
git add web/src/components/BackupManager.vue web/src/utils/environment.ts
git commit -m "feat(web): use Tauri commands on desktop platform"
```

---

## Phase 5: E2E Tests

### Task 18: Add Playwright E2E test for backup export

**Files:**
- Create: `web/e2e/backup.spec.ts`

**Step 1: Write E2E test**

Create `web/e2e/backup.spec.ts`:

```typescript
import { test, expect } from '@playwright/test'

test.describe('Backup Feature', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/')
    // Login if needed
    // Navigate to settings
    await page.click('[data-testid="nav-settings"]')
  })

  test('should export backup successfully', async ({ page }) => {
    // Find export button
    await page.click('text=Export Backup')
    
    // Wait for download
    const [download] = await Promise.all([
      page.waitForEvent('download'),
      page.click('button:has-text("Export Backup")'),
    ])
    
    expect(download.suggestedFilename()).toMatch(/rss-backup-v\d+\.\d+\.\d+-\d{4}-\d{2}-\d{2}\.zip/)
  })

  test('should show export options', async ({ page }) => {
    await expect(page.locator('text=Include RSS Items')).toBeVisible()
    await expect(page.locator('text=Include Article Previews')).toBeVisible()
    await expect(page.locator('text=Include Fetch Logs')).toBeVisible()
  })
})
```

**Step 2: Run E2E test**

Run: `cd web && pnpm test:e2e backup.spec.ts`
Expected: Tests PASS

**Step 3: Commit**

```bash
git add web/e2e/backup.spec.ts
git commit -m "test(e2e): add backup export E2E test"
```

---

## Phase 6: Documentation

### Task 19: Update README with backup feature

**Files:**
- Modify: `README.md`
- Modify: `CHANGELOG.md`

**Step 1: Add feature to README**

Add to Features section in `README.md`:

```markdown
- **Backup and Restore** - Export/import encrypted JSON backups with migration support
```

Add new section:

```markdown
## Backup and Restore

### Export Backup

1. Go to Settings > Data Management
2. Select options (RSS items, article previews, logs)
3. Click "Export Backup"
4. Encrypted ZIP file will be downloaded

### Import Backup

1. Go to Settings > Data Management
2. Click "Choose File" and select backup ZIP
3. Preview backup content
4. Click "Confirm Import"

### Backup Password

Backup files are encrypted with a password. Set via environment variable:

```bash
export BACKUP_PASSWORD=your_password
```

Default password: `kimhsiao`

### Backup File Format

- JSON format with all database content
- Encrypted as ZIP with AES-256
- Filename: `rss-backup-v{version}-{date}.zip`
```

**Step 2: Update CHANGELOG**

Add to `CHANGELOG.md`:

```markdown
## [Unreleased]

### Added
- Backup and restore functionality with encrypted ZIP files
- Migration support between machines and versions
- Data merge on restore (backup takes priority)
```

**Step 3: Commit**

```bash
git add README.md CHANGELOG.md
git commit -m "docs: add backup feature documentation"
```

---

## Task 20: Final commit and version bump

**Step 1: Run all tests**

Run:
```bash
# Backend tests
uv run pytest

# Frontend tests
cd web && pnpm test

# E2E tests
cd web && pnpm test:e2e
```

**Step 2: Update version**

Update version in:
- `pyproject.toml`
- `package.json`
- `src-tauri/tauri.conf.json`
- `src-tauri/Cargo.toml`

**Step 3: Create release commit**

```bash
git add -A
git commit -m "release: v0.11.0 - add backup and restore feature"
git tag v0.11.0
```

---

## Summary

This plan covers:

1. **Backend Service** (Tasks 1-7): Password provider, schemas, serialization, encryption, merge logic
2. **REST API** (Tasks 8-9): Export, import, preview endpoints
3. **Frontend UI** (Tasks 10-13): API client, i18n, BackupManager component
4. **Tauri Commands** (Tasks 14-17): Desktop-specific file dialogs
5. **E2E Tests** (Task 18): Playwright tests
6. **Documentation** (Tasks 19-20): README, CHANGELOG updates