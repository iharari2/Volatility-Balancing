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


def _normalize_guardrail_pct(value: Optional[Decimal]) -> Optional[Decimal]:
    if value is None:
        return None
    return value / Decimal("100") if value > Decimal("1") else value


def normalize_guardrail_config(config: GuardrailConfig) -> GuardrailConfig:
    """Normalize guardrail percentages to fractional values (0-1) when needed."""
    return GuardrailConfig(
        min_stock_pct=_normalize_guardrail_pct(config.min_stock_pct),
        max_stock_pct=_normalize_guardrail_pct(config.max_stock_pct),
        max_trade_pct_of_position=_normalize_guardrail_pct(config.max_trade_pct_of_position),
        max_daily_notional=config.max_daily_notional,
        max_orders_per_day=config.max_orders_per_day,
    )


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
