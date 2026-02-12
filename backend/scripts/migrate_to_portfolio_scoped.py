#!/usr/bin/env python3
"""
Migration script to add tenant_id and portfolio_id columns to existing database tables.

This script migrates the database schema to support portfolio-scoped state.
It adds the necessary columns to existing tables and sets default values.
"""

import sys
import os
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import create_engine, text, inspect  # noqa: E402
from sqlalchemy.engine import Engine  # noqa: E402

# Import models for migration


def get_db_path() -> str:
    """Get the database path from environment or default."""
    sql_url = os.getenv("SQL_URL", "sqlite:///./vb.sqlite")
    # Extract path from sqlite:/// URL
    if sql_url.startswith("sqlite:///"):
        db_path = sql_url.replace("sqlite:///", "")
        return db_path
    return sql_url


def column_exists(engine: Engine, table_name: str, column_name: str) -> bool:
    """Check if a column exists in a table."""
    inspector = inspect(engine)
    columns = [col["name"] for col in inspector.get_columns(table_name)]
    return column_name in columns


def migrate_portfolios_table(engine: Engine) -> None:
    """Add tenant_id, type, trading_state, trading_hours_policy to portfolios table."""
    with engine.connect() as conn:
        # Check if columns already exist
        if column_exists(engine, "portfolios", "tenant_id"):
            print("[OK] portfolios.tenant_id already exists")
        else:
            print("Adding tenant_id to portfolios table...")
            conn.execute(
                text("ALTER TABLE portfolios ADD COLUMN tenant_id TEXT NOT NULL DEFAULT 'default'")
            )
            conn.execute(
                text("CREATE INDEX IF NOT EXISTS ix_portfolios_tenant_id ON portfolios(tenant_id)")
            )
            conn.commit()
            print("[OK] Added tenant_id to portfolios")

        if column_exists(engine, "portfolios", "type"):
            print("[OK] portfolios.type already exists")
        else:
            print("Adding type to portfolios table...")
            conn.execute(
                text("ALTER TABLE portfolios ADD COLUMN type TEXT NOT NULL DEFAULT 'LIVE'")
            )
            conn.commit()
            print("[OK] Added type to portfolios")

        if column_exists(engine, "portfolios", "trading_state"):
            print("[OK] portfolios.trading_state already exists")
        else:
            print("Adding trading_state to portfolios table...")
            conn.execute(
                text(
                    "ALTER TABLE portfolios ADD COLUMN trading_state TEXT NOT NULL DEFAULT 'NOT_CONFIGURED'"
                )
            )
            conn.commit()
            print("[OK] Added trading_state to portfolios")

        if column_exists(engine, "portfolios", "trading_hours_policy"):
            print("[OK] portfolios.trading_hours_policy already exists")
        else:
            print("Adding trading_hours_policy to portfolios table...")
            conn.execute(
                text(
                    "ALTER TABLE portfolios ADD COLUMN trading_hours_policy TEXT NOT NULL DEFAULT 'OPEN_ONLY'"
                )
            )
            conn.commit()
            print("[OK] Added trading_hours_policy to portfolios")


def migrate_positions_table(engine: Engine) -> None:
    """Add tenant_id, portfolio_id, rename ticker to asset_symbol, remove cash, add avg_cost."""
    with engine.connect() as conn:
        # Check if tenant_id exists
        if column_exists(engine, "positions", "tenant_id"):
            print("[OK] positions.tenant_id already exists")
        else:
            print("Adding tenant_id to positions table...")
            conn.execute(
                text("ALTER TABLE positions ADD COLUMN tenant_id TEXT NOT NULL DEFAULT 'default'")
            )
            conn.execute(
                text("CREATE INDEX IF NOT EXISTS ix_positions_tenant_id ON positions(tenant_id)")
            )
            conn.commit()
            print("[OK] Added tenant_id to positions")

        # Check if portfolio_id exists
        if column_exists(engine, "positions", "portfolio_id"):
            print("[OK] positions.portfolio_id already exists")
        else:
            print("Adding portfolio_id to positions table...")
            # First, try to get portfolio_id from existing data if possible
            # For now, set default to 'default'
            conn.execute(
                text(
                    "ALTER TABLE positions ADD COLUMN portfolio_id TEXT NOT NULL DEFAULT 'default'"
                )
            )
            conn.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS ix_positions_portfolio_id ON positions(portfolio_id)"
                )
            )
            conn.commit()
            print("[OK] Added portfolio_id to positions")

        # Check if asset_symbol exists (renamed from ticker)
        if column_exists(engine, "positions", "asset_symbol"):
            print("[OK] positions.asset_symbol already exists")
        elif column_exists(engine, "positions", "ticker"):
            print("Renaming ticker to asset_symbol in positions table...")
            # SQLite doesn't support RENAME COLUMN directly, so we need to recreate
            # For now, just add asset_symbol and copy data
            conn.execute(text("ALTER TABLE positions ADD COLUMN asset_symbol TEXT"))
            conn.execute(
                text("UPDATE positions SET asset_symbol = ticker WHERE asset_symbol IS NULL")
            )
            conn.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS ix_positions_asset_symbol ON positions(asset_symbol)"
                )
            )
            conn.commit()
            print("[OK] Added asset_symbol to positions (copied from ticker)")
        else:
            print("Adding asset_symbol to positions table...")
            conn.execute(
                text("ALTER TABLE positions ADD COLUMN asset_symbol TEXT NOT NULL DEFAULT ''")
            )
            conn.commit()
            print("[OK] Added asset_symbol to positions")

        # Check if avg_cost exists
        if column_exists(engine, "positions", "avg_cost"):
            print("[OK] positions.avg_cost already exists")
        else:
            print("Adding avg_cost to positions table...")
            conn.execute(text("ALTER TABLE positions ADD COLUMN avg_cost REAL"))
            conn.commit()
            print("[OK] Added avg_cost to positions")

        # Note: cash column removal is handled by not using it - we don't drop it to preserve data


def migrate_orders_table(engine: Engine) -> None:
    """Add tenant_id and portfolio_id to orders table."""
    with engine.connect() as conn:
        if column_exists(engine, "orders", "tenant_id"):
            print("[OK] orders.tenant_id already exists")
        else:
            print("Adding tenant_id to orders table...")
            conn.execute(
                text("ALTER TABLE orders ADD COLUMN tenant_id TEXT NOT NULL DEFAULT 'default'")
            )
            conn.execute(
                text("CREATE INDEX IF NOT EXISTS ix_orders_tenant_id ON orders(tenant_id)")
            )
            conn.commit()
            print("[OK] Added tenant_id to orders")

        if column_exists(engine, "orders", "portfolio_id"):
            print("[OK] orders.portfolio_id already exists")
        else:
            print("Adding portfolio_id to orders table...")
            conn.execute(
                text("ALTER TABLE orders ADD COLUMN portfolio_id TEXT NOT NULL DEFAULT 'default'")
            )
            conn.execute(
                text("CREATE INDEX IF NOT EXISTS ix_orders_portfolio_id ON orders(portfolio_id)")
            )
            conn.commit()
            print("[OK] Added portfolio_id to orders")


def migrate_trades_table(engine: Engine) -> None:
    """Add tenant_id and portfolio_id to trades table."""
    with engine.connect() as conn:
        if column_exists(engine, "trades", "tenant_id"):
            print("[OK] trades.tenant_id already exists")
        else:
            print("Adding tenant_id to trades table...")
            conn.execute(
                text("ALTER TABLE trades ADD COLUMN tenant_id TEXT NOT NULL DEFAULT 'default'")
            )
            conn.execute(
                text("CREATE INDEX IF NOT EXISTS ix_trades_tenant_id ON trades(tenant_id)")
            )
            conn.commit()
            print("[OK] Added tenant_id to trades")

        if column_exists(engine, "trades", "portfolio_id"):
            print("[OK] trades.portfolio_id already exists")
        else:
            print("Adding portfolio_id to trades table...")
            conn.execute(
                text("ALTER TABLE trades ADD COLUMN portfolio_id TEXT NOT NULL DEFAULT 'default'")
            )
            conn.execute(
                text("CREATE INDEX IF NOT EXISTS ix_trades_portfolio_id ON trades(portfolio_id)")
            )
            conn.commit()
            print("[OK] Added portfolio_id to trades")


def migrate_events_table(engine: Engine) -> None:
    """Add tenant_id and portfolio_id to events table (nullable)."""
    with engine.connect() as conn:
        if column_exists(engine, "events", "tenant_id"):
            print("[OK] events.tenant_id already exists")
        else:
            print("Adding tenant_id to events table...")
            conn.execute(text("ALTER TABLE events ADD COLUMN tenant_id TEXT"))
            conn.execute(
                text("CREATE INDEX IF NOT EXISTS ix_events_tenant_id ON events(tenant_id)")
            )
            conn.commit()
            print("[OK] Added tenant_id to events")

        if column_exists(engine, "events", "portfolio_id"):
            print("[OK] events.portfolio_id already exists")
        else:
            print("Adding portfolio_id to events table...")
            conn.execute(text("ALTER TABLE events ADD COLUMN portfolio_id TEXT"))
            conn.execute(
                text("CREATE INDEX IF NOT EXISTS ix_events_portfolio_id ON events(portfolio_id)")
            )
            conn.commit()
            print("[OK] Added portfolio_id to events")


# REMOVED: create_portfolio_cash_table - PortfolioCash has been removed, cash is now in Position.cash


def create_portfolio_config_table(engine: Engine) -> None:
    """Create portfolio_config table if it doesn't exist."""
    with engine.connect() as conn:
        inspector = inspect(engine)
        if "portfolio_config" in inspector.get_table_names():
            print("[OK] portfolio_config table already exists")
        else:
            print("Creating portfolio_config table...")
            conn.execute(
                text(
                    """
                CREATE TABLE portfolio_config (
                    tenant_id TEXT NOT NULL,
                    portfolio_id TEXT NOT NULL,
                    trigger_up_pct REAL NOT NULL DEFAULT 3.0,
                    trigger_down_pct REAL NOT NULL DEFAULT -3.0,
                    min_stock_pct REAL NOT NULL DEFAULT 20.0,
                    max_stock_pct REAL NOT NULL DEFAULT 80.0,
                    max_trade_pct_of_position REAL,
                    commission_rate_pct REAL NOT NULL DEFAULT 0.0,
                    version INTEGER NOT NULL DEFAULT 1,
                    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (tenant_id, portfolio_id),
                    FOREIGN KEY (tenant_id, portfolio_id) REFERENCES portfolios(tenant_id, id) ON DELETE CASCADE
                )
            """
                )
            )
            conn.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS ix_portfolio_config_tenant_portfolio ON portfolio_config(tenant_id, portfolio_id)"
                )
            )
            conn.commit()
            print("[OK] Created portfolio_config table")


def migrate_existing_data(engine: Engine) -> None:
    """Migrate existing data to set portfolio_id for positions based on existing relationships."""
    with engine.connect() as conn:
        # Try to set portfolio_id for positions based on portfolio_positions join table if it exists
        inspector = inspect(engine)
        if "portfolio_positions" in inspector.get_table_names():
            print("Migrating position portfolio_id from portfolio_positions table...")
            try:
                conn.execute(
                    text(
                        """
                    UPDATE positions
                    SET portfolio_id = (
                        SELECT portfolio_id
                        FROM portfolio_positions
                        WHERE portfolio_positions.position_id = positions.id
                        LIMIT 1
                    )
                    WHERE portfolio_id = 'default'
                """
                    )
                )
                conn.commit()
                print("[OK] Migrated portfolio_id for positions")
            except Exception as e:
                print(f"[WARN] Could not migrate portfolio_id from portfolio_positions: {e}")

        # Set portfolio_id for orders and trades based on their position_id
        print("Migrating order/trade portfolio_id from positions...")
        try:
            conn.execute(
                text(
                    """
                UPDATE orders
                SET portfolio_id = (
                    SELECT portfolio_id
                    FROM positions
                    WHERE positions.id = orders.position_id
                    LIMIT 1
                ),
                tenant_id = (
                    SELECT tenant_id
                    FROM positions
                    WHERE positions.id = orders.position_id
                    LIMIT 1
                )
                WHERE portfolio_id = 'default' OR tenant_id = 'default'
            """
                )
            )
            conn.commit()
            print("[OK] Migrated tenant_id and portfolio_id for orders")
        except Exception as e:
            print(f"⚠️  Could not migrate orders: {e}")

        try:
            conn.execute(
                text(
                    """
                UPDATE trades
                SET portfolio_id = (
                    SELECT portfolio_id
                    FROM positions
                    WHERE positions.id = trades.position_id
                    LIMIT 1
                ),
                tenant_id = (
                    SELECT tenant_id
                    FROM positions
                    WHERE positions.id = trades.position_id
                    LIMIT 1
                )
                WHERE portfolio_id = 'default' OR tenant_id = 'default'
            """
                )
            )
            conn.commit()
            print("[OK] Migrated tenant_id and portfolio_id for trades")
        except Exception as e:
            print(f"⚠️  Could not migrate trades: {e}")


# REMOVED: migrate_portfolio_cash_to_positions - PortfolioCash has been removed, cash is now in Position.cash
# If you have existing portfolio_cash data, you'll need to manually migrate it to Position.cash


def main():
    """Run the migration."""
    print("=" * 60)
    print("Portfolio-Scoped State Migration")
    print("=" * 60)
    print()

    db_path = get_db_path()
    if not os.path.exists(db_path):
        print(f"Database file not found: {db_path}")
        print("Creating new database with schema...")
        # Create new database - create_all will handle it
        from infrastructure.persistence.sql.models import get_engine, create_all

        engine = get_engine(f"sqlite:///{db_path}")
        create_all(engine)
        print("[OK] Created new database with portfolio-scoped schema")
        return

    print(f"Migrating database: {db_path}")
    print()

    engine = create_engine(f"sqlite:///{db_path}")

    try:
        # Migrate tables
        migrate_portfolios_table(engine)
        migrate_positions_table(engine)
        migrate_orders_table(engine)
        migrate_trades_table(engine)
        migrate_events_table(engine)

        # Create new tables
        create_portfolio_config_table(engine)

        # Migrate existing data
        migrate_existing_data(engine)
        # REMOVED: migrate_portfolio_cash_to_positions - PortfolioCash has been removed

        print()
        print("=" * 60)
        print("[OK] Migration completed successfully!")
        print("=" * 60)

    except Exception as e:
        print()
        print("=" * 60)
        print(f"ERROR: Migration failed: {e}")
        print("=" * 60)
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
