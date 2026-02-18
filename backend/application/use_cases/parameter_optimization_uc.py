# =========================
# backend/application/use_cases/parameter_optimization_uc.py
# =========================

from typing import List, Optional, Dict, Any, TYPE_CHECKING
from uuid import UUID, uuid4
from datetime import datetime, timezone, timedelta
import statistics
import traceback

from domain.entities.optimization_config import OptimizationConfig, OptimizationStatus
from domain.entities.optimization_result import (
    OptimizationResult,
    OptimizationResultStatus,
    ParameterCombination,
)
from domain.ports.optimization_repo import (
    OptimizationConfigRepo,
    OptimizationResultRepo,
    HeatmapDataRepo,
)
from domain.value_objects.parameter_range import ParameterRange
from domain.value_objects.optimization_criteria import OptimizationCriteria, OptimizationMetric
from domain.value_objects.heatmap_data import HeatmapData, HeatmapCell, HeatmapMetric

if TYPE_CHECKING:
    from application.use_cases.simulation_unified_uc import SimulationUnifiedUC


class CreateOptimizationRequest:
    """Request to create a new optimization configuration."""

    def __init__(
        self,
        name: str,
        ticker: str,
        start_date: datetime,
        end_date: datetime,
        parameter_ranges: Dict[str, ParameterRange],
        optimization_criteria: OptimizationCriteria,
        created_by: UUID,
        description: Optional[str] = None,
        max_combinations: Optional[int] = None,
        batch_size: int = 10,
        initial_cash: float = 10000.0,
        intraday_interval_minutes: int = 30,
        include_after_hours: bool = False,
    ):
        self.name = name
        self.ticker = ticker
        self.start_date = start_date
        self.end_date = end_date
        self.parameter_ranges = parameter_ranges
        self.optimization_criteria = optimization_criteria
        self.created_by = created_by
        self.description = description
        self.max_combinations = max_combinations
        self.batch_size = batch_size
        self.initial_cash = initial_cash
        self.intraday_interval_minutes = intraday_interval_minutes
        self.include_after_hours = include_after_hours


class OptimizationProgress:
    """Progress information for an optimization run."""

    def __init__(
        self,
        config_id: UUID,
        total_combinations: int,
        completed_combinations: int,
        failed_combinations: int,
        status: str,
        started_at: Optional[datetime] = None,
        estimated_completion: Optional[datetime] = None,
    ):
        self.config_id = config_id
        self.total_combinations = total_combinations
        self.completed_combinations = completed_combinations
        self.failed_combinations = failed_combinations
        self.status = status
        self.started_at = started_at
        self.estimated_completion = estimated_completion

    @property
    def progress_percentage(self) -> float:
        """Calculate progress percentage."""
        if self.total_combinations == 0:
            return 0.0
        return (
            (self.completed_combinations + self.failed_combinations) / self.total_combinations * 100
        )

    @property
    def remaining_combinations(self) -> int:
        """Calculate remaining combinations."""
        return self.total_combinations - self.completed_combinations - self.failed_combinations


class ParameterOptimizationUC:
    """Use case for parameter optimization."""

    def __init__(
        self,
        config_repo: OptimizationConfigRepo,
        result_repo: OptimizationResultRepo,
        heatmap_repo: HeatmapDataRepo,
        simulation_uc: "SimulationUnifiedUC",
    ):
        self.config_repo = config_repo
        self.result_repo = result_repo
        self.heatmap_repo = heatmap_repo
        self.simulation_uc = simulation_uc

    def create_optimization_config(self, request: CreateOptimizationRequest) -> OptimizationConfig:
        """Create a new optimization configuration."""
        # Validate parameter ranges
        self._validate_parameter_ranges(request.parameter_ranges)

        # Create the configuration
        config = OptimizationConfig.create(
            name=request.name,
            ticker=request.ticker,
            start_date=request.start_date,
            end_date=request.end_date,
            parameter_ranges=request.parameter_ranges,
            optimization_criteria=request.optimization_criteria,
            created_by=request.created_by,
            description=request.description,
            max_combinations=request.max_combinations,
            batch_size=request.batch_size,
            initial_cash=request.initial_cash,
            intraday_interval_minutes=request.intraday_interval_minutes,
            include_after_hours=request.include_after_hours,
        )

        # Save the configuration
        self.config_repo.save(config)

        return config

    def run_optimization(self, config_id: UUID) -> None:
        """Start an optimization run."""
        config = self.config_repo.get_by_id(config_id)
        if not config:
            raise ValueError(f"Optimization config not found: {config_id}")

        if not config.can_start():
            raise ValueError(f"Cannot start optimization in status: {config.status}")

        # Update status to running
        config.update_status(OptimizationStatus.RUNNING)
        self.config_repo.update_status(config_id, config.status.value)

        try:
            # Generate parameter combinations
            combinations = self._generate_parameter_combinations(config)

            # Create initial results for each combination
            for combination in combinations:
                result = OptimizationResult(
                    id=uuid4(),
                    config_id=config_id,
                    parameter_combination=combination,
                    metrics={},
                    status=OptimizationResultStatus.PENDING,
                )
                self.result_repo.save_result(result)

            # Process each combination with real simulation
            self._process_parameter_combinations(config, combinations)
        except Exception as e:
            print(f"Optimization failed: {e}")
            traceback.print_exc()
            config.update_status(OptimizationStatus.FAILED)
            self.config_repo.update_status(config_id, config.status.value)

    def get_optimization_progress(self, config_id: UUID) -> OptimizationProgress:
        """Get the current progress of an optimization."""
        config = self.config_repo.get_by_id(config_id)
        if not config:
            raise ValueError(f"Optimization config not found: {config_id}")

        # Check if optimization has been started (not in DRAFT status)
        if config.status == OptimizationStatus.DRAFT:
            raise ValueError("Optimization is not running")

        results = self.result_repo.get_by_config(config_id)
        completed = len([r for r in results if r.is_completed()])
        failed = len([r for r in results if r.is_failed()])

        return OptimizationProgress(
            config_id=config_id,
            total_combinations=config.calculate_total_combinations(),
            completed_combinations=completed,
            failed_combinations=failed,
            status=config.status.value,
            started_at=(
                config.created_at
                if config.status in [OptimizationStatus.RUNNING, OptimizationStatus.COMPLETED]
                else None
            ),
        )

    def get_optimization_results(self, config_id: UUID) -> List[OptimizationResult]:
        """Get all results for an optimization."""
        return self.result_repo.get_completed_results(config_id)

    def get_heatmap_data(
        self, config_id: UUID, x_parameter: str, y_parameter: str, metric: str
    ) -> Optional[HeatmapData]:
        """Get heatmap data for specific parameters and metric."""
        return self.heatmap_repo.get_heatmap_data(config_id, x_parameter, y_parameter, metric)

    def generate_heatmap_data(
        self, config_id: UUID, x_parameter: str, y_parameter: str, metric: str
    ) -> HeatmapData:
        """Generate heatmap data for specific parameters and metric."""
        results = self.result_repo.get_completed_results(config_id)
        if not results:
            raise ValueError("No completed results found for heatmap generation")

        # Extract unique x and y values
        x_values = sorted(
            set(
                r.parameter_combination.parameters[x_parameter]
                for r in results
                if x_parameter in r.parameter_combination.parameters
            )
        )
        y_values = sorted(
            set(
                r.parameter_combination.parameters[y_parameter]
                for r in results
                if y_parameter in r.parameter_combination.parameters
            )
        )

        # Create heatmap cells
        cells = []
        for result in results:
            if (
                x_parameter in result.parameter_combination.parameters
                and y_parameter in result.parameter_combination.parameters
            ):
                x_val = result.parameter_combination.parameters[x_parameter]
                y_val = result.parameter_combination.parameters[y_parameter]
                metric_val = result.get_metric_value(OptimizationMetric(metric))

                cell = HeatmapCell(
                    x_value=x_val,
                    y_value=y_val,
                    metric_value=metric_val or 0.0,
                    parameter_combination_id=result.parameter_combination.combination_id,
                    is_valid=metric_val is not None,
                    error_message=None if metric_val is not None else "No metric value",
                )
                cells.append(cell)

        # Calculate statistics
        valid_values = [c.metric_value for c in cells if c.is_valid]
        min_val = min(valid_values) if valid_values else 0.0
        max_val = max(valid_values) if valid_values else 0.0
        mean_val = sum(valid_values) / len(valid_values) if valid_values else 0.0

        heatmap_data = HeatmapData(
            config_id=str(config_id),
            x_parameter=x_parameter,
            y_parameter=y_parameter,
            metric=HeatmapMetric(metric),
            cells=cells,
            x_values=x_values,
            y_values=y_values,
            min_value=min_val,
            max_value=max_val,
            mean_value=mean_val,
            created_at=datetime.now(timezone.utc).isoformat(),
        )

        # Save the heatmap data
        self.heatmap_repo.save_heatmap_data(heatmap_data)

        return heatmap_data

    def _validate_parameter_ranges(self, parameter_ranges: Dict[str, ParameterRange]) -> None:
        """Validate parameter ranges."""
        if not parameter_ranges:
            raise ValueError("At least one parameter range must be specified")

        for name, param_range in parameter_ranges.items():
            if not isinstance(param_range, ParameterRange):
                raise ValueError(f"Invalid parameter range for {name}")

            # Allow single-value parameters (min_value == max_value)
            if param_range.get_value_count() < 1:
                raise ValueError(f"Parameter {name} must have at least 1 value")

    def _generate_parameter_combinations(
        self, config: OptimizationConfig
    ) -> List[ParameterCombination]:
        """Generate all parameter combinations for optimization."""
        from itertools import product

        # Get all parameter values
        param_values = {}
        for name, param_range in config.parameter_ranges.items():
            param_values[name] = param_range.generate_values()

        # Generate all combinations
        combinations = []
        for i, combination in enumerate(product(*param_values.values())):
            if config.max_combinations and i >= config.max_combinations:
                break

            # Create parameter dictionary
            params = dict(zip(param_values.keys(), combination))

            # Create combination
            combination_obj = ParameterCombination(
                parameters=params,
                combination_id=f"{config.id}_{i}",
                created_at=datetime.now(timezone.utc),
            )
            combinations.append(combination_obj)

        return combinations

    def _prefetch_market_data(self, config: OptimizationConfig):
        """Fetch historical price data and dividends once for the entire date range."""
        from infrastructure.market.market_data_storage import MarketDataStorage

        start_date = config.start_date
        end_date = config.end_date

        # Ensure timezone-aware
        if start_date.tzinfo is None:
            start_date = start_date.replace(tzinfo=timezone.utc)
        if end_date.tzinfo is None:
            end_date = end_date.replace(tzinfo=timezone.utc)

        fetch_start = start_date - timedelta(days=1)
        fetch_end = end_date + timedelta(days=1)

        # Cap at current time
        now = datetime.now(timezone.utc)
        if fetch_end > now:
            fetch_end = now

        print(f"[Optimization] Fetching historical data for {config.ticker} "
              f"from {fetch_start} to {fetch_end}")
        historical_data = self.simulation_uc.market_data.fetch_historical_data(
            config.ticker, fetch_start, fetch_end, config.intraday_interval_minutes
        )

        if not historical_data:
            raise ValueError(
                f"No historical data available for {config.ticker} "
                f"from {fetch_start} to {fetch_end}"
            )

        # Build MarketDataStorage and sim_data
        market_storage = MarketDataStorage()
        for price_data in historical_data:
            market_storage.store_price_data(config.ticker, price_data)

        sim_data = market_storage.get_simulation_data(
            config.ticker, fetch_start, fetch_end, config.include_after_hours
        )

        print(f"[Optimization] Fetched {len(historical_data)} data points, "
              f"{len(sim_data.price_data)} simulation points")

        # Fetch dividend history
        dividend_history = []
        if self.simulation_uc.dividend_market_data:
            try:
                dividend_history = self.simulation_uc.dividend_market_data.get_dividend_history(
                    config.ticker, fetch_start, fetch_end
                )
                print(f"[Optimization] Found {len(dividend_history)} dividend events")
            except Exception as e:
                print(f"[Optimization] Warning: Failed to fetch dividends: {e}")

        return historical_data, sim_data, dividend_history

    def _build_position_config(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Map flat optimization parameters to nested position_config dict."""
        position_config = {
            "trigger_threshold_pct": params.get("trigger_threshold_pct", 0.03),
            "rebalance_ratio": params.get("rebalance_ratio", 1.6667),
            "commission_rate": params.get("commission_rate", 0.0001),
            "min_notional": params.get("min_notional", 100.0),
            "allow_after_hours": params.get("allow_after_hours", True),
            "guardrails": {
                "min_stock_alloc_pct": params.get("min_stock_alloc_pct", 0.25),
                "max_stock_alloc_pct": params.get("max_stock_alloc_pct", 0.75),
            },
        }

        # Handle max_orders_per_day if specified
        if "max_orders_per_day" in params:
            position_config["guardrails"]["max_orders_per_day"] = int(params["max_orders_per_day"])

        # Handle min_qty if specified
        if "min_qty" in params:
            position_config["min_qty"] = params["min_qty"]

        return position_config

    def _map_simulation_result_to_metrics(self, sim_result) -> Dict[OptimizationMetric, float]:
        """Convert SimulationResult fields to optimization metrics."""
        metrics = {}

        # Direct mappings
        metrics[OptimizationMetric.TOTAL_RETURN] = sim_result.algorithm_return_pct
        metrics[OptimizationMetric.SHARPE_RATIO] = sim_result.algorithm_sharpe_ratio
        metrics[OptimizationMetric.MAX_DRAWDOWN] = sim_result.algorithm_max_drawdown
        metrics[OptimizationMetric.VOLATILITY] = sim_result.algorithm_volatility
        metrics[OptimizationMetric.TRADE_COUNT] = float(sim_result.algorithm_trades)

        # Calmar Ratio: annualized_return / abs(max_drawdown)
        annualized_return = sim_result.algorithm_return_pct
        max_dd = abs(sim_result.algorithm_max_drawdown)
        if max_dd > 0:
            metrics[OptimizationMetric.CALMAR_RATIO] = annualized_return / max_dd
        else:
            metrics[OptimizationMetric.CALMAR_RATIO] = 0.0

        # Sortino Ratio: (mean_return - rf) / downside_deviation
        daily_returns_list = [r["return"] for r in sim_result.daily_returns]
        if len(daily_returns_list) >= 2:
            mean_ret = statistics.mean(daily_returns_list)
            downside = [r for r in daily_returns_list if r < 0]
            if len(downside) >= 2:
                downside_dev = statistics.stdev(downside) * (252 ** 0.5)
                if downside_dev > 0:
                    metrics[OptimizationMetric.SORTINO_RATIO] = (mean_ret * 252) / downside_dev
                else:
                    metrics[OptimizationMetric.SORTINO_RATIO] = 0.0
            else:
                metrics[OptimizationMetric.SORTINO_RATIO] = 0.0
        else:
            metrics[OptimizationMetric.SORTINO_RATIO] = 0.0

        # Win Rate: profitable_trades / total_trades from trade_log
        trade_log = sim_result.trade_log
        if trade_log:
            profitable = sum(1 for t in trade_log if t.get("commission", 0) >= 0)
            # Simple: count trades where sell price > buy price
            # Since we don't track individual P&L per trade easily,
            # use daily_returns positive days as proxy
            positive_days = sum(1 for r in daily_returns_list if r > 0)
            total_days = len(daily_returns_list)
            metrics[OptimizationMetric.WIN_RATE] = (
                positive_days / total_days if total_days > 0 else 0.0
            )
        else:
            metrics[OptimizationMetric.WIN_RATE] = 0.0

        # Profit Factor: sum(gains) / abs(sum(losses)) from daily_returns
        gains = sum(r for r in daily_returns_list if r > 0)
        losses = sum(r for r in daily_returns_list if r < 0)
        if losses < 0:
            metrics[OptimizationMetric.PROFIT_FACTOR] = gains / abs(losses)
        else:
            metrics[OptimizationMetric.PROFIT_FACTOR] = float("inf") if gains > 0 else 0.0

        # Avg Trade Duration: total_trading_days / trade_count
        if sim_result.algorithm_trades > 0:
            metrics[OptimizationMetric.AVG_TRADE_DURATION] = (
                sim_result.total_trading_days / sim_result.algorithm_trades
            )
        else:
            metrics[OptimizationMetric.AVG_TRADE_DURATION] = float(sim_result.total_trading_days)

        return metrics

    def _process_parameter_combinations(
        self, config: OptimizationConfig, combinations: List[ParameterCombination]
    ) -> None:
        """Process parameter combinations using real simulation engine."""
        # Prefetch market data once
        try:
            historical_data, sim_data, dividend_history = self._prefetch_market_data(config)
        except Exception as e:
            print(f"[Optimization] Failed to prefetch market data: {e}")
            traceback.print_exc()
            config.update_status(OptimizationStatus.FAILED)
            self.config_repo.update_status(config.id, config.status.value)
            return

        total = len(combinations)
        for i, combination in enumerate(combinations):
            print(f"[Optimization] Processing combination {i + 1}/{total}: "
                  f"{combination.parameters}")

            # Find the result for this combination
            results = self.result_repo.get_by_config(config.id)
            result = next(
                (
                    r
                    for r in results
                    if r.parameter_combination.combination_id == combination.combination_id
                ),
                None,
            )

            if not result:
                continue

            try:
                # Build position config from flat parameters
                position_config = self._build_position_config(combination.parameters)

                # Run real simulation with pre-fetched data
                sim_result = self.simulation_uc.run_simulation_with_data(
                    ticker=config.ticker,
                    start_date=config.start_date,
                    end_date=config.end_date,
                    historical_data=historical_data,
                    sim_data=sim_data,
                    dividend_history=dividend_history,
                    initial_cash=config.initial_cash,
                    position_config=position_config,
                    lightweight=True,
                )

                # Map simulation result to optimization metrics
                metrics = self._map_simulation_result_to_metrics(sim_result)

                result.metrics = metrics
                result.status = OptimizationResultStatus.COMPLETED
                result.completed_at = datetime.now(timezone.utc)
                self.result_repo.save_result(result)

                print(f"[Optimization] Combination {i + 1}/{total} completed: "
                      f"return={metrics.get(OptimizationMetric.TOTAL_RETURN, 0):.2f}%, "
                      f"sharpe={metrics.get(OptimizationMetric.SHARPE_RATIO, 0):.3f}")

            except Exception as e:
                print(f"[Optimization] Combination {i + 1}/{total} failed: {e}")
                traceback.print_exc()
                result.status = OptimizationResultStatus.FAILED
                result.error_message = str(e)
                result.completed_at = datetime.now(timezone.utc)
                self.result_repo.save_result(result)

        # Update config status to completed
        config.update_status(OptimizationStatus.COMPLETED)
        self.config_repo.update_status(config.id, config.status.value)
        print(f"[Optimization] Optimization completed for config {config.id}")
