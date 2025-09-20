#!/usr/bin/env python3
"""
Unit test for trade persistence functionality.

This test verifies that:
1. Trade repositories work correctly
2. Trades can be saved and retrieved
3. The system integrates properly with the existing test framework
"""

import os
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

import pytest
from datetime import datetime, timezone
from domain.entities.trade import Trade
from domain.value_objects.types import OrderSide
from infrastructure.persistence.memory.trades_repo_mem import InMemoryTradesRepo


class TestTradePersistence:
    """Test trade persistence functionality."""

    def test_in_memory_trade_repository(self):
        """Test in-memory trade repository functionality."""
        repo = InMemoryTradesRepo()

        # Create test trades
        trade1 = Trade(
            id="trd_001",
            order_id="ord_123",
            position_id="pos_456",
            side="BUY",  # type: OrderSide
            qty=10.0,
            price=150.0,
            commission=1.5,
            executed_at=datetime.now(timezone.utc),
        )

        trade2 = Trade(
            id="trd_002",
            order_id="ord_124",
            position_id="pos_456",
            side="SELL",  # type: OrderSide
            qty=5.0,
            price=155.0,
            commission=0.75,
            executed_at=datetime.now(timezone.utc),
        )

        # Save trades
        repo.save(trade1)
        repo.save(trade2)

        # Test retrieval
        assert repo.get("trd_001") is not None
        assert repo.get("trd_002") is not None
        assert repo.get("trd_999") is None  # Non-existent trade

        # Test position queries
        position_trades = repo.list_for_position("pos_456")
        assert len(position_trades) == 2
        assert all(t.position_id == "pos_456" for t in position_trades)

        # Test order queries
        order1_trades = repo.list_for_order("ord_123")
        assert len(order1_trades) == 1
        assert order1_trades[0].id == "trd_001"

        order2_trades = repo.list_for_order("ord_124")
        assert len(order2_trades) == 1
        assert order2_trades[0].id == "trd_002"

        # Test clear
        repo.clear()
        assert len(repo.list_for_position("pos_456")) == 0
        assert repo.get("trd_001") is None

    def test_trade_entity_validation(self):
        """Test that trade entities work correctly with the persistence layer."""
        repo = InMemoryTradesRepo()

        # Test with different trade types
        trades = [
            Trade(
                id=f"trd_{i}",
                order_id=f"ord_{i}",
                position_id=f"pos_{i}",
                side="BUY" if i % 2 == 0 else "SELL",
                qty=float(i * 10),
                price=150.0 + i,
                commission=float(i * 0.1),
                executed_at=datetime.now(timezone.utc),
            )
            for i in range(1, 6)
        ]

        # Save all trades
        for trade in trades:
            repo.save(trade)

        # Verify all trades are saved
        assert len(repo.list_for_position("pos_1")) == 1
        assert len(repo.list_for_position("pos_2")) == 1
        assert len(repo.list_for_position("pos_3")) == 1
        assert len(repo.list_for_position("pos_4")) == 1
        assert len(repo.list_for_position("pos_5")) == 1

        # Verify trade data integrity
        for i in range(1, 6):
            trade = repo.get(f"trd_{i}")
            assert trade is not None
            assert trade.qty == float(i * 10)
            assert trade.price == 150.0 + i
            assert trade.commission == float(i * 0.1)
            assert trade.side == ("BUY" if i % 2 == 0 else "SELL")

    def test_trade_side_validation(self):
        """Test that trade sides are properly validated."""
        repo = InMemoryTradesRepo()

        # Valid trades
        valid_trade = Trade(
            id="trd_valid",
            order_id="ord_valid",
            position_id="pos_valid",
            side="BUY",  # type: OrderSide
            qty=10.0,
            price=150.0,
            commission=1.0,
            executed_at=datetime.now(timezone.utc),
        )

        repo.save(valid_trade)
        assert repo.get("trd_valid") is not None

        # Test that the trade side is preserved correctly
        retrieved = repo.get("trd_valid")
        assert retrieved.side == "BUY"
        assert isinstance(retrieved.side, str)

    def test_trade_persistence_integration(self):
        """Test that trade persistence integrates with the existing system."""
        # This test verifies that our trade persistence system
        # works with the existing domain model and doesn't break anything

        repo = InMemoryTradesRepo()

        # Create a realistic trade scenario
        buy_trade = Trade(
            id="trd_buy_001",
            order_id="ord_buy_123",
            position_id="pos_aapl_001",
            side="BUY",  # type: OrderSide
            qty=100.0,
            price=150.25,
            commission=1.50,
            executed_at=datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
        )

        sell_trade = Trade(
            id="trd_sell_001",
            order_id="ord_sell_124",
            position_id="pos_aapl_001",
            side="SELL",  # type: OrderSide
            qty=50.0,
            price=155.75,
            commission=0.78,
            executed_at=datetime(2024, 1, 15, 14, 45, 0, tzinfo=timezone.utc),
        )

        # Save trades
        repo.save(buy_trade)
        repo.save(sell_trade)

        # Verify position has both trades
        position_trades = repo.list_for_position("pos_aapl_001")
        assert len(position_trades) == 2

        # Verify trades are ordered by execution time (newest first)
        assert position_trades[0].id == "trd_sell_001"  # More recent
        assert position_trades[1].id == "trd_buy_001"  # Earlier

        # Verify individual order queries work
        buy_order_trades = repo.list_for_order("ord_buy_123")
        assert len(buy_order_trades) == 1
        assert buy_order_trades[0].side == "BUY"

        sell_order_trades = repo.list_for_order("ord_sell_124")
        assert len(sell_order_trades) == 1
        assert sell_order_trades[0].side == "SELL"


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])
