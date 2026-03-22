"""Router for JSON-RPC requests to existing API handlers."""

import re
from typing import Any

from fastapi import HTTPException

from src.api.deps import (
    get_auth_service,
    get_feed_service,
    get_fetch_service,
    get_session,
    get_source_service,
)
from src.api.routes import feed, health, keys, logs, sources, stats
from src.config import settings
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
                "fetch_interval": s.fetch_interval,
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
                fetch_interval=body.get("fetch_interval", 0),
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
            "fetch_interval": source.fetch_interval,
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
            "fetch_interval": source.fetch_interval,
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
            "fetch_interval": source.fetch_interval,
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
        from src.services.source_service import SourceService

        source_id = self._extract_path_param(path, r"/api/v1/sources/(\d+)/refresh$")
        source_service = await get_source_service(session)
        source = await source_service.get_source(source_id)

        if not source:
            raise HTTPException(status_code=404, detail="Source not found")

        if self._scheduler:
            await self._scheduler.refresh_source(source_id)
        else:
            fetch_service = await get_fetch_service(session)
            await fetch_service.fetch_source(source)
            await session.commit()

        return {"status": 200, "headers": {}, "body": {"message": "Refresh triggered"}}

    async def _handle_refresh_all_sources(self, session: Any) -> dict[str, Any]:
        if self._scheduler:
            await self._scheduler.refresh_all()
        else:
            from src.services.source_service import SourceService
            source_service = await get_source_service(session)
            sources = await source_service.get_sources()
            fetch_service = await get_fetch_service(session)
            for source in sources:
                if source.is_active:
                    await fetch_service.fetch_source(source)
            await session.commit()

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
        """Extract path parameter from path using regex.

        Args:
            path: Request path.
            pattern: Regex pattern with capture group.

        Returns:
            Extracted parameter as integer.

        Raises:
            InvalidParams: If parameter cannot be extracted.
        """
        match = re.match(pattern, path)
        if not match:
            raise InvalidParams({"detail": f"Invalid path format: {path}"})

        try:
            return int(match.group(1))
        except ValueError as e:
            raise InvalidParams({"detail": f"Invalid parameter value: {e}"}) from e
