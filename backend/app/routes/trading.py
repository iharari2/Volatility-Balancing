# =========================
# backend/app/routes/trading.py
# =========================
"""
API routes for continuous trading service management.
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.di import container
from application.services.continuous_trading_service import (
    get_continuous_trading_service,
)

router = APIRouter(prefix="/v1", tags=["trading"])


class StartTradingRequest(BaseModel):
    polling_interval_seconds: int = 300  # Default 5 minutes


class TradingStatusResponse(BaseModel):
    position_id: str
    is_running: bool
    is_paused: bool
    start_time: Optional[str] = None
    last_check: Optional[str] = None
    total_checks: int
    total_trades: int
    total_errors: int
    last_error: Optional[str] = None


@router.post("/trading/start/{position_id}")
def start_trading(
    position_id: str, request: Optional[StartTradingRequest] = None
) -> Dict[str, Any]:
    """
    Start continuous trading for a position.

    This will begin monitoring the position at regular intervals (default 5 minutes),
    evaluating for triggers, and automatically submitting/filling orders.

    NOTE: This endpoint uses legacy position lookup. For portfolio-scoped positions,
    use the portfolio-scoped trading endpoints instead.
    """
    try:
        # Verify position exists - search across portfolios (legacy support)
        # TODO: Update to require tenant_id and portfolio_id
        position = None
        tenant_id = "default"
        portfolios = container.portfolio_repo.list_all(tenant_id=tenant_id)
        for portfolio in portfolios:
            pos = container.positions.get(
                tenant_id=tenant_id,
                portfolio_id=portfolio.id,
                position_id=position_id,
            )
            if pos:
                position = pos
                break

        if not position:
            raise HTTPException(status_code=404, detail="position_not_found")

        # Get service
        service = get_continuous_trading_service()

        # Get polling interval
        interval = 300  # Default 5 minutes
        if request and request.polling_interval_seconds:
            interval = request.polling_interval_seconds
            if interval < 60:  # Minimum 1 minute
                interval = 60
            if interval > 3600:  # Maximum 1 hour
                interval = 3600

        # Start trading
        started = service.start_trading(position_id, interval)

        if not started:
            # Check if already running
            status = service.get_status(position_id)
            if status and status.is_running:
                return {
                    "message": "Trading already running for this position",
                    "position_id": position_id,
                    "status": "running",
                }

        return {
            "message": "Continuous trading started",
            "position_id": position_id,
            "polling_interval_seconds": interval,
            "status": "started",
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error starting trading: {e}")
        import traceback

        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error starting trading: {str(e)}")


@router.post("/trading/stop/{position_id}")
def stop_trading(position_id: str) -> Dict[str, Any]:
    """Stop continuous trading for a position."""
    try:
        service = get_continuous_trading_service()
        stopped = service.stop_trading(position_id)

        if not stopped:
            raise HTTPException(status_code=404, detail="Trading not running for this position")

        return {
            "message": "Continuous trading stopped",
            "position_id": position_id,
            "status": "stopped",
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error stopping trading: {str(e)}")


@router.post("/trading/pause/{position_id}")
def pause_trading(position_id: str) -> Dict[str, Any]:
    """Pause continuous trading (can be resumed)."""
    try:
        service = get_continuous_trading_service()
        paused = service.pause_trading(position_id)

        if not paused:
            raise HTTPException(status_code=404, detail="Trading not running for this position")

        return {
            "message": "Continuous trading paused",
            "position_id": position_id,
            "status": "paused",
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error pausing trading: {str(e)}")


@router.post("/trading/resume/{position_id}")
def resume_trading(position_id: str) -> Dict[str, Any]:
    """Resume paused continuous trading."""
    try:
        service = get_continuous_trading_service()
        resumed = service.resume_trading(position_id)

        if not resumed:
            raise HTTPException(status_code=404, detail="Trading not paused for this position")

        return {
            "message": "Continuous trading resumed",
            "position_id": position_id,
            "status": "running",
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error resuming trading: {str(e)}")


@router.get("/trading/status/{position_id}", response_model=TradingStatusResponse)
def get_trading_status(position_id: str) -> TradingStatusResponse:
    """Get trading status for a position."""
    try:
        service = get_continuous_trading_service()
        status = service.get_status(position_id)

        if not status:
            raise HTTPException(status_code=404, detail="No trading status found for this position")

        return TradingStatusResponse(
            position_id=status.position_id,
            is_running=status.is_running,
            is_paused=status.is_paused,
            start_time=status.start_time.isoformat() if status.start_time else None,
            last_check=status.last_check.isoformat() if status.last_check else None,
            total_checks=status.total_checks,
            total_trades=status.total_trades,
            total_errors=status.total_errors,
            last_error=status.last_error,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting trading status: {str(e)}")


@router.get("/trading/active")
def list_active_trading() -> Dict[str, Any]:
    """List all actively trading positions."""
    try:
        service = get_continuous_trading_service()
        active = service.list_active()

        return {
            "active_positions": [
                {
                    "position_id": status.position_id,
                    "is_running": status.is_running,
                    "is_paused": status.is_paused,
                    "start_time": status.start_time.isoformat() if status.start_time else None,
                    "last_check": status.last_check.isoformat() if status.last_check else None,
                    "total_checks": status.total_checks,
                    "total_trades": status.total_trades,
                    "total_errors": status.total_errors,
                }
                for status in active.values()
            ],
            "count": len(active),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing active trading: {str(e)}")


@router.post("/trading/cycle")
def run_trading_cycle(
    position_id: Optional[str] = Query(
        None, description="Optional: run cycle for specific position only"
    ),
) -> Dict[str, Any]:
    """
    Manually trigger a trading cycle (for testing or on-demand execution).

    This is the "console" layer - it calls the same orchestrator as the worker,
    but triggered via API instead of schedule.

    If position_id is provided, runs cycle for that position only.
    Otherwise, runs cycle for all active positions.
    """
    try:
        orchestrator = container.live_trading_orchestrator

        if position_id:
            # Run cycle for specific position
            # First check why the position might not be active

            position_found = False
            portfolio_running = False
            has_anchor = False
            portfolio_id = None

            try:
                if container.portfolio_repo:
                    portfolios = container.portfolio_repo.list_all(tenant_id="default")
                    for portfolio in portfolios:
                        positions = container.positions.list_all(
                            tenant_id=portfolio.tenant_id,
                            portfolio_id=portfolio.id,
                        )
                        for pos in positions:
                            if pos.id == position_id:
                                position_found = True
                                has_anchor = pos.anchor_price is not None
                                portfolio_running = portfolio.trading_state == "RUNNING"
                                portfolio_id = portfolio.id
                                break
                        if position_found:
                            break
            except Exception:
                pass  # Ignore errors in diagnostic check

            trace_id = orchestrator.run_cycle_for_position(position_id, source="api/manual")
            if trace_id is None:
                # Provide specific error message
                if not position_found:
                    detail = f"Position {position_id} not found in any portfolio"
                elif not portfolio_running:
                    detail = f"Position {position_id} found but portfolio {portfolio_id} is not in RUNNING state. Please set portfolio trading state to RUNNING."
                elif not has_anchor:
                    detail = f"Position {position_id} found but anchor_price is not set. Please set an anchor price for this position."
                else:
                    detail = f"Position {position_id} not found or inactive"
                raise HTTPException(status_code=404, detail=detail)
            return {
                "message": "Trading cycle executed",
                "position_id": position_id,
                "trace_id": trace_id,
                "source": "api/manual",
            }
        else:
            # Run cycle for all active positions
            orchestrator.run_cycle(source="api/manual")
            return {
                "message": "Trading cycle executed for all active positions",
                "source": "api/manual",
            }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error running trading cycle: {str(e)}")


@router.get("/trading/worker/status")
def get_worker_status() -> Dict[str, Any]:
    """Get status of the background trading worker."""
    try:
        from application.services.trading_worker import get_trading_worker

        worker = get_trading_worker()
        return {
            "running": worker.is_running(),
            "enabled": worker.enabled,
            "interval_seconds": worker.interval_seconds,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting worker status: {str(e)}")


@router.get("/trading/diagnostics")
def get_trading_diagnostics() -> Dict[str, Any]:
    """
    Get comprehensive diagnostics for why trading might not be happening.

    This endpoint checks:
    1. Worker status
    2. Portfolio states
    3. Position anchor prices
    4. Timeline write status
    """
    try:
        from application.services.trading_worker import get_trading_worker

        diagnostics = {
            "worker": {},
            "portfolios": [],
            "active_positions": [],
            "issues": [],
            "recommendations": [],
        }

        # Check worker status
        try:
            worker = get_trading_worker()
            diagnostics["worker"] = {
                "running": worker.is_running(),
                "enabled": worker.enabled,
                "interval_seconds": worker.interval_seconds,
            }
            if not worker.enabled:
                diagnostics["issues"].append("Worker is DISABLED")
                diagnostics["recommendations"].append(
                    "Enable worker: POST /v1/trading/worker/enable with {\"enabled\": true}"
                )
            if not worker.is_running():
                diagnostics["issues"].append("Worker is NOT RUNNING")
        except Exception as e:
            diagnostics["worker"] = {"error": str(e)}
            diagnostics["issues"].append(f"Could not get worker status: {e}")

        # Check portfolios
        tenant_id = "default"
        portfolios = container.portfolio_repo.list_all(tenant_id=tenant_id)

        for portfolio in portfolios:
            positions = container.positions.list_all(
                tenant_id=portfolio.tenant_id,
                portfolio_id=portfolio.id,
            )
            positions_with_anchor = [p for p in positions if p.anchor_price is not None]

            portfolio_info = {
                "id": portfolio.id,
                "name": portfolio.name,
                "trading_state": portfolio.trading_state,
                "is_running": portfolio.trading_state == "RUNNING",
                "total_positions": len(positions),
                "positions_with_anchor": len(positions_with_anchor),
            }
            diagnostics["portfolios"].append(portfolio_info)

            if portfolio.trading_state != "RUNNING":
                diagnostics["issues"].append(
                    f"Portfolio '{portfolio.name}' (id={portfolio.id}) is in state '{portfolio.trading_state}', not 'RUNNING'"
                )
                diagnostics["recommendations"].append(
                    f"Set portfolio to RUNNING: PUT /v1/tenants/default/portfolios/{portfolio.id}/trading-state with {{\"state\": \"RUNNING\"}}"
                )

            if portfolio.trading_state == "RUNNING":
                for pos in positions:
                    if pos.anchor_price is not None:
                        diagnostics["active_positions"].append({
                            "position_id": pos.id,
                            "portfolio_id": portfolio.id,
                            "asset": pos.asset_symbol,
                            "anchor_price": pos.anchor_price,
                            "qty": pos.qty,
                            "cash": getattr(pos, 'cash', 0),
                        })
                    else:
                        diagnostics["issues"].append(
                            f"Position {pos.id} ({pos.asset_symbol}) has no anchor_price set"
                        )

        # Check timeline writes
        if hasattr(container, "evaluation_timeline"):
            try:
                # Try to get recent timeline entries
                for portfolio in portfolios:
                    if portfolio.trading_state == "RUNNING":
                        positions = container.positions.list_all(
                            tenant_id=portfolio.tenant_id,
                            portfolio_id=portfolio.id,
                        )
                        for pos in positions:
                            if pos.anchor_price is not None:
                                timeline = container.evaluation_timeline.list_by_position(
                                    tenant_id=portfolio.tenant_id,
                                    portfolio_id=portfolio.id,
                                    position_id=pos.id,
                                    mode="LIVE",
                                    limit=1,
                                )
                                if not timeline:
                                    diagnostics["issues"].append(
                                        f"Position {pos.id} ({pos.asset_symbol}) has NO timeline entries"
                                    )
                                    diagnostics["recommendations"].append(
                                        f"Run manual cycle: POST /v1/trading/cycle?position_id={pos.id}"
                                    )
            except Exception as e:
                diagnostics["issues"].append(f"Error checking timeline: {e}")

        # Summary
        diagnostics["summary"] = {
            "total_issues": len(diagnostics["issues"]),
            "active_position_count": len(diagnostics["active_positions"]),
            "can_trade": len(diagnostics["active_positions"]) > 0 and diagnostics["worker"].get("enabled", False),
        }

        return diagnostics
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error getting diagnostics: {str(e)}")


class WorkerEnableRequest(BaseModel):
    enabled: bool


@router.post("/trading/worker/enable")
def set_worker_enabled(request: WorkerEnableRequest) -> Dict[str, Any]:
    """Enable or disable the trading worker. State persists on the server."""
    try:
        from application.services.trading_worker import get_trading_worker

        worker = get_trading_worker()
        worker.set_enabled(request.enabled)

        return {
            "message": f"Worker {'enabled' if request.enabled else 'disabled'}",
            "enabled": worker.enabled,
            "running": worker.is_running(),
            "interval_seconds": worker.interval_seconds,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error setting worker enabled state: {str(e)}")
