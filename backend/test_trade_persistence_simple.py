#!/usr/bin/env python3
"""
Simple test for trade persistence functionality.

This test verifies that:
1. Trade repositories work correctly
2. Trades can be saved and retrieved
3. SQL persistence works for trades
"""

import os
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from datetime import datetime, timezone
from domain.entities.trade import Trade
from domain.value_objects.types import OrderSide
from infrastructure.persistence.memory.trades_repo_mem import InMemoryTradesRepo
from infrastructure.persistence.sql.trades_repo_sql import SQLTradesRepo
from infrastructure.persistence.sql.models import get_engine, create_all
from sqlalchemy.orm import sessionmaker


def test_in_memory_trades():
    """Test in-memory trade repository."""
    print("🧪 Testing In-Memory Trade Repository")
    print("-" * 40)

    repo = InMemoryTradesRepo()

    # Create a test trade
    trade = Trade(
        id="trd_test_001",
        order_id="ord_123",
        position_id="pos_456",
        side="BUY",  # type: OrderSide
        qty=10.0,
        price=150.0,
        commission=1.5,
        executed_at=datetime.now(timezone.utc),
    )

    # Save trade
    repo.save(trade)
    print("✅ Trade saved to in-memory repo")

    # Retrieve trade
    retrieved = repo.get("trd_test_001")
    assert retrieved is not None, "Trade should be retrievable"
    assert retrieved.id == "trd_test_001", "Trade ID should match"
    assert retrieved.side == "BUY", "Trade side should match"
    print("✅ Trade retrieved successfully")

    # List trades for position
    position_trades = repo.list_for_position("pos_456")
    assert len(position_trades) == 1, "Should have 1 trade for position"
    print("✅ Position trades listed correctly")

    # List trades for order
    order_trades = repo.list_for_order("ord_123")
    assert len(order_trades) == 1, "Should have 1 trade for order"
    print("✅ Order trades listed correctly")

    print("✅ In-memory trade repository test passed!\n")


def test_sql_trades():
    """Test SQL trade repository."""
    print("🧪 Testing SQL Trade Repository")
    print("-" * 40)

    # Use an in-memory database for this test
    db_url = "sqlite:///:memory:"

    try:
        # Create engine and tables
        engine = get_engine(db_url)
        create_all(engine)
        print("✅ Database tables created")

        # Create repository
        Session = sessionmaker(bind=engine, expire_on_commit=False, autoflush=False)
        repo = SQLTradesRepo(Session)

        # Create a test trade
        trade = Trade(
            id="trd_sql_001",
            order_id="ord_sql_123",
            position_id="pos_sql_456",
            side="SELL",  # type: OrderSide
            qty=5.0,
            price=155.0,
            commission=0.75,
            executed_at=datetime.now(timezone.utc),
        )

        # Save trade
        repo.save(trade)
        print("✅ Trade saved to SQL repo")

        # Retrieve trade
        retrieved = repo.get("trd_sql_001")
        assert retrieved is not None, "Trade should be retrievable"
        assert retrieved.id == "trd_sql_001", "Trade ID should match"
        assert retrieved.side == "SELL", "Trade side should match"
        assert retrieved.qty == 5.0, "Trade quantity should match"
        assert retrieved.price == 155.0, "Trade price should match"
        print("✅ Trade retrieved successfully from SQL")

        # List trades for position
        position_trades = repo.list_for_position("pos_sql_456")
        assert len(position_trades) == 1, "Should have 1 trade for position"
        print("✅ Position trades listed correctly from SQL")

        # List trades for order
        order_trades = repo.list_for_order("ord_sql_123")
        assert len(order_trades) == 1, "Should have 1 trade for order"
        print("✅ Order trades listed correctly from SQL")

        print("✅ SQL trade repository test passed!\n")

    except Exception as e:
        print(f"❌ SQL trade repository test failed: {e}")
        raise
    finally:
        # Clean up test database
        try:
            import os

            if os.path.exists("test_trades_persistence.sqlite"):
                os.remove("test_trades_persistence.sqlite")
                print("🧹 Test database cleaned up")
        except:
            pass


def test_trade_persistence_integration():
    """Test that trades persist across repository instances."""
    print("🧪 Testing Trade Persistence Integration")
    print("-" * 40)

    db_url = "sqlite:///:memory:"

    try:
        # Create first repository instance
        engine = get_engine(db_url)
        create_all(engine)
        Session1 = sessionmaker(bind=engine, expire_on_commit=False, autoflush=False)
        repo1 = SQLTradesRepo(Session1)

        # Create and save trade
        trade = Trade(
            id="trd_persist_001",
            order_id="ord_persist_123",
            position_id="pos_persist_456",
            side="BUY",  # type: OrderSide
            qty=100.0,
            price=200.0,
            commission=2.0,
            executed_at=datetime.now(timezone.utc),
        )
        repo1.save(trade)
        print("✅ Trade saved with first repository instance")

        # Create second repository instance (simulating restart)
        Session2 = sessionmaker(bind=engine, expire_on_commit=False, autoflush=False)
        repo2 = SQLTradesRepo(Session2)

        # Verify trade persists
        persisted_trade = repo2.get("trd_persist_001")
        assert persisted_trade is not None, "Trade should persist across instances"
        assert persisted_trade.qty == 100.0, "Trade data should be intact"
        print("✅ Trade persisted across repository instances")

        # Verify position and order queries work
        position_trades = repo2.list_for_position("pos_persist_456")
        assert len(position_trades) == 1, "Position trades should persist"

        order_trades = repo2.list_for_order("ord_persist_123")
        assert len(order_trades) == 1, "Order trades should persist"

        print("✅ Trade persistence integration test passed!\n")

    except Exception as e:
        print(f"❌ Trade persistence integration test failed: {e}")
        raise
    finally:
        # Clean up test database
        try:
            import os

            if os.path.exists("test_persistence_integration.sqlite"):
                os.remove("test_persistence_integration.sqlite")
                print("🧹 Integration test database cleaned up")
        except:
            pass


def main():
    """Run all trade persistence tests."""
    print("🚀 Running Trade Persistence Tests")
    print("=" * 50)

    try:
        test_in_memory_trades()
        test_sql_trades()
        test_trade_persistence_integration()

        print("🎉 All trade persistence tests passed!")
        print("✅ Trade logging system is working correctly")
        return True

    except Exception as e:
        print(f"❌ Trade persistence tests failed: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
