# =========================
# backend/tests/integration/test_health.py
# =========================
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_endpoints():
    r1 = client.get("/healthz")
    r2 = client.get("/v1/healthz")
    assert r1.status_code == 200 and r1.json().get("status") == "ok"
    assert r2.status_code == 200 and r2.json().get("version") == "v1"