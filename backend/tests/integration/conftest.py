# =========================
# backend/tests/integration/conftest.py
# =========================
"""Shared fixtures for integration tests."""

import pytest
from starlette.testclient import TestClient
from app.main import create_app
import httpx


@pytest.fixture
def client():
    """Create test client."""
    app = create_app(enable_trading_worker=False)
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def async_client():
    """Async client for ASGI app using anyio pytest plugin."""
    app = create_app(enable_trading_worker=False)
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture
def tenant_id():
    """Default tenant ID for tests."""
    return "default"


@pytest.fixture
def portfolio_id(client, tenant_id):
    """Create a test portfolio and return its ID."""
    import uuid

    unique_suffix = uuid.uuid4().hex[:8]
    response = client.post(
        f"/v1/tenants/{tenant_id}/portfolios",
        json={
            "name": f"Test Portfolio {unique_suffix}",
            "type": "LIVE",
            "template": "DEFAULT",
            "hours_policy": "OPEN_ONLY",
        },
    )
    if response.status_code != 201:
        try:
            print(response.json())
        except ValueError:
            print(response.text)
    assert response.status_code == 201
    return response.json()["portfolio_id"]


@pytest.fixture
def position_id(client, tenant_id, portfolio_id):
    """Create a position in the test portfolio and return its ID."""
    response = client.post(
        f"/v1/tenants/{tenant_id}/portfolios/{portfolio_id}/positions",
        json={
            "asset": "AAPL",
            "qty": 100.0,
            "anchor_price": 150.0,
            "starting_cash": {"currency": "USD", "amount": 10000.0},
        },
    )
    if response.status_code != 201:
        try:
            print(response.json())
        except ValueError:
            print(response.text)
    assert response.status_code == 201
    return response.json()["position_id"]
