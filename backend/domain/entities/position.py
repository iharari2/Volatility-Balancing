# =========================
# backend/domain/entities/position.py
# =========================
from dataclasses import dataclass, field
from datetime import datetime

from domain.value_objects.guardrails import GuardrailPolicy


@dataclass
class Position:
    id: str
    ticker: str
    qty: float = 0.0
    cash: float = 0.0
    guardrails: GuardrailPolicy = field(default_factory=GuardrailPolicy)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

