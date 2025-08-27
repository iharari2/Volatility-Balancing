# =========================
# backend/app/di.py
# =========================
from infrastructure.persistence.memory.positions_repo_mem import InMemoryPositionsRepo
from infrastructure.persistence.memory.orders_repo_mem import InMemoryOrdersRepo
from infrastructure.persistence.memory.events_repo_mem import InMemoryEventsRepo
from infrastructure.persistence.memory.idempotency_repo_mem import InMemoryIdempotencyRepo
from infrastructure.time.clock import Clock


class _Container:
    def __init__(self) -> None:
        self.positions = InMemoryPositionsRepo()
        self.orders = InMemoryOrdersRepo()
        self.events = InMemoryEventsRepo()
        self.idempotency = InMemoryIdempotencyRepo()
        self.clock = Clock()

    def reset(self) -> None:
        self.positions.clear()
        self.orders.clear()
        self.events.clear()
        self.idempotency.clear()


container = _Container()

