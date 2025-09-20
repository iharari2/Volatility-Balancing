# =========================
# backend/application/use_cases/simulation_uc.py
# =========================
from __future__ import annotations
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import threading

from domain.ports.market_data import MarketDataRepo
from domain.ports.positions_repo import PositionsRepo
from domain.ports.events_repo import EventsRepo
from domain.entities.market_data import SimulationData
from infrastructure.time.clock import Clock
from infrastructure.cache.simulation_cache import simulation_cache


@dataclass
class SimulationProgress:
    """Progress tracking for simulation."""

    status: str  # "initializing", "fetching_data", "processing", "completed", "error"
    progress: float  # 0.0 to 1.0
    message: str
    current_step: str
    total_steps: int
    completed_steps: int
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    error: Optional[str] = None


class SimulationProgressTracker:
    """Thread-safe progress tracker for simulations."""

    def __init__(self):
        self._progress: Dict[str, SimulationProgress] = {}
        self._lock = threading.Lock()

    def update_progress(self, simulation_id: str, progress: SimulationProgress):
        """Update progress for a simulation."""
        with self._lock:
            self._progress[simulation_id] = progress

    def get_progress(self, simulation_id: str) -> Optional[SimulationProgress]:
        """Get current progress for a simulation."""
        with self._lock:
            return self._progress.get(simulation_id)

    def clear_progress(self, simulation_id: str):
        """Clear progress for a simulation."""
        with self._lock:
            self._progress.pop(simulation_id, None)


# Global progress tracker
_progress_tracker = SimulationProgressTracker()


def get_simulation_progress(simulation_id: str) -> Optional[SimulationProgress]:
    """Get progress for a simulation."""
    return _progress_tracker.get_progress(simulation_id)


def clear_simulation_progress(simulation_id: str):
    """Clear progress for a simulation."""
    _progress_tracker.clear_progress(simulation_id)


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

    # Market data for visualization
    price_data: List[Dict[str, Any]]

    # Dividend analysis
    dividend_analysis: Dict[str, Any]


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
        initial_asset_value: Optional[float] = None,
        initial_asset_units: Optional[float] = None,
        simulation_id: Optional[str] = None,
    ) -> SimulationResult:
        """Run a complete trading simulation."""

        # Check cache first
        config_key = {
            "ticker": ticker,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "initial_cash": initial_cash,
            "initial_asset_value": initial_asset_value,
            "initial_asset_units": initial_asset_units,
            "position_config": position_config,
            "include_after_hours": include_after_hours,
        }

        cached_result = simulation_cache.get(config_key)
        if cached_result:
            print(f"Cache hit for simulation {ticker} {start_date} to {end_date}")
            return cached_result

        # Initialize progress tracking
        if simulation_id:
            _progress_tracker.update_progress(
                simulation_id,
                SimulationProgress(
                    status="initializing",
                    progress=0.0,
                    message="Initializing simulation...",
                    current_step="setup",
                    total_steps=5,
                    completed_steps=0,
                    start_time=datetime.now(timezone.utc),
                ),
            )

        # Default position configuration
        if position_config is None:
            position_config = {
                "trigger_threshold_pct": 0.03,
                "rebalance_ratio": 1.6667,
                "commission_rate": 0.0001,
                "min_notional": 100.0,
                "allow_after_hours": True,  # Default to after hours ON
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

        # Validate date range
        now = datetime.now(timezone.utc)
        if start_date > now:
            raise ValueError(f"Start date {start_date} cannot be in the future")
        if end_date > now:
            raise ValueError(f"End date {end_date} cannot be in the future")
        if start_date >= end_date:
            raise ValueError(f"Start date {start_date} must be before end date {end_date}")

        # Check if dates are too far in the past (yfinance limitation)
        days_ago = (now - end_date).days
        if days_ago > 30:
            raise ValueError(
                f"End date {end_date} is too far in the past. yfinance only supports data from the last 30 days"
            )

        # Check if start date is too far in the past
        start_days_ago = (now - start_date).days
        if start_days_ago > 30:
            print(
                f"Warning: Start date {start_date} is {start_days_ago} days in the past. yfinance may have limited data."
            )
            # Don't raise error, just warn

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

        # Update progress - fetching data
        if simulation_id:
            _progress_tracker.update_progress(
                simulation_id,
                SimulationProgress(
                    status="fetching_data",
                    progress=0.2,
                    message=f"Fetching historical data for {ticker}...",
                    current_step="data_fetch",
                    total_steps=5,
                    completed_steps=1,
                    start_time=datetime.now(timezone.utc),
                ),
            )

        print(f"Fetching historical data for {ticker} from {fetch_start} to {fetch_end}")
        historical_data = self.market_data.fetch_historical_data(ticker, fetch_start, fetch_end)

        if not historical_data:
            if simulation_id:
                _progress_tracker.update_progress(
                    simulation_id,
                    SimulationProgress(
                        status="error",
                        progress=0.0,
                        message=f"No price data available for {ticker} in date range",
                        current_step="data_fetch",
                        total_steps=5,
                        completed_steps=1,
                        error=f"No price data available for {ticker} in date range",
                    ),
                )
            raise ValueError(f"No price data available for {ticker} in date range")

        # Store the fetched data in market data storage for simulation
        from infrastructure.market.market_data_storage import MarketDataStorage

        market_storage = MarketDataStorage()
        for price_data in historical_data:
            market_storage.store_price_data(ticker, price_data)

        # Get simulation data using the stored data
        print(f"Getting simulation data for {ticker} from {fetch_start} to {fetch_end}")
        sim_data = market_storage.get_simulation_data(
            ticker, fetch_start, fetch_end, include_after_hours
        )

        if not sim_data.price_data:
            raise ValueError(f"No price data available for {ticker} in date range")

        # Update progress - processing simulation
        if simulation_id:
            _progress_tracker.update_progress(
                simulation_id,
                SimulationProgress(
                    status="processing",
                    progress=0.4,
                    message="Running algorithm simulation...",
                    current_step="algorithm_sim",
                    total_steps=5,
                    completed_steps=2,
                    start_time=datetime.now(timezone.utc),
                ),
            )

        # Run algorithm simulation
        algo_result = self._simulate_algorithm(
            sim_data, initial_cash, position_config, initial_asset_value, initial_asset_units
        )

        # Update progress - buy & hold simulation
        if simulation_id:
            _progress_tracker.update_progress(
                simulation_id,
                SimulationProgress(
                    status="processing",
                    progress=0.6,
                    message="Running buy & hold simulation...",
                    current_step="buy_hold_sim",
                    total_steps=5,
                    completed_steps=3,
                    start_time=datetime.now(timezone.utc),
                ),
            )

        # Run buy & hold simulation
        buy_hold_result = self._simulate_buy_hold(
            sim_data, initial_cash, initial_asset_value, initial_asset_units
        )

        # Update progress - finalizing results
        if simulation_id:
            _progress_tracker.update_progress(
                simulation_id,
                SimulationProgress(
                    status="processing",
                    progress=0.8,
                    message="Calculating final results...",
                    current_step="finalize",
                    total_steps=5,
                    completed_steps=4,
                    start_time=datetime.now(timezone.utc),
                ),
            )

        # Calculate comparison metrics
        comparison_metrics = self._calculate_comparison_metrics(algo_result, buy_hold_result)

        # Convert price data to API format
        price_data = [
            {
                "timestamp": p.timestamp.isoformat(),
                "price": p.price,
                "volume": getattr(p, "volume", 0),
                "is_market_hours": getattr(p, "is_market_hours", True),
            }
            for p in sim_data.price_data
        ]

        # Update progress - completed
        if simulation_id:
            _progress_tracker.update_progress(
                simulation_id,
                SimulationProgress(
                    status="completed",
                    progress=1.0,
                    message="Simulation completed successfully!",
                    current_step="completed",
                    total_steps=5,
                    completed_steps=5,
                    start_time=datetime.now(timezone.utc),
                    end_time=datetime.now(timezone.utc),
                ),
            )

        # Calculate dividend analysis
        dividend_analysis = self._calculate_dividend_analysis(ticker, start_date, end_date)

        result = SimulationResult(
            ticker=ticker,
            start_date=start_date,
            end_date=end_date,
            total_trading_days=sim_data.total_trading_days,
            price_data=price_data,
            dividend_analysis=dividend_analysis,
            **algo_result,
            **buy_hold_result,
            **comparison_metrics,
        )

        # Cache the result
        simulation_cache.put(config_key, result)
        print(f"Cached simulation result for {ticker} {start_date} to {end_date}")

        return result

    def _simulate_algorithm(
        self,
        sim_data: SimulationData,
        initial_cash: float,
        position_config: Dict[str, Any],
        initial_asset_value: Optional[float] = None,
        initial_asset_units: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Simulate the volatility trading algorithm."""

        # Initialize portfolio
        cash = initial_cash
        shares = 0.0
        anchor_price = None
        total_commission = 0.0

        # Handle initial asset allocation
        if initial_asset_value is not None and initial_asset_value > 0:
            # Use asset value to calculate shares at first price
            if sim_data.price_data:
                first_price = sim_data.price_data[0].price
                shares = initial_asset_value / first_price
                cash -= initial_asset_value
                anchor_price = first_price
        elif initial_asset_units is not None and initial_asset_units > 0:
            # Use specified number of units
            if sim_data.price_data:
                first_price = sim_data.price_data[0].price
                shares = initial_asset_units
                cost = shares * first_price
                cash -= cost
                anchor_price = first_price

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
                        if shares > 0:
                            # Normal sell: we have shares to sell
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
                        else:
                            # Special case: we have 0 shares but want to sell
                            # Convert this to a buy order (buy the absolute quantity)
                            buy_qty = abs(qty)
                            cost = buy_qty * current_price + commission
                            if cost <= cash:
                                cash -= cost
                                shares += buy_qty
                                total_commission += commission
                                anchor_price = current_price  # Update anchor after trade

                                trade_log.append(
                                    {
                                        "timestamp": current_time.isoformat(),
                                        "side": "BUY",  # Convert sell to buy
                                        "qty": buy_qty,
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

    def _simulate_buy_hold(
        self,
        sim_data: SimulationData,
        initial_cash: float,
        initial_asset_value: Optional[float] = None,
        initial_asset_units: Optional[float] = None,
    ) -> Dict[str, Any]:
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

        # Calculate initial shares based on asset allocation
        if initial_asset_value is not None and initial_asset_value > 0:
            # Use asset value to calculate shares
            shares = initial_asset_value / start_price
            remaining_cash = initial_cash - initial_asset_value
            # Buy additional shares with remaining cash
            additional_shares = remaining_cash / start_price
            shares += additional_shares
        elif initial_asset_units is not None and initial_asset_units > 0:
            # Use specified number of units
            shares = initial_asset_units
            cost = shares * start_price
            remaining_cash = initial_cash - cost
            # Buy additional shares with remaining cash
            additional_shares = remaining_cash / start_price
            shares += additional_shares
        else:
            # Standard buy and hold - buy all at start
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

        # Apply order sizing formula: ΔQ_raw = (P_anchor / P - 1) × r × ((A + C) / P)
        rebalance_ratio = config["rebalance_ratio"]

        raw_qty = (
            (anchor_price / current_price - 1) * rebalance_ratio * (total_value / current_price)
        )

        # Apply side based on trigger direction
        if current_price < anchor_price * (1 - config["trigger_threshold_pct"]):
            # BUY trigger: keep positive
            pass
        else:
            # SELL trigger: make negative
            raw_qty = -raw_qty

        # raw_qty is already correctly signed from the calculation above

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
            # Allow selling if we have shares OR if this is the first trade (shares = 0)
            # In the latter case, we'll convert it to a buy order
            valid = abs(raw_qty) <= shares or shares == 0

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

    def _calculate_dividend_analysis(
        self, ticker: str, start_date: datetime, end_date: datetime
    ) -> Dict[str, Any]:
        """Calculate dividend analysis for the simulation period."""
        try:
            # Get dividend history for the period
            from infrastructure.market.yfinance_dividend_adapter import YFinanceDividendAdapter

            dividend_adapter = YFinanceDividendAdapter()
            dividends = dividend_adapter.get_dividend_history(ticker, start_date, end_date)

            if not dividends:
                return {
                    "total_dividends": 0,
                    "dividend_yield": 0.0,
                    "dividend_count": 0,
                    "total_dividend_amount": 0.0,
                    "dividends": [],
                    "message": "No dividends found for this period",
                }

            # Calculate metrics
            total_dividend_amount = sum(float(div.dps) for div in dividends)
            dividend_count = len(dividends)

            # Get average price for yield calculation
            from infrastructure.market.yfinance_adapter import YFinanceAdapter

            market_adapter = YFinanceAdapter()
            price_data = market_adapter.get_historical_data(ticker, start_date, end_date)

            avg_price = 0.0
            if price_data and price_data.price_data:
                prices = [float(p.price) for p in price_data.price_data]
                avg_price = sum(prices) / len(prices) if prices else 0.0

            dividend_yield = (total_dividend_amount / avg_price * 100) if avg_price > 0 else 0.0

            # Format dividend data
            dividend_list = []
            for div in dividends:
                dividend_list.append(
                    {
                        "ex_date": div.ex_date.isoformat(),
                        "pay_date": div.pay_date.isoformat(),
                        "dps": float(div.dps),
                        "currency": div.currency,
                        "withholding_tax_rate": div.withholding_tax_rate,
                    }
                )

            return {
                "total_dividends": total_dividend_amount,
                "dividend_yield": dividend_yield,
                "dividend_count": dividend_count,
                "total_dividend_amount": total_dividend_amount,
                "dividends": dividend_list,
                "message": f"Found {dividend_count} dividend(s) totaling ${total_dividend_amount:.4f} per share",
            }

        except Exception as e:
            print(f"Error calculating dividend analysis: {e}")
            return {
                "total_dividends": 0,
                "dividend_yield": 0.0,
                "dividend_count": 0,
                "total_dividend_amount": 0.0,
                "dividends": [],
                "message": f"Error calculating dividends: {str(e)}",
            }
