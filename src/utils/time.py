"""Time utilities with configurable timezone support."""

from datetime import UTC, datetime
from zoneinfo import ZoneInfo

from src.config import settings


def get_timezone() -> ZoneInfo:
    """Get the configured application timezone.

    Returns:
        ZoneInfo object for the configured timezone.
    """
    return settings.timezone


def now() -> datetime:
    """Return current datetime in configured timezone as naive.

    Returns naive datetime (no tzinfo) for compatibility with SQLite.
    The datetime is in the configured application timezone (default: Asia/Taipei).

    Returns:
        Current datetime in configured timezone without tzinfo.
    """
    return datetime.now(get_timezone()).replace(tzinfo=None)


def utcnow() -> datetime:
    """Return current UTC datetime as naive.

    Returns naive datetime for compatibility with SQLite.
    Use this for RSS standard fields that require UTC.

    Returns:
        Current UTC datetime without tzinfo.
    """
    return datetime.now(UTC).replace(tzinfo=None)


def to_iso_string(dt: datetime | None) -> str:
    """Convert datetime to ISO 8601 string.

    Args:
        dt: Datetime object or None.

    Returns:
        ISO 8601 string, or empty string if input is None.
    """
    if dt is None:
        return ""
    return dt.strftime("%Y-%m-%dT%H:%M:%S")