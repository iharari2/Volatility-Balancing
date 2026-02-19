# =========================
# backend/tests/conftest.py
# =========================
import glob as globmod
import os
import pytest
import asyncio
import functools
from concurrent.futures import ThreadPoolExecutor
import starlette.concurrency
import fastapi.routing

# Per-worker SQLite for pytest-xdist parallel execution
_worker_id = os.environ.get("PYTEST_XDIST_WORKER", "gw0")

# Make sure tests use in-memory for faster execution
os.environ.setdefault("APP_PERSISTENCE", "memory")
os.environ.setdefault("APP_EVENTS", "memory")
os.environ.setdefault("APP_IDEMPOTENCY", "memory")
os.environ.setdefault("SQL_URL", f"sqlite:///./vb_test_{_worker_id}.sqlite")
os.environ.setdefault("APP_AUTO_CREATE", "1")  # Create tables for portfolio repo
os.environ.setdefault("TICK_DETERMINISTIC", "true")

from starlette.testclient import TestClient
from app.main import create_app
from app.di import container

# Ensure database tables are created for portfolio repo
# (Even with memory persistence, portfolio repo uses SQL)
from infrastructure.persistence.sql.models import get_engine, create_all

sql_url = os.getenv("SQL_URL", "sqlite:///./vb_test.sqlite")
portfolio_engine = get_engine(sql_url)
create_all(portfolio_engine)

_threadpool_executor = ThreadPoolExecutor(max_workers=4)


async def _patched_run_in_threadpool(func, *args, **kwargs):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(
        _threadpool_executor, functools.partial(func, *args, **kwargs)
    )


starlette.concurrency.run_in_threadpool = _patched_run_in_threadpool
fastapi.routing.run_in_threadpool = _patched_run_in_threadpool


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
    app = create_app(enable_trading_worker=False)
    with TestClient(app) as test_client:
        yield test_client


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


@pytest.fixture(scope="session", autouse=True)
def cleanup_worker_dbs():
    """Clean up per-worker SQLite files after the test session."""
    yield
    for db_file in globmod.glob("vb_test_gw*.sqlite"):
        try:
            os.remove(db_file)
        except OSError:
            pass


@pytest.fixture()
def current_price():
    return 15.50


@pytest.fixture()
def ticker():
    return "ZIM"
