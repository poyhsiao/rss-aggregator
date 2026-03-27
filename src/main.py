"""Main FastAPI application."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.deps import get_scheduler, set_scheduler
from src.api.routes import feed, health, history, keys, logs, previews, sources, stats, trash
from src.config import settings
from src.scheduler.fetch_scheduler import FetchScheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    if settings.scheduler_enabled:
        from src.db.database import async_session_factory

        scheduler = FetchScheduler(
            session_factory=async_session_factory,
            check_interval=settings.scheduler_interval,
        )
        set_scheduler(scheduler)
        await scheduler.start()

    yield

    scheduler = get_scheduler()
    if scheduler:
        await scheduler.stop()


app = FastAPI(
    title="RSS Aggregator",
    description="Aggregate multiple RSS feeds into a single, filterable output",
    version="0.9.3",
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