#!/usr/bin/env python3
from application.use_cases.simulation_unified_uc import SimulationResult
from datetime import datetime

# Test creating a SimulationResult with trigger_analysis
try:
    result = SimulationResult(
        ticker="TEST",
        start_date=datetime.now(),
        end_date=datetime.now(),
        total_trading_days=1,
        initial_cash=10000,
        algorithm_trades=0,
        algorithm_pnl=0,
        algorithm_return_pct=0,
        algorithm_volatility=0,
        algorithm_sharpe_ratio=0,
        algorithm_max_drawdown=0,
        buy_hold_pnl=0,
        buy_hold_return_pct=0,
        buy_hold_volatility=0,
        buy_hold_sharpe_ratio=0,
        buy_hold_max_drawdown=0,
        excess_return=0,
        alpha=0,
        beta=0,
        information_ratio=0,
        trade_log=[],
        daily_returns=[],
        total_dividends_received=0,
        dividend_events=[],
        price_data=[],
        trigger_analysis=[],
    )
    print("SimulationResult created successfully with trigger_analysis")
    print(f"trigger_analysis field exists: {hasattr(result, 'trigger_analysis')}")
except Exception as e:
    print(f"Error creating SimulationResult: {e}")
    import traceback

    traceback.print_exc()
