# =========================
# backend/app/routes/portfolios.py
# =========================

from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, ConfigDict

from app.di import container
from application.services.portfolio_service import PortfolioService

# Align with other routers (positions, simulations) that use /v1 prefix
router = APIRouter(prefix="/v1/tenants/{tenant_id}/portfolios", tags=["portfolios"])


# --- Request/Response Models ---


class StartingCash(BaseModel):
    currency: str = "USD"
    amount: float


class CreatePortfolioRequest(BaseModel):
    name: str
    description: Optional[str] = None
    type: str = "LIVE"  # LIVE/SIM/SANDBOX
    template: str = "DEFAULT"
    hours_policy: str = "OPEN_ONLY"  # OPEN_ONLY/OPEN_PLUS_AFTER_HOURS
    model_config = ConfigDict(extra="forbid")


class UpdatePortfolioRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class CashTransactionRequest(BaseModel):
    amount: float
    reason: Optional[str] = None
    position_id: Optional[str] = None  # If provided, deposit/withdraw to/from specific position


class CreatePositionRequest(BaseModel):
    asset: str
    qty: float = 0.0
    avg_cost: Optional[float] = None
    anchor_price: Optional[float] = None
    starting_cash: StartingCash
    model_config = ConfigDict(extra="forbid")


class PortfolioResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    user_id: str
    created_at: str
    updated_at: str


class PortfolioSummaryResponse(BaseModel):
    portfolio_id: str
    portfolio_name: str
    description: Optional[str]
    total_positions: int
    total_cash: float
    total_value: float
    positions_by_ticker: Dict[str, Any]
    created_at: str
    updated_at: str


# --- Dependency Injection ---


def get_portfolio_service() -> PortfolioService:
    """Get portfolio service instance."""
    return PortfolioService(
        portfolio_repo=container.portfolio_repo,
        positions_repo=container.positions,
        portfolio_config_repo=container.portfolio_config_repo,
        baseline_repo=getattr(container, "position_baseline", None),
        market_data_repo=getattr(container, "market_data", None),
    )


# --- API Endpoints ---


@router.post("", response_model=Dict[str, str], status_code=201)
def create_portfolio(
    tenant_id: str,
    request: CreatePortfolioRequest,
    portfolio_service: PortfolioService = Depends(get_portfolio_service),
) -> Dict[str, str]:
    """Create a new portfolio with metadata and config."""
    try:
        portfolio = portfolio_service.create_portfolio(
            tenant_id=tenant_id,
            name=request.name,
            description=request.description,
            user_id="default",
            portfolio_type=request.type,
            trading_hours_policy=request.hours_policy,
            template=request.template,
        )
        return {"portfolio_id": portfolio.id}
    except ValueError as e:
        # Handle validation errors (e.g., duplicate name)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating portfolio: {str(e)}")


@router.get("", response_model=List[PortfolioResponse])
def list_portfolios(
    tenant_id: str,
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    portfolio_service: PortfolioService = Depends(get_portfolio_service),
) -> List[PortfolioResponse]:
    """List all portfolios for a tenant."""
    try:
        portfolios = portfolio_service.list_portfolios(tenant_id=tenant_id, user_id=user_id)
        return [
            PortfolioResponse(
                id=p.id,
                name=p.name,
                description=p.description,
                user_id=p.user_id,
                created_at=p.created_at.isoformat(),
                updated_at=p.updated_at.isoformat(),
            )
            for p in portfolios
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing portfolios: {str(e)}")


@router.get("/{portfolio_id}", response_model=PortfolioResponse)
def get_portfolio(
    tenant_id: str,
    portfolio_id: str,
    portfolio_service: PortfolioService = Depends(get_portfolio_service),
) -> PortfolioResponse:
    """Get portfolio details."""
    try:
        portfolio = portfolio_service.get_portfolio(tenant_id=tenant_id, portfolio_id=portfolio_id)
        if not portfolio:
            raise HTTPException(status_code=404, detail="Portfolio not found")

        return PortfolioResponse(
            id=portfolio.id,
            name=portfolio.name,
            description=portfolio.description,
            user_id=portfolio.user_id,
            created_at=portfolio.created_at.isoformat(),
            updated_at=portfolio.updated_at.isoformat(),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting portfolio: {str(e)}")


@router.put("/{portfolio_id}", response_model=PortfolioResponse)
def update_portfolio(
    tenant_id: str,
    portfolio_id: str,
    request: UpdatePortfolioRequest,
    portfolio_service: PortfolioService = Depends(get_portfolio_service),
) -> PortfolioResponse:
    """Update portfolio metadata."""
    try:
        portfolio = portfolio_service.update_portfolio(
            tenant_id=tenant_id,
            portfolio_id=portfolio_id,
            name=request.name,
            description=request.description,
        )
        if not portfolio:
            raise HTTPException(status_code=404, detail="Portfolio not found")

        return PortfolioResponse(
            id=portfolio.id,
            name=portfolio.name,
            description=portfolio.description,
            user_id=portfolio.user_id,
            created_at=portfolio.created_at.isoformat(),
            updated_at=portfolio.updated_at.isoformat(),
        )
    except ValueError as e:
        # Handle validation errors (e.g., duplicate name)
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating portfolio: {str(e)}")


@router.delete("/{portfolio_id}", status_code=204)
def delete_portfolio(
    tenant_id: str,
    portfolio_id: str,
    portfolio_service: PortfolioService = Depends(get_portfolio_service),
):
    """Delete a portfolio."""
    try:
        deleted = portfolio_service.delete_portfolio(tenant_id=tenant_id, portfolio_id=portfolio_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Portfolio not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting portfolio: {str(e)}")


@router.get("/{portfolio_id}/overview", response_model=Dict[str, Any])
def get_portfolio_overview(
    tenant_id: str,
    portfolio_id: str,
    portfolio_service: PortfolioService = Depends(get_portfolio_service),
) -> Dict[str, Any]:
    """Get portfolio overview with cash, positions, config, and KPIs."""
    try:
        overview = portfolio_service.get_portfolio_overview(
            tenant_id=tenant_id, portfolio_id=portfolio_id
        )
        if not overview:
            raise HTTPException(status_code=404, detail="Portfolio not found")
        return overview
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting portfolio overview: {str(e)}")


@router.get("/{portfolio_id}/positions", response_model=List[Dict[str, Any]])
def get_portfolio_positions(
    tenant_id: str,
    portfolio_id: str,
    portfolio_service: PortfolioService = Depends(get_portfolio_service),
) -> List[Dict[str, Any]]:
    """Get all positions in a portfolio."""
    try:
        positions = portfolio_service.get_portfolio_positions(
            tenant_id=tenant_id, portfolio_id=portfolio_id
        )
        result = []
        for p in positions:
            try:
                cash_value = getattr(p, "cash", None)
                if cash_value is None:
                    cash_value = 0.0
                result.append(
                    {
                        "id": p.id,
                        "asset": p.asset_symbol,
                        "qty": p.qty,
                        "cash": float(cash_value),  # Cash lives in PositionCell, default to 0.0
                        "anchor_price": p.anchor_price,
                        "avg_cost": p.avg_cost,
                    }
                )
            except Exception as pos_error:
                # Log individual position error but continue
                print(f"Error processing position {getattr(p, 'id', 'unknown')}: {pos_error}")
                continue
        return result
    except Exception as e:
        import traceback

        print(f"Error getting portfolio positions: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error getting portfolio positions: {str(e)}")


@router.post("/{portfolio_id}/positions", status_code=201)
def create_position_in_portfolio(
    tenant_id: str,
    portfolio_id: str,
    request: CreatePositionRequest,
    portfolio_service: PortfolioService = Depends(get_portfolio_service),
) -> Dict[str, str]:
    """Create a new position in a portfolio."""
    try:
        # Validate required fields
        if not request.asset or not request.asset.strip():
            raise HTTPException(status_code=400, detail="Asset symbol is required")
        if request.qty < 0:
            raise HTTPException(status_code=400, detail="Quantity must be 0 or greater")
        if request.starting_cash.amount < 0:
            raise HTTPException(status_code=400, detail="Starting cash must be 0 or greater")

        # Create position directly in the portfolio
        # Per usage model: starting_cash is provided with the position request
        position = portfolio_service.create_position_in_portfolio(
            tenant_id=tenant_id,
            portfolio_id=portfolio_id,
            asset_symbol=request.asset.strip().upper(),
            qty=request.qty,
            anchor_price=request.anchor_price,
            avg_cost=request.avg_cost,
            starting_cash=request.starting_cash.amount,
        )
        return {
            "message": "Position created in portfolio",
            "portfolio_id": portfolio_id,
            "position_id": position.id,
        }
    except HTTPException:
        raise
    except ValueError as e:
        # Handle validation errors
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Log the full error for debugging
        import traceback

        error_detail = str(e)
        print(f"Error creating position: {error_detail}")
        traceback.print_exc()

        # Include more context in the error message
        if "status" in error_detail.lower() or "no such column" in error_detail.lower():
            error_detail = (
                f"Database schema issue: {error_detail}. This may require running a migration."
            )

        raise HTTPException(
            status_code=500,
            detail=f"Failed to create position for asset {request.asset}: {error_detail}",
        )


@router.post("/{portfolio_id}/positions/{position_id}", status_code=201)
def add_position_to_portfolio(
    tenant_id: str,
    portfolio_id: str,
    position_id: str,
    portfolio_service: PortfolioService = Depends(get_portfolio_service),
) -> Dict[str, str]:
    """Add an existing position to a portfolio."""
    try:
        added = portfolio_service.add_position_to_portfolio(
            tenant_id=tenant_id, portfolio_id=portfolio_id, position_id=position_id
        )
        if not added:
            raise HTTPException(
                status_code=400,
                detail="Position already in portfolio or portfolio/position not found",
            )
        return {
            "message": "Position added to portfolio",
            "portfolio_id": portfolio_id,
            "position_id": position_id,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding position to portfolio: {str(e)}")


@router.delete("/{portfolio_id}/positions/{position_id}", status_code=204)
def remove_position_from_portfolio(
    tenant_id: str,
    portfolio_id: str,
    position_id: str,
    portfolio_service: PortfolioService = Depends(get_portfolio_service),
):
    """Remove a position from a portfolio."""
    try:
        removed = portfolio_service.remove_position_from_portfolio(
            tenant_id=tenant_id, portfolio_id=portfolio_id, position_id=position_id
        )
        if not removed:
            raise HTTPException(status_code=404, detail="Position not found in portfolio")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error removing position from portfolio: {str(e)}"
        )


@router.post("/{portfolio_id}/positions/{position_id}/start", status_code=200)
def start_position_trading(
    tenant_id: str,
    portfolio_id: str,
    position_id: str,
    portfolio_service: PortfolioService = Depends(get_portfolio_service),
) -> Dict[str, Any]:
    """
    Start trading for a position (per usage model: user presses "Start" on a Position).

    Sets position status to RUNNING and starts the backend scheduler/orchestrator.
    """
    try:
        # Get position
        position = portfolio_service._positions_repo.get(
            tenant_id=tenant_id, portfolio_id=portfolio_id, position_id=position_id
        )
        if not position:
            raise HTTPException(status_code=404, detail="Position not found")

        # Update status to RUNNING
        # Note: We need to update the PositionModel directly since Position entity doesn't have status yet
        from infrastructure.persistence.sql.models import PositionModel
        from app.di import container

        # Get session from positions repo
        if hasattr(container.positions, "_sf"):
            with container.positions._sf() as session:
                position_model = session.get(PositionModel, position_id)
                if position_model:
                    position_model.status = "RUNNING"
                    session.commit()

        # Start trading orchestrator for this position
        from application.orchestrators.live_trading import LiveTradingOrchestrator

        orchestrator = LiveTradingOrchestrator(
            position_repo=container.positions,
            market_data=container.market_data,
            event_logger=getattr(container, "event_logger", None),
        )
        trace_id = orchestrator.run_cycle_for_position(position_id, source="api/manual")

        return {
            "message": "Position trading started",
            "position_id": position_id,
            "status": "RUNNING",
            "trace_id": trace_id,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting position trading: {str(e)}")


@router.post("/{portfolio_id}/positions/{position_id}/pause", status_code=200)
def pause_position_trading(
    tenant_id: str,
    portfolio_id: str,
    position_id: str,
    portfolio_service: PortfolioService = Depends(get_portfolio_service),
) -> Dict[str, Any]:
    """
    Pause trading for a position.

    Sets position status to PAUSED. Trading stops but can be resumed.
    """
    try:
        # Get position
        position = portfolio_service._positions_repo.get(
            tenant_id=tenant_id, portfolio_id=portfolio_id, position_id=position_id
        )
        if not position:
            raise HTTPException(status_code=404, detail="Position not found")

        # Update status to PAUSED
        from infrastructure.persistence.sql.models import PositionModel
        from app.di import container

        if hasattr(container.positions, "_sf"):
            with container.positions._sf() as session:
                position_model = session.get(PositionModel, position_id)
                if position_model:
                    position_model.status = "PAUSED"
                    session.commit()

        return {
            "message": "Position trading paused",
            "position_id": position_id,
            "status": "PAUSED",
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error pausing position trading: {str(e)}")


@router.get("/{portfolio_id}/positions/{position_id}/baseline", status_code=200)
def get_position_baseline(
    tenant_id: str,
    portfolio_id: str,
    position_id: str,
) -> Dict[str, Any]:
    """
    Get the latest baseline for a position (per usage model: baseline comparison).
    """
    try:
        from app.di import container

        if not hasattr(container, "position_baseline"):
            raise HTTPException(status_code=501, detail="Baseline repository not available")

        baseline = container.position_baseline.get_latest(position_id)
        if not baseline:
            raise HTTPException(status_code=404, detail="No baseline found for this position")

        return baseline
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting baseline: {str(e)}")


@router.get("/{portfolio_id}/positions/{position_id}/events", status_code=200)
def get_position_events(
    tenant_id: str,
    portfolio_id: str,
    position_id: str,
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    limit: Optional[int] = Query(100, description="Maximum number of events to return"),
) -> List[Dict[str, Any]]:
    """
    Get event log for a position (per usage model: chronological event log).

    Returns simplified immutable log entries for quick queries.
    """
    try:
        from app.di import container

        if not hasattr(container, "position_event"):
            raise HTTPException(status_code=501, detail="Event repository not available")

        events = container.position_event.list_by_position(
            position_id=position_id,
            event_type=event_type,
            limit=limit,
        )

        return events
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting events: {str(e)}")


@router.get("/{portfolio_id}/positions/{position_id}/timeline", status_code=200)
def get_position_timeline(
    tenant_id: str,
    portfolio_id: str,
    position_id: str,
    mode: Optional[str] = Query(None, description="Filter by mode (LIVE/SIMULATION)"),
    limit: Optional[int] = Query(100, description="Maximum number of timeline rows to return"),
) -> List[Dict[str, Any]]:
    """
    Get detailed evaluation timeline for a position (Trade Screen - Event Log).

    Returns comprehensive timeline rows with OHLC, trigger thresholds, guardrail limits,
    actions, and position state changes.
    """
    try:
        from app.di import container

        if not hasattr(container, "evaluation_timeline"):
            raise HTTPException(status_code=501, detail="Timeline repository not available")

        timeline = container.evaluation_timeline.list_by_position(
            tenant_id=tenant_id,
            portfolio_id=portfolio_id,
            position_id=position_id,
            mode=mode,
            limit=limit,
        )

        return timeline
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting timeline: {str(e)}")


@router.get("/{portfolio_id}/summary", response_model=PortfolioSummaryResponse)
def get_portfolio_summary(
    tenant_id: str,
    portfolio_id: str,
    portfolio_service: PortfolioService = Depends(get_portfolio_service),
) -> PortfolioSummaryResponse:
    """Get portfolio summary with aggregated metrics."""
    try:
        summary = portfolio_service.get_portfolio_summary(
            tenant_id=tenant_id, portfolio_id=portfolio_id
        )
        if not summary:
            raise HTTPException(status_code=404, detail="Portfolio not found")

        return PortfolioSummaryResponse(**summary)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting portfolio summary: {str(e)}")


@router.get("/{portfolio_id}/analytics", response_model=Dict[str, Any])
def get_portfolio_analytics(
    tenant_id: str,
    portfolio_id: str,
    portfolio_service: PortfolioService = Depends(get_portfolio_service),
) -> Dict[str, Any]:
    """Get detailed portfolio analytics."""
    try:
        analytics = portfolio_service.get_portfolio_analytics(
            tenant_id=tenant_id, portfolio_id=portfolio_id
        )
        if not analytics:
            raise HTTPException(status_code=404, detail="Portfolio not found")

        return analytics
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting portfolio analytics: {str(e)}")


@router.post("/{portfolio_id}/cash/deposit", status_code=200)
def deposit_cash(
    tenant_id: str,
    portfolio_id: str,
    request: CashTransactionRequest,
    portfolio_service: PortfolioService = Depends(get_portfolio_service),
) -> Dict[str, Any]:
    """Deposit cash into a portfolio."""
    try:
        if request.amount <= 0:
            raise HTTPException(status_code=400, detail="Deposit amount must be positive")

        result = portfolio_service.deposit_cash(
            tenant_id=tenant_id,
            portfolio_id=portfolio_id,
            amount=request.amount,
            position_id=request.position_id,
        )
        if not result:
            raise HTTPException(status_code=404, detail="Portfolio not found")

        # Generate a trace_id for audit purposes
        from uuid import uuid4

        trace_id = f"trace_{uuid4().hex[:8]}"

        return {
            "data": None,
            "trace_id": trace_id,
            "message": f"Deposited ${request.amount:.2f} to {result.get('positions_updated', 0)} positions",
            "cash_balance": result.get("cash_balance", 0.0),
            "available_cash": result.get("available_cash", 0.0),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error depositing cash: {str(e)}")


@router.post("/{portfolio_id}/cash/withdraw", status_code=200)
def withdraw_cash(
    tenant_id: str,
    portfolio_id: str,
    request: CashTransactionRequest,
    portfolio_service: PortfolioService = Depends(get_portfolio_service),
) -> Dict[str, Any]:
    """Withdraw cash from a portfolio."""
    try:
        if request.amount <= 0:
            raise HTTPException(status_code=400, detail="Withdrawal amount must be positive")

        result = portfolio_service.withdraw_cash(
            tenant_id=tenant_id,
            portfolio_id=portfolio_id,
            amount=request.amount,
            position_id=request.position_id,
        )
        if not result:
            raise HTTPException(status_code=404, detail="Portfolio not found")

        # Generate a trace_id for audit purposes
        from uuid import uuid4

        trace_id = f"trace_{uuid4().hex[:8]}"

        return {
            "data": None,
            "trace_id": trace_id,
            "message": f"Withdrew ${request.amount:.2f} from {result.get('positions_updated', 0)} positions",
            "cash_balance": result.get("cash_balance", 0.0),
            "available_cash": result.get("available_cash", 0.0),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error withdrawing cash: {str(e)}")


class PortfolioConfigRequest(BaseModel):
    trigger_threshold_up_pct: float
    trigger_threshold_down_pct: float
    min_stock_pct: float
    max_stock_pct: float
    max_trade_pct_of_position: float
    commission_rate: float
    market_hours_policy: str  # 'market-open-only' | 'market-plus-after-hours'


@router.get("/{portfolio_id}/config", response_model=Dict[str, Any])
def get_portfolio_config(
    tenant_id: str,
    portfolio_id: str,
    portfolio_service: PortfolioService = Depends(get_portfolio_service),
) -> Dict[str, Any]:
    """Get portfolio configuration."""
    try:
        portfolio = portfolio_service.get_portfolio(tenant_id=tenant_id, portfolio_id=portfolio_id)
        if not portfolio:
            raise HTTPException(status_code=404, detail="Portfolio not found")

        config = portfolio_service.get_portfolio_config(
            tenant_id=tenant_id, portfolio_id=portfolio_id
        )

        # Map backend format to frontend format
        return {
            "trigger_threshold_up_pct": config.trigger_up_pct if config else 3.0,
            "trigger_threshold_down_pct": config.trigger_down_pct if config else -3.0,
            "min_stock_pct": config.min_stock_pct if config else 25.0,
            "max_stock_pct": config.max_stock_pct if config else 75.0,
            "max_trade_pct_of_position": config.max_trade_pct_of_position if config else 50.0,
            "commission_rate": config.commission_rate_pct if config else 0.1,
            "market_hours_policy": (
                "market-plus-after-hours"
                if portfolio.trading_hours_policy == "OPEN_PLUS_AFTER_HOURS"
                else "market-open-only"
            ),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting portfolio config: {str(e)}")


@router.put("/{portfolio_id}/config", status_code=200)
def update_portfolio_config(
    tenant_id: str,
    portfolio_id: str,
    request: PortfolioConfigRequest,
    portfolio_service: PortfolioService = Depends(get_portfolio_service),
) -> Dict[str, Any]:
    """Update portfolio configuration."""
    try:
        # Update portfolio trading_hours_policy if market_hours_policy changed
        portfolio = portfolio_service.get_portfolio(tenant_id=tenant_id, portfolio_id=portfolio_id)
        if not portfolio:
            raise HTTPException(status_code=404, detail="Portfolio not found")

        # Map frontend market_hours_policy to backend trading_hours_policy
        trading_hours_policy = (
            "OPEN_PLUS_AFTER_HOURS"
            if request.market_hours_policy == "market-plus-after-hours"
            else "OPEN_ONLY"
        )

        if portfolio.trading_hours_policy != trading_hours_policy:
            portfolio_service.update_portfolio(
                tenant_id=tenant_id,
                portfolio_id=portfolio_id,
                trading_hours_policy=trading_hours_policy,
            )

        # Update config
        portfolio_service.update_portfolio_config(
            tenant_id=tenant_id,
            portfolio_id=portfolio_id,
            trigger_up_pct=request.trigger_threshold_up_pct,
            trigger_down_pct=request.trigger_threshold_down_pct,
            min_stock_pct=request.min_stock_pct,
            max_stock_pct=request.max_stock_pct,
            max_trade_pct_of_position=request.max_trade_pct_of_position,
            commission_rate_pct=request.commission_rate,
        )

        return {"message": "Config updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating portfolio config: {str(e)}")


@router.get("/{portfolio_id}/config/effective", response_model=Dict[str, Any])
def get_effective_config(
    tenant_id: str,
    portfolio_id: str,
    portfolio_service: PortfolioService = Depends(get_portfolio_service),
) -> Dict[str, Any]:
    """Get effective configuration (what the engine actually uses)."""
    try:
        portfolio = portfolio_service.get_portfolio(tenant_id=tenant_id, portfolio_id=portfolio_id)
        if not portfolio:
            raise HTTPException(status_code=404, detail="Portfolio not found")

        config = portfolio_service.get_portfolio_config(
            tenant_id=tenant_id, portfolio_id=portfolio_id
        )

        # Effective config is the same as editable for now (no overrides yet)
        return {
            "trigger_threshold_up_pct": config.trigger_up_pct if config else 3.0,
            "trigger_threshold_down_pct": config.trigger_down_pct if config else -3.0,
            "min_stock_pct": config.min_stock_pct if config else 25.0,
            "max_stock_pct": config.max_stock_pct if config else 75.0,
            "max_trade_pct_of_position": config.max_trade_pct_of_position if config else 50.0,
            "commission_rate": config.commission_rate_pct if config else 0.1,
            "market_hours_policy": (
                "market-plus-after-hours"
                if portfolio.trading_hours_policy == "OPEN_PLUS_AFTER_HOURS"
                else "market-open-only"
            ),
            "last_updated": (
                config.updated_at.isoformat() if config else datetime.now(timezone.utc).isoformat()
            ),
            "version": config.version if config else 1,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting effective config: {str(e)}")
