# =========================
# backend/domain/entities/position.py
# =========================
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone

from domain.value_objects.guardrails import GuardrailPolicy
from domain.value_objects.order_policy import OrderPolicy


@dataclass
class Position:
    id: str
    ticker: str
    qty: float
    cash: float

    guardrails: GuardrailPolicy = field(default_factory=GuardrailPolicy)
    order_policy: OrderPolicy = field(default_factory=OrderPolicy)

    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
