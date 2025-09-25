# =========================
# backend/infrastructure/persistence/memory/optimization_repo_mem.py
# =========================

from typing import List, Optional
from uuid import UUID

from domain.entities.optimization_config import OptimizationConfig, OptimizationStatus
from domain.entities.optimization_result import OptimizationResult, OptimizationResultStatus
from domain.ports.optimization_repo import (
    OptimizationConfigRepo,
    OptimizationResultRepo,
    HeatmapDataRepo,
)
from domain.value_objects.heatmap_data import HeatmapData


class InMemoryOptimizationConfigRepo(OptimizationConfigRepo):
    """In-memory implementation of optimization configuration repository."""

    def __init__(self):
        self._configs: dict[UUID, OptimizationConfig] = {}

    def save(self, config: OptimizationConfig) -> None:
        """Save an optimization configuration."""
        self._configs[config.id] = config

    def get_by_id(self, config_id: UUID) -> Optional[OptimizationConfig]:
        """Get an optimization configuration by ID."""
        return self._configs.get(config_id)

    def get_by_user(self, user_id: UUID) -> List[OptimizationConfig]:
        """Get all optimization configurations for a user."""
        return [config for config in self._configs.values() if config.created_by == user_id]

    def update_status(self, config_id: UUID, status: str) -> None:
        """Update the status of an optimization configuration."""
        if config_id in self._configs:
            config = self._configs[config_id]
            # Convert string status to enum
            status_enum = OptimizationStatus(status)
            # Create a new config with updated status
            updated_config = OptimizationConfig(
                id=config.id,
                name=config.name,
                ticker=config.ticker,
                start_date=config.start_date,
                end_date=config.end_date,
                parameter_ranges=config.parameter_ranges,
                optimization_criteria=config.optimization_criteria,
                created_by=config.created_by,
                created_at=config.created_at,
                updated_at=config.updated_at,
                status=status_enum,
                description=config.description,
                max_combinations=config.max_combinations,
                batch_size=config.batch_size,
            )
            self._configs[config_id] = updated_config

    def delete(self, config_id: UUID) -> None:
        """Delete an optimization configuration."""
        self._configs.pop(config_id, None)

    def list_all(self, limit: int = 100, offset: int = 0) -> List[OptimizationConfig]:
        """List all optimization configurations with pagination."""
        configs = list(self._configs.values())
        return configs[offset : offset + limit]


class InMemoryOptimizationResultRepo(OptimizationResultRepo):
    """In-memory implementation of optimization result repository."""

    def __init__(self):
        self._results: dict[str, OptimizationResult] = {}

    def save_result(self, result: OptimizationResult) -> None:
        """Save an optimization result."""
        self._results[result.parameter_combination.combination_id] = result

    def get_by_config(self, config_id: UUID) -> List[OptimizationResult]:
        """Get all results for a configuration."""
        return [result for result in self._results.values() if result.config_id == config_id]

    def get_by_combination_id(self, combination_id: str) -> Optional[OptimizationResult]:
        """Get a result by combination ID."""
        return self._results.get(combination_id)

    def update_result(self, result: OptimizationResult) -> None:
        """Update an optimization result."""
        self._results[result.parameter_combination.combination_id] = result

    def delete_by_config(self, config_id: UUID) -> None:
        """Delete all results for a configuration."""
        to_delete = [
            combination_id
            for combination_id, result in self._results.items()
            if result.config_id == config_id
        ]
        for combination_id in to_delete:
            del self._results[combination_id]

    def get_completed_results(self, config_id: UUID) -> List[OptimizationResult]:
        """Get only completed results for a configuration."""
        return [
            result
            for result in self._results.values()
            if result.config_id == config_id and result.status == OptimizationResultStatus.COMPLETED
        ]

    def get_failed_results(self, config_id: UUID) -> List[OptimizationResult]:
        """Get only failed results for a configuration."""
        return [
            result
            for result in self._results.values()
            if result.config_id == config_id and result.status == OptimizationResultStatus.FAILED
        ]


class InMemoryHeatmapDataRepo(HeatmapDataRepo):
    """In-memory implementation of heatmap data repository."""

    def __init__(self):
        self._heatmap_data: dict[str, HeatmapData] = {}

    def _get_key(self, config_id: UUID, x_parameter: str, y_parameter: str, metric: str) -> str:
        """Generate a unique key for heatmap data."""
        return f"{config_id}_{x_parameter}_{y_parameter}_{metric}"

    def save_heatmap_data(self, heatmap_data: HeatmapData) -> None:
        """Save heatmap data."""
        key = self._get_key(
            heatmap_data.config_id,
            heatmap_data.x_parameter,
            heatmap_data.y_parameter,
            heatmap_data.metric,
        )
        self._heatmap_data[key] = heatmap_data

    def get_heatmap_data(
        self, config_id: UUID, x_parameter: str, y_parameter: str, metric: str
    ) -> Optional[HeatmapData]:
        """Get heatmap data for specific parameters and metric."""
        key = self._get_key(config_id, x_parameter, y_parameter, metric)
        return self._heatmap_data.get(key)

    def get_available_heatmaps(self, config_id: UUID) -> List[dict]:
        """Get list of available heatmap combinations for a configuration."""
        available = []
        for key, heatmap_data in self._heatmap_data.items():
            if heatmap_data.config_id == config_id:
                available.append(
                    {
                        "x_parameter": heatmap_data.x_parameter,
                        "y_parameter": heatmap_data.y_parameter,
                        "metric": heatmap_data.metric,
                    }
                )
        return available

    def delete_heatmap_data(self, config_id: UUID) -> None:
        """Delete all heatmap data for a configuration."""
        to_delete = [
            key
            for key, heatmap_data in self._heatmap_data.items()
            if heatmap_data.config_id == config_id
        ]
        for key in to_delete:
            del self._heatmap_data[key]
