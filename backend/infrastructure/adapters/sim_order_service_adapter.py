# =========================
# backend/infrastructure/adapters/sim_order_service_adapter.py
# =========================
"""Adapter implementing ISimulationOrderService for simulation orders."""

from application.ports.orders import ISimulationOrderService
from domain.value_objects.trade_intent import TradeIntent
from domain.value_objects.market import MarketQuote
from uuid import uuid4


class SimOrderServiceAdapter(ISimulationOrderService):
    """Adapter that implements ISimulationOrderService for simulation orders."""

    def __init__(self, simulation_repo):
        """
        Initialize adapter with simulation repository.

        Args:
            simulation_repo: Simulation repository for storing simulation orders
        """
        self.simulation_repo = simulation_repo

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
        # Generate simulation order ID
        sim_order_id = f"sim_ord_{uuid4().hex[:8]}"

        # Store simulation order
        # TODO: Implement proper storage in simulation repository
        # For now, we'll just return the ID
        # In a full implementation, this would store the order in simulation tables

        return sim_order_id
