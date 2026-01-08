import os

import pytest
from fastapi import HTTPException

from app.di import container
from app.routes.market import get_market_price


class StubMarketData:
    def __init__(self, result, error_kind=None):
        self._result = result
        self.last_error_kind = error_kind

    def clear_cache(self, ticker=None):
        return None

    def get_price(self, ticker, force_refresh=False):
        return self._result

    def validate_price(self, price_data, allow_after_hours=True):
        return {"valid": True, "warnings": [], "rejections": []}


class DummyResponse:
    def __init__(self, detail):
        self._detail = detail

    def json(self):
        return {"detail": self._detail}


def test_market_price_invalid_ticker_returns_404():
    original = container.market_data
    container.market_data = StubMarketData(None, error_kind="not_found")
    try:
        with pytest.raises(HTTPException) as exc:
            get_market_price("THISISNOTATICKER", force_refresh=True)
        assert exc.value.status_code == 404
        assert exc.value.detail == "No market data found for THISISNOTATICKER"
    finally:
        container.market_data = original


def test_market_price_invalid_ticker_force_refresh_returns_404():
    original = container.market_data
    container.market_data = StubMarketData(None, error_kind="not_found")
    try:
        try:
            get_market_price("THISISNOTATICKER", force_refresh=True)
            pytest.fail("Expected HTTPException for invalid ticker")
        except HTTPException as exc:
            response = DummyResponse(exc.detail)
            assert exc.status_code == 404
            assert response.json() == {
                "detail": "No market data found for THISISNOTATICKER",
            }
    finally:
        container.market_data = original


def test_market_price_forced_error_returns_503(monkeypatch):
    original = container.market_data
    container.market_data = StubMarketData(None, error_kind="not_found")
    try:
        monkeypatch.setenv("MARKET_DATA_FORCE_ERROR", "true")
        with pytest.raises(HTTPException) as exc:
            get_market_price("AAPL", force_refresh=True)
        assert exc.value.status_code == 503
        assert exc.value.detail == "Market data provider unavailable. Try again."
    finally:
        container.market_data = original
        os.environ.pop("MARKET_DATA_FORCE_ERROR", None)
