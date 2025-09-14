# =========================
# backend/domain/value_objects/order_policy.py
# =========================
# backend/domain/value_objects/order_policy.py
from __future__ import annotations
from dataclasses import dataclass


@dataclass
class OrderPolicy:
    min_qty: float = 0.0
    min_notional: float = 0.0
    lot_size: float = 0.0
    qty_step: float = 0.0
    # "hold" | "reject" | "clip"
    action_below_min: str = "hold"

    def round_qty(self, q: float) -> float:
        if self.qty_step and self.qty_step > 0:
            steps = round(q / self.qty_step)
            return steps * self.qty_step
        return q

    def clamp_to_lot(self, q: float) -> float:
        if self.lot_size and self.lot_size > 0:
            lots = round(q / self.lot_size)
            return lots * self.lot_size
        return q
