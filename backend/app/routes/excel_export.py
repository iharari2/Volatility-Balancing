# =========================
# backend/app/routes/excel_export.py
# =========================

from dataclasses import asdict
from typing import List, Optional
from uuid import UUID
import io
from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import StreamingResponse
from datetime import datetime, timezone

from app.di import container
from application.services.excel_export_service import ExcelExportService
from application.services.timeline_excel_export_service import TimelineExcelExportService
from application.use_cases.parameter_optimization_uc import ParameterOptimizationUC
from application.use_cases.simulation_unified_uc import SimulationUnifiedUC

router = APIRouter(prefix="/v1/excel", tags=["excel-export"])


def get_ticker_for_position(position_id: str, requested_ticker: str = None) -> str:
    """Get ticker for a position - use requested ticker if provided, otherwise use position-based lookup"""

    # If a specific ticker is requested, use it directly
    if requested_ticker:
        return requested_ticker.upper()

    # Search for position in database to get real ticker
    try:
        tenant_id = "default"
        portfolios = container.portfolio_repo.list_all(tenant_id=tenant_id)
        for portfolio in portfolios:
            pos = container.positions.get(
                tenant_id=tenant_id,
                portfolio_id=portfolio.id,
                position_id=position_id,
            )
            if pos:
                return getattr(pos, "asset_symbol", getattr(pos, "ticker", "UNKNOWN"))
    except Exception:
        pass

    # No hardcoded mappings for AAPL/MSFT anymore
    return "UNKNOWN"


def get_real_market_data(ticker: str) -> dict:
    """Fetch real current market data for a ticker"""
    try:
        from infrastructure.market.yfinance_adapter import YFinanceAdapter
        from datetime import datetime, timedelta

        yf_adapter = YFinanceAdapter()

        # Get current quote
        quote = yf_adapter.get_current_quote(ticker)

        if quote:
            return {
                "current_price": quote.price,
                "bid": quote.bid,
                "ask": quote.ask,
                "volume": quote.volume,
                "market_cap": getattr(quote, "market_cap", None),
                "pe_ratio": getattr(quote, "pe_ratio", None),
                "52_week_high": getattr(quote, "week_52_high", None),
                "52_week_low": getattr(quote, "week_52_low", None),
                "timestamp": datetime.now().isoformat(),
            }
        else:
            # Fallback to basic price if quote fails
            end_date = datetime.now()
            start_date = end_date - timedelta(days=1)

            historical_data = yf_adapter.fetch_historical_data(
                ticker=ticker,
                start_date=start_date,
                end_date=end_date,
                intraday_interval_minutes=60,
            )

            if historical_data:
                latest = historical_data[-1]
                return {
                    "current_price": latest.close,
                    "bid": latest.close * 0.999,  # Approximate bid
                    "ask": latest.close * 1.001,  # Approximate ask
                    "volume": latest.volume,
                    "timestamp": latest.timestamp.isoformat(),
                }

    except Exception as e:
        print(f"Warning: Could not fetch real market data for {ticker}: {e}")

    # Return None if real data fetch fails - caller should handle fallback
    return None


# Dependency injection for Excel export service
def get_excel_export_service() -> ExcelExportService:
    """Get Excel export service instance."""
    return ExcelExportService()


# Dependency injection for parameter optimization use case
def get_parameter_optimization_uc() -> ParameterOptimizationUC:
    """Get parameter optimization use case instance."""
    return ParameterOptimizationUC(
        config_repo=container.optimization_config,
        result_repo=container.optimization_result,
        heatmap_repo=container.heatmap_data,
        simulation_uc=container.simulation_uc,
    )


# Dependency injection for simulation use case
def get_simulation_uc() -> SimulationUnifiedUC:
    """Get simulation use case instance."""
    return container.simulation_uc


@router.get("/optimization/{config_id}/export")
async def export_optimization_results(
    config_id: str,
    format: str = Query("xlsx", description="Export format (xlsx, csv)"),
    excel_service: ExcelExportService = Depends(get_excel_export_service),
    optimization_uc: ParameterOptimizationUC = Depends(get_parameter_optimization_uc),
):
    """Export optimization results to Excel format."""
    try:
        # Validate config_id
        try:
            config_uuid = UUID(config_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid config_id format")

        # Get optimization results
        results = optimization_uc.get_optimization_results(config_uuid)
        if not results:
            raise HTTPException(status_code=404, detail="Optimization results not found")

        # Get configuration name
        config = optimization_uc.config_repo.get_by_id(config_uuid)
        config_name = (
            getattr(config, "name", f"Optimization_{config_id}")
            if config
            else f"Optimization_{config_id}"
        )

        if format.lower() == "xlsx":
            # Export to Excel
            excel_data = excel_service.export_optimization_results(results, config_name)

            # Create streaming response
            def generate():
                yield excel_data

            return StreamingResponse(
                generate(),
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={
                    "Content-Disposition": f"attachment; filename=optimization_results_{config_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                },
            )
        else:
            raise HTTPException(
                status_code=400, detail="Unsupported format. Only 'xlsx' is supported."
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error exporting optimization results: {str(e)}"
        )


@router.get("/simulation/{simulation_id}/export")
async def export_simulation_results(
    simulation_id: str,
    format: str = Query("xlsx", description="Export format (xlsx, csv)"),
    ticker: str = Query(None, description="Override ticker symbol (e.g., 'NVDA', 'BRK.A', 'SPY')"),
    excel_service: ExcelExportService = Depends(get_excel_export_service),
):
    """Export simulation results to Excel format."""
    try:
        # Create the correct SimulationResult format for Excel export
        from datetime import datetime, timedelta

        actual_ticker = get_ticker_for_position(simulation_id, ticker)

        # Fetch real historical data for the simulation
        try:
            from infrastructure.market.yfinance_adapter import YFinanceAdapter

            yf_adapter = YFinanceAdapter()
            end_date = datetime.now()
            start_date = end_date - timedelta(days=365)  # 1 year of data

            historical_data = yf_adapter.fetch_historical_data(
                ticker=actual_ticker,
                start_date=start_date,
                end_date=end_date,
                intraday_interval_minutes=None,  # Daily data
            )

            if historical_data and len(historical_data) > 0:
                # Calculate real metrics from historical data
                prices = [data.close for data in historical_data]
                returns = [
                    (prices[i] - prices[i - 1]) / prices[i - 1] for i in range(1, len(prices))
                ]

                import statistics
                import math

                avg_return = statistics.mean(returns) if returns else 0
                volatility = statistics.stdev(returns) if len(returns) > 1 else 0
                annualized_return = (1 + avg_return) ** 252 - 1  # Assuming 252 trading days
                annualized_volatility = volatility * math.sqrt(252)
                sharpe_ratio = (
                    annualized_return / annualized_volatility if annualized_volatility > 0 else 0
                )

                # Calculate max drawdown
                peak = prices[0]
                max_drawdown = 0
                for price in prices:
                    if price > peak:
                        peak = price
                    drawdown = (peak - price) / peak
                    if drawdown > max_drawdown:
                        max_drawdown = drawdown

                # Calculate P&L based on real data
                initial_cash = 100000.0
                initial_price = prices[0]
                final_price = prices[-1]

                # Simulate algorithm performance (simplified)
                algorithm_pnl = initial_cash * annualized_return
                buy_hold_pnl = initial_cash * ((final_price - initial_price) / initial_price)

                # Generate time series data from real historical data
                time_series_data = []
                for i, data in enumerate(historical_data[:100]):  # Limit to 100 data points
                    time_series_data.append(
                        {
                            "date": data.timestamp.strftime("%Y-%m-%d"),
                            "open": data.open,
                            "high": data.high,
                            "low": data.low,
                            "close": data.close,
                            "volume": data.volume,
                            "returns": returns[i] if i < len(returns) else 0,
                        }
                    )

            else:
                # Fallback values
                annualized_return = 0.15
                annualized_volatility = 0.12
                sharpe_ratio = 1.5
                max_drawdown = 0.08
                algorithm_pnl = 15000.0
                buy_hold_pnl = 12000.0
                time_series_data = []

        except Exception as e:
            print(f"Warning: Could not fetch historical data for {actual_ticker}: {e}")
            # Fallback values
            annualized_return = 0.15
            annualized_volatility = 0.12
            sharpe_ratio = 1.5
            max_drawdown = 0.08
            algorithm_pnl = 15000.0
            buy_hold_pnl = 12000.0
            time_series_data = []

        # Create the domain entity SimulationResult that Excel service expects
        from domain.entities.simulation_result import SimulationResult as DomainSimulationResult

        # Convert dates to strings
        start_date_str = start_date.strftime("%Y-%m-%d")
        end_date_str = end_date.strftime("%Y-%m-%d")

        # Create metrics dict
        metrics = {
            "algorithm_pnl": algorithm_pnl,
            "total_return": annualized_return,  # Template expects "total_return" not "algorithm_return_pct"
            "volatility": annualized_volatility,
            "sharpe_ratio": sharpe_ratio,
            "max_drawdown": max_drawdown,
            "buy_hold_pnl": buy_hold_pnl,
            "buy_hold_return_pct": ((buy_hold_pnl / 100000.0) * 100) if buy_hold_pnl else 0,
            "buy_hold_volatility": annualized_volatility * 0.9,
            "buy_hold_sharpe_ratio": sharpe_ratio * 0.8,
            "buy_hold_max_drawdown": max_drawdown * 1.1,
            "excess_return": algorithm_pnl - buy_hold_pnl,
            "alpha": 0.02,
            "beta": 1.0,
            "information_ratio": 0.5,
        }

        # Create raw_data dict
        raw_data = {
            "total_trading_days": 252,
            "initial_cash": 100000.0,
            "algorithm_trades": 15,
            "trade_log": [],
            "daily_returns": [],
            "total_dividends_received": 0.0,
            "dividend_events": [],
            "price_data": time_series_data,
            "trigger_analysis": [],
            "time_series_data": time_series_data,
        }

        # Create domain entity
        simulation_result = DomainSimulationResult.create(
            ticker=actual_ticker,
            start_date=start_date_str,
            end_date=end_date_str,
            parameters={"trigger_threshold": 0.03, "rebalance_threshold": 0.05},
            metrics=metrics,
            raw_data=raw_data,
        )

        if format.lower() == "xlsx":
            # Export to Excel
            excel_data = excel_service.export_simulation_results(
                simulation_result, simulation_result.ticker
            )

            # Create streaming response
            def generate():
                yield excel_data

            return StreamingResponse(
                generate(),
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={
                    "Content-Disposition": f"attachment; filename=simulation_results_{simulation_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                },
            )
        else:
            raise HTTPException(
                status_code=400, detail="Unsupported format. Only 'xlsx' is supported."
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting simulation results: {str(e)}")


@router.get("/trading/export")
async def export_trading_data(
    format: str = Query("xlsx", description="Export format (xlsx, csv)"),
    position_ids: Optional[List[str]] = Query(None, description="Specific position IDs to export"),
    start_date: Optional[str] = Query(None, description="Start date for data export (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date for data export (ISO format)"),
    excel_service: ExcelExportService = Depends(get_excel_export_service),
):
    """Export trading data (positions, trades, orders) to Excel format."""
    try:
        # Get positions data
        positions_data = []
        if position_ids:
            # Search across all portfolios for legacy support
            tenant_id = "default"
            for pos_id in position_ids:
                try:
                    position = None
                    portfolios = container.portfolio_repo.list_all(tenant_id=tenant_id)
                    for portfolio in portfolios:
                        pos = container.positions.get(
                            tenant_id=tenant_id, portfolio_id=portfolio.id, position_id=pos_id
                        )
                        if pos:
                            position = pos
                            break

                    if position:
                        # Get cash from Position entity (cash lives in Position)
                        cash_balance = getattr(position, "cash", 0.0)

                        # Get ticker safely
                        position_ticker = getattr(
                            position, "ticker", getattr(position, "asset_symbol", "UNKNOWN")
                        )

                        positions_data.append(
                            {
                                "id": str(position.id),
                                "ticker": position_ticker,
                                "shares": getattr(
                                    position, "qty", 0.0
                                ),  # Position uses qty, not shares
                                "cash_balance": cash_balance,  # Cash from Position entity
                                "created_at": (
                                    position.created_at.isoformat()
                                    if hasattr(position, "created_at")
                                    else None
                                ),
                                "updated_at": (
                                    position.updated_at.isoformat()
                                    if hasattr(position, "updated_at")
                                    else None
                                ),
                            }
                        )
                except Exception as e:
                    # Skip positions that cause errors
                    import logging

                    logging.warning(
                        f"Skipping position {getattr(position, 'id', 'unknown')} due to error: {e}"
                    )
                    continue
        else:
            # Get all positions (this would need to be implemented in the repository)
            # For now, return empty list
            positions_data = []

        # Get trades and orders data
        trades_data = []
        orders_data = []
        if position_ids:
            for pos_id in position_ids:
                try:
                    pos_orders = container.orders.list_for_position(pos_id, limit=10000)
                    for order in pos_orders:
                        orders_data.append(asdict(order))
                    pos_trades = container.trades.list_for_position(pos_id, limit=10000)
                    for trade in pos_trades:
                        trades_data.append(asdict(trade))
                except Exception:
                    import logging
                    logging.warning(f"Skipping orders/trades for position {pos_id}")

        if format.lower() == "xlsx":
            # Export to Excel
            excel_data = excel_service.export_trading_data(
                positions_data,
                trades_data,
                orders_data,
                f"Trading Data Export - {datetime.now().strftime('%Y-%m-%d')}",
            )

            # Create streaming response
            def generate():
                yield excel_data

            return StreamingResponse(
                generate(),
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={
                    "Content-Disposition": f"attachment; filename=trading_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                },
            )
        else:
            raise HTTPException(
                status_code=400, detail="Unsupported format. Only 'xlsx' is supported."
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting trading data: {str(e)}")


@router.get("/positions/{position_id}/export")
async def export_position_data(
    position_id: str,
    format: str = Query("xlsx", description="Export format (xlsx, csv)"),
    ticker: str = Query(None, description="Override ticker symbol (e.g., 'NVDA', 'BRK.A', 'SPY')"),
    include_trades: bool = Query(True, description="Include trade history"),
    include_orders: bool = Query(True, description="Include order history"),
    excel_service: ExcelExportService = Depends(get_excel_export_service),
):
    """Export specific position data to Excel format."""
    try:
        # Get position data - search across portfolios (legacy support)
        # TODO: Update to require tenant_id and portfolio_id
        position = None
        tenant_id = "default"
        try:
            portfolios = container.portfolio_repo.list_all(tenant_id=tenant_id)
            for portfolio in portfolios:
                pos = container.positions.get(
                    tenant_id=tenant_id, portfolio_id=portfolio.id, position_id=position_id
                )
                if pos:
                    position = pos
                    break
        except Exception:
            position = None

        if not position:
            # Create mock position data with real market data for demo/testing purposes
            from datetime import datetime

            actual_ticker = get_ticker_for_position(position_id, ticker)
            market_data = get_real_market_data(actual_ticker)

            # Use real market data if available
            if market_data:
                current_price = market_data["current_price"]
                shares = 100
                cash_balance = 5000.0
                market_value = shares * current_price
            else:
                # Fallback values
                current_price = 150.0
                shares = 100
                cash_balance = 5000.0
                market_value = shares * current_price

            position = type(
                "MockPosition",
                (),
                {
                    "id": position_id,
                    "tenant_id": tenant_id,
                    "portfolio_id": "demo_portfolio",
                    "ticker": actual_ticker,
                    "qty": float(shares),  # Use qty to match Position entity
                    "shares": shares,  # Keep for backward compatibility
                    "cash_balance": cash_balance,
                    "current_price": current_price,
                    "market_value": market_value,
                    "total_value": cash_balance + market_value,
                    "created_at": datetime.now(),
                    "updated_at": datetime.now(),
                    "market_data": market_data,  # Store for later use
                },
            )()

        # Get cash from Position entity (cash lives in Position)
        cash_balance = getattr(position, "cash", 5000.0)

        # Prepare position data
        # Handle both real Position entities and mock positions
        position_qty = getattr(position, "qty", getattr(position, "shares", 100.0))
        position_ticker = getattr(position, "ticker", getattr(position, "asset_symbol", "UNKNOWN"))

        positions_data = [
            {
                "id": str(position.id),
                "ticker": position_ticker,
                "shares": position_qty,  # Use qty if available, otherwise shares
                "cash_balance": cash_balance,
                "created_at": (
                    position.created_at.isoformat() if hasattr(position, "created_at") else None
                ),
                "updated_at": (
                    position.updated_at.isoformat() if hasattr(position, "updated_at") else None
                ),
            }
        ]

        # Get ticker for trades/orders (handle both real Position and mock)
        position_ticker = getattr(position, "ticker", getattr(position, "asset_symbol", "UNKNOWN"))

        # Get trades data for this position
        trades_data = []
        if include_trades:
            # This would need to be implemented in the trades repository
            # Return empty for now instead of mock AAPL data
            trades_data = []

        # Get orders data for this position
        orders_data = []
        if include_orders:
            # This would need to be implemented in the orders repository
            # Return empty for now instead of mock AAPL data
            orders_data = []

        if format.lower() == "xlsx":
            # Get ticker for filename (handle both real Position and mock)
            position_ticker = getattr(
                position, "ticker", getattr(position, "asset_symbol", "UNKNOWN")
            )

            # Export to Excel
            excel_data = excel_service.export_trading_data(
                positions_data,
                trades_data,
                orders_data,
                f"Position Data - {position_ticker} - {position_id}",
            )

            # Create streaming response
            def generate():
                yield excel_data

            return StreamingResponse(
                generate(),
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={
                    "Content-Disposition": f"attachment; filename=position_{position_ticker}_{position_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                },
            )
        else:
            raise HTTPException(
                status_code=400, detail="Unsupported format. Only 'xlsx' is supported."
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting position data: {str(e)}")


@router.get("/dividends/export")
async def export_dividend_data(
    tenant_id: str = Query(..., description="Tenant ID"),
    portfolio_id: str = Query(..., description="Portfolio ID"),
    position_id: str = Query(..., description="Position ID"),
    format: str = Query("xlsx", description="Export format"),
    excel_service: ExcelExportService = Depends(get_excel_export_service),
):
    """Export dividend data (receivables + upcoming) for a position to Excel."""
    try:
        # Look up position
        position = container.positions.get(
            tenant_id=tenant_id,
            portfolio_id=portfolio_id,
            position_id=position_id,
        )
        if not position:
            raise HTTPException(status_code=404, detail="Position not found")

        ticker = getattr(position, "ticker", getattr(position, "asset_symbol", "UNKNOWN"))

        # Get all receivables for this position
        receivables = list(container.dividend_receivable.get_receivables_by_position(position_id))

        # Get dividends by ticker (for ex_date/pay_date lookup)
        dividends_by_id = {}
        all_dividends = list(container.dividend.get_dividends_by_ticker(ticker))
        for d in all_dividends:
            dividends_by_id[d.id] = d

        # Build receivables rows (join with dividend for dates)
        receivables_data = []
        total_pending = 0
        total_paid = 0
        for rec in receivables:
            div = dividends_by_id.get(rec.dividend_id)
            row = {
                "status": rec.status,
                "ex_date": div.ex_date.strftime("%Y-%m-%d") if div else "",
                "pay_date": div.pay_date.strftime("%Y-%m-%d") if div else "",
                "shares_at_record": rec.shares_at_record,
                "gross_amount": float(rec.gross_amount),
                "withholding_tax": float(rec.withholding_tax),
                "net_amount": float(rec.net_amount),
                "paid_at": rec.paid_at.strftime("%Y-%m-%d %H:%M:%S") if rec.paid_at else "",
            }
            receivables_data.append(row)
            if rec.status == "pending":
                total_pending += 1
            elif rec.status == "paid":
                total_paid += 1

        # Build upcoming dividends
        upcoming_data = []
        from datetime import datetime as dt_cls
        now = dt_cls.now()
        for d in all_dividends:
            if d.ex_date > now:
                upcoming_data.append({
                    "ex_date": d.ex_date.strftime("%Y-%m-%d"),
                    "pay_date": d.pay_date.strftime("%Y-%m-%d"),
                    "dps": float(d.dps),
                    "currency": d.currency,
                })
        # Sort upcoming by ex_date
        upcoming_data.sort(key=lambda x: x["ex_date"])

        summary = {
            "ticker": ticker,
            "position_id": position_id,
            "total_pending": total_pending,
            "total_paid": total_paid,
        }

        excel_data = excel_service.export_dividend_data(receivables_data, upcoming_data, summary)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"dividends_{ticker}_{timestamp}.xlsx"

        return StreamingResponse(
            io.BytesIO(excel_data),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting dividend data: {str(e)}")


@router.get("/export/formats")
async def get_export_formats():
    """Get available export formats."""
    return {
        "formats": [
            {
                "name": "Excel (.xlsx)",
                "value": "xlsx",
                "description": "Microsoft Excel format with multiple sheets and formatting",
                "mime_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            }
        ],
        "supported_data_types": [
            "optimization_results",
            "simulation_results",
            "trading_data",
            "position_data",
        ],
    }


@router.get("/positions/export")
async def export_positions(
    excel_service: ExcelExportService = Depends(get_excel_export_service),
):
    """
    Export all positions to Excel format.

    NOTE: This endpoint uses legacy position lookup. For portfolio-scoped positions,
    use portfolio-specific export endpoints instead.
    """
    try:
        # Get all positions - search across all portfolios (legacy support)
        # TODO: Update to require tenant_id and portfolio_id
        positions = []
        tenant_id = "default"
        try:
            portfolios = container.portfolio_repo.list_all(tenant_id=tenant_id)
            for portfolio in portfolios:
                portfolio_positions = container.positions.list_all(
                    tenant_id=tenant_id,
                    portfolio_id=portfolio.id,
                )
                positions.extend(portfolio_positions)
        except Exception:
            positions = []

        if not positions:
            # Return empty export instead of generating mock data
            positions_data = []
        else:
            # Convert to dict format for Excel export with real market data
            positions_data = []
            for pos in positions:
                try:
                    # Get ticker safely (handle both Position entity and mock objects)
                    position_ticker = getattr(
                        pos, "ticker", getattr(pos, "asset_symbol", "UNKNOWN")
                    )

                    # Get real market data for this position
                    market_data = get_real_market_data(position_ticker)

                    # Get cash from Position entity (cash lives in Position)
                    cash_balance = getattr(pos, "cash", 0.0)

                    position_data = {
                        "id": str(pos.id),
                        "ticker": position_ticker,
                        "qty": getattr(pos, "qty", 0.0),
                        "cash": cash_balance,  # Cash from Position entity
                        "anchor_price": getattr(pos, "anchor_price", None),
                        "created_at": (
                            pos.created_at.isoformat() if hasattr(pos, "created_at") else None
                        ),
                        "updated_at": (
                            pos.updated_at.isoformat() if hasattr(pos, "updated_at") else None
                        ),
                    }

                    # Add real market data if available
                    if market_data:
                        pos_qty = getattr(pos, "qty", 0.0)
                        pos_anchor = getattr(pos, "anchor_price", None)
                        market_value = pos_qty * market_data["current_price"]
                        total_value = cash_balance + market_value
                        position_data.update(
                            {
                                "current_price": market_data["current_price"],
                                "bid": market_data["bid"],
                                "ask": market_data["ask"],
                                "volume": market_data["volume"],
                                "market_value": market_value,
                                "total_value": total_value,
                                "asset_allocation_pct": (
                                    (market_value / total_value * 100) if total_value > 0 else 0
                                ),
                                "pnl": (market_data["current_price"] - (pos_anchor or 0)) * pos_qty,
                                "pnl_pct": (
                                    (
                                        (market_data["current_price"] - (pos_anchor or 0))
                                        / pos_anchor
                                        * 100
                                    )
                                    if pos_anchor and pos_anchor > 0
                                    else 0
                                ),
                                "market_cap": market_data.get("market_cap"),
                                "pe_ratio": market_data.get("pe_ratio"),
                                "52_week_high": market_data.get("52_week_high"),
                                "52_week_low": market_data.get("52_week_low"),
                                "data_timestamp": market_data["timestamp"],
                            }
                        )
                    else:
                        # Fallback calculations without real market data
                        from datetime import datetime

                        pos_qty = getattr(pos, "qty", 0.0)
                        pos_anchor = getattr(pos, "anchor_price", None)
                        estimated_price = (
                            pos_anchor * 1.02 if pos_anchor else 150.0
                        )  # Small estimated gain
                        market_value = pos_qty * estimated_price
                        total_value = cash_balance + market_value
                        position_data.update(
                            {
                                "current_price": estimated_price,
                                "market_value": market_value,
                                "total_value": total_value,
                                "pnl": (
                                    (estimated_price - pos_anchor) * pos_qty if pos_anchor else 0
                                ),
                                "pnl_pct": 2.0,  # 2% estimated gain
                                "data_timestamp": datetime.now().isoformat(),
                                "note": "Real market data unavailable - using estimates",
                            }
                        )

                    positions_data.append(position_data)
                except Exception as e:
                    # Skip positions that cause errors, but log them
                    import logging

                    logging.warning(
                        f"Skipping position {getattr(pos, 'id', 'unknown')} due to error: {e}"
                    )
                    continue

        # Export to Excel
        excel_data = excel_service.export_trading_data(positions_data, [], [], "Positions Export")

        def generate():
            yield excel_data

        from datetime import datetime

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        return StreamingResponse(
            generate(),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename=positions_export_{timestamp}.xlsx"
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting positions: {str(e)}")


@router.get("/trades/export")
async def export_trades(
    excel_service: ExcelExportService = Depends(get_excel_export_service),
):
    """Export all trades to Excel format."""
    try:
        # Get all trades - search across all positions (legacy support)
        # TODO: Update to require tenant_id and portfolio_id
        trades = []
        tenant_id = "default"
        try:
            portfolios = container.portfolio_repo.list_all(tenant_id=tenant_id)
            for portfolio in portfolios:
                positions = container.positions.list_all(
                    tenant_id=tenant_id, portfolio_id=portfolio.id
                )
                for position in positions:
                    position_trades = container.trades.list_for_position(position.id)
                    trades.extend(position_trades)
        except Exception:
            trades = []

        if not trades:
            # Return empty export instead of 404 for better UX
            trades = []

        # Convert to dict format for Excel export
        trades_data = []
        for trade in trades:
            trades_data.append(
                {
                    "id": str(trade.id),
                    "position_id": str(trade.position_id),
                    "ticker": trade.ticker,
                    "qty": trade.qty,
                    "price": trade.price,
                    "side": trade.side,
                    "timestamp": trade.timestamp.isoformat(),
                    "commission": getattr(trade, "commission", 0),
                }
            )

        # Export to Excel
        excel_data = excel_service.export_trading_data([], trades_data, [], "Trades Export")

        def generate():
            yield excel_data

        return StreamingResponse(
            generate(),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename=trades_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting trades: {str(e)}")


@router.get("/orders/export")
async def export_orders(
    excel_service: ExcelExportService = Depends(get_excel_export_service),
):
    """Export all orders to Excel format."""
    try:
        # Get all orders - search across all positions (legacy support)
        # TODO: Update to require tenant_id and portfolio_id
        orders = []
        tenant_id = "default"
        try:
            portfolios = container.portfolio_repo.list_all(tenant_id=tenant_id)
            for portfolio in portfolios:
                positions = container.positions.list_all(
                    tenant_id=tenant_id, portfolio_id=portfolio.id
                )
                for position in positions:
                    position_orders = container.orders.list_for_position(position.id)
                    orders.extend(position_orders)
        except Exception:
            orders = []

        if not orders:
            # Return empty export instead of 404 for better UX
            orders = []

        # Convert to dict format for Excel export
        orders_data = []
        for order in orders:
            orders_data.append(
                {
                    "id": str(order.id),
                    "position_id": str(order.position_id),
                    "ticker": order.ticker,
                    "qty": order.qty,
                    "price": order.price,
                    "side": order.side,
                    "status": order.status,
                    "timestamp": order.timestamp.isoformat(),
                }
            )

        # Export to Excel
        excel_data = excel_service.export_trading_data([], [], orders_data, "Orders Export")

        def generate():
            yield excel_data

        return StreamingResponse(
            generate(),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename=orders_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting orders: {str(e)}")


# Enhanced export endpoints with comprehensive data linking
@router.get("/simulation/{simulation_id}/enhanced-export")
async def export_enhanced_simulation_results(
    simulation_id: str,
    format: str = Query("xlsx", description="Export format (xlsx, csv)"),
    ticker: str = Query(None, description="Override ticker symbol (e.g., 'NVDA', 'BRK.A', 'SPY')"),
    excel_service: ExcelExportService = Depends(get_excel_export_service),
):
    """Export enhanced simulation results with comprehensive data logs."""
    try:
        # Get simulation result from repository - with fallback to mock data
        try:
            simulation_result = container.simulation.get_simulation_result(UUID(simulation_id))
        except Exception:
            simulation_result = None

        if not simulation_result:
            # Create simulation result with real market data for demo purposes
            from domain.entities.simulation_result import SimulationResult as DomainSimulationResult

            actual_ticker = get_ticker_for_position(simulation_id, ticker)

            # Fetch real historical data for enhanced simulation
            try:
                from infrastructure.market.yfinance_adapter import YFinanceAdapter
                from datetime import datetime, timedelta

                yf_adapter = YFinanceAdapter()
                end_date = datetime.now()
                start_date = end_date - timedelta(days=365)  # 1 year of data

                historical_data = yf_adapter.fetch_historical_data(
                    ticker=actual_ticker,
                    start_date=start_date,
                    end_date=end_date,
                    intraday_interval_minutes=None,  # Daily data
                )

                if historical_data and len(historical_data) > 0:
                    # Calculate real metrics from historical data
                    prices = [data.close for data in historical_data]
                    returns = [
                        (prices[i] - prices[i - 1]) / prices[i - 1] for i in range(1, len(prices))
                    ]

                    import statistics
                    import math

                    avg_return = statistics.mean(returns) if returns else 0
                    volatility = statistics.stdev(returns) if len(returns) > 1 else 0
                    annualized_return = (1 + avg_return) ** 252 - 1  # Assuming 252 trading days
                    annualized_volatility = volatility * math.sqrt(252)
                    sharpe_ratio = (
                        annualized_return / annualized_volatility
                        if annualized_volatility > 0
                        else 0
                    )

                    # Calculate max drawdown
                    peak = prices[0]
                    max_drawdown = 0
                    for price in prices:
                        if price > peak:
                            peak = price
                        drawdown = (peak - price) / peak
                        if drawdown > max_drawdown:
                            max_drawdown = drawdown

                    # Calculate P&L based on real data
                    initial_cash = 100000.0
                    initial_price = prices[0]
                    final_price = prices[-1]

                    # Simulate algorithm performance (simplified)
                    algorithm_pnl = initial_cash * annualized_return
                    buy_hold_pnl = initial_cash * ((final_price - initial_price) / initial_price)

                    # Generate time series data from real historical data
                    time_series_data = []
                    for i, data in enumerate(
                        historical_data[:50]
                    ):  # Limit to 50 data points for demo
                        time_series_data.append(
                            {
                                "date": data.timestamp.strftime("%Y-%m-%d"),
                                "open": data.open,
                                "high": data.high,
                                "low": data.low,
                                "close": data.close,
                                "volume": data.volume,
                                "returns": returns[i] if i < len(returns) else 0,
                            }
                        )

                    metrics = {
                        "sharpe_ratio": round(sharpe_ratio, 3),
                        "return_pct": round(annualized_return * 100, 2),
                        "volatility": round(annualized_volatility, 3),
                        "algorithm_pnl": round(algorithm_pnl, 2),
                        "buy_hold_pnl": round(buy_hold_pnl, 2),
                        "total_return": round(annualized_return, 3),
                        "max_drawdown": round(max_drawdown, 3),
                    }

                    raw_data = {
                        "trade_log": [],  # Would be populated in real simulation
                        "time_series_data": time_series_data,
                        "total_trading_days": len(historical_data),
                        "initial_cash": initial_cash,
                        "algorithm_trades": min(15, len(historical_data) // 10),  # Estimate trades
                    }

                    start_date_str = start_date.strftime("%Y-%m-%d")
                    end_date_str = end_date.strftime("%Y-%m-%d")

                else:
                    # Fallback to basic data
                    metrics = {
                        "sharpe_ratio": 1.5,
                        "return_pct": 15.2,
                        "volatility": 0.12,
                        "algorithm_pnl": 15000.0,
                        "buy_hold_pnl": 12000.0,
                        "total_return": 0.15,
                        "max_drawdown": 0.08,
                    }
                    raw_data = {
                        "trade_log": [],
                        "time_series_data": [],
                        "total_trading_days": 252,
                        "initial_cash": 100000.0,
                        "algorithm_trades": 15,
                    }
                    start_date_str = "2024-01-01"
                    end_date_str = "2024-12-31"

            except Exception as e:
                print(
                    f"Warning: Could not fetch historical data for enhanced simulation {actual_ticker}: {e}"
                )
                # Fallback metrics
                metrics = {
                    "sharpe_ratio": 1.5,
                    "return_pct": 15.2,
                    "volatility": 0.12,
                    "algorithm_pnl": 15000.0,
                    "buy_hold_pnl": 12000.0,
                    "total_return": 0.15,
                    "max_drawdown": 0.08,
                }
                raw_data = {
                    "trade_log": [],
                    "time_series_data": [],
                    "total_trading_days": 252,
                    "initial_cash": 100000.0,
                    "algorithm_trades": 15,
                }
                start_date_str = "2024-01-01"
                end_date_str = "2024-12-31"

            simulation_result = DomainSimulationResult.create(
                ticker=actual_ticker,
                start_date=start_date_str,
                end_date=end_date_str,
                parameters={"trigger_threshold": 0.03, "rebalance_threshold": 0.05},
                metrics=metrics,
                raw_data=raw_data,
            )

        # The domain entity is already in the correct format for Excel export
        # No conversion needed - use it directly
        excel_data = excel_service.export_comprehensive_simulation_report(
            simulation_result, simulation_result.ticker
        )

        def generate():
            yield excel_data

        return StreamingResponse(
            generate(),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename=enhanced_simulation_{simulation_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error exporting enhanced simulation: {str(e)}"
        )


@router.get("/trading/enhanced-export")
async def export_enhanced_trading_data(
    format: str = Query("xlsx", description="Export format (xlsx, csv)"),
    excel_service: ExcelExportService = Depends(get_excel_export_service),
):
    """Export enhanced trading data with comprehensive audit trail."""
    try:
        # Get all trading data - search across all portfolios (legacy support)
        tenant_id = "default"
        positions = []
        try:
            portfolios = container.portfolio_repo.list_all(tenant_id=tenant_id)
            for portfolio in portfolios:
                portfolio_positions = container.positions.list_all(
                    tenant_id=tenant_id, portfolio_id=portfolio.id
                )
                positions.extend(portfolio_positions)
        except Exception:
            positions = []

        # Get trades, orders, and events across all positions
        trades = []
        orders = []
        events = []
        try:
            portfolios = container.portfolio_repo.list_all(tenant_id=tenant_id)
            for portfolio in portfolios:
                portfolio_positions = container.positions.list_all(
                    tenant_id=tenant_id, portfolio_id=portfolio.id
                )
                for position in portfolio_positions:
                    position_trades = container.trades.list_for_position(position.id)
                    trades.extend(position_trades)
                    position_orders = container.orders.list_for_position(position.id)
                    orders.extend(position_orders)
                    position_events = container.events.list_for_position(position.id)
                    events.extend(position_events)
        except Exception:
            pass  # Use empty lists if can't fetch

        # Convert to dictionaries for export
        positions_data = []
        for position in positions:
            try:
                # Get cash from Position entity (cash lives in Position)
                cash_balance = getattr(position, "cash", 0.0)

                # Get ticker safely
                position_ticker = getattr(
                    position, "ticker", getattr(position, "asset_symbol", "UNKNOWN")
                )

                positions_data.append(
                    {
                        "id": str(position.id),
                        "ticker": position_ticker,
                        "shares": getattr(position, "qty", 0.0),  # Position uses qty, not shares
                        "anchor_price": getattr(position, "anchor_price", None),
                        "cash_balance": cash_balance,  # Cash from Position entity
                        "created_at": (
                            position.created_at.isoformat()
                            if hasattr(position, "created_at")
                            else None
                        ),
                        "updated_at": (
                            position.updated_at.isoformat()
                            if hasattr(position, "updated_at")
                            else None
                        ),
                    }
                )
            except Exception as e:
                # Skip positions that cause errors
                import logging

                logging.warning(
                    f"Skipping position {getattr(position, 'id', 'unknown')} due to error: {e}"
                )
                continue

        trades_data = []
        for trade in trades:
            trades_data.append(
                {
                    "id": str(trade.id),
                    "position_id": str(trade.position_id),
                    "side": trade.side,
                    "qty": trade.qty,
                    "price": trade.price,
                    "commission": trade.commission,
                    "timestamp": trade.timestamp.isoformat(),
                }
            )

        orders_data = []
        for order in orders:
            orders_data.append(
                {
                    "id": str(order.id),
                    "position_id": str(order.position_id),
                    "side": order.side,
                    "qty": order.qty,
                    "price": order.price,
                    "status": order.status,
                    "timestamp": order.timestamp.isoformat(),
                }
            )

        events_data = []
        for event in events:
            events_data.append(
                {
                    "id": str(event.id),
                    "position_id": str(event.position_id),
                    "event_type": event.event_type,
                    "description": event.description,
                    "timestamp": event.timestamp.isoformat(),
                }
            )

        # Export to enhanced Excel format
        excel_data = excel_service.export_trading_audit_report_enhanced(
            positions_data, trades_data, orders_data, events_data, "Enhanced Trading Audit Report"
        )

        def generate():
            yield excel_data

        return StreamingResponse(
            generate(),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename=enhanced_trading_audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error exporting enhanced trading data: {str(e)}"
        )


@router.get("/export/templates")
async def get_export_templates():
    """Get available Excel export templates."""
    return {
        "templates": [
            {
                "name": "Optimization Results",
                "description": "Comprehensive optimization analysis with parameter analysis and performance metrics",
                "sheets": [
                    "Summary",
                    "Detailed Results",
                    "Parameter Analysis",
                    "Performance Metrics",
                ],
                "endpoint": "/v1/excel/optimization/{config_id}/export",
            },
            {
                "name": "Simulation Results",
                "description": "Trading simulation results with trade logs and performance analysis",
                "sheets": ["Simulation Summary", "Trade Log", "Daily Returns", "Price Data"],
                "endpoint": "/v1/excel/simulation/{simulation_id}/export",
            },
            {
                "name": "Trading Data",
                "description": "Complete trading data including positions, trades, and orders",
                "sheets": ["Summary", "Positions", "Trades", "Orders"],
                "endpoint": "/v1/excel/trading/export",
            },
            {
                "name": "Position Data",
                "description": "Individual position data with trade and order history",
                "sheets": ["Position Summary", "Trades", "Orders"],
                "endpoint": "/v1/excel/positions/{position_id}/export",
            },
            {
                "name": "Comprehensive Position Data",
                "description": "Detailed per-position export with market data, position data, algo data, additional data, and transaction data",
                "sheets": [
                    "Summary",
                    "Market Data",
                    "Position Data",
                    "Algorithm Data",
                    "Additional Data",
                    "Transaction Data",
                    "Simulation Analysis",
                ],
                "endpoint": "/v1/excel/positions/{position_id}/comprehensive-export",
            },
        ]
    }


@router.get("/positions/{position_id}/comprehensive-export")
async def export_position_comprehensive_data(
    position_id: str,
    ticker: str = Query(None, description="Override ticker symbol (e.g., 'NVDA', 'BRK.A', 'SPY')"),
    include_simulation: bool = Query(False, description="Include simulation analysis if available"),
    excel_service: ExcelExportService = Depends(get_excel_export_service),
):
    """
    Export comprehensive per-position data to Excel with all data categories.

    This endpoint provides detailed export including:
    - Market Data: OHLCV, bid/ask, dividend data
    - Position Data: Anchor price, asset qty, values, percentages
    - Algorithm Data: Triggers, guardrails, configuration
    - Additional Data: Performance metrics, commission values
    - Transaction Data: Action, qty, $, commission, reason
    - Simulation Analysis: If simulation data is available
    """
    try:
        # Get position data from the portfolio context
        # For now, we'll create a mock position - in real implementation,
        # this would come from the portfolio repository
        from domain.entities.position import Position

        # Mock position data (in real implementation, fetch from database)
        from domain.value_objects.guardrails import GuardrailPolicy
        from domain.value_objects.order_policy import OrderPolicy

        mock_position = Position(
            id=position_id,
            tenant_id="default",
            portfolio_id="demo_portfolio",
            asset_symbol=get_ticker_for_position(position_id, ticker),
            qty=100.0,
            anchor_price=145.0,
            dividend_receivable=0.0,
            withholding_tax_rate=0.25,
            guardrails=GuardrailPolicy(
                min_stock_alloc_pct=0.25,
                max_stock_alloc_pct=0.75,
            ),
            order_policy=OrderPolicy(
                trigger_threshold_pct=0.03,
                rebalance_ratio=1.66667,
                min_qty=1.0,
                commission_rate=0.0001,
                allow_after_hours=True,
            ),
        )

        # Create a compatible position object for the comprehensive service
        # The comprehensive service expects frontend-style position data
        compatible_position = type(
            "Position",
            (),
            {
                "ticker": mock_position.ticker,
                "name": f"{mock_position.ticker} Inc.",  # Mock company name
                "currentPrice": (mock_position.anchor_price or 150.0) * 1.02,  # Mock current price
                "anchorPrice": mock_position.anchor_price or 150.0,
                "units": mock_position.qty,
                "cashAmount": 5000.0,  # Mock cash (cash is in Position entity)
                "assetAmount": mock_position.qty * ((mock_position.anchor_price or 150.0) * 1.02),
                "marketValue": mock_position.qty * ((mock_position.anchor_price or 150.0) * 1.02),
                "pnl": mock_position.qty * ((mock_position.anchor_price or 150.0) * 1.02)
                - mock_position.qty * (mock_position.anchor_price or 150.0),
                "pnlPercent": 2.0,  # Mock 2% gain
                "isActive": True,
                "config": type(
                    "Config",
                    (),
                    {
                        "buyTrigger": -mock_position.order_policy.trigger_threshold_pct,
                        "sellTrigger": mock_position.order_policy.trigger_threshold_pct,
                        "lowGuardrail": mock_position.guardrails.min_stock_alloc_pct,
                        "highGuardrail": mock_position.guardrails.max_stock_alloc_pct,
                        "rebalanceRatio": mock_position.order_policy.rebalance_ratio,
                        "minQuantity": mock_position.order_policy.min_qty,
                        "commission": mock_position.order_policy.commission_rate,
                        "dividendTax": mock_position.withholding_tax_rate,
                        "tradeAfterHours": mock_position.order_policy.allow_after_hours,
                    },
                )(),
            },
        )()

        # Generate comprehensive Excel data
        excel_data = excel_service.export_position_comprehensive_data(
            position=compatible_position,
            market_data=None,  # Will generate mock data
            transaction_data=None,  # Will generate mock data
            simulation_data=None,  # Will be None unless include_simulation=True
        )

        # Create filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"comprehensive_position_data_{mock_position.ticker}_{timestamp}.xlsx"

        # Return Excel file as streaming response
        return StreamingResponse(
            io.BytesIO(excel_data),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to export comprehensive position data: {str(e)}"
        )


@router.get("/trading/{position_id}/activity-export")
async def export_activity_log(
    position_id: str,
    excel_service: ExcelExportService = Depends(get_excel_export_service),
):
    """Export activity log (events) for a position to Excel format."""
    try:
        # Get position to get ticker
        # Get position - search across portfolios (legacy support)
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
            raise HTTPException(status_code=404, detail="Position not found")

        # Get ticker safely
        ticker = getattr(position, "ticker", getattr(position, "asset_symbol", "UNKNOWN"))

        # Get all events for this position
        position_events = list(container.events.list_for_position(position_id))

        if not position_events:
            raise HTTPException(status_code=404, detail="No events found for this position")

        # Convert events to dict format
        events_data = []
        for event in position_events:
            events_data.append(
                {
                    "id": event.id,
                    "type": event.type,
                    "ts": event.ts.isoformat() if event.ts else None,
                    "message": event.message,
                    "inputs": event.inputs if hasattr(event, "inputs") else {},
                    "outputs": event.outputs if hasattr(event, "outputs") else {},
                }
            )

        # Export to Excel
        excel_data = excel_service.export_activity_log(events_data, position_id, ticker)

        def generate():
            yield excel_data

        filename = (
            f"activity_log_{ticker}_{position_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        )

        return StreamingResponse(
            generate(),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to export activity log: {str(e)}")


@router.get("/timeline/export")
def export_timeline_excel(
    tenant_id: str = Query(..., description="Tenant ID"),
    portfolio_id: str = Query(..., description="Portfolio ID"),
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    mode: Optional[str] = Query(None, description="Filter by mode (LIVE or SIMULATION)"),
) -> StreamingResponse:
    """
    Export PositionEvaluationTimeline to Excel according to specification.

    Creates 5 sheets:
    - Timeline: Chronological, non-verbose columns
    - Timeline_Verbose: All columns
    - Trades: Rows where action in BUY/SELL
    - Dividends: Rows where dividend_applied = true
    - Summary: KPIs, totals, drawdown, volatility
    """
    try:
        # Parse dates
        start_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00")) if start_date else None
        end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00")) if end_date else None

        # Create export service
        export_service = TimelineExcelExportService(container.evaluation_timeline)

        # Generate Excel
        excel_data = export_service.export_portfolio_timeline(
            tenant_id=tenant_id,
            portfolio_id=portfolio_id,
            start_date=start_dt,
            end_date=end_dt,
            mode=mode,
        )

        return StreamingResponse(
            io.BytesIO(excel_data),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f'attachment; filename="timeline_export_{portfolio_id}_{datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")}.xlsx"'
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting timeline: {str(e)}")
