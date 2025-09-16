# =========================
# backend/app/routes/positions.py
# =========================
# backend/app/routes/positions.py  (only the relevant bits)

from typing import Optional, cast
from typing import Any, Dict
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.di import container
from dataclasses import asdict
from domain.value_objects.order_policy import OrderPolicy
from domain.value_objects.types import ActionBelowMin
from application.use_cases.evaluate_position_uc import EvaluatePositionUC
from application.use_cases.simulation_uc import SimulationUC

router = APIRouter(prefix="/v1")


class OrderPolicyIn(BaseModel):
    min_qty: float = 0.0
    min_notional: float = 0.0
    lot_size: float = 0.0
    qty_step: float = 0.0
    action_below_min: str = "hold"  # "hold" | "reject" | "clip"
    # Volatility trading parameters
    trigger_threshold_pct: float = 0.03
    rebalance_ratio: float = 1.6667
    commission_rate: float = 0.0001
    # Market hours configuration
    allow_after_hours: bool = False


class CreatePositionRequest(BaseModel):
    ticker: str
    qty: float = 0.0
    cash: float = 0.0
    order_policy: Optional[OrderPolicyIn] = None


class CreatePositionResponse(BaseModel):
    id: str
    ticker: str
    qty: float
    cash: float
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
    pos_repo = container.positions
    pos = pos_repo.create(ticker=payload.ticker, qty=payload.qty, cash=payload.cash)

    if payload.order_policy:
        op = payload.order_policy
        pos.order_policy = OrderPolicy(
            min_qty=op.min_qty,
            min_notional=op.min_notional,
            lot_size=op.lot_size,
            qty_step=op.qty_step,
            action_below_min=op.action_below_min,
        )
        pos_repo.save(pos)

    return CreatePositionResponse(id=pos.id, ticker=pos.ticker, qty=pos.qty, cash=pos.cash)


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
def evaluate_position(position_id: str, current_price: float) -> Dict[str, Any]:
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


@router.post("/simulation/run")
def run_simulation(
    ticker: str,
    start_date: str,
    end_date: str,
    initial_cash: float = 10000.0,
    position_config: Optional[Dict[str, Any]] = None,
    include_after_hours: bool = False,
) -> Dict[str, Any]:
    """Run a trading simulation for backtesting and performance comparison."""
    try:
        from datetime import datetime

        start_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
        end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))

        # Create simulation use case
        sim_uc = SimulationUC(
            market_data=container.market_data,
            positions=container.positions,
            events=container.events,
            clock=container.clock,
        )

        # Run simulation
        result = sim_uc.run_simulation(
            ticker=ticker,
            start_date=start_dt,
            end_date=end_dt,
            initial_cash=initial_cash,
            position_config=position_config,
            include_after_hours=include_after_hours,
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
        }

    except Exception as e:
        raise HTTPException(400, detail=f"Error running simulation: {str(e)}")


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
