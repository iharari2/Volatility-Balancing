# =========================
# backend/app/main.py
# =========================
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.health import router as health_router
from app.routes.positions import router as positions_router
from app.routes.orders import router as orders_router
from app.routes.dividends import router as dividends_router

API_PREFIX = "/v1"

app = FastAPI(title="Volatility Balancing API", version="v1")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(health_router, prefix=API_PREFIX)
app.include_router(positions_router)  # positions_router already has /v1 prefix
app.include_router(orders_router, prefix=API_PREFIX)
app.include_router(dividends_router)  # dividends_router already has /v1 prefix
