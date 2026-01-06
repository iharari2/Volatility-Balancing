# =========================
# backend/tests/conftest.py
# =========================
import os
import pytest

# Make sure tests use in-memory for faster execution
os.environ.setdefault("APP_PERSISTENCE", "memory")
os.environ.setdefault("APP_EVENTS", "memory")
os.environ.setdefault("APP_IDEMPOTENCY", "memory")
os.environ.setdefault("SQL_URL", "sqlite:///./vb_test.sqlite")
os.environ.setdefault("APP_AUTO_CREATE", "1")  # Create tables for portfolio repo
os.environ.setdefault("TRADING_WORKER_ENABLED", "false")
os.environ.setdefault("TRADING_WORKER_INTERVAL_SECONDS", "3600")

from starlette.testclient import TestClient
from app.main import app
from app.di import container

# Ensure database tables are created for portfolio repo
# (Even with memory persistence, portfolio repo uses SQL)
from infrastructure.persistence.sql.models import get_engine, create_all

sql_url = os.getenv("SQL_URL", "sqlite:///./vb_test.sqlite")
portfolio_engine = get_engine(sql_url)
create_all(portfolio_engine)


@pytest.fixture(autouse=True)
def reset_container():
    """Reset container before each test to ensure clean state."""
    container.reset()
    yield
    # Cleanup after test if needed


@pytest.fixture()
def client():
    # Reset container to ensure clean state
    container.reset()
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
        # Note: Cash is now stored in Position.cash, not PortfolioCash

    pos = container.positions.create(
        tenant_id=tenant_id,
        portfolio_id=portfolio_id,
        asset_symbol="ZIM",
        qty=0.0,
        anchor_price=None,
    )
    return pos.id


@pytest.fixture()
def current_price():
    return 15.50


@pytest.fixture()
def ticker():
    return "ZIM"
