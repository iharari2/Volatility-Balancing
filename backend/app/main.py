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
from app.routes.version import router as version_router
from app.routes.positions import router as positions_router
from app.routes.portfolios import router as portfolios_router
from app.routes.orders import router as orders_router
from app.routes.dividends import router as dividends_router
from app.routes.optimization import router as optimization_router
from app.routes.market import router as market_router
from app.routes.trading import router as trading_router

from app.routes.excel_export import router as excel_export_router
from app.routes.simulations import router as simulations_router
from app.routes.sim import router as sim_router
from app.routes.positions_cockpit import router as positions_cockpit_router
from app.routes.portfolio_cockpit_api import router as portfolio_cockpit_router
from application.services.trading_worker import start_trading_worker, stop_trading_worker

API_PREFIX = "/v1"


def _fix_portfolio_trading_states():
    """
    Fix existing portfolios that have trading_state != RUNNING.

    This ensures all portfolios are active for trading by default.
    Called on app startup to fix legacy portfolios created before the default was changed.
    """
    try:
        from app.di import container
        from infrastructure.persistence.sql.models import PortfolioModel

        if hasattr(container, 'portfolio_repo') and hasattr(container.portfolio_repo, '_sf'):
            with container.portfolio_repo._sf() as session:
                # Find all portfolios not in RUNNING state
                portfolios = session.query(PortfolioModel).filter(
                    PortfolioModel.trading_state != "RUNNING"
                ).all()

                if portfolios:
                    for portfolio in portfolios:
                        old_state = portfolio.trading_state
                        portfolio.trading_state = "RUNNING"
                        print(f"[Startup] Fixed portfolio '{portfolio.name}' (id={portfolio.id}): {old_state} -> RUNNING")
                    session.commit()
                    print(f"[Startup] Fixed {len(portfolios)} portfolio(s) to RUNNING state")
                else:
                    print("[Startup] All portfolios already in RUNNING state")
    except Exception as e:
        print(f"[Startup] Warning: Could not fix portfolio states: {e}")


def _resolve_worker_enabled(override: bool | None) -> bool:
    if override is not None:
        return override
    return os.getenv("TRADING_WORKER_ENABLED", "true").lower() == "true"


def create_app(enable_trading_worker: bool | None = None) -> FastAPI:
    """Create the FastAPI app with optional worker toggle for tests."""

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        """Lifespan context manager for startup and shutdown events."""
        # Fix any portfolios stuck in non-RUNNING state
        _fix_portfolio_trading_states()

        # Start trading worker
        worker_enabled = _resolve_worker_enabled(enable_trading_worker)
        if worker_enabled:
            start_trading_worker()
        yield
        if worker_enabled:
            stop_trading_worker()

    app = FastAPI(title="Volatility Balancing API", version="v1", lifespan=lifespan)
    if os.getenv("VB_TIMING", "").lower() in {"1", "true", "yes", "on"}:
        # Minimal ASGI middleware to trace response send completion.
        class TimingMiddleware:
            def __init__(self, app, **kwargs):
                self.inner_app = app

            async def __call__(self, scope, receive, send):
                if scope["type"] != "http":
                    await self.inner_app(scope, receive, send)
                    return
                print(f"asgi_timing request_start path={scope.get('path')}")

                async def send_wrapper(message):
                    if message["type"] == "http.response.start":
                        print(
                            f"asgi_timing response_start path={scope.get('path')} status={message.get('status')}"
                        )
                    if message["type"] == "http.response.body" and not message.get("more_body"):
                        print(f"asgi_timing response_end path={scope.get('path')}")
                    await send(message)

                await self.inner_app(scope, receive, send_wrapper)
                print(f"asgi_timing request_end path={scope.get('path')}")

        app.add_middleware(TimingMiddleware)

    # Add CORS middleware unless explicitly disabled for debugging.
    if os.getenv("VB_TIMING_NO_CORS", "").lower() not in {"1", "true", "yes", "on"}:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # Allow all origins for development
            allow_credentials=False,  # Set to False when using allow_origins=["*"]
            allow_methods=["*"],
            allow_headers=["*"],
        )
    app.include_router(health_router, prefix=API_PREFIX)
    app.include_router(version_router)
    app.include_router(positions_router)  # positions_router already has /v1 prefix
    app.include_router(portfolios_router)  # portfolios_router already has /v1/portfolios prefix
    app.include_router(orders_router)  # orders_router already has /api prefix in routes
    app.include_router(dividends_router)  # dividends_router already has /v1 prefix
    app.include_router(optimization_router)  # optimization_router already has /v1 prefix
    app.include_router(market_router)
    app.include_router(trading_router)  # trading_router already has /v1 prefix
    app.include_router(excel_export_router)  # excel_export_router already has /v1 prefix
    app.include_router(simulations_router)  # simulations_router already has /v1 prefix
    app.include_router(sim_router)
    app.include_router(
        positions_cockpit_router
    )  # positions_cockpit_router already has /v1/tenants/{tenant_id}/portfolios/{portfolio_id}/positions/{position_id} prefix
    app.include_router(portfolio_cockpit_router)

    def __sync_ping() -> dict[str, bool]:
        return {"ok": True}

    app.add_api_route("/__sync_ping", __sync_ping, methods=["GET"])

    return app


app = create_app()
