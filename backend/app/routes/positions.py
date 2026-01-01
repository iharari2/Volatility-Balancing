# =========================
# backend/app/routes/positions.py
# =========================
# backend/app/routes/positions.py  (only the relevant bits)

from typing import Optional
from typing import Any, Dict
from fastapi import APIRouter, HTTPException, Query, Header
from pydantic import BaseModel
from app.di import container
from datetime import datetime, timezone
from uuid import uuid4

router = APIRouter(prefix="/v1")


# REMOVED: Legacy helper functions - All endpoints now require tenant_id and portfolio_id


def _find_position_legacy(position_id: str):
    """Legacy helper to find a position by ID across all portfolios.

    This is used by deprecated endpoints that don't have tenant_id/portfolio_id.
    Returns (position, tenant_id, portfolio_id) or (None, None, None) if not found.
    """
    # Query positions table directly by ID for better performance and reliability
    # This avoids session/transaction issues when iterating through portfolios
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
                            return pos, tenant_id, portfolio_id
                except Exception:
                    pass
    except (ImportError, AttributeError):
        pass

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


@router.post("/positions/{position_id}/tick")
def tick_position(position_id: str) -> Dict[str, Any]:
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
    try:
        # Find position across portfolios
        position, tenant_id, portfolio_id = _find_position_legacy(position_id)
        if not position:
            raise HTTPException(status_code=404, detail=f"Position {position_id} not found")

        # Get latest live quote
        price_data = container.market_data.get_reference_price(position.asset_symbol)
        if not price_data:
            raise HTTPException(
                status_code=404, detail=f"No market data available for {position.asset_symbol}"
            )

        # Evaluate position using EvaluatePositionUC
        eval_uc = container.evaluate_position_uc
        evaluation_result = eval_uc.evaluate(
            tenant_id=tenant_id,
            portfolio_id=portfolio_id,
            position_id=position_id,
            current_price=price_data.price,
        )

        action = evaluation_result.get("action", "HOLD")
        action_reason = evaluation_result.get("action_reason", "No trigger detected")
        order_proposal = evaluation_result.get("order_proposal")

        # If BUY/SELL, create and execute order
        order_id = None
        trade_id = None
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

            submit_uc = container.submit_order_uc
            execute_uc = container.execute_order_uc

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

        # Reload position to get updated state
        updated_position = container.positions.get(
            tenant_id=tenant_id,
            portfolio_id=portfolio_id,
            position_id=position_id,
        )

        # Get baseline for delta calculations
        baseline = None
        if hasattr(container, "position_baseline"):
            baseline = container.position_baseline.get_latest(position_id)

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

        # Build response
        return {
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
                "order_id": order_id,
                "trade_id": trade_id,
                "evaluation_timestamp": datetime.now(timezone.utc).isoformat(),
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        import traceback

        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error executing tick: {str(e)}")


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


@router.get("/positions/{position_id}/events")
def list_position_events_legacy(position_id: str, limit: int = Query(100)) -> Dict[str, Any]:
    """Legacy endpoint to list events for a position."""
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

    return {"position_id": position_id, "events": events}


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
        from application.use_cases.submit_order_uc import CreateOrderRequest

        submit_uc = container.submit_order_uc
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
