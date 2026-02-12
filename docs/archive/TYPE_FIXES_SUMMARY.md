# Type Mismatch Fixes Summary

## Issue
`current_price` parameter comes in as `Decimal` (from market data), but code was doing arithmetic with `float` values like `position.qty`, causing `TypeError: unsupported operand type(s) for *: 'float' and 'decimal.Decimal'`.

## Fixes Applied

All arithmetic operations with `current_price` now convert it to `float` first:

1. **Line 356** - `_check_and_reset_anchor_if_anomalous`: Anchor price comparison
2. **Line 498-501** - `_calculate_order_proposal`: Order sizing calculation
3. **Line 624-629** - `_calculate_order_proposal`: Post-trade allocation calculation
4. **Line 552-577** - `_calculate_order_proposal`: Guardrail trimming and validation
5. **Line 741-742** - `_check_auto_rebalancing`: Current asset value calculation
6. **Line 755-778** - `_check_auto_rebalancing`: BUY rebalancing calculation
7. **Line 787-812** - `_check_auto_rebalancing`: SELL rebalancing calculation
8. **Line 990-993** - `_log_evaluation_event`: P&L calculation
9. **Line 1005-1006** - `_log_evaluation_event`: Price change calculation

## Pattern Used

```python
# Convert to float to avoid Decimal/float type mismatch
current_price_float = float(current_price)
# Then use current_price_float in all calculations
```

## Testing

After these fixes, the evaluation should complete without type errors. Test with:

```bash
# Manual cycle
curl -X POST "http://localhost:8000/v1/trading/cycle?position_id=pos_f0c83651"

# Check for errors in server logs
# Should see evaluation completing successfully
```



