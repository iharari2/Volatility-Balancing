# =========================
# backend/application/use_cases/evaluate_position_uc.py
# =========================
from __future__ import annotations
from typing import Dict, Any
from domain.ports.positions_repo import PositionsRepo
from domain.ports.events_repo import EventsRepo
from domain.entities.event import Event
from infrastructure.time.clock import Clock
from uuid import uuid4


class EvaluatePositionUC:
    """Simple volatility trading evaluation logic."""

    def __init__(
        self,
        positions: PositionsRepo,
        events: EventsRepo,
        clock: Clock,
    ) -> None:
        self.positions = positions
        self.events = events
        self.clock = clock

    def evaluate(self, position_id: str, current_price: float) -> Dict[str, Any]:
        """Evaluate position for volatility triggers."""

        # Get position
        position = self.positions.get(position_id)
        if not position:
            raise KeyError("position_not_found")

        # Check if we have an anchor price
        if not position.anchor_price:
            return {
                "position_id": position_id,
                "current_price": current_price,
                "anchor_price": None,
                "trigger_detected": False,
                "reasoning": "No anchor price set - cannot evaluate triggers",
            }

        # Check triggers
        trigger_result = self._check_triggers(position, current_price)

        # Log event
        self._log_evaluation_event(position, current_price, trigger_result)

        return {
            "position_id": position_id,
            "current_price": current_price,
            "anchor_price": position.anchor_price,
            "trigger_detected": trigger_result["triggered"],
            "trigger_type": trigger_result.get("side"),
            "reasoning": trigger_result["reasoning"],
        }

    def _check_triggers(self, position, current_price: float) -> Dict[str, Any]:
        """Check if current price triggers buy or sell."""
        anchor = position.anchor_price
        threshold = position.order_policy.trigger_threshold_pct

        # Buy trigger: P ≤ P_anchor × (1 − τ)
        buy_threshold = anchor * (1 - threshold)
        # Sell trigger: P ≥ P_anchor × (1 + τ)
        sell_threshold = anchor * (1 + threshold)

        if current_price <= buy_threshold:
            return {
                "triggered": True,
                "side": "BUY",
                "reasoning": f"Price ${current_price:.2f} ≤ buy threshold ${buy_threshold:.2f} (${anchor:.2f} × {1-threshold:.1%})",
            }
        elif current_price >= sell_threshold:
            return {
                "triggered": True,
                "side": "SELL",
                "reasoning": f"Price ${current_price:.2f} ≥ sell threshold ${sell_threshold:.2f} (${anchor:.2f} × {1+threshold:.1%})",
            }
        else:
            return {
                "triggered": False,
                "reasoning": f"Price ${current_price:.2f} within threshold range [${buy_threshold:.2f}, ${sell_threshold:.2f}]",
            }

    def _log_evaluation_event(
        self, position, current_price: float, trigger_result: Dict[str, Any]
    ) -> None:
        """Log evaluation event."""
        event = Event(
            id=f"evt_eval_{position.id}_{uuid4().hex[:8]}",
            position_id=position.id,
            type="threshold_crossed" if trigger_result["triggered"] else "evaluation_completed",
            inputs={
                "current_price": current_price,
                "anchor_price": position.anchor_price,
                "threshold_pct": position.order_policy.trigger_threshold_pct,
            },
            outputs={
                "trigger_detected": trigger_result["triggered"],
                "trigger_type": trigger_result.get("side"),
                "reasoning": trigger_result["reasoning"],
            },
            message=trigger_result["reasoning"],
            ts=self.clock.now(),
        )
        self.events.append(event)
