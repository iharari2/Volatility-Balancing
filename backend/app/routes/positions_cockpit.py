# =========================
# backend/app/routes/positions_cockpit.py
# =========================
"""
Position Cockpit API endpoints.

Provides position-centric endpoints for the Position Cockpit UI.
All endpoints are scoped to tenant_id and portfolio_id for security.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel

from app.di import container
from application.services.portfolio_service import PortfolioService
from app.routes.portfolios import get_portfolio_service

router = APIRouter(
    prefix="/v1/tenants/{tenant_id}/portfolios/{portfolio_id}/positions/{position_id}",
    tags=["position-cockpit"],
)


class CockpitSummaryResponse(BaseModel):
    """Response model for position cockpit summary."""

    position: Dict[str, Any]
    baseline: Optional[Dict[str, Any]]
    current_market_data: Optional[Dict[str, Any]]
    trading_status: str  # RUNNING / PAUSED
    position_vs_baseline: Dict[str, Any]  # % and abs deltas
    stock_vs_baseline: Dict[str, Any]  # % and abs deltas


@router.get("/cockpit", response_model=CockpitSummaryResponse)
def get_position_cockpit(
    tenant_id: str,
    portfolio_id: str,
    position_id: str,
    portfolio_service: PortfolioService = Depends(get_portfolio_service),
) -> CockpitSummaryResponse:
    """
    Get comprehensive position cockpit data.

    Returns position details, baseline, current market data, trading status,
    and calculated deltas (position vs baseline, stock vs baseline).
    """
    try:
        cockpit = portfolio_service.get_position_cockpit(
            tenant_id=tenant_id, portfolio_id=portfolio_id, position_id=position_id
        )
        if not cockpit:
            raise HTTPException(status_code=404, detail="Position not found")

        return CockpitSummaryResponse(**cockpit)
    except HTTPException:
        raise
    except Exception as e:
        import traceback

        print(f"Error getting position cockpit: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error getting position cockpit: {str(e)}")


@router.post("/baseline/reset")
def reset_position_baseline(
    tenant_id: str,
    portfolio_id: str,
    position_id: str,
    portfolio_service: PortfolioService = Depends(get_portfolio_service),
) -> Dict[str, Any]:
    """
    Reset the baseline for a position to its current state.
    """
    try:
        baseline = portfolio_service.reset_position_baseline(
            tenant_id=tenant_id, portfolio_id=portfolio_id, position_id=position_id
        )
        if not baseline:
            raise HTTPException(status_code=404, detail="Position not found")
        return {"message": "Baseline reset successful", "baseline": baseline}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error resetting baseline: {str(e)}")


@router.get("/marketdata")
def get_position_marketdata(
    tenant_id: str,
    portfolio_id: str,
    position_id: str,
    limit: int = Query(50, description="Maximum number of data points to return"),
    portfolio_service: PortfolioService = Depends(get_portfolio_service),
) -> Dict[str, Any]:
    """
    Get recent market data for a position.

    Returns latest market data and recent historical data points.
    """
    try:
        data = portfolio_service.get_position_market_data(
            tenant_id=tenant_id, portfolio_id=portfolio_id, position_id=position_id, limit=limit
        )
        if not data:
            raise HTTPException(status_code=404, detail="Position not found")
        return data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting market data: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting market data: {str(e)}")


@router.get("/timeline")
def get_position_timeline_cockpit(
    tenant_id: str,
    portfolio_id: str,
    position_id: str,
    limit: int = Query(500, description="Maximum number of timeline rows to return"),
) -> List[Dict[str, Any]]:
    """
    Get detailed evaluation timeline for a position.
    """
    try:
        if not hasattr(container, "evaluation_timeline"):
            raise HTTPException(status_code=501, detail="Timeline repository not available")

        timeline = container.evaluation_timeline.list_by_position(
            tenant_id=tenant_id,
            portfolio_id=portfolio_id,
            position_id=position_id,
            mode="LIVE",
            limit=limit,
        )

        return timeline
    except HTTPException:
        raise
    except Exception as e:
        import traceback

        error_details = traceback.format_exc()
        print(f"Error getting timeline for position {position_id}: {e}")
        print(f"Traceback: {error_details}")
        # Return empty list instead of 500 to prevent UI breakage
        # The error is logged for debugging
        return []


@router.get("/events")
def get_position_events_cockpit(
    tenant_id: str,
    portfolio_id: str,
    position_id: str,
    limit: int = Query(500, description="Maximum number of events to return"),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
) -> Dict[str, Any]:
    """
    Get events for position cockpit (from PositionEvaluationTimeline).

    Returns timeline events with full details for the cockpit view.
    """
    try:
        if not hasattr(container, "evaluation_timeline"):
            raise HTTPException(status_code=501, detail="Timeline repository not available")

        # Get baseline for delta calculations
        baseline = None
        if hasattr(container, "position_baseline"):
            baseline = container.position_baseline.get_latest(position_id)

        # Get timeline events
        timeline = container.evaluation_timeline.list_by_position(
            tenant_id=tenant_id,
            portfolio_id=portfolio_id,
            position_id=position_id,
            mode="LIVE",
            limit=limit,
        )

        # Enrich timeline events with baseline deltas
        enriched_timeline = []
        for row in timeline:
            enriched_row = dict(row)

            # Calculate position vs baseline and stock vs baseline deltas if baseline exists
            if baseline:
                baseline_total_value = baseline.get("baseline_total_value", 0.0)
                baseline_stock_value = baseline.get("baseline_stock_value", 0.0)

                # Get position state after from timeline row
                total_value_after = row.get("position_total_value_after")
                stock_value_after = row.get("position_stock_value_after")

                if total_value_after is not None and baseline_total_value > 0:
                    position_delta_pct = (
                        (total_value_after - baseline_total_value) / baseline_total_value
                    ) * 100
                    enriched_row["position_delta_vs_baseline_pct"] = position_delta_pct
                else:
                    enriched_row["position_delta_vs_baseline_pct"] = None

                if stock_value_after is not None and baseline_stock_value > 0:
                    stock_delta_pct = (
                        (stock_value_after - baseline_stock_value) / baseline_stock_value
                    ) * 100
                    enriched_row["stock_delta_vs_baseline_pct"] = stock_delta_pct
                else:
                    enriched_row["stock_delta_vs_baseline_pct"] = None
            else:
                enriched_row["position_delta_vs_baseline_pct"] = None
                enriched_row["stock_delta_vs_baseline_pct"] = None

            enriched_timeline.append(enriched_row)

        # Filter by event type if provided
        if event_type:
            enriched_timeline = [
                row for row in enriched_timeline if row.get("evaluation_type") == event_type
            ]

        return {
            "position_id": position_id,
            "total_count": len(enriched_timeline),
            "events": enriched_timeline,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting events: {str(e)}")


class PositionConfigRequest(BaseModel):
    """Request model for updating position configuration."""

    trigger_threshold_up_pct: Optional[float] = None
    trigger_threshold_down_pct: Optional[float] = None
    min_stock_pct: Optional[float] = None
    max_stock_pct: Optional[float] = None
    max_trade_pct_of_position: Optional[float] = None
    commission_rate: Optional[float] = None


@router.get("/config")
def get_position_config(
    tenant_id: str,
    portfolio_id: str,
    position_id: str,
    portfolio_service: PortfolioService = Depends(get_portfolio_service),
) -> Dict[str, Any]:
    """
    Get position-specific configuration.

    Returns position config if set, otherwise falls back to portfolio config.
    """
    try:
        # Get position to verify it exists
        positions = portfolio_service.get_portfolio_positions(
            tenant_id=tenant_id, portfolio_id=portfolio_id
        )
        position = next((p for p in positions if p.id == position_id), None)
        if not position:
            raise HTTPException(status_code=404, detail="Position not found")

        # Try to get position-specific config from ConfigRepo
        config_repo = container.config
        trigger_config = config_repo.get_trigger_config(position_id)
        guardrail_config = config_repo.get_guardrail_config(position_id)

        # Get portfolio config as fallback
        portfolio_config = portfolio_service.get_portfolio_config(
            tenant_id=tenant_id, portfolio_id=portfolio_id
        )

        # Return position config if exists, otherwise portfolio config
        # TriggerConfig stores percentages as Decimal (e.g., 3.0 for 3%)
        # PortfolioConfig stores as float (e.g., 3.0 for 3%)
        return {
            "trigger_threshold_up_pct": (
                float(trigger_config.up_threshold_pct)
                if trigger_config
                else (portfolio_config.trigger_up_pct if portfolio_config else 3.0)
            ),
            "trigger_threshold_down_pct": (
                float(trigger_config.down_threshold_pct)
                if trigger_config
                else (portfolio_config.trigger_down_pct if portfolio_config else -3.0)
            ),
            # GuardrailConfig stores as decimal (0.25 for 25%), convert to percentage for frontend
            "min_stock_pct": (
                float(guardrail_config.min_stock_pct) * 100
                if guardrail_config
                else (portfolio_config.min_stock_pct if portfolio_config else 25.0)
            ),
            "max_stock_pct": (
                float(guardrail_config.max_stock_pct) * 100
                if guardrail_config
                else (portfolio_config.max_stock_pct if portfolio_config else 75.0)
            ),
            "max_trade_pct_of_position": (
                float(guardrail_config.max_trade_pct_of_position) * 100
                if guardrail_config and guardrail_config.max_trade_pct_of_position
                else (
                    portfolio_config.max_trade_pct_of_position
                    if portfolio_config and portfolio_config.max_trade_pct_of_position
                    else 50.0
                )
            ),
            "commission_rate": (
                config_repo.get_commission_rate(asset_id=position.asset_symbol)
                if position
                else (portfolio_config.commission_rate_pct if portfolio_config else 0.1)
            ),
            "is_position_specific": trigger_config is not None or guardrail_config is not None,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting position config: {str(e)}")


@router.put("/config")
def update_position_config(
    tenant_id: str,
    portfolio_id: str,
    position_id: str,
    request: PositionConfigRequest,
    portfolio_service: PortfolioService = Depends(get_portfolio_service),
) -> Dict[str, Any]:
    """
    Update position-specific configuration.

    This allows each position (cell) to have its own strategy settings,
    independent of the portfolio-level config.
    """
    try:
        # Get position to verify it exists
        positions = portfolio_service.get_portfolio_positions(
            tenant_id=tenant_id, portfolio_id=portfolio_id
        )
        position = next((p for p in positions if p.id == position_id), None)
        if not position:
            raise HTTPException(status_code=404, detail="Position not found")

        config_repo = container.config

        # Get current configs (or create new ones)
        trigger_config = config_repo.get_trigger_config(position_id)
        guardrail_config = config_repo.get_guardrail_config(position_id)

        # Get portfolio config as defaults
        portfolio_config = portfolio_service.get_portfolio_config(
            tenant_id=tenant_id, portfolio_id=portfolio_id
        )

        # Update trigger config if provided
        if (
            request.trigger_threshold_up_pct is not None
            or request.trigger_threshold_down_pct is not None
        ):
            from domain.value_objects.configs import TriggerConfig
            from decimal import Decimal

            if trigger_config:
                # Update existing
                new_trigger_config = TriggerConfig(
                    up_threshold_pct=(
                        Decimal(str(request.trigger_threshold_up_pct))
                        if request.trigger_threshold_up_pct is not None
                        else trigger_config.up_threshold_pct
                    ),
                    down_threshold_pct=(
                        Decimal(str(request.trigger_threshold_down_pct))
                        if request.trigger_threshold_down_pct is not None
                        else trigger_config.down_threshold_pct
                    ),
                )
            else:
                # Create new with defaults from portfolio or system defaults
                up_pct = (
                    Decimal(str(request.trigger_threshold_up_pct))
                    if request.trigger_threshold_up_pct is not None
                    else Decimal(str(portfolio_config.trigger_up_pct if portfolio_config else 3.0))
                )
                down_pct = (
                    Decimal(str(request.trigger_threshold_down_pct))
                    if request.trigger_threshold_down_pct is not None
                    else Decimal(
                        str(portfolio_config.trigger_down_pct if portfolio_config else -3.0)
                    )
                )
                new_trigger_config = TriggerConfig(
                    up_threshold_pct=up_pct,
                    down_threshold_pct=down_pct,
                )
            config_repo.set_trigger_config(position_id, new_trigger_config)

        # Update guardrail config if provided
        if any(
            [
                request.min_stock_pct is not None,
                request.max_stock_pct is not None,
                request.max_trade_pct_of_position is not None,
            ]
        ):
            from domain.value_objects.configs import GuardrailConfig
            from decimal import Decimal

            if guardrail_config:
                # Update existing
                new_guardrail_config = GuardrailConfig(
                    min_stock_pct=(
                        Decimal(str(request.min_stock_pct / 100))
                        if request.min_stock_pct is not None
                        else guardrail_config.min_stock_pct
                    ),
                    max_stock_pct=(
                        Decimal(str(request.max_stock_pct / 100))
                        if request.max_stock_pct is not None
                        else guardrail_config.max_stock_pct
                    ),
                    max_trade_pct_of_position=(
                        Decimal(str(request.max_trade_pct_of_position / 100))
                        if request.max_trade_pct_of_position is not None
                        else guardrail_config.max_trade_pct_of_position
                    ),
                    max_orders_per_day=guardrail_config.max_orders_per_day,
                )
            else:
                # Create new with defaults from portfolio or system defaults
                # GuardrailConfig stores as decimal (0.25 for 25%), but frontend sends as percentage (25.0)
                new_guardrail_config = GuardrailConfig(
                    min_stock_pct=(
                        Decimal(str(request.min_stock_pct / 100))
                        if request.min_stock_pct is not None
                        else Decimal(
                            str(
                                (portfolio_config.min_stock_pct if portfolio_config else 25.0) / 100
                            )
                        )
                    ),
                    max_stock_pct=(
                        Decimal(str(request.max_stock_pct / 100))
                        if request.max_stock_pct is not None
                        else Decimal(
                            str(
                                (portfolio_config.max_stock_pct if portfolio_config else 75.0) / 100
                            )
                        )
                    ),
                    max_trade_pct_of_position=(
                        Decimal(str(request.max_trade_pct_of_position / 100))
                        if request.max_trade_pct_of_position is not None
                        else Decimal(
                            str(
                                (
                                    portfolio_config.max_trade_pct_of_position
                                    if portfolio_config
                                    else 50.0
                                )
                                / 100
                            )
                        )
                    ),
                    max_orders_per_day=None,
                )
            config_repo.set_guardrail_config(position_id, new_guardrail_config)

        # Update commission rate if provided
        if request.commission_rate is not None:
            from domain.ports.config_repo import ConfigScope

            config_repo.set_commission_rate(
                rate=request.commission_rate / 100,  # Convert from percentage to decimal
                scope=ConfigScope.TENANT_ASSET,
                tenant_id=tenant_id,
                asset_id=position.asset_symbol,
            )

        return {
            "message": "Position configuration updated successfully",
            "position_id": position_id,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating position config: {str(e)}")


# =============================================================================
# Position History Endpoints (Multi-Day Trading Support)
# =============================================================================


class PositionSnapshotResponse(BaseModel):
    """Response model for position snapshot at a point in time."""

    position_id: str
    as_of: str
    total_value: Optional[float]
    stock_value: Optional[float]
    cash: Optional[float]
    qty: Optional[float]
    allocation_pct: Optional[float]
    market_price: Optional[float]
    found: bool


@router.get("/history/snapshot")
def get_position_snapshot_at(
    tenant_id: str,
    portfolio_id: str,
    position_id: str,
    as_of: Optional[str] = Query(None, description="ISO timestamp to query state at (default: now)"),
    mode: Optional[str] = Query("LIVE", description="Mode filter: LIVE or SIMULATION"),
) -> PositionSnapshotResponse:
    """
    Get position state as of a specific timestamp.

    Useful for viewing historical portfolio state during multi-day trading.
    Returns the most recent evaluation record before or at the given timestamp.
    """
    try:
        if not hasattr(container, "evaluation_timeline"):
            raise HTTPException(status_code=501, detail="Timeline repository not available")

        # Parse as_of timestamp
        if as_of:
            try:
                as_of_dt = datetime.fromisoformat(as_of.replace("Z", "+00:00"))
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid timestamp format: {as_of}")
        else:
            as_of_dt = datetime.now(timezone.utc)

        # Get snapshot
        snapshot = container.evaluation_timeline.get_position_snapshot_at(
            tenant_id=tenant_id,
            portfolio_id=portfolio_id,
            position_id=position_id,
            as_of=as_of_dt,
            mode=mode,
        )

        if not snapshot:
            return PositionSnapshotResponse(
                position_id=position_id,
                as_of=as_of_dt.isoformat(),
                total_value=None,
                stock_value=None,
                cash=None,
                qty=None,
                allocation_pct=None,
                market_price=None,
                found=False,
            )

        total_value = snapshot.get("position_total_value_before")
        stock_value = snapshot.get("position_stock_value_before")
        cash = snapshot.get("position_cash_before")
        qty = snapshot.get("position_qty_before")
        market_price = snapshot.get("market_price_raw")

        allocation_pct = None
        if total_value and stock_value and total_value > 0:
            allocation_pct = round((stock_value / total_value) * 100, 2)

        return PositionSnapshotResponse(
            position_id=position_id,
            as_of=as_of_dt.isoformat(),
            total_value=float(total_value) if total_value else None,
            stock_value=float(stock_value) if stock_value else None,
            cash=float(cash) if cash else None,
            qty=float(qty) if qty else None,
            allocation_pct=allocation_pct,
            market_price=float(market_price) if market_price else None,
            found=True,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting position snapshot: {str(e)}")


class DailySummary(BaseModel):
    """Daily summary of position performance."""

    date: str
    open_value: Optional[float]
    close_value: Optional[float]
    high_value: Optional[float]
    low_value: Optional[float]
    daily_return_pct: Optional[float]
    evaluation_count: int
    trade_count: int


class DailySummariesResponse(BaseModel):
    """Response model for daily summaries."""

    position_id: str
    days: List[DailySummary]
    total_days: int


@router.get("/history/daily", response_model=DailySummariesResponse)
def get_position_daily_summaries(
    tenant_id: str,
    portfolio_id: str,
    position_id: str,
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    mode: Optional[str] = Query("LIVE", description="Mode filter: LIVE or SIMULATION"),
) -> DailySummariesResponse:
    """
    Get daily performance summaries for a position.

    Returns aggregated daily data including open/close/high/low values,
    daily returns, and trade counts. Useful for multi-day performance tracking.
    """
    try:
        if not hasattr(container, "evaluation_timeline"):
            raise HTTPException(status_code=501, detail="Timeline repository not available")

        # Parse dates
        start_dt = None
        end_dt = None
        if start_date:
            try:
                start_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid start_date format: {start_date}")
        if end_date:
            try:
                end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid end_date format: {end_date}")

        # Get daily summaries
        summaries = container.evaluation_timeline.get_daily_summaries(
            tenant_id=tenant_id,
            portfolio_id=portfolio_id,
            position_id=position_id,
            start_date=start_dt,
            end_date=end_dt,
            mode=mode,
        )

        # Calculate daily returns
        days = []
        prev_close = None
        for summary in reversed(summaries):  # Process oldest first for return calculation
            daily_return_pct = None
            if prev_close and summary.get("open_value"):
                daily_return_pct = round(
                    ((summary["close_value"] - prev_close) / prev_close) * 100, 2
                ) if summary.get("close_value") else None

            days.append(DailySummary(
                date=summary["date"],
                open_value=summary.get("open_value"),
                close_value=summary.get("close_value"),
                high_value=summary.get("high_value"),
                low_value=summary.get("low_value"),
                daily_return_pct=daily_return_pct,
                evaluation_count=summary.get("evaluation_count", 0),
                trade_count=summary.get("trade_count", 0),
            ))

            if summary.get("close_value"):
                prev_close = summary["close_value"]

        # Reverse back to newest first
        days.reverse()

        return DailySummariesResponse(
            position_id=position_id,
            days=days,
            total_days=len(days),
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting daily summaries: {str(e)}")


class PerformancePoint(BaseModel):
    """Single point in performance time series."""

    timestamp: str
    total_value: float
    stock_value: float
    cash: float
    qty: float
    allocation_pct: float


class PerformanceSeriesResponse(BaseModel):
    """Response model for performance time series."""

    position_id: str
    interval: str
    start_time: Optional[str]
    end_time: Optional[str]
    points: List[PerformancePoint]
    total_points: int


@router.get("/history/performance", response_model=PerformanceSeriesResponse)
def get_position_performance_series(
    tenant_id: str,
    portfolio_id: str,
    position_id: str,
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    interval: str = Query("1h", description="Time interval: 1m, 5m, 15m, 30m, 1h, 4h, 1d"),
    mode: Optional[str] = Query("LIVE", description="Mode filter: LIVE or SIMULATION"),
) -> PerformanceSeriesResponse:
    """
    Get time series of position value for charting.

    Returns portfolio value at regular intervals for building performance charts.
    Useful for tracking position performance over multiple days.
    """
    try:
        if not hasattr(container, "evaluation_timeline"):
            raise HTTPException(status_code=501, detail="Timeline repository not available")

        # Validate interval
        valid_intervals = ["1m", "5m", "15m", "30m", "1h", "4h", "1d"]
        if interval not in valid_intervals:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid interval: {interval}. Must be one of: {', '.join(valid_intervals)}"
            )

        # Parse dates
        start_dt = None
        end_dt = None
        if start_date:
            try:
                start_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid start_date format: {start_date}")
        if end_date:
            try:
                end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid end_date format: {end_date}")

        # Get performance series
        series = container.evaluation_timeline.get_performance_series(
            tenant_id=tenant_id,
            portfolio_id=portfolio_id,
            position_id=position_id,
            start_date=start_dt,
            end_date=end_dt,
            mode=mode,
            interval=interval,
        )

        points = [
            PerformancePoint(
                timestamp=p["timestamp"],
                total_value=p["total_value"],
                stock_value=p["stock_value"],
                cash=p["cash"],
                qty=p["qty"],
                allocation_pct=p["allocation_pct"],
            )
            for p in series
        ]

        start_time = points[0].timestamp if points else None
        end_time = points[-1].timestamp if points else None

        return PerformanceSeriesResponse(
            position_id=position_id,
            interval=interval,
            start_time=start_time,
            end_time=end_time,
            points=points,
            total_points=len(points),
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting performance series: {str(e)}")
