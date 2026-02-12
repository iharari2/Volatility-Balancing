# =========================
# backend/domain/value_objects/guardrails.py
# =========================
from dataclasses import dataclass


@dataclass
class GuardrailPolicy:
    """
    Legacy guardrail policy value object.

    NOTE: This class is kept for backward compatibility with Position entities.
    New code should use GuardrailConfig from ConfigRepo instead.
    The check_after_fill() method has been removed - use GuardrailEvaluator.validate_after_fill() instead.
    """

    min_stock_alloc_pct: float = 0.25  # 25% min stock allocation
    max_stock_alloc_pct: float = 0.75  # 75% max stock allocation
    max_orders_per_day: int = 5
    # Maximum percentage of position/cash that can be traded in a single order
    max_sell_pct_per_trade: float = 0.5  # e.g. 0.5 = max 50% of shares in one sell
    max_buy_pct_per_trade: float = 0.5  # e.g. 0.5 = max 50% of cash in one buy
