# backend/application/use_cases/evaluate_experiment_uc.py
from __future__ import annotations

import logging
from typing import Dict, Any, Optional

from domain.ports.trading_experiment_repo import TradingExperimentRepo
from domain.ports.positions_repo import PositionsRepo
from domain.ports.market_data import MarketDataRepo
from application.use_cases.evaluate_position_uc import EvaluatePositionUC
from application.services.broker_integration_service import BrokerIntegrationService


class EvaluateExperimentUC:
    """
    Use case for running one evaluation cycle on a trading experiment.

    Steps:
    1. Get current price
    2. Run position evaluation (EvaluatePositionUC)
    3. Execute trade via broker if triggered
    4. Update experiment metrics
    """

    _logger = logging.getLogger(__name__)

    def __init__(
        self,
        experiment_repo: TradingExperimentRepo,
        positions_repo: PositionsRepo,
        market_data: MarketDataRepo,
        evaluate_position_uc: EvaluatePositionUC,
        broker_integration: Optional[BrokerIntegrationService] = None,
    ) -> None:
        self.experiment_repo = experiment_repo
        self.positions_repo = positions_repo
        self.market_data = market_data
        self.evaluate_position_uc = evaluate_position_uc
        self.broker_integration = broker_integration

    def execute(
        self,
        tenant_id: str,
        experiment_id: str,
    ) -> Dict[str, Any]:
        """
        Run one evaluation tick on the experiment.

        Args:
            tenant_id: Tenant identifier
            experiment_id: Experiment to evaluate

        Returns:
            Dict with evaluation results
        """
        # Get experiment
        experiment = self.experiment_repo.get(tenant_id, experiment_id)
        if not experiment:
            raise KeyError(f"Experiment not found: {experiment_id}")

        if experiment.status != "RUNNING":
            return {
                "experiment_id": experiment_id,
                "message": f"Experiment is {experiment.status}, not running",
                "trigger_detected": False,
                "trade_executed": False,
            }

        # Get current price
        price_data = self.market_data.get_reference_price(experiment.ticker)
        if not price_data:
            raise ValueError(f"Unable to fetch price for ticker: {experiment.ticker}")

        current_price = price_data.price

        # Get position to check current value before evaluation
        position = self.positions_repo.get(
            tenant_id=tenant_id,
            portfolio_id=experiment.portfolio_id,
            position_id=experiment.position_id,
        )
        if not position:
            raise KeyError(f"Position not found: {experiment.position_id}")

        previous_portfolio_value = position.get_total_value(current_price)

        self._logger.debug(
            "Evaluating experiment %s: price=%.2f, prev_value=%.2f",
            experiment_id,
            current_price,
            previous_portfolio_value,
        )

        # Run position evaluation
        evaluation_result = self.evaluate_position_uc.evaluate(
            tenant_id=tenant_id,
            portfolio_id=experiment.portfolio_id,
            position_id=experiment.position_id,
            current_price=current_price,
        )

        trigger_detected = evaluation_result.get("trigger_detected", False)
        order_proposal = evaluation_result.get("order_proposal")
        trade_executed = False
        action_taken = None
        order_qty = None
        commission = 0.0

        # Execute trade if trigger detected and order is valid
        if trigger_detected and order_proposal:
            validation = order_proposal.get("validation", {})
            if validation.get("valid", False):
                # Execute the order via broker integration
                trade_executed, trade_result = self._execute_trade(
                    tenant_id=tenant_id,
                    portfolio_id=experiment.portfolio_id,
                    position_id=experiment.position_id,
                    side=order_proposal["side"],
                    qty=abs(order_proposal["trimmed_qty"]),
                    current_price=current_price,
                )
                if trade_executed:
                    action_taken = order_proposal["side"]
                    order_qty = abs(order_proposal["trimmed_qty"])
                    commission = trade_result.get("commission", 0.0)

        # Re-fetch position to get updated values after trade
        position = self.positions_repo.get(
            tenant_id=tenant_id,
            portfolio_id=experiment.portfolio_id,
            position_id=experiment.position_id,
        )

        new_portfolio_value = position.get_total_value(current_price)

        # Update experiment metrics
        experiment.update_metrics(
            current_price=current_price,
            portfolio_value=new_portfolio_value,
            trade_executed=trade_executed,
            commission=commission,
        )
        self.experiment_repo.save(experiment)

        self._logger.info(
            "Experiment %s tick complete: price=%.2f, value=%.2f, buyhold=%.2f, trade=%s",
            experiment_id,
            current_price,
            new_portfolio_value,
            experiment.current_buyhold_value,
            trade_executed,
        )

        return {
            "experiment_id": experiment_id,
            "current_price": current_price,
            "previous_portfolio_value": previous_portfolio_value,
            "new_portfolio_value": new_portfolio_value,
            "buyhold_value": experiment.current_buyhold_value,
            "trigger_detected": trigger_detected,
            "trade_executed": trade_executed,
            "action_taken": action_taken,
            "order_qty": order_qty,
            "evaluation_count": experiment.evaluation_count,
            "message": self._build_message(
                trigger_detected, trade_executed, action_taken, order_qty
            ),
        }

    def _execute_trade(
        self,
        tenant_id: str,
        portfolio_id: str,
        position_id: str,
        side: str,
        qty: float,
        current_price: float,
    ) -> tuple[bool, Dict[str, Any]]:
        """
        Execute a trade via the broker integration service.

        Returns (success, result_dict)
        """
        if not self.broker_integration:
            self._logger.warning("No broker integration configured, skipping trade execution")
            return False, {}

        try:
            # Use broker integration to submit and execute order
            from application.dto.orders import CreateOrderRequest

            # Create order through broker integration
            # The broker integration service handles submission and fill
            order_request = CreateOrderRequest(side=side, qty=qty)

            # We need to create the order and submit it to the broker
            # For the stub broker, orders fill immediately
            from domain.entities.order import Order
            from uuid import uuid4
            from datetime import datetime, timezone

            order = Order(
                id=f"ord_{uuid4().hex[:8]}",
                tenant_id=tenant_id,
                portfolio_id=portfolio_id,
                position_id=position_id,
                side=side,
                qty=qty,
                status="created",
                idempotency_key=f"exp_tick_{uuid4().hex[:8]}",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )

            # Get the orders repo from broker integration
            orders_repo = self.broker_integration._orders_repo
            orders_repo.save(order)

            # Submit to broker
            result = self.broker_integration.submit_order(
                order=order,
                ticker=None,  # Will be fetched from position if needed
            )

            if result.get("success"):
                # Get commission from order after fill
                updated_order = orders_repo.get(order.id)
                commission = updated_order.total_commission if updated_order else 0.0
                return True, {"commission": commission}
            else:
                return False, {"error": result.get("error", "Unknown error")}

        except Exception as e:
            self._logger.error("Trade execution failed: %s", e)
            return False, {"error": str(e)}

    def _build_message(
        self,
        trigger_detected: bool,
        trade_executed: bool,
        action_taken: Optional[str],
        order_qty: Optional[float],
    ) -> str:
        """Build a human-readable message about the evaluation result."""
        if not trigger_detected:
            return "No trigger detected - position unchanged"

        if trade_executed and action_taken and order_qty:
            return f"Trade executed: {action_taken} {order_qty:.4f} shares"

        return "Trigger detected but trade not executed"


class CompleteExperimentUC:
    """Use case for completing a trading experiment."""

    _logger = logging.getLogger(__name__)

    def __init__(
        self,
        experiment_repo: TradingExperimentRepo,
        positions_repo: PositionsRepo,
        market_data: MarketDataRepo,
    ) -> None:
        self.experiment_repo = experiment_repo
        self.positions_repo = positions_repo
        self.market_data = market_data

    def execute(
        self,
        tenant_id: str,
        experiment_id: str,
    ) -> Dict[str, Any]:
        """
        Complete an experiment and calculate final metrics.

        Args:
            tenant_id: Tenant identifier
            experiment_id: Experiment to complete

        Returns:
            Dict with final experiment results
        """
        experiment = self.experiment_repo.get(tenant_id, experiment_id)
        if not experiment:
            raise KeyError(f"Experiment not found: {experiment_id}")

        if experiment.status == "COMPLETED":
            return {
                "experiment_id": experiment_id,
                "message": "Experiment already completed",
                "status": experiment.status,
            }

        # Get final price
        price_data = self.market_data.get_reference_price(experiment.ticker)
        if price_data:
            current_price = price_data.price

            # Get position for final value
            position = self.positions_repo.get(
                tenant_id=tenant_id,
                portfolio_id=experiment.portfolio_id,
                position_id=experiment.position_id,
            )
            if position:
                final_portfolio_value = position.get_total_value(current_price)
                experiment.current_portfolio_value = final_portfolio_value
                experiment.current_buyhold_value = experiment.calculate_buyhold_value(current_price)

        # Mark as completed
        experiment.complete()
        self.experiment_repo.save(experiment)

        self._logger.info(
            "Experiment %s completed: portfolio=%.2f, buyhold=%.2f, excess=%.2f%%",
            experiment_id,
            experiment.current_portfolio_value,
            experiment.current_buyhold_value,
            experiment.get_excess_return_pct(),
        )

        return {
            "experiment_id": experiment_id,
            "status": experiment.status,
            "started_at": experiment.started_at.isoformat(),
            "ended_at": experiment.ended_at.isoformat() if experiment.ended_at else None,
            "days_running": experiment.get_days_running(),
            "initial_capital": experiment.initial_capital,
            "final_portfolio_value": experiment.current_portfolio_value,
            "final_buyhold_value": experiment.current_buyhold_value,
            "portfolio_return_pct": experiment.get_portfolio_return_pct(),
            "buyhold_return_pct": experiment.get_buyhold_return_pct(),
            "excess_return_pct": experiment.get_excess_return_pct(),
            "total_evaluations": experiment.evaluation_count,
            "total_trades": experiment.trade_count,
            "total_commission": experiment.total_commission_paid,
        }
