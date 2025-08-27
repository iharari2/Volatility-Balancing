# =========================
# backend/tests/conftest.py
# =========================
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.di import container


@pytest.fixture(autouse=True)
def reset_state():
    container.reset()
    yield
    container.reset()


@pytest.fixture()
def client():
    return TestClient(app)


@pytest.fixture()
def position_id():
    pos = container.positions.create(ticker="ZIM", qty=0.0, cash=10000.0)
    return pos.id
