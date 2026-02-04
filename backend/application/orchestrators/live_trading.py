# =========================
# backend/application/orchestrators/live_trading.py
# =========================
from typing import Callable, Optional, TYPE_CHECKING
import uuid

from domain.services.price_trigger import PriceTrigger
from domain.services.guardrail_evaluator import GuardrailEvaluator
from domain.value_objects.configs import TriggerConfig, GuardrailConfig
# Note: container is imported inside functions to avoid circular import

from application.ports.market_data import IMarketDataProvider
from application.ports.orders import IOrderService
from application.ports.repos import IPositionRepository
from application.ports.event_logger import IEventLogger
from application.events import EventType
from domain.ports.portfolio_repo import PortfolioRepo
from domain.ports.market_data import MarketDataRepo

if TYPE_CHECKING:
    from application.use_cases.evaluate_position_uc import EvaluatePositionUC


class LiveTradingOrchestrator:
    """Orchestrator for live trading cycles."""

    def __init__(
        self,
        market_data: IMarketDataProvider,
        order_service: IOrderService,
        position_repo: IPositionRepository,
        event_logger: IEventLogger,
        trigger_config_provider: Callable[[str], TriggerConfig],
        guardrail_config_provider: Callable[[str], GuardrailConfig],
        portfolio_repo: Optional[PortfolioRepo] = None,
        market_data_repo: Optional[MarketDataRepo] = None,
        evaluate_position_uc: Optional["EvaluatePositionUC"] = None,
    ):
        self.market_data = market_data
        self.order_service = order_service
        self.position_repo = position_repo
        self.event_logger = event_logger
        self.trigger_config_provider = trigger_config_provider
        self.guardrail_config_provider = guardrail_config_provider
        self.portfolio_repo = portfolio_repo
        self.market_data_repo = market_data_repo  # For getting PriceData with is_market_hours
        self.evaluate_position_uc = evaluate_position_uc

    def run_cycle(self, source: str = "worker") -> None:
        """
        One trading cycle for all active positions:

        - For each active position:
          - Load PositionState
          - Fetch latest MarketQuote
          - Get trigger & guardrail configs
          - Evaluate Trigger
          - Evaluate Guardrails
          - If allowed => send TradeIntent to IOrderService
          - Log all decisions with trace_id for full audit trail

        Args:
            source: Source of the cycle trigger ("worker", "api/manual", etc.)
        """
        import logging
        logger = logging.getLogger(__name__)

        positions_evaluated = 0
        triggers_fired = 0
        orders_created = 0
        errors_count = 0

        active_positions = list(self.position_repo.get_active_positions_for_trading())
        logger.info("Trading cycle starting: %d active positions to evaluate", len(active_positions))

        for position_id in active_positions:
            result = self.run_cycle_for_position(position_id, source=source)
            positions_evaluated += 1
            if result is not None:
                # Check if order was created by looking at event log
                # Note: This is a simplified check - actual order creation is tracked in run_cycle_for_position
                pass
            else:
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
        try:
            # Check if position is active (exists and is enabled for trading)
            # We'll check by trying to load it and see if it's in active positions
            active_positions = list(self.position_repo.get_active_positions_for_trading())
            if position_id not in active_positions:
                # Try to find the position to provide a more specific error message
                try:
                    # Search for the position to check why it's not active
                    search_tenant_id = "default"
                    position_found = False
                    portfolio_running = False
                    has_anchor = False

                    if self.portfolio_repo:
                        portfolios = self.portfolio_repo.list_all(tenant_id=search_tenant_id)
                        for portfolio in portfolios:
                            if portfolio.trading_state == "RUNNING":
                                portfolio_running = True
                            positions = self.positions_repo.list_all(
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
                        print(f"⚠️  Position {position_id} not found in any portfolio")
                    elif not portfolio_running:
                        print(f"⚠️  Position {position_id} found but portfolio is not RUNNING")
                    elif not has_anchor:
                        print(f"⚠️  Position {position_id} found but anchor_price is not set")
                except Exception as e:
                    print(f"⚠️  Error checking position status: {e}")

                return None  # Position not found or not active

            # Start new trace for this cycle
            trace_id = str(uuid.uuid4())

            state = self.position_repo.load_position_state(position_id)
            quote = self.market_data.get_latest_quote(state.ticker)
            ticker = state.ticker  # Store for use in unified path

            # --- Unified Evaluation Path ---
            # If evaluate_position_uc is available, use it for consistent logic and timeline logging
            unified_path_handled = False  # Track if unified path successfully handled the cycle
            if self.evaluate_position_uc:
                import logging

                logger = logging.getLogger(__name__)

                # Need tenant_id and portfolio_id - try to find them
                search_tenant_id = "default"
                search_portfolio_id = None

                # Search across all portfolios to find this position (inefficient but safe for now)
                # Ideally the orchestrator would be called with these IDs
                if self.portfolio_repo:
                    portfolios = self.portfolio_repo.list_all(tenant_id=search_tenant_id)
                    logger.debug(
                        f"Unified path: Searching {len(portfolios)} portfolios for position {position_id}"
                    )
                    for portfolio in portfolios:
                        # Try to get position in this portfolio
                        from app.di import container

                        pos = container.positions.get(
                            tenant_id=search_tenant_id,
                            portfolio_id=portfolio.id,
                            position_id=position_id,
                        )
                        if pos:
                            search_portfolio_id = portfolio.id
                            logger.info(
                                f"Unified path: Found position {position_id} in portfolio {search_portfolio_id}"
                            )
                            break
                else:
                    logger.warning(
                        f"Unified path: No portfolio_repo available for position {position_id}"
                    )

                if search_portfolio_id:
                    # Store portfolio/tenant IDs for use in order submission and config providers
                    self._last_evaluation_portfolio_id = search_portfolio_id
                    self._last_evaluation_tenant_id = search_tenant_id
                    # Store for use in old path too
                    stored_tenant_id = search_tenant_id
                    stored_portfolio_id = search_portfolio_id

                    # Run full evaluation through use case (handles timeline logging)
                    evaluation_result = self.evaluate_position_uc.evaluate(
                        tenant_id=search_tenant_id,
                        portfolio_id=search_portfolio_id,
                        position_id=position_id,
                        current_price=quote.price,
                    )

                    # If unified path detected a trigger and has an order proposal, submit it directly
                    trigger_detected = evaluation_result.get("trigger_detected", False)
                    order_proposal = evaluation_result.get("order_proposal")

                    logger.info(
                        f"Unified path: Evaluation result for position {position_id}: "
                        f"trigger_detected={trigger_detected}, "
                        f"has_order_proposal={order_proposal is not None}"
                    )

                    if trigger_detected and order_proposal:
                        validation = order_proposal.get("validation", {})
                        is_valid = validation.get("valid", False)
                        rejections = validation.get("rejections", [])

                        logger.info(
                            f"Unified path: Order proposal for position {position_id}: "
                            f"side={order_proposal.get('side')}, "
                            f"trimmed_qty={order_proposal.get('trimmed_qty')}, "
                            f"validation_valid={is_valid}, "
                            f"rejections={rejections}"
                        )

                        # Only submit if validation passed
                        if is_valid:
                            try:
                                import logging

                                logger = logging.getLogger(__name__)
                                logger.info(
                                    f"Unified path: Submitting order for position {position_id}: "
                                    f"side={order_proposal.get('side')}, "
                                    f"qty={order_proposal.get('trimmed_qty')}"
                                )

                                # Convert order_proposal to TradeIntent for order service
                                from domain.value_objects.trade_intent import TradeIntent
                                from decimal import Decimal

                                # Safely extract side - handle both "BUY"/"SELL" and "buy"/"sell"
                                side_str = order_proposal.get("side", "").upper()
                                if side_str not in ["BUY", "SELL"]:
                                    raise ValueError(
                                        f"Invalid order side: {order_proposal.get('side')}"
                                    )

                                trade_intent = TradeIntent(
                                    side=side_str.lower(),  # "BUY" -> "buy"
                                    qty=Decimal(str(order_proposal.get("trimmed_qty", 0))),
                                    reason=order_proposal.get("reasoning")
                                    or "Trigger condition met",
                                )

                                # Submit order using order service
                                order_id = self.order_service.submit_live_order(
                                    position_id=position_id,
                                    portfolio_id=search_portfolio_id,
                                    tenant_id=search_tenant_id,
                                    trade_intent=trade_intent,
                                    quote=quote,
                                )

                                logger.info(
                                    f"Unified path: Order submitted successfully: order_id={order_id}"
                                )

                                # Log order creation event (use existing trace_id from line 121)
                                order_event = self.event_logger.log(
                                    EventType.ORDER_CREATED,
                                    asset_id=ticker,
                                    trace_id=trace_id,  # Use existing trace_id
                                    parent_event_id=None,
                                    source=source,
                                    payload={
                                        "position_id": position_id,
                                        "order_id": order_id,
                                        "trade_intent": {
                                            "side": trade_intent.side,
                                            "qty": str(trade_intent.qty),
                                            "reason": trade_intent.reason,
                                        },
                                        "quote": {
                                            "ticker": quote.ticker,
                                            "price": str(quote.price),
                                            "timestamp": quote.timestamp.isoformat(),
                                        },
                                    },
                                )

                                # Execute the order immediately (auto-fill in live trading)
                                try:
                                    from application.use_cases.execute_order_uc import (
                                        ExecuteOrderUC,
                                    )
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

                                    # Fill order at current market price
                                    fill_request = FillOrderRequest(
                                        qty=float(trade_intent.qty),
                                        price=float(quote.price),
                                        commission=order_proposal.get("commission", 0.0),
                                    )

                                    fill_response = execute_uc.execute(order_id, fill_request)

                                    logger.info(
                                        f"Unified path: Order executed successfully: "
                                        f"order_id={order_id}, "
                                        f"filled_qty={fill_response.filled_qty}, "
                                        f"status={fill_response.status}"
                                    )

                                    # Log execution event
                                    self.event_logger.log(
                                        EventType.EXECUTION_RECORDED,
                                        asset_id=ticker,
                                        trace_id=trace_id,
                                        parent_event_id=order_event.event_id,
                                        source=source,
                                        payload={
                                            "position_id": position_id,
                                            "order_id": order_id,
                                            "trade_id": None,  # Will be set by execute_uc
                                            "filled_qty": fill_response.filled_qty,
                                            "price": str(quote.price),
                                            "status": fill_response.status,
                                        },
                                    )

                                except Exception as exec_error:
                                    logger.error(
                                        f"Unified path: Failed to execute order {order_id}: {exec_error}",
                                        exc_info=True,
                                    )
                                    # Order was submitted but execution failed - this is logged but we continue
                                    # The order can be executed manually later if needed

                                unified_path_handled = True  # Mark as handled
                                return trace_id  # Successfully submitted (and executed if possible) via unified path

                            except Exception as unified_error:
                                import logging

                                logger = logging.getLogger(__name__)
                                logger.error(
                                    f"Unified path: Failed to submit order for position {position_id}: {unified_error}",
                                    exc_info=True,
                                )
                                # Fall through to old path as backup
                        else:
                            logger.warning(
                                f"Unified path: Order validation failed for position {position_id}: "
                                f"rejections={rejections}"
                            )
                    else:
                        if not trigger_detected:
                            logger.debug(
                                f"Unified path: No trigger detected for position {position_id}"
                            )
                        if not order_proposal:
                            logger.debug(
                                f"Unified path: No order proposal for position {position_id}"
                            )

                    # Note: We still continue with the rest of the method for trace logging
                    # and potentially order submission until we fully unify the paths.
                else:
                    logger.warning(
                        f"Unified path: Could not find portfolio_id for position {position_id}, "
                        f"falling back to old path"
                    )

            # --- End Unified Evaluation Path ---

            # Skip old path if unified path already handled it
            if unified_path_handled:
                return trace_id

            # 1. Log price event (OLD PATH - only runs if unified path didn't handle it)
            price_event = self.event_logger.log(
                EventType.PRICE_EVENT,
                asset_id=state.ticker,
                trace_id=trace_id,
                source=source,
                payload={
                    "position_id": position_id,
                    "ticker": state.ticker,
                    "price": str(quote.price),
                    "timestamp": quote.timestamp.isoformat(),
                    "anchor_price": str(state.anchor_price) if state.anchor_price else None,
                },
            )

            # Get tenant_id and portfolio_id for config providers
            # Try to find them from the position
            from app.di import container

            search_tenant_id = "default"
            search_portfolio_id = None
            if self.portfolio_repo:
                portfolios = self.portfolio_repo.list_all(tenant_id=search_tenant_id)
                for portfolio in portfolios:
                    pos = container.positions.get(
                        tenant_id=search_tenant_id,
                        portfolio_id=portfolio.id,
                        position_id=position_id,
                    )
                    if pos:
                        search_portfolio_id = portfolio.id
                        break

            # Use config providers with full parameters, or fallback to extracting from position
            if search_portfolio_id and hasattr(self.trigger_config_provider, "__call__"):
                try:
                    trigger_config: TriggerConfig = self.trigger_config_provider(
                        search_tenant_id, search_portfolio_id, position_id
                    )
                except TypeError:
                    # Fallback: provider might only take position_id
                    trigger_config: TriggerConfig = self.trigger_config_provider(position_id)
            else:
                # Fallback: extract from position
                from infrastructure.adapters.converters import order_policy_to_trigger_config

                trigger_config = (
                    order_policy_to_trigger_config(state.order_policy)
                    if hasattr(state, "order_policy") and state.order_policy
                    else TriggerConfig(
                        up_threshold_pct=Decimal("0.03"), down_threshold_pct=Decimal("0.03")
                    )
                )

            if search_portfolio_id and hasattr(self.guardrail_config_provider, "__call__"):
                try:
                    guardrail_config: GuardrailConfig = self.guardrail_config_provider(
                        search_tenant_id, search_portfolio_id, position_id
                    )
                except TypeError:
                    # Fallback: provider might only take position_id
                    guardrail_config: GuardrailConfig = self.guardrail_config_provider(position_id)
            else:
                # Fallback: extract from position
                from infrastructure.adapters.converters import guardrail_policy_to_guardrail_config

                guardrail_config = (
                    guardrail_policy_to_guardrail_config(state.guardrails)
                    if hasattr(state, "guardrails") and state.guardrails
                    else GuardrailConfig(
                        min_stock_pct=Decimal("0.0"),
                        max_stock_pct=Decimal("1.0"),
                        max_trade_pct_of_position=Decimal("0.5"),
                    )
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
                source=source,
                payload={
                    "position_id": position_id,
                    "ticker": state.ticker,
                    "trigger_decision": {
                        "fired": trigger_decision.fired,
                        "direction": trigger_decision.direction,
                        "reason": trigger_decision.reason,
                    },
                    "anchor_price": str(state.anchor_price) if state.anchor_price else None,
                    "current_price": str(quote.price),
                    "threshold_pct": str(trigger_config.up_threshold_pct),
                },
            )

            if not trigger_decision.fired:
                return trace_id  # Cycle completed, no trigger fired

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
                source=source,
                payload={
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
                return trace_id  # Cycle completed, guardrail blocked

            # Check market hours policy before submitting order
            # Get portfolio_id and tenant_id from position_repo (it has access to portfolio info)
            portfolio_id = None
            tenant_id = None
            allow_after_hours = True  # Default to allow if we can't determine

            # Try to get portfolio info from position_repo if it's the adapter
            if hasattr(self.position_repo, "positions_repo") and hasattr(
                self.position_repo, "portfolio_repo"
            ):
                # This is PositionRepoAdapter - we can search for the position
                if self.portfolio_repo:
                    # Search for position to get portfolio_id
                    # Try multiple tenant IDs in case it's not "default"
                    tenant_ids_to_try = ["default"]
                    # Also try to get from unified evaluation path if it was called
                    if hasattr(self, "_last_evaluation_tenant_id") and hasattr(
                        self, "_last_evaluation_portfolio_id"
                    ):
                        # If we already found it in unified path, use those values directly
                        portfolio_id = self._last_evaluation_portfolio_id
                        tenant_id = self._last_evaluation_tenant_id
                        # Get portfolio to check trading hours policy
                        portfolio = self.portfolio_repo.get(
                            tenant_id=tenant_id, portfolio_id=portfolio_id
                        )
                        if portfolio:
                            if portfolio.trading_hours_policy == "OPEN_ONLY":
                                allow_after_hours = False
                            elif portfolio.trading_hours_policy == "OPEN_PLUS_AFTER_HOURS":
                                allow_after_hours = True
                        # Skip the search loop since we already have the IDs
                        tenant_ids_to_try = []
                    else:
                        tenant_ids_to_try.insert(
                            0, getattr(self, "_last_evaluation_tenant_id", "default")
                        )

                    for search_tenant_id in tenant_ids_to_try:
                        portfolios = self.portfolio_repo.list_all(tenant_id=search_tenant_id)
                        for portfolio in portfolios:
                            pos = self.position_repo.positions_repo.get(
                                tenant_id=portfolio.tenant_id,
                                portfolio_id=portfolio.id,
                                position_id=position_id,
                            )
                            if pos:
                                portfolio_id = portfolio.id
                                tenant_id = portfolio.tenant_id
                                # Check portfolio trading_hours_policy
                                if portfolio.trading_hours_policy == "OPEN_ONLY":
                                    allow_after_hours = False
                                elif portfolio.trading_hours_policy == "OPEN_PLUS_AFTER_HOURS":
                                    allow_after_hours = True
                                break
                        if portfolio_id:
                            break

            # If we still don't have portfolio_id/tenant_id, we can't submit the order
            if not portfolio_id or not tenant_id:
                import logging

                logger = logging.getLogger(__name__)
                logger.error(
                    f"Cannot submit order for position {position_id}: "
                    f"Could not find portfolio_id and tenant_id. "
                    f"portfolio_id={portfolio_id}, tenant_id={tenant_id}"
                )
                # Log this as a guardrail block
                self.event_logger.log(
                    EventType.GUARDRAIL_EVALUATED,
                    asset_id=state.ticker,
                    trace_id=trace_id,
                    parent_event_id=guardrail_event.event_id,
                    source=source,
                    payload={
                        "position_id": position_id,
                        "decision": {
                            "allowed": False,
                            "reason": f"Cannot submit order: portfolio_id ({portfolio_id}) or tenant_id ({tenant_id}) not found",
                        },
                    },
                )
                return trace_id  # Cannot submit without portfolio/tenant info

            # Check if we're in market hours and if after-hours is allowed
            if self.market_data_repo:
                # Get PriceData to check is_market_hours
                price_data = self.market_data_repo.get_reference_price(state.ticker)
                if price_data and not price_data.is_market_hours:
                    if not allow_after_hours:
                        # Log that trade was blocked due to market hours policy
                        self.event_logger.log(
                            EventType.GUARDRAIL_EVALUATED,
                            asset_id=state.ticker,
                            trace_id=trace_id,
                            parent_event_id=guardrail_event.event_id,
                            source=source,
                            payload={
                                "position_id": position_id,
                                "decision": {
                                    "allowed": False,
                                    "reason": "Market is closed - after-hours trading disabled (portfolio policy: OPEN_ONLY)",
                                },
                            },
                        )
                        return trace_id  # Blocked by market hours policy

            # Submit live order
            import logging

            logger = logging.getLogger(__name__)
            logger.info(
                f"Submitting order for position {position_id}: "
                f"side={guardrail_decision.trade_intent.side}, "
                f"qty={guardrail_decision.trade_intent.qty}, "
                f"portfolio_id={portfolio_id or 'default'}, "
                f"tenant_id={tenant_id or 'default'}"
            )

            try:
                order_id = self.order_service.submit_live_order(
                    position_id=position_id,
                    portfolio_id=portfolio_id or "default",  # Fallback if not found
                    tenant_id=tenant_id or "default",  # Fallback if not found
                    trade_intent=guardrail_decision.trade_intent,
                    quote=quote,
                )
                logger.info(f"Order submitted successfully: order_id={order_id}")
            except Exception as order_error:
                logger.error(
                    f"Failed to submit order for position {position_id}: {order_error}",
                    exc_info=True,
                )
                # Re-raise so it gets caught by outer exception handler
                raise

            # 4. Log order creation
            order_event = self.event_logger.log(
                EventType.ORDER_CREATED,
                asset_id=state.ticker,
                trace_id=trace_id,
                parent_event_id=guardrail_event.event_id,
                source=source,
                payload={
                    "position_id": position_id,
                    "order_id": order_id,
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
                    "commission_estimate": None,  # TODO: Calculate from config
                },
            )

            return trace_id

        except Exception as e:
            # Log error but don't fail the entire cycle
            import logging

            logger = logging.getLogger(__name__)
            logger.error(
                f"Error in trading cycle for position {position_id}: {e}",
                exc_info=True,
                extra={
                    "position_id": position_id,
                    "source": source,
                    "trace_id": trace_id if "trace_id" in locals() else None,
                },
            )
            # Also log to event logger if available
            try:
                self.event_logger.log(
                    EventType.TRIGGER_EVALUATED,  # Using existing event type for errors
                    asset_id=state.ticker if "state" in locals() else "UNKNOWN",
                    trace_id=trace_id if "trace_id" in locals() else None,
                    source=source,
                    payload={
                        "position_id": position_id,
                        "error": str(e),
                        "error_type": type(e).__name__,
                    },
                )
            except Exception:
                pass  # Don't fail if event logging fails
            return None
