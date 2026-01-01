# =========================
# backend/domain/value_objects/configs.py
# =========================
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional


@dataclass
class TriggerConfig:
    """Trigger configuration for price-based trading decisions."""

    up_threshold_pct: Decimal  # e.g. +3 percent
    down_threshold_pct: Decimal  # e.g. -3 percent
    # optional: step index, hysteresis, etc


@dataclass
class GuardrailConfig:
    """Guardrail configuration for position limits."""

    min_stock_pct: Decimal  # e.g. 0.3
    max_stock_pct: Decimal  # e.g. 0.7
    max_trade_pct_of_position: Optional[Decimal] = None
    max_daily_notional: Optional[Decimal] = None
    max_orders_per_day: Optional[int] = None  # Daily order limit


@dataclass
class OrderPolicyConfig:
    """Order policy configuration for order execution rules."""

    min_qty: Decimal = Decimal("0")
    min_notional: Decimal = Decimal("100.0")  # $100 default
    lot_size: Decimal = Decimal("0")
    qty_step: Decimal = Decimal("0")
    action_below_min: str = "hold"  # "hold" | "reject" | "clip"
    rebalance_ratio: Decimal = Decimal("1.6667")  # r from spec (5/3 ratio)
    order_sizing_strategy: str = "proportional"
    allow_after_hours: bool = True
    commission_rate: Optional[Decimal] = (
        None  # Optional - can come from ConfigRepo.get_commission_rate()
    )
