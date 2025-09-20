#!/usr/bin/env python3
from application.use_cases.simulation_unified_uc import SimulationUnifiedUC
from app.di import container
from datetime import datetime, timedelta

# Test the simulation to see what's in algo_result
try:
    sim_uc = SimulationUnifiedUC(
        market_data=container.market_data,
        positions=container.positions,
        events=container.events,
        clock=container.clock,
        dividend_market_data=container.dividend_market_data,
    )

    end_date = datetime.now() - timedelta(days=1)
    start_date = end_date - timedelta(days=5)

    print(f"Testing simulation from {start_date.date()} to {end_date.date()}")

    result = sim_uc.run_simulation(
        ticker="ZIM",
        start_date=start_date,
        end_date=end_date,
        initial_cash=10000,
        position_config={
            "trigger_threshold_pct": 0.03,
            "rebalance_ratio": 0.5,
            "commission_rate": 0.001,
            "min_notional": 100,
            "allow_after_hours": True,
            "guardrails": {
                "min_stock_alloc_pct": 0.25,
                "max_stock_alloc_pct": 0.75,
                "max_orders_per_day": 5,
            },
        },
        include_after_hours=True,
    )

    print("Simulation completed successfully")
    print(f"Result type: {type(result)}")
    print(f"trigger_analysis field exists: {hasattr(result, 'trigger_analysis')}")
    if hasattr(result, "trigger_analysis"):
        print(f"trigger_analysis length: {len(result.trigger_analysis)}")

except Exception as e:
    print(f"Error running simulation: {e}")
    import traceback

    traceback.print_exc()
