"""API routes package."""

from src.api.routes import app_settings, backup, feed, health, history, keys, logs, previews, source_groups, sources, stats, trash

__all__ = [
    "app_settings",
    "backup",
    "feed",
    "health",
    "history",
    "keys",
    "logs",
    "previews",
    "source_groups",
    "sources",
    "stats",
    "trash",
]