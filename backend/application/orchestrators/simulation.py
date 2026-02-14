# =========================
# backend/application/orchestrators/simulation.py
# =========================
from datetime import datetime
from typing import Iterable

from domain.services.price_trigger import PriceTrigger
from domain.services.guardrail_evaluator import GuardrailEvaluator
from domain.value_objects.configs import TriggerConfig, GuardrailConfig

from application.ports.market_data import IHistoricalPriceProvider
from application.ports.orders import ISimulationOrderService
from application.ports.repos import ISimulationPositionRepository


class SimulationOrchestrator:
    """Orchestrator for simulation runs."""

    def __init__(
        self,
        historical_data: IHistoricalPriceProvider,
        sim_order_service: ISimulationOrderService,
        sim_position_repo: ISimulationPositionRepository,
    ):
        self.historical_data = historical_data
        self.sim_order_service = sim_order_service
        self.sim_position_repo = sim_position_repo

    def run_simulation(
        self,
        simulation_run_id: str,
        position_id: str,
        timestamps: Iterable[datetime],
        trigger_config: TriggerConfig,
        guardrail_config: GuardrailConfig,
    ) -> None:
        """
        Replays the strategy over a sequence of timestamps:

        - At each ts, get historical MarketQuote
        - Load simulation PositionState for that ts
        - Run same Trigger and Guardrail logic
        - Submit simulated orders (no real broker)
        """
        for ts in timestamps:
            state = self.sim_position_repo.load_sim_position_state(simulation_run_id, position_id)
            quote = self.historical_data.get_quote_at(state.ticker, ts)

            trigger_decision = PriceTrigger.evaluate(
                anchor_price=state.anchor_price,
                current_price=quote.price,
                config=trigger_config,
            )

            if not trigger_decision.fired:
                continue

            guardrail_decision = GuardrailEvaluator.evaluate(
                position_state=state,
                trigger_decision=trigger_decision,
                config=guardrail_config,
                price=quote.price,
            )

            if not guardrail_decision.allowed or guardrail_decision.trade_intent is None:
                continue

            self.sim_order_service.submit_simulated_order(
                simulation_run_id=simulation_run_id,
                position_id=position_id,
                trade_intent=guardrail_decision.trade_intent,
                quote=quote,
            )
