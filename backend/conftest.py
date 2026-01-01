# =========================
# backend/conftest.py
# =========================
import os
import pytest

# Make sure tests use in-memory for faster execution
os.environ.setdefault("APP_PERSISTENCE", "memory")
os.environ.setdefault("APP_EVENTS", "memory")
os.environ.setdefault("APP_IDEMPOTENCY", "memory")
os.environ.setdefault("SQL_URL", "sqlite:///./vb_test.sqlite")
os.environ.setdefault("APP_AUTO_CREATE", "0")

from starlette.testclient import TestClient
from app.main import app
from app.di import container
from tests.fixtures.mock_market_data import MockMarketDataAdapter


@pytest.fixture()
def client():
    # Reset container to ensure clean state
    container.reset()
    # Override market data adapter with mock for fast testing
    container.market_data = MockMarketDataAdapter()
    return TestClient(app)


@pytest.fixture()
def position_id():
    # Create a default portfolio first for test positions
    tenant_id = "default"
    portfolio_id = "test_portfolio"
    # Create portfolio if it doesn't exist
    portfolio = container.portfolio_repo.get(tenant_id=tenant_id, portfolio_id=portfolio_id)
    if not portfolio:
        from domain.entities.portfolio import Portfolio

        portfolio = Portfolio(
            id=portfolio_id,
            tenant_id=tenant_id,
            name="Test Portfolio",
            description="Test portfolio for unit tests",
        )
        container.portfolio_repo.save(portfolio)

    pos = container.positions.create(
        tenant_id=tenant_id,
        portfolio_id=portfolio_id,
        asset_symbol="ZIM",
        qty=0.0,
        anchor_price=None,
    )
    # Set cash on position (cash lives in Position entity)
    pos.cash = 10_000.0
    container.positions.save(pos)
    return pos.id


@pytest.fixture()
def current_price():
    return 15.50


@pytest.fixture()
def ticker():
    return "ZIM"
