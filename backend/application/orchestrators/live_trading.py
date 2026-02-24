# =========================
# backend/application/orchestrators/live_trading.py
# =========================
from typing import Optional, TYPE_CHECKING
import uuid

from application.ports.market_data import IMarketDataProvider
from application.ports.orders import IOrderService
from application.ports.repos import IPositionRepository
from domain.ports.portfolio_repo import PortfolioRepo

if TYPE_CHECKING:
    from application.use_cases.evaluate_position_uc import EvaluatePositionUC


class LiveTradingOrchestrator:
    """Orchestrator for live trading cycles."""

    def __init__(
        self,
        market_data: IMarketDataProvider,
        order_service: IOrderService,
        position_repo: IPositionRepository,
        portfolio_repo: Optional[PortfolioRepo] = None,
        evaluate_position_uc: Optional["EvaluatePositionUC"] = None,
        orders_repo=None,
    ):
        self.market_data = market_data
        self.order_service = order_service
        self.position_repo = position_repo
        self.portfolio_repo = portfolio_repo
        self.evaluate_position_uc = evaluate_position_uc
        self.orders_repo = orders_repo

    def run_cycle(self, source: str = "worker") -> None:
        """
        One trading cycle for all active positions.

        Args:
            source: Source of the cycle trigger ("worker", "api/manual", etc.)
        """
        import logging
        logger = logging.getLogger(__name__)

        positions_evaluated = 0
        errors_count = 0

        active_positions = list(self.position_repo.get_active_positions_for_trading())
        logger.info("Trading cycle starting: %d active positions to evaluate", len(active_positions))

        for position_id in active_positions:
            result = self.run_cycle_for_position(position_id, source=source)
            positions_evaluated += 1
            if result is None:
                errors_count += 1

        logger.info(
            "Trading cycle complete: %d positions evaluated, %d errors",
            positions_evaluated, errors_count
        )

    def run_cycle_for_position(self, position_id: str, source: str = "worker") -> Optional[str]:
        """
        Run one trading cycle for a single position.

        Args:
            position_id: ID of the position to evaluate
            source: Source of the cycle trigger ("worker", "api/manual", etc.)

        Returns:
            trace_id if cycle was executed, None if position not found or inactive
        """
        import logging
        logger = logging.getLogger(__name__)

        try:
            # Check if position is active
            active_positions = list(self.position_repo.get_active_positions_for_trading())
            if position_id not in active_positions:
                self._log_inactive_position(position_id, logger)
                return None

            trace_id = str(uuid.uuid4())

            if not self.evaluate_position_uc:
                logger.error("No evaluate_position_uc available for position %s", position_id)
                return None

            # Find tenant_id and portfolio_id for this position
            tenant_id, portfolio_id = self._find_position_context(position_id, logger)
            if not portfolio_id:
                logger.warning(
                    "Could not find portfolio_id for position %s, skipping", position_id
                )
                return None

            # Run full evaluation through use case
            # (handles market hours, triggers, guardrails, timeline logging)
            evaluation_result = self.evaluate_position_uc.evaluate_with_market_data(
                tenant_id=tenant_id,
                portfolio_id=portfolio_id,
                position_id=position_id,
                source=source,
            )

            trigger_detected = evaluation_result.get("trigger_detected", False)
            order_proposal = evaluation_result.get("order_proposal")

            logger.info(
                "Evaluation result for position %s: trigger_detected=%s, has_order_proposal=%s",
                position_id, trigger_detected, order_proposal is not None,
            )

            if not trigger_detected or not order_proposal:
                return trace_id  # No trade needed

            # Validate order proposal
            validation = order_proposal.get("validation", {})
            is_valid = validation.get("valid", False)
            rejections = validation.get("rejections", [])

            if not is_valid:
                logger.warning(
                    "Order validation failed for position %s: rejections=%s",
                    position_id, rejections,
                )
                return trace_id

            # Check for pending/unfilled orders before submitting
            if self.orders_repo:
                open_statuses = {"created", "submitted", "pending", "working", "partial"}
                existing_orders = self.orders_repo.list_for_position(position_id, limit=20)
                for existing_order in existing_orders:
                    if existing_order.status in open_statuses:
                        logger.warning(
                            "Skipping order for position %s: pending order %s is still %s",
                            position_id, existing_order.id, existing_order.status,
                        )
                        return trace_id

            # Fetch quote for order submission
            state = self.position_repo.load_position_state(position_id)
            quote = self.market_data.get_latest_quote(state.ticker)

            # Submit order
            self._submit_and_execute_order(
                position_id=position_id,
                portfolio_id=portfolio_id,
                tenant_id=tenant_id,
                order_proposal=order_proposal,
                quote=quote,
                logger=logger,
            )

            return trace_id

        except Exception as e:
            logger.error(
                "Error in trading cycle for position %s: %s",
                position_id, e,
                exc_info=True,
                extra={
                    "position_id": position_id,
                    "source": source,
                    "trace_id": trace_id if "trace_id" in locals() else None,
                },
            )
            return None

    def _find_position_context(self, position_id: str, logger):
        """Find tenant_id and portfolio_id for a position."""
        tenant_id = "default"
        portfolio_id = None

        if self.portfolio_repo:
            portfolios = self.portfolio_repo.list_all(tenant_id=tenant_id)
            for portfolio in portfolios:
                from app.di import container
                pos = container.positions.get(
                    tenant_id=tenant_id,
                    portfolio_id=portfolio.id,
                    position_id=position_id,
                )
                if pos:
                    portfolio_id = portfolio.id
                    logger.info("Found position %s in portfolio %s", position_id, portfolio_id)
                    break

        return tenant_id, portfolio_id

    def _log_inactive_position(self, position_id: str, logger):
        """Log why a position is not active."""
        try:
            if not self.portfolio_repo:
                logger.warning("Position %s not in active positions list", position_id)
                return

            search_tenant_id = "default"
            position_found = False
            portfolio_running = False
            has_anchor = False

            portfolios = self.portfolio_repo.list_all(tenant_id=search_tenant_id)
            for portfolio in portfolios:
                from app.di import container
                positions = container.positions.list_all(
                    tenant_id=portfolio.tenant_id,
                    portfolio_id=portfolio.id,
                )
                for pos in positions:
                    if pos.id == position_id:
                        position_found = True
                        has_anchor = pos.anchor_price is not None
                        portfolio_running = portfolio.trading_state == "RUNNING"
                        break
                if position_found:
                    break

            if not position_found:
                logger.warning("Position %s not found in any portfolio", position_id)
            elif not portfolio_running:
                logger.warning("Position %s found but portfolio is not RUNNING", position_id)
            elif not has_anchor:
                logger.warning("Position %s found but anchor_price is not set", position_id)
        except Exception as e:
            logger.warning("Error checking position status for %s: %s", position_id, e)

    def _submit_and_execute_order(
        self, position_id, portfolio_id, tenant_id, order_proposal, quote, logger
    ):
        """Submit and auto-execute an order from an order proposal."""
        from domain.value_objects.trade_intent import TradeIntent
        from decimal import Decimal

        side_str = order_proposal.get("side", "").upper()
        if side_str not in ["BUY", "SELL"]:
            raise ValueError(f"Invalid order side: {order_proposal.get('side')}")

        trade_intent = TradeIntent(
            side=side_str.lower(),
            qty=Decimal(str(order_proposal.get("trimmed_qty", 0))),
            reason=order_proposal.get("reasoning") or "Trigger condition met",
        )

        logger.info(
            "Submitting order for position %s: side=%s, qty=%s",
            position_id, trade_intent.side, trade_intent.qty,
        )

        order_id = self.order_service.submit_live_order(
            position_id=position_id,
            portfolio_id=portfolio_id,
            tenant_id=tenant_id,
            trade_intent=trade_intent,
            quote=quote,
        )

        logger.info("Order submitted successfully: order_id=%s", order_id)

        # Execute the order immediately (auto-fill in live trading)
        try:
            from application.use_cases.execute_order_uc import ExecuteOrderUC
            from application.dto.orders import FillOrderRequest
            from app.di import container

            execute_uc = ExecuteOrderUC(
                positions=container.positions,
                orders=container.orders,
                trades=container.trades,
                events=container.events,
                clock=container.clock,
                guardrail_config_provider=container.guardrail_config_provider,
                order_policy_config_provider=container.order_policy_config_provider,
                evaluation_timeline_repo=container.evaluation_timeline,
            )

            fill_request = FillOrderRequest(
                qty=float(trade_intent.qty),
                price=float(quote.price),
                commission=order_proposal.get("commission", 0.0),
            )

            fill_response = execute_uc.execute(order_id, fill_request)

            logger.info(
                "Order executed successfully: order_id=%s, filled_qty=%s, status=%s",
                order_id, fill_response.filled_qty, fill_response.status,
            )
        except Exception as exec_error:
            logger.error(
                "Failed to execute order %s: %s", order_id, exec_error,
                exc_info=True,
            )
