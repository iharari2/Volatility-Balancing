# =========================
# backend/application/services/portfolio_service.py
# =========================
"""
Portfolio Service for managing portfolios and portfolio-level operations.

This service provides portfolio-level aggregation, analytics, and management
capabilities, complementing the Position service which handles individual positions.
"""

from __future__ import annotations
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta

from domain.entities.portfolio import Portfolio
from domain.entities.portfolio_config import PortfolioConfig
from domain.ports.portfolio_repo import PortfolioRepo
from domain.ports.positions_repo import PositionsRepo
from domain.ports.portfolio_config_repo import PortfolioConfigRepo
from domain.ports.position_baseline_repo import PositionBaselineRepo


class PortfolioService:
    """Service for portfolio-level operations and aggregation."""

    def __init__(
        self,
        portfolio_repo: PortfolioRepo,
        positions_repo: PositionsRepo,
        portfolio_config_repo: PortfolioConfigRepo,
        baseline_repo: Optional[PositionBaselineRepo] = None,
        market_data_repo: Optional[Any] = None,
    ):
        self._portfolio_repo = portfolio_repo
        self._positions_repo = positions_repo
        self._portfolio_config_repo = portfolio_config_repo
        self._baseline_repo = baseline_repo
        self._market_data_repo = market_data_repo

    # --- Portfolio CRUD Operations ---

    def create_portfolio(
        self,
        tenant_id: str,
        name: str,
        description: Optional[str] = None,
        user_id: str = "default",
        portfolio_type: str = "LIVE",
        trading_hours_policy: str = "OPEN_ONLY",
        starting_cash: Optional[Dict[str, Any]] = None,
        holdings: Optional[List[Dict[str, Any]]] = None,
        template: str = "DEFAULT",
    ) -> Portfolio:
        """Create a new portfolio with cash, positions, and config in a transaction.

        Note: For true transaction safety, this should use a database transaction.
        Currently, each repository operation commits separately. For production,
        wrap this in a transaction context manager.
        """
        try:
            # Check for duplicate portfolio name within the same tenant
            existing_portfolios = self._portfolio_repo.list_all(
                tenant_id=tenant_id, user_id=user_id
            )
            for existing in existing_portfolios:
                if existing.name.strip().lower() == name.strip().lower():
                    raise ValueError(
                        f"Portfolio with name '{name}' already exists. Please choose a different name."
                    )

            # Create portfolio
            portfolio = self._portfolio_repo.create(
                tenant_id=tenant_id,
                name=name,
                description=description,
                user_id=user_id,
                portfolio_type=portfolio_type,
                trading_state="NOT_CONFIGURED",
                trading_hours_policy=trading_hours_policy,
            )

            # Get starting cash amount (used as fallback if positions don't specify cash)
            cash_amount = starting_cash.get("amount", 0.0) if starting_cash else 0.0
            currency = starting_cash.get("currency", "USD") if starting_cash else "USD"

            # Create positions if provided - each position gets its own cash allocation
            positions_created = []
            total_cash_allocated = 0.0

            if holdings:
                for holding in holdings:
                    asset_symbol = holding.get("asset")
                    if not asset_symbol:
                        continue
                    qty = holding.get("qty", 0.0)
                    if qty <= 0:
                        continue
                    anchor_price = holding.get("anchor_price")
                    avg_cost = holding.get("avg_cost")
                    # Each position has its own cash allocation (cash lives in Position entity)
                    position_cash = holding.get("cash")
                    if position_cash is None:
                        # If no cash specified for this position, use 0 (will be handled below)
                        position_cash = 0.0

                    # Create position without cash first (repo.create doesn't take cash)
                    position = self._positions_repo.create(
                        tenant_id=tenant_id,
                        portfolio_id=portfolio.id,
                        asset_symbol=asset_symbol,
                        qty=qty,
                        anchor_price=anchor_price,
                        avg_cost=avg_cost,
                    )
                    # Then set cash on the Position entity and save
                    position.cash = position_cash
                    self._positions_repo.save(position)

                    positions_created.append(position)
                    total_cash_allocated += position_cash

            # If positions didn't specify cash but portfolio has starting_cash, distribute it
            remaining_cash = cash_amount - total_cash_allocated
            if remaining_cash > 0 and positions_created:
                # Distribute remaining cash equally to positions that didn't have cash specified
                # (or distribute to all if none specified cash)
                cash_per_position = remaining_cash / len(positions_created)
                for position in positions_created:
                    position.cash += cash_per_position
                    self._positions_repo.save(position)
            elif remaining_cash > 0 and not positions_created:
                # No positions yet - create a special "CASH" position to hold the cash
                # This ensures cash is not lost and can be distributed when real positions are added
                cash_position = self._positions_repo.create(
                    tenant_id=tenant_id,
                    portfolio_id=portfolio.id,
                    asset_symbol="CASH",
                    qty=0.0,  # No shares, just cash
                    anchor_price=None,
                    avg_cost=None,
                )
                # Set cash after creation (cash lives in Position entity)
                cash_position.cash = remaining_cash
                self._positions_repo.save(cash_position)
                # Note: User can later add real positions and cash can be redistributed

            # Create config from template
            # Map template to config values
            template_configs = {
                "DEFAULT": {
                    "trigger_up_pct": 3.0,
                    "trigger_down_pct": -3.0,
                    "min_stock_pct": 20.0,
                    "max_stock_pct": 60.0,
                    "max_trade_pct_of_position": 10.0,
                    "commission_rate_pct": 0.1,
                },
                "CONSERVATIVE": {
                    "trigger_up_pct": 4.0,
                    "trigger_down_pct": -4.0,
                    "min_stock_pct": 15.0,
                    "max_stock_pct": 50.0,
                    "max_trade_pct_of_position": 5.0,
                    "commission_rate_pct": 0.1,
                },
                "AGGRESSIVE": {
                    "trigger_up_pct": 2.0,
                    "trigger_down_pct": -2.0,
                    "min_stock_pct": 25.0,
                    "max_stock_pct": 75.0,
                    "max_trade_pct_of_position": 15.0,
                    "commission_rate_pct": 0.1,
                },
                "CUSTOM": {
                    "trigger_up_pct": 3.0,
                    "trigger_down_pct": -3.0,
                    "min_stock_pct": 20.0,
                    "max_stock_pct": 60.0,
                    "max_trade_pct_of_position": 10.0,
                    "commission_rate_pct": 0.1,
                },
            }

            config_values = template_configs.get(template.upper(), template_configs["DEFAULT"])
            try:
                self._portfolio_config_repo.create(
                    tenant_id=tenant_id,
                    portfolio_id=portfolio.id,
                    trigger_up_pct=config_values["trigger_up_pct"],
                    trigger_down_pct=config_values["trigger_down_pct"],
                    min_stock_pct=config_values["min_stock_pct"],
                    max_stock_pct=config_values["max_stock_pct"],
                    max_trade_pct_of_position=config_values["max_trade_pct_of_position"],
                    commission_rate_pct=config_values["commission_rate_pct"],
                )
            except Exception as config_error:
                # Log config creation error but don't fail portfolio creation
                # Portfolio is already saved, config can be created later
                print(
                    f"Warning: Failed to create config for portfolio {portfolio.id}: {config_error}"
                )
                # Continue - portfolio is still valid without config (can be created later)

            return portfolio
        except Exception as e:
            # If portfolio creation itself fails, raise the error
            # Note: Portfolio may already be saved if error occurs after save()
            print(f"Error creating portfolio: {str(e)}")
            raise Exception(f"Failed to create portfolio: {str(e)}") from e

    def get_portfolio(self, tenant_id: str, portfolio_id: str) -> Optional[Portfolio]:
        """Get a portfolio by ID, scoped to tenant."""
        return self._portfolio_repo.get(tenant_id=tenant_id, portfolio_id=portfolio_id)

    def list_portfolios(self, tenant_id: str, user_id: Optional[str] = None) -> List[Portfolio]:
        """List all portfolios for a tenant, optionally filtered by user_id."""
        return self._portfolio_repo.list_all(tenant_id=tenant_id, user_id=user_id)

    def update_portfolio(
        self,
        tenant_id: str,
        portfolio_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        trading_state: Optional[str] = None,
        trading_hours_policy: Optional[str] = None,
    ) -> Optional[Portfolio]:
        """Update portfolio metadata. Validates name uniqueness if name is being changed."""
        portfolio = self._portfolio_repo.get(tenant_id=tenant_id, portfolio_id=portfolio_id)
        if not portfolio:
            return None

        # Check for duplicate name if name is being changed
        if name is not None and name.strip().lower() != portfolio.name.strip().lower():
            existing_portfolios = self._portfolio_repo.list_all(
                tenant_id=tenant_id, user_id=portfolio.user_id
            )
            for existing in existing_portfolios:
                if (
                    existing.id != portfolio.id
                    and existing.name.strip().lower() == name.strip().lower()
                ):
                    raise ValueError(
                        f"Portfolio with name '{name}' already exists. Please choose a different name."
                    )

        portfolio.update(
            name=name,
            description=description,
            trading_state=trading_state,
            trading_hours_policy=trading_hours_policy,
        )
        self._portfolio_repo.save(portfolio)
        return portfolio

    def delete_portfolio(self, tenant_id: str, portfolio_id: str) -> bool:
        """Delete a portfolio."""
        return self._portfolio_repo.delete(tenant_id=tenant_id, portfolio_id=portfolio_id)

    # --- Position Management ---

    def add_position_to_portfolio(
        self, tenant_id: str, portfolio_id: str, position_id: str
    ) -> bool:
        """Add a position to a portfolio."""
        # Verify portfolio exists
        portfolio = self._portfolio_repo.get(tenant_id=tenant_id, portfolio_id=portfolio_id)
        if not portfolio:
            return False

        # Verify position exists (position must already be scoped to tenant+portfolio)
        position = self._positions_repo.get(
            tenant_id=tenant_id, portfolio_id=portfolio_id, position_id=position_id
        )
        if not position:
            return False

        # Add position to portfolio
        return self._portfolio_repo.add_position(
            tenant_id=tenant_id, portfolio_id=portfolio_id, position_id=position_id
        )

    def remove_position_from_portfolio(
        self, tenant_id: str, portfolio_id: str, position_id: str
    ) -> bool:
        """Remove a position from a portfolio."""
        return self._portfolio_repo.remove_position(
            tenant_id=tenant_id, portfolio_id=portfolio_id, position_id=position_id
        )

    def get_portfolio_positions(self, tenant_id: str, portfolio_id: str) -> List[Any]:
        """Get all positions in a portfolio."""
        return self._positions_repo.list_all(tenant_id=tenant_id, portfolio_id=portfolio_id)

    def create_position_in_portfolio(
        self,
        tenant_id: str,
        portfolio_id: str,
        asset_symbol: str,
        qty: float,
        anchor_price: Optional[float] = None,
        avg_cost: Optional[float] = None,
        starting_cash: float = 0.0,
    ) -> Any:
        """
        Create a new position directly in a portfolio.

        Per usage model: A PositionBaseline is created immediately when position is added.
        """
        # Create position (status defaults to RUNNING)
        # The interface doesn't include cash, but implementation may support it
        # Try to pass cash directly, fallback to setting it after creation
        try:
            import inspect

            sig = inspect.signature(self._positions_repo.create)
            if "cash" in sig.parameters:
                # Implementation supports cash parameter
                position = self._positions_repo.create(
                    tenant_id=tenant_id,
                    portfolio_id=portfolio_id,
                    asset_symbol=asset_symbol,
                    qty=qty,
                    anchor_price=anchor_price,
                    avg_cost=avg_cost,
                    cash=starting_cash,
                )
            else:
                # Interface doesn't support cash parameter - create then set cash
                position = self._positions_repo.create(
                    tenant_id=tenant_id,
                    portfolio_id=portfolio_id,
                    asset_symbol=asset_symbol,
                    qty=qty,
                    anchor_price=anchor_price,
                    avg_cost=avg_cost,
                )
                if starting_cash != 0.0:
                    position.cash = starting_cash
                    self._positions_repo.save(position)
        except TypeError:
            # Fallback if introspection fails or signature check fails
            position = self._positions_repo.create(
                tenant_id=tenant_id,
                portfolio_id=portfolio_id,
                asset_symbol=asset_symbol,
                qty=qty,
                anchor_price=anchor_price,
                avg_cost=avg_cost,
            )
            if starting_cash != 0.0:
                position.cash = starting_cash
                self._positions_repo.save(position)
        except Exception as e:
            # Re-raise with more context
            raise ValueError(f"Failed to create position for asset {asset_symbol}: {str(e)}") from e

        # Get current market price for baseline (if available)
        baseline_price = anchor_price or avg_cost
        if not baseline_price and self._market_data_repo:
            try:
                price_data = self._market_data_repo.get_reference_price(asset_symbol)
                if price_data:
                    baseline_price = price_data.price
            except Exception:
                pass  # If market data unavailable, use anchor_price or avg_cost

        # Create PositionBaseline immediately (per usage model)
        if self._baseline_repo and baseline_price:
            # Use Position entity's method to calculate baseline value
            baseline_total_value = position.get_total_value(baseline_price)
            baseline_stock_value = position.get_stock_value(baseline_price)

            baseline_data = {
                "position_id": position.id,
                "baseline_price": baseline_price,
                "baseline_qty": qty,
                "baseline_cash": position.cash,
                "baseline_total_value": baseline_total_value,
                "baseline_stock_value": baseline_stock_value,
                "baseline_timestamp": datetime.now(timezone.utc),
            }
            self._baseline_repo.save(baseline_data)

        return position

    def deposit_cash(
        self, tenant_id: str, portfolio_id: str, amount: float, position_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Deposit cash into a portfolio or specific position (cash lives in PositionCell)."""
        if position_id:
            # Deposit to specific position
            position = self._positions_repo.get(
                tenant_id=tenant_id, portfolio_id=portfolio_id, position_id=position_id
            )
            if not position:
                raise ValueError(f"Position {position_id} not found")
            position.cash += amount
            self._positions_repo.save(position)
            positions_updated = [position]
        else:
            # Distribute equally to all positions (backward compatibility)
            positions = self.get_portfolio_positions(tenant_id=tenant_id, portfolio_id=portfolio_id)
            if not positions:
                raise ValueError("No positions found in portfolio - cannot deposit cash")
            cash_per_position = amount / len(positions)
            for position in positions:
                position.cash += cash_per_position
                self._positions_repo.save(position)
            positions_updated = positions

        # Return summary
        all_positions = self.get_portfolio_positions(tenant_id=tenant_id, portfolio_id=portfolio_id)
        total_cash = sum(p.cash for p in all_positions)
        return {
            "cash_balance": total_cash,
            "available_cash": total_cash,  # No reserved cash in position-level model
            "positions_updated": len(positions_updated),
            "position_id": position_id if position_id else None,
        }

    def withdraw_cash(
        self, tenant_id: str, portfolio_id: str, amount: float, position_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Withdraw cash from a portfolio or specific position (cash lives in PositionCell)."""
        if position_id:
            # Withdraw from specific position
            position = self._positions_repo.get(
                tenant_id=tenant_id, portfolio_id=portfolio_id, position_id=position_id
            )
            if not position:
                raise ValueError(f"Position {position_id} not found")
            if position.cash < amount:
                raise ValueError(
                    f"Insufficient cash in position: have ${position.cash:.2f}, need ${amount:.2f}"
                )
            position.cash -= amount
            self._positions_repo.save(position)
            positions_updated = [position]
        else:
            # Withdraw equally from all positions (backward compatibility)
            positions = self.get_portfolio_positions(tenant_id=tenant_id, portfolio_id=portfolio_id)
            if not positions:
                raise ValueError("No positions found in portfolio - cannot withdraw cash")

            # Check total available cash
            total_cash = sum(p.cash for p in positions)
            if total_cash < amount:
                raise ValueError(f"Insufficient cash: have ${total_cash:.2f}, need ${amount:.2f}")

            # Withdraw equally from each position
            cash_per_position = amount / len(positions)
            for position in positions:
                if position.cash < cash_per_position:
                    # If a position doesn't have enough, take what it has and adjust others
                    actual_withdraw = min(position.cash, cash_per_position)
                    position.cash -= actual_withdraw
                    amount -= actual_withdraw
                else:
                    position.cash -= cash_per_position
                self._positions_repo.save(position)
            positions_updated = positions

        # If there's remaining amount due to rounding, withdraw from first position
        if amount > 0.01:  # Small threshold for floating point
            positions[0].cash -= amount
            self._positions_repo.save(positions[0])

        # Return summary (for backward compatibility with API)
        total_cash_after = sum(p.cash for p in positions)
        return {
            "cash_balance": total_cash_after,
            "available_cash": total_cash_after,
            "positions_updated": len(positions),
        }

    # --- Portfolio Analytics ---

    def get_portfolio_summary(self, tenant_id: str, portfolio_id: str) -> Optional[Dict[str, Any]]:
        """Get portfolio summary with aggregated metrics."""
        portfolio = self._portfolio_repo.get(tenant_id=tenant_id, portfolio_id=portfolio_id)
        if not portfolio:
            return None

        positions = self.get_portfolio_positions(tenant_id=tenant_id, portfolio_id=portfolio_id)

        # Calculate aggregate metrics from positions (cash lives in PositionCell)
        total_cash = 0.0
        total_qty = {}  # Group by asset_symbol
        total_value = 0.0

        for position in positions:
            try:
                # Safely get cash value
                cash_value = getattr(position, "cash", None)
                if cash_value is None:
                    cash_value = 0.0
                total_cash += float(cash_value)

                asset_symbol = position.asset_symbol
                if asset_symbol not in total_qty:
                    total_qty[asset_symbol] = 0.0
                total_qty[asset_symbol] += position.qty

                # Use Position entity's method to calculate value
                # For now, uses anchor_price or avg_cost as fallback (no current market price)
                # position.get_total_value() includes position.cash
                position_total_value = position.get_total_value()
                total_value += position_total_value
            except Exception as pos_error:
                # Log error but continue processing other positions
                print(
                    f"Error processing position {getattr(position, 'id', 'unknown')} in summary: {pos_error}"
                )
                continue

        # total_value already includes total_cash because it's summed from position.get_total_value()
        # which returns position.cash + position.get_stock_value()

        return {
            "portfolio_id": portfolio.id,
            "portfolio_name": portfolio.name,
            "description": portfolio.description,
            "total_positions": len(positions),
            "total_cash": total_cash,
            "total_value": total_value,
            "positions_by_ticker": {
                asset_symbol: {
                    "qty": qty,
                    "positions": [p.id for p in positions if p.asset_symbol == asset_symbol],
                }
                for asset_symbol, qty in total_qty.items()
            },
            "created_at": portfolio.created_at.isoformat(),
            "updated_at": portfolio.updated_at.isoformat(),
        }

    def get_portfolio_config(self, tenant_id: str, portfolio_id: str) -> Optional[PortfolioConfig]:
        """Get portfolio configuration."""
        return self._portfolio_config_repo.get(tenant_id=tenant_id, portfolio_id=portfolio_id)

    def update_portfolio_config(
        self,
        tenant_id: str,
        portfolio_id: str,
        trigger_up_pct: Optional[float] = None,
        trigger_down_pct: Optional[float] = None,
        min_stock_pct: Optional[float] = None,
        max_stock_pct: Optional[float] = None,
        max_trade_pct_of_position: Optional[float] = None,
        commission_rate_pct: Optional[float] = None,
    ) -> Optional[PortfolioConfig]:
        """Update portfolio configuration."""
        config = self._portfolio_config_repo.get(tenant_id=tenant_id, portfolio_id=portfolio_id)
        if not config:
            # Create config if it doesn't exist
            config = self._portfolio_config_repo.create(
                tenant_id=tenant_id,
                portfolio_id=portfolio_id,
                trigger_up_pct=trigger_up_pct or 3.0,
                trigger_down_pct=trigger_down_pct or -3.0,
                min_stock_pct=min_stock_pct or 25.0,
                max_stock_pct=max_stock_pct or 75.0,
                max_trade_pct_of_position=max_trade_pct_of_position,
                commission_rate_pct=commission_rate_pct or 0.1,
            )
        else:
            # Update existing config
            config.update(
                trigger_up_pct=trigger_up_pct,
                trigger_down_pct=trigger_down_pct,
                min_stock_pct=min_stock_pct,
                max_stock_pct=max_stock_pct,
                max_trade_pct_of_position=max_trade_pct_of_position,
                commission_rate_pct=commission_rate_pct,
            )
            self._portfolio_config_repo.save(config)
        return config

    def get_portfolio_analytics(
        self, tenant_id: str, portfolio_id: str, days: int = 30, position_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Get detailed portfolio analytics with historical time series.

        Args:
            position_id: Optional position ID to filter analytics to a single position.

        Returns:
            Analytics data including:
            - time_series: Daily snapshots of value, stock, cash, percentages
            - kpis: Volatility, max drawdown, sharpe-like ratio, returns
            - events: List of trades and dividends in the period
            - guardrails: min_stock_pct and max_stock_pct from config
            - performance: Alpha and return comparison vs buy-hold
        """
        summary = self.get_portfolio_summary(tenant_id=tenant_id, portfolio_id=portfolio_id)
        if not summary:
            return None

        all_positions = self.get_portfolio_positions(tenant_id=tenant_id, portfolio_id=portfolio_id)

        # Filter positions if position_id is specified
        if position_id:
            positions = [p for p in all_positions if p.id == position_id]
            if not positions:
                return None  # Position not found
        else:
            positions = all_positions

        # 1. Allocation percentages
        total_value = summary["total_value"]
        allocation = {}
        cash_value = sum(p.cash for p in positions)  # Cash lives in PositionCell

        if total_value > 0:
            allocation["CASH"] = {
                "value": cash_value,
                "percentage": (cash_value / total_value) * 100 if total_value > 0 else 0.0,
            }

        for position in positions:
            asset_symbol = position.asset_symbol
            price = position.anchor_price or position.avg_cost
            position_value = (
                position.get_total_value(price) if price else position.get_total_value()
            )

            if asset_symbol not in allocation:
                allocation[asset_symbol] = {"value": 0.0, "percentage": 0.0}

            allocation[asset_symbol]["value"] += position_value
            if total_value > 0:
                allocation[asset_symbol]["percentage"] = (
                    allocation[asset_symbol]["value"] / total_value
                ) * 100

        # 2. Historical Time Series (from evaluation_timeline)
        # We aggregate daily snapshots for the portfolio
        time_series = []
        try:
            from app.di import container
            from collections import defaultdict

            if hasattr(container, "evaluation_timeline"):
                # Calculate date range based on days parameter
                end_date = datetime.now(timezone.utc)
                start_date = end_date - timedelta(days=days)

                # Get timeline for all positions in the portfolio
                # Filter by date range and exclude simulation data for live analytics
                rows = container.evaluation_timeline.list_by_portfolio(
                    tenant_id=tenant_id,
                    portfolio_id=portfolio_id,
                    start_date=start_date,
                    end_date=end_date,
                    limit=5000,  # Increased limit for more data points
                )

                # Filter rows by position_id if specified
                if position_id:
                    rows = [r for r in rows if r.get("position_id") == position_id]

                print(f"📊 Analytics: Found {len(rows)} timeline rows for portfolio {portfolio_id} (last {days} days)" +
                      (f", filtered to position {position_id}" if position_id else ""))

                # Group by day and position, taking the latest evaluation per position per day
                # Structure: {day: {position_id: {timestamp, values...}}}
                daily_position_data: Dict[str, Dict[str, Dict[str, Any]]] = defaultdict(dict)

                for row in rows:
                    dt = row.get("timestamp")
                    if not dt:
                        continue
                    if isinstance(dt, str):
                        dt = datetime.fromisoformat(dt.replace("Z", "+00:00"))
                    day_key = dt.strftime("%Y-%m-%d")
                    row_position_id = row.get("position_id", "unknown")

                    # Keep only the latest evaluation per position per day
                    existing = daily_position_data[day_key].get(row_position_id)
                    if existing is None or dt > existing.get("timestamp", dt):
                        # Use "after" values if available, fallback to "before" values
                        total_val = row.get("position_total_value_after")
                        if total_val is None or total_val == 0:
                            total_val = row.get("position_total_value_before") or 0.0
                        stock_val = row.get("position_stock_value_after")
                        if stock_val is None:
                            stock_val = row.get("position_stock_value_before") or 0.0
                        cash_val = row.get("position_cash_after")
                        if cash_val is None:
                            cash_val = row.get("position_cash_before") or 0.0

                        daily_position_data[day_key][row_position_id] = {
                            "timestamp": dt,
                            "total_value": total_val,
                            "stock_value": stock_val,
                            "cash": cash_val,
                        }

                # Aggregate across positions for each day
                for day in sorted(daily_position_data.keys()):
                    positions_data = daily_position_data[day]
                    total_value = sum(p["total_value"] for p in positions_data.values())
                    stock_value = sum(p["stock_value"] for p in positions_data.values())
                    cash_value = sum(p["cash"] for p in positions_data.values())

                    # Only include days with valid data (total_value > 0)
                    if total_value > 0:
                        time_series.append(
                            {
                                "date": day,
                                "value": total_value,
                                "stock": stock_value,
                                "cash": cash_value,
                                "stock_pct": (stock_value / total_value * 100),
                                "cash_pct": (cash_value / total_value * 100),
                            }
                        )

                print(f"   Aggregated to {len(time_series)} valid daily data points")

        except Exception as e:
            print(f"Warning: Failed to fetch historical time series for analytics: {e}")
            import traceback
            traceback.print_exc()

        # If no timeline data exists, create a single point from current position values
        if not time_series and positions:
            today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            current_stock_value = 0.0
            current_cash_value = 0.0
            for pos in positions:
                price = pos.anchor_price or pos.avg_cost or 0.0
                current_stock_value += pos.qty * price
                current_cash_value += pos.cash
            current_total = current_stock_value + current_cash_value
            if current_total > 0:
                time_series.append({
                    "date": today,
                    "value": current_total,
                    "stock": current_stock_value,
                    "cash": current_cash_value,
                    "stock_pct": (current_stock_value / current_total * 100) if current_total > 0 else 0.0,
                    "cash_pct": (current_cash_value / current_total * 100) if current_total > 0 else 0.0,
                })

        # 3. Calculate performance metrics from time series
        kpis = {}
        if time_series and len(time_series) > 1:
            # Calculate returns from time series
            values = [point["value"] for point in time_series if point["value"] > 0]
            if len(values) > 1:
                # Daily returns
                daily_returns = []
                for i in range(1, len(values)):
                    if values[i - 1] > 0:
                        daily_return = (values[i] - values[i - 1]) / values[i - 1]
                        daily_returns.append(daily_return)

                if daily_returns:
                    # Volatility (annualized standard deviation of daily returns)
                    import statistics

                    mean_return = statistics.mean(daily_returns)
                    variance = statistics.variance(daily_returns) if len(daily_returns) > 1 else 0.0
                    std_dev = statistics.stdev(daily_returns) if len(daily_returns) > 1 else 0.0
                    # Annualize: multiply by sqrt(252 trading days)
                    kpis["volatility"] = std_dev * (252**0.5) * 100  # Convert to percentage

                    # Sharpe-like ratio (simplified: return / volatility)
                    # Use total return from first to last value
                    total_return = (values[-1] - values[0]) / values[0] if values[0] > 0 else 0.0
                    annualized_return = (
                        total_return * (252 / len(daily_returns)) if len(daily_returns) > 0 else 0.0
                    )
                    kpis["sharpe_like"] = (
                        annualized_return / (std_dev * (252**0.5)) if std_dev > 0 else 0.0
                    )

                # Max Drawdown
                peak = values[0]
                max_drawdown = 0.0
                for value in values:
                    if value > peak:
                        peak = value
                    drawdown = (peak - value) / peak if peak > 0 else 0.0
                    if drawdown > max_drawdown:
                        max_drawdown = drawdown
                kpis["max_drawdown"] = -max_drawdown * 100  # Negative percentage

        # 4. Calculate total commissions and dividends from positions
        total_commission_paid = sum(
            getattr(p, "total_commission_paid", 0.0) or 0.0 for p in positions
        )
        total_dividends_received = sum(
            getattr(p, "total_dividends_received", 0.0) or 0.0 for p in positions
        )

        # 5. Calculate return percentage from time_series if available
        pnl_pct = 0.0
        if time_series and len(time_series) >= 2:
            first_value = time_series[0].get("value", 0)
            last_value = time_series[-1].get("value", 0)
            if first_value > 0:
                pnl_pct = ((last_value - first_value) / first_value) * 100

        # Set defaults for metrics that couldn't be calculated
        kpis.setdefault("volatility", 0.0)
        kpis.setdefault("max_drawdown", 0.0)
        kpis.setdefault("sharpe_like", 0.0)
        kpis["pnl_pct"] = pnl_pct
        kpis["commission_total"] = total_commission_paid
        kpis["dividend_total"] = total_dividends_received

        # 6. Fetch events (trades and dividends) for the period
        events: List[Dict[str, Any]] = []
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)

        # Track seen trades to avoid duplicates
        seen_trade_keys: set = set()

        try:
            from app.di import container

            # First, fetch trades from the trades table
            for pos in positions:
                trades = container.trades.list_for_position(pos.id, limit=500)
                for trade in trades:
                    trade_date = trade.executed_at
                    if trade_date and start_date <= trade_date <= end_date:
                        # Create a unique key based on date, position, side for dedup
                        trade_key = f"{trade_date.strftime('%Y-%m-%d')}_{pos.id}_{trade.side}_{trade.qty}"
                        seen_trade_keys.add(trade_key)
                        events.append({
                            "date": trade_date.strftime("%Y-%m-%d"),
                            "type": "TRADE",
                            "side": trade.side,
                            "qty": trade.qty,
                            "price": trade.price,
                            "commission": trade.commission,
                            "position_id": pos.id,
                            "asset_symbol": pos.asset_symbol,
                        })

            # Also fetch BUY/SELL actions from evaluation_timeline (for consistency with workspace Events tab)
            # This catches trades that may only be recorded in timeline but not in trades table
            if hasattr(container, "evaluation_timeline"):
                for pos in positions:
                    timeline_rows = container.evaluation_timeline.list_by_position(
                        tenant_id=tenant_id,
                        portfolio_id=portfolio_id,
                        position_id=pos.id,
                        start_date=start_date,
                        end_date=end_date,
                        limit=500,
                    )
                    for row in timeline_rows:
                        action = row.get("action")
                        if action in ("BUY", "SELL"):
                            # Handle both timestamp column names
                            row_ts = row.get("timestamp") or row.get("evaluated_at")
                            if row_ts:
                                if isinstance(row_ts, str):
                                    row_ts = datetime.fromisoformat(row_ts.replace("Z", "+00:00"))
                                # Calculate qty from the change
                                qty_before = row.get("position_qty_before") or 0
                                qty_after = row.get("position_qty_after") or 0
                                qty_change = abs(qty_after - qty_before)
                                if qty_change > 0:
                                    trade_key = f"{row_ts.strftime('%Y-%m-%d')}_{pos.id}_{action}_{qty_change}"
                                    # Only add if not already seen from trades table
                                    if trade_key not in seen_trade_keys:
                                        seen_trade_keys.add(trade_key)
                                        events.append({
                                            "date": row_ts.strftime("%Y-%m-%d"),
                                            "type": "TRADE",
                                            "side": action,
                                            "qty": qty_change,
                                            "price": row.get("effective_price") or row.get("close") or 0.0,
                                            "commission": row.get("commission") or 0.0,
                                            "position_id": pos.id,
                                            "asset_symbol": pos.asset_symbol,
                                        })

            # Fetch dividends for each position
            for pos in positions:
                receivables = container.dividend_receivable.get_receivables_by_position(pos.id)
                for recv in receivables:
                    # Use ex_date for the event date
                    ex_date = getattr(recv, "ex_date", None)
                    if ex_date:
                        if isinstance(ex_date, str):
                            ex_date = datetime.fromisoformat(ex_date.replace("Z", "+00:00"))
                        if start_date <= ex_date <= end_date:
                            events.append({
                                "date": ex_date.strftime("%Y-%m-%d"),
                                "type": "DIVIDEND",
                                "gross_amount": getattr(recv, "gross_amount", 0.0),
                                "net_amount": getattr(recv, "net_amount", 0.0),
                                "shares_held": getattr(recv, "shares_held", 0.0),
                                "dps": getattr(recv, "dps", 0.0),
                                "position_id": pos.id,
                                "asset_symbol": pos.asset_symbol,
                            })

            # Sort events by date
            events.sort(key=lambda e: e["date"])
        except Exception as e:
            print(f"Warning: Failed to fetch events for analytics: {e}")
            import traceback
            traceback.print_exc()

        # 7. Get guardrails - position-specific config first, then portfolio config
        guardrails: Optional[Dict[str, float]] = None
        try:
            from app.di import container

            # If position_id is specified, check for position-specific guardrail config
            if position_id and len(positions) == 1:
                guardrail_config = container.config.get_guardrail_config(position_id)
                if guardrail_config:
                    # GuardrailConfig stores values as decimals (0.25 = 25%), convert to percentage
                    guardrails = {
                        "min_stock_pct": float(guardrail_config.min_stock_pct) * 100,
                        "max_stock_pct": float(guardrail_config.max_stock_pct) * 100,
                    }

            # Fall back to portfolio config if no position-specific config
            if guardrails is None:
                portfolio_config = self._portfolio_config_repo.get(
                    tenant_id=tenant_id, portfolio_id=portfolio_id
                )
                if portfolio_config:
                    # Portfolio config already stores as percentages
                    guardrails = {
                        "min_stock_pct": portfolio_config.min_stock_pct,
                        "max_stock_pct": portfolio_config.max_stock_pct,
                    }
        except Exception as e:
            print(f"Warning: Failed to fetch guardrails for analytics: {e}")

        # 8. Calculate performance metrics (alpha = portfolio return - buy-hold return)
        performance: Dict[str, float] = {
            "alpha": 0.0,
            "portfolio_return_pct": 0.0,
            "benchmark_return_pct": 0.0,
        }
        if time_series and len(time_series) >= 2:
            first_point = time_series[0]
            last_point = time_series[-1]

            # Portfolio return (total value change)
            first_value = first_point.get("value", 0)
            last_value = last_point.get("value", 0)
            if first_value > 0:
                portfolio_return = ((last_value - first_value) / first_value) * 100
                performance["portfolio_return_pct"] = round(portfolio_return, 2)

            # Benchmark return (stock-only / buy-hold)
            # This represents what would have happened if we held stock without rebalancing
            first_stock = first_point.get("stock", 0)
            last_stock = last_point.get("stock", 0)
            if first_stock > 0:
                benchmark_return = ((last_stock - first_stock) / first_stock) * 100
                performance["benchmark_return_pct"] = round(benchmark_return, 2)

            # Alpha = portfolio return - benchmark return
            performance["alpha"] = round(
                performance["portfolio_return_pct"] - performance["benchmark_return_pct"], 2
            )

        # 9. Fetch SPY (S&P 500) data for market benchmark comparison
        try:
            if time_series and len(time_series) >= 2:
                from app.di import container

                first_date_str = time_series[0].get("date")
                last_date_str = time_series[-1].get("date")

                if first_date_str and last_date_str:
                    # Parse dates and add buffer for market data availability
                    spy_start = datetime.strptime(first_date_str, "%Y-%m-%d").replace(
                        tzinfo=timezone.utc
                    )
                    spy_end = datetime.strptime(last_date_str, "%Y-%m-%d").replace(
                        tzinfo=timezone.utc
                    ) + timedelta(days=1)

                    # Fetch SPY historical data
                    spy_data = container.market_data.fetch_historical_data(
                        "SPY", spy_start, spy_end, intraday_interval_minutes=1440
                    )

                    if spy_data and len(spy_data) >= 2:
                        # Build a date -> price lookup for SPY
                        spy_by_date: Dict[str, float] = {}
                        for price_point in spy_data:
                            date_key = price_point.timestamp.strftime("%Y-%m-%d")
                            # Take the closing price for each day
                            spy_by_date[date_key] = price_point.close or price_point.price

                        # Find SPY prices matching our time series dates
                        first_spy_price = spy_by_date.get(first_date_str)
                        last_spy_price = spy_by_date.get(last_date_str)

                        # If exact dates not found, use closest available
                        if not first_spy_price and spy_data:
                            first_spy_price = spy_data[0].close or spy_data[0].price
                        if not last_spy_price and spy_data:
                            last_spy_price = spy_data[-1].close or spy_data[-1].price

                        if first_spy_price and last_spy_price and first_spy_price > 0:
                            spy_return = (
                                (last_spy_price - first_spy_price) / first_spy_price
                            ) * 100
                            performance["spy_return_pct"] = round(spy_return, 2)
                            performance["spy_alpha"] = round(
                                performance["portfolio_return_pct"] - spy_return, 2
                            )
                            print(
                                f"📊 SPY benchmark: {first_spy_price:.2f} -> {last_spy_price:.2f}, "
                                f"return={spy_return:.2f}%, alpha={performance['spy_alpha']:.2f}%"
                            )
                        else:
                            print("⚠️ Could not calculate SPY return - missing price data")
                    else:
                        print(f"⚠️ No SPY data returned for period {first_date_str} to {last_date_str}")
        except Exception as e:
            print(f"⚠️ Failed to fetch SPY benchmark data: {e}")
            # Continue without SPY data - it's optional

        return {
            **summary,
            "allocation": allocation,
            "time_series": time_series,
            "kpis": kpis,
            "diversification": {
                "num_tickers": len([k for k in allocation.keys() if k != "CASH"]),
                "num_positions": len(positions),
            },
            "events": events,
            "guardrails": guardrails,
            "performance": performance,
        }

    def get_portfolio_overview(self, tenant_id: str, portfolio_id: str) -> Optional[Dict[str, Any]]:
        """Get portfolio overview with cash, positions, config, and KPIs."""
        portfolio = self._portfolio_repo.get(tenant_id=tenant_id, portfolio_id=portfolio_id)
        if not portfolio:
            return None

        positions = self.get_portfolio_positions(tenant_id=tenant_id, portfolio_id=portfolio_id)
        config = self._portfolio_config_repo.get(tenant_id=tenant_id, portfolio_id=portfolio_id)

        # Calculate KPIs from positions
        # Portfolio total value = sum of all position (cell) total values
        # Position = Cell, and each position has cash + stock
        total_value = 0.0
        total_cash = 0.0
        total_stock_value = 0.0
        positions_list = []

        for position in positions:
            price = position.anchor_price or position.avg_cost
            # Position total value = cash + stock value (this is the cell's total value)
            position_total_value = position.get_total_value(price)
            position_stock_value = position.get_stock_value(price)
            position_cash = position.cash or 0.0

            total_value += position_total_value
            total_cash += position_cash
            total_stock_value += position_stock_value

            positions_list.append(
                {
                    "asset": position.asset_symbol,
                    "qty": position.qty,
                    "anchor": position.anchor_price,
                    "avg_cost": position.avg_cost,
                    "cash": position_cash,
                    "stock_value": position_stock_value,
                    "total_value": position_total_value,
                }
            )

        stock_pct = (total_stock_value / total_value * 100) if total_value > 0 else 0.0

        # Calculate portfolio-level P&L based on contributed capital
        total_contributed = sum(getattr(p, "contributed_capital", 0.0) or 0.0 for p in positions)
        pnl_pct = 0.0
        if total_contributed > 0:
            pnl_pct = ((total_value - total_contributed) / total_contributed) * 100

        return {
            "portfolio": {
                "id": portfolio.id,
                "name": portfolio.name,
                "state": portfolio.trading_state,
                "type": portfolio.type,
                "hours_policy": portfolio.trading_hours_policy,
            },
            "cash": {
                "currency": "USD",  # Default currency (cash lives in PositionCell)
                "cash_balance": total_cash,
                "reserved_cash": 0.0,  # No reserved cash in position-level model
            },
            "positions": positions_list,
            "config_effective": {
                "trigger_up_pct": config.trigger_up_pct if config else 3.0,
                "trigger_down_pct": config.trigger_down_pct if config else -3.0,
                "min_stock_pct": config.min_stock_pct if config else 20.0,
                "max_stock_pct": config.max_stock_pct if config else 80.0,
                "max_trade_pct_of_position": config.max_trade_pct_of_position if config else None,
                "commission_rate_pct": config.commission_rate_pct if config else 0.0,
            },
            "kpis": {
                "total_value": total_value,
                "stock_pct": stock_pct,
                "cash_pct": 100.0 - stock_pct,
                "pnl_pct": pnl_pct,
                "pnl_abs": total_value - total_contributed,
            },
        }

    def get_position_cockpit(
        self, tenant_id: str, portfolio_id: str, position_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get holistic position cockpit data (per usage model: Position cockpit summary)."""
        position = self._positions_repo.get(
            tenant_id=tenant_id, portfolio_id=portfolio_id, position_id=position_id
        )
        if not position:
            return None

        # Get latest baseline
        baseline = None
        if self._baseline_repo:
            baseline = self._baseline_repo.get_latest(position_id)

        # Get current market price
        current_market_data = None
        if self._market_data_repo:
            try:
                price_data = self._market_data_repo.get_reference_price(position.asset_symbol)
                if price_data:
                    current_market_data = {
                        "price": price_data.price,
                        "source": getattr(price_data, "source", "unknown"),
                        "timestamp": (
                            price_data.timestamp.isoformat()
                            if price_data.timestamp
                            else datetime.now(timezone.utc).isoformat()
                        ),
                        "is_market_hours": getattr(price_data, "is_market_hours", True),
                    }
            except Exception:
                pass

        # Calculate deltas
        position_vs_baseline = {"pct": None, "abs": None}
        stock_vs_baseline = {"pct": None, "abs": None}

        if baseline and current_market_data:
            current_price = current_market_data["price"]
            current_total_value = position.get_total_value(current_price)
            baseline_total_value = baseline.get("baseline_total_value", 0.0)

            if baseline_total_value > 0:
                position_vs_baseline["abs"] = current_total_value - baseline_total_value
                position_vs_baseline["pct"] = (
                    (current_total_value / baseline_total_value) - 1
                ) * 100

            baseline_price = baseline.get("baseline_price", 0.0)
            if baseline_price > 0:
                stock_vs_baseline["abs"] = current_price - baseline_price
                stock_vs_baseline["pct"] = ((current_price / baseline_price) - 1) * 100

        # Status: RUNNING / PAUSED
        # Note: Position entity might not have status yet, so check model via repo if possible
        status = "RUNNING"
        try:
            # Try to get status from the underlying model if repo provides access
            if hasattr(self._positions_repo, "_sf"):
                from infrastructure.persistence.sql.models import PositionModel

                with self._positions_repo._sf() as session:
                    model = session.get(PositionModel, position_id)
                    if model and model.status:
                        status = model.status
        except Exception:
            pass

        # Calculate stock allocation: stock_value / total_position_value
        stock_allocation_pct = None
        stock_value = None
        total_position_value = None
        if current_market_data:
            current_price = current_market_data["price"]
            stock_value = position.qty * current_price
            total_position_value = position.cash + stock_value
            if total_position_value > 0:
                stock_allocation_pct = (stock_value / total_position_value) * 100

        # Get guardrail configuration - position-specific first, then portfolio
        guardrail_config = None
        min_stock_pct = None
        max_stock_pct = None
        try:
            from app.di import container

            # Check for position-specific guardrail config first
            pos_guardrail_config = container.config.get_guardrail_config(position_id)
            if pos_guardrail_config:
                # GuardrailConfig stores as decimal (0.25 = 25%), convert to percentage
                min_stock_pct = float(pos_guardrail_config.min_stock_pct) * 100
                max_stock_pct = float(pos_guardrail_config.max_stock_pct) * 100
                guardrail_config = {
                    "min_stock_pct": min_stock_pct,
                    "max_stock_pct": max_stock_pct,
                }
            else:
                # Fall back to portfolio config
                config = self._portfolio_config_repo.get(tenant_id=tenant_id, portfolio_id=portfolio_id)
                if config:
                    min_stock_pct = config.min_stock_pct
                    max_stock_pct = config.max_stock_pct
                    guardrail_config = {
                        "min_stock_pct": min_stock_pct,
                        "max_stock_pct": max_stock_pct,
                    }
        except Exception:
            pass

        # Determine if allocation is within guardrails
        allocation_within_guardrails = None
        if (
            stock_allocation_pct is not None
            and min_stock_pct is not None
            and max_stock_pct is not None
        ):
            allocation_within_guardrails = min_stock_pct <= stock_allocation_pct <= max_stock_pct

        return {
            "position": {
                "id": position.id,
                "asset_symbol": position.asset_symbol,
                "qty": position.qty,
                "cash": position.cash,
                "anchor_price": position.anchor_price,
                "avg_cost": position.avg_cost,
                "total_commission_paid": position.total_commission_paid,
                "total_dividends_received": position.total_dividends_received,
            },
            "baseline": baseline,
            "current_market_data": current_market_data,
            "trading_status": status,
            "position_vs_baseline": position_vs_baseline,
            "stock_vs_baseline": stock_vs_baseline,
            "stock_allocation": {
                "stock_value": stock_value,
                "total_position_value": total_position_value,
                "stock_allocation_pct": stock_allocation_pct,
            },
            "guardrails": guardrail_config,
            "allocation_within_guardrails": allocation_within_guardrails,
        }

    def get_position_market_data(
        self, tenant_id: str, portfolio_id: str, position_id: str, limit: int = 50
    ) -> Optional[Dict[str, Any]]:
        """Get latest and recent market data for a position."""
        position = self._positions_repo.get(
            tenant_id=tenant_id, portfolio_id=portfolio_id, position_id=position_id
        )
        if not position:
            return None

        # Latest snapshot
        latest = None
        if self._market_data_repo:
            try:
                price_data = self._market_data_repo.get_reference_price(position.asset_symbol)
                if price_data:
                    latest = {
                        "session": (
                            "REGULAR"
                            if getattr(price_data, "is_market_hours", True)
                            else "EXTENDED"
                        ),
                        "effective_price": price_data.price,
                        "price": price_data.price,
                        "price_policy_effective": getattr(price_data, "policy", "UNKNOWN"),
                        "best_bid": getattr(price_data, "bid", None),
                        "best_ask": getattr(price_data, "ask", None),
                        "open_price": getattr(price_data, "open", None),
                        "high_price": getattr(price_data, "high", None),
                        "low_price": getattr(price_data, "low", None),
                        "close_price": getattr(price_data, "close", None),
                        "volume": getattr(price_data, "volume", None),
                        "timestamp": (
                            price_data.timestamp.isoformat()
                            if price_data.timestamp
                            else datetime.now(timezone.utc).isoformat()
                        ),
                    }
            except Exception:
                pass

        # Recent data (from evaluation timeline if available, or just the latest snapshot)
        recent = []
        try:
            # If we have evaluation timeline repo, we can get recent effective prices
            from app.di import container

            if hasattr(container, "evaluation_timeline"):
                rows = container.evaluation_timeline.list_by_position(
                    tenant_id=tenant_id,
                    portfolio_id=portfolio_id,
                    position_id=position_id,
                    limit=limit,
                )
                for row in rows:
                    recent.append(
                        {
                            "timestamp": row["timestamp"],
                            "session": row.get("market_session", "REGULAR"),
                            "effective_price": row.get("effective_price"),
                            "price": row.get("last_trade_price"),
                            "close": row.get("close_price"),
                            "bid": row.get("best_bid"),
                            "ask": row.get("best_ask"),
                        }
                    )
        except Exception:
            pass

        return {
            "position_id": position_id,
            "asset_symbol": position.asset_symbol,
            "latest": latest,
            "recent": recent,
        }

    def reset_position_baseline(
        self, tenant_id: str, portfolio_id: str, position_id: str
    ) -> Optional[Dict[str, Any]]:
        """Reset the baseline for a position to current state (per usage model: Reset baseline button)."""
        position = self._positions_repo.get(
            tenant_id=tenant_id, portfolio_id=portfolio_id, position_id=position_id
        )
        if not position:
            return None

        # Get current market price
        current_price = position.anchor_price or position.avg_cost
        if self._market_data_repo:
            try:
                price_data = self._market_data_repo.get_reference_price(position.asset_symbol)
                if price_data:
                    current_price = price_data.price
            except Exception:
                pass

        if not current_price:
            raise ValueError(
                f"Cannot reset baseline for {position.asset_symbol}: current price unknown"
            )

        # Create NEW baseline record
        if self._baseline_repo:
            baseline_total_value = position.get_total_value(current_price)
            baseline_stock_value = position.get_stock_value(current_price)

            baseline_data = {
                "position_id": position.id,
                "baseline_price": current_price,
                "baseline_qty": position.qty,
                "baseline_cash": position.cash,
                "baseline_total_value": baseline_total_value,
                "baseline_stock_value": baseline_stock_value,
                "baseline_timestamp": datetime.now(timezone.utc),
            }
            self._baseline_repo.save(baseline_data)
            return baseline_data

        return None
