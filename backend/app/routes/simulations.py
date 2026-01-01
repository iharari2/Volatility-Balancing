# =========================
# backend/app/routes/simulations.py
# =========================

from typing import Optional
from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import StreamingResponse
from datetime import datetime
from uuid import UUID

from app.di import container
from application.services.excel_export_service import ExcelExportService
from application.services.verbose_timeline_service import VerboseTimelineService

router = APIRouter(prefix="/v1/simulations", tags=["simulations"])


# Dependency injection for Excel export service
def get_excel_export_service() -> ExcelExportService:
    """Get Excel export service instance."""
    return ExcelExportService()


# Dependency injection for verbose timeline service
def get_verbose_timeline_service() -> VerboseTimelineService:
    """Get verbose timeline service instance."""
    return VerboseTimelineService()


@router.get("/")
def list_simulations(
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of simulations to return"),
    offset: int = Query(0, ge=0, description="Number of simulations to skip"),
    ticker: Optional[str] = Query(None, description="Filter by ticker symbol"),
) -> dict:
    """List all available simulations."""
    try:
        if ticker:
            simulations = container.simulation.get_simulations_by_ticker(ticker, limit)
        else:
            simulations = container.simulation.list_simulations(limit, offset)

        return {
            "simulations": [
                {
                    "id": str(sim.id),
                    "ticker": sim.ticker,
                    "start_date": sim.start_date,
                    "end_date": sim.end_date,
                    "created_at": sim.created_at.isoformat(),
                    "metrics": {
                        "algorithm_return_pct": sim.metrics.get("algorithm_return_pct", 0),
                        "buy_hold_return_pct": sim.metrics.get("buy_hold_return_pct", 0),
                        "excess_return": sim.metrics.get("excess_return", 0),
                        "algorithm_trades": sim.metrics.get("algorithm_trades", 0),
                    },
                }
                for sim in simulations
            ],
            "total": len(simulations),
            "limit": limit,
            "offset": offset,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing simulations: {str(e)}")


@router.get("/{simulation_id}")
def get_simulation(simulation_id: str) -> dict:
    """Get a specific simulation by ID."""
    try:
        simulation = container.simulation.get_simulation_result(UUID(simulation_id))
        if not simulation:
            raise HTTPException(status_code=404, detail="Simulation not found")

        return {
            "id": str(simulation.id),
            "ticker": simulation.ticker,
            "start_date": simulation.start_date,
            "end_date": simulation.end_date,
            "created_at": simulation.created_at.isoformat(),
            "parameters": simulation.parameters,
            "metrics": simulation.metrics,
            "raw_data": simulation.raw_data,
        }
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid simulation ID format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting simulation: {str(e)}")


@router.get("/{simulation_id}/export")
async def export_simulation(
    simulation_id: str,
    format: str = Query("xlsx", description="Export format (xlsx, csv)"),
    excel_service: ExcelExportService = Depends(get_excel_export_service),
):
    """Export a specific simulation to Excel format."""
    try:
        # Get simulation from repository
        simulation = container.simulation.get_simulation_result(UUID(simulation_id))
        if not simulation:
            raise HTTPException(status_code=404, detail="Simulation not found")

        # Convert domain entity to use case format for Excel export
        from application.use_cases.simulation_unified_uc import SimulationResult

        # Extract data from raw_data
        raw_data = simulation.raw_data or {}

        result = SimulationResult(
            ticker=simulation.ticker,
            start_date=datetime.fromisoformat(simulation.start_date.replace("Z", "+00:00")),
            end_date=datetime.fromisoformat(simulation.end_date.replace("Z", "+00:00")),
            total_trading_days=simulation.total_trading_days,
            initial_cash=simulation.initial_cash,
            algorithm_trades=simulation.algorithm_trades,
            algorithm_pnl=simulation.algorithm_pnl,
            algorithm_return_pct=simulation.algorithm_return_pct,
            algorithm_volatility=simulation.algorithm_volatility,
            algorithm_sharpe_ratio=simulation.algorithm_sharpe_ratio,
            algorithm_max_drawdown=simulation.algorithm_max_drawdown,
            buy_hold_pnl=simulation.buy_hold_pnl,
            buy_hold_return_pct=simulation.buy_hold_return_pct,
            buy_hold_volatility=simulation.buy_hold_volatility,
            buy_hold_sharpe_ratio=simulation.buy_hold_sharpe_ratio,
            buy_hold_max_drawdown=simulation.buy_hold_max_drawdown,
            excess_return=simulation.excess_return,
            alpha=simulation.alpha,
            beta=simulation.beta,
            information_ratio=simulation.information_ratio,
            trade_log=simulation.trade_log or [],
            daily_returns=simulation.daily_returns or [],
            total_dividends_received=getattr(simulation, "total_dividends_received", 0),
            dividend_events=raw_data.get("dividend_events", []),
            price_data=raw_data.get("price_data", []),
            trigger_analysis=raw_data.get("trigger_analysis", []),
            time_series_data=raw_data.get("time_series_data", []),
            debug_storage_info=raw_data.get("debug_storage_info"),
            debug_retrieval_info=raw_data.get("debug_retrieval_info"),
            debug_info=raw_data.get("debug_info", []),
            dividend_analysis=raw_data.get("dividend_analysis", {}),
        )

        # Export to Excel
        excel_data = excel_service.export_simulation_results(result, simulation.ticker)

        def generate():
            yield excel_data

        return StreamingResponse(
            generate(),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename=simulation_{simulation.ticker}_{simulation_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            },
        )

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid simulation ID format")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting simulation: {str(e)}")


@router.get("/{simulation_id}/verbose-timeline")
def get_verbose_timeline(
    simulation_id: str,
    timeline_service: VerboseTimelineService = Depends(get_verbose_timeline_service),
) -> dict:
    """Get verbose timeline view for a simulation."""
    try:
        # Access the database model directly through the repository's session
        from infrastructure.persistence.sql.models import SimulationResultModel

        # Get the session from the simulation repo
        sim_repo = container.simulation
        if not hasattr(sim_repo, "session"):
            raise HTTPException(status_code=500, detail="Cannot access database session")

        model = (
            sim_repo.session.query(SimulationResultModel)
            .filter(SimulationResultModel.id == simulation_id)
            .first()
        )

        if not model:
            raise HTTPException(status_code=404, detail="Simulation not found")

        # Extract data directly from the model
        time_series_data = model.time_series_data or []
        trade_log = model.trade_log or []
        dividend_analysis = model.dividend_analysis or {}
        trigger_analysis = model.trigger_analysis or []
        price_data = model.price_data or []

        # Log for debugging
        import logging

        logger = logging.getLogger(__name__)
        logger.info(
            f"Verbose timeline request for simulation {simulation_id}: "
            f"time_series_data={len(time_series_data)} rows, "
            f"trade_log={len(trade_log)} trades"
        )

        # Convert to dict for timeline service
        simulation_dict = {
            "time_series_data": time_series_data,
            "trade_log": trade_log,
            "dividend_analysis": dividend_analysis,
            "trigger_analysis": trigger_analysis,
            "price_data": price_data,
        }

        # Build timeline
        timeline_rows = timeline_service.build_timeline_from_simulation(simulation_dict)

        logger.info(f"Generated {len(timeline_rows)} timeline rows")

        return {
            "simulation_id": simulation_id,
            "ticker": model.ticker,
            "start_date": model.start_date.isoformat() if model.start_date else "",
            "end_date": model.end_date.isoformat() if model.end_date else "",
            "rows": timeline_rows,
            "total_rows": len(timeline_rows),
        }

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid simulation ID format")
    except HTTPException:
        raise
    except Exception as e:
        import traceback

        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error building verbose timeline: {str(e)}")


@router.delete("/{simulation_id}")
def delete_simulation(simulation_id: str) -> dict:
    """Delete a simulation by ID."""
    try:
        success = container.simulation.delete_simulation_result(UUID(simulation_id))
        if not success:
            raise HTTPException(status_code=404, detail="Simulation not found")

        return {"message": "Simulation deleted successfully"}
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid simulation ID format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting simulation: {str(e)}")
