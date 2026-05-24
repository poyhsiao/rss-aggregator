# tests/api/test_global_exception_handler.py
import pytest
from fastapi.testclient import TestClient
from src.main import app


def test_global_exception_handler_returns_json():
    """Unhandled exceptions should return JSON with error details."""
    @app.get("/test-exception")
    async def raise_exception():
        raise ValueError("Test error")

    client = TestClient(app, raise_server_exceptions=False)
    response = client.get("/test-exception")

    assert response.status_code == 500
    json_data = response.json()
    assert "detail" in json_data
    assert json_data["detail"] == "Internal server error"


def test_global_exception_handler_includes_error_type():
    """Exception handler should include the exception type in response."""
    @app.get("/test-exception-type")
    async def raise_type_error():
        raise TypeError("Type error test")

    client = TestClient(app, raise_server_exceptions=False)
    response = client.get("/test-exception-type")

    assert response.status_code == 500
    json_data = response.json()
    assert "type" in json_data
    assert json_data["type"] == "TypeError"