# =========================
# backend/application/use_cases/simulation_unified_uc.py
# =========================
from __future__ import annotations
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from uuid import uuid4

from domain.ports.market_data import MarketDataRepo
from domain.ports.positions_repo import PositionsRepo
from domain.ports.events_repo import EventsRepo
from domain.ports.dividend_market_data import DividendMarketDataRepo
from domain.entities.market_data import SimulationData
from domain.entities.position import Position
from domain.entities.dividend import Dividend
from domain.value_objects.order_policy import OrderPolicy
from domain.value_objects.guardrails import GuardrailPolicy
from application.use_cases.evaluate_position_uc import EvaluatePositionUC
from application.use_cases.submit_order_uc import SubmitOrderUC
from application.use_cases.execute_order_uc import ExecuteOrderUC
from application.dto.orders import CreateOrderRequest, FillOrderRequest
from infrastructure.persistence.memory.orders_repo_mem import InMemoryOrdersRepo
from infrastructure.persistence.memory.idempotency_repo_mem import InMemoryIdempotencyRepo
from infrastructure.time.clock import Clock


@dataclass
class SimulationResult:
    """Result of a trading simulation."""

    ticker: str
    start_date: datetime
    end_date: datetime
    total_trading_days: int
    initial_cash: float

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

    # Dividend data
    total_dividends_received: float
    dividend_events: List[Dict[str, Any]]

    # Market data for visualization
    price_data: List[Dict[str, Any]]

    # Trigger analysis
    trigger_analysis: List[Dict[str, Any]]

    # Debug info
    debug_storage_info: Optional[Dict[str, Any]] = None
    debug_retrieval_info: Optional[Dict[str, Any]] = None
    debug_info: Optional[List[Dict[str, Any]]] = None


class SimulationUnifiedUC:
    """Use case for running trading simulations using the actual trading logic."""

    def __init__(
        self,
        market_data: MarketDataRepo,
        positions: PositionsRepo,
        events: EventsRepo,
        clock: Clock,
        dividend_market_data: Optional[DividendMarketDataRepo] = None,
    ) -> None:
        self.market_data = market_data
        self.positions = positions
        self.events = events
        self.clock = clock
        self.dividend_market_data = dividend_market_data

    def run_simulation(
        self,
        ticker: str,
        start_date: datetime,
        end_date: datetime,
        initial_cash: float = 10000.0,
        position_config: Optional[Dict[str, Any]] = None,
        include_after_hours: bool = False,
    ) -> SimulationResult:
        """Run a complete trading simulation using actual trading use cases."""

        # Default position configuration
        if position_config is None:
            position_config = {
                "trigger_threshold_pct": 0.03,
                "rebalance_ratio": 0.5,
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
            print(
                f"Warning: Start date {start_date} is {days_ago} days in the past. yfinance may have limited data."
            )

        # Fetch historical data
        fetch_start = start_date - timedelta(days=1)  # Get one extra day for context
        fetch_end = end_date + timedelta(days=1)

        print(f"Fetching historical data for {ticker} from {fetch_start} to {fetch_end}")
        historical_data = self.market_data.fetch_historical_data(ticker, fetch_start, fetch_end)

        # Fetch dividend history if dividend market data is available
        dividend_history = []
        if self.dividend_market_data:
            print(f"Fetching dividend history for {ticker} from {fetch_start} to {fetch_end}")
            dividend_history = self.dividend_market_data.get_dividend_history(
                ticker, fetch_start, fetch_end
            )
            print(f"Found {len(dividend_history)} dividend events")

        # Store the fetched data in market data storage for simulation
        from infrastructure.market.market_data_storage import MarketDataStorage

        market_storage = MarketDataStorage()
        for price_data in historical_data:
            market_storage.store_price_data(ticker, price_data)

        # Debug: Check what data was stored
        debug_storage_info = {
            "stored_count": len(historical_data),
            "first_data": None,
            "last_data": None,
            "test_message": "DEBUG: Server is running updated code",
        }
        if historical_data:
            debug_storage_info["first_data"] = {
                "price": historical_data[0].price,
                "volume": historical_data[0].volume,
                "timestamp": historical_data[0].timestamp.isoformat(),
            }
            debug_storage_info["last_data"] = {
                "price": historical_data[-1].price,
                "volume": historical_data[-1].volume,
                "timestamp": historical_data[-1].timestamp.isoformat(),
            }

        # Get simulation data with minute-by-minute data for realistic trading simulation
        print(
            f"Getting minute-by-minute simulation data for {ticker} from {fetch_start} to {fetch_end}"
        )
        sim_data = market_storage.get_simulation_data(
            ticker, fetch_start, fetch_end, include_after_hours
        )

        # Debug: Check what data was retrieved
        debug_retrieval_info = {
            "retrieved_count": len(sim_data.price_data),
            "first_retrieved": None,
            "last_retrieved": None,
        }
        if sim_data.price_data:
            debug_retrieval_info["first_retrieved"] = {
                "price": sim_data.price_data[0].price,
                "volume": sim_data.price_data[0].volume,
                "timestamp": sim_data.price_data[0].timestamp.isoformat(),
            }
            debug_retrieval_info["last_retrieved"] = {
                "price": sim_data.price_data[-1].price,
                "volume": sim_data.price_data[-1].volume,
                "timestamp": sim_data.price_data[-1].timestamp.isoformat(),
            }

        print(
            f"Using {len(sim_data.price_data)} minute-by-minute data points for realistic simulation"
        )

        if not sim_data.price_data:
            raise ValueError(f"No price data available for {ticker} in the specified date range")

        # Convert price data to list of dictionaries for frontend
        price_data = []
        for data_point in sim_data.price_data:
            price_data.append(
                {
                    "timestamp": data_point.timestamp.isoformat(),
                    "price": data_point.price,
                    "volume": data_point.volume,
                }
            )

        # Run algorithm simulation using actual trading logic
        algo_result = self._simulate_algorithm_unified(
            sim_data, initial_cash, position_config, dividend_history, market_storage
        )

        # Run buy & hold simulation
        buy_hold_result = self._simulate_buy_hold(sim_data, initial_cash)

        # Calculate comparison metrics
        excess_return = algo_result["algorithm_return_pct"] - buy_hold_result["buy_hold_return_pct"]
        alpha = excess_return  # Simplified alpha calculation
        beta = 1.0  # Simplified beta calculation
        information_ratio = (
            excess_return / algo_result["algorithm_volatility"]
            if algo_result["algorithm_volatility"] > 0
            else 0
        )

        # Extract trigger_analysis from algo_result to avoid duplicate parameter
        trigger_analysis = algo_result.pop("trigger_analysis", [])

        return SimulationResult(
            ticker=ticker,
            start_date=start_date,
            end_date=end_date,
            total_trading_days=sim_data.total_trading_days,
            initial_cash=initial_cash,
            price_data=price_data,
            trigger_analysis=trigger_analysis,
            debug_storage_info=debug_storage_info,
            debug_retrieval_info=debug_retrieval_info,
            debug_info=algo_result.pop("debug_info", []),
            **algo_result,
            **buy_hold_result,
            excess_return=excess_return,
            alpha=alpha,
            beta=beta,
            information_ratio=information_ratio,
        )

    def _simulate_algorithm_unified(
        self,
        sim_data: SimulationData,
        initial_cash: float,
        position_config: Dict[str, Any],
        dividend_history: List[Dividend] = None,
        market_storage: MarketDataStorage = None,
    ) -> Dict[str, Any]:
        """Simulate the volatility balancing algorithm using the actual trading use cases."""
        from infrastructure.persistence.memory.positions_repo_mem import InMemoryPositionsRepo
        from infrastructure.persistence.memory.events_repo_mem import InMemoryEventsRepo

        # Create temporary repositories for simulation
        temp_positions = InMemoryPositionsRepo()
        temp_orders = InMemoryOrdersRepo()
        temp_events = InMemoryEventsRepo()
        temp_idempotency = InMemoryIdempotencyRepo()

        # Create use cases with temporary repositories
        # Use the market_storage that has the data, or fall back to self.market_data
        market_data_source = market_storage if market_storage else self.market_data
        evaluate_uc = EvaluatePositionUC(
            positions=temp_positions,
            events=temp_events,
            market_data=market_data_source,
            clock=self.clock,
        )
        submit_uc = SubmitOrderUC(
            positions=temp_positions,
            orders=temp_orders,
            idempotency=temp_idempotency,
            events=temp_events,
            clock=self.clock,
        )
        execute_uc = ExecuteOrderUC(
            positions=temp_positions, orders=temp_orders, events=temp_events, clock=self.clock
        )

        # Create a temporary position for simulation
        position_id = f"sim_{uuid4().hex[:8]}"
        order_policy = OrderPolicy(
            trigger_threshold_pct=position_config["trigger_threshold_pct"],
            rebalance_ratio=position_config["rebalance_ratio"],
            commission_rate=position_config["commission_rate"],
            min_notional=position_config["min_notional"],
            allow_after_hours=position_config["allow_after_hours"],
        )
        guardrails = GuardrailPolicy(
            min_stock_alloc_pct=position_config["guardrails"]["min_stock_alloc_pct"],
            max_stock_alloc_pct=position_config["guardrails"]["max_stock_alloc_pct"],
            max_orders_per_day=100,  # Allow more orders for simulation
        )

        position = Position(
            id=position_id,
            ticker=sim_data.ticker,
            qty=0.0,
            cash=initial_cash,
            order_policy=order_policy,
            guardrails=guardrails,
        )
        temp_positions.save(position)

        # Track simulation state
        trade_log = []
        portfolio_values = []
        daily_returns = []
        dividend_events = []
        total_dividends_received = 0.0
        current_simulation_day = None
        trigger_analysis = []  # Track all trigger evaluations
        debug_info = []  # Track debug information

        for price_data in sim_data.price_data:
            current_price = price_data.price
            current_time = price_data.timestamp
            current_day = current_time.date()

            # Debug: Collect first few price data points
            if len(trigger_analysis) < 3:
                debug_info.append(
                    {
                        "iteration": len(trigger_analysis),
                        "price": current_price,
                        "volume": getattr(price_data, "volume", "N/A"),
                        "timestamp": current_time.isoformat(),
                        "price_data_attrs": [
                            attr for attr in dir(price_data) if not attr.startswith("_")
                        ],
                        "price_data_dict": {
                            k: v for k, v in price_data.__dict__.items() if not k.startswith("_")
                        },
                    }
                )

            # Reset daily order count for new simulation day
            if current_simulation_day != current_day:
                current_simulation_day = current_day
                # Clear daily order count by creating new repositories for each day
                temp_orders = InMemoryOrdersRepo()
                temp_idempotency = InMemoryIdempotencyRepo()
                # Recreate use cases with fresh repositories
                submit_uc = SubmitOrderUC(
                    positions=temp_positions,
                    orders=temp_orders,
                    idempotency=temp_idempotency,
                    events=temp_events,
                    clock=self.clock,
                )
                execute_uc = ExecuteOrderUC(
                    positions=temp_positions,
                    orders=temp_orders,
                    events=temp_events,
                    clock=self.clock,
                )
                print(f"New simulation day: {current_day}")

            # Set anchor price on first evaluation
            if position.anchor_price is None:
                position.set_anchor_price(current_price)
                temp_positions.save(position)
                continue

            # Check for dividend events on this date
            if dividend_history:
                current_date = current_time.date()
                for dividend in dividend_history:
                    if dividend.ex_date.date() == current_date and position.qty > 0:
                        # Process ex-dividend date
                        old_anchor = position.anchor_price
                        position.adjust_anchor_for_dividend(float(dividend.dps))

                        # Calculate dividend receivable
                        gross_amount = dividend.calculate_gross_amount(position.qty)
                        net_amount = dividend.calculate_net_amount(position.qty)

                        # Add to cash (simplified - in real system this would be a receivable)
                        position.cash += float(net_amount)
                        total_dividends_received += float(net_amount)

                        # Log dividend event
                        dividend_events.append(
                            {
                                "date": current_date.isoformat(),
                                "ex_date": dividend.ex_date.isoformat(),
                                "pay_date": dividend.pay_date.isoformat(),
                                "dps": float(dividend.dps),
                                "shares": position.qty,
                                "gross_amount": float(gross_amount),
                                "net_amount": float(net_amount),
                                "withholding_tax": float(
                                    dividend.calculate_withholding_tax(position.qty)
                                ),
                                "old_anchor": old_anchor,
                                "new_anchor": position.anchor_price,
                            }
                        )

                        print(
                            f"Dividend processed: {dividend.dps} per share on {current_date}, net amount: ${net_amount:.2f}"
                        )

                        # Update position in repository
                        temp_positions.save(position)

            # Track trigger analysis
            # Debug: Check price_data attributes (only for first few iterations)
            debug_price_data = {}
            if len(trigger_analysis) < 3:
                debug_price_data = {
                    "has_volume": hasattr(price_data, "volume"),
                    "volume_value": getattr(price_data, "volume", "NO_VOLUME_ATTR"),
                    "price_data_type": type(price_data).__name__,
                    "price_data_dict": (
                        str(price_data.__dict__) if hasattr(price_data, "__dict__") else "NO_DICT"
                    ),
                }

            trigger_info = {
                "timestamp": current_time.isoformat(),
                "date": current_time.strftime("%Y-%m-%d"),
                "time": current_time.strftime("%H:%M:%S"),
                "price": current_price,  # Mid-quote used for trading
                "bid": current_price - current_price * 0.0005,  # Bid price with 0.05% spread
                "ask": current_price + current_price * 0.0005,  # Ask price with 0.05% spread
                "open": getattr(price_data, "open", current_price),  # Daily open price
                "high": getattr(price_data, "high", current_price),  # Daily high price
                "low": getattr(price_data, "low", current_price),  # Daily low price
                "close": getattr(price_data, "close", current_price),  # Daily close price
                "volume": (getattr(price_data, "volume", 0)),
                "debug_price_data": debug_price_data,
                "anchor_price": position.anchor_price,
                "price_change_pct": (
                    ((current_price / position.anchor_price) - 1) * 100
                    if position.anchor_price
                    else 0
                ),
                "trigger_threshold": position.order_policy.trigger_threshold_pct * 100,
                "triggered": False,
                "side": None,
                "qty": 0,
                "reason": "No trigger",
                "executed": False,
                "execution_error": None,
                "cash_after": position.cash,
                "shares_after": position.qty,
                "dividend": 0.0,
            }

            # Evaluate position using the actual trading logic
            try:
                evaluation = evaluate_uc.evaluate(position_id, current_price)

                if evaluation["trigger_detected"] and evaluation["order_proposal"]:
                    order_proposal = evaluation["order_proposal"]
                    trigger_info.update(
                        {
                            "triggered": True,
                            "side": order_proposal["side"],
                            "qty": order_proposal["trimmed_qty"],
                            "reason": "Trigger condition met",
                        }
                    )

                    # Submit order using actual trading logic
                    order_request = CreateOrderRequest(
                        side=order_proposal["side"], qty=abs(order_proposal["trimmed_qty"])
                    )

                    try:
                        submit_response = submit_uc.execute(
                            position_id, order_request, f"sim_{current_time.timestamp()}"
                        )

                        if submit_response.accepted:
                            # Execute order using actual trading logic
                            fill_request = FillOrderRequest(
                                qty=abs(order_proposal["trimmed_qty"]),
                                price=current_price,
                                commission=order_proposal["commission"],
                            )

                            try:
                                fill_response = execute_uc.execute(
                                    submit_response.order_id, fill_request
                                )

                                if fill_response.status == "filled":
                                    # Update position reference
                                    position = temp_positions.get(position_id)

                                    # Log the trade
                                    trade_log.append(
                                        {
                                            "timestamp": current_time.isoformat(),
                                            "side": order_proposal["side"],
                                            "qty": order_proposal["trimmed_qty"],
                                            "price": current_price,
                                            "commission": order_proposal["commission"],
                                            "cash_after": position.cash,
                                            "shares_after": position.qty,
                                        }
                                    )

                                    # Mark as executed
                                    trigger_info.update(
                                        {
                                            "executed": True,
                                            "commission": order_proposal["commission"],
                                            "cash_after": position.cash,
                                            "shares_after": position.qty,
                                        }
                                    )

                            except Exception as e:
                                # Order execution failed - continue simulation
                                trigger_info.update(
                                    {"executed": False, "execution_error": f"Execution failed: {e}"}
                                )
                                print(f"Order execution failed: {e}")
                        else:
                            trigger_info.update(
                                {
                                    "executed": False,
                                    "execution_error": f"Order not accepted: {submit_response}",
                                }
                            )

                    except Exception as e:
                        # Order submission failed - continue simulation
                        trigger_info.update(
                            {"executed": False, "execution_error": f"Submission failed: {e}"}
                        )
                        print(f"Order submission failed: {e}")
                else:
                    # No trigger - check why
                    if abs(trigger_info["price_change_pct"]) < trigger_info["trigger_threshold"]:
                        trigger_info["reason"] = (
                            f"Price change {trigger_info['price_change_pct']:.2f}% below threshold {trigger_info['trigger_threshold']:.2f}%"
                        )
                    else:
                        trigger_info["reason"] = "Other evaluation conditions not met"

            except Exception as e:
                # Evaluation failed - continue simulation
                trigger_info.update(
                    {"executed": False, "execution_error": f"Evaluation failed: {e}"}
                )
                print(f"Position evaluation failed: {e}")

            # Add trigger analysis
            trigger_analysis.append(trigger_info)

            # Calculate portfolio value
            portfolio_value = position.cash + (position.qty * current_price)
            portfolio_values.append(portfolio_value)

            # Debug logging
            if len(portfolio_values) % 10 == 0:  # Log every 10th day
                print(
                    f"Day {len(portfolio_values)}: Cash=${position.cash:.2f}, Qty={position.qty:.2f}, Price=${current_price:.2f}, Portfolio=${portfolio_value:.2f}"
                )

            # Calculate daily returns
            if len(portfolio_values) > 1:
                daily_return = (portfolio_values[-1] / portfolio_values[-2]) - 1
                daily_returns.append(
                    {
                        "date": current_time.date().isoformat(),
                        "return": daily_return,
                        "portfolio_value": portfolio_value,
                        "cash": position.cash,
                        "shares": position.qty,  # Use qty instead of shares
                        "stock_value": position.qty * current_price,
                        "price": current_price,
                    }
                )

        # Calculate final metrics
        final_value = portfolio_values[-1] if portfolio_values else initial_cash
        total_return = (final_value - initial_cash) / initial_cash

        # Debug logging
        print("Algorithm simulation complete:")
        print(f"  Initial cash: ${initial_cash:.2f}")
        print(f"  Final value: ${final_value:.2f}")
        print(f"  Total return: {total_return * 100:.2f}%")
        print(f"  Portfolio values count: {len(portfolio_values)}")
        if portfolio_values:
            print(f"  First portfolio value: ${portfolio_values[0]:.2f}")
            print(f"  Last portfolio value: ${portfolio_values[-1]:.2f}")

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
            "total_dividends_received": total_dividends_received,
            "dividend_events": dividend_events,
            "trigger_analysis": trigger_analysis,
            "debug_info": debug_info,  # Add debug information
        }

    def _simulate_buy_hold(self, sim_data: SimulationData, initial_cash: float) -> Dict[str, Any]:
        """Simulate buy and hold strategy."""
        if not sim_data.price_data:
            return {
                "buy_hold_trades": 0,
                "buy_hold_pnl": 0.0,
                "buy_hold_return_pct": 0.0,
                "buy_hold_volatility": 0.0,
                "buy_hold_sharpe_ratio": 0.0,
                "buy_hold_max_drawdown": 0.0,
            }

        # Buy at first price
        first_price = sim_data.price_data[0].price
        shares = initial_cash / first_price
        cash = 0.0

        # Track portfolio values
        portfolio_values = []
        daily_returns = []

        for price_data in sim_data.price_data:
            current_price = price_data.price
            portfolio_value = cash + (shares * current_price)
            portfolio_values.append(portfolio_value)

            # Calculate daily returns
            if len(portfolio_values) > 1:
                daily_return = (portfolio_values[-1] / portfolio_values[-2]) - 1
                daily_returns.append(
                    {
                        "date": price_data.timestamp.date().isoformat(),
                        "return": daily_return,
                        "portfolio_value": portfolio_value,
                    }
                )

        # Calculate final metrics
        final_value = portfolio_values[-1] if portfolio_values else initial_cash
        total_return = (final_value - initial_cash) / initial_cash
        volatility = self._calculate_volatility([r["return"] for r in daily_returns])
        sharpe_ratio = self._calculate_sharpe_ratio(daily_returns)
        max_drawdown = self._calculate_max_drawdown(portfolio_values)

        return {
            "buy_hold_pnl": final_value - initial_cash,
            "buy_hold_return_pct": total_return * 100,
            "buy_hold_volatility": volatility,
            "buy_hold_sharpe_ratio": sharpe_ratio,
            "buy_hold_max_drawdown": max_drawdown,
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

        # Annualized Sharpe ratio (assuming 252 trading days)
        return (mean_return * 252) / (std_return * (252**0.5))

    def _calculate_max_drawdown(self, portfolio_values: List[float]) -> float:
        """Calculate maximum drawdown."""
        if not portfolio_values:
            return 0.0

        peak = portfolio_values[0]
        max_dd = 0.0

        for value in portfolio_values:
            if value > peak:
                peak = value
            drawdown = (peak - value) / peak
            max_dd = max(max_dd, drawdown)

        return max_dd * 100  # Return as percentage
