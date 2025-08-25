from fastapi.testclient import TestClient
from app.main import app
import time

def test_stub_fill_same_day_at_limit():
    c = TestClient(app)
    r = c.post("/api/v1/orders", json={"account_id":"test","symbol":"MSFT","side":"buy","qty":1,"limit_price":123.45})
    assert r.status_code == 200
    oid = r.json()["id"]

    for _ in range(6):
        s = c.get(f"/api/v1/orders/{oid}").json()
        if s.get("status") == "filled":
            assert abs(s["fill_price"] - 123.45) < 1e-9
            return
        time.sleep(0.5)
    raise AssertionError("order did not auto-fill")
