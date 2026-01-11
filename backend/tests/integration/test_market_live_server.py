import json
import os
import subprocess

import pytest


BASE_URL = os.getenv("LIVE_SERVER_BASE_URL", "http://127.0.0.1:8000")
pytestmark = pytest.mark.e2e


def _e2e_enabled() -> bool:
    return os.getenv("E2E_SERVER", "").lower() in ("1", "true", "yes")


def _curl_json(url: str) -> tuple[int, dict]:
    result = subprocess.run(
        ["curl", "-s", "-w", "\n%{http_code}", url],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "curl failed")
    body, status = result.stdout.rsplit("\n", 1)
    return int(status), json.loads(body)


def test_market_price_invalid_ticker_live():
    if not _e2e_enabled() and os.getenv("LIVE_SERVER_TESTS", "false").lower() != "true":
        pytest.skip("E2E_SERVER/LIVE_SERVER_TESTS not enabled")
    if os.getenv("LIVE_SERVER_FORCE_ERROR", "false").lower() == "true":
        pytest.skip("LIVE_SERVER_FORCE_ERROR enabled; invalid ticker returns 503")
    try:
        status_code, payload = _curl_json(
            f"{BASE_URL}/v1/market/price/THISISNOTATICKER?force_refresh=true"
        )
    except Exception as exc:
        pytest.skip(f"Live server not reachable in this environment: {exc}")

    if status_code == 503:
        assert payload.get("detail") == "Market data provider unavailable. Try again."
        return
    assert status_code == 404
    detail = payload.get("detail", "")
    assert "No market data found for THISISNOTATICKER" in detail


def test_market_price_forced_error_live():
    if not _e2e_enabled() and os.getenv("LIVE_SERVER_TESTS", "false").lower() != "true":
        pytest.skip("E2E_SERVER/LIVE_SERVER_TESTS not enabled")
    if os.getenv("LIVE_SERVER_FORCE_ERROR", "false").lower() != "true":
        pytest.skip("LIVE_SERVER_FORCE_ERROR not enabled")
    try:
        status_code, payload = _curl_json(f"{BASE_URL}/v1/market/price/AAPL")
    except Exception as exc:
        pytest.skip(f"Live server not reachable in this environment: {exc}")

    assert status_code == 503
    assert payload.get("detail") == "Market data provider unavailable. Try again."
