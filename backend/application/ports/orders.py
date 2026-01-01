# =========================
# backend/application/ports/orders.py
# =========================
from abc import ABC, abstractmethod

from domain.value_objects.trade_intent import TradeIntent
from domain.value_objects.market import MarketQuote


class IOrderService(ABC):
    """Port for live order submission."""

    @abstractmethod
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
        ...


class ISimulationOrderService(ABC):
    """Port for simulated order submission."""

    @abstractmethod
    def submit_simulated_order(
        self,
        simulation_run_id: str,
        position_id: str,
        trade_intent: TradeIntent,
        quote: MarketQuote,
    ) -> str:
        """
        Simulation only.
        No broker calls.
        Writes simulated orders in sim tables, returns sim_order_id.
        """
        ...
