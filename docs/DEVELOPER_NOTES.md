# Developer Notes

## Order Policy Fields

- `min_qty`: smallest orderable quantity
- `min_notional`: smallest notional (qty × price)
- `lot_size`: fixed lot granularity (0 → ignore)
- `qty_step`: smallest increment (0 → ignore)
- `action_below_min`: "hold" or "reject" ("clip" reserved/NYI)
- `order_sizing_strategy`: Strategy for calculating order sizes ("proportional", "fixed_percentage", "original")

## Order Sizing Strategies

The system supports multiple order sizing strategies through the Strategy pattern:

### Available Strategies

1. **Proportional** (Default): `ΔQ_raw = (P_anchor / P - 1) × r × ((A + C) / P)`

   - Most conservative, scales with price deviation
   - Zero at anchor price

2. **Fixed Percentage**: Uses fixed percentage of available resources

   - BUY: `(cash × r) / P`
   - SELL: `-(shares × r)`

3. **Original**: `ΔQ_raw = (P_anchor / P) × r × ((A + C) / P)`
   - Original aggressive strategy

### Implementation

- Strategy selection via `OrderSizingStrategyFactory`
- Context object provides all necessary data
- Strategies are stateless and thread-safe
- Easy to add new strategies by implementing `OrderSizingStrategy` interface

### Usage

```python
# In EvaluatePositionUC
strategy = OrderSizingStrategyFactory.create_strategy(position.order_policy.order_sizing_strategy)
context = OrderSizingContext(current_price, anchor_price, cash, shares, rebalance_ratio, trigger_threshold_pct, side)
raw_qty = strategy.calculate_raw_qty(context)
```

## Fill Pipeline (ExecuteOrderUC)

Load order & position.

q_req = abs(request.qty)
q_req = policy.round_qty(q_req)
q_req = policy.clamp_to_lot(q_req)

If below min_qty/min_notional:

reject → order.status="rejected", event fill_rejected_below_min.

else (hold) → respond skipped, event fill_skipped_below_min.

Guardrails:

SELL: if q_req > pos.qty → raise GuardrailBreach.

Apply fill & commission:

BUY: pos.qty += q_req; pos.cash -= (q_req \* price) + commission

SELL: pos.qty -= q_req; pos.cash += (q_req \* price) - commission

Persist: save position → set order filled → append order_filled event
