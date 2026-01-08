# Operating Model (24x7 Backend)

## 1) Purpose and principles

- Trade continues even if GUI is off; the backend is the source of truth.
- Clean separation: TradingOrchestrator decides intent; ExecutionWorker performs fills.
- Idempotency and auditability are required for every tick and every action.
- Market data and notifications must never block trading.
- Strong tenant isolation: every read/write is scoped by tenant_id.

## 2) State model (3 domains)

### Positions DB (canonical)
- Portfolios and Positions (Position is state only; no trigger/guardrail thresholds stored).
- Orders (intent) and Trades/Executions (actual fills).
- Aggregates include cumulative commissions and dividends (gross/net as defined).

### Config store
- Triggers, guardrails, trading policies, commission rate configuration.
- Extended-hours preference and price policy (MID/LAST/BID/ASK).

### Event log (immutable)
- Timeline used for audit, debugging, analytics, and simulation replay.
- Every evaluation step yields an event row (HOLD included).
- Simulation uses its own repositories/tables and timeline; never writes to production state.

## 3) 24x7 Trading workflow (5-minute tick)

### Schedule
- EventBridge schedule: `rate(5 minutes)` -> TradingOrchestrator.

### TradingOrchestrator responsibilities
- Load ACTIVE positions by tenant_id.
- Determine session for each symbol: REGULAR | EXTENDED | CLOSED.
- Fetch quote via provider interface (no direct yfinance dependency in core flow).
- Evaluate triggers and guardrails using domain services.
- Always write EvaluationEvent (HOLD included).
- Enqueue OrderIntent when action is allowed.
- Idempotency: enforce `dedupe_key` and/or `(tick_id, position_id)` uniqueness.

### OrderIntent queue
- SQS OrderIntent queue with DLQ for failed processing.
- OrderIntent is the durable intent message; execution is asynchronous.

### ExecutionWorker responsibilities
- Execute via paper broker now; broker adapter later.
- Compute commissions using the commission snapshot stored on the order.
- Update Position state (qty, cash, anchor, aggregates).
- Append Execution/Trade event and PositionUpdated event.

## 4) Market hours and extended hours policy

- User choice: allow or disallow extended hours.
- Price policy choice: MID (default) | LAST | BID | ASK.
- Logging requirement: every EvaluationEvent includes session, price_policy, and price_effective.
- If extended hours are not allowed, orchestrator logs CLOSED and takes no action.

## 5) Corporate Actions: Dividends (NEW)

- Dividends are handled by a separate corporate-actions workflow; not part of trigger/guardrail logic.
- Two scheduled jobs (EventBridge), daily off-hours:
  - DividendIngestion: fetch announcements via provider interface; store DividendAnnouncement; log DividendAnnouncementEvent.
  - DividendProcessing: process ex-date and pay-date.
    - On ex-date: compute entitlement using qty at ex-date; record DividendAccrued event; update dividend_receivable.
    - On pay-date: move net dividend to Position.cash; update total_dividends_received (gross/net as defined); log DividendPaidEvent.
- Correctness when qty changes after ex-date: entitlement is fixed based on ex-date holdings.

### Minimal entity fields
- DividendAnnouncement: symbol, ex_date, pay_date, amount_per_share, withholding_tax_pct (optional), source.
- DividendAccrual: qty_eligible, gross, withholding, net.
- Position aggregates: total_dividends_net (and/or gross), dividend_receivable.

## 6) Event log schema overview (minimum required fields)

All events must include: tenant_id, portfolio_id, position_id, symbol, ts, and correlation ids (tick_id or corporate_action_id).

- EvaluationEvent: session, price_policy, price_effective, trigger_decision, guardrail_decision, action, reason, deltas.
- OrderIntent (queued): action, qty, price_policy, commission_snapshot, dedupe_key, tick_id.
- Execution/Trade event: executed_qty, executed_price, commission, broker_ref, tick_id.
- PositionUpdated event: qty, cash, anchor, aggregates, tick_id.
- DividendAnnouncement event: corporate_action_id, source, announcement fields.
- DividendAccrued event: corporate_action_id, qty_eligible, gross, withholding, net.
- DividendPaid event: corporate_action_id, cash_delta, total_dividends_net.

## 7) Testing rules

- Unit + integration tests must run offline by default.
- Any provider network tests must be explicitly marked (e.g., pytest mark "live") and skipped in CI.
- Provide deterministic fake providers for quotes and dividends for tests and local dev.

## What this ensures

- Trading continues on schedule without a GUI.
- Intent and execution are cleanly separated and auditable.
- Every decision and fill is traceable, idempotent, and tenant-scoped.
- Corporate actions are correct and isolated from trading logic.
- Market data and notifications cannot block trading.
