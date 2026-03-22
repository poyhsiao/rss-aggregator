"""JSON-RPC 2.0 protocol implementation."""

import json
from dataclasses import dataclass
from typing import Any


class JSONRPCError(Exception):
    """JSON-RPC error."""

    def __init__(self, code: int, message: str, data: Any = None) -> None:
        self.code = code
        self.message = message
        self.data = data
        super().__init__(message)


class ParseError(JSONRPCError):
    """Invalid JSON was received."""

    def __init__(self, data: Any = None) -> None:
        super().__init__(-32700, "Parse error", data)


class InvalidRequest(JSONRPCError):
    """The JSON sent is not a valid Request object."""

    def __init__(self, data: Any = None) -> None:
        super().__init__(-32600, "Invalid Request", data)


class MethodNotFound(JSONRPCError):
    """The method does not exist / is not available."""

    def __init__(self, data: Any = None) -> None:
        super().__init__(-32601, "Method not found", data)


class InvalidParams(JSONRPCError):
    """Invalid method parameter(s)."""

    def __init__(self, data: Any = None) -> None:
        super().__init__(-32602, "Invalid params", data)


class InternalError(JSONRPCError):
    """Internal JSON-RPC error."""

    def __init__(self, data: Any = None) -> None:
        super().__init__(-32603, "Internal error", data)


@dataclass
class JSONRPCRequest:
    """JSON-RPC 2.0 request."""

    jsonrpc: str
    method: str
    params: dict[str, Any] | None = None
    id: int | str | None = None


@dataclass
class JSONRPCResponse:
    """JSON-RPC 2.0 response."""

    jsonrpc: str = "2.0"
    result: dict[str, Any] | None = None
    error: dict[str, Any] | None = None
    id: int | str | None = None


def parse_request(raw: str) -> JSONRPCRequest:
    """Parse JSON-RPC request from string.

    Args:
        raw: Raw JSON string.

    Returns:
        Parsed JSON-RPC request.

    Raises:
        ParseError: If JSON is invalid.
        InvalidRequest: If request is not valid JSON-RPC.
    """
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ParseError({"detail": str(e)}) from e

    if not isinstance(data, dict):
        raise InvalidRequest({"detail": "Request must be an object"})

    if data.get("jsonrpc") != "2.0":
        raise InvalidRequest({"detail": "jsonrpc version must be 2.0"})

    if "method" not in data:
        raise InvalidRequest({"detail": "method is required"})

    if not isinstance(data["method"], str):
        raise InvalidRequest({"detail": "method must be a string"})

    return JSONRPCRequest(
        jsonrpc=data["jsonrpc"],
        method=data["method"],
        params=data.get("params"),
        id=data.get("id"),
    )


def serialize_response(response: JSONRPCResponse) -> str:
    """Serialize JSON-RPC response to string.

    Args:
        response: JSON-RPC response object.

    Returns:
        JSON string.
    """
    return json.dumps(
        {
            "jsonrpc": response.jsonrpc,
            "result": response.result,
            "error": response.error,
            "id": response.id,
        },
        ensure_ascii=False,
    )


def create_success_response(
    result: dict[str, Any], request_id: int | str | None
) -> JSONRPCResponse:
    """Create success JSON-RPC response.

    Args:
        result: Result data.
        request_id: Request ID.

    Returns:
        JSON-RPC response.
    """
    return JSONRPCResponse(result=result, id=request_id)


def create_error_response(
    error: JSONRPCError, request_id: int | str | None
) -> JSONRPCResponse:
    """Create error JSON-RPC response.

    Args:
        error: JSON-RPC error.
        request_id: Request ID.

    Returns:
        JSON-RPC response.
    """
    error_data = {"code": error.code, "message": error.message}
    if error.data is not None:
        error_data["data"] = error.data

    return JSONRPCResponse(error=error_data, id=request_id)
