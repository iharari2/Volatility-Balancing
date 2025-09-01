# =========================
# backend/tests/conftest.py
# =========================
import os
import pytest

# Make sure tests use SQLite + auto create
os.environ.setdefault("APP_PERSISTENCE", "sql")
os.environ.setdefault("APP_EVENTS", "sql")
os.environ.setdefault("APP_IDEMPOTENCY", "memory")
os.environ.setdefault("SQL_URL", "sqlite:///./vb_test.sqlite")
os.environ.setdefault("APP_AUTO_CREATE", "1")

from starlette.testclient import TestClient
from app.main import app
from app.di import container


@pytest.fixture()
def client():
    return TestClient(app)


@pytest.fixture()
def position_id():
    pos = container.positions.create(ticker="ZIM", qty=0.0, cash=10_000.0)
    return pos.id
