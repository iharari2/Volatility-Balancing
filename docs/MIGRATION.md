MIGRATION.md (drop-in)
Summary

We embedded an OrderPolicy on Position, added commission handling to fills, tightened SELL guardrails, and made event IDs unique. The API now accepts order_policy on position creation and commission on fills. orders.idempotency_key is NOT NULL.

DB changes
Positions

Adds nullable columns (non-breaking):

op_min_qty (float)

op_min_notional (float)

op_lot_size (float)

op_qty_step (float)

op_action_below_min (varchar)

Orders

idempotency_key is NOT NULL.

SQL (PostgreSQL)
ALTER TABLE positions
ADD COLUMN op_min_qty DOUBLE PRECISION,
ADD COLUMN op_min_notional DOUBLE PRECISION,
ADD COLUMN op_lot_size DOUBLE PRECISION,
ADD COLUMN op_qty_step DOUBLE PRECISION,
ADD COLUMN op_action_below_min VARCHAR(16);

ALTER TABLE orders
ALTER COLUMN idempotency_key SET NOT NULL;

SQLite (dev)

Easiest: delete vb.sqlite and restart; schema auto-creates.

If you must migrate in-place, use the standard \_new copy/rename pattern (SQLite cannot ALTER COLUMN):

CREATE TABLE positions_new (...) with new columns,

INSERT INTO positions_new (...) SELECT ... FROM positions;

DROP TABLE positions;

ALTER TABLE positions_new RENAME TO positions;

For orders.idempotency_key, guarantee no NULLs before creating new table with NOT NULL.

API surface (breaking/observable)

POST /v1/positions

body supports optional order_policy:

{
"ticker": "ZIM",
"qty": 0,
"cash": 10000,
"order_policy": {
"min_qty": 0.0,
"min_notional": 0.0,
"lot_size": 0.0,
"qty_step": 0.0,
"action_below_min": "hold"
}
}

POST /v1/orders/{order_id}/fill

body supports optional commission (default 0.0):

{ "qty": 2.0, "price": 10.0, "commission": 1.0 }

Health endpoint is /v1/healthz.

Behavior changes

Order policy (applied to requested fill qty after rounding/clamping):

Below min?

reject → order status rejected, event fill_rejected_below_min, no position change.

otherwise (hold) → response skipped, event fill_skipped_below_min, no position change.

clip reserved (not implemented yet).

Commission:

BUY: cash -= price \* qty + commission

SELL: cash += price \* qty - commission

SELL guardrail: if qty > position.qty → raise GuardrailBreach, no fill event.

Event IDs: we now generate unique IDs per event to avoid UNIQUE violations.

Test updates you may need

When calling FillOrderRequest, include commission as needed (defaults to 0.0).

If you create orders directly in tests, set idempotency_key (column is NOT NULL).

Expect SELL-insufficient-qty to error before any “filled” event is emitted.

Quick smoke

# health

curl -s http://localhost:8000/v1/healthz

# create position with policy

curl -s -X POST localhost:8000/v1/positions \
 -H 'Content-Type: application/json' \
 -d '{"ticker":"AAA","qty":0,"cash":1000,
"order_policy":{"min_qty":0,"min_notional":0,"lot_size":0,"qty_step":0,"action_below_min":"hold"}}'
