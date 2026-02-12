# Volatility Balancing – Agent Rules (Authoritative)

These rules override any existing implementation patterns. Do not "simplify" them away.

## Architecture invariants
1. **Clean Architecture boundaries**
   - Domain: pure business logic only (no HTTP, DB, external calls).
   - Application: use-cases/orchestrators, depends on Domain only.
   - Infrastructure: adapters (DB, providers, broker, web, etc).

2. **Position is state only**
   - A Position must NOT know trigger thresholds or guardrail thresholds.
   - Trigger/guardrail evaluation lives in domain services and/or application use-cases.

3. **Each position has its own cash bucket**
   - PositionCell = (asset + its cash).
   - Positions are independent; no shared cash pool across positions unless explicitly introduced later.

4. **Portfolio is a container**
   - Portfolio groups positions and provides aggregation for analytics.
   - Portfolio does not implement trading logic.

5. **Simulation isolation**
   - Simulation must never write to production Orders/Trades/Positions/Dividends tables/state.
   - Simulation writes only to simulation repositories/tables and emits its own timeline.

6. **Execution model**
   - Order = intent.
   - Trade/Execution = actual fill.
   - Execution is asynchronous conceptually, even if mocked in dev.

7. **UI is a client only**
   - UI never re-implements trigger/guardrail logic.
   - UI renders backend-provided position summaries + event/timeline rows.

8. **Audit/event timeline is first-class**
   - Every evaluation step yields an event row.
   - Timeline rows include: price source, trigger decision, guardrail decision, action + reason, deltas.

9. **Extended-hours policy**
   - User config: allow/disallow extended hours.
   - Price policy choices include at least: MID (default), LAST, BID, ASK.
   - Every timeline row logs the chosen policy and the effective price used.

## Working agreement for agents (Codex)
- Before changing code, check AGENTS.md and follow it.
- Prefer minimal, reversible diffs.
- Always run tests and show results.
- Do not delete working code; refactor by moving + adapting.