## What

- Add OrderPolicy (min_qty, min_notional, lot_size, qty_step, action_below_min)
- Commission handling in FillOrderRequest & ExecuteOrderUC
- SQL persistence for policy; events; idempotency enforced

## Why

- Enforce trading policy at entry
- Deterministic idempotency
- Better testability & observability via events

## Notes

- DB: add columns op_min_qty, op_min_notional, op_lot_size, op_qty_step, op_action_below_min
- Tests: use factory for orders (idempotency_key default)
- Event IDs now uuid4

## Checks

- [ ] ruff clean
- [ ] mypy clean
- [ ] pytest (unit+integration)
- [ ] Manual smoke on /v1/\*
