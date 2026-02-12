#!/usr/bin/env python3
import sys
import os
from datetime import datetime

# Add the current directory to Python path
sys.path.insert(0, os.getcwd())

# Test importing SimulationResult from different locations
try:
    from application.use_cases.simulation_unified_uc import SimulationResult as UnifiedResult

    print("Unified SimulationResult imported successfully")
    print(f"Unified SimulationResult fields: {UnifiedResult.__dataclass_fields__.keys()}")
except Exception as e:
    print(f"Error importing Unified SimulationResult: {e}")

try:
    from application.use_cases.simulation_uc import SimulationResult as OldResult

    print("Old SimulationResult imported successfully")
    print(f"Old SimulationResult fields: {OldResult.__dataclass_fields__.keys()}")
except Exception as e:
    print(f"Error importing Old SimulationResult: {e}")

# Test creating both
try:
    unified_result = UnifiedResult(
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
    print("Unified SimulationResult created successfully")
except Exception as e:
    print(f"Error creating Unified SimulationResult: {e}")

try:
    old_result = OldResult(
        ticker="TEST",
        start_date=datetime.now(),
        end_date=datetime.now(),
        total_trading_days=1,
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
    )
    print("Old SimulationResult created successfully")
except Exception as e:
    print(f"Error creating Old SimulationResult: {e}")
