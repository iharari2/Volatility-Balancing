# =========================
# backend/application/use_cases/parameter_optimization_uc.py
# =========================

from typing import List, Optional, Dict
from uuid import UUID, uuid4
from datetime import datetime, timezone

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
from domain.ports.simulation_repo import SimulationRepo
from domain.value_objects.parameter_range import ParameterRange
from domain.value_objects.optimization_criteria import OptimizationCriteria, OptimizationMetric
from domain.value_objects.heatmap_data import HeatmapData, HeatmapCell, HeatmapMetric


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
        simulation_repo: SimulationRepo,
    ):
        self.config_repo = config_repo
        self.result_repo = result_repo
        self.heatmap_repo = heatmap_repo
        self.simulation_repo = simulation_repo

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

        # Process each combination with mock simulation
        self._process_parameter_combinations(config, combinations)

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

    def _process_parameter_combinations(
        self, config: OptimizationConfig, combinations: List[ParameterCombination]
    ) -> None:
        """Process parameter combinations with mock simulation results."""
        import random
        import time

        for i, combination in enumerate(combinations):
            # Simulate processing time
            time.sleep(0.1)  # Small delay to simulate processing

            # Generate mock metrics based on parameters
            # This creates realistic-looking results that vary with parameters
            base_return = 0.10 + random.uniform(-0.05, 0.05)
            base_sharpe = 1.0 + random.uniform(-0.3, 0.3)
            base_drawdown = -0.05 + random.uniform(-0.02, 0.02)

            # Add some parameter-based variation
            if "trigger_threshold_pct" in combination.parameters:
                threshold = combination.parameters["trigger_threshold_pct"]
                # Higher thresholds might lead to better risk-adjusted returns
                base_sharpe += (threshold - 0.03) * 10  # Scale factor
                base_return += (threshold - 0.03) * 2

            if "rebalance_ratio" in combination.parameters:
                ratio = combination.parameters["rebalance_ratio"]
                # Higher ratios might lead to more trades but potentially better returns
                base_return += (ratio - 1.75) * 0.5
                base_sharpe += (ratio - 1.75) * 0.2

            # Generate mock metrics
            metrics = {
                OptimizationMetric.TOTAL_RETURN: max(
                    0.0, base_return + random.uniform(-0.02, 0.02)
                ),
                OptimizationMetric.SHARPE_RATIO: max(0.0, base_sharpe + random.uniform(-0.1, 0.1)),
                OptimizationMetric.MAX_DRAWDOWN: min(
                    0.0, base_drawdown + random.uniform(-0.01, 0.01)
                ),
                OptimizationMetric.VOLATILITY: max(0.05, 0.12 + random.uniform(-0.03, 0.03)),
                OptimizationMetric.CALMAR_RATIO: max(
                    0.0, base_return / abs(base_drawdown) + random.uniform(-0.5, 0.5)
                ),
                OptimizationMetric.SORTINO_RATIO: max(0.0, base_sharpe + random.uniform(-0.2, 0.2)),
                OptimizationMetric.WIN_RATE: max(0.0, min(1.0, 0.6 + random.uniform(-0.1, 0.1))),
                OptimizationMetric.PROFIT_FACTOR: max(0.0, 1.5 + random.uniform(-0.3, 0.3)),
                OptimizationMetric.TRADE_COUNT: max(1, int(20 + random.uniform(-5, 10))),
                OptimizationMetric.AVG_TRADE_DURATION: max(1.0, 5.0 + random.uniform(-2, 3)),
            }

            # Get the result and update it
            results = self.result_repo.get_by_config(config.id)
            result = next(
                (
                    r
                    for r in results
                    if r.parameter_combination.combination_id == combination.combination_id
                ),
                None,
            )

            if result:
                result.metrics = metrics
                result.status = OptimizationResultStatus.COMPLETED
                result.completed_at = datetime.now(timezone.utc)
                self.result_repo.save_result(result)

        # Update config status to completed
        config.update_status(OptimizationStatus.COMPLETED)
        self.config_repo.update_status(config.id, config.status.value)
