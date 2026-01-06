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

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.health import router as health_router
from app.routes.positions import router as positions_router
from app.routes.portfolios import router as portfolios_router
from app.routes.orders import router as orders_router
from app.routes.dividends import router as dividends_router
from app.routes.optimization import router as optimization_router
from app.routes.market import router as market_router
from app.routes.trading import router as trading_router

from app.routes.excel_export import router as excel_export_router
from app.routes.simulations import router as simulations_router
from app.routes.positions_cockpit import router as positions_cockpit_router
from app.routes.portfolio_cockpit_api import router as portfolio_cockpit_router
from application.services.trading_worker import start_trading_worker, stop_trading_worker

API_PREFIX = "/v1"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    # Startup
    start_trading_worker()
    yield
    # Shutdown
    stop_trading_worker()


app = FastAPI(title="Volatility Balancing API", version="v1", lifespan=lifespan)

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
app.include_router(portfolios_router)  # portfolios_router already has /v1/portfolios prefix
app.include_router(orders_router, prefix=API_PREFIX)
app.include_router(dividends_router)  # dividends_router already has /v1 prefix
app.include_router(optimization_router)  # optimization_router already has /v1 prefix
app.include_router(market_router)
app.include_router(trading_router)  # trading_router already has /v1 prefix
app.include_router(excel_export_router)  # excel_export_router already has /v1 prefix
app.include_router(simulations_router)  # simulations_router already has /v1 prefix
app.include_router(
    positions_cockpit_router
)  # positions_cockpit_router already has /v1/tenants/{tenant_id}/portfolios/{portfolio_id}/positions/{position_id} prefix
app.include_router(portfolio_cockpit_router)
