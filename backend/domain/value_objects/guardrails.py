# =========================
# backend/domain/value_objects/guardrails.py
# =========================
from dataclasses import dataclass


@dataclass
class GuardrailPolicy:
    min_stock_alloc_pct: float = 0.0  # e.g. 0.25
    max_stock_alloc_pct: float = 1.0  # e.g. 0.75
    max_orders_per_day: int = 5

    def check_after_fill(
        self,
        *,
        qty_now: float,
        cash_now: float,
        side: str,
        fill_qty: float,
        price: float,
        commission: float = 0.0,
        dividend_receivable: float = 0.0,
    ) -> tuple[bool, str | None]:
        dq = fill_qty if side == "BUY" else -fill_qty
        new_qty = qty_now + dq
        cash_delta = (
            -(fill_qty * price) - commission if side == "BUY" else +(fill_qty * price) - commission
        )
        new_cash = cash_now + cash_delta
        effective_cash = new_cash + dividend_receivable

        stock_val = max(new_qty, 0.0) * price
        total_val = stock_val + max(effective_cash, 0.0)
        # no capital → allow (or treat as 0% to avoid div-by-zero)
        if total_val <= 0:
            return True, None

        alloc = stock_val / total_val
        if self.min_stock_alloc_pct and alloc < self.min_stock_alloc_pct:
            return False, f"alloc {alloc:.3f} < min {self.min_stock_alloc_pct:.3f}"
        if alloc > self.max_stock_alloc_pct:
            return False, f"alloc {alloc:.3f} > max {self.max_stock_alloc_pct:.3f}"
        return True, None
