"""Main FastAPI application."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import Response

from src.api.deps import get_scheduler, set_scheduler
from src.api.routes import feed, health, keys, logs, sources, stats
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
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(health.router)
app.include_router(feed.router, prefix="/api/v1")
app.include_router(sources.router, prefix="/api/v1")
app.include_router(keys.router, prefix="/api/v1")
app.include_router(stats.router, prefix="/api/v1")
app.include_router(logs.router, prefix="/api/v1")


@app.exception_handler(404)
async def not_found_handler(request: Request, exc: Exception) -> Response:
    """Handle 404 errors with empty response."""
    return Response(status_code=404)