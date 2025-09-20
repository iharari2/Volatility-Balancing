# =========================
# backend/app/routes/positions.py
# =========================
# backend/app/routes/positions.py  (only the relevant bits)

from typing import Optional, cast
from typing import Any, Dict
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from infrastructure.market.simulation_presets import SimulationPresetManager, SimulationPreset
from app.di import container
from dataclasses import asdict
from domain.value_objects.order_policy import OrderPolicy
from domain.value_objects.types import ActionBelowMin
from application.use_cases.evaluate_position_uc import EvaluatePositionUC

router = APIRouter(prefix="/v1")


class OrderPolicyIn(BaseModel):
    min_qty: float = 0.0
    min_notional: float = 0.0
    lot_size: float = 0.0
    qty_step: float = 0.0
    action_below_min: str = "hold"  # "hold" | "reject" | "clip"
    # Volatility trading parameters
    trigger_threshold_pct: float = 0.03
    rebalance_ratio: float = 0.5  # Updated to match simulation default
    commission_rate: float = 0.0001
    # Market hours configuration
    allow_after_hours: bool = True  # Default to after hours ON


class GuardrailsIn(BaseModel):
    min_stock_alloc_pct: float = 0.25
    max_stock_alloc_pct: float = 0.75
    max_orders_per_day: int = 5


class CreatePositionRequest(BaseModel):
    ticker: str
    qty: float = 0.0
    cash: float = 0.0
    anchor_price: Optional[float] = None
    order_policy: Optional[OrderPolicyIn] = None
    guardrails: Optional[GuardrailsIn] = None
    withholding_tax_rate: Optional[float] = None


class CreatePositionResponse(BaseModel):
    id: str
    ticker: str
    qty: float
    cash: float
    anchor_price: Optional[float] = None
    # expose policy if you want it in the API response; otherwise remove:
    order_policy: Optional[OrderPolicyIn] = None


def _to_domain_policy(op: Optional[OrderPolicyIn]) -> OrderPolicy:
    if not op:
        return OrderPolicy()

    allowed = {"hold", "reject", "clip"}
    if op.action_below_min not in allowed:
        raise HTTPException(
            status_code=422,
            detail=f"Unsupported action_below_min: {op.action_below_min!r}",
        )
    action = cast(ActionBelowMin, op.action_below_min)

    return OrderPolicy(
        min_qty=op.min_qty,
        min_notional=op.min_notional,
        lot_size=op.lot_size,
        qty_step=op.qty_step,
        action_below_min=action,
        trigger_threshold_pct=op.trigger_threshold_pct,
        rebalance_ratio=op.rebalance_ratio,
        commission_rate=op.commission_rate,
        allow_after_hours=op.allow_after_hours,
    )


@router.post("/positions", response_model=CreatePositionResponse, status_code=201)
def create_position(payload: CreatePositionRequest) -> CreatePositionResponse:
    try:
        print(f"Creating position with payload: {payload}")
        pos_repo = container.positions

        # Check if position with same ticker already exists
        existing_positions = pos_repo.list_all()
        print(f"Found {len(existing_positions)} existing positions")
        existing_pos = next((p for p in existing_positions if p.ticker == payload.ticker), None)

        if existing_pos:
            # Update existing position instead of creating new one
            print(f"Updating existing position: {existing_pos.id}")
            existing_pos.qty = payload.qty
            existing_pos.cash = payload.cash
            if payload.anchor_price is not None:
                existing_pos.anchor_price = payload.anchor_price
            pos = existing_pos
        else:
            # Create new position
            print("Creating new position")
            pos = pos_repo.create(ticker=payload.ticker, qty=payload.qty, cash=payload.cash)
            if payload.anchor_price is not None:
                pos.anchor_price = payload.anchor_price

        if payload.order_policy:
            # Validate and convert order policy
            validated_policy = _to_domain_policy(payload.order_policy)
            pos.order_policy = validated_policy
            pos_repo.save(pos)

        if payload.guardrails:
            # Convert guardrails
            from domain.value_objects.guardrails import GuardrailPolicy

            pos.guardrails = GuardrailPolicy(
                min_stock_alloc_pct=payload.guardrails.min_stock_alloc_pct,
                max_stock_alloc_pct=payload.guardrails.max_stock_alloc_pct,
                max_orders_per_day=payload.guardrails.max_orders_per_day,
            )
            pos_repo.save(pos)

        print(f"Position created/updated: {pos.id}")
        return CreatePositionResponse(
            id=pos.id,
            ticker=pos.ticker,
            qty=pos.qty,
            cash=pos.cash,
            anchor_price=pos.anchor_price,
            order_policy=payload.order_policy,  # Include the order policy in response
        )
    except HTTPException:
        # Re-raise HTTP exceptions (like validation errors) as-is
        raise
    except Exception as e:
        print(f"Error creating position: {e}")
        import traceback

        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/positions")
def list_positions() -> Dict[str, Any]:
    """List all positions."""
    positions = container.positions.list_all()
    return {
        "positions": [
            {
                "id": pos.id,
                "ticker": pos.ticker,
                "qty": pos.qty,
                "cash": pos.cash,
                "anchor_price": pos.anchor_price,
                "order_policy": {
                    "trigger_threshold_pct": pos.order_policy.trigger_threshold_pct,
                    "rebalance_ratio": pos.order_policy.rebalance_ratio,
                    "commission_rate": pos.order_policy.commission_rate,
                    "min_notional": pos.order_policy.min_notional,
                    "allow_after_hours": pos.order_policy.allow_after_hours,
                },
                "guardrails": {
                    "min_stock_alloc_pct": pos.guardrails.min_stock_alloc_pct,
                    "max_stock_alloc_pct": pos.guardrails.max_stock_alloc_pct,
                    "max_orders_per_day": pos.guardrails.max_orders_per_day,
                },
            }
            for pos in positions
        ]
    }


@router.post("/clear-positions")
def clear_all_positions() -> Dict[str, Any]:
    """Clear all positions from memory."""
    container.positions.clear()
    return {"message": "All positions cleared", "count": 0}


@router.get("/positions/{position_id}")
def get_position(position_id: str) -> Dict[str, Any]:
    pos = container.positions.get(position_id)
    if not pos:
        raise HTTPException(404, detail="position_not_found")
    return {
        "id": pos.id,
        "ticker": pos.ticker,
        "qty": pos.qty,
        "cash": pos.cash,
        "anchor_price": pos.anchor_price,
        "order_policy": {
            "trigger_threshold_pct": pos.order_policy.trigger_threshold_pct,
            "rebalance_ratio": pos.order_policy.rebalance_ratio,
            "commission_rate": pos.order_policy.commission_rate,
            "min_notional": pos.order_policy.min_notional,
        },
        "guardrails": {
            "min_stock_alloc_pct": pos.guardrails.min_stock_alloc_pct,
            "max_stock_alloc_pct": pos.guardrails.max_stock_alloc_pct,
            "max_orders_per_day": pos.guardrails.max_orders_per_day,
        },
    }


@router.post("/positions/{position_id}/evaluate")
def evaluate_position(position_id: str, current_price: float = Query(...)) -> Dict[str, Any]:
    """Evaluate position for volatility triggers with manual price."""
    if not container.positions.get(position_id):
        raise HTTPException(404, detail="position_not_found")

    uc = EvaluatePositionUC(
        positions=container.positions,
        events=container.events,
        market_data=container.market_data,
        clock=container.clock,
    )

    return uc.evaluate(position_id, current_price)


@router.post("/positions/{position_id}/evaluate/market")
def evaluate_position_with_market_data(position_id: str) -> Dict[str, Any]:
    """Evaluate position using real-time market data with after-hours support."""
    if not container.positions.get(position_id):
        raise HTTPException(404, detail="position_not_found")

    uc = EvaluatePositionUC(
        positions=container.positions,
        events=container.events,
        market_data=container.market_data,
        clock=container.clock,
    )

    return uc.evaluate_with_market_data(position_id)


@router.post("/positions/{position_id}/anchor")
def set_anchor_price(position_id: str, price: float) -> Dict[str, Any]:
    """Set the anchor price for volatility trading."""
    pos = container.positions.get(position_id)
    if not pos:
        raise HTTPException(404, detail="position_not_found")

    pos.set_anchor_price(price)
    container.positions.save(pos)

    return {
        "position_id": position_id,
        "anchor_price": price,
        "message": f"Anchor price set to ${price:.2f}",
    }


@router.get("/positions/{position_id}/events")
def list_events(position_id: str, limit: int = 100) -> Dict[str, Any]:
    events = container.events.list_for_position(position_id, limit=limit)
    return {"position_id": position_id, "events": [asdict(e) for e in events]}


@router.get("/market/status")
def get_market_status() -> Dict[str, Any]:
    """Get current market status and hours."""
    market_status = container.market_data.get_market_status()
    return {
        "is_open": market_status.is_open,
        "next_open": market_status.next_open.isoformat() if market_status.next_open else None,
        "next_close": market_status.next_close.isoformat() if market_status.next_close else None,
        "timezone": market_status.timezone,
    }


@router.get("/market/price/{ticker}")
def get_market_price(ticker: str) -> Dict[str, Any]:
    """Get current market price data for a ticker."""
    price_data = container.market_data.get_price(ticker)
    if not price_data:
        raise HTTPException(404, detail="ticker_not_found")

    # Validate the price data
    validation = container.market_data.validate_price(price_data, allow_after_hours=True)

    return {
        "ticker": price_data.ticker,
        "price": price_data.price,
        "source": price_data.source.value,
        "timestamp": price_data.timestamp.isoformat(),
        "bid": price_data.bid,
        "ask": price_data.ask,
        "volume": price_data.volume,
        "last_trade_price": price_data.last_trade_price,
        "last_trade_time": (
            price_data.last_trade_time.isoformat() if price_data.last_trade_time else None
        ),
        "is_market_hours": price_data.is_market_hours,
        "is_fresh": price_data.is_fresh,
        "is_inline": price_data.is_inline,
        "validation": validation,
    }


@router.get("/market/historical/{ticker}")
def get_historical_data(
    ticker: str, start_date: str, end_date: str, market_hours_only: bool = False
) -> Dict[str, Any]:
    """Get historical price data for a ticker."""
    try:
        from datetime import datetime

        start_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
        end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))

        # Fetch historical data
        historical_data = container.market_data.fetch_historical_data(ticker, start_dt, end_dt)

        # Convert to API format
        price_data = []
        for data in historical_data:
            price_data.append(
                {
                    "ticker": data.ticker,
                    "price": data.price,
                    "source": data.source.value,
                    "timestamp": data.timestamp.isoformat(),
                    "bid": data.bid,
                    "ask": data.ask,
                    "volume": data.volume,
                    "is_market_hours": data.is_market_hours,
                    "is_fresh": data.is_fresh,
                    "is_inline": data.is_inline,
                }
            )

        return {
            "ticker": ticker,
            "start_date": start_date,
            "end_date": end_date,
            "market_hours_only": market_hours_only,
            "data_points": len(price_data),
            "price_data": price_data,
        }

    except Exception as e:
        raise HTTPException(400, detail=f"Error fetching historical data: {str(e)}")


class SimulationRequest(BaseModel):
    ticker: str
    start_date: str
    end_date: str
    initial_cash: float = 10000.0
    position_config: Optional[Dict[str, Any]] = None
    include_after_hours: bool = False
    intraday_interval_minutes: int = 30  # Configurable intraday simulation interval
    detailed_trigger_analysis: bool = True  # Performance optimization for long simulations


@router.post("/simulation/run")
def run_simulation(request: SimulationRequest) -> Dict[str, Any]:
    """Run a trading simulation for backtesting and performance comparison."""
    try:
        from datetime import datetime

        start_dt = datetime.fromisoformat(request.start_date.replace("Z", "+00:00"))
        end_dt = datetime.fromisoformat(request.end_date.replace("Z", "+00:00"))

        # Create simulation use case
        from application.use_cases.simulation_unified_uc import SimulationUnifiedUC

        sim_uc = SimulationUnifiedUC(
            market_data=container.market_data,
            positions=container.positions,
            events=container.events,
            clock=container.clock,
            dividend_market_data=container.dividend_market_data,
        )

        # Run simulation
        result = sim_uc.run_simulation(
            ticker=request.ticker,
            start_date=start_dt,
            end_date=end_dt,
            initial_cash=request.initial_cash,
            position_config=request.position_config,
            include_after_hours=request.include_after_hours,
            intraday_interval_minutes=request.intraday_interval_minutes,
            detailed_trigger_analysis=request.detailed_trigger_analysis,
        )

        # Convert result to API format
        return {
            "ticker": result.ticker,
            "start_date": result.start_date.isoformat(),
            "end_date": result.end_date.isoformat(),
            "total_trading_days": result.total_trading_days,
            # Algorithm performance
            "algorithm": {
                "trades": result.algorithm_trades,
                "pnl": result.algorithm_pnl,
                "return_pct": result.algorithm_return_pct,
                "volatility": result.algorithm_volatility,
                "sharpe_ratio": result.algorithm_sharpe_ratio,
                "max_drawdown": result.algorithm_max_drawdown,
            },
            # Buy & Hold performance
            "buy_hold": {
                "pnl": result.buy_hold_pnl,
                "return_pct": result.buy_hold_return_pct,
                "volatility": result.buy_hold_volatility,
                "sharpe_ratio": result.buy_hold_sharpe_ratio,
                "max_drawdown": result.buy_hold_max_drawdown,
            },
            # Comparison metrics
            "comparison": {
                "excess_return": result.excess_return,
                "alpha": result.alpha,
                "beta": result.beta,
                "information_ratio": result.information_ratio,
            },
            # Trade details
            "trade_log": result.trade_log,
            "daily_returns": result.daily_returns,
            # Dividend data
            "total_dividends_received": result.total_dividends_received,
            "dividend_events": result.dividend_events,
            # Market data for visualization
            "price_data": result.price_data,
            # Trigger analysis
            "trigger_analysis": result.trigger_analysis,
            # Debug info
            "debug_info": getattr(result, "debug_info", []),
            "debug_storage_info": getattr(result, "debug_storage_info", {}),
            "debug_retrieval_info": getattr(result, "debug_retrieval_info", {}),
        }

    except Exception as e:
        raise HTTPException(400, detail=f"Error running simulation: {str(e)}")


@router.get("/simulation/presets")
def get_simulation_presets() -> Dict[str, Any]:
    """Get all available simulation presets."""
    try:
        presets = SimulationPresetManager.get_all_presets()
        return {
            "presets": presets,
            "count": len(presets)
        }
    except Exception as e:
        raise HTTPException(500, detail=f"Error fetching presets: {str(e)}")


@router.get("/simulation/presets/{preset_id}")
def get_simulation_preset(preset_id: str) -> Dict[str, Any]:
    """Get a specific simulation preset by ID."""
    try:
        # Convert string to enum
        preset_enum = SimulationPreset(preset_id)
        config = SimulationPresetManager.get_preset_config(preset_enum)
        
        if not config:
            raise HTTPException(404, detail=f"Preset '{preset_id}' not found")
        
        config["preset_id"] = preset_id
        return config
    except ValueError:
        raise HTTPException(400, detail=f"Invalid preset ID: {preset_id}")
    except Exception as e:
        raise HTTPException(500, detail=f"Error fetching preset: {str(e)}")


@router.post("/simulation/run-with-preset")
def run_simulation_with_preset(
    ticker: str,
    start_date: str,
    end_date: str,
    preset_id: str,
    initial_cash: float = 10000.0
) -> Dict[str, Any]:
    """Run a simulation using a predefined preset."""
    try:
        from datetime import datetime
        
        # Get preset configuration
        preset_enum = SimulationPreset(preset_id)
        preset_config = SimulationPresetManager.get_preset_config(preset_enum)
        
        if not preset_config:
            raise HTTPException(404, detail=f"Preset '{preset_id}' not found")
        
        # Parse dates
        start_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
        end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
        
        # Create simulation use case
        from application.use_cases.simulation_unified_uc import SimulationUnifiedUC
        
        sim_uc = SimulationUnifiedUC(
            market_data=container.market_data,
            positions=container.positions,
            events=container.events,
            clock=container.clock,
            dividend_market_data=container.dividend_market_data,
        )
        
        # Run simulation with preset configuration
        result = sim_uc.run_simulation(
            ticker=ticker,
            start_date=start_dt,
            end_date=end_dt,
            initial_cash=initial_cash,
            position_config=preset_config["position_config"],
            include_after_hours=preset_config["include_after_hours"],
            intraday_interval_minutes=preset_config["intraday_interval_minutes"],
            detailed_trigger_analysis=preset_config["detailed_trigger_analysis"],
        )
        
        # Convert result to API format
        return {
            "ticker": result.ticker,
            "start_date": result.start_date.isoformat(),
            "end_date": result.end_date.isoformat(),
            "initial_cash": result.initial_cash,
            "preset_used": {
                "preset_id": preset_id,
                "name": preset_config["name"],
                "description": preset_config["description"]
            },
            "final_cash": result.final_cash,
            "final_shares": result.final_shares,
            "final_total_value": result.final_total_value,
            "total_pnl": result.total_pnl,
            "total_return_pct": result.total_return_pct,
            "total_commission": result.total_commission,
            "total_trades": result.total_trades,
            "buy_trades": result.buy_trades,
            "sell_trades": result.sell_trades,
            # Algorithm performance
            "algorithm": {
                "pnl": result.algorithm_pnl,
                "return_pct": result.algorithm_return_pct,
                "volatility": result.algorithm_volatility,
                "sharpe_ratio": result.algorithm_sharpe_ratio,
                "max_drawdown": result.algorithm_max_drawdown,
            },
            # Buy & Hold performance
            "buy_hold": {
                "pnl": result.buy_hold_pnl,
                "return_pct": result.buy_hold_return_pct,
                "volatility": result.buy_hold_volatility,
                "sharpe_ratio": result.buy_hold_sharpe_ratio,
                "max_drawdown": result.buy_hold_max_drawdown,
            },
            # Comparison metrics
            "comparison": {
                "excess_return": result.excess_return,
                "alpha": result.alpha,
                "beta": result.beta,
                "information_ratio": result.information_ratio,
            },
            # Trade details
            "trade_log": result.trade_log,
            "daily_returns": result.daily_returns,
            # Dividend data
            "total_dividends_received": result.total_dividends_received,
            "dividend_events": result.dividend_events,
            # Market data for visualization
            "price_data": result.price_data,
            # Trigger analysis
            "trigger_analysis": result.trigger_analysis,
            # Debug info
            "debug_info": getattr(result, "debug_info", []),
            "debug_storage_info": getattr(result, "debug_storage_info", {}),
            "debug_retrieval_info": getattr(result, "debug_retrieval_info", {}),
        }
        
    except ValueError:
        raise HTTPException(400, detail=f"Invalid preset ID: {preset_id}")
    except Exception as e:
        raise HTTPException(400, detail=f"Error running simulation with preset: {str(e)}")


@router.get("/simulation/volatility/{ticker}")
def get_volatility_data(ticker: str, window_minutes: int = 60) -> Dict[str, Any]:
    """Get volatility data for a ticker."""
    try:
        volatility = container.market_data.get_volatility(ticker, window_minutes)

        from datetime import datetime

        return {
            "ticker": ticker,
            "window_minutes": window_minutes,
            "volatility": volatility,
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        raise HTTPException(400, detail=f"Error getting volatility data: {str(e)}")


# Orders endpoints
class CreateOrderRequest(BaseModel):
    side: str  # "BUY" or "SELL"
    qty: float
    price: float


@router.post("/positions/{position_id}/orders/auto-size")
def auto_size_order(
    position_id: str, current_price: float = Query(...), idempotency_key: str = Query(None)
) -> Dict[str, Any]:
    """Create an auto-sized order based on position evaluation."""
    pos = container.positions.get(position_id)
    if not pos:
        raise HTTPException(404, detail="position_not_found")

    # Evaluate the position first
    uc = EvaluatePositionUC(
        positions=container.positions,
        events=container.events,
        market_data=container.market_data,
        clock=container.clock,
    )

    evaluation = uc.evaluate(position_id, current_price)

    if not evaluation.get("trigger_detected") or not evaluation.get("order_proposal"):
        return {
            "position_id": position_id,
            "current_price": current_price,
            "order_submitted": False,
            "reason": "No trigger detected or no valid order proposal",
            "evaluation": evaluation,
        }

    # Create the order
    order_proposal = evaluation["order_proposal"]
    order_id = f"auto_order_{position_id}_{int(__import__('time').time())}"

    return {
        "position_id": position_id,
        "current_price": current_price,
        "order_submitted": True,
        "order_id": order_id,
        "order_details": {
            "side": order_proposal["side"],
            "qty": order_proposal["trimmed_qty"],
            "price": current_price,
            "notional": order_proposal["notional"],
            "commission": order_proposal["commission"],
        },
        "evaluation": evaluation,
    }
