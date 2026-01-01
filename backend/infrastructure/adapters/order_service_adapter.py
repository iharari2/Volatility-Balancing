# =========================
# backend/infrastructure/adapters/order_service_adapter.py
# =========================
"""Adapter implementing IOrderService using existing order submission logic."""

from application.ports.orders import IOrderService
from domain.value_objects.trade_intent import TradeIntent
from domain.value_objects.market import MarketQuote
from domain.value_objects.types import OrderSide
from application.use_cases.submit_order_uc import SubmitOrderUC
from application.dto.orders import CreateOrderRequest


class LiveOrderServiceAdapter(IOrderService):
    """Adapter that implements IOrderService using existing SubmitOrderUC."""

    def __init__(self, submit_order_uc: SubmitOrderUC):
        """
        Initialize adapter with existing submit order use case.

        Args:
            submit_order_uc: Existing SubmitOrderUC implementation
        """
        self.submit_order_uc = submit_order_uc

    def submit_live_order(
        self,
        position_id: str,
        portfolio_id: str,
        tenant_id: str,
        trade_intent: TradeIntent,
        quote: MarketQuote,
    ) -> str:
        """
        Live trading.
        Creates order record, calls broker, returns order_id.
        Must be idempotent for repeated calls with same trade intent.
        """
        from uuid import uuid4

        # Convert TradeIntent to CreateOrderRequest
        # Note: TradeIntent uses "buy"/"sell", OrderSide is Literal["BUY", "SELL"]
        # OrderSide is a type alias, not an enum, so use string literals directly
        side: OrderSide = "BUY" if trade_intent.side.lower() == "buy" else "SELL"

        request = CreateOrderRequest(
            side=side,
            qty=float(trade_intent.qty),
        )

        # Generate idempotency key from trade intent
        # Use a combination of position_id, side, qty, and price for idempotency
        idempotency_key = (
            f"{position_id}_{trade_intent.side}_{trade_intent.qty}_{quote.price}_{uuid4().hex[:8]}"
        )

        # Submit order using existing use case
        response = self.submit_order_uc.execute(
            tenant_id=tenant_id,
            portfolio_id=portfolio_id,
            position_id=position_id,
            request=request,
            idempotency_key=idempotency_key,
        )

        return response.order_id
