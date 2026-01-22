# =========================
# backend/domain/ports/broker_service.py
# =========================
"""
Broker service port (interface) for order execution.

This abstraction layer enables switching between stub (development/testing)
and real broker (Alpaca) implementations.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Optional, List


class BrokerOrderStatus(str, Enum):
    """Status of an order at the broker."""
    PENDING = "pending"       # Order submitted, awaiting acceptance
    WORKING = "working"       # Order accepted, in the market
    PARTIAL = "partial"       # Partially filled
    FILLED = "filled"         # Completely filled
    REJECTED = "rejected"     # Rejected by broker
    CANCELLED = "cancelled"   # Cancelled by user or system
    EXPIRED = "expired"       # Time-in-force expired


@dataclass
class BrokerOrderRequest:
    """Request to submit an order to the broker."""
    client_order_id: str           # Our internal order ID for reference
    symbol: str                     # Ticker symbol (e.g., "AAPL")
    side: str                       # "buy" or "sell"
    qty: Decimal                    # Number of shares
    order_type: str = "market"      # "market", "limit", "stop", "stop_limit"
    limit_price: Optional[Decimal] = None  # For limit orders
    stop_price: Optional[Decimal] = None   # For stop orders
    time_in_force: str = "day"      # "day", "gtc", "ioc", "fok"
    extended_hours: bool = False    # Allow extended hours trading


@dataclass
class BrokerOrderResponse:
    """Response from broker after order submission."""
    broker_order_id: str           # Broker's ID for this order
    client_order_id: str           # Our internal order ID echoed back
    status: BrokerOrderStatus      # Current status
    submitted_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    message: Optional[str] = None  # Any message from broker (e.g., rejection reason)


@dataclass
class BrokerOrderState:
    """Current state of an order at the broker."""
    broker_order_id: str
    client_order_id: str
    status: BrokerOrderStatus
    symbol: str
    side: str
    qty: Decimal
    filled_qty: Decimal = Decimal("0")
    avg_fill_price: Optional[Decimal] = None
    submitted_at: Optional[datetime] = None
    filled_at: Optional[datetime] = None
    last_update: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    rejection_reason: Optional[str] = None


@dataclass
class BrokerFill:
    """A fill (execution) event from the broker."""
    broker_order_id: str           # Which order this fill belongs to
    fill_id: str                   # Unique fill identifier
    fill_qty: Decimal              # Shares filled in this event
    fill_price: Decimal            # Price per share
    commission: Decimal            # Commission charged for this fill
    executed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class MarketHours:
    """Market hours information."""
    is_open: bool
    current_time: datetime
    next_open: Optional[datetime] = None
    next_close: Optional[datetime] = None
    session: str = "regular"  # "regular", "pre-market", "after-hours", "closed"


class IBrokerService(ABC):
    """
    Abstract interface for broker operations.

    Implementations:
    - StubBrokerAdapter: For development and testing
    - AlpacaBrokerAdapter: For live trading with Alpaca
    """

    @abstractmethod
    def submit_order(self, request: BrokerOrderRequest) -> BrokerOrderResponse:
        """
        Submit an order to the broker.

        Args:
            request: Order details to submit

        Returns:
            BrokerOrderResponse with broker_order_id and initial status

        Raises:
            BrokerConnectionError: If cannot connect to broker
            BrokerRejectionError: If order is immediately rejected
        """
        ...

    @abstractmethod
    def cancel_order(self, broker_order_id: str) -> bool:
        """
        Request cancellation of an order.

        Args:
            broker_order_id: The broker's order ID to cancel

        Returns:
            True if cancellation request was accepted, False otherwise
            Note: A True return doesn't mean the order is cancelled,
            just that the request was submitted. Check status for confirmation.
        """
        ...

    @abstractmethod
    def get_order_status(self, broker_order_id: str) -> Optional[BrokerOrderState]:
        """
        Get current status of an order.

        Args:
            broker_order_id: The broker's order ID

        Returns:
            Current state of the order, or None if not found
        """
        ...

    @abstractmethod
    def get_fills(self, broker_order_id: str) -> List[BrokerFill]:
        """
        Get all fills for an order.

        Args:
            broker_order_id: The broker's order ID

        Returns:
            List of fills (executions) for this order, empty if none
        """
        ...

    @abstractmethod
    def is_market_open(self) -> bool:
        """
        Check if the market is currently open for trading.

        Returns:
            True if regular market hours, False otherwise
        """
        ...

    @abstractmethod
    def get_market_hours(self) -> MarketHours:
        """
        Get detailed market hours information.

        Returns:
            MarketHours with current session info and times
        """
        ...


class BrokerError(Exception):
    """Base exception for broker operations."""
    pass


class BrokerConnectionError(BrokerError):
    """Raised when unable to connect to the broker."""
    pass


class BrokerRejectionError(BrokerError):
    """Raised when an order is rejected by the broker."""
    def __init__(self, message: str, rejection_reason: Optional[str] = None):
        super().__init__(message)
        self.rejection_reason = rejection_reason
