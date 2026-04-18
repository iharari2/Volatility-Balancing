# =========================
# backend/app/routes/positions_cockpit.py
# =========================
"""
Position Cockpit API endpoints.

Provides position-centric endpoints for the Position Cockpit UI.
All endpoints are scoped to tenant_id and portfolio_id for security.
"""

from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel

from app.di import container
from app.auth import get_current_user, CurrentUser
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
    user: CurrentUser = Depends(get_current_user),
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
    user: CurrentUser = Depends(get_current_user),
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
    user: CurrentUser = Depends(get_current_user),
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
    user: CurrentUser = Depends(get_current_user),
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
    user: CurrentUser = Depends(get_current_user),
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
    allow_after_hours: Optional[bool] = None


@router.get("/config")
def get_position_config(
    tenant_id: str,
    portfolio_id: str,
    position_id: str,
    portfolio_service: PortfolioService = Depends(get_portfolio_service),
    user: CurrentUser = Depends(get_current_user),
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

        # Per-position config only
        config_repo = container.config
        trigger_config = config_repo.get_trigger_config(position_id)
        guardrail_config = config_repo.get_guardrail_config(position_id)
        order_policy_config = config_repo.get_order_policy_config(position_id)

        return {
            "trigger_threshold_up_pct": float(trigger_config.up_threshold_pct) if trigger_config else 3.0,
            "trigger_threshold_down_pct": float(trigger_config.down_threshold_pct) if trigger_config else -3.0,
            "min_stock_pct": float(guardrail_config.min_stock_pct) * 100 if guardrail_config else 25.0,
            "max_stock_pct": float(guardrail_config.max_stock_pct) * 100 if guardrail_config else 75.0,
            "max_trade_pct_of_position": (
                float(guardrail_config.max_trade_pct_of_position) * 100
                if guardrail_config and guardrail_config.max_trade_pct_of_position
                else 50.0
            ),
            "commission_rate": (
                config_repo.get_commission_rate(asset_id=position.asset_symbol) if position else 0.1
            ),
            "allow_after_hours": order_policy_config.allow_after_hours if order_policy_config else False,
            "is_position_specific": True,
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
    user: CurrentUser = Depends(get_current_user),
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
        from decimal import Decimal

        # Get current per-position configs
        trigger_config = config_repo.get_trigger_config(position_id)
        guardrail_config = config_repo.get_guardrail_config(position_id)

        # Update trigger config if provided
        if (
            request.trigger_threshold_up_pct is not None
            or request.trigger_threshold_down_pct is not None
        ):
            from domain.value_objects.configs import TriggerConfig

            new_trigger_config = TriggerConfig(
                up_threshold_pct=(
                    Decimal(str(request.trigger_threshold_up_pct))
                    if request.trigger_threshold_up_pct is not None
                    else (trigger_config.up_threshold_pct if trigger_config else Decimal("3.0"))
                ),
                down_threshold_pct=(
                    Decimal(str(request.trigger_threshold_down_pct))
                    if request.trigger_threshold_down_pct is not None
                    else (trigger_config.down_threshold_pct if trigger_config else Decimal("-3.0"))
                ),
            )
            config_repo.set_trigger_config(position_id, new_trigger_config)

        # Update guardrail config if provided
        if any([
            request.min_stock_pct is not None,
            request.max_stock_pct is not None,
            request.max_trade_pct_of_position is not None,
        ]):
            from domain.value_objects.configs import GuardrailConfig

            new_guardrail_config = GuardrailConfig(
                min_stock_pct=(
                    Decimal(str(request.min_stock_pct / 100))
                    if request.min_stock_pct is not None
                    else (guardrail_config.min_stock_pct if guardrail_config else Decimal("0.25"))
                ),
                max_stock_pct=(
                    Decimal(str(request.max_stock_pct / 100))
                    if request.max_stock_pct is not None
                    else (guardrail_config.max_stock_pct if guardrail_config else Decimal("0.75"))
                ),
                max_trade_pct_of_position=(
                    Decimal(str(request.max_trade_pct_of_position / 100))
                    if request.max_trade_pct_of_position is not None
                    else (guardrail_config.max_trade_pct_of_position if guardrail_config else Decimal("0.5"))
                ),
                max_orders_per_day=guardrail_config.max_orders_per_day if guardrail_config else None,
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

        # Update allow_after_hours if provided
        if request.allow_after_hours is not None:
            from domain.value_objects.configs import OrderPolicyConfig
            from decimal import Decimal

            order_policy_config = config_repo.get_order_policy_config(position_id)
            if order_policy_config:
                # Update existing config
                new_order_policy_config = OrderPolicyConfig(
                    min_qty=order_policy_config.min_qty,
                    min_notional=order_policy_config.min_notional,
                    lot_size=order_policy_config.lot_size,
                    qty_step=order_policy_config.qty_step,
                    action_below_min=order_policy_config.action_below_min,
                    rebalance_ratio=order_policy_config.rebalance_ratio,
                    order_sizing_strategy=order_policy_config.order_sizing_strategy,
                    allow_after_hours=request.allow_after_hours,
                    commission_rate=order_policy_config.commission_rate,
                )
            else:
                # Create new config with defaults
                new_order_policy_config = OrderPolicyConfig(
                    allow_after_hours=request.allow_after_hours,
                )
            config_repo.set_order_policy_config(position_id, new_order_policy_config)

        return {
            "message": "Position configuration updated successfully",
            "position_id": position_id,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating position config: {str(e)}")
