"""Stdio server for JSON-RPC communication."""

import asyncio
import sys
import traceback

from src.config import settings
from src.scheduler.fetch_scheduler import FetchScheduler
from src.stdio.protocol import (
    InternalError,
    JSONRPCRequest,
    JSONRPCResponse,
    ParseError,
    InvalidRequest,
    parse_request,
    serialize_response,
    create_error_response,
)
from src.stdio.router import StdioRouter


class StdioServer:
    """Stdio server for JSON-RPC communication."""

    def __init__(self) -> None:
        self._router = StdioRouter()
        self._scheduler: FetchScheduler | None = None
        self._running = False

    async def start(self) -> None:
        """Start the stdio server."""
        print("[DEBUG] Starting stdio server...", file=sys.stderr, flush=True)
        print(f"[DEBUG] Database URL: {settings.database_url}", file=sys.stderr, flush=True)
        print(f"[DEBUG] Require API key: {settings.require_api_key}", file=sys.stderr, flush=True)

        await self._init_database()

        if settings.scheduler_enabled:
            from src.db.database import async_session_factory

            self._scheduler = FetchScheduler(
                session_factory=async_session_factory,
                check_interval=settings.scheduler_interval,
            )
            self._router.set_scheduler(self._scheduler)
            await self._scheduler.start()

        self._running = True
        print("[DEBUG] Server ready, entering run loop", file=sys.stderr, flush=True)
        await self._run_loop()

    async def _init_database(self) -> None:
        """Initialize database tables and run migrations."""
        print("[DEBUG] Initializing database...", file=sys.stderr, flush=True)
        from src.db.database import engine
        from src.models import Base

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            await self._run_migrations(conn)
        print("[DEBUG] Database tables created", file=sys.stderr, flush=True)

        await self._init_default_sources()

    async def _run_migrations(self, conn) -> None:
        """Run manual migrations for existing databases."""
        from sqlalchemy import text

        result = await conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name='fetch_batches'")
        )
        if result.fetchone() is None:
            print("[DEBUG] Creating fetch_batches table...", file=sys.stderr, flush=True)
            await conn.execute(
                text("""
                    CREATE TABLE fetch_batches (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        items_count INTEGER NOT NULL,
                        sources TEXT NOT NULL,
                        notes VARCHAR(500),
                        created_at DATETIME NOT NULL,
                        updated_at DATETIME NOT NULL,
                        deleted_at DATETIME
                    )
                """)
            )

        result = await conn.execute(
            text("PRAGMA table_info(feed_items)")
        )
        columns = {row[1] for row in result.fetchall()}
        if "batch_id" not in columns:
            print("[DEBUG] Adding batch_id column to feed_items...", file=sys.stderr, flush=True)
            await conn.execute(
                text("ALTER TABLE feed_items ADD COLUMN batch_id INTEGER")
            )

    async def _init_default_sources(self) -> None:
        from src.db.database import async_session_factory
        from src.services.source_service import SourceService

        if not settings.default_sources:
            return

        async with async_session_factory() as session:
            source_service = SourceService(session)
            existing = await source_service.get_sources()
            if existing:
                print("[DEBUG] Sources already exist, skipping default sources", file=sys.stderr, flush=True)
                return

            sources_config = settings.default_sources.split(",")
            for source_str in sources_config:
                source_str = source_str.strip()
                if not source_str:
                    continue
                parts = source_str.split("|")
                if len(parts) >= 2:
                    name = parts[0].strip()
                    url = parts[1].strip()
                    fetch_interval = int(parts[2]) if len(parts) > 2 else 900
                    try:
                        await source_service.create_source(name, url, fetch_interval)
                        print(f"[DEBUG] Created default source: {name}", file=sys.stderr, flush=True)
                    except ValueError as e:
                        print(f"[DEBUG] Failed to create source: {e}", file=sys.stderr, flush=True)

    async def stop(self) -> None:
        """Stop the stdio server."""
        self._running = False

        if self._scheduler:
            await self._scheduler.stop()

    async def _run_loop(self) -> None:
        """Main server loop."""
        while self._running:
            try:
                line = await self._read_line()
                if not line:
                    break

                response = await self._process_request(line)
                await self._write_response(response)

            except Exception as e:
                error_msg = f"{e}\n{traceback.format_exc()}"
                print(f"[DEBUG] Error in run loop: {error_msg}", file=sys.stderr, flush=True)
                error_response = create_error_response(
                    InternalError({"detail": str(e)}), None
                )
                await self._write_response(error_response)

    async def _read_line(self) -> str | None:
        """Read a line from stdin.

        Returns:
            Line from stdin, or None if EOF.
        """
        loop = asyncio.get_event_loop()
        line = await loop.run_in_executor(None, sys.stdin.readline)

        if not line:
            return None

        return line.strip()

    async def _write_response(self, response: JSONRPCResponse) -> None:
        """Write response to stdout.

        Args:
            response: JSON-RPC response.
        """
        loop = asyncio.get_event_loop()
        serialized = serialize_response(response)
        await loop.run_in_executor(None, lambda: print(serialized, flush=True))

    async def _process_request(self, raw: str) -> JSONRPCResponse:
        """Process a JSON-RPC request.

        Args:
            raw: Raw JSON string.

        Returns:
            JSON-RPC response.
        """
        print(f"[DEBUG] Processing request: {raw[:200]}", file=sys.stderr, flush=True)
        try:
            request = parse_request(raw)
        except ParseError as e:
            return create_error_response(e, None)
        except InvalidRequest as e:
            return create_error_response(e, None)

        try:
            result = await self._router.route(request)
            print(f"[DEBUG] Request processed successfully", file=sys.stderr, flush=True)
            return result
        except Exception as e:
            error_msg = f"{e}\n{traceback.format_exc()}"
            print(f"[DEBUG] Router error: {error_msg}", file=sys.stderr, flush=True)
            return create_error_response(InternalError({"detail": str(e)}), request.id)
