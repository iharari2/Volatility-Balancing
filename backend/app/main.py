from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uuid, time

app = FastAPI(title="VB MVP API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "ok"}

# ---- simple in-memory stub for MVP smoke ----
ORDERS = {}

class OrderIn(BaseModel):
    account_id: str
    symbol: str
    side: str
    qty: int
    limit_price: float | None = None

@app.post("/api/v1/orders")
def place_order(o: OrderIn):
    if o.limit_price is None:  # enforce limit-only per MVP stub
        o.limit_price = 1.0
    if o.qty <= 0:
        raise HTTPException(400, "qty must be > 0")
    oid = str(uuid.uuid4())
    ORDERS[oid] = {"id": oid, "status": "accepted", "limit_price": float(o.limit_price)}
    # simulate same-day fill at limit after small delay
    ORDERS[oid]["_filled_at"] = time.time() + 1.5
    return {"id": oid, "status": "accepted", "limit_price": float(o.limit_price)}

@app.get("/api/v1/orders/{oid}")
def get_order(oid: str):
    if oid not in ORDERS:
        raise HTTPException(404, "not found")
    od = ORDERS[oid]
    if "_filled_at" in od and time.time() >= od["_filled_at"]:
        od["status"] = "filled"
        od["fill_price"] = od["limit_price"]
        od.pop("_filled_at", None)
    return od

@app.post("/api/v1/orders/{oid}/cancel")
def cancel_order(oid: str):
    if oid not in ORDERS:
        raise HTTPException(404, "not found")
    od = ORDERS[oid]
    if od.get("status") == "filled":
        return {"status": "too_late"}
    od["status"] = "canceled"
    return {"status": "canceled"}
