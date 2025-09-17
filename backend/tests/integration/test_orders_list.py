# backend/tests/integration/test_orders_list.py


def test_list_orders_for_position(client, position_id):
    headers = {"Idempotency-Key": "list-k1"}
    response = client.post(
        f"/v1/positions/{position_id}/orders",
        json={"side": "BUY", "qty": 1, "price": 100.0},
        headers=headers,
    )
    assert response.status_code in [
        200,
        201,
    ], f"Expected 200 or 201, got {response.status_code}: {response.text}"

    r = client.get(f"/v1/positions/{position_id}/orders?limit=10")
    assert r.status_code == 200
    body = r.json()
    assert body["position_id"] == position_id
    assert isinstance(body["orders"], list) and len(body["orders"]) >= 1
