"""Router for JSON-RPC requests to existing API handlers."""

import base64
import re
from typing import Any

from fastapi import HTTPException

from src.api.deps import (
    get_auth_service,
    get_backup_service,
    get_feed_service,
    get_fetch_service,
    get_history_service,
    get_preview_service,
    get_session,
    get_source_service,
)
from src.api.routes import feed, health, keys, logs, sources, stats
from src.config import settings
from src.schemas.history import UpdateBatchNameRequest
from src.db.database import async_session_factory
from src.models.fetch_log import FetchLog
from src.scheduler.fetch_scheduler import FetchScheduler
from src.stdio.protocol import (
    InternalError,
    InvalidParams,
    JSONRPCRequest,
    JSONRPCResponse,
    MethodNotFound,
    create_error_response,
    create_success_response,
)


class StdioRouter:
    """Route JSON-RPC requests to existing API handlers."""

    def __init__(self) -> None:
        self._scheduler: FetchScheduler | None = None

    def set_scheduler(self, scheduler: FetchScheduler) -> None:
        """Set scheduler instance."""
        self._scheduler = scheduler

    async def _create_log(
        self,
        session: Any,
        source_id: int | None,
        status: str,
        log_type: str,
        message: str,
        items_count: int | None = None,
    ) -> None:
        log = FetchLog(
            source_id=source_id,
            status=status,
            log_type=log_type,
            message=message,
            items_count=items_count,
        )
        session.add(log)

    async def route(self, request: JSONRPCRequest) -> JSONRPCResponse:
        """Route JSON-RPC request to appropriate handler.

        Args:
            request: JSON-RPC request.

        Returns:
            JSON-RPC response.
        """
        try:
            method, path = self._parse_method(request.method)
            params = request.params or {}

            headers = params.get("headers", {})
            query = params.get("query", {})
            body = params.get("body")

            result = await self._execute_handler(
                method, path, headers, query, body
            )

            return create_success_response(result, request.id)

        except MethodNotFound as e:
            return create_error_response(e, request.id)
        except InvalidParams as e:
            return create_error_response(e, request.id)
        except HTTPException as e:
            error = InternalError(
                {
                    "status": e.status_code,
                    "detail": e.detail,
                }
            )
            return create_error_response(error, request.id)
        except Exception as e:
            error = InternalError({"detail": str(e)})
            return create_error_response(error, request.id)

    def _parse_method(self, method: str) -> tuple[str, str]:
        """Parse HTTP method and path from method string.

        Args:
            method: Method string in format "METHOD /path".

        Returns:
            Tuple of (http_method, path).

        Raises:
            MethodNotFound: If method format is invalid.
        """
        parts = method.split(" ", 1)
        if len(parts) != 2:
            raise MethodNotFound({"detail": f"Invalid method format: {method}"})

        http_method, path = parts
        http_method = http_method.upper()

        valid_methods = {"GET", "POST", "PUT", "DELETE", "PATCH"}
        if http_method not in valid_methods:
            raise MethodNotFound({"detail": f"Invalid HTTP method: {http_method}"})

        return http_method, path

    async def _execute_handler(
        self,
        http_method: str,
        path: str,
        headers: dict[str, str],
        query: dict[str, Any],
        body: Any,
    ) -> dict[str, Any]:
        """Execute the appropriate handler.

        Args:
            http_method: HTTP method.
            path: Request path.
            headers: Request headers.
            query: Query parameters.
            body: Request body.

        Returns:
            Response data with status, headers, and body.

        Raises:
            MethodNotFound: If route not found.
            InvalidParams: If parameters are invalid.
            HTTPException: If handler raises HTTP exception.
        """
        if path == "/health" and http_method == "GET":
            result = await health.health_check()
            return {"status": 200, "headers": {}, "body": result}

        async with async_session_factory() as session:
            await self._validate_api_key(headers, session)

            if path == "/api/v1/feed" and http_method == "GET":
                return await self._handle_get_feed(query, session)

            if path == "/api/v1/sources" and http_method == "GET":
                return await self._handle_list_sources(session)

            if path == "/api/v1/sources" and http_method == "POST":
                return await self._handle_create_source(body, session)

            if path == "/api/v1/sources/refresh" and http_method == "POST":
                return await self._handle_refresh_all_sources(session)

            if path.startswith("/api/v1/sources/") and path.endswith("/refresh") and http_method == "POST":
                return await self._handle_refresh_source(path, session)

            if path.startswith("/api/v1/sources/") and path.endswith("/feed") and http_method == "GET":
                return await self._handle_get_source_feed(path, query, session)

            if path.startswith("/api/v1/sources/") and http_method == "GET":
                return await self._handle_get_source(path, session)

            if path.startswith("/api/v1/sources/") and http_method == "PUT":
                return await self._handle_update_source(path, body, session)

            if path.startswith("/api/v1/sources/") and http_method == "DELETE":
                return await self._handle_delete_source(path, session)

            if path == "/api/v1/keys" and http_method == "GET":
                return await self._handle_list_keys(session)

            if path == "/api/v1/keys" and http_method == "POST":
                return await self._handle_create_key(body, session)

            if path.startswith("/api/v1/keys/") and http_method == "DELETE":
                return await self._handle_delete_key(path, session)

            if path == "/api/v1/stats" and http_method == "GET":
                return await self._handle_get_stats(query, session)

            if path == "/api/v1/logs" and http_method == "GET":
                return await self._handle_get_logs(query, session)

            if path == "/api/v1/history/batches" and http_method == "GET":
                return await self._handle_get_history_batches(query, session)

            if re.match(r"^/api/v1/history/batches/\d+$", path) and http_method == "GET":
                return await self._handle_get_history_by_batch(path, query, session)

            if re.match(r"^/api/v1/history/batches/\d+/name$", path) and http_method == "PATCH":
                return await self._handle_update_batch_name(path, body, session)

            if re.match(r"^/api/v1/history/batches/\d+$", path) and http_method == "DELETE":
                return await self._handle_delete_batch(path, session)

            if path == "/api/v1/previews/fetch" and http_method == "POST":
                return await self._handle_fetch_preview(body, session)

            if path.startswith("/api/v1/previews/") and http_method == "GET":
                return await self._handle_get_preview_by_hash(path, session)

            if path == "/api/v1/previews" and http_method == "GET":
                return await self._handle_get_preview_by_url(query, session)

            if path == "/api/v1/previews" and http_method == "POST":
                return await self._handle_create_preview(body, session)

            if path == "/api/v1/previews" and http_method == "DELETE":
                return await self._handle_delete_all_previews(session)

            if path == "/api/v1/backup/export" and http_method == "POST":
                return await self._handle_export_backup(body, session)

            if path == "/api/v1/backup/import" and http_method == "POST":
                return await self._handle_import_backup(body, session)

            if path == "/api/v1/backup/preview" and http_method == "POST":
                return await self._handle_preview_backup(body, session)

            raise MethodNotFound({"detail": f"Route not found: {http_method} {path}"})

    async def _validate_api_key(
        self, headers: dict[str, str], session: Any
    ) -> None:
        """Validate API key from headers.

        Args:
            headers: Request headers.
            session: Database session.

        Raises:
            HTTPException: If API key is invalid.
        """
        if not settings.require_api_key:
            return

        api_key = headers.get("X-API-Key")
        if not api_key:
            raise HTTPException(status_code=401, detail="API key required")

        auth_service = await get_auth_service(session)
        if not await auth_service.validate_key(api_key):
            raise HTTPException(status_code=401, detail="Invalid API key")

    async def _handle_get_feed(
        self, query: dict[str, Any], session: Any
    ) -> dict[str, Any]:
        """Handle GET /api/v1/feed."""
        feed_service = await get_feed_service(session)

        format_val = query.get("format", "rss")
        sort_by = query.get("sort_by", "published_at")
        sort_order = query.get("sort_order", "desc")
        valid_time = query.get("valid_time")
        keywords = query.get("keywords")
        source_id = query.get("source_id")

        # For JSON format, return parsed objects instead of JSON string
        if format_val == "json":
            items = await feed_service.get_feed_items(
                sort_by=sort_by,
                sort_order=sort_order,
                valid_time=valid_time,
                keywords=keywords,
            )
            return {
                "status": 200,
                "headers": {"content-type": "application/json"},
                "body": items,
            }

        content, content_type = await feed_service.get_formatted_feed(
            format=format_val,
            sort_by=sort_by,
            sort_order=sort_order,
            valid_time=valid_time,
            keywords=keywords,
            source_id=source_id,
        )

        return {
            "status": 200,
            "headers": {"content-type": content_type},
            "body": content,
        }

    async def _handle_list_sources(self, session: Any) -> dict[str, Any]:
        """Handle GET /api/v1/sources."""
        source_service = await get_source_service(session)
        sources = await source_service.get_sources()

        from src.utils.time import to_iso_string

        body = [
            {
                "id": s.id,
                "name": s.name,
                "url": s.url,
                "is_active": s.is_active,
                "last_fetched_at": to_iso_string(s.last_fetched_at),
                "last_error": s.last_error,
                "created_at": to_iso_string(s.created_at) or "",
                "updated_at": to_iso_string(s.updated_at) or "",
            }
            for s in sources
        ]

        return {"status": 200, "headers": {}, "body": body}

    async def _handle_create_source(
        self, body: Any, session: Any
    ) -> dict[str, Any]:
        """Handle POST /api/v1/sources."""
        if not body:
            raise InvalidParams({"detail": "Request body is required"})

        source_service = await get_source_service(session)

        try:
            source = await source_service.create_source(
                name=body["name"],
                url=body["url"],
            )
            await self._create_log(
                session,
                source_id=source.id,
                status="success",
                log_type="source_created",
                message=f"Source '{source.name}' created with URL: {source.url}",
            )
            await session.commit()
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e

        from src.utils.time import to_iso_string

        result_body = {
            "id": source.id,
            "name": source.name,
            "url": source.url,
            "is_active": source.is_active,
            "last_fetched_at": None,
            "last_error": None,
            "created_at": to_iso_string(source.created_at) or "",
            "updated_at": to_iso_string(source.updated_at) or "",
        }

        return {"status": 201, "headers": {}, "body": result_body}

    async def _handle_get_source(
        self, path: str, session: Any
    ) -> dict[str, Any]:
        """Handle GET /api/v1/sources/{id}."""
        source_id = self._extract_path_param(path, r"/api/v1/sources/(\d+)$")
        source_service = await get_source_service(session)
        source = await source_service.get_source(source_id)

        if not source:
            raise HTTPException(status_code=404, detail="Source not found")

        from src.utils.time import to_iso_string

        body = {
            "id": source.id,
            "name": source.name,
            "url": source.url,
            "is_active": source.is_active,
            "last_fetched_at": to_iso_string(source.last_fetched_at),
            "last_error": source.last_error,
            "created_at": to_iso_string(source.created_at) or "",
            "updated_at": to_iso_string(source.updated_at) or "",
        }

        return {"status": 200, "headers": {}, "body": body}

    async def _handle_update_source(
        self, path: str, body: Any, session: Any
    ) -> dict[str, Any]:
        """Handle PUT /api/v1/sources/{id}."""
        if not body:
            raise InvalidParams({"detail": "Request body is required"})

        source_id = self._extract_path_param(path, r"/api/v1/sources/(\d+)$")
        source_service = await get_source_service(session)

        try:
            source = await source_service.update_source(
                source_id,
                **{k: v for k, v in body.items() if v is not None},
            )
            await self._create_log(
                session,
                source_id=source.id,
                status="success",
                log_type="source_updated",
                message=f"Source '{source.name}' updated",
            )
            await session.commit()
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e)) from e

        from src.utils.time import to_iso_string

        result_body = {
            "id": source.id,
            "name": source.name,
            "url": source.url,
            "is_active": source.is_active,
            "last_fetched_at": to_iso_string(source.last_fetched_at),
            "last_error": source.last_error,
            "created_at": to_iso_string(source.created_at) or "",
            "updated_at": to_iso_string(source.updated_at) or "",
        }

        return {"status": 200, "headers": {}, "body": result_body}

    async def _handle_delete_source(
        self, path: str, session: Any
    ) -> dict[str, Any]:
        """Handle DELETE /api/v1/sources/{id}."""
        source_id = self._extract_path_param(path, r"/api/v1/sources/(\d+)$")
        source_service = await get_source_service(session)

        try:
            source = await source_service.get_source(source_id)
            if not source:
                raise HTTPException(status_code=404, detail="Source not found")

            source_name = source.name
            await source_service.delete_source(source_id)
            await self._create_log(
                session,
                source_id=None,
                status="success",
                log_type="source_deleted",
                message=f"Source '{source_name}' (ID: {source_id}) deleted",
            )
            await session.commit()
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e)) from e

        return {"status": 204, "headers": {}, "body": None}

    async def _handle_refresh_source(self, path: str, session: Any) -> dict[str, Any]:
        """Handle POST /api/v1/sources/{id}/refresh."""
        import json as json_module
        from src.models import FetchBatch
        from src.services.source_service import SourceService
        from src.utils.time import now

        source_id = self._extract_path_param(path, r"/api/v1/sources/(\d+)/refresh$")
        source_service = await get_source_service(session)
        source = await source_service.get_source(source_id)

        if not source:
            raise HTTPException(status_code=404, detail="Source not found")

        if self._scheduler:
            await self._scheduler.refresh_source(source_id)
        else:
            fetch_service = await get_fetch_service(session)
            
            batch = FetchBatch(items_count=0, sources=json_module.dumps([source.name]))
            session.add(batch)
            await session.flush()
            
            items = await fetch_service.fetch_source(source, batch_id=batch.id)
            batch.items_count = len(items)
            
            await session.commit()

        return {"status": 200, "headers": {}, "body": {"message": "Refresh triggered"}}

    async def _handle_refresh_all_sources(self, session: Any) -> dict[str, Any]:
        if self._scheduler:
            await self._scheduler.refresh_all()
        else:
            fetch_service = await get_fetch_service(session)
            await fetch_service.fetch_all()

        return {"status": 200, "headers": {}, "body": {"message": "All sources refresh triggered"}}

    async def _handle_get_source_feed(
        self, path: str, query: dict[str, Any], session: Any
    ) -> dict[str, Any]:
        """Handle GET /api/v1/sources/{id}/feed."""
        source_id = self._extract_path_param(path, r"/api/v1/sources/(\d+)/feed$")
        feed_service = await get_feed_service(session)
        source_service = await get_source_service(session)
        source = await source_service.get_source(source_id)

        if not source:
            raise HTTPException(status_code=404, detail="Source not found")

        format_val = query.get("format", "rss")
        sort_by = query.get("sort_by", "published_at")
        sort_order = query.get("sort_order", "desc")
        valid_time = query.get("valid_time")
        keywords = query.get("keywords")

        # For JSON format, return parsed objects instead of JSON string
        if format_val == "json":
            items = await feed_service.get_feed_items(
                sort_by=sort_by,
                sort_order=sort_order,
                valid_time=valid_time,
                keywords=keywords,
                source_id=source_id,
            )
            return {
                "status": 200,
                "headers": {"content-type": "application/json"},
                "body": items,
            }

        content, content_type = await feed_service.get_formatted_feed(
            format=format_val,
            sort_by=sort_by,
            sort_order=sort_order,
            valid_time=valid_time,
            keywords=keywords,
            source_id=source_id,
        )

        return {
            "status": 200,
            "headers": {"content-type": content_type},
            "body": content,
        }

    async def _handle_list_keys(self, session: Any) -> dict[str, Any]:
        """Handle GET /api/v1/keys."""
        from sqlalchemy import select
        from src.models import APIKey

        result = await session.execute(
            select(APIKey).where(APIKey.deleted_at.is_(None))
        )
        keys = list(result.scalars().all())

        body = [
            {"id": k.id, "key": k.key, "name": k.name, "is_active": k.is_active}
            for k in keys
        ]

        return {"status": 200, "headers": {}, "body": body}

    async def _handle_create_key(
        self, body: Any, session: Any
    ) -> dict[str, Any]:
        """Handle POST /api/v1/keys."""
        import secrets

        from sqlalchemy import select
        from src.models import APIKey

        if not body:
            raise InvalidParams({"detail": "Request body is required"})

        key = body.get("key")
        if not key:
            key = secrets.token_urlsafe(32)

        result = await session.execute(select(APIKey).where(APIKey.key == key))
        if result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Key already exists")

        api_key = APIKey(key=key, name=body.get("name"))
        session.add(api_key)
        await session.commit()
        await session.refresh(api_key)

        result_body = {
            "id": api_key.id,
            "key": api_key.key,
            "name": api_key.name,
            "is_active": api_key.is_active,
        }

        return {"status": 201, "headers": {}, "body": result_body}

    async def _handle_delete_key(self, path: str, session: Any) -> dict[str, Any]:
        """Handle DELETE /api/v1/keys/{id}."""
        from sqlalchemy import select
        from src.models import APIKey

        key_id = self._extract_path_param(path, r"/api/v1/keys/(\d+)$")

        result = await session.execute(
            select(APIKey).where(APIKey.id == key_id, APIKey.deleted_at.is_(None))
        )
        api_key = result.scalar_one_or_none()

        if not api_key:
            raise HTTPException(status_code=404, detail="API key not found")

        api_key.soft_delete()
        await session.commit()

        return {"status": 204, "headers": {}, "body": None}

    async def _handle_get_stats(
        self, query: dict[str, Any], session: Any
    ) -> dict[str, Any]:
        """Handle GET /api/v1/stats."""
        from datetime import date, timedelta
        from sqlalchemy import select
        from src.models import Stats

        days = query.get("days", 7)
        if isinstance(days, str):
            try:
                days = int(days)
            except ValueError:
                raise InvalidParams({"detail": "days must be a valid integer"})

        if not isinstance(days, int) or days < 1 or days > 365:
            raise InvalidParams({"detail": "days must be between 1 and 365"})

        start_date = date.today() - timedelta(days=days)

        result = await session.execute(
            select(Stats)
            .where(Stats.date >= start_date, Stats.deleted_at.is_(None))
            .order_by(Stats.date.desc())
        )
        stats = list(result.scalars().all())

        body = [
            {
                "date": str(s.date),
                "total_requests": s.total_requests,
                "successful_fetches": s.successful_fetches,
                "failed_fetches": s.failed_fetches,
            }
            for s in stats
        ]

        return {"status": 200, "headers": {}, "body": body}

    async def _handle_get_logs(
        self, query: dict[str, Any], session: Any
    ) -> dict[str, Any]:
        """Handle GET /api/v1/logs."""
        from sqlalchemy import select
        from src.models import FetchLog
        from src.utils.time import to_iso_string

        # Convert string params to correct types
        limit = query.get("limit", 100)
        if isinstance(limit, str):
            try:
                limit = int(limit)
            except ValueError:
                raise InvalidParams({"detail": "limit must be a valid integer"})

        source_id = query.get("source_id")
        if source_id is not None and isinstance(source_id, str):
            try:
                source_id = int(source_id)
            except ValueError:
                raise InvalidParams({"detail": "source_id must be a valid integer"})

        status = query.get("status")

        if not isinstance(limit, int) or limit < 1 or limit > 1000:
            raise InvalidParams({"detail": "limit must be between 1 and 1000"})

        if status and status not in ("success", "error"):
            raise InvalidParams({"detail": "status must be 'success' or 'error'"})

        db_query = select(FetchLog).where(FetchLog.deleted_at.is_(None))

        if source_id is not None:
            db_query = db_query.where(FetchLog.source_id == source_id)

        if status is not None:
            db_query = db_query.where(FetchLog.status == status)

        db_query = db_query.order_by(FetchLog.created_at.desc()).limit(limit)

        result = await session.execute(db_query)
        logs = list(result.scalars().all())

        body = [
            {
                "id": log.id,
                "source_id": log.source_id,
                "status": log.status,
                "log_type": log.log_type,
                "message": log.message,
                "items_count": log.items_count,
                "created_at": to_iso_string(log.created_at) or "",
            }
            for log in logs
        ]

        return {"status": 200, "headers": {}, "body": body}

    def _extract_path_param(self, path: str, pattern: str) -> int:
        match = re.match(pattern, path)
        if not match:
            raise InvalidParams({"detail": f"Invalid path format: {path}"})

        try:
            return int(match.group(1))
        except ValueError as e:
            raise InvalidParams({"detail": f"Invalid parameter value: {e}"}) from e

    async def _handle_get_history_batches(
        self, query: dict[str, Any], session: Any
    ) -> dict[str, Any]:
        limit = query.get("limit", 50)
        if isinstance(limit, str):
            try:
                limit = int(limit)
            except ValueError:
                raise InvalidParams({"detail": "limit must be a valid integer"})

        offset = query.get("offset", 0)
        if isinstance(offset, str):
            try:
                offset = int(offset)
            except ValueError:
                raise InvalidParams({"detail": "offset must be a valid integer"})

        if not isinstance(limit, int) or limit < 1 or limit > 100:
            raise InvalidParams({"detail": "limit must be between 1 and 100"})

        if not isinstance(offset, int) or offset < 0:
            raise InvalidParams({"detail": "offset must be >= 0"})

        history_service = await get_history_service(session)
        result = await history_service.get_history_batches(limit=limit, offset=offset)

        body = {
            "batches": [
                {
                    "id": b.id,
                    "items_count": b.items_count,
                    "sources": b.sources,
                    "created_at": b.created_at,
                }
                for b in result.batches
            ],
            "total_batches": result.total_batches,
            "total_items": result.total_items,
        }

        return {"status": 200, "headers": {}, "body": body}

    async def _handle_get_history_by_batch(
        self, path: str, query: dict[str, Any], session: Any
    ) -> dict[str, Any]:
        batch_id = self._extract_path_param(path, r"/api/v1/history/batches/(\d+)$")

        page = query.get("page", 1)
        if isinstance(page, str):
            try:
                page = int(page)
            except ValueError:
                raise InvalidParams({"detail": "page must be a valid integer"})

        page_size = query.get("page_size", 50)
        if isinstance(page_size, str):
            try:
                page_size = int(page_size)
            except ValueError:
                raise InvalidParams({"detail": "page_size must be a valid integer"})

        if not isinstance(page, int) or page < 1:
            raise InvalidParams({"detail": "page must be >= 1"})

        if not isinstance(page_size, int) or page_size < 1 or page_size > 100:
            raise InvalidParams({"detail": "page_size must be between 1 and 100"})

        history_service = await get_history_service(session)
        items, pagination = await history_service.get_history_by_batch(
            batch_id=batch_id,
            page=page,
            page_size=page_size,
        )

        body = {
            "items": [
                {
                    "id": item.id,
                    "source_id": item.source_id,
                    "source": item.source,
                    "title": item.title,
                    "link": item.link,
                    "description": item.description,
                    "published_at": item.published_at,
                    "fetched_at": item.fetched_at,
                }
                for item in items
            ],
            "pagination": {
                "page": pagination.page,
                "page_size": pagination.page_size,
                "total_items": pagination.total_items,
                "total_pages": pagination.total_pages,
            },
        }

        return {"status": 200, "headers": {}, "body": body}

    async def _handle_update_batch_name(
        self, path: str, body: Any, session: Any
    ) -> dict[str, Any]:
        batch_id = self._extract_path_param(
            path, r"/api/v1/history/batches/(\d+)/name$"
        )

        if not body or "name" not in body:
            return {
                "status": 422,
                "headers": {},
                "body": {"detail": "name is required"},
            }

        try:
            request = UpdateBatchNameRequest(name=body["name"])
        except Exception as e:
            return {
                "status": 422,
                "headers": {},
                "body": {"detail": f"Invalid request body: {e}"},
            }

        history_service = await get_history_service(session)
        result = await history_service.update_batch_name(batch_id, request)

        if not result:
            return {
                "status": 404,
                "headers": {},
                "body": {"detail": f"Batch {batch_id} not found"},
            }

        return {
            "status": 200,
            "headers": {},
            "body": {
                "id": result.id,
                "name": result.name,
                "items_count": result.items_count,
                "sources": result.sources,
                "created_at": result.created_at,
                "latest_fetched_at": result.latest_fetched_at,
                "latest_published_at": result.latest_published_at,
            },
        }

    async def _handle_delete_batch(
        self, path: str, session: Any
    ) -> dict[str, Any]:
        batch_id = self._extract_path_param(path, r"/api/v1/history/batches/(\d+)$")

        history_service = await get_history_service(session)
        success = await history_service.delete_batch(batch_id)

        if not success:
            return {
                "status": 404,
                "headers": {},
                "body": {"detail": f"Batch {batch_id} not found"},
            }

        return {"status": 200, "headers": {}, "body": {"success": True}}

    async def _handle_fetch_preview(
        self, body: Any, session: Any
    ) -> dict[str, Any]:
        if not body or "url" not in body:
            raise InvalidParams({"detail": "url is required"})

        preview_service = await get_preview_service(session)
        result = await preview_service.fetch_and_cache(body["url"])

        from src.utils.time import to_iso_string

        return {
            "status": 201,
            "headers": {},
            "body": {
                "id": result.id,
                "url": result.url,
                "url_hash": result.url_hash,
                "markdown_content": result.markdown_content,
                "title": result.title,
                "created_at": to_iso_string(result.created_at) or "",
                "updated_at": to_iso_string(result.updated_at) or "",
            },
        }

    async def _handle_get_preview_by_hash(
        self, path: str, session: Any
    ) -> dict[str, Any]:
        match = re.match(r"/api/v1/previews/([a-f0-9]{64})$", path)
        if not match:
            raise InvalidParams({"detail": f"Invalid path format: {path}"})
        url_hash = match.group(1)

        preview_service = await get_preview_service(session)
        result = await preview_service.get_by_url_hash(url_hash)

        if not result:
            raise HTTPException(status_code=404, detail="Preview not found")

        from src.utils.time import to_iso_string

        return {
            "status": 200,
            "headers": {},
            "body": {
                "id": result.id,
                "url": result.url,
                "url_hash": result.url_hash,
                "markdown_content": result.markdown_content,
                "title": result.title,
                "created_at": to_iso_string(result.created_at) or "",
                "updated_at": to_iso_string(result.updated_at) or "",
            },
        }

    async def _handle_get_preview_by_url(
        self, query: dict[str, Any], session: Any
    ) -> dict[str, Any]:
        url = query.get("url")
        if not url:
            raise InvalidParams({"detail": "url query parameter is required"})

        preview_service = await get_preview_service(session)
        result = await preview_service.get_by_url(url)

        if not result:
            raise HTTPException(status_code=404, detail="Preview not found")

        from src.utils.time import to_iso_string

        return {
            "status": 200,
            "headers": {},
            "body": {
                "id": result.id,
                "url": result.url,
                "url_hash": result.url_hash,
                "markdown_content": result.markdown_content,
                "title": result.title,
                "created_at": to_iso_string(result.created_at) or "",
                "updated_at": to_iso_string(result.updated_at) or "",
            },
        }

    async def _handle_create_preview(
        self, body: Any, session: Any
    ) -> dict[str, Any]:
        if not body:
            raise InvalidParams({"detail": "Request body is required"})

        if "url" not in body or "markdown_content" not in body:
            raise InvalidParams(
                {"detail": "url and markdown_content are required"}
            )

        preview_service = await get_preview_service(session)
        result = await preview_service.upsert(
            url=body["url"],
            markdown_content=body["markdown_content"],
            title=body.get("title"),
        )

        from src.utils.time import to_iso_string

        return {
            "status": 201,
            "headers": {},
            "body": {
                "id": result.id,
                "url": result.url,
                "url_hash": result.url_hash,
                "markdown_content": result.markdown_content,
                "title": result.title,
                "created_at": to_iso_string(result.created_at) or "",
                "updated_at": to_iso_string(result.updated_at) or "",
            },
        }

    async def _handle_delete_all_previews(
        self, session: Any
    ) -> dict[str, Any]:
        preview_service = await get_preview_service(session)
        await preview_service.delete_all()
        return {
            "status": 204,
            "headers": {},
            "body": None,
        }

    async def _handle_export_backup(
        self, body: Any, session: Any
    ) -> dict[str, Any]:
        from src.schemas.backup import ExportOptions

        options = None
        if body:
            options = ExportOptions(
                include_feed_items=body.get("include_feed_items", True),
                include_preview_contents=body.get("include_preview_contents", True),
                include_logs=body.get("include_logs", False),
            )

        backup_service = await get_backup_service(session)
        zip_data = await backup_service.export_backup(options)
        filename = backup_service._generate_backup_filename("0.10.0")

        zip_base64 = base64.b64encode(zip_data).decode("utf-8")

        return {
            "status": 200,
            "headers": {
                "content-type": "application/zip",
                "content-disposition": f'attachment; filename="{filename}"',
                "x-backup-filename": filename,
            },
            "body": {"data": zip_base64, "filename": filename},
        }

    async def _handle_import_backup(
        self, body: Any, session: Any
    ) -> dict[str, Any]:
        if not body or "data" not in body:
            raise InvalidParams({"detail": "Backup data (base64) is required"})

        try:
            zip_data = base64.b64decode(body["data"])
        except Exception as e:
            raise InvalidParams({"detail": f"Invalid base64 data: {e}"}) from e

        backup_service = await get_backup_service(session)
        result = await backup_service.import_backup(zip_data)

        return {
            "status": 200,
            "headers": {},
            "body": {
                "success": result.success,
                "message": result.message,
                "summary": result.summary.model_dump() if result.summary else None,
            },
        }

    async def _handle_preview_backup(
        self, body: Any, session: Any
    ) -> dict[str, Any]:
        if not body or "data" not in body:
            raise InvalidParams({"detail": "Backup data (base64) is required"})

        try:
            zip_data = base64.b64decode(body["data"])
        except Exception as e:
            raise InvalidParams({"detail": f"Invalid base64 data: {e}"}) from e

        backup_service = await get_backup_service(session)
        preview = await backup_service.preview_backup(zip_data)

        if preview is None:
            raise HTTPException(
                status_code=400,
                detail="Failed to parse backup file. Invalid format or wrong password.",
            )

        return {
            "status": 200,
            "headers": {},
            "body": {
                "version": preview.version,
                "exported_at": preview.exported_at,
                "counts": preview.counts.model_dump(),
                "config": preview.config.model_dump(),
            },
        }
