# Order Sizing Strategies

## Overview

The Volatility Balancing system supports multiple order sizing strategies that can be selected per position. This extensible design allows for different trading approaches and makes it easy to add new strategies in the future.

## Strategy Pattern Implementation

### Base Interface

All order sizing strategies implement the `OrderSizingStrategy` interface:

```python
class OrderSizingStrategy(ABC):
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
```

### Context Object

The `OrderSizingContext` provides all necessary data for calculations:

```python
@dataclass
class OrderSizingContext:
    current_price: float
    anchor_price: float
    cash: float
    shares: float
    rebalance_ratio: float
    trigger_threshold_pct: float
    side: str  # "BUY" or "SELL"
```

## Available Strategies

### 1. Proportional Strategy (Default)

**Formula:** `ΔQ_raw = (P_anchor / P - 1) × r × ((A + C) / P)`

**Characteristics:**

- Scales proportionally with price deviation from anchor
- Zero order size when current price equals anchor price
- Most conservative and intuitive approach
- Reduces trade sizes by ~97% compared to original formula

**Example:**

- Anchor price: $150
- Current price: $145 (-3.3% change)
- Portfolio value: $10,000
- Rebalance ratio: 0.5
- Raw qty: `(150/145 - 1) × 0.5 × (10000/145) = 1.19 shares`

**Best for:** Conservative trading, minimizing position swings

### 2. Fixed Percentage Strategy

**Formula:**

- BUY: `ΔQ_raw = (cash × r) / P`
- SELL: `ΔQ_raw = -(shares × r)`

**Characteristics:**

- Uses fixed percentage of available resources
- Consistent trade sizes regardless of price deviation
- Simple and predictable
- Good for steady rebalancing

**Example:**

- Cash: $5,000
- Shares: 50
- Rebalance ratio: 0.5
- BUY: `(5000 × 0.5) / 150 = 16.67 shares`
- SELL: `-(50 × 0.5) = -25 shares`

**Best for:** Steady rebalancing, consistent trade sizes

### 3. Original Strategy

**Formula:** `ΔQ_raw = (P_anchor / P) × r × ((A + C) / P)`

**Characteristics:**

- The original aggressive strategy
- Based on total portfolio value
- More aggressive than proportional strategy
- Higher trade volumes

**Example:**

- Anchor price: $150
- Current price: $145
- Portfolio value: $10,000
- Rebalance ratio: 0.5
- Raw qty: `(150/145) × 0.5 × (10000/145) = 35.67 shares`

**Best for:** Aggressive trading, maximum responsiveness

## Strategy Selection

### Configuration

Strategies are selected via the `order_sizing_strategy` parameter in the `OrderPolicy`:

```python
order_policy = OrderPolicy(
    order_sizing_strategy="proportional",  # Default
    rebalance_ratio=0.5,
    # ... other parameters
)
```

### Available Options

- `"proportional"` - Proportional strategy (default)
- `"fixed_percentage"` - Fixed percentage strategy
- `"original"` - Original aggressive strategy

### Factory Pattern

The `OrderSizingStrategyFactory` creates strategy instances:

```python
# Create a strategy
strategy = OrderSizingStrategyFactory.create_strategy("proportional")

# Get available strategies
strategies = OrderSizingStrategyFactory.get_available_strategies()
```

## Adding New Strategies

### Step 1: Create Strategy Class

```python
class MyCustomStrategy(OrderSizingStrategy):
    def calculate_raw_qty(self, context: OrderSizingContext) -> float:
        # Your custom logic here
        return raw_qty

    def get_name(self) -> str:
        return "My Custom Strategy"

    def get_description(self) -> str:
        return "Description of how it works"
```

### Step 2: Register with Factory

```python
class OrderSizingStrategyFactory:
    _strategies = {
        "proportional": ProportionalStrategy,
        "fixed_percentage": FixedPercentageStrategy,
        "original": OriginalStrategy,
        "my_custom": MyCustomStrategy,  # Add your strategy
    }
```

### Step 3: Update Configuration

Add the new strategy to the configuration options in the frontend and API.

## Performance Comparison

| Strategy         | Trade Size | Responsiveness | Risk Level | Use Case             |
| ---------------- | ---------- | -------------- | ---------- | -------------------- |
| Proportional     | Small      | High           | Low        | Conservative trading |
| Fixed Percentage | Medium     | Medium         | Medium     | Steady rebalancing   |
| Original         | Large      | Very High      | High       | Aggressive trading   |

## Integration Points

### Trading System

- `EvaluatePositionUC` uses the selected strategy
- Strategy is determined by position's `OrderPolicy`
- Can be changed per position

### Simulation System

- Both `SimulationUC` and `SimulationUnifiedUC` support strategies
- `SimulationUnifiedUC` uses the same strategies as trading
- Consistent behavior between simulation and live trading

### Frontend

- Strategy selection in configuration panels
- Real-time preview of strategy behavior
- Strategy-specific help text and examples

## Future Enhancements

### Potential New Strategies

1. **Volatility-Adjusted**: Adjusts trade size based on recent volatility
2. **Time-Decay**: Reduces trade size as time passes since last trade
3. **Momentum-Based**: Increases trade size during strong trends
4. **Machine Learning**: Uses ML models to optimize trade sizes

### Configuration Enhancements

1. **Strategy Parameters**: Custom parameters per strategy
2. **Dynamic Switching**: Change strategies based on market conditions
3. **A/B Testing**: Compare strategy performance
4. **Strategy Presets**: Pre-configured strategy combinations

## Best Practices

1. **Start Conservative**: Begin with proportional strategy
2. **Monitor Performance**: Track strategy effectiveness
3. **Test in Simulation**: Always test new strategies in simulation first
4. **Document Changes**: Keep track of strategy modifications
5. **Gradual Rollout**: Introduce new strategies gradually

## Troubleshooting

### Common Issues

1. **Strategy Not Found**: Check strategy name spelling
2. **Unexpected Trade Sizes**: Verify strategy parameters
3. **Performance Issues**: Consider strategy complexity
4. **Configuration Errors**: Validate strategy parameters

### Debug Tools

1. **Strategy Logging**: Log strategy decisions
2. **Performance Metrics**: Track strategy effectiveness
3. **Configuration Validation**: Validate strategy parameters
4. **Simulation Testing**: Test strategies before live use
