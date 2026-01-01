# =========================
# backend/domain/value_objects/decisions.py
# =========================
from dataclasses import dataclass
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from domain.value_objects.trade_intent import TradeIntent


@dataclass
class TriggerDecision:
    """Decision from price trigger evaluation."""

    fired: bool
    direction: Optional[str] = None  # "buy" | "sell" | None
    reason: Optional[str] = None


@dataclass
class GuardrailDecision:
    """Decision from guardrail evaluation."""

    allowed: bool
    reason: Optional[str] = None
    trade_intent: Optional["TradeIntent"] = None
