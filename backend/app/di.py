# backend/app/di.py
from __future__ import annotations

import os

from domain.ports.positions_repo import PositionsRepo
from domain.ports.orders_repo import OrdersRepo
from domain.ports.trades_repo import TradesRepo
from domain.ports.events_repo import EventsRepo
from domain.ports.idempotency_repo import IdempotencyRepo
from domain.ports.market_data import MarketDataRepo
from domain.ports.dividend_repo import DividendRepo, DividendReceivableRepo
from domain.ports.dividend_market_data import DividendMarketDataRepo
from domain.ports.optimization_repo import (
    OptimizationConfigRepo,
    OptimizationResultRepo,
    HeatmapDataRepo,
)
from domain.ports.simulation_repo import SimulationRepo

from infrastructure.time.clock import Clock

# In-memory backends
from infrastructure.persistence.memory.positions_repo_mem import InMemoryPositionsRepo
from infrastructure.persistence.memory.orders_repo_mem import InMemoryOrdersRepo
from infrastructure.persistence.memory.trades_repo_mem import InMemoryTradesRepo
from infrastructure.persistence.memory.events_repo_mem import InMemoryEventsRepo
from infrastructure.persistence.memory.idempotency_repo_mem import InMemoryIdempotencyRepo
from infrastructure.persistence.memory.dividend_repo import (
    InMemoryDividendRepo,
    InMemoryDividendReceivableRepo,
)
from infrastructure.market.yfinance_adapter import YFinanceAdapter
from infrastructure.market.yfinance_dividend_adapter import YFinanceDividendAdapter

# SQL bits (imported unconditionally; OK since deps are installed)
from sqlalchemy.orm import sessionmaker
from infrastructure.persistence.sql.models import get_engine, create_all
from infrastructure.persistence.sql.positions_repo_sql import SQLPositionsRepo
from infrastructure.persistence.sql.orders_repo_sql import SQLOrdersRepo
from infrastructure.persistence.sql.trades_repo_sql import SQLTradesRepo
from infrastructure.persistence.sql.events_repo_sql import SQLEventsRepo
from infrastructure.persistence.sql.portfolio_state_repo_sql import SQLPortfolioStateRepo

# Optimization repositories
from infrastructure.persistence.memory.optimization_repo_mem import (
    InMemoryOptimizationConfigRepo,
    InMemoryOptimizationResultRepo,
    InMemoryHeatmapDataRepo,
)
from infrastructure.persistence.memory.simulation_repo_mem import InMemorySimulationRepo

# Use cases
from application.use_cases.parameter_optimization_uc import ParameterOptimizationUC


def _truthy(envval: str | None) -> bool:
    """Interpret common truthy env values."""
    if envval is None:
        return False
    return envval.strip().lower() not in ("0", "false", "no", "off", "")


class _Container:
    positions: PositionsRepo
    orders: OrdersRepo
    trades: TradesRepo
    events: EventsRepo
    idempotency: IdempotencyRepo
    market_data: MarketDataRepo
    dividend: DividendRepo
    dividend_receivable: DividendReceivableRepo
    dividend_market_data: DividendMarketDataRepo
    portfolio_state: SQLPortfolioStateRepo
    clock: Clock

    # Optimization repositories (placeholder implementations)
    optimization_config: OptimizationConfigRepo
    optimization_result: OptimizationResultRepo
    heatmap_data: HeatmapDataRepo
    simulation: SimulationRepo

    # Use cases
    parameter_optimization_uc: ParameterOptimizationUC

    def __init__(self) -> None:
        self.clock = Clock()
        self.market_data = YFinanceAdapter()
        self.dividend_market_data = YFinanceDividendAdapter()
        self.dividend = InMemoryDividendRepo()
        self.dividend_receivable = InMemoryDividendReceivableRepo()

        # Initialize optimization repositories
        self.optimization_config = InMemoryOptimizationConfigRepo()
        self.optimization_result = InMemoryOptimizationResultRepo()
        self.heatmap_data = InMemoryHeatmapDataRepo()
        self.simulation = InMemorySimulationRepo()

        # Initialize use cases
        self.parameter_optimization_uc = ParameterOptimizationUC(
            config_repo=self.optimization_config,
            result_repo=self.optimization_result,
            heatmap_repo=self.heatmap_data,
            simulation_repo=self.simulation,
        )

        persistence = os.getenv("APP_PERSISTENCE", "memory").lower()
        events_backend = os.getenv("APP_EVENTS", "memory").lower()
        idem_backend = os.getenv("APP_IDEMPOTENCY", "memory").lower()
        auto_create = _truthy(os.getenv("APP_AUTO_CREATE"))

        sql_url = os.getenv("SQL_URL", "sqlite:///./vb.sqlite")

        main_engine = None

        # --- Positions & Orders & Trades backend ---
        if persistence == "sql":
            main_engine = get_engine(sql_url)
            if auto_create:
                create_all(main_engine)
            Session = sessionmaker(bind=main_engine, expire_on_commit=False, autoflush=False)
            self.positions = SQLPositionsRepo(Session)
            self.orders = SQLOrdersRepo(Session)
            self.trades = SQLTradesRepo(Session)
        else:
            self.positions = InMemoryPositionsRepo()
            self.orders = InMemoryOrdersRepo()
            self.trades = InMemoryTradesRepo()

        # --- Events backend (can be independent of positions/orders) ---
        if events_backend == "sql":
            ev_engine = main_engine or get_engine(sql_url)
            if auto_create and ev_engine is not main_engine:
                # If we didn’t already create tables on the same engine, do it now.
                create_all(ev_engine)
            EvSession = sessionmaker(bind=ev_engine, expire_on_commit=False, autoflush=False)
            self.events = SQLEventsRepo(EvSession)
        else:
            self.events = InMemoryEventsRepo()

        # --- Idempotency backend ---
        if idem_backend == "redis":
            try:
                import redis
                from infrastructure.persistence.redis.idempotency_repo_redis import (
                    RedisIdempotencyRepo,
                )

                client = redis.Redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"))
                self.idempotency = RedisIdempotencyRepo(client)
            except Exception:
                # If Redis is not available, fall back to in-memory.
                self.idempotency = InMemoryIdempotencyRepo()
        else:
            self.idempotency = InMemoryIdempotencyRepo()

        # --- Portfolio State (always SQL when available) ---
        if main_engine:
            Session = sessionmaker(bind=main_engine, expire_on_commit=False, autoflush=False)
            self.portfolio_state = SQLPortfolioStateRepo(Session)
        else:
            # Fallback to in-memory for development
            from infrastructure.persistence.memory.portfolio_state_repo_mem import (
                InMemoryPortfolioStateRepo,
            )

            self.portfolio_state = InMemoryPortfolioStateRepo()

    def reset(self) -> None:
        self.positions.clear()
        self.orders.clear()
        self.trades.clear()
        self.events.clear()
        self.idempotency.clear()
        self.portfolio_state.clear()
        # Note: dividend repos don't have clear() methods yet, but they're in-memory so they reset on restart


container = _Container()


# Dependency injection functions for FastAPI
def get_parameter_optimization_uc() -> ParameterOptimizationUC:
    """Get the parameter optimization use case."""
    return container.parameter_optimization_uc
