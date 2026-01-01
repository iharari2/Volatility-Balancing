# Golden Tests Debugging Guide

## Common Issues and Fixes

### 1. OrderPolicyConfig Missing

**Symptom**: Order proposal validation fails with "below minimum" errors
**Fix**: Add `OrderPolicyConfig` to ConfigRepo before evaluation

```python
order_policy_config = OrderPolicyConfig(
    min_qty=Decimal("0"),
    min_notional=Decimal("100.0"),
    allow_after_hours=True,
    rebalance_ratio=Decimal("1.6667"),
)
container.config.set_order_policy_config(pos.id, order_policy_config)
```

### 2. Trigger Type Case Mismatch

**Symptom**: AssertionError on `trigger_type == "buy"` (should be "BUY")
**Fix**: Check for uppercase "BUY"/"SELL" (from `_check_triggers`)

### 3. Quantity Sign Issues

**Symptom**: Negative qty errors or wrong direction
**Fix**:

- BUY orders: `trimmed_qty` should be positive (use `abs()` if negative)
- SELL orders: `trimmed_qty` is negative, use `abs()` for submission

### 4. Order Proposal Validation Failures

**Symptom**: `validation["valid"] == False`
**Common Reasons**:

- Below `min_notional` ($100 default)
- Insufficient cash for BUY
- Insufficient shares for SELL
- Market hours check (if `allow_after_hours=False`)
- Order too small (< 0.001 shares)

**Debug**: Check `validation["rejections"]` for specific reason

### 5. ConfigScope Import Error

**Symptom**: `AttributeError: 'InMemoryConfigRepo' object has no attribute 'ConfigScope'`
**Fix**: Import `ConfigScope` from `domain.ports.config_repo`

## Test Structure Checklist

For each scenario test:

- [ ] Create position with anchor_price
- [ ] Set TriggerConfig in ConfigRepo
- [ ] Set GuardrailConfig in ConfigRepo
- [ ] Set OrderPolicyConfig in ConfigRepo (for validation)
- [ ] Set commission_rate in ConfigRepo
- [ ] Use `container.get_evaluate_position_uc()` for evaluation
- [ ] Check `trigger_type` is uppercase ("BUY"/"SELL")
- [ ] Handle order proposal validation gracefully
- [ ] Use `abs()` for SELL order quantities
- [ ] Verify final position state

## Running Tests with Debug Output

```bash
# Run with verbose output
pytest tests/integration/test_golden_scenarios.py -v -s

# Run specific test
pytest tests/integration/test_golden_scenarios.py::TestScenarioB_SimpleBuyAndSellCycle::test_scenario_b_orchestrator_level -v -s

# Show print statements
pytest tests/integration/test_golden_scenarios.py -v -s --capture=no
```


















