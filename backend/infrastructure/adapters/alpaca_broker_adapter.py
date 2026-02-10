# =========================
# backend/infrastructure/adapters/alpaca_broker_adapter.py
# =========================
"""
Alpaca broker adapter for live/paper trading.

Implements IBrokerService using the Alpaca trading API.
Supports both paper and live trading modes.
"""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, List
import logging

from domain.ports.broker_service import (
    IBrokerService,
    BrokerOrderRequest,
    BrokerOrderResponse,
    BrokerOrderState,
    BrokerOrderStatus,
    BrokerFill,
    MarketHours,
    BrokerError,
    BrokerRejectionError,
)
from infrastructure.config.broker_credentials import AlpacaCredentials

logger = logging.getLogger(__name__)


class AlpacaBrokerAdapter(IBrokerService):
    """
    Alpaca broker implementation.

    Uses the alpaca-py library for API communication.
    Supports market orders with commission tracking.
    """

    def __init__(self, credentials: AlpacaCredentials):
        """
        Initialize Alpaca broker adapter.

        Args:
            credentials: Alpaca API credentials

        Raises:
            ImportError: If alpaca-py is not installed
        """
        self.credentials = credentials
        self._trading_client = None
        self._data_client = None

        # Lazy import to allow stub broker usage without alpaca-py
        try:
            from alpaca.trading.client import TradingClient
            from alpaca.data.historical import StockHistoricalDataClient

            self._trading_client = TradingClient(
                api_key=credentials.api_key,
                secret_key=credentials.secret_key,
                paper=credentials.paper,
            )

            self._data_client = StockHistoricalDataClient(
                api_key=credentials.api_key,
                secret_key=credentials.secret_key,
            )

            logger.info(
                f"Alpaca broker initialized (paper={credentials.paper})"
            )
        except ImportError:
            raise ImportError(
                "alpaca-py is required for Alpaca integration. "
                "Install with: pip install alpaca-py"
            )

    def submit_order(self, request: BrokerOrderRequest) -> BrokerOrderResponse:
        """Submit an order to Alpaca."""
        from alpaca.trading.requests import MarketOrderRequest, LimitOrderRequest
        from alpaca.trading.enums import OrderSide, TimeInForce

        try:
            # Create order request
            side = OrderSide.BUY if request.side.lower() == "buy" else OrderSide.SELL

            if request.order_type == "limit" and request.limit_price:
                order_data = LimitOrderRequest(
                    symbol=request.symbol,
                    qty=float(request.qty),
                    side=side,
                    time_in_force=TimeInForce.DAY,
                    limit_price=float(request.limit_price),
                    client_order_id=request.client_order_id,
                )
            else:
                # Default to market order
                order_data = MarketOrderRequest(
                    symbol=request.symbol,
                    qty=float(request.qty),
                    side=side,
                    time_in_force=TimeInForce.DAY,
                    client_order_id=request.client_order_id,
                )

            # Submit order
            order = self._trading_client.submit_order(order_data)

            logger.info(
                f"Alpaca order submitted: {order.id} for {request.symbol} "
                f"{request.side} {request.qty}"
            )

            return BrokerOrderResponse(
                broker_order_id=str(order.id),
                client_order_id=request.client_order_id,
                status=self._map_order_status(order.status),
                submitted_at=order.submitted_at or datetime.now(timezone.utc),
                message=f"Order submitted: {order.status.value}",
            )

        except Exception as e:
            logger.error(f"Alpaca order submission failed: {e}")
            if "insufficient" in str(e).lower():
                raise BrokerRejectionError(f"Insufficient funds: {e}")
            raise BrokerError(f"Order submission failed: {e}")

    def cancel_order(self, broker_order_id: str) -> bool:
        """Request cancellation of an order."""
        try:
            self._trading_client.cancel_order_by_id(broker_order_id)
            logger.info(f"Alpaca order cancelled: {broker_order_id}")
            return True
        except Exception as e:
            logger.error(f"Alpaca order cancellation failed: {e}")
            return False

    def get_order_status(self, broker_order_id: str) -> Optional[BrokerOrderState]:
        """Get current status of an order."""
        try:
            order = self._trading_client.get_order_by_id(broker_order_id)

            filled_qty = Decimal(str(order.filled_qty)) if order.filled_qty else Decimal(0)
            avg_price = Decimal(str(order.filled_avg_price)) if order.filled_avg_price else None

            return BrokerOrderState(
                broker_order_id=str(order.id),
                client_order_id=order.client_order_id,
                status=self._map_order_status(order.status),
                symbol=order.symbol,
                side=order.side.value.lower(),
                qty=Decimal(str(order.qty)),
                filled_qty=filled_qty,
                avg_fill_price=avg_price,
                submitted_at=order.submitted_at,
                filled_at=order.filled_at,
                last_update=datetime.now(timezone.utc),
                rejection_reason=order.failed_at and "Order failed" or None,
            )

        except Exception as e:
            logger.error(f"Failed to get order status: {e}")
            return None

    def get_fills(self, broker_order_id: str) -> List[BrokerFill]:
        """Get all fills for an order."""
        try:
            order = self._trading_client.get_order_by_id(broker_order_id)

            if not order.filled_qty or float(order.filled_qty) == 0:
                return []

            # Alpaca provides aggregate fill info, not individual fills
            # Create a single fill record from the aggregate data
            fill_qty = Decimal(str(order.filled_qty))
            fill_price = Decimal(str(order.filled_avg_price)) if order.filled_avg_price else Decimal(0)

            # Alpaca doesn't charge commissions for most trades
            # But we can estimate based on SEC/FINRA fees for sells
            commission = Decimal("0")
            if order.side.value.lower() == "sell":
                # SEC fee: $8 per $1M, FINRA TAF: $0.000119 per share (max $5.95)
                notional = fill_qty * fill_price
                sec_fee = notional * Decimal("0.000008")
                finra_fee = min(fill_qty * Decimal("0.000119"), Decimal("5.95"))
                commission = sec_fee + finra_fee

            return [
                BrokerFill(
                    broker_order_id=broker_order_id,
                    fill_id=f"{broker_order_id}_fill",
                    fill_qty=fill_qty,
                    fill_price=fill_price,
                    commission=commission,
                    executed_at=order.filled_at or datetime.now(timezone.utc),
                )
            ]

        except Exception as e:
            logger.error(f"Failed to get fills: {e}")
            return []

    def is_market_open(self) -> bool:
        """Check if US stock market is open."""
        try:
            clock = self._trading_client.get_clock()
            return clock.is_open
        except Exception as e:
            logger.error(f"Failed to check market hours: {e}")
            return False

    def get_market_hours(self) -> MarketHours:
        """Get market hours info."""
        try:
            clock = self._trading_client.get_clock()

            session = "regular"
            if not clock.is_open:
                session = "closed"
            # Note: Alpaca clock doesn't distinguish pre/post market in basic API

            return MarketHours(
                is_open=clock.is_open,
                current_time=clock.timestamp,
                session=session,
                next_open=clock.next_open,
                next_close=clock.next_close,
            )

        except Exception as e:
            logger.error(f"Failed to get market hours: {e}")
            return MarketHours(
                is_open=False,
                current_time=datetime.now(timezone.utc),
                session="unknown",
            )

    def _map_order_status(self, alpaca_status) -> BrokerOrderStatus:
        """Map Alpaca order status to our BrokerOrderStatus."""
        # Import here to avoid issues if alpaca-py isn't installed
        from alpaca.trading.enums import OrderStatus as AlpacaOrderStatus

        status_map = {
            AlpacaOrderStatus.NEW: BrokerOrderStatus.PENDING,
            AlpacaOrderStatus.ACCEPTED: BrokerOrderStatus.PENDING,
            AlpacaOrderStatus.PENDING_NEW: BrokerOrderStatus.PENDING,
            AlpacaOrderStatus.ACCEPTED_FOR_BIDDING: BrokerOrderStatus.PENDING,
            AlpacaOrderStatus.PARTIALLY_FILLED: BrokerOrderStatus.PARTIAL,
            AlpacaOrderStatus.FILLED: BrokerOrderStatus.FILLED,
            AlpacaOrderStatus.DONE_FOR_DAY: BrokerOrderStatus.FILLED,
            AlpacaOrderStatus.CANCELED: BrokerOrderStatus.CANCELLED,
            AlpacaOrderStatus.EXPIRED: BrokerOrderStatus.CANCELLED,
            AlpacaOrderStatus.REPLACED: BrokerOrderStatus.CANCELLED,
            AlpacaOrderStatus.PENDING_CANCEL: BrokerOrderStatus.WORKING,
            AlpacaOrderStatus.PENDING_REPLACE: BrokerOrderStatus.WORKING,
            AlpacaOrderStatus.REJECTED: BrokerOrderStatus.REJECTED,
            AlpacaOrderStatus.SUSPENDED: BrokerOrderStatus.REJECTED,
            AlpacaOrderStatus.STOPPED: BrokerOrderStatus.WORKING,
            AlpacaOrderStatus.CALCULATED: BrokerOrderStatus.WORKING,
        }

        return status_map.get(alpaca_status, BrokerOrderStatus.PENDING)

    def get_account(self) -> dict:
        """Get account information (for debugging/monitoring)."""
        try:
            account = self._trading_client.get_account()
            return {
                "buying_power": float(account.buying_power),
                "cash": float(account.cash),
                "portfolio_value": float(account.portfolio_value),
                "equity": float(account.equity),
                "status": account.status.value,
                "trading_blocked": account.trading_blocked,
                "pattern_day_trader": account.pattern_day_trader,
            }
        except Exception as e:
            logger.error(f"Failed to get account: {e}")
            return {}

    def get_positions(self) -> List[dict]:
        """Get all positions (for debugging/monitoring)."""
        try:
            positions = self._trading_client.get_all_positions()
            return [
                {
                    "symbol": p.symbol,
                    "qty": float(p.qty),
                    "avg_entry_price": float(p.avg_entry_price),
                    "market_value": float(p.market_value),
                    "current_price": float(p.current_price),
                    "unrealized_pl": float(p.unrealized_pl),
                    "unrealized_plpc": float(p.unrealized_plpc),
                }
                for p in positions
            ]
        except Exception as e:
            logger.error(f"Failed to get positions: {e}")
            return []
