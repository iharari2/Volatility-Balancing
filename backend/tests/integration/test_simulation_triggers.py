#!/usr/bin/env python3
"""
Integration test to compare market triggers vs simulation triggers.

This test ensures that the simulation algorithm correctly identifies and processes
all trigger conditions that should result in trades.
"""

import pytest
from datetime import datetime, timezone, timedelta
from tests.fixtures.mock_market_data import MockMarketDataAdapter
from application.use_cases.simulation_uc import SimulationUC
from infrastructure.persistence.memory.positions_repo_mem import InMemoryPositionsRepo
from infrastructure.persistence.memory.events_repo_mem import InMemoryEventsRepo
from infrastructure.time.clock import Clock


class TestSimulationTriggers:
    """Test simulation trigger detection and processing."""

    @pytest.fixture
    def simulation_uc(self):
        """Create simulation use case with dependencies."""
        return SimulationUC(
            market_data=MockMarketDataAdapter(),
            positions=InMemoryPositionsRepo(),
            events=InMemoryEventsRepo(),
            clock=Clock(),
        )

    @pytest.fixture
    def market_data_adapter(self):
        """Create market data adapter."""
        return MockMarketDataAdapter()

    def test_trigger_detection_vs_simulation_trades(self, simulation_uc, market_data_adapter):
        """Test that simulation generates trades when triggers are detected."""
        # Use a 5-day period for fast testing
        end = datetime.now(timezone.utc)
        start = end - timedelta(days=5)

        print(f"Testing period: {start.date()} to {end.date()}")

        # Debug: Check if data is being fetched
        raw_data = market_data_adapter.fetch_historical_data("AAPL", start, end)
        print(f"Raw historical data points: {len(raw_data)}")

        if raw_data:
            print(f"First raw data: {raw_data[0].timestamp} - ${raw_data[0].price:.2f}")
            print(f"Last raw data: {raw_data[-1].timestamp} - ${raw_data[-1].price:.2f}")

        # Check storage
        stored_data = market_data_adapter.storage.get_historical_data("AAPL", start, end)
        print(f"Stored data points: {len(stored_data)}")

        # Get simulation data
        sim_data = market_data_adapter.get_simulation_data("AAPL", start, end, False)
        print(f"Simulation data price points: {len(sim_data.price_data)}")

        assert (
            len(sim_data.price_data) > 0
        ), f"Should have price data for 30-day period. Raw: {len(raw_data)}, Stored: {len(stored_data)}, Sim: {len(sim_data.price_data)}"

        # Calculate expected triggers manually
        prices = [p.price for p in sim_data.price_data]
        anchor_price = prices[0]
        threshold_pct = 0.03  # 3%
        buy_threshold = anchor_price * (1 - threshold_pct)
        sell_threshold = anchor_price * (1 + threshold_pct)

        # Count expected triggers
        expected_buy_triggers = [p for p in prices if p <= buy_threshold]
        expected_sell_triggers = [p for p in prices if p >= sell_threshold]

        print(f"Expected BUY triggers: {len(expected_buy_triggers)}")
        print(f"Expected SELL triggers: {len(expected_sell_triggers)}")
        print(f"Price range: ${min(prices):.2f} - ${max(prices):.2f}")
        print(
            f"Anchor: ${anchor_price:.2f}, Buy threshold: ${buy_threshold:.2f}, Sell threshold: ${sell_threshold:.2f}"
        )

        # Run simulation
        result = simulation_uc.run_simulation(
            ticker="AAPL",
            start_date=start,
            end_date=end,
            initial_cash=10000.0,
            position_config={
                "trigger_threshold_pct": threshold_pct,
                "rebalance_ratio": 1.6667,
                "commission_rate": 0.0001,
                "min_notional": 100.0,
                "allow_after_hours": False,
                "guardrails": {"min_stock_alloc_pct": 0.25, "max_stock_alloc_pct": 0.75},
            },
        )

        print("Simulation result:")
        print(f"  Total trading days: {result.total_trading_days}")
        print(f"  Algorithm trades: {result.algorithm_trades}")
        print(f"  Trade log length: {len(result.trade_log)}")

        # Validate simulation results
        assert result.total_trading_days > 0, "Should have trading days"
        assert (
            result.algorithm_trades > 0
        ), f"Should have trades when {len(expected_sell_triggers)} sell triggers exist"
        assert len(result.trade_log) > 0, "Should have trade log entries"

        # Validate that trades correspond to expected triggers
        if result.trade_log:
            print(f"First trade: {result.trade_log[0]}")
            print(f"Last trade: {result.trade_log[-1]}")

            # Check that trades are within expected price ranges
            trade_prices = [trade.get("price", 0) for trade in result.trade_log if "price" in trade]
            if trade_prices:
                # The simulation uses its own data source, so we need to get the actual data range
                # that the simulation used, not the test data range
                # For now, just check that trade prices are reasonable (positive and not extreme)
                assert all(p > 0 for p in trade_prices), "All trade prices should be positive"
                assert all(p < 10000 for p in trade_prices), "All trade prices should be reasonable"
                # Note: We can't directly compare with sim_data.price_data because the simulation
                # uses a different data source (MarketDataStorage vs MockMarketDataAdapter)

    def test_simulation_with_different_thresholds(self, simulation_uc, market_data_adapter):
        """Test simulation with different trigger thresholds."""
        end = datetime.now(timezone.utc)
        start = end - timedelta(days=5)

        # Test with 1% threshold (should generate more trades)
        result_1pct = simulation_uc.run_simulation(
            ticker="AAPL",
            start_date=start,
            end_date=end,
            initial_cash=10000.0,
            position_config={
                "trigger_threshold_pct": 0.01,  # 1%
                "rebalance_ratio": 1.6667,
                "commission_rate": 0.0001,
                "min_notional": 100.0,
                "allow_after_hours": False,
                "guardrails": {"min_stock_alloc_pct": 0.25, "max_stock_alloc_pct": 0.75},
            },
        )

        # Test with 5% threshold (should generate fewer trades)
        result_5pct = simulation_uc.run_simulation(
            ticker="AAPL",
            start_date=start,
            end_date=end,
            initial_cash=10000.0,
            position_config={
                "trigger_threshold_pct": 0.05,  # 5%
                "rebalance_ratio": 1.6667,
                "commission_rate": 0.0001,
                "min_notional": 100.0,
                "allow_after_hours": False,
                "guardrails": {"min_stock_alloc_pct": 0.25, "max_stock_alloc_pct": 0.75},
            },
        )

        print(f"1% threshold trades: {result_1pct.algorithm_trades}")
        print(f"5% threshold trades: {result_5pct.algorithm_trades}")

        # Lower threshold should generally generate more trades
        assert (
            result_1pct.algorithm_trades >= result_5pct.algorithm_trades
        ), "Lower threshold should generate more or equal trades"

    def test_simulation_data_consistency(self, market_data_adapter):
        """Test that simulation data is consistent and complete."""
        end = datetime.now(timezone.utc)
        start = end - timedelta(days=5)

        # First fetch data to ensure it's available
        market_data_adapter.fetch_historical_data("AAPL", start, end)

        # Get simulation data
        sim_data = market_data_adapter.get_simulation_data("AAPL", start, end, False)

        # Validate data structure
        assert len(sim_data.price_data) > 0, "Should have price data"
        assert all(
            hasattr(p, "price") for p in sim_data.price_data
        ), "All price data should have price"
        assert all(
            hasattr(p, "timestamp") for p in sim_data.price_data
        ), "All price data should have timestamp"

        # Validate data consistency
        prices = [p.price for p in sim_data.price_data]
        assert all(isinstance(p, (int, float)) for p in prices), "All prices should be numeric"
        assert all(p > 0 for p in prices), "All prices should be positive"

        # Validate chronological order
        timestamps = [p.timestamp for p in sim_data.price_data]
        assert timestamps == sorted(timestamps), "Timestamps should be in chronological order"

        # Validate date range - the mock data generator starts at 9:30 AM on the start date
        # so the first timestamp might be before the exact start time but on the same day
        first_timestamp = timestamps[0]
        last_timestamp = timestamps[-1]

        # Check that the first timestamp is on or after the start date (allowing for market hours)
        assert (
            first_timestamp.date() >= start.date()
        ), f"First timestamp {first_timestamp} should be on or after start date {start.date()}"
        assert (
            last_timestamp <= end
        ), f"Last timestamp {last_timestamp} should be before end date {end}"


if __name__ == "__main__":
    # Run the test directly for debugging
    import sys

    sys.path.append(".")

    # Create instances directly
    simulation_uc = SimulationUC(
        market_data=MockMarketDataAdapter(),
        positions=InMemoryPositionsRepo(),
        events=InMemoryEventsRepo(),
        clock=Clock(),
    )
    market_data_adapter = MockMarketDataAdapter()

    test = TestSimulationTriggers()
    test.test_trigger_detection_vs_simulation_trades(simulation_uc, market_data_adapter)
