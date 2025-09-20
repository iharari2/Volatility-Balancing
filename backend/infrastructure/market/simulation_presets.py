# =========================
# backend/infrastructure/market/simulation_presets.py
# =========================
from __future__ import annotations
from typing import Dict, Any, List
from enum import Enum


class SimulationPreset(Enum):
    """Predefined simulation presets for common trading scenarios."""

    DAY_TRADING = "day_trading"
    SWING_TRADING = "swing_trading"
    LONG_TERM_INVESTING = "long_term_investing"
    HIGH_FREQUENCY = "high_frequency"
    CONSERVATIVE = "conservative"
    AGGRESSIVE = "aggressive"


class SimulationPresetManager:
    """Manages simulation presets for different trading strategies."""

    @staticmethod
    def get_preset_config(preset: SimulationPreset) -> Dict[str, Any]:
        """Get configuration for a specific simulation preset."""
        presets = {
            SimulationPreset.DAY_TRADING: {
                "name": "Day Trading",
                "description": "High-frequency intraday trading with tight thresholds",
                "position_config": {
                    "trigger_threshold_pct": 0.005,  # 0.5% - very sensitive
                    "rebalance_ratio": 0.3,  # Smaller position changes
                    "commission_rate": 0.001,  # Standard commission
                    "min_notional": 50,  # Lower minimum
                    "allow_after_hours": False,  # Only during market hours
                    "guardrails": {
                        "min_stock_alloc_pct": 0.1,  # 10% minimum
                        "max_stock_alloc_pct": 0.9,  # 90% maximum
                        "max_orders_per_day": 50,  # High frequency
                    },
                },
                "intraday_interval_minutes": 5,  # 5-minute intervals
                "include_after_hours": False,
                "detailed_trigger_analysis": True,
            },
            SimulationPreset.SWING_TRADING: {
                "name": "Swing Trading",
                "description": "Medium-term position changes with moderate thresholds",
                "position_config": {
                    "trigger_threshold_pct": 0.02,  # 2% - moderate sensitivity
                    "rebalance_ratio": 1.6667,  # Balanced position changes (5/3 ratio)
                    "commission_rate": 0.001,
                    "min_notional": 100,
                    "allow_after_hours": True,
                    "guardrails": {
                        "min_stock_alloc_pct": 0.2,  # 20% minimum
                        "max_stock_alloc_pct": 0.8,  # 80% maximum
                        "max_orders_per_day": 20,  # Moderate frequency
                    },
                },
                "intraday_interval_minutes": 30,  # 30-minute intervals
                "include_after_hours": True,
                "detailed_trigger_analysis": True,
            },
            SimulationPreset.LONG_TERM_INVESTING: {
                "name": "Long-term Investing",
                "description": "Conservative long-term position management",
                "position_config": {
                    "trigger_threshold_pct": 0.05,  # 5% - less sensitive
                    "rebalance_ratio": 0.2,  # Smaller position changes
                    "commission_rate": 0.001,
                    "min_notional": 500,  # Higher minimum
                    "allow_after_hours": True,
                    "guardrails": {
                        "min_stock_alloc_pct": 0.3,  # 30% minimum
                        "max_stock_alloc_pct": 0.7,  # 70% maximum
                        "max_orders_per_day": 5,  # Low frequency
                    },
                },
                "intraday_interval_minutes": 60,  # 1-hour intervals
                "include_after_hours": True,
                "detailed_trigger_analysis": False,  # Performance optimization
            },
            SimulationPreset.HIGH_FREQUENCY: {
                "name": "High Frequency Trading",
                "description": "Ultra-high frequency trading with minimal thresholds",
                "position_config": {
                    "trigger_threshold_pct": 0.001,  # 0.1% - extremely sensitive
                    "rebalance_ratio": 0.1,  # Very small position changes
                    "commission_rate": 0.0005,  # Lower commission
                    "min_notional": 25,  # Very low minimum
                    "allow_after_hours": False,
                    "guardrails": {
                        "min_stock_alloc_pct": 0.05,  # 5% minimum
                        "max_stock_alloc_pct": 0.95,  # 95% maximum
                        "max_orders_per_day": 200,  # Very high frequency
                    },
                },
                "intraday_interval_minutes": 1,  # 1-minute intervals
                "include_after_hours": False,
                "detailed_trigger_analysis": True,
            },
            SimulationPreset.CONSERVATIVE: {
                "name": "Conservative Strategy",
                "description": "Risk-averse approach with wide guardrails",
                "position_config": {
                    "trigger_threshold_pct": 0.08,  # 8% - less sensitive
                    "rebalance_ratio": 0.15,  # Small position changes
                    "commission_rate": 0.001,
                    "min_notional": 200,
                    "allow_after_hours": True,
                    "guardrails": {
                        "min_stock_alloc_pct": 0.4,  # 40% minimum
                        "max_stock_alloc_pct": 0.6,  # 60% maximum
                        "max_orders_per_day": 3,  # Very low frequency
                    },
                },
                "intraday_interval_minutes": 120,  # 2-hour intervals
                "include_after_hours": True,
                "detailed_trigger_analysis": False,
            },
            SimulationPreset.AGGRESSIVE: {
                "name": "Aggressive Strategy",
                "description": "High-risk, high-reward approach with tight guardrails",
                "position_config": {
                    "trigger_threshold_pct": 0.01,  # 1% - sensitive
                    "rebalance_ratio": 0.8,  # Large position changes
                    "commission_rate": 0.001,
                    "min_notional": 50,
                    "allow_after_hours": True,
                    "guardrails": {
                        "min_stock_alloc_pct": 0.05,  # 5% minimum
                        "max_stock_alloc_pct": 0.95,  # 95% maximum
                        "max_orders_per_day": 30,  # High frequency
                    },
                },
                "intraday_interval_minutes": 15,  # 15-minute intervals
                "include_after_hours": True,
                "detailed_trigger_analysis": True,
            },
        }

        return presets.get(preset, {})

    @staticmethod
    def get_all_presets() -> List[Dict[str, Any]]:
        """Get all available simulation presets."""
        presets = []
        for preset in SimulationPreset:
            config = SimulationPresetManager.get_preset_config(preset)
            config["preset_id"] = preset.value
            presets.append(config)
        return presets

    @staticmethod
    def get_preset_by_name(name: str) -> Dict[str, Any]:
        """Get preset configuration by name."""
        for preset in SimulationPreset:
            config = SimulationPresetManager.get_preset_config(preset)
            if config.get("name", "").lower() == name.lower():
                config["preset_id"] = preset.value
                return config
        return {}

    @staticmethod
    def validate_preset_config(config: Dict[str, Any]) -> List[str]:
        """Validate a preset configuration."""
        errors = []

        if "position_config" not in config:
            errors.append("Missing position_config")
            return errors

        pos_config = config["position_config"]

        # Validate trigger threshold
        if "trigger_threshold_pct" not in pos_config:
            errors.append("Missing trigger_threshold_pct")
        elif not 0 < pos_config["trigger_threshold_pct"] < 1:
            errors.append("trigger_threshold_pct must be between 0 and 1")

        # Validate rebalance ratio
        if "rebalance_ratio" not in pos_config:
            errors.append("Missing rebalance_ratio")
        elif not 0 < pos_config["rebalance_ratio"] <= 1:
            errors.append("rebalance_ratio must be between 0 and 1")

        # Validate guardrails
        if "guardrails" not in pos_config:
            errors.append("Missing guardrails")
        else:
            guardrails = pos_config["guardrails"]
            if "min_stock_alloc_pct" not in guardrails:
                errors.append("Missing min_stock_alloc_pct")
            elif not 0 <= guardrails["min_stock_alloc_pct"] <= 1:
                errors.append("min_stock_alloc_pct must be between 0 and 1")

            if "max_stock_alloc_pct" not in guardrails:
                errors.append("Missing max_stock_alloc_pct")
            elif not 0 <= guardrails["max_stock_alloc_pct"] <= 1:
                errors.append("max_stock_alloc_pct must be between 0 and 1")

            if guardrails.get("min_stock_alloc_pct", 0) >= guardrails.get("max_stock_alloc_pct", 1):
                errors.append("min_stock_alloc_pct must be less than max_stock_alloc_pct")

        return errors
