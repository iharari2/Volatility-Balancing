# =========================
# backend/domain/ports/optimization_repo.py
# =========================

from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from domain.entities.optimization_config import OptimizationConfig
from domain.entities.optimization_result import OptimizationResult
from domain.value_objects.heatmap_data import HeatmapData


class OptimizationConfigRepo(ABC):
    """Repository interface for optimization configurations."""

    @abstractmethod
    def save(self, config: OptimizationConfig) -> None:
        """Save an optimization configuration."""
        pass

    @abstractmethod
    def get_by_id(self, config_id: UUID) -> Optional[OptimizationConfig]:
        """Get an optimization configuration by ID."""
        pass

    @abstractmethod
    def get_by_user(self, user_id: UUID) -> List[OptimizationConfig]:
        """Get all optimization configurations for a user."""
        pass

    @abstractmethod
    def update_status(self, config_id: UUID, status: str) -> None:
        """Update the status of an optimization configuration."""
        pass

    @abstractmethod
    def delete(self, config_id: UUID) -> None:
        """Delete an optimization configuration."""
        pass

    @abstractmethod
    def list_all(self, limit: int = 100, offset: int = 0) -> List[OptimizationConfig]:
        """List all optimization configurations with pagination."""
        pass


class OptimizationResultRepo(ABC):
    """Repository interface for optimization results."""

    @abstractmethod
    def save_result(self, result: OptimizationResult) -> None:
        """Save an optimization result."""
        pass

    @abstractmethod
    def get_by_config(self, config_id: UUID) -> List[OptimizationResult]:
        """Get all results for a configuration."""
        pass

    @abstractmethod
    def get_by_combination_id(self, combination_id: str) -> Optional[OptimizationResult]:
        """Get a result by combination ID."""
        pass

    @abstractmethod
    def update_result(self, result: OptimizationResult) -> None:
        """Update an optimization result."""
        pass

    @abstractmethod
    def delete_by_config(self, config_id: UUID) -> None:
        """Delete all results for a configuration."""
        pass

    @abstractmethod
    def get_completed_results(self, config_id: UUID) -> List[OptimizationResult]:
        """Get only completed results for a configuration."""
        pass

    @abstractmethod
    def get_failed_results(self, config_id: UUID) -> List[OptimizationResult]:
        """Get only failed results for a configuration."""
        pass


class HeatmapDataRepo(ABC):
    """Repository interface for heatmap data."""

    @abstractmethod
    def save_heatmap_data(self, heatmap_data: HeatmapData) -> None:
        """Save heatmap data."""
        pass

    @abstractmethod
    def get_heatmap_data(
        self, config_id: UUID, x_parameter: str, y_parameter: str, metric: str
    ) -> Optional[HeatmapData]:
        """Get heatmap data for specific parameters and metric."""
        pass

    @abstractmethod
    def get_available_heatmaps(self, config_id: UUID) -> List[dict]:
        """Get list of available heatmap combinations for a configuration."""
        pass

    @abstractmethod
    def delete_heatmap_data(self, config_id: UUID) -> None:
        """Delete all heatmap data for a configuration."""
        pass


