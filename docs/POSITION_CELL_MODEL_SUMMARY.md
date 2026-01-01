# Position Cell Model - Summary

## Overview

The Position Cell Model treats each position as a **self-contained trading cell** that combines cash and stock. This model provides better isolation, clearer performance measurement, and more intuitive management.

## Core Concept

### Position as Cell

```
Position Cell = Cash + Stock
Total Value = Cash + (Qty × Current Price)
```

Each position:

- Has its own cash balance (`Position.cash`)
- Has its own stock holdings (`Position.qty`)
- Has its own strategy configuration
- Trades independently
- Measures performance vs stock performance

## Key Benefits

1. **Clear Ownership**: Cash belongs to the position, not the portfolio
2. **Independent Trading**: Each position trades independently with its own cash
3. **Performance Measurement**: Easy to compare position performance vs stock performance
4. **Simpler Mental Model**: One position = one cell = one strategy
5. **Better Isolation**: Positions don't share cash, reducing complexity

## GUI Requirements

### Display Position as Cell

The GUI should show each position as a unified cell displaying:

1. **Value Breakdown**

   - Cash component (amount and %)
   - Stock component (value and %)
   - Total value
   - Visual representation (bar/pie chart)

2. **Performance Metrics**

   - Position return (total value change)
   - Stock return (price change)
   - Alpha (outperformance: position return - stock return)
   - Visual indicators (colors, arrows, badges)

3. **Strategy Status**
   - Active/Paused indicator
   - Trigger thresholds
   - Guardrail limits
   - Quick configuration access

### Data and Trade Per Position

- All data scoped to position
- All trading actions scoped to position
- Strategy applied per position
- Performance measured per position

### KPI Measurement

**Position Performance vs Stock Performance:**

- **Position Return**: `((current_total_value - initial_total_value) / initial_total_value) × 100`
- **Stock Return**: `((current_price - initial_price) / initial_price) × 100`
  - Where `initial_price` is the anchor price at position creation (starting price)
  - Both returns are measured from the same starting point (position creation)
- **Alpha**: `position_return - stock_return`

**Visual Display:**

- Show position return prominently
- Show stock return for comparison
- Highlight alpha (green if positive, red if negative)
- Use icons: ✓ for outperforming, ✗ for underperforming

## Documentation

### Architecture

- **[Position Cell Model](architecture/position-cell-model.md)** - Complete architecture documentation
- **[Position Performance KPIs](architecture/position-performance-kpis.md)** - Performance measurement details
- **[Domain Model](architecture/domain-model.md)** - Updated with position cell concept

### Product/GUI

- **[Position Cell GUI Spec](product/POSITION_CELL_GUI_SPEC.md)** - Detailed GUI specification
- **[GUI Design](product/GUI%20design.md)** - Updated with position cell requirements

## Implementation Status

✅ **Completed:**

- Cash moved from `PortfolioCash` to `Position.cash`
- All code updated to use `Position.cash`
- Documentation created

⏳ **Next Steps (GUI Implementation):**

- Update position list view to show cells
- Add performance comparison (position vs stock)
- Display alpha prominently
- Show cash + stock breakdown visually
- Apply strategy per position in UI

---

_Last updated: 2025-01-XX_







