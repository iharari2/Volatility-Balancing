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
from application.ports.event_logger import IEventLogger
from application.events import EventType


class SimulationOrchestrator:
    """Orchestrator for simulation runs."""

    def __init__(
        self,
        historical_data: IHistoricalPriceProvider,
        sim_order_service: ISimulationOrderService,
        sim_position_repo: ISimulationPositionRepository,
        event_logger: IEventLogger,
    ):
        self.historical_data = historical_data
        self.sim_order_service = sim_order_service
        self.sim_position_repo = sim_position_repo
        self.event_logger = event_logger

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
        - Log all events under simulation_run_id with trace_id
        """
        # Use simulation_run_id as trace_id for all events in this simulation
        trace_id = simulation_run_id

        for ts in timestamps:
            state = self.sim_position_repo.load_sim_position_state(simulation_run_id, position_id)
            quote = self.historical_data.get_quote_at(state.ticker, ts)

            # 1. Log price event
            price_event = self.event_logger.log(
                EventType.PRICE_EVENT,
                asset_id=state.ticker,
                trace_id=trace_id,
                source="simulation",
                payload={
                    "simulation_run_id": simulation_run_id,
                    "position_id": position_id,
                    "ticker": state.ticker,
                    "price": str(quote.price),
                    "timestamp": ts.isoformat(),
                    "anchor_price": str(state.anchor_price) if state.anchor_price else None,
                },
            )

            trigger_decision = PriceTrigger.evaluate(
                anchor_price=state.anchor_price,
                current_price=quote.price,
                config=trigger_config,
            )

            # 2. Log trigger evaluation
            trigger_event = self.event_logger.log(
                EventType.TRIGGER_EVALUATED,
                asset_id=state.ticker,
                trace_id=trace_id,
                parent_event_id=price_event.event_id,
                source="simulation",
                payload={
                    "simulation_run_id": simulation_run_id,
                    "position_id": position_id,
                    "ts": ts.isoformat(),
                    "trigger_decision": {
                        "fired": trigger_decision.fired,
                        "direction": trigger_decision.direction,
                        "reason": trigger_decision.reason,
                    },
                },
            )

            if not trigger_decision.fired:
                continue

            guardrail_decision = GuardrailEvaluator.evaluate(
                position_state=state,
                trigger_decision=trigger_decision,
                config=guardrail_config,
                price=quote.price,
            )

            # 3. Log guardrail evaluation
            guardrail_event = self.event_logger.log(
                EventType.GUARDRAIL_EVALUATED,
                asset_id=state.ticker,
                trace_id=trace_id,
                parent_event_id=trigger_event.event_id,
                source="simulation",
                payload={
                    "simulation_run_id": simulation_run_id,
                    "position_id": position_id,
                    "decision": {
                        "allowed": guardrail_decision.allowed,
                        "reason": guardrail_decision.reason,
                        "trade_intent": (
                            {
                                "side": guardrail_decision.trade_intent.side,
                                "qty": str(guardrail_decision.trade_intent.qty),
                                "reason": guardrail_decision.trade_intent.reason,
                            }
                            if guardrail_decision.trade_intent
                            else None
                        ),
                    },
                },
            )

            if not guardrail_decision.allowed or guardrail_decision.trade_intent is None:
                continue

            sim_order_id = self.sim_order_service.submit_simulated_order(
                simulation_run_id=simulation_run_id,
                position_id=position_id,
                trade_intent=guardrail_decision.trade_intent,
                quote=quote,
            )

            # 4. Log order creation
            self.event_logger.log(
                EventType.ORDER_CREATED,
                asset_id=state.ticker,
                trace_id=trace_id,
                parent_event_id=guardrail_event.event_id,
                source="simulation",
                payload={
                    "simulation_run_id": simulation_run_id,
                    "position_id": position_id,
                    "sim_order_id": sim_order_id,
                    "trade_intent": {
                        "side": guardrail_decision.trade_intent.side,
                        "qty": str(guardrail_decision.trade_intent.qty),
                        "reason": guardrail_decision.trade_intent.reason,
                    },
                    "quote": {
                        "ticker": quote.ticker,
                        "price": str(quote.price),
                        "timestamp": quote.timestamp.isoformat(),
                    },
                },
            )
