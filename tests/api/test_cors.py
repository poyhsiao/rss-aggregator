# import pytest
from fastapi.testclient import TestClient
from src.main import app


def test_cors_requires_explicit_origins():
    """When allow_credentials=True, allow_origins cannot be ['*'].

    Browsers reject CORS responses where allow_origins='*' with allow_credentials=True.
    The app must use explicit, non-wildcard origins from ALLOWED_ORIGINS env var.
    """
    client = TestClient(app)
    # Request with a non-whitelisted origin
    response = client.options(
        "/",
        headers={
            "Origin": "http://localhost:8080",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 200
    allow_origin = response.headers.get("access-control-allow-origin", "")
    # With credentials=True, the server must NOT reply with "*"
    assert allow_origin != "*", (
        f"CORS misconfiguration: allow_origins='*' with allow_credentials=True is rejected by browsers. "
        f"Got allow_origin={allow_origin!r}"
    )
