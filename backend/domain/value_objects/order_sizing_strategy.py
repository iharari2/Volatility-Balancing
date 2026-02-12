# =========================
# backend/domain/value_objects/order_sizing_strategy.py
# =========================
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict


@dataclass
class OrderSizingContext:
    """Context for order sizing calculations."""
    current_price: float
    anchor_price: float
    cash: float
    shares: float
    rebalance_ratio: float
    trigger_threshold_pct: float
    side: str  # "BUY" or "SELL"


class OrderSizingStrategy(ABC):
    """Abstract base class for order sizing strategies."""
    
    @abstractmethod
    def calculate_raw_qty(self, context: OrderSizingContext) -> float:
        """Calculate raw order quantity using the strategy."""
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """Get the human-readable name of the strategy."""
        pass
    
    @abstractmethod
    def get_description(self) -> str:
        """Get a description of how the strategy works."""
        pass


class ProportionalStrategy(OrderSizingStrategy):
    """
    Strategy: ΔQ_raw = (P_anchor / P - 1) × r × ((A + C) / P)
    
    This strategy scales order size proportionally to price deviation from anchor.
    Zero order size when current price equals anchor price.
    """
    
    def calculate_raw_qty(self, context: OrderSizingContext) -> float:
        total_value = context.shares * context.current_price + context.cash
        raw_qty = (context.anchor_price / context.current_price - 1) * context.rebalance_ratio * (total_value / context.current_price)
        
        # Apply side (BUY = positive, SELL = negative)
        if context.side == "SELL":
            raw_qty = -raw_qty
            
        return raw_qty
    
    def get_name(self) -> str:
        return "Proportional"
    
    def get_description(self) -> str:
        return "Scales with price deviation from anchor. Zero at anchor price."


class FixedPercentageStrategy(OrderSizingStrategy):
    """
    Strategy: Uses fixed percentage of available resources
    
    For BUY: percentage of available cash
    For SELL: percentage of current shares
    """
    
    def calculate_raw_qty(self, context: OrderSizingContext) -> float:
        if context.side == "BUY":
            # Use percentage of available cash
            raw_qty = (context.cash * context.rebalance_ratio) / context.current_price
        else:
            # Use percentage of current shares
            raw_qty = -(context.shares * context.rebalance_ratio)
            
        return raw_qty
    
    def get_name(self) -> str:
        return "Fixed Percentage"
    
    def get_description(self) -> str:
        return "Uses fixed percentage of available cash/shares."


class OriginalStrategy(OrderSizingStrategy):
    """
    Strategy: ΔQ_raw = (P_anchor / P) × r × ((A + C) / P)
    
    The original aggressive strategy that trades based on total portfolio value.
    """
    
    def calculate_raw_qty(self, context: OrderSizingContext) -> float:
        total_value = context.shares * context.current_price + context.cash
        raw_qty = (context.anchor_price / context.current_price) * context.rebalance_ratio * (total_value / context.current_price)
        
        # Apply side (BUY = positive, SELL = negative)
        if context.side == "SELL":
            raw_qty = -raw_qty
            
        return raw_qty
    
    def get_name(self) -> str:
        return "Original"
    
    def get_description(self) -> str:
        return "Original aggressive strategy based on total portfolio value."


class OrderSizingStrategyFactory:
    """Factory for creating order sizing strategies."""
    
    _strategies = {
        "proportional": ProportionalStrategy,
        "fixed_percentage": FixedPercentageStrategy,
        "original": OriginalStrategy,
    }
    
    @classmethod
    def create_strategy(cls, strategy_name: str) -> OrderSizingStrategy:
        """Create a strategy instance by name."""
        if strategy_name not in cls._strategies:
            raise ValueError(f"Unknown strategy: {strategy_name}. Available: {list(cls._strategies.keys())}")
        
        return cls._strategies[strategy_name]()
    
    @classmethod
    def get_available_strategies(cls) -> Dict[str, str]:
        """Get all available strategies with their descriptions."""
        return {
            name: strategy_class().get_description()
            for name, strategy_class in cls._strategies.items()
        }
    
    @classmethod
    def get_strategy_info(cls) -> Dict[str, Dict[str, str]]:
        """Get detailed information about all strategies."""
        return {
            name: {
                "name": strategy_class().get_name(),
                "description": strategy_class().get_description(),
            }
            for name, strategy_class in cls._strategies.items()
        }
