# =========================
# backend/application/use_cases/simulation_uc.py
# =========================
from __future__ import annotations
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from domain.ports.market_data import MarketDataRepo
from domain.ports.positions_repo import PositionsRepo
from domain.ports.events_repo import EventsRepo
from domain.entities.market_data import SimulationData
from infrastructure.time.clock import Clock


@dataclass
class SimulationResult:
    """Result of a trading simulation."""

    ticker: str
    start_date: datetime
    end_date: datetime
    total_trading_days: int

    # Algorithm performance
    algorithm_trades: int
    algorithm_pnl: float
    algorithm_return_pct: float
    algorithm_volatility: float
    algorithm_sharpe_ratio: float
    algorithm_max_drawdown: float

    # Buy & Hold performance
    buy_hold_pnl: float
    buy_hold_return_pct: float
    buy_hold_volatility: float
    buy_hold_sharpe_ratio: float
    buy_hold_max_drawdown: float

    # Comparison metrics
    excess_return: float
    alpha: float
    beta: float
    information_ratio: float

    # Trade details
    trade_log: List[Dict[str, Any]]
    daily_returns: List[Dict[str, Any]]


class SimulationUC:
    """Use case for running trading simulations and backtesting."""

    def __init__(
        self,
        market_data: MarketDataRepo,
        positions: PositionsRepo,
        events: EventsRepo,
        clock: Clock,
    ) -> None:
        self.market_data = market_data
        self.positions = positions
        events = events
        self.clock = clock

    def run_simulation(
        self,
        ticker: str,
        start_date: datetime,
        end_date: datetime,
        initial_cash: float = 10000.0,
        position_config: Optional[Dict[str, Any]] = None,
        include_after_hours: bool = False,
    ) -> SimulationResult:
        """Run a complete trading simulation."""

        # Default position configuration
        if position_config is None:
            position_config = {
                "trigger_threshold_pct": 0.03,
                "rebalance_ratio": 1.6667,
                "commission_rate": 0.0001,
                "min_notional": 100.0,
                "allow_after_hours": include_after_hours,
                "guardrails": {
                    "min_stock_alloc_pct": 0.25,
                    "max_stock_alloc_pct": 0.75,
                },
            }

        # Ensure timezone-aware datetimes
        if start_date.tzinfo is None:
            start_date = start_date.replace(tzinfo=timezone.utc)
        if end_date.tzinfo is None:
            end_date = end_date.replace(tzinfo=timezone.utc)

        # Fetch historical data first - use a shorter range for 1-minute data
        # yfinance only allows 8 days of 1-minute data per request
        days_diff = (end_date - start_date).days
        if days_diff > 7:
            # For longer periods, use daily data
            fetch_start = start_date - timedelta(days=1)
            fetch_end = end_date + timedelta(days=1)
        else:
            # For shorter periods, use 1-minute data
            fetch_start = start_date - timedelta(hours=1)
            fetch_end = end_date + timedelta(hours=1)

        print(f"Fetching historical data for {ticker} from {fetch_start} to {fetch_end}")
        historical_data = self.market_data.fetch_historical_data(ticker, fetch_start, fetch_end)

        if not historical_data:
            raise ValueError(f"No price data available for {ticker} in date range")

        # Get simulation data
        sim_data = self.market_data.get_simulation_data(
            ticker, start_date, end_date, include_after_hours
        )

        if not sim_data.price_data:
            raise ValueError(f"No price data available for {ticker} in date range")

        # Run algorithm simulation
        algo_result = self._simulate_algorithm(sim_data, initial_cash, position_config)

        # Run buy & hold simulation
        buy_hold_result = self._simulate_buy_hold(sim_data, initial_cash)

        # Calculate comparison metrics
        comparison_metrics = self._calculate_comparison_metrics(algo_result, buy_hold_result)

        return SimulationResult(
            ticker=ticker,
            start_date=start_date,
            end_date=end_date,
            total_trading_days=sim_data.total_trading_days,
            **algo_result,
            **buy_hold_result,
            **comparison_metrics,
        )

    def _simulate_algorithm(
        self, sim_data: SimulationData, initial_cash: float, position_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Simulate the volatility trading algorithm."""

        # Initialize portfolio
        cash = initial_cash
        shares = 0.0
        anchor_price = None
        total_commission = 0.0

        trade_log = []
        daily_returns = []
        portfolio_values = []

        # Process each price point
        for price_data in sim_data.price_data:
            current_price = price_data.price
            current_time = price_data.timestamp

            # Set anchor price on first trade or after a trade
            if anchor_price is None:
                anchor_price = current_price
                continue

            # Check for triggers
            trigger_result = self._check_triggers(current_price, anchor_price, position_config)

            if trigger_result["triggered"]:
                # Calculate order size
                order_result = self._calculate_order_size(
                    current_price, anchor_price, cash, shares, position_config
                )

                if order_result["valid"]:
                    # Execute trade
                    qty = order_result["qty"]
                    commission = order_result["commission"]

                    if qty > 0:  # Buy
                        cost = qty * current_price + commission
                        if cost <= cash:
                            cash -= cost
                            shares += qty
                            total_commission += commission
                            anchor_price = current_price  # Update anchor after trade

                            trade_log.append(
                                {
                                    "timestamp": current_time.isoformat(),
                                    "side": "BUY",
                                    "qty": qty,
                                    "price": current_price,
                                    "commission": commission,
                                    "cash_after": cash,
                                    "shares_after": shares,
                                }
                            )

                    elif qty < 0:  # Sell
                        sell_qty = min(abs(qty), shares)
                        if sell_qty > 0:
                            proceeds = sell_qty * current_price - commission
                            cash += proceeds
                            shares -= sell_qty
                            total_commission += commission
                            anchor_price = current_price  # Update anchor after trade

                            trade_log.append(
                                {
                                    "timestamp": current_time.isoformat(),
                                    "side": "SELL",
                                    "qty": -sell_qty,
                                    "price": current_price,
                                    "commission": commission,
                                    "cash_after": cash,
                                    "shares_after": shares,
                                }
                            )

            # Calculate portfolio value
            portfolio_value = cash + (shares * current_price)
            portfolio_values.append(portfolio_value)

            # Calculate daily returns (simplified - would need proper daily grouping)
            if len(portfolio_values) > 1:
                daily_return = (portfolio_values[-1] / portfolio_values[-2]) - 1
                daily_returns.append(
                    {
                        "date": current_time.date().isoformat(),
                        "return": daily_return,
                        "portfolio_value": portfolio_value,
                    }
                )

        # Calculate final metrics
        final_value = cash + (shares * sim_data.price_data[-1].price)
        total_return = (final_value - initial_cash) / initial_cash
        volatility = self._calculate_volatility([r["return"] for r in daily_returns])
        sharpe_ratio = self._calculate_sharpe_ratio(daily_returns)
        max_drawdown = self._calculate_max_drawdown(portfolio_values)

        return {
            "algorithm_trades": len(trade_log),
            "algorithm_pnl": final_value - initial_cash,
            "algorithm_return_pct": total_return * 100,
            "algorithm_volatility": volatility,
            "algorithm_sharpe_ratio": sharpe_ratio,
            "algorithm_max_drawdown": max_drawdown,
            "trade_log": trade_log,
            "daily_returns": daily_returns,
        }

    def _simulate_buy_hold(self, sim_data: SimulationData, initial_cash: float) -> Dict[str, Any]:
        """Simulate buy and hold strategy."""

        if not sim_data.price_data:
            return {
                "buy_hold_pnl": 0.0,
                "buy_hold_return_pct": 0.0,
                "buy_hold_volatility": 0.0,
                "buy_hold_sharpe_ratio": 0.0,
                "buy_hold_max_drawdown": 0.0,
            }

        start_price = sim_data.price_data[0].price
        end_price = sim_data.price_data[-1].price

        # Buy at start
        shares = initial_cash / start_price
        final_value = shares * end_price
        total_return = (final_value - initial_cash) / initial_cash

        # Calculate daily returns for buy & hold
        daily_returns = []
        for i, price_data in enumerate(sim_data.price_data):
            if i == 0:
                continue
            daily_return = (price_data.price / sim_data.price_data[i - 1].price) - 1
            daily_returns.append(
                {
                    "date": price_data.timestamp.date().isoformat(),
                    "return": daily_return,
                    "portfolio_value": shares * price_data.price,
                }
            )

        volatility = self._calculate_volatility([r["return"] for r in daily_returns])
        sharpe_ratio = self._calculate_sharpe_ratio(daily_returns)

        # Calculate max drawdown for buy & hold
        portfolio_values = [shares * p.price for p in sim_data.price_data]
        max_drawdown = self._calculate_max_drawdown(portfolio_values)

        return {
            "buy_hold_pnl": final_value - initial_cash,
            "buy_hold_return_pct": total_return * 100,
            "buy_hold_volatility": volatility,
            "buy_hold_sharpe_ratio": sharpe_ratio,
            "buy_hold_max_drawdown": max_drawdown,
        }

    def _check_triggers(
        self, current_price: float, anchor_price: float, config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Check if current price triggers buy or sell."""
        threshold = config["trigger_threshold_pct"]

        # Buy trigger: P ≤ P_anchor × (1 − τ)
        buy_threshold = anchor_price * (1 - threshold)
        # Sell trigger: P ≥ P_anchor × (1 + τ)
        sell_threshold = anchor_price * (1 + threshold)

        if current_price <= buy_threshold:
            return {
                "triggered": True,
                "side": "BUY",
                "reasoning": f"Price ${current_price:.2f} ≤ buy threshold ${buy_threshold:.2f}",
            }
        elif current_price >= sell_threshold:
            return {
                "triggered": True,
                "side": "SELL",
                "reasoning": f"Price ${current_price:.2f} ≥ sell threshold ${sell_threshold:.2f}",
            }
        else:
            return {
                "triggered": False,
                "reasoning": f"Price ${current_price:.2f} within threshold range",
            }

    def _calculate_order_size(
        self,
        current_price: float,
        anchor_price: float,
        cash: float,
        shares: float,
        config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Calculate order size using the specification formula."""

        # Calculate portfolio values
        asset_value = shares * current_price
        total_value = asset_value + cash

        # Apply order sizing formula: ΔQ_raw = (P_anchor / P) × r × ((A + C) / P)
        rebalance_ratio = config["rebalance_ratio"]
        raw_qty = (anchor_price / current_price) * rebalance_ratio * (total_value / current_price)

        # Apply side based on trigger (simplified)
        if current_price < anchor_price * (1 - config["trigger_threshold_pct"]):
            raw_qty = abs(raw_qty)  # Buy
        else:
            raw_qty = -abs(raw_qty)  # Sell

        # Apply guardrail trimming (simplified)
        min_alloc = config["guardrails"]["min_stock_alloc_pct"]
        max_alloc = config["guardrails"]["max_stock_alloc_pct"]

        post_qty = shares + raw_qty
        post_asset_value = post_qty * current_price
        post_total_value = post_asset_value + cash
        post_asset_pct = post_asset_value / post_total_value if post_total_value > 0 else 0

        if post_asset_pct < min_alloc:
            # Need to buy more
            target_asset_value = min_alloc * post_total_value
            target_qty = target_asset_value / current_price
            raw_qty = target_qty - shares
        elif post_asset_pct > max_alloc:
            # Need to sell more
            target_asset_value = max_alloc * post_total_value
            target_qty = target_asset_value / current_price
            raw_qty = target_qty - shares

        # Calculate commission
        notional = abs(raw_qty) * current_price
        commission = notional * config["commission_rate"]

        # Validate order
        valid = True
        if raw_qty > 0:  # Buy
            cost = raw_qty * current_price + commission
            valid = cost <= cash
        elif raw_qty < 0:  # Sell
            valid = abs(raw_qty) <= shares

        return {
            "qty": raw_qty,
            "commission": commission,
            "valid": valid,
        }

    def _calculate_volatility(self, returns: List[float]) -> float:
        """Calculate volatility from returns."""
        if len(returns) < 2:
            return 0.0

        import statistics

        return statistics.stdev(returns) * (252**0.5)  # Annualized

    def _calculate_sharpe_ratio(self, daily_returns: List[Dict[str, Any]]) -> float:
        """Calculate Sharpe ratio."""
        if not daily_returns:
            return 0.0

        returns = [r["return"] for r in daily_returns]
        if len(returns) < 2:
            return 0.0

        import statistics

        mean_return = statistics.mean(returns)
        std_return = statistics.stdev(returns)

        if std_return == 0:
            return 0.0

        # Assume risk-free rate of 2% annually
        risk_free_rate = 0.02 / 252  # Daily risk-free rate
        return (mean_return - risk_free_rate) / std_return * (252**0.5)

    def _calculate_max_drawdown(self, portfolio_values: List[float]) -> float:
        """Calculate maximum drawdown."""
        if not portfolio_values:
            return 0.0

        peak = portfolio_values[0]
        max_dd = 0.0

        for value in portfolio_values:
            if value > peak:
                peak = value
            else:
                drawdown = (peak - value) / peak
                max_dd = max(max_dd, drawdown)

        return max_dd * 100  # Return as percentage

    def _calculate_comparison_metrics(
        self, algo_result: Dict[str, Any], buy_hold_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate comparison metrics between algorithm and buy & hold."""

        excess_return = algo_result["algorithm_return_pct"] - buy_hold_result["buy_hold_return_pct"]

        # Alpha calculation (simplified)
        alpha = excess_return

        # Beta calculation (simplified - would need proper regression)
        beta = 1.0  # Placeholder

        # Information ratio
        algo_vol = algo_result["algorithm_volatility"]
        information_ratio = excess_return / algo_vol if algo_vol > 0 else 0.0

        return {
            "excess_return": excess_return,
            "alpha": alpha,
            "beta": beta,
            "information_ratio": information_ratio,
        }
