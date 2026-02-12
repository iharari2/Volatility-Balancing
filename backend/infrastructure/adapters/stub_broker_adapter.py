# =========================
# backend/infrastructure/adapters/stub_broker_adapter.py
# =========================
"""
Stub broker adapter for development and testing.

Simulates broker behavior with configurable fill modes:
- immediate: Orders fill instantly
- delayed: Orders stay in "working" state until manually advanced
- reject: All orders are rejected

Commission: 0.1% with $0.01 minimum (configurable)
"""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, List, Optional, Literal
from uuid import uuid4

from domain.ports.broker_service import (
    IBrokerService,
    BrokerOrderRequest,
    BrokerOrderResponse,
    BrokerOrderState,
    BrokerOrderStatus,
    BrokerFill,
    MarketHours,
)


FillMode = Literal["immediate", "delayed", "reject"]


class StubBrokerAdapter(IBrokerService):
    """
    Stub broker implementation for development and testing.

    Features:
    - Configurable fill modes (immediate, delayed, reject)
    - Commission calculation (default 0.1% with $0.01 minimum)
    - Optional price slippage simulation
    - In-memory order and fill tracking
    - Simulated market hours
    """

    def __init__(
        self,
        fill_mode: FillMode = "immediate",
        commission_rate: Decimal = Decimal("0.001"),  # 0.1%
        min_commission: Decimal = Decimal("0.01"),    # $0.01 minimum
        slippage_pct: Decimal = Decimal("0"),         # No slippage by default
        simulate_market_hours: bool = False,          # Always open by default
    ):
        """
        Initialize stub broker.

        Args:
            fill_mode: How orders should be filled
                - "immediate": Fill instantly on submission
                - "delayed": Stay working, call advance_order() to fill
                - "reject": Reject all orders
            commission_rate: Commission as decimal (0.001 = 0.1%)
            min_commission: Minimum commission per fill
            slippage_pct: Price slippage simulation (0.01 = 1%)
            simulate_market_hours: If True, simulate market hours; else always open
        """
        self.fill_mode = fill_mode
        self.commission_rate = commission_rate
        self.min_commission = min_commission
        self.slippage_pct = slippage_pct
        self.simulate_market_hours = simulate_market_hours

        # Internal tracking
        self._orders: Dict[str, _StubOrder] = {}
        self._fills: Dict[str, List[BrokerFill]] = {}

        # Price tracking (for fill simulation when no price provided)
        self._last_prices: Dict[str, Decimal] = {}

    def set_price(self, symbol: str, price: Decimal) -> None:
        """Set the simulated price for a symbol (for testing)."""
        self._last_prices[symbol] = price

    def submit_order(self, request: BrokerOrderRequest) -> BrokerOrderResponse:
        """Submit an order to the stub broker."""
        # Generate broker order ID
        broker_order_id = f"stub_{uuid4().hex[:12]}"
        now = datetime.now(timezone.utc)

        # Check fill mode
        if self.fill_mode == "reject":
            # Store as rejected
            self._orders[broker_order_id] = _StubOrder(
                broker_order_id=broker_order_id,
                client_order_id=request.client_order_id,
                request=request,
                status=BrokerOrderStatus.REJECTED,
                submitted_at=now,
                rejection_reason="Stub broker in reject mode",
            )
            return BrokerOrderResponse(
                broker_order_id=broker_order_id,
                client_order_id=request.client_order_id,
                status=BrokerOrderStatus.REJECTED,
                submitted_at=now,
                message="Order rejected: stub broker in reject mode",
            )

        # Create order
        order = _StubOrder(
            broker_order_id=broker_order_id,
            client_order_id=request.client_order_id,
            request=request,
            status=BrokerOrderStatus.PENDING,
            submitted_at=now,
        )
        self._orders[broker_order_id] = order
        self._fills[broker_order_id] = []

        # Handle fill mode
        if self.fill_mode == "immediate":
            self._fill_order(broker_order_id)
            return BrokerOrderResponse(
                broker_order_id=broker_order_id,
                client_order_id=request.client_order_id,
                status=BrokerOrderStatus.FILLED,
                submitted_at=now,
                message="Order filled immediately",
            )
        else:  # delayed
            order.status = BrokerOrderStatus.WORKING
            return BrokerOrderResponse(
                broker_order_id=broker_order_id,
                client_order_id=request.client_order_id,
                status=BrokerOrderStatus.WORKING,
                submitted_at=now,
                message="Order submitted, awaiting fill",
            )

    def cancel_order(self, broker_order_id: str) -> bool:
        """Request cancellation of an order."""
        order = self._orders.get(broker_order_id)
        if not order:
            return False

        # Can only cancel working or pending orders
        if order.status not in (BrokerOrderStatus.PENDING, BrokerOrderStatus.WORKING):
            return False

        order.status = BrokerOrderStatus.CANCELLED
        return True

    def get_order_status(self, broker_order_id: str) -> Optional[BrokerOrderState]:
        """Get current status of an order."""
        order = self._orders.get(broker_order_id)
        if not order:
            return None

        fills = self._fills.get(broker_order_id, [])
        filled_qty = sum(f.fill_qty for f in fills)
        avg_price = None
        if fills:
            total_value = sum(f.fill_qty * f.fill_price for f in fills)
            avg_price = total_value / filled_qty if filled_qty else None

        return BrokerOrderState(
            broker_order_id=order.broker_order_id,
            client_order_id=order.client_order_id,
            status=order.status,
            symbol=order.request.symbol,
            side=order.request.side,
            qty=order.request.qty,
            filled_qty=filled_qty,
            avg_fill_price=avg_price,
            submitted_at=order.submitted_at,
            filled_at=order.filled_at,
            last_update=datetime.now(timezone.utc),
            rejection_reason=order.rejection_reason,
        )

    def get_fills(self, broker_order_id: str) -> List[BrokerFill]:
        """Get all fills for an order."""
        return self._fills.get(broker_order_id, [])

    def is_market_open(self) -> bool:
        """Check if market is open."""
        if not self.simulate_market_hours:
            return True

        # Simple simulation: open 9:30-16:00 ET, Mon-Fri
        now = datetime.now(timezone.utc)
        # Rough check (not accounting for holidays)
        if now.weekday() >= 5:  # Weekend
            return False

        # Convert to ET (roughly UTC-5)
        et_hour = (now.hour - 5) % 24
        if 9 <= et_hour < 16 or (et_hour == 9 and now.minute >= 30):
            return True
        return False

    def get_market_hours(self) -> MarketHours:
        """Get market hours info."""
        is_open = self.is_market_open()
        now = datetime.now(timezone.utc)

        session = "regular" if is_open else "closed"
        if not self.simulate_market_hours:
            session = "regular"  # Always regular when not simulating

        return MarketHours(
            is_open=is_open,
            current_time=now,
            session=session,
        )

    # --- Test/Development helpers ---

    def advance_order(
        self,
        broker_order_id: str,
        fill_price: Optional[Decimal] = None,
        partial_qty: Optional[Decimal] = None,
    ) -> bool:
        """
        Manually advance an order (for delayed fill mode testing).

        Args:
            broker_order_id: Order to advance
            fill_price: Price to fill at (uses simulated price if not provided)
            partial_qty: If provided, do a partial fill of this quantity

        Returns:
            True if order was advanced, False if not found or not advanceable
        """
        order = self._orders.get(broker_order_id)
        # Allow advancing pending, working, or partially filled orders
        if not order or order.status not in (
            BrokerOrderStatus.PENDING,
            BrokerOrderStatus.WORKING,
            BrokerOrderStatus.PARTIAL,
        ):
            return False

        return self._fill_order(broker_order_id, fill_price, partial_qty)

    def _fill_order(
        self,
        broker_order_id: str,
        fill_price: Optional[Decimal] = None,
        partial_qty: Optional[Decimal] = None,
    ) -> bool:
        """Internal method to create a fill for an order."""
        order = self._orders.get(broker_order_id)
        if not order:
            return False

        # Get current filled quantity
        current_fills = self._fills.get(broker_order_id, [])
        already_filled = sum(f.fill_qty for f in current_fills)
        remaining_qty = order.request.qty - already_filled

        if remaining_qty <= 0:
            return False

        # Determine fill quantity
        fill_qty = partial_qty if partial_qty else remaining_qty
        fill_qty = min(fill_qty, remaining_qty)

        # Determine fill price
        price = fill_price
        if price is None:
            # Use limit price if available, else last known price, else $100
            if order.request.limit_price:
                price = order.request.limit_price
            elif order.request.symbol in self._last_prices:
                price = self._last_prices[order.request.symbol]
            else:
                price = Decimal("100.00")

        # Apply slippage
        if self.slippage_pct:
            if order.request.side.lower() == "buy":
                price = price * (1 + self.slippage_pct)
            else:
                price = price * (1 - self.slippage_pct)

        # Calculate commission
        notional = fill_qty * price
        commission = max(notional * self.commission_rate, self.min_commission)

        # Create fill
        now = datetime.now(timezone.utc)
        fill = BrokerFill(
            broker_order_id=broker_order_id,
            fill_id=f"fill_{uuid4().hex[:8]}",
            fill_qty=fill_qty,
            fill_price=price,
            commission=commission,
            executed_at=now,
        )
        self._fills.setdefault(broker_order_id, []).append(fill)

        # Update order status
        new_filled = already_filled + fill_qty
        if new_filled >= order.request.qty:
            order.status = BrokerOrderStatus.FILLED
            order.filled_at = now
        else:
            order.status = BrokerOrderStatus.PARTIAL

        return True

    def reset(self) -> None:
        """Clear all orders and fills (for testing)."""
        self._orders.clear()
        self._fills.clear()
        self._last_prices.clear()

    def get_all_orders(self) -> Dict[str, BrokerOrderState]:
        """Get all orders (for testing/debugging)."""
        return {
            order_id: self.get_order_status(order_id)
            for order_id in self._orders
        }


class _StubOrder:
    """Internal order tracking for stub broker."""

    def __init__(
        self,
        broker_order_id: str,
        client_order_id: str,
        request: BrokerOrderRequest,
        status: BrokerOrderStatus,
        submitted_at: datetime,
        filled_at: Optional[datetime] = None,
        rejection_reason: Optional[str] = None,
    ):
        self.broker_order_id = broker_order_id
        self.client_order_id = client_order_id
        self.request = request
        self.status = status
        self.submitted_at = submitted_at
        self.filled_at = filled_at
        self.rejection_reason = rejection_reason
