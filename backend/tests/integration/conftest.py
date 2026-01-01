# =========================
# backend/tests/integration/conftest.py
# =========================
"""Shared fixtures for integration tests."""

import pytest
from starlette.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


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
            "starting_cash": {"currency": "USD", "amount": 10000.0},
            "holdings": [{"asset": "AAPL", "qty": 100.0, "anchor_price": 150.0}],
        },
    )
    assert response.status_code == 201
    return response.json()["portfolio_id"]


@pytest.fixture
def position_id(client, tenant_id, portfolio_id):
    """Get the first position ID from the test portfolio."""
    response = client.get(f"/v1/tenants/{tenant_id}/portfolios/{portfolio_id}/positions")
    assert response.status_code == 200
    positions = response.json()
    assert len(positions) > 0, "No positions found in portfolio"
    return positions[0]["id"]
