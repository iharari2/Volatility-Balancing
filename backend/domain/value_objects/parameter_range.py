# =========================
# backend/domain/value_objects/parameter_range.py
# =========================

from dataclasses import dataclass
from typing import List, Union
from enum import Enum


class ParameterType(Enum):
    """Types of parameters that can be optimized."""

    FLOAT = "float"
    INTEGER = "integer"
    BOOLEAN = "boolean"
    CATEGORICAL = "categorical"


@dataclass(frozen=True)
class ParameterRange:
    """Defines a range of values for a parameter to be optimized."""

    min_value: Union[float, int, bool, str]
    max_value: Union[float, int, bool, str]
    step_size: Union[float, int]
    parameter_type: ParameterType
    name: str
    description: str = ""
    categorical_values: List[str] = None

    def __post_init__(self):
        """Validate the parameter range after initialization."""
        if self.parameter_type == ParameterType.CATEGORICAL:
            if not self.categorical_values:
                raise ValueError("Categorical parameters must specify categorical_values")
            if len(self.categorical_values) < 2:
                raise ValueError("Categorical parameters must have at least 2 values")
        else:
            if self.categorical_values is not None:
                raise ValueError("Non-categorical parameters cannot have categorical_values")

            if self.min_value >= self.max_value:
                raise ValueError("min_value must be less than max_value")

            if self.step_size <= 0:
                raise ValueError("step_size must be positive")

    def generate_values(self) -> List[Union[float, int, bool, str]]:
        """Generate all possible values for this parameter range."""
        if self.parameter_type == ParameterType.CATEGORICAL:
            return self.categorical_values.copy()

        values = []
        current = self.min_value

        while current <= self.max_value:
            if self.parameter_type == ParameterType.INTEGER:
                values.append(int(current))
            else:
                values.append(current)
            current += self.step_size

        return values

    def get_value_count(self) -> int:
        """Get the number of possible values for this parameter."""
        if self.parameter_type == ParameterType.CATEGORICAL:
            return len(self.categorical_values)

        return int((self.max_value - self.min_value) / self.step_size) + 1

    def is_valid_value(self, value: Union[float, int, bool, str]) -> bool:
        """Check if a value is valid for this parameter range."""
        if self.parameter_type == ParameterType.CATEGORICAL:
            return value in self.categorical_values

        return self.min_value <= value <= self.max_value

    def normalize_value(self, value: Union[float, int, bool, str]) -> float:
        """Normalize a value to a 0-1 range for optimization algorithms."""
        if self.parameter_type == ParameterType.CATEGORICAL:
            if value not in self.categorical_values:
                raise ValueError(f"Value {value} not in categorical values")
            return self.categorical_values.index(value) / (len(self.categorical_values) - 1)

        if not self.is_valid_value(value):
            raise ValueError(f"Value {value} not in valid range")

        return (value - self.min_value) / (self.max_value - self.min_value)

    def denormalize_value(self, normalized_value: float) -> Union[float, int, bool, str]:
        """Convert a normalized value back to the original parameter space."""
        if self.parameter_type == ParameterType.CATEGORICAL:
            index = int(round(normalized_value * (len(self.categorical_values) - 1)))
            index = max(0, min(index, len(self.categorical_values) - 1))
            return self.categorical_values[index]

        value = self.min_value + normalized_value * (self.max_value - self.min_value)

        if self.parameter_type == ParameterType.INTEGER:
            return int(round(value))

        return value


