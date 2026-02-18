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
from domain.ports.simulation_repo import SimulationRepo
from domain.ports.evaluation_timeline_repo import EvaluationTimelineRepo
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
from infrastructure.persistence.memory.trades_repo_mem import InMemoryTradesRepo
from infrastructure.persistence.memory.config_repo_mem import InMemoryConfigRepo
from infrastructure.time.clock import Clock
from infrastructure.market.market_data_storage import MarketDataStorage
from typing import Callable


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

    # Comprehensive time-series data
    time_series_data: Optional[List[Dict[str, Any]]] = None

    # Dividend analysis
    dividend_analysis: Optional[Dict[str, Any]] = None


class SimulationUnifiedUC:
    """Use case for running trading simulations using the actual trading logic."""

    def __init__(
        self,
        market_data: MarketDataRepo,
        positions: PositionsRepo,
        events: EventsRepo,
        clock: Clock,
        dividend_market_data: Optional[DividendMarketDataRepo] = None,
        simulation_repo: Optional[SimulationRepo] = None,
        evaluation_timeline_repo: Optional[EvaluationTimelineRepo] = None,
    ) -> None:
        self.market_data = market_data
        self.positions = positions
        self.events = events
        self.clock = clock
        self.dividend_market_data = dividend_market_data
        self.simulation_repo = simulation_repo
        self.evaluation_timeline_repo = evaluation_timeline_repo

    def run_simulation(
        self,
        ticker: str,
        start_date: datetime,
        end_date: datetime,
        initial_cash: float = 10000.0,
        position_config: Optional[Dict[str, Any]] = None,
        include_after_hours: bool = False,
        intraday_interval_minutes: int = 30,
        detailed_trigger_analysis: bool = True,
        initial_asset_value: Optional[float] = None,
        initial_asset_units: Optional[float] = None,
        progress_callback: Optional[Callable[[str, float], None]] = None,
        simulation_id: Optional[str] = None,
        timeout_seconds: Optional[int] = None,
    ) -> SimulationResult:
        """Run a complete trading simulation using actual trading use cases."""

        # Progress tracking helper
        def report_progress(message: str, percentage: float):
            if progress_callback:
                progress_callback(message, percentage)
            print(f"[{percentage:5.1f}%] {message}")

            # Update progress tracker if simulation_id is provided
            if simulation_id:
                from application.use_cases.simulation_uc import (
                    _progress_tracker,
                    SimulationProgress,
                )
                from datetime import datetime, timezone

                status = "processing"
                if percentage >= 100:
                    status = "completed"
                elif percentage <= 0:
                    status = "initializing"

                _progress_tracker.update_progress(
                    simulation_id,
                    SimulationProgress(
                        status=status,
                        progress=percentage / 100.0,
                        message=message,
                        current_step="simulation",
                        total_steps=5,
                        completed_steps=int(percentage / 20),
                        start_time=datetime.now(timezone.utc),
                    ),
                )

        report_progress("Starting simulation...", 0.0)

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
        report_progress("Validating date range...", 5.0)
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

        # Cap fetch_end at current time to avoid requesting future data
        if fetch_end > now:
            fetch_end = now

        report_progress(f"Fetching historical data for {ticker}...", 10.0)
        print(f"Fetching historical data for {ticker} from {fetch_start} to {fetch_end}")
        try:
            historical_data = self.market_data.fetch_historical_data(
                ticker, fetch_start, fetch_end, intraday_interval_minutes
            )
        except Exception as e:
            raise Exception(f"Failed to fetch historical data for {ticker}: {str(e)}")

        if not historical_data:
            raise Exception(
                f"No historical data available for {ticker} from {fetch_start} to {fetch_end}"
            )

        # Fetch dividend history if dividend market data is available
        report_progress("Fetching dividend history...", 15.0)
        dividend_history = []
        if self.dividend_market_data:
            try:
                print(f"Fetching dividend history for {ticker} from {fetch_start} to {fetch_end}")
                dividend_history = self.dividend_market_data.get_dividend_history(
                    ticker, fetch_start, fetch_end
                )
                print(f"Found {len(dividend_history)} dividend events")
            except Exception as e:
                print(f"Warning: Failed to fetch dividend history for {ticker}: {str(e)}")
                dividend_history = []

        # Store the fetched data in market data storage for simulation
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
            sim_data,
            initial_cash,
            position_config,
            dividend_history,
            market_storage,
            detailed_trigger_analysis,
            initial_asset_value,
            initial_asset_units,
            report_progress,
            simulation_id=simulation_id,  # Pass simulation_id for timeline
            ticker=ticker,  # Pass ticker for timeline
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

        report_progress("Simulation completed successfully!", 100.0)

        # Calculate dividend analysis
        dividend_analysis = self._calculate_dividend_analysis(
            ticker, start_date, end_date, sim_data, algo_result
        )

        # Create simulation result
        result = SimulationResult(
            ticker=ticker,
            start_date=start_date,
            end_date=end_date,
            total_trading_days=sim_data.total_trading_days,
            initial_cash=initial_cash,
            price_data=price_data,
            trigger_analysis=trigger_analysis,
            time_series_data=algo_result.pop("time_series_data", []),
            debug_storage_info=debug_storage_info,
            debug_retrieval_info=debug_retrieval_info,
            debug_info=algo_result.pop("debug_info", []),
            **algo_result,
            **buy_hold_result,
            excess_return=excess_return,
            alpha=alpha,
            beta=beta,
            information_ratio=information_ratio,
            dividend_analysis=dividend_analysis,
        )

        # Save to repository if available
        if self.simulation_repo:
            try:
                # Convert to domain entity format for persistence
                from domain.entities.simulation_result import (
                    SimulationResult as DomainSimulationResult,
                )
                from uuid import uuid4

                domain_result = DomainSimulationResult(
                    id=uuid4(),
                    ticker=result.ticker,
                    start_date=result.start_date.isoformat(),
                    end_date=result.end_date.isoformat(),
                    total_trading_days=result.total_trading_days,
                    initial_cash=result.initial_cash,
                    algorithm_trades=result.algorithm_trades,
                    algorithm_pnl=result.algorithm_pnl,
                    algorithm_return_pct=result.algorithm_return_pct,
                    algorithm_volatility=result.algorithm_volatility,
                    algorithm_sharpe_ratio=result.algorithm_sharpe_ratio,
                    algorithm_max_drawdown=result.algorithm_max_drawdown,
                    buy_hold_pnl=result.buy_hold_pnl,
                    buy_hold_return_pct=result.buy_hold_return_pct,
                    buy_hold_volatility=result.buy_hold_volatility,
                    buy_hold_sharpe_ratio=result.buy_hold_sharpe_ratio,
                    buy_hold_max_drawdown=result.buy_hold_max_drawdown,
                    excess_return=result.excess_return,
                    alpha=result.alpha,
                    beta=result.beta,
                    information_ratio=result.information_ratio,
                    trade_log=result.trade_log,
                    daily_returns=result.daily_returns,
                    dividend_analysis=result.dividend_analysis,
                    price_data=result.price_data,
                    trigger_analysis=result.trigger_analysis,
                    time_series_data=result.time_series_data,
                    debug_info=result.debug_info,
                )

                self.simulation_repo.save_simulation_result(domain_result)
                print(f"Simulation result saved with ID: {domain_result.id}")
            except Exception as e:
                print(f"Warning: Failed to save simulation result: {e}")

        return result

    def run_simulation_with_data(
        self,
        ticker: str,
        start_date: datetime,
        end_date: datetime,
        historical_data: list,
        sim_data: SimulationData,
        dividend_history: list,
        initial_cash: float = 10000.0,
        position_config: Optional[Dict[str, Any]] = None,
        lightweight: bool = False,
    ) -> SimulationResult:
        """Run simulation with pre-fetched market data.

        This avoids redundant data fetching when running multiple simulations
        over the same date range (e.g., parameter optimization).

        When lightweight=True, skips heavy collections (time_series_data,
        trigger_analysis, price_data, debug info) and does not save to repo.
        """
        # Default position configuration
        if position_config is None:
            position_config = {
                "trigger_threshold_pct": 0.03,
                "rebalance_ratio": 1.6667,
                "commission_rate": 0.0001,
                "min_notional": 100.0,
                "allow_after_hours": True,
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

        if not sim_data.price_data:
            raise ValueError(f"No price data available for {ticker} in the specified date range")

        # Build a fresh MarketDataStorage from the provided historical data
        market_storage = MarketDataStorage()
        for price_point in historical_data:
            market_storage.store_price_data(ticker, price_point)

        # Run algorithm simulation
        algo_result = self._simulate_algorithm_unified(
            sim_data,
            initial_cash,
            position_config,
            dividend_history,
            market_storage,
            detailed_trigger_analysis=not lightweight,
            report_progress=None,
            simulation_id=None,
            ticker=ticker,
        )

        # Run buy & hold simulation
        buy_hold_result = self._simulate_buy_hold(sim_data, initial_cash)

        # Calculate comparison metrics
        excess_return = algo_result["algorithm_return_pct"] - buy_hold_result["buy_hold_return_pct"]
        alpha = excess_return
        beta = 1.0
        information_ratio = (
            excess_return / algo_result["algorithm_volatility"]
            if algo_result["algorithm_volatility"] > 0
            else 0
        )

        trigger_analysis = algo_result.pop("trigger_analysis", [])
        time_series_data = algo_result.pop("time_series_data", [])
        debug_info = algo_result.pop("debug_info", [])

        # In lightweight mode, discard heavy collections
        if lightweight:
            trigger_analysis = []
            time_series_data = []
            debug_info = []

        result = SimulationResult(
            ticker=ticker,
            start_date=start_date,
            end_date=end_date,
            total_trading_days=sim_data.total_trading_days,
            initial_cash=initial_cash,
            price_data=[],  # Skip in lightweight
            trigger_analysis=trigger_analysis,
            time_series_data=time_series_data,
            debug_storage_info=None,
            debug_retrieval_info=None,
            debug_info=debug_info,
            **algo_result,
            **buy_hold_result,
            excess_return=excess_return,
            alpha=alpha,
            beta=beta,
            information_ratio=information_ratio,
            dividend_analysis=None,  # Skip expensive dividend re-fetch
        )

        return result

    def _simulate_algorithm_unified(
        self,
        sim_data: SimulationData,
        initial_cash: float,
        position_config: Dict[str, Any],
        dividend_history: List[Dividend] = None,
        market_storage: MarketDataStorage = None,
        detailed_trigger_analysis: bool = False,  # Default to False for better performance
        initial_asset_value: Optional[float] = None,
        initial_asset_units: Optional[float] = None,
        report_progress: Optional[Callable[[str, float], None]] = None,
        simulation_id: Optional[str] = None,
        ticker: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Simulate the volatility balancing algorithm using the actual trading use cases."""
        from infrastructure.persistence.memory.positions_repo_mem import InMemoryPositionsRepo
        from infrastructure.persistence.memory.events_repo_mem import InMemoryEventsRepo

        # Safe progress reporting wrapper
        def safe_report_progress(message: str, percentage: float):
            if report_progress:
                try:
                    report_progress(message, percentage)
                except Exception:
                    pass  # Ignore progress reporting errors

        # Create temporary repositories for simulation
        temp_positions = InMemoryPositionsRepo()
        temp_orders = InMemoryOrdersRepo()
        temp_trades = InMemoryTradesRepo()
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
            evaluation_timeline_repo=self.evaluation_timeline_repo,  # Pass timeline repo for simulation
            # Simulation runs on a synthetic portfolio; after-hours is controlled by include_after_hours.
            # We intentionally do NOT pass portfolio_repo here.
        )
        # Create in-memory config repo for simulation
        temp_config = InMemoryConfigRepo()

        submit_uc = SubmitOrderUC(
            positions=temp_positions,
            orders=temp_orders,
            idempotency=temp_idempotency,
            events=temp_events,
            config_repo=temp_config,
            clock=self.clock,
        )
        execute_uc = ExecuteOrderUC(
            positions=temp_positions,
            orders=temp_orders,
            trades=temp_trades,
            events=temp_events,
            clock=self.clock,
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
            max_orders_per_day=999999,  # Unlimited for simulation (clock uses real date, not sim date)
        )

        # Calculate initial position based on asset allocation
        # Default to 50/50 split if no asset value/units specified
        initial_qty = 0.0
        initial_cash_after_asset = initial_cash

        if sim_data.price_data:
            first_price = sim_data.price_data[0].price
            if first_price <= 0:
                raise ValueError(f"Invalid first price: {first_price}")

            if initial_asset_value is not None and initial_asset_value > 0:
                # Use asset value to calculate shares at first price
                initial_qty = initial_asset_value / first_price
                initial_cash_after_asset = initial_cash
            elif initial_asset_units is not None and initial_asset_units > 0:
                # Use specified number of units
                initial_qty = initial_asset_units
                initial_cash_after_asset = initial_cash
            else:
                # Default: 50/50 split between cash and shares
                # Total value = initial_cash, split equally
                half_value = initial_cash / 2.0
                initial_qty = half_value / first_price
                initial_cash_after_asset = half_value
                print(f"Using default 50/50 split: {initial_qty:.4f} shares @ ${first_price:.2f} + ${initial_cash_after_asset:.2f} cash")

        position = Position(
            id=position_id,
            tenant_id="simulation",  # Simulation uses a synthetic tenant
            portfolio_id="simulation",  # Simulation uses a synthetic portfolio
            asset_symbol=sim_data.ticker,  # Use asset_symbol, not ticker
            qty=initial_qty,
            cash=initial_cash_after_asset,
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
        time_series_data = []  # Track comprehensive time-series data

        safe_report_progress("Starting simulation loop...", 20.0)
        total_data_points = len(sim_data.price_data)
        processed_points = 0

        # Optimize progress updates - only update every 10% for better performance
        update_frequency = max(1, total_data_points // 10)
        if update_frequency < 50:
            update_frequency = 50

        for price_data in sim_data.price_data:
            current_price = price_data.price
            # Ensure timestamp is Python datetime, not pandas Timestamp
            current_time = price_data.timestamp
            if hasattr(current_time, 'to_pydatetime'):
                current_time = current_time.to_pydatetime()
            current_day = current_time.date()

            # Update the market_storage price cache so get_price() returns current simulation price
            if market_data_source and hasattr(market_data_source, 'store_price_data'):
                market_data_source.store_price_data(sim_data.ticker, price_data)

            # Update progress less frequently for better performance
            processed_points += 1
            if processed_points % update_frequency == 0 or processed_points == total_data_points:
                progress_pct = 20.0 + (processed_points / total_data_points) * 70.0  # 20-90% range
                safe_report_progress(
                    f"Processing data point {processed_points}/{total_data_points} ({progress_pct:.1f}%)...",
                    progress_pct,
                )

            # Only collect minimal debug info for first iteration
            if len(trigger_analysis) == 0:
                debug_info.append(
                    {
                        "iteration": 0,
                        "price": current_price,
                        "timestamp": current_time.isoformat(),
                    }
                )

            # Reset daily order count for new simulation day
            if current_simulation_day != current_day:
                current_simulation_day = current_day
                # Optimize: Just clear the daily order count instead of recreating repositories
                # This is much faster than recreating all repositories and use cases
                # daily_order_count = 0  # Not needed for current implementation
                # Only print for first few days to reduce logging overhead
                if len(trigger_analysis) < 100:
                    print(f"New simulation day: {current_day}")

            # Set anchor price on first evaluation
            if position.anchor_price is None:
                position.set_anchor_price(current_price)
                temp_positions.save(position)

                # Collect initial time-series data point
                time_series_data.append(
                    {
                        "timestamp": current_time.isoformat(),
                        "date": current_time.strftime("%Y-%m-%d"),
                        "time": current_time.strftime("%H:%M:%S"),
                        "price": current_price,
                        "volume": getattr(price_data, "volume", 0),
                        "is_market_hours": getattr(price_data, "is_market_hours", True),
                        "anchor_price": position.anchor_price,
                        "shares": position.qty,
                        "cash": position.cash,
                        "asset_value": position.qty * current_price,
                        "total_value": position.cash + (position.qty * current_price),
                        "asset_allocation_pct": (
                            (position.qty * current_price)
                            / (position.cash + (position.qty * current_price))
                            * 100
                            if (position.cash + (position.qty * current_price)) > 0
                            else 0
                        ),
                        "price_change_pct": 0.0,
                        "trigger_threshold_pct": (
                            position.order_policy.trigger_threshold_pct * 100
                            if position.order_policy
                            else 3.0  # Default fallback
                        ),
                        "triggered": False,
                        "side": None,
                        "executed": False,
                        "commission": 0.0,
                        "trade_qty": 0.0,
                        "trade_notional": 0.0,
                        "dividend_event": False,
                        "dividend_dps": 0.0,
                        "dividend_gross": 0.0,
                        "dividend_net": 0.0,
                        "dividend_withholding": 0.0,
                    }
                )
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

                        # Update the last time-series data point to mark dividend event
                        if time_series_data:
                            time_series_data[-1].update(
                                {
                                    "dividend_event": True,
                                    "dividend_dps": float(dividend.dps),
                                    "dividend_gross": float(gross_amount),
                                    "dividend_net": float(net_amount),
                                    "dividend_withholding": float(
                                        dividend.calculate_withholding_tax(position.qty)
                                    ),
                                }
                            )

                        print(
                            f"Dividend processed: {dividend.dps} per share on {current_date}, net amount: ${net_amount:.2f}"
                        )

                        # Update position in repository
                        temp_positions.save(position)

            # Capture anchor price BEFORE evaluation (used for trigger calculation)
            # This is the reference price that determines if a trigger fires
            pre_eval_anchor = position.anchor_price

            # Track trigger analysis (optimized for performance)
            # Only create detailed trigger info if detailed analysis is enabled
            if detailed_trigger_analysis:
                trigger_info = {
                    "timestamp": current_time.isoformat(),
                    "date": current_time.strftime("%Y-%m-%d"),
                    "time": current_time.strftime("%H:%M:%S"),
                    "price": current_price,
                    "anchor_price": pre_eval_anchor,
                    "price_change_pct": (
                        ((current_price / position.anchor_price) - 1) * 100
                        if position.anchor_price
                        else 0
                    ),
                    "trigger_threshold": (
                        position.order_policy.trigger_threshold_pct * 100
                        if position.order_policy
                        else 3.0  # Default fallback
                    ),
                    "triggered": False,
                    "side": None,
                    "qty": 0,
                    "reason": "No trigger",
                    "executed": False,
                    "execution_error": None,
                    "cash_after": position.cash,
                    "shares_after": position.qty,
                    "dividend": 0.0,
                    "bid": current_price - current_price * 0.0005,
                    "ask": current_price + current_price * 0.0005,
                    "open": getattr(price_data, "open", current_price),
                    "high": getattr(price_data, "high", current_price),
                    "low": getattr(price_data, "low", current_price),
                    "close": getattr(price_data, "close", current_price),
                    "volume": getattr(price_data, "volume", 0),
                }
            else:
                # Minimal trigger info for better performance
                trigger_info = {
                    "timestamp": current_time.isoformat(),
                    "price": current_price,
                    "anchor_price": pre_eval_anchor,
                    "price_change_pct": (
                        ((current_price / pre_eval_anchor) - 1) * 100
                        if pre_eval_anchor
                        else 0
                    ),
                    "triggered": False,
                    "side": None,
                    "qty": 0,
                    "reason": "No trigger",
                    "executed": False,
                    "execution_error": None,
                }

            # Evaluate position using the actual trading logic
            try:
                # Simulation uses synthetic tenant/portfolio IDs (must match position creation)
                sim_tenant_id = "simulation"
                sim_portfolio_id = "simulation"
                evaluation = evaluate_uc.evaluate(
                    tenant_id=sim_tenant_id,
                    portfolio_id=sim_portfolio_id,
                    position_id=position_id,
                    current_price=current_price,
                    write_timeline=False,  # Simulation writes its own timeline
                )

                # Write to timeline for EVERY evaluation (simulation mode)
                self._write_simulation_timeline_row(
                    position=position,
                    price_data=price_data,
                    evaluation=evaluation,
                    trigger_info=trigger_info,
                    order_proposal=evaluation.get("order_proposal"),
                    execution_info=None,  # Will be updated after execution
                    simulation_id=simulation_id,
                    ticker=ticker or sim_data.ticker,
                    timestamp=current_time,
                )

                # Debug: Log ALL evaluations that detect triggers
                delta_pct = evaluation.get("delta_pct", 0)
                threshold_pct = position.order_policy.trigger_threshold_pct * 100 if position.order_policy else 3.0
                if evaluation.get("trigger_detected", False):
                    print(f"  >>> EVAL TRIGGER: price=${current_price:.2f}, anchor=${position.anchor_price:.2f}, delta={delta_pct:+.2f}% (threshold=±{threshold_pct:.1f}%), trigger_detected={evaluation.get('trigger_detected')}, trigger_type={evaluation.get('trigger_type')}")

                # Debug: Log evaluation results periodically
                if len(trigger_analysis) < 20 or len(trigger_analysis) % 100 == 0:
                    print(f"  Eval #{len(trigger_analysis)}: price=${current_price:.2f}, anchor=${position.anchor_price:.2f}, delta={delta_pct:+.2f}% (threshold=±{threshold_pct:.1f}%), trigger={evaluation.get('trigger_detected', False)}")

                if evaluation["trigger_detected"]:
                    # Mark as triggered even if order_proposal is blocked by guardrails
                    trigger_info["triggered"] = True
                    trigger_info["side"] = evaluation.get("trigger_type")
                    trigger_info["reason"] = evaluation.get("reasoning", "Trigger condition met")
                    print(f"  >>> TRIGGER DETECTED: side={trigger_info['side']}, trigger_info['triggered']={trigger_info['triggered']}")

                    if evaluation["order_proposal"]:
                        order_proposal = evaluation["order_proposal"]
                        trigger_info.update(
                            {
                                "side": order_proposal["side"],
                                "qty": order_proposal["trimmed_qty"],
                            }
                        )

                        # Submit order using actual trading logic
                        order_request = CreateOrderRequest(
                            side=order_proposal["side"], qty=abs(order_proposal["trimmed_qty"])
                        )

                        try:
                            submit_response = submit_uc.execute(
                                tenant_id="simulation",
                                portfolio_id="simulation",
                                position_id=position_id,
                                request=order_request,
                                idempotency_key=f"sim_{current_time.timestamp()}",
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
                                        position = temp_positions.get(
                                            tenant_id="simulation",
                                            portfolio_id="simulation",
                                            position_id=position_id
                                        )

                                        # Reset anchor price to execution price after trade
                                        old_anchor = position.anchor_price
                                        position.set_anchor_price(current_price)
                                        temp_positions.save(position)
                                        print(f"  >>> ANCHOR RESET: {old_anchor:.2f} -> {current_price:.2f} after {order_proposal['side']} trade")

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

                                        # Update timeline row with execution info
                                        self._update_simulation_timeline_execution(
                                            position=position,
                                            price_data=price_data,
                                            order_id=submit_response.order_id,
                                            trade_id=None,  # TODO: Get trade_id from execution
                                            execution_price=current_price,
                                            execution_qty=order_proposal["trimmed_qty"],
                                            execution_commission=order_proposal["commission"],
                                            simulation_id=simulation_id,
                                            ticker=ticker or sim_data.ticker,
                                            timestamp=current_time,
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
                        # Trigger detected but order blocked (e.g., by guardrails)
                        trigger_info["qty"] = 0
                        trigger_info["executed"] = False
                        trigger_info["execution_error"] = "Order blocked by guardrails (no valid order proposal)"
                else:
                    # No trigger - check why
                    threshold = trigger_info.get("trigger_threshold", threshold_pct)
                    if abs(trigger_info["price_change_pct"]) < threshold:
                        trigger_info["reason"] = (
                            f"Price change {trigger_info['price_change_pct']:.2f}% below threshold {threshold:.2f}%"
                        )
                    else:
                        trigger_info["reason"] = "Other evaluation conditions not met"

            except Exception as e:
                # Evaluation failed - continue simulation
                import traceback
                print(f"Evaluation failed: {e}")
                traceback.print_exc()
                trigger_info.update(
                    {"executed": False, "execution_error": f"Evaluation failed: {e}"}
                )
                print(f"Position evaluation failed: {e}")

            # Add trigger analysis only if detailed analysis is enabled or triggered
            if detailed_trigger_analysis or trigger_info.get("triggered", False):
                trigger_analysis.append(trigger_info)

            # Calculate portfolio value
            portfolio_value = position.cash + (position.qty * current_price)
            portfolio_values.append(portfolio_value)

            # Collect comprehensive time-series data for every time point
            # Use delta_pct from evaluation (more accurate than local calculation)
            eval_delta_pct = evaluation.get("delta_pct", 0) if evaluation else 0

            # Debug: Log triggered events
            if trigger_info.get("triggered", False):
                print(f"  >>> Adding triggered event to time_series_data: triggered={trigger_info.get('triggered')}, side={trigger_info.get('side')}, price_change={eval_delta_pct:.2f}%")

            time_series_data.append(
                {
                    "timestamp": current_time.isoformat(),
                    "date": current_time.strftime("%Y-%m-%d"),
                    "time": current_time.strftime("%H:%M:%S"),
                    "price": current_price,
                    "volume": getattr(price_data, "volume", 0),
                    "is_market_hours": getattr(price_data, "is_market_hours", True),
                    "anchor_price": pre_eval_anchor,  # Use pre-trade anchor for accurate trigger display
                    "shares": position.qty,
                    "cash": position.cash,
                    "asset_value": position.qty * current_price,
                    "total_value": portfolio_value,
                    "asset_allocation_pct": (
                        (position.qty * current_price) / portfolio_value * 100
                        if portfolio_value > 0
                        else 0
                    ),
                    "price_change_pct": eval_delta_pct,
                    "trigger_threshold_pct": position.order_policy.trigger_threshold_pct * 100,
                    "triggered": trigger_info.get("triggered", False),
                    "side": trigger_info.get("side"),
                    "executed": trigger_info.get("executed", False),
                    "commission": trigger_info.get("commission", 0.0),
                    "trade_qty": trigger_info.get("qty", 0.0),
                    "trade_notional": (
                        trigger_info.get("qty", 0.0) * current_price
                        if trigger_info.get("qty", 0.0) != 0
                        else 0.0
                    ),
                    "dividend_event": False,  # Will be updated if dividend occurs
                    "dividend_dps": 0.0,
                    "dividend_gross": 0.0,
                    "dividend_net": 0.0,
                    "dividend_withholding": 0.0,
                    "execution_error": trigger_info.get("execution_error"),
                    "reason": evaluation.get("reasoning", trigger_info.get("reason", "No trigger")) if evaluation else "No evaluation",
                    # Show new anchor price if it changed (i.e., a trade executed)
                    "new_anchor_price": position.anchor_price if position.anchor_price != pre_eval_anchor else None,
                }
            )

            # Debug logging - reduce frequency for better performance
            if len(portfolio_values) % 100 == 0:  # Log every 100th data point instead of 10th
                print(
                    f"Progress: {len(portfolio_values)} data points processed, Portfolio=${portfolio_value:.2f}"
                )

            # Calculate daily returns
            if len(portfolio_values) > 1:
                if portfolio_values[-2] <= 0:
                    daily_return = 0.0  # Avoid division by zero
                else:
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
        if initial_cash <= 0:
            raise ValueError(f"Invalid initial cash: {initial_cash}")
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

        # Debug: Count triggered events
        triggered_count = sum(1 for ts in time_series_data if ts.get("triggered", False))
        print(f"  Time series data points: {len(time_series_data)}")
        print(f"  Triggered events in time_series_data: {triggered_count}")

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
            "time_series_data": time_series_data,  # Add comprehensive time-series data
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
        if first_price <= 0:
            raise ValueError(f"Invalid first price for buy-hold: {first_price}")
        if initial_cash <= 0:
            raise ValueError(f"Invalid initial cash for buy-hold: {initial_cash}")
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
                if portfolio_values[-2] <= 0:
                    daily_return = 0.0  # Avoid division by zero
                else:
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
        if initial_cash <= 0:
            raise ValueError(f"Invalid initial cash for buy-hold: {initial_cash}")
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

    def _calculate_dividend_analysis(
        self,
        ticker: str,
        start_date: datetime,
        end_date: datetime,
        sim_data: SimulationData = None,
        algo_result: Dict[str, Any] = None,
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

            # Calculate total dividends received for the position
            total_dividends_received = 0.0
            if sim_data and algo_result:
                # Calculate dividends based on shares held during each dividend period
                # This is more realistic than just using final quantity

                # Get the initial asset value to calculate initial shares
                initial_asset_value = algo_result.get("initial_asset_value", 10000)

                # Calculate initial shares (this is what we would have bought at the start)
                if sim_data.price_data:
                    first_price = sim_data.price_data[0].price
                    if first_price > 0:
                        initial_shares = initial_asset_value / first_price

                        # For simplicity, assume we hold shares throughout the period
                        # In reality, the algorithm might trade, but for dividend calculation
                        # we'll use a conservative estimate based on average holdings

                        # Calculate average shares held (simplified: use initial shares as baseline)
                        avg_shares_held = initial_shares * 0.7  # Assume 70% average holding

                        if avg_shares_held > 0:
                            # Calculate total dividends received based on average shares held
                            total_dividends_received = total_dividend_amount * avg_shares_held

                            # Apply withholding tax (25% default)
                            withholding_tax_rate = 0.25
                            net_dividends_received = total_dividends_received * (
                                1 - withholding_tax_rate
                            )
                            withholding_tax_amount = total_dividends_received * withholding_tax_rate
                        else:
                            net_dividends_received = 0.0
                            withholding_tax_amount = 0.0
                    else:
                        net_dividends_received = 0.0
                        withholding_tax_amount = 0.0
                else:
                    net_dividends_received = 0.0
                    withholding_tax_amount = 0.0
            else:
                net_dividends_received = 0.0
                withholding_tax_amount = 0.0

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
                "total_dividends_received": total_dividends_received,
                "net_dividends_received": net_dividends_received,
                "withholding_tax_amount": withholding_tax_amount,
                "dividends": dividend_list,
                "message": f"Found {dividend_count} dividend(s) totaling ${total_dividend_amount:.4f} per share, ${net_dividends_received:.2f} net received",
            }
        except Exception as e:
            print(f"Error calculating dividend analysis: {e}")
            return {
                "total_dividends": 0,
                "dividend_yield": 0.0,
                "dividend_count": 0,
                "total_dividend_amount": 0.0,
                "total_dividends_received": 0.0,
                "net_dividends_received": 0.0,
                "withholding_tax_amount": 0.0,
                "dividends": [],
                "message": f"Error calculating dividends: {str(e)}",
            }

    def _write_simulation_timeline_row(
        self,
        position,
        price_data,
        evaluation: Dict[str, Any],
        trigger_info: Dict[str, Any],
        order_proposal: Optional[Dict[str, Any]],
        execution_info: Optional[Dict[str, Any]],
        simulation_id: Optional[str],
        ticker: str,
        timestamp: datetime,
    ) -> None:
        """Write a timeline row for simulation evaluation."""
        if not self.evaluation_timeline_repo or not simulation_id:
            return  # Timeline repo not available or no simulation_id

        try:
            # Ensure timestamp is a Python datetime, not a pandas Timestamp
            import pandas as pd
            if isinstance(timestamp, pd.Timestamp):
                timestamp = timestamp.to_pydatetime()
            from application.helpers.timeline_builder import build_timeline_row_from_evaluation

            # For simulation, use synthetic tenant_id/portfolio_id
            tenant_id = "simulation"
            portfolio_id = simulation_id  # Use simulation_id as portfolio_id

            # Determine action
            action = "HOLD"
            action_reason = "No trigger detected"
            if evaluation.get("trigger_detected") and order_proposal:
                side = order_proposal.get("side", "")
                action = "BUY" if side == "BUY" else "SELL" if side == "SELL" else "HOLD"
                action_reason = evaluation.get("reasoning", "Trigger fired")

            # Build timeline row
            timeline_row = build_timeline_row_from_evaluation(
                mode="SIMULATION",
                tenant_id=tenant_id,
                portfolio_id=portfolio_id,
                portfolio_name=f"Simulation: {ticker}",
                position_id=position.id,
                symbol=ticker,
                timestamp=timestamp,
                trace_id=None,
                simulation_run_id=simulation_id,
                source="simulation",
                price_data=price_data,
                effective_price=price_data.price,
                price_validation={"valid": True, "rejections": [], "warnings": []},
                allow_after_hours=True,  # Simulation controls this via include_after_hours
                trading_hours_policy="OPEN_PLUS_AFTER_HOURS",  # Default for simulation
                position_qty=position.qty,
                position_cash=position.cash or 0.0,
                position_dividend_receivable=position.dividend_receivable or 0.0,
                anchor_price=position.anchor_price,
                anchor_reset_info=None,  # TODO: Track anchor resets in simulation
                trigger_config={
                    "up_threshold_pct": trigger_info.get("trigger_threshold", 0.03) * 100,
                    "down_threshold_pct": -trigger_info.get("trigger_threshold", 0.03) * 100,
                },
                trigger_result={
                    "triggered": evaluation.get("trigger_detected", False),
                    "side": evaluation.get("trigger_type"),
                    "reasoning": evaluation.get("reasoning", "No trigger"),
                },
                guardrail_config={
                    "min_stock_pct": position.guardrails.min_stock_alloc_pct,
                    "max_stock_pct": position.guardrails.max_stock_alloc_pct,
                },
                guardrail_result={
                    "allowed": (
                        order_proposal.get("validation", {}).get("valid", True)
                        if order_proposal
                        else True
                    ),
                    "reason": None,
                },
                order_policy={
                    "rebalance_ratio": position.order_policy.rebalance_ratio,
                    "commission_rate": position.order_policy.commission_rate,
                },
                order_proposal=order_proposal,
                action=action,
                action_reason=action_reason,
                execution_info=execution_info,
            )

            # Save to timeline
            self.evaluation_timeline_repo.save(timeline_row)

        except Exception as e:
            # Don't fail simulation if timeline write fails
            print(f"⚠️  Failed to write simulation timeline row: {e}")
            import traceback

            traceback.print_exc()

    def _update_simulation_timeline_execution(
        self,
        position,
        price_data,
        order_id: str,
        trade_id: Optional[str],
        execution_price: float,
        execution_qty: float,
        execution_commission: float,
        simulation_id: Optional[str],
        ticker: str,
        timestamp: datetime,
    ) -> None:
        """Update timeline row with execution info after trade is filled."""
        if not self.evaluation_timeline_repo or not simulation_id:
            return

        try:
            # Ensure timestamp is a Python datetime, not a pandas Timestamp
            import pandas as pd
            if isinstance(timestamp, pd.Timestamp):
                timestamp = timestamp.to_pydatetime()

            # Find the most recent timeline row for this simulation/position/timestamp
            # For now, we'll create a new row with execution info
            # TODO: Implement update logic to find and update existing row
            from application.helpers.timeline_builder import build_timeline_row_from_evaluation

            tenant_id = "simulation"
            portfolio_id = simulation_id

            execution_info = {
                "order_id": order_id,
                "trade_id": trade_id,
                "price": execution_price,
                "qty": execution_qty,
                "commission": execution_commission,
                "commission_rate": position.order_policy.commission_rate,
                "status": "FILLED",
                "timestamp": timestamp,
            }

            # Build timeline row with execution info
            timeline_row = build_timeline_row_from_evaluation(
                mode="SIMULATION",
                tenant_id=tenant_id,
                portfolio_id=portfolio_id,
                portfolio_name=f"Simulation: {ticker}",
                position_id=position.id,
                symbol=ticker,
                timestamp=timestamp,
                trace_id=None,
                simulation_run_id=simulation_id,
                source="simulation",
                price_data=price_data,
                effective_price=execution_price,
                price_validation={"valid": True, "rejections": [], "warnings": []},
                allow_after_hours=True,
                trading_hours_policy="OPEN_PLUS_AFTER_HOURS",
                position_qty=position.qty,
                position_cash=position.cash or 0.0,
                position_dividend_receivable=position.dividend_receivable or 0.0,
                anchor_price=position.anchor_price,
                trigger_config=None,
                trigger_result={"triggered": True, "side": "BUY" if execution_qty > 0 else "SELL"},
                guardrail_config=None,
                guardrail_result={"allowed": True},
                order_policy=None,
                order_proposal=None,
                action="BUY" if execution_qty > 0 else "SELL",
                action_reason="Trade executed",
                execution_info=execution_info,
                position_qty_after=position.qty,
                position_cash_after=position.cash,
            )

            # Save to timeline
            self.evaluation_timeline_repo.save(timeline_row)

        except Exception as e:
            print(f"⚠️  Failed to update simulation timeline execution: {e}")
