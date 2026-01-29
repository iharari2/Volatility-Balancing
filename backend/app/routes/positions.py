# =========================
# backend/app/routes/positions.py
# =========================
# backend/app/routes/positions.py  (only the relevant bits)

from typing import Optional
from typing import Any, Dict, List
import logging
import os
import time
from fastapi import APIRouter, HTTPException, Query, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from app.di import container
from datetime import datetime, timezone
from uuid import uuid4

router = APIRouter(prefix="/v1")
logger = logging.getLogger(__name__)


def _timing_enabled() -> bool:
    return os.getenv("VB_TIMING", "").lower() in {"1", "true", "yes", "on"}


# REMOVED: Legacy helper functions - All endpoints now require tenant_id and portfolio_id


def _find_position_legacy(position_id: str):
    """Legacy helper to find a position by ID across all portfolios.

    This is used by deprecated endpoints that don't have tenant_id/portfolio_id.
    Returns (position, tenant_id, portfolio_id) or (None, None, None) if not found.
    """
    # Query positions table directly by ID for better performance and reliability
    # This avoids session/transaction issues when iterating through portfolios
    timing_enabled = _timing_enabled()
    start_time = time.perf_counter() if timing_enabled else None
    try:
        from infrastructure.persistence.sql.models import PositionModel
        from infrastructure.persistence.sql.positions_repo_sql import SQLPositionsRepo
        from sqlalchemy import select, text

        # Check if we're using SQL repo and can access session factory
        if isinstance(container.positions, SQLPositionsRepo) and hasattr(
            container.positions, "_sf"
        ):
            session_factory = container.positions._sf
            with session_factory() as s:
                try:
                    # Try with status column first
                    stmt = select(PositionModel).where(PositionModel.id == position_id)
                    row = s.execute(stmt).scalar_one_or_none()
                    if row:
                        pos = container.positions.get(
                            tenant_id=row.tenant_id,
                            portfolio_id=row.portfolio_id,
                            position_id=position_id,
                        )
                        if pos:
                            if timing_enabled and start_time is not None:
                                logger.info(
                                    "tick_timing step=_find_position_legacy_sql_hit elapsed=%.4fs",
                                    time.perf_counter() - start_time,
                                )
                            return pos, row.tenant_id, row.portfolio_id
                except Exception:
                    # If status column doesn't exist, use raw SQL
                    try:
                        raw_sql = text(
                            """
                            SELECT tenant_id, portfolio_id FROM positions
                            WHERE id = :position_id
                            LIMIT 1
                            """
                        )
                        result = s.execute(raw_sql, {"position_id": position_id})
                        row = result.fetchone()
                        if row:
                            tenant_id, portfolio_id = row[0], row[1]
                            pos = container.positions.get(
                                tenant_id=tenant_id,
                                portfolio_id=portfolio_id,
                                position_id=position_id,
                            )
                            if pos:
                                if timing_enabled and start_time is not None:
                                    logger.info(
                                        "tick_timing step=_find_position_legacy_raw_hit elapsed=%.4fs",
                                        time.perf_counter() - start_time,
                                    )
                                return pos, tenant_id, portfolio_id
                    except Exception:
                        pass
    except (ImportError, AttributeError):
        # Not using SQL repo or can't access it, fall through to portfolio iteration
        pass

    # Fallback: iterate through portfolios (original method)
    # Try default tenant first
    tenant_id = "default"
    portfolios = container.portfolio_repo.list_all(tenant_id=tenant_id)

    for portfolio in portfolios:
        pos = container.positions.get(
            tenant_id=tenant_id, portfolio_id=portfolio.id, position_id=position_id
        )
        if pos:
            if timing_enabled and start_time is not None:
                logger.info(
                    "tick_timing step=_find_position_legacy_fallback_hit elapsed=%.4fs",
                    time.perf_counter() - start_time,
                )
            return pos, tenant_id, portfolio.id

    # If not found in default tenant, try to find it by querying all positions
    # This handles cases where positions might be in other tenants
    try:
        from infrastructure.persistence.sql.models import PositionModel
        from infrastructure.persistence.sql.positions_repo_sql import SQLPositionsRepo
        from sqlalchemy import select, text

        if isinstance(container.positions, SQLPositionsRepo) and hasattr(
            container.positions, "_sf"
        ):
            session_factory = container.positions._sf
            with session_factory() as s:
                try:
                    # Query without tenant restriction
                    raw_sql = text(
                        """
                        SELECT tenant_id, portfolio_id FROM positions
                        WHERE id = :position_id
                        LIMIT 1
                        """
                    )
                    result = s.execute(raw_sql, {"position_id": position_id})
                    row = result.fetchone()
                    if row:
                        tenant_id, portfolio_id = row[0], row[1]
                        pos = container.positions.get(
                            tenant_id=tenant_id, portfolio_id=portfolio_id, position_id=position_id
                        )
                        if pos:
                            if timing_enabled and start_time is not None:
                                logger.info(
                                    "tick_timing step=_find_position_legacy_scan_hit elapsed=%.4fs",
                                    time.perf_counter() - start_time,
                                )
                            return pos, tenant_id, portfolio_id
                except Exception:
                    pass

    except (ImportError, AttributeError):
        pass

    if timing_enabled and start_time is not None:
        logger.info(
            "tick_timing step=_find_position_legacy_miss elapsed=%.4fs",
            time.perf_counter() - start_time,
        )

    return None, None, None


class OrderPolicyIn(BaseModel):
    min_qty: float = 0.0
    min_notional: float = 0.0
    lot_size: float = 0.0
    qty_step: float = 0.0
    action_below_min: str = "hold"  # "hold" | "reject" | "clip"
    # Volatility trading parameters
    # ... existing code ...


# ... existing code continues ...


def _tick_position_sync(position_id: str) -> Dict[str, Any]:
    """
    Execute one deterministic trading evaluation cycle for a position.

    This endpoint:
    - Fetches latest live quote
    - Evaluates trigger and guardrails using domain services
    - Decides HOLD/SKIP/BUY/SELL
    - If BUY/SELL: creates Order + immediately creates Trade using effective price policy MID (default)
    - Updates Position state through ExecuteOrderUC only
    - Writes exactly one PositionEvent row per tick (even if HOLD)
    - Returns CycleResult JSON including position snapshot, baseline deltas, allocation% vs guardrails, last event summary
    """
    timing_enabled = _timing_enabled()
    total_start = time.perf_counter() if timing_enabled else None
    last_step = total_start
    timings: List[tuple[str, float]] = []
    try:
        if timing_enabled:
            logger.info("tick_timing step=start position_id=%s", position_id)
        # Find position across portfolios
        position, tenant_id, portfolio_id = _find_position_legacy(position_id)
        if not position:
            raise HTTPException(status_code=404, detail=f"Position {position_id} not found")
        if timing_enabled and last_step is not None:
            now = time.perf_counter()
            timings.append(("find_position", now - last_step))
            last_step = now

        # Get latest live quote
        price_data = container.market_data.get_reference_price(position.asset_symbol)
        if not price_data:
            raise HTTPException(
                status_code=404, detail=f"No market data available for {position.asset_symbol}"
            )
        if timing_enabled and last_step is not None:
            now = time.perf_counter()
            timings.append(("get_price", now - last_step))
            last_step = now

        # Evaluate position using EvaluatePositionUC
        eval_uc = container.evaluate_position_uc
        evaluation_result = eval_uc.evaluate(
            tenant_id=tenant_id,
            portfolio_id=portfolio_id,
            position_id=position_id,
            current_price=price_data.price,
            write_timeline=False,
        )
        if timing_enabled and last_step is not None:
            now = time.perf_counter()
            timings.append(("evaluate", now - last_step))
            last_step = now

        trigger_detected = evaluation_result.get("trigger_detected", False)
        trigger_type = evaluation_result.get("trigger_type")
        order_proposal = evaluation_result.get("order_proposal")

        action = "HOLD"
        if trigger_detected and trigger_type in ("BUY", "SELL"):
            action = trigger_type

        action_reason = evaluation_result.get("reasoning", "No trigger detected")
        if order_proposal and "validation" in order_proposal:
            validation_result = order_proposal["validation"]
            if not validation_result.get("valid"):
                rejections = validation_result.get("rejections", [])
                action_reason = f"Trade blocked: {', '.join(rejections)}"
                action = "SKIP"
        elif trigger_detected and action in ("BUY", "SELL") and not order_proposal:
            action = "SKIP"

        # If BUY/SELL, create and execute order
        order_id = None
        trade_id = None
        mid_price = price_data.price
        if action in ("BUY", "SELL") and order_proposal:
            validation_result = order_proposal.get("validation", {})
            if not validation_result.get("valid"):
                order_proposal = None
        if action in ("BUY", "SELL") and order_proposal:
            # Calculate MID price (default policy)
            mid_price = price_data.price  # Fallback to effective price
            if price_data.bid is not None and price_data.ask is not None:
                mid_price = (price_data.bid + price_data.ask) / 2.0
            elif price_data.bid is not None:
                mid_price = price_data.bid
            elif price_data.ask is not None:
                mid_price = price_data.ask

            # Submit order
            from application.use_cases.submit_order_uc import CreateOrderRequest
            from application.use_cases.execute_order_uc import FillOrderRequest

            from application.use_cases.submit_order_uc import SubmitOrderUC
            from application.use_cases.execute_order_uc import ExecuteOrderUC

            submit_uc = SubmitOrderUC(
                positions=container.positions,
                orders=container.orders,
                events=container.events,
                idempotency=container.idempotency,
                config_repo=container.config,
                clock=container.clock,
                guardrail_config_provider=container.guardrail_config_provider,
            )
            execute_uc = ExecuteOrderUC(
                positions=container.positions,
                orders=container.orders,
                trades=container.trades,
                events=container.events,
                clock=container.clock,
                guardrail_config_provider=container.guardrail_config_provider,
                order_policy_config_provider=container.order_policy_config_provider,
            )

            order_request = CreateOrderRequest(
                side=action,
                qty=abs(order_proposal.get("trimmed_qty", 0.0)),
                price=mid_price,
            )

            idempotency_key = (
                f"tick_{position_id}_{int(datetime.now(timezone.utc).timestamp() * 1000)}"
            )
            submit_response = submit_uc.execute(
                tenant_id=tenant_id,
                portfolio_id=portfolio_id,
                position_id=position_id,
                request=order_request,
                idempotency_key=idempotency_key,
            )
            if timing_enabled and last_step is not None:
                now = time.perf_counter()
                timings.append(("submit_order", now - last_step))
                last_step = now

            if submit_response.accepted:
                order_id = submit_response.order_id

                # Immediately execute order
                fill_request = FillOrderRequest(
                    qty=abs(order_proposal.get("trimmed_qty", 0.0)),
                    price=mid_price,
                    commission=order_proposal.get("commission", 0.0),
                )

                fill_response = execute_uc.execute(order_id, fill_request)
                if fill_response.status == "filled":
                    trade_id = fill_response.trade_id
            if timing_enabled and last_step is not None:
                now = time.perf_counter()
                timings.append(("execute_order", now - last_step))
                last_step = now

        # Reload position to get updated state
        updated_position = container.positions.get(
            tenant_id=tenant_id,
            portfolio_id=portfolio_id,
            position_id=position_id,
        )
        if timing_enabled and last_step is not None:
            now = time.perf_counter()
            timings.append(("reload_position", now - last_step))
            last_step = now

        # Resolve allow_after_hours and trading_hours_policy for timeline
        portfolio = None
        if hasattr(container, "portfolio_repo"):
            portfolio = container.portfolio_repo.get(
                tenant_id=tenant_id, portfolio_id=portfolio_id
            )
        if timing_enabled and last_step is not None:
            now = time.perf_counter()
            timings.append(("load_portfolio", now - last_step))
            last_step = now

        allow_after_hours = position.order_policy.allow_after_hours if position.order_policy else False
        if hasattr(container, "order_policy_config_provider"):
            order_policy_config = container.order_policy_config_provider(
                tenant_id, portfolio_id, position_id
            )
            if order_policy_config is not None:
                allow_after_hours = order_policy_config.allow_after_hours

        if portfolio is not None:
            if portfolio.trading_hours_policy == "OPEN_ONLY":
                allow_after_hours = False
            elif portfolio.trading_hours_policy == "OPEN_PLUS_AFTER_HOURS":
                allow_after_hours = True

        validation = container.market_data.validate_price(price_data, allow_after_hours)
        trigger_result = {
            "triggered": trigger_detected,
            "side": trigger_type,
            "reasoning": evaluation_result.get("reasoning", "No trigger detected"),
        }
        anchor_reset_info = evaluation_result.get("anchor_reset")
        execution_info = None
        if trade_id and order_proposal:
            execution_info = {
                "price": mid_price,
                "qty": abs(order_proposal.get("trimmed_qty", 0.0)),
                "commission": order_proposal.get("commission", 0.0),
                "timestamp": datetime.now(timezone.utc),
                "status": "filled",
            }

        # Write exactly one timeline row for this tick
        eval_uc._write_timeline_row(
            tenant_id=tenant_id,
            portfolio_id=portfolio_id,
            position=position,
            price_data=price_data,
            validation=validation,
            allow_after_hours=allow_after_hours,
            trading_hours_policy=portfolio.trading_hours_policy if portfolio else None,
            anchor_reset_info=anchor_reset_info,
            trigger_result=trigger_result,
            order_proposal=order_proposal,
            action=action,
            source="api/manual",
            order_id=order_id,
            trade_id=trade_id,
            execution_info=execution_info,
            position_qty_after=updated_position.qty if updated_position else None,
            position_cash_after=updated_position.cash if updated_position else None,
        )
        if timing_enabled and last_step is not None:
            now = time.perf_counter()
            timings.append(("write_timeline", now - last_step))
            last_step = now

        # Get baseline for delta calculations
        baseline = None
        if hasattr(container, "position_baseline"):
            baseline = container.position_baseline.get_latest(position_id)
        if timing_enabled and last_step is not None:
            now = time.perf_counter()
            timings.append(("load_baseline", now - last_step))
            last_step = now

        # Calculate position snapshot
        current_price = price_data.price
        stock_value = updated_position.qty * current_price
        total_value = (updated_position.cash or 0.0) + stock_value
        allocation_pct = (stock_value / total_value * 100) if total_value > 0 else 0.0

        # Calculate baseline deltas
        position_vs_baseline = {"pct": None, "abs": None}
        stock_vs_baseline = {"pct": None, "abs": None}

        if baseline:
            baseline_total_value = baseline.get("baseline_total_value", 0.0)
            baseline_stock_value = baseline.get("baseline_stock_value", 0.0)

            if baseline_total_value > 0:
                position_vs_baseline["abs"] = total_value - baseline_total_value
                position_vs_baseline["pct"] = ((total_value / baseline_total_value) - 1) * 100

            if baseline_stock_value > 0:
                stock_vs_baseline["abs"] = stock_value - baseline_stock_value
                stock_vs_baseline["pct"] = ((stock_value / baseline_stock_value) - 1) * 100

        # Get guardrail config for allocation comparison
        guardrail_config = None
        if hasattr(container, "guardrail_config_provider"):
            guardrail_config = container.guardrail_config_provider(
                tenant_id, portfolio_id, position_id
            )
        if timing_enabled and last_step is not None:
            now = time.perf_counter()
            timings.append(("load_guardrails", now - last_step))
            last_step = now

        allocation_vs_guardrails = {
            "current_allocation_pct": allocation_pct,
            "min_stock_pct": float(guardrail_config.min_stock_pct) if guardrail_config else None,
            "max_stock_pct": float(guardrail_config.max_stock_pct) if guardrail_config else None,
            "within_guardrails": True,
        }

        if guardrail_config:
            min_pct = float(guardrail_config.min_stock_pct)
            max_pct = float(guardrail_config.max_stock_pct)
            allocation_vs_guardrails["within_guardrails"] = min_pct <= allocation_pct <= max_pct

        # Get last event (should be the one just written by EvaluatePositionUC)
        last_event = None
        if hasattr(container, "position_event"):
            events = container.position_event.list_by_position(
                position_id=position_id,
                limit=1,
            )
            if events:
                last_event = events[0]
        if timing_enabled and last_step is not None:
            now = time.perf_counter()
            timings.append(("load_last_event", now - last_step))
            last_step = now

        if timing_enabled and total_start is not None:
            total_elapsed = time.perf_counter() - total_start
            timing_summary = " ".join(f"{label}={duration:.4f}s" for label, duration in timings)
            logger.info("tick_timing total=%.4fs %s", total_elapsed, timing_summary)

        # Build response
        trigger_direction = "NONE"
        if action == "BUY":
            trigger_direction = "DOWN"
        elif action == "SELL":
            trigger_direction = "UP"

        response_payload = {
            "position_snapshot": {
                "position_id": position_id,
                "symbol": updated_position.asset_symbol,
                "qty": updated_position.qty,
                "cash": updated_position.cash or 0.0,
                "stock_value": stock_value,
                "total_value": total_value,
                "allocation_pct": allocation_pct,
                "anchor_price": updated_position.anchor_price,
                "current_price": current_price,
            },
            "baseline_deltas": {
                "position_vs_baseline": position_vs_baseline,
                "stock_vs_baseline": stock_vs_baseline,
            },
            "allocation_vs_guardrails": allocation_vs_guardrails,
            "last_event": (
                {
                    "event_id": last_event.get("event_id") if last_event else None,
                    "timestamp": last_event.get("timestamp") if last_event else None,
                    "event_type": last_event.get("event_type") if last_event else None,
                    "action": last_event.get("action") if last_event else None,
                    "action_reason": last_event.get("action_reason") if last_event else None,
                }
                if last_event
                else None
            ),
            "cycle_result": {
                "action": action,
                "action_reason": action_reason,
                "trigger_direction": trigger_direction,
                "order_id": order_id,
                "trade_id": trade_id,
                "evaluation_timestamp": datetime.now(timezone.utc).isoformat(),
            },
        }
        if timing_enabled:
            logger.info("tick_timing step=response_ready position_id=%s", position_id)
            from fastapi.encoders import jsonable_encoder

            encode_start = time.perf_counter()
            response_payload = jsonable_encoder(response_payload)
            logger.info(
                "tick_timing step=response_encoded elapsed=%.4fs position_id=%s",
                time.perf_counter() - encode_start,
                position_id,
            )
        if timing_enabled:
            return JSONResponse(content=response_payload)
        return response_payload

    except HTTPException:
        raise
    except Exception as e:
        import traceback

        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error executing tick: {str(e)}")
    finally:
        if timing_enabled:
            logger.info("tick_timing step=exit position_id=%s", position_id)


@router.post("/positions/{position_id}/tick")
async def tick_position(position_id: str) -> Dict[str, Any]:
    return _tick_position_sync(position_id)


class SimulationRequest(BaseModel):
    """Request model for running a simulation for a position."""

    start_date: str
    end_date: str
    initial_cash: Optional[float] = None
    include_after_hours: bool = False
    intraday_interval_minutes: int = 30
    position_config: Optional[Dict[str, Any]] = None


@router.post("/positions/{position_id}/simulation/run")
def run_simulation_for_position(
    position_id: str,
    request: SimulationRequest,
) -> Dict[str, Any]:
    """
    Execute a simulation for a position.

    Uses the position's ticker and configuration to run a historical simulation.
    """
    try:
        # Find position across portfolios
        position, tenant_id, portfolio_id = _find_position_legacy(position_id)
        if not position:
            raise HTTPException(status_code=404, detail=f"Position {position_id} not found")

        # Parse dates
        start_date = datetime.fromisoformat(request.start_date.replace("Z", "+00:00"))
        end_date = datetime.fromisoformat(request.end_date.replace("Z", "+00:00"))

        # Get position config if not provided
        position_config = request.position_config
        if not position_config:
            # Extract config from position's order_policy and guardrails
            position_config = {
                "trigger_threshold_pct": (
                    position.order_policy.trigger_threshold_pct if position.order_policy else 0.03
                ),
                "rebalance_ratio": (
                    position.order_policy.rebalance_ratio if position.order_policy else 1.6667
                ),
                "commission_rate": (
                    position.order_policy.commission_rate if position.order_policy else 0.0001
                ),
                "min_notional": (
                    position.order_policy.min_notional if position.order_policy else 100.0
                ),
                "allow_after_hours": request.include_after_hours,
                "guardrails": {
                    "min_stock_alloc_pct": (
                        position.guardrails.min_stock_alloc_pct if position.guardrails else 0.25
                    ),
                    "max_stock_alloc_pct": (
                        position.guardrails.max_stock_alloc_pct if position.guardrails else 0.75
                    ),
                },
            }

        # Determine initial cash - use position's current cash if not specified
        initial_cash = request.initial_cash
        if initial_cash is None:
            # Use position's current total value as initial cash for simulation
            current_price = container.market_data.get_reference_price(position.asset_symbol)
            if current_price:
                stock_value = position.qty * current_price.price
                initial_cash = (position.cash or 0.0) + stock_value
            else:
                initial_cash = position.cash or 10000.0

        # Run simulation using the unified simulation use case
        simulation_uc = container.simulation_uc
        simulation_id = str(uuid4())

        result = simulation_uc.run_simulation(
            ticker=position.asset_symbol,
            start_date=start_date,
            end_date=end_date,
            initial_cash=initial_cash,
            position_config=position_config,
            include_after_hours=request.include_after_hours,
            intraday_interval_minutes=request.intraday_interval_minutes,
            simulation_id=simulation_id,
        )

        # Convert result to dict for JSON response
        return {
            "simulation_id": simulation_id,
            "position_id": position_id,
            "ticker": position.asset_symbol,
            "start_date": (
                result.start_date.isoformat()
                if hasattr(result.start_date, "isoformat")
                else str(result.start_date)
            ),
            "end_date": (
                result.end_date.isoformat()
                if hasattr(result.end_date, "isoformat")
                else str(result.end_date)
            ),
            "initial_cash": result.initial_cash,
            "algorithm_return_pct": result.algorithm_return_pct,
            "buy_hold_return_pct": result.buy_hold_return_pct,
            "excess_return": result.excess_return,
            "algorithm_trades": result.algorithm_trades,
            "algorithm_pnl": result.algorithm_pnl,
            "buy_hold_pnl": result.buy_hold_pnl,
            "sharpe_ratio": result.algorithm_sharpe_ratio,
            "max_drawdown": result.algorithm_max_drawdown,
            "volatility": result.algorithm_volatility,
            "total_trading_days": result.total_trading_days,
            # Include timeline/events data for GUI
            "time_series_data": result.time_series_data,
            "trade_log": result.trade_log,
            "trigger_analysis": result.trigger_analysis,
        }

    except HTTPException:
        raise
    except Exception as e:
        import traceback

        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error running simulation: {str(e)}")


class StandaloneSimulationRequest(BaseModel):
    """Request model for running a standalone simulation (no position required)."""

    ticker: str
    start_date: str
    end_date: str
    initial_cash: float = 10000.0
    include_after_hours: bool = False
    intraday_interval_minutes: int = 30
    position_config: Optional[Dict[str, Any]] = None


@router.post("/simulation/run")
def run_standalone_simulation(
    request: StandaloneSimulationRequest,
) -> Dict[str, Any]:
    """
    Execute a standalone simulation for any ticker (no position required).

    This endpoint allows running simulations directly without needing to create a position first.
    Perfect for testing and analysis.
    """
    try:
        # Parse dates
        start_date = datetime.fromisoformat(request.start_date.replace("Z", "+00:00"))
        end_date = datetime.fromisoformat(request.end_date.replace("Z", "+00:00"))

        # Default position config if not provided
        position_config = request.position_config
        if not position_config:
            position_config = {
                "trigger_threshold_pct": 0.03,
                "rebalance_ratio": 1.6667,
                "commission_rate": 0.0001,
                "min_notional": 100.0,
                "allow_after_hours": request.include_after_hours,
                "guardrails": {
                    "min_stock_alloc_pct": 0.25,
                    "max_stock_alloc_pct": 0.75,
                },
            }

        # Run simulation using the unified simulation use case
        simulation_uc = container.simulation_uc
        simulation_id = str(uuid4())

        result = simulation_uc.run_simulation(
            ticker=request.ticker.upper(),
            start_date=start_date,
            end_date=end_date,
            initial_cash=request.initial_cash,
            position_config=position_config,
            include_after_hours=request.include_after_hours,
            intraday_interval_minutes=request.intraday_interval_minutes,
            simulation_id=simulation_id,
        )

        # Convert result to dict for JSON response
        return {
            "simulation_id": simulation_id,
            "ticker": request.ticker.upper(),
            "start_date": (
                result.start_date.isoformat()
                if hasattr(result.start_date, "isoformat")
                else str(result.start_date)
            ),
            "end_date": (
                result.end_date.isoformat()
                if hasattr(result.end_date, "isoformat")
                else str(result.end_date)
            ),
            "initial_cash": result.initial_cash,
            "algorithm_return_pct": result.algorithm_return_pct,
            "buy_hold_return_pct": result.buy_hold_return_pct,
            "excess_return": result.excess_return,
            "algorithm_trades": result.algorithm_trades,
            "algorithm_pnl": result.algorithm_pnl,
            "buy_hold_pnl": result.buy_hold_pnl,
            "sharpe_ratio": result.algorithm_sharpe_ratio,
            "max_drawdown": result.algorithm_max_drawdown,
            "volatility": result.algorithm_volatility,
            "total_trading_days": result.total_trading_days,
            "algorithm": {
                "return_pct": result.algorithm_return_pct,
                "pnl": result.algorithm_pnl,
                "trades": result.algorithm_trades,
                "volatility": result.algorithm_volatility,
                "sharpe_ratio": result.algorithm_sharpe_ratio,
                "max_drawdown": result.algorithm_max_drawdown,
            },
            "buy_hold": {
                "return_pct": result.buy_hold_return_pct,
                "pnl": result.buy_hold_pnl,
                "volatility": result.buy_hold_volatility,
                "sharpe_ratio": result.buy_hold_sharpe_ratio,
                "max_drawdown": result.buy_hold_max_drawdown,
            },
            "comparison": {
                "excess_return": result.excess_return,
                "alpha": result.alpha,
                "beta": result.beta,
                "information_ratio": result.information_ratio,
            },
            # Include timeline/events data for GUI
            "time_series_data": result.time_series_data,
            "trade_log": result.trade_log,
            "trigger_analysis": result.trigger_analysis,
        }

    except HTTPException:
        raise
    except Exception as e:
        import traceback

        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error running simulation: {str(e)}")


@router.post("/positions/{position_id}/anchor")
def set_anchor_price_legacy(position_id: str, price: float = Query(...)) -> Dict[str, Any]:
    """Legacy endpoint to set anchor price for a position."""
    position, tenant_id, portfolio_id = _find_position_legacy(position_id)
    if not position:
        raise HTTPException(status_code=404, detail=f"Position {position_id} not found")

    # Update anchor price
    position.set_anchor_price(price)
    # Save position (save() only takes position object, not tenant_id/portfolio_id)
    container.positions.save(position)

    return {
        "position_id": position_id,
        "anchor_price": price,
        "message": "Anchor price set successfully",
    }


@router.post("/positions/{position_id}/evaluate")
def evaluate_position_legacy(position_id: str, current_price: float = Query(...)) -> Dict[str, Any]:
    """Legacy endpoint to evaluate a position with a manual price."""
    position, tenant_id, portfolio_id = _find_position_legacy(position_id)
    if not position:
        raise HTTPException(status_code=404, detail="position_not_found")

    # Evaluate position
    eval_uc = container.evaluate_position_uc
    evaluation_result = eval_uc.evaluate(
        tenant_id=tenant_id,
        portfolio_id=portfolio_id,
        position_id=position_id,
        current_price=current_price,
    )

    return evaluation_result


@router.post("/positions/{position_id}/evaluate/market")
def evaluate_position_with_market_data_legacy(position_id: str) -> Dict[str, Any]:
    """Legacy endpoint to evaluate a position using market data."""
    position, tenant_id, portfolio_id = _find_position_legacy(position_id)
    if not position:
        raise HTTPException(status_code=404, detail=f"Position {position_id} not found")

    # Get market data
    price_data = container.market_data.get_reference_price(position.asset_symbol)
    if not price_data:
        raise HTTPException(
            status_code=400, detail=f"No market data available for {position.asset_symbol}"
        )

    # Evaluate position
    eval_uc = container.evaluate_position_uc
    evaluation_result = eval_uc.evaluate(
        tenant_id=tenant_id,
        portfolio_id=portfolio_id,
        position_id=position_id,
        current_price=price_data.price,
    )

    return evaluation_result


@router.get("/positions/{position_id}/timeline")
async def list_position_timeline_legacy(
    position_id: str,
    limit: int = Query(200, description="Maximum number of timeline rows"),
    start_date: Optional[str] = Query(None, description="Filter events from this date (ISO format)"),
    end_date: Optional[str] = Query(None, description="Filter events until this date (ISO format)"),
    event_type: Optional[str] = Query(None, description="Filter by event/evaluation type (comma-separated for multiple)"),
    action: Optional[str] = Query(None, description="Filter by action (BUY, SELL, HOLD, SKIP - comma-separated for multiple)"),
) -> List[Dict[str, Any]]:
    """Legacy endpoint to list evaluation timeline rows for a position.

    Supports filtering by:
    - start_date: ISO format datetime string (e.g., 2024-01-01T00:00:00Z)
    - end_date: ISO format datetime string
    - event_type: Comma-separated list of event types (e.g., DAILY_CHECK,PRICE_UPDATE)
    - action: Comma-separated list of actions (e.g., BUY,SELL)
    """
    position, tenant_id, portfolio_id = _find_position_legacy(position_id)
    if not position:
        raise HTTPException(status_code=404, detail=f"Position {position_id} not found")

    if not hasattr(container, "evaluation_timeline"):
        raise HTTPException(status_code=501, detail="Timeline repository not available")

    # Parse date filters
    parsed_start_date = None
    parsed_end_date = None
    if start_date:
        try:
            parsed_start_date = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid start_date format: {start_date}")
    if end_date:
        try:
            parsed_end_date = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid end_date format: {end_date}")

    timeline = container.evaluation_timeline.list_by_position(
        tenant_id=tenant_id,
        portfolio_id=portfolio_id,
        position_id=position_id,
        mode="LIVE",
        start_date=parsed_start_date,
        end_date=parsed_end_date,
        limit=limit,
    )

    # Parse event_type and action filters
    event_types = [t.strip().upper() for t in event_type.split(",")] if event_type else []
    actions = [a.strip().upper() for a in action.split(",")] if action else []

    # Normalize and filter
    normalized = []
    for row in timeline:
        # Apply event_type filter
        if event_types:
            row_event_type = (row.get("evaluation_type") or row.get("event_type") or "").upper()
            if row_event_type not in event_types:
                continue

        # Apply action filter
        if actions:
            row_action = (row.get("action") or "").upper()
            if row_action not in actions:
                continue

        row_copy = dict(row)
        if "current_price" not in row_copy:
            row_copy["current_price"] = row_copy.get("effective_price")
        if "allocation_after" not in row_copy:
            row_copy["allocation_after"] = row_copy.get("position_stock_pct_after")
            if row_copy["allocation_after"] is None:
                row_copy["allocation_after"] = row_copy.get("post_trade_stock_pct")
        normalized.append(row_copy)

    return normalized


@router.get("/positions/{position_id}/events")
def list_position_events_legacy(
    position_id: str,
    limit: int = Query(100),
    start_date: Optional[str] = Query(None, description="Filter events from this date (ISO format)"),
    end_date: Optional[str] = Query(None, description="Filter events until this date (ISO format)"),
    event_type: Optional[str] = Query(None, description="Filter by event type (comma-separated for multiple)"),
    search: Optional[str] = Query(None, description="Search in event messages"),
) -> Dict[str, Any]:
    """Legacy endpoint to list events for a position.

    Supports filtering by:
    - start_date: ISO format datetime string (e.g., 2024-01-01T00:00:00Z)
    - end_date: ISO format datetime string
    - event_type: Comma-separated list of event types (e.g., order_filled,trigger_detected)
    - search: Text search in event messages
    """
    position, tenant_id, portfolio_id = _find_position_legacy(position_id)
    if not position:
        raise HTTPException(status_code=404, detail=f"Position {position_id} not found")

    # Get events
    if not hasattr(container, "position_event"):
        raise HTTPException(status_code=501, detail="Event repository not available")

    events = container.position_event.list_by_position(
        position_id=position_id,
        limit=limit,
    )

    # Parse date filters
    parsed_start_date = None
    parsed_end_date = None
    if start_date:
        try:
            parsed_start_date = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid start_date format: {start_date}")
    if end_date:
        try:
            parsed_end_date = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid end_date format: {end_date}")

    # Parse event_type filter
    event_types = [t.strip().lower() for t in event_type.split(",")] if event_type else []

    # Apply filters
    filtered_events = []
    for event in events:
        # Date filter
        if parsed_start_date or parsed_end_date:
            event_ts = event.get("timestamp") or event.get("ts")
            if event_ts:
                if isinstance(event_ts, str):
                    try:
                        event_dt = datetime.fromisoformat(event_ts.replace("Z", "+00:00"))
                    except ValueError:
                        event_dt = None
                else:
                    event_dt = event_ts
                if event_dt:
                    if parsed_start_date and event_dt < parsed_start_date:
                        continue
                    if parsed_end_date and event_dt > parsed_end_date:
                        continue

        # Event type filter
        if event_types:
            event_event_type = (event.get("event_type") or event.get("type") or "").lower()
            if event_event_type not in event_types:
                continue

        # Text search filter
        if search:
            message = (event.get("message") or "").lower()
            if search.lower() not in message:
                continue

        filtered_events.append(event)

    return {"position_id": position_id, "events": filtered_events}


@router.post("/positions/{position_id}/orders/auto-size")
def auto_size_order_legacy(
    position_id: str,
    current_price: float = Query(...),
    idempotency_key: Optional[str] = Header(default=None, alias="Idempotency-Key"),
) -> Dict[str, Any]:
    """Legacy endpoint to submit an auto-sized order for a position."""
    position, tenant_id, portfolio_id = _find_position_legacy(position_id)
    if not position:
        raise HTTPException(status_code=404, detail="position_not_found")

    # Evaluate position
    eval_uc = container.evaluate_position_uc
    try:
        evaluation_result = eval_uc.evaluate(
            tenant_id=tenant_id,
            portfolio_id=portfolio_id,
            position_id=position_id,
            current_price=current_price,
        )
    except KeyError as e:
        # EvaluatePositionUC raises KeyError("position_not_found") when position doesn't exist
        if str(e) == "position_not_found" or "position_not_found" in str(e):
            raise HTTPException(status_code=404, detail="position_not_found")
        raise

    order_submitted = False
    if evaluation_result.get("action") in ("BUY", "SELL") and evaluation_result.get(
        "order_proposal"
    ):
        # Submit order
        from application.use_cases.submit_order_uc import CreateOrderRequest, SubmitOrderUC

        submit_uc = SubmitOrderUC(
            positions=container.positions,
            orders=container.orders,
            events=container.events,
            idempotency=container.idempotency,
            config_repo=container.config,
            clock=container.clock,
            guardrail_config_provider=container.guardrail_config_provider,
        )
        order_proposal = evaluation_result["order_proposal"]

        order_request = CreateOrderRequest(
            side=evaluation_result["action"],
            qty=abs(order_proposal.get("trimmed_qty", 0.0)),
            price=current_price,
        )

        submit_response = submit_uc.execute(
            tenant_id=tenant_id,
            portfolio_id=portfolio_id,
            position_id=position_id,
            request=order_request,
            idempotency_key=idempotency_key or "",
        )

        order_submitted = submit_response.accepted

    return {
        "position_id": position_id,
        "current_price": current_price,
        "order_submitted": order_submitted,
        "evaluation": evaluation_result,
    }


@router.post("/clear-positions")
def clear_all_positions_legacy() -> Dict[str, Any]:
    """Legacy endpoint to clear all positions."""
    # Clear all positions by clearing portfolios
    tenant_id = "default"
    portfolios = container.portfolio_repo.list_all(tenant_id=tenant_id)

    count = 0
    for portfolio in portfolios:
        positions = container.positions.list_all(tenant_id=tenant_id, portfolio_id=portfolio.id)
        for position in positions:
            container.positions.delete(
                tenant_id=tenant_id, portfolio_id=portfolio.id, position_id=position.id
            )
            count += 1

    # Return count of remaining positions (should be 0 after clearing)
    remaining = 0
    for portfolio in portfolios:
        remaining += len(
            container.positions.list_all(tenant_id=tenant_id, portfolio_id=portfolio.id)
        )

    return {"message": "All positions cleared", "count": remaining}
