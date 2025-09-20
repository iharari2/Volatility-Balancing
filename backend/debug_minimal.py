#!/usr/bin/env python3
"""
Minimal test to debug the SimulationResult issue
"""

# Test 1: Direct import and creation
print("=== Test 1: Direct SimulationResult creation ===")
try:
    from application.use_cases.simulation_unified_uc import SimulationResult
    from datetime import datetime

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
    print("✓ Direct SimulationResult creation works")
except Exception as e:
    print(f"✗ Direct SimulationResult creation failed: {e}")

# Test 2: Check if there are multiple SimulationResult classes
print("\n=== Test 2: Check for multiple SimulationResult classes ===")
import sys

for module_name, module in sys.modules.items():
    if hasattr(module, "SimulationResult"):
        print(f"Found SimulationResult in {module_name}")
        if hasattr(module.SimulationResult, "__dataclass_fields__"):
            fields = list(module.SimulationResult.__dataclass_fields__.keys())
            has_trigger_analysis = "trigger_analysis" in fields
            print(f"  Fields: {fields}")
            print(f"  Has trigger_analysis: {has_trigger_analysis}")

print("\n=== Test 3: Check what's actually being imported ===")
from application.use_cases import simulation_unified_uc

print(
    f"simulation_unified_uc.SimulationResult fields: {list(simulation_unified_uc.SimulationResult.__dataclass_fields__.keys())}"
)

try:
    from application.use_cases import simulation_uc

    print(
        f"simulation_uc.SimulationResult fields: {list(simulation_uc.SimulationResult.__dataclass_fields__.keys())}"
    )
except ImportError:
    print("simulation_uc not found")
