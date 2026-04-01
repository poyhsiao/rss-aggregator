"""Main FastAPI application."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.deps import get_scheduler, set_scheduler
from src.api.routes import backup, feed, health, history, keys, logs, previews, source_groups, sources, stats, trash
from src.config import settings
from src.scheduler.fetch_scheduler import FetchScheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    from src.db.database import async_session_factory

    scheduler = FetchScheduler(
        session_factory=async_session_factory,
        check_interval=settings.scheduler_interval,
    )
    set_scheduler(scheduler)

    if settings.scheduler_enabled:
        await scheduler.start()

    yield

    if settings.scheduler_enabled:
        await scheduler.stop()


app = FastAPI(
    title="RSS Aggregator",
    description="Aggregate multiple RSS feeds into a single, filterable output",
    version="0.11.1",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins.split(",") if settings.allowed_origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(feed.router, prefix="/api/v1")
app.include_router(sources.router, prefix="/api/v1")
app.include_router(keys.router, prefix="/api/v1")
app.include_router(stats.router, prefix="/api/v1")
app.include_router(logs.router, prefix="/api/v1")
app.include_router(history.router, prefix="/api/v1")
app.include_router(previews.router, prefix="/api/v1")
app.include_router(trash.router, prefix="/api/v1")
app.include_router(backup.router, prefix="/api/v1")
app.include_router(source_groups.router, prefix="/api/v1")