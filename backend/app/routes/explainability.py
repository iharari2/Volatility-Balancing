# backend/app/routes/explainability.py
"""
Explainability API endpoints.

Provides endpoints for the Explainability Table feature, supporting both
live trading and simulation data sources.
"""

from typing import Optional, List
from datetime import datetime
from uuid import UUID
from io import BytesIO

from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import StreamingResponse

from app.di import container
from application.services.explainability_timeline_service import ExplainabilityTimelineService


# Create router for live position explainability
live_router = APIRouter(
    prefix="/v1/tenants/{tenant_id}/portfolios/{portfolio_id}/positions/{position_id}",
    tags=["explainability"],
)

# Create router for simulation explainability
simulation_router = APIRouter(
    prefix="/v1/simulations",
    tags=["explainability"],
)


def get_explainability_service() -> ExplainabilityTimelineService:
    """Get explainability timeline service instance."""
    return ExplainabilityTimelineService()


@live_router.get("/explainability")
def get_live_explainability(
    tenant_id: str,
    portfolio_id: str,
    position_id: str,
    start_date: Optional[str] = Query(None, description="Start date filter (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date filter (YYYY-MM-DD)"),
    action: Optional[str] = Query(None, description="Action filter (comma-separated: BUY,SELL,HOLD,SKIP)"),
    aggregation: str = Query("daily", description="Aggregation mode: 'daily' or 'all'"),
    limit: int = Query(500, ge=1, le=2000, description="Maximum number of rows to return"),
    service: ExplainabilityTimelineService = Depends(get_explainability_service),
) -> dict:
    """
    Get explainability timeline for a live position.

    Returns a unified view of how the trading algorithm behaved at each timestamp,
    with all the data needed to understand why decisions were made.

    Args:
        tenant_id: Tenant ID
        portfolio_id: Portfolio ID
        position_id: Position ID
        start_date: Optional start date filter (YYYY-MM-DD)
        end_date: Optional end date filter (YYYY-MM-DD)
        action: Optional action filter (comma-separated: BUY,SELL,HOLD,SKIP)
        aggregation: Aggregation mode ('daily' shows 1 row per day if no action, 'all' shows all rows)
        limit: Maximum number of rows to return

    Returns:
        ExplainabilityTimeline with rows and metadata
    """
    try:
        # Validate timeline repository is available
        if not hasattr(container, "evaluation_timeline"):
            raise HTTPException(status_code=501, detail="Timeline repository not available")

        # Parse date filters
        start_dt = None
        end_dt = None
        if start_date:
            try:
                start_dt = datetime.fromisoformat(start_date)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid start_date format: {start_date}")
        if end_date:
            try:
                end_dt = datetime.fromisoformat(end_date)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid end_date format: {end_date}")

        # Parse action filter
        actions_list = None
        if action:
            actions_list = [a.strip().upper() for a in action.split(",")]

        # Get position info for metadata
        position = container.positions.get(
            tenant_id=tenant_id, portfolio_id=portfolio_id, position_id=position_id
        )
        symbol = position.asset_symbol if position else None

        # Fetch timeline data from repository
        timeline_records = container.evaluation_timeline.list_by_position(
            tenant_id=tenant_id,
            portfolio_id=portfolio_id,
            position_id=position_id,
            mode="LIVE",
            limit=limit * 10,  # Fetch more to allow for filtering
        )

        # Convert to explainability rows
        rows = service.build_from_live_timeline(
            evaluation_records=timeline_records,
            position_id=position_id,
            portfolio_id=portfolio_id,
            symbol=symbol,
        )

        # Build timeline with filtering and aggregation
        timeline = service.build_timeline(
            rows=rows,
            start_date=start_dt,
            end_date=end_dt,
            actions=actions_list,
            aggregation=aggregation,
            limit=limit,
            position_id=position_id,
            portfolio_id=portfolio_id,
            symbol=symbol,
            mode="LIVE",
        )

        return timeline.to_dict()

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error getting explainability data: {str(e)}")


@live_router.get("/explainability/export")
def export_live_explainability(
    tenant_id: str,
    portfolio_id: str,
    position_id: str,
    start_date: Optional[str] = Query(None, description="Start date filter (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date filter (YYYY-MM-DD)"),
    action: Optional[str] = Query(None, description="Action filter (comma-separated: BUY,SELL,HOLD,SKIP)"),
    aggregation: str = Query("daily", description="Aggregation mode: 'daily' or 'all'"),
    service: ExplainabilityTimelineService = Depends(get_explainability_service),
):
    """
    Export explainability timeline to Excel.

    Returns an Excel file with the explainability timeline data.
    """
    try:
        # Validate timeline repository is available
        if not hasattr(container, "evaluation_timeline"):
            raise HTTPException(status_code=501, detail="Timeline repository not available")

        # Parse date filters
        start_dt = None
        end_dt = None
        if start_date:
            try:
                start_dt = datetime.fromisoformat(start_date)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid start_date format: {start_date}")
        if end_date:
            try:
                end_dt = datetime.fromisoformat(end_date)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid end_date format: {end_date}")

        # Parse action filter
        actions_list = None
        if action:
            actions_list = [a.strip().upper() for a in action.split(",")]

        # Get position info
        position = container.positions.get(
            tenant_id=tenant_id, portfolio_id=portfolio_id, position_id=position_id
        )
        symbol = position.asset_symbol if position else "unknown"

        # Fetch all timeline data
        timeline_records = container.evaluation_timeline.list_by_position(
            tenant_id=tenant_id,
            portfolio_id=portfolio_id,
            position_id=position_id,
            mode="LIVE",
            limit=10000,
        )

        # Convert to explainability rows
        rows = service.build_from_live_timeline(
            evaluation_records=timeline_records,
            position_id=position_id,
            portfolio_id=portfolio_id,
            symbol=symbol,
        )

        # Build timeline with filtering and aggregation
        timeline = service.build_timeline(
            rows=rows,
            start_date=start_dt,
            end_date=end_dt,
            actions=actions_list,
            aggregation=aggregation,
            limit=10000,
            position_id=position_id,
            portfolio_id=portfolio_id,
            symbol=symbol,
            mode="LIVE",
        )

        # Generate Excel
        excel_data = _generate_excel(timeline.rows, symbol, "LIVE")

        filename = f"explainability_{symbol}_{position_id[:8]}_{datetime.now().strftime('%Y%m%d')}.xlsx"

        return StreamingResponse(
            iter([excel_data]),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error exporting explainability data: {str(e)}")


@simulation_router.get("/{simulation_id}/explainability")
def get_simulation_explainability(
    simulation_id: str,
    start_date: Optional[str] = Query(None, description="Start date filter (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date filter (YYYY-MM-DD)"),
    action: Optional[str] = Query(None, description="Action filter (comma-separated: BUY,SELL,HOLD,SKIP)"),
    aggregation: str = Query("daily", description="Aggregation mode: 'daily' or 'all'"),
    limit: int = Query(500, ge=1, le=2000, description="Maximum number of rows to return"),
    service: ExplainabilityTimelineService = Depends(get_explainability_service),
) -> dict:
    """
    Get explainability timeline for a simulation.

    Returns a unified view of how the trading algorithm behaved at each timestamp
    during the simulation.
    """
    try:
        # Get simulation from repository
        simulation = container.simulation.get_simulation_result(UUID(simulation_id))
        if not simulation:
            raise HTTPException(status_code=404, detail="Simulation not found")

        # Parse date filters
        start_dt = None
        end_dt = None
        if start_date:
            try:
                start_dt = datetime.fromisoformat(start_date)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid start_date format: {start_date}")
        if end_date:
            try:
                end_dt = datetime.fromisoformat(end_date)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid end_date format: {end_date}")

        # Parse action filter
        actions_list = None
        if action:
            actions_list = [a.strip().upper() for a in action.split(",")]

        # Build simulation result dict
        raw_data = simulation.raw_data or {}
        simulation_result = {
            "id": str(simulation.id),
            "ticker": simulation.ticker,
            "time_series_data": raw_data.get("time_series_data", []),
            "trade_log": simulation.trade_log or [],
        }

        # Convert to explainability rows
        rows = service.build_from_simulation(simulation_result)

        # Build timeline with filtering and aggregation
        timeline = service.build_timeline(
            rows=rows,
            start_date=start_dt,
            end_date=end_dt,
            actions=actions_list,
            aggregation=aggregation,
            limit=limit,
            simulation_run_id=simulation_id,
            symbol=simulation.ticker,
            mode="SIMULATION",
        )

        return timeline.to_dict()

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid simulation ID format")
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error getting explainability data: {str(e)}")


@simulation_router.get("/{simulation_id}/explainability/export")
def export_simulation_explainability(
    simulation_id: str,
    start_date: Optional[str] = Query(None, description="Start date filter (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date filter (YYYY-MM-DD)"),
    action: Optional[str] = Query(None, description="Action filter (comma-separated: BUY,SELL,HOLD,SKIP)"),
    aggregation: str = Query("daily", description="Aggregation mode: 'daily' or 'all'"),
    service: ExplainabilityTimelineService = Depends(get_explainability_service),
):
    """
    Export simulation explainability timeline to Excel.
    """
    try:
        # Get simulation from repository
        simulation = container.simulation.get_simulation_result(UUID(simulation_id))
        if not simulation:
            raise HTTPException(status_code=404, detail="Simulation not found")

        # Parse date filters
        start_dt = None
        end_dt = None
        if start_date:
            try:
                start_dt = datetime.fromisoformat(start_date)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid start_date format: {start_date}")
        if end_date:
            try:
                end_dt = datetime.fromisoformat(end_date)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid end_date format: {end_date}")

        # Parse action filter
        actions_list = None
        if action:
            actions_list = [a.strip().upper() for a in action.split(",")]

        # Build simulation result dict
        raw_data = simulation.raw_data or {}
        simulation_result = {
            "id": str(simulation.id),
            "ticker": simulation.ticker,
            "time_series_data": raw_data.get("time_series_data", []),
            "trade_log": simulation.trade_log or [],
        }

        # Convert to explainability rows
        rows = service.build_from_simulation(simulation_result)

        # Build timeline
        timeline = service.build_timeline(
            rows=rows,
            start_date=start_dt,
            end_date=end_dt,
            actions=actions_list,
            aggregation=aggregation,
            limit=10000,
            simulation_run_id=simulation_id,
            symbol=simulation.ticker,
            mode="SIMULATION",
        )

        # Generate Excel
        excel_data = _generate_excel(timeline.rows, simulation.ticker, "SIMULATION")

        filename = f"explainability_{simulation.ticker}_{simulation_id[:8]}_{datetime.now().strftime('%Y%m%d')}.xlsx"

        return StreamingResponse(
            iter([excel_data]),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid simulation ID format")
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error exporting explainability data: {str(e)}")


def _generate_excel(rows: List, symbol: str, mode: str) -> bytes:
    """Generate Excel file from explainability rows."""
    try:
        import openpyxl
        from openpyxl.styles import Font, PatternFill, Alignment
        from openpyxl.utils import get_column_letter
    except ImportError:
        raise HTTPException(
            status_code=500,
            detail="openpyxl not installed. Run: pip install openpyxl"
        )

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Explainability"

    # Define columns
    columns = [
        ("Timestamp", "timestamp"),
        ("Date", "date"),
        ("Price", "price"),
        ("Open", "open"),
        ("High", "high"),
        ("Low", "low"),
        ("Close", "close"),
        ("Anchor", "anchor_price"),
        ("Delta %", "delta_pct"),
        ("Qty", "qty"),
        ("Stock Value", "stock_value"),
        ("Cash", "cash"),
        ("Total Value", "total_value"),
        ("Stock %", "stock_pct"),
        ("Min %", "min_stock_pct"),
        ("Max %", "max_stock_pct"),
        ("Guardrail OK", "guardrail_allowed"),
        ("Block Reason", "guardrail_block_reason"),
        ("Action", "action"),
        ("Reason", "action_reason"),
        ("Exec Price", "execution_price"),
        ("Exec Qty", "execution_qty"),
        ("Commission", "commission"),
    ]

    # Header style
    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")

    # Write headers
    for col_idx, (label, _) in enumerate(columns, 1):
        cell = ws.cell(row=1, column=col_idx, value=label)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center")

    # Row fill styles
    buy_fill = PatternFill(start_color="E2EFDA", end_color="E2EFDA", fill_type="solid")
    sell_fill = PatternFill(start_color="FCE4D6", end_color="FCE4D6", fill_type="solid")

    # Write data
    for row_idx, row in enumerate(rows, 2):
        row_dict = row.to_dict()
        action = row_dict.get("action", "")

        for col_idx, (_, key) in enumerate(columns, 1):
            value = row_dict.get(key)

            # Format values
            if value is None:
                value = ""
            elif key in ("price", "open", "high", "low", "close", "anchor_price",
                        "stock_value", "cash", "total_value", "execution_price", "commission"):
                if value:
                    value = round(float(value), 2)
            elif key in ("delta_pct", "stock_pct", "min_stock_pct", "max_stock_pct"):
                if value:
                    value = round(float(value), 2)
            elif key == "guardrail_allowed":
                value = "Yes" if value else "No"

            cell = ws.cell(row=row_idx, column=col_idx, value=value)

            # Apply row highlighting
            if action == "BUY":
                cell.fill = buy_fill
            elif action == "SELL":
                cell.fill = sell_fill

    # Auto-size columns
    for col_idx, (label, _) in enumerate(columns, 1):
        col_letter = get_column_letter(col_idx)
        max_length = len(label)
        for row in ws.iter_rows(min_row=2, min_col=col_idx, max_col=col_idx):
            for cell in row:
                if cell.value:
                    max_length = max(max_length, len(str(cell.value)))
        ws.column_dimensions[col_letter].width = min(max_length + 2, 30)

    # Freeze header row
    ws.freeze_panes = "A2"

    # Save to bytes
    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer.getvalue()
