# tests/api/test_backup_version.py
"""Tests for backup version dynamic reading."""
import pytest


def test_backup_version_not_hardcoded_in_route():
    """Backup route should use version from config, not hardcoded string."""
    from src.api.routes import backup

    # Read the source file content
    import inspect
    source = inspect.getsource(backup)

    # The hardcoded "0.10.0" should NOT appear in the route file
    assert '"0.10.0"' not in source, "Version '0.10.0' should not be hardcoded in backup.py"


def test_backup_version_not_hardcoded_in_service():
    """Backup service should use version from config, not hardcoded string."""
    from src.services import backup_service

    # Read the module source
    import inspect
    source = inspect.getsource(backup_service)

    # The hardcoded "0.20.0" should NOT appear in the service file
    assert '"0.20.0"' not in source, "Version '0.20.0' should not be hardcoded in backup_service.py"


def test_config_has_app_version():
    """Config should have app_version attribute."""
    from src.config import get_settings

    settings = get_settings()
    assert hasattr(settings, "app_version"), "Settings should have app_version attribute"
    assert settings.app_version is not None
    assert len(settings.app_version) > 0