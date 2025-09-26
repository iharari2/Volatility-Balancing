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


@pytest.fixture()
def client():
    # Reset container to ensure clean state
    container.reset()
    return TestClient(app)


@pytest.fixture()
def position_id():
    pos = container.positions.create(ticker="ZIM", qty=0.0, cash=10_000.0)
    return pos.id


@pytest.fixture()
def current_price():
    return 15.50


@pytest.fixture()
def ticker():
    return "ZIM"
