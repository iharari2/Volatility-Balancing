from __future__ import annotations

from app.di import container
from infrastructure.market.deterministic_market_data import DeterministicMarketDataAdapter


def test_position_tick_endpoint_returns_shape(client, position_id):
    deterministic = DeterministicMarketDataAdapter()
    container.market_data = deterministic
    container.evaluate_position_uc.market_data = deterministic
    container.simulation_uc.market_data = deterministic

    response = client.post(f"/v1/positions/{position_id}/tick")
    assert response.status_code == 200

    payload = response.json()
    assert "position_snapshot" in payload
    assert "cycle_result" in payload

    position_snapshot = payload["position_snapshot"]
    assert position_snapshot.get("position_id") == position_id
    assert position_snapshot.get("symbol") is not None
