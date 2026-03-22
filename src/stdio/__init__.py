"""Stdio adapter module for desktop mode.

This module provides JSON-RPC 2.0 communication over stdio for desktop applications.
"""

from src.stdio.protocol import (
    JSONRPCError,
    JSONRPCRequest,
    JSONRPCResponse,
    parse_request,
    serialize_response,
)
from src.stdio.router import StdioRouter
from src.stdio.server import StdioServer

__all__ = [
    "JSONRPCError",
    "JSONRPCRequest",
    "JSONRPCResponse",
    "parse_request",
    "serialize_response",
    "StdioRouter",
    "StdioServer",
]
