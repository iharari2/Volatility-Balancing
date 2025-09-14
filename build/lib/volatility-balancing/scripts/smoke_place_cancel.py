import os, time, requests
BASE = os.environ.get("API_BASE","http://localhost:8000")
print("Smoke: health", BASE)
r = requests.get(f"{BASE}/health"); r.raise_for_status()
print("OK", r.json())

print("Smoke: place order")
r = requests.post(f"{BASE}/api/v1/orders", json={"account_id":"test","symbol":"MSFT","side":"buy","qty":1,"limit_price":100})
r.raise_for_status(); oid = r.json()["id"]; print("order id", oid)

for _ in range(6):
    s = requests.get(f"{BASE}/api/v1/orders/{oid}").json()
    if s.get("status")=="filled":
        assert abs(s["fill_price"]-s["limit_price"])<1e-9
        print("filled at", s["fill_price"])
        break
    time.sleep(0.5)
else:
    raise SystemExit("order did not fill in time")

print("Smoke: cancel (may be too_late if already filled)")
r = requests.post(f"{BASE}/api/v1/orders/{oid}/cancel"); r.raise_for_status()
print("cancel:", r.json())
