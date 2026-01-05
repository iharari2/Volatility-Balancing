Position is pure state, it never knows trigger thresholds nor guardrail thresholds

Each position has its own cash bucket (PositionCell = asset + cash); positions are independent

Portfolio is a container of positions (no pooled cash unless explicitly introduced later)

Simulation never modifies production Orders/Trades/Positions/Dividends; uses isolated simulation repos/tables

Execution is modeled async: Order is intent; Trade/Execution is reality

UI must be driven by backend API + event/audit timeline; UI must not re-implement trading logic

Extended-hours trading policy is user-configurable; default price is MID; every event line logs price_source

Every evaluation step produces an event row (at least one line per day; more for intraday)
After writing, summarize it in 8 bullets and stop.