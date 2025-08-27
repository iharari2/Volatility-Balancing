from fastapi.testclient import TestClient
from app.main import create_app

client = TestClient(create_app())

def test_missing_idempotency():
    r = client.post("/v1/positions/pos1/orders", json={"side": "BUY", "qty": 1})
    assert r.status_code == 400

def test_submit_and_replay_same_order_id():
    headers = {"Idempotency-Key": "k1"}
    r1 = client.post("/v1/positions/pos1/orders", json={"side": "BUY", "qty": 2}, headers=headers)
    r2 = client.post("/v1/positions/pos1/orders", json={"side": "BUY", "qty": 2}, headers=headers)
    assert r1.status_code in (200, 201) and r2.status_code in (200, 201)
    assert r1.json()["order_id"] == r2.json()["order_id"]
    assert r1.json()["accepted"] is True