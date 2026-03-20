from datetime import datetime


def to_iso_string(dt: datetime | None) -> str | None:
    """Convert datetime to ISO 8601 string with Z suffix for UTC.

    Args:
        dt: Datetime object or None.

    Returns:
        ISO 8601 string with Z suffix, or None if input is None.
    """
    if dt is None:
        return None
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")