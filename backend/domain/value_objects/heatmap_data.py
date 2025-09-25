# =========================
# backend/domain/value_objects/heatmap_data.py
# =========================

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from enum import Enum


class HeatmapMetric(Enum):
    """Metrics that can be visualized in heatmaps."""

    TOTAL_RETURN = "total_return"
    SHARPE_RATIO = "sharpe_ratio"
    MAX_DRAWDOWN = "max_drawdown"
    VOLATILITY = "volatility"
    CALMAR_RATIO = "calmar_ratio"
    SORTINO_RATIO = "sortino_ratio"
    WIN_RATE = "win_rate"
    PROFIT_FACTOR = "profit_factor"
    TRADE_COUNT = "trade_count"
    AVG_TRADE_DURATION = "avg_trade_duration"


@dataclass(frozen=True)
class HeatmapCell:
    """A single cell in a heatmap."""

    x_value: float
    y_value: float
    metric_value: float
    parameter_combination_id: str
    is_valid: bool = True
    error_message: Optional[str] = None

    def __post_init__(self):
        """Validate the heatmap cell."""
        if not self.is_valid and not self.error_message:
            raise ValueError("Invalid cells must have an error message")


@dataclass(frozen=True)
class HeatmapData:
    """Data structure for heatmap visualization."""

    config_id: str
    x_parameter: str
    y_parameter: str
    metric: HeatmapMetric
    cells: List[HeatmapCell]
    x_values: List[float]
    y_values: List[float]
    min_value: float
    max_value: float
    mean_value: float
    created_at: str

    def __post_init__(self):
        """Validate the heatmap data."""
        if not self.cells:
            raise ValueError("Heatmap must have at least one cell")

        if not self.x_values or not self.y_values:
            raise ValueError("X and Y values cannot be empty")

        if self.min_value > self.max_value:
            raise ValueError("Min value cannot be greater than max value")

    def get_cell(self, x_value: float, y_value: float) -> Optional[HeatmapCell]:
        """Get a specific cell by x and y values."""
        for cell in self.cells:
            if abs(cell.x_value - x_value) < 1e-6 and abs(cell.y_value - y_value) < 1e-6:
                return cell
        return None

    def get_valid_cells(self) -> List[HeatmapCell]:
        """Get only valid cells."""
        return [cell for cell in self.cells if cell.is_valid]

    def get_invalid_cells(self) -> List[HeatmapCell]:
        """Get only invalid cells."""
        return [cell for cell in self.cells if not cell.is_valid]

    def get_metric_values(self) -> List[float]:
        """Get all metric values from valid cells."""
        return [cell.metric_value for cell in self.get_valid_cells()]

    def get_normalized_values(self) -> List[float]:
        """Get normalized metric values (0-1 range)."""
        valid_values = self.get_metric_values()
        if not valid_values:
            return []

        min_val = min(valid_values)
        max_val = max(valid_values)

        if max_val == min_val:
            return [0.5] * len(valid_values)

        return [(val - min_val) / (max_val - min_val) for val in valid_values]

    def get_statistics(self) -> Dict[str, float]:
        """Get statistical summary of the heatmap data."""
        valid_values = self.get_metric_values()
        if not valid_values:
            return {}

        return {
            "min": min(valid_values),
            "max": max(valid_values),
            "mean": sum(valid_values) / len(valid_values),
            "count": len(valid_values),
            "valid_count": len(self.get_valid_cells()),
            "invalid_count": len(self.get_invalid_cells()),
        }

    def to_matrix(self) -> List[List[Optional[float]]]:
        """Convert heatmap data to a 2D matrix for visualization."""
        matrix = []

        for y_val in self.y_values:
            row = []
            for x_val in self.x_values:
                cell = self.get_cell(x_val, y_val)
                if cell and cell.is_valid:
                    row.append(cell.metric_value)
                else:
                    row.append(None)
            matrix.append(row)

        return matrix

    def get_parameter_combinations(self) -> List[Dict[str, Any]]:
        """Get all parameter combinations represented in this heatmap."""
        combinations = []
        for cell in self.cells:
            if cell.is_valid:
                combinations.append(
                    {
                        self.x_parameter: cell.x_value,
                        self.y_parameter: cell.y_value,
                        "combination_id": cell.parameter_combination_id,
                        "metric_value": cell.metric_value,
                    }
                )
        return combinations


