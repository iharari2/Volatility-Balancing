# =========================
# backend/app/main.py
# =========================
import os

# Set environment variables for SQL persistence if not already set
if not os.getenv("APP_PERSISTENCE"):
    os.environ["APP_PERSISTENCE"] = "sql"
if not os.getenv("APP_EVENTS"):
    os.environ["APP_EVENTS"] = "sql"
if not os.getenv("APP_AUTO_CREATE"):
    os.environ["APP_AUTO_CREATE"] = "true"
if not os.getenv("SQL_URL"):
    os.environ["SQL_URL"] = "sqlite:///./vb.sqlite"

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.health import router as health_router
from app.routes.positions import router as positions_router
from app.routes.orders import router as orders_router
from app.routes.dividends import router as dividends_router
from app.routes.optimization import router as optimization_router
from app.routes.market import router as market_router

API_PREFIX = "/v1"

app = FastAPI(title="Volatility Balancing API", version="v1")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=False,  # Set to False when using allow_origins=["*"]
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(health_router, prefix=API_PREFIX)
app.include_router(positions_router)  # positions_router already has /v1 prefix
app.include_router(orders_router, prefix=API_PREFIX)
app.include_router(dividends_router)  # dividends_router already has /v1 prefix
app.include_router(optimization_router)  # optimization_router already has /v1 prefix
app.include_router(market_router)  # market_router already has /v1 prefix
