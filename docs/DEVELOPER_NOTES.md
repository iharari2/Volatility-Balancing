DEVELOPER_NOTES.md (order policy + fills)
OrderPolicy fields

min_qty: smallest orderable quantity.

min_notional: smallest notional (qty \* price).

lot_size: fixed lot granularity (0 → ignore).

qty_step: smallest increment (0 → ignore).

action_below_min: "hold" or "reject" ( "clip" reserved/NYI).

Fill pipeline (ExecuteOrderUC)

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
