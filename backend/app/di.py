# =========================
# backend/app/di.py
# =========================
import os

from domain.ports.positions_repo import PositionsRepo
from domain.ports.orders_repo import OrdersRepo
from domain.ports.events_repo import EventsRepo
from domain.ports.idempotency_repo import IdempotencyRepo

from infrastructure.persistence.memory.positions_repo_mem import InMemoryPositionsRepo
from infrastructure.persistence.memory.orders_repo_mem import InMemoryOrdersRepo
from infrastructure.persistence.memory.events_repo_mem import InMemoryEventsRepo
from infrastructure.persistence.memory.idempotency_repo_mem import InMemoryIdempotencyRepo
from infrastructure.time.clock import Clock


class _Container:
    positions: PositionsRepo
    orders: OrdersRepo
    events: EventsRepo
    idempotency: IdempotencyRepo
    clock: Clock

    def __init__(self) -> None:
        persistence = os.getenv("APP_PERSISTENCE", "memory").lower()
        events_backend = os.getenv("APP_EVENTS", "memory").lower()
        idem_backend = os.getenv("APP_IDEMPOTENCY", "memory").lower()

        self.clock = Clock()

        sql_url = os.getenv("SQL_URL", "sqlite:///./vb.sqlite")

        # --- Positions & Orders backend ---
        if persistence == "sql":
            from sqlalchemy.orm import sessionmaker
            from infrastructure.persistence.sql.models import get_engine, create_all
            from infrastructure.persistence.sql.positions_repo_sql import SQLPositionsRepo
            from infrastructure.persistence.sql.orders_repo_sql import SQLOrdersRepo

            engine = get_engine(sql_url)
            create_all(engine)
            Session = sessionmaker(bind=engine, expire_on_commit=False, autoflush=False)
            self.positions = SQLPositionsRepo(Session)
            self.orders = SQLOrdersRepo(Session)
        else:
            self.positions = InMemoryPositionsRepo()
            self.orders = InMemoryOrdersRepo()

        # --- Events backend ---
        if events_backend == "sql":
            from sqlalchemy.orm import sessionmaker as ev_sessionmaker
            from infrastructure.persistence.sql.models import (
                get_engine as get_ev_engine,
                create_all as ev_create_all,
            )
            from infrastructure.persistence.sql.events_repo_sql import SQLEventsRepo
            from infrastructure.persistence.sql.positions_repo_sql import SQLPositionsRepo

            ev_engine = get_ev_engine(sql_url)
            ev_create_all(ev_engine)
            EvSession = ev_sessionmaker(bind=ev_engine, expire_on_commit=False, autoflush=False)
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
                # Fallback silently to in-memory if Redis is unavailable
                self.idempotency = InMemoryIdempotencyRepo()
        else:
            self.idempotency = InMemoryIdempotencyRepo()

    def reset(self) -> None:
        self.positions.clear()
        self.orders.clear()
        self.events.clear()
        self.idempotency.clear()


container = _Container()
