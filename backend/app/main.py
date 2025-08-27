# =========================
# backend/app/main.py
# =========================
from fastapi import FastAPI

from app.routes.health import router as health_router
from app.routes.positions import router as positions_router
from app.routes.orders import router as orders_router

app = FastAPI(title="Volatility Balancing API", version="v1")
app.include_router(health_router)
app.include_router(positions_router, prefix="/v1")
app.include_router(orders_router, prefix="/v1")
