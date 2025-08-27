# =========================
# backend/domain/value_objects/guardrails.py
# =========================
from dataclasses import dataclass

@dataclass
class GuardrailPolicy:
    min_stock_alloc_pct: float = 0.0
    max_stock_alloc_pct: float = 1.0
    max_orders_per_day: int = 5
