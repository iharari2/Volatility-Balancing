# Volatility Balancing – Test Scenarios

This document defines a set of **golden scenarios** for validating the correctness of Volatility Balancing at both the **domain level** (pure logic) and **orchestrator level** (end-to-end flows with in-memory adapters).

These scenarios are the reference for unit tests, integration tests, and manual/visual verification.

---

## Scenario A – No Trade Inside Trigger Band

**Purpose:**  
Verify that no trades are generated when price movements stay within the trigger band. This validates that `PriceTrigger` does not fire spuriously and that the orchestrator does not create unintended orders.

### Initial State

- Portfolio: `PBAL-001`
- Asset: `ABC`
- Position:
  - Cash: `10,000`
  - Shares: `0`
  - Anchor price: `100`
  - `total_commission_paid`: `0`
  - `total_dividends_received`: `0`
- No existing orders or trades.

### Configuration

- Trigger config:
  - `up_threshold_pct`: `+3%`
  - `down_threshold_pct`: `-3%`
- Guardrail config:
  - `min_stock_pct`: `0%`
  - `max_stock_pct`: `50%`
  - `max_trade_pct_of_position`: `10%` (used when a trigger fires)
- Commission:
  - Default commission rate: `0.10%` (0.001)
- No special dividend events.

### Price Path

For asset `ABC`:

- `t0`: `100` (anchor)
- `t1`: `101` (+1.0% vs anchor)
- `t2`: `102` (+2.0%)
- `t3`: `101.5` (+1.5%)
- `t4`: `99.9` (−0.1%)

### Expected Behavior

- No `TriggerDecision` with BUY or SELL should be produced (all should be `NONE`).
- No `GuardrailDecision` should be evaluated for actual trades.
- No orders or trades should be created.
- Final state:
  - Cash: `10,000`
  - Shares: `0`
  - `total_commission_paid`: `0`
  - `total_dividends_received`: `0`

---

## Scenario B – Simple Buy and Sell Cycle

**Purpose:**  
Validate that triggers fire when thresholds are crossed, guardrails allow trades within limits, and positions update correctly for a simple buy then sell sequence with commissions.

### Initial State

- Portfolio: `PBAL-001`
- Asset: `ABC`
- Position:
  - Cash: `10,000`
  - Shares: `0`
  - Anchor price: `100`
  - `total_commission_paid`: `0`
  - `total_dividends_received`: `0`

### Configuration

- Trigger config:
  - `up_threshold_pct`: `+3%`
  - `down_threshold_pct`: `-3%`
- Guardrail config:
  - `min_stock_pct`: `0%`
  - `max_stock_pct`: `50%` (at most 50% of portfolio in stock)
  - `max_trade_pct_of_position`: `10%` of portfolio value per trigger event
- Commission:
  - Default commission rate: `0.10%` (0.001)
- No dividend events for this scenario.

### Price Path

For asset `ABC`:

- `t0`: `100` (anchor)
- `t1`: `96.9` (≈ −3.1% → **BUY trigger** expected)
- `t2`: `100` (back near anchor → no trigger)
- `t3`: `103.2` (≈ +3.2% → **SELL trigger** expected)

### Expected Behavior (Conceptual)

1. **At `t1` (96.9):**
   - `PriceTrigger` should produce a BUY trigger (down beyond −3%).
   - `GuardrailEvaluator` should allow the trade (current stock_pct = 0%, under 50%).
   - Order:
     - Side: BUY
     - Notional size: about 10% of portfolio value (based on config), within guardrails.
     - `commission_rate_snapshot` = 0.10%.
   - Execution:
     - One BUY trade at ~96.9.
     - `commission` charged accordingly.
   - Position:
     - Cash decreases by trade notional + commission.
     - Shares increase by executed quantity.
     - `total_commission_paid` > 0.

2. **At `t2` (100):**
   - Price near anchor; no trigger (inside band).
   - No new orders or trades.

3. **At `t3` (103.2):**
   - `PriceTrigger` should produce a SELL trigger (> +3% vs anchor).
   - `GuardrailEvaluator` should allow SELL (reduces stock exposure).
   - Order:
     - Side: SELL
     - Size consistent with `max_trade_pct_of_position` and holdings.
   - Execution:
     - One SELL trade around 103.2.
     - Additional commission charged.
   - Position:
     - Shares reduced appropriately.
     - Cash increased by proceeds minus commission.
     - `total_commission_paid` reflects both trades.

### Final State (Qualitative)

- There must be:
  - 1 BUY trade, 1 SELL trade, correct directions.
  - Non-zero `total_commission_paid`.
- Stock allocation and cash should be closer to initial balance after the full cycle, consistent with the rebalancing logic (exact numbers depend on precise trade sizing rules but must be deterministic and testable).

---

## Scenario C – Guardrail Blocking Trade

**Purpose:**  
Validate that guardrails **block** trades when the portfolio is beyond allowed allocation, even if a trigger fires.

### Initial State

- Portfolio: `PBAL-001`
- Asset: `ABC`
- Position:
  - Total portfolio value: `10,000` (implied)
  - Current:
    - Cash: `4,000`
    - Stock value: `6,000` (i.e., 60% in stock)
  - Shares: number consistent with 6,000 at anchor price (e.g., 60 shares at 100)
  - Anchor price: `100`
  - `total_commission_paid`: some previous value, not critical
  - `total_dividends_received`: not critical

### Configuration

- Trigger config:
  - `up_threshold_pct`: `+3%`
  - `down_threshold_pct`: `-3%`
- Guardrail config:
  - `min_stock_pct`: `0%`
  - `max_stock_pct`: `50%`
  - `max_trade_pct_of_position`: `10%`
- Commission:
  - Default commission rate: `0.10%`.

### Price Path

For asset `ABC`:

- `t0`: `100` (anchor, ~60% in stock)
- `t1`: `103.5` (~ +3.5% → BUY trigger *might* occur depending on logic, OR treat as SELL scenario, see note below)

> **Note:**  
> For testing guardrail blocking, define it explicitly as:
> - If configuration would cause a **BUY** when already above `max_stock_pct`, guardrails must block.  
> Alternatively, invert to SELL scenario (above target, SELL allowed; BUY blocked).  
> Pick one consistent rule and test it.

### Expected Behavior

- `PriceTrigger` produces a trigger decision consistent with configuration (e.g., BUY or SELL).
- `GuardrailEvaluator` evaluates the proposed direction:
  - If proposed action would increase stock allocation when already at 60% (> 50% max), it must **block**.
- No new order or trade is created for the blocked action.
- Final position:
  - Stock allocation remains at 60% (no change from this event).
  - Cash unchanged except for market value change (if tracked separately).
  - No additional commission.

---

## Scenario D – Portfolio Creation and Adding Positions

**Purpose:**  
Verify correct creation of portfolio and positions, including adding new assets and enforcing basic invariants (no negative cash, consistent totals, etc.). This scenario is essential for testing repositories and simple flows before any triggers or guardrails.

### Initial State

- System has no portfolios or positions for tenant `T-001`.

### Steps

1. **Create a portfolio**
   - Create portfolio `PBAL-NEW-001` for tenant `T-001`.
   - Initial cash deposit: `50,000`.
   - No positions yet.

2. **Add first asset position via trade**
   - Asset: `ABC`
   - Price: `100`
   - Commission rate: `0.10%`.
   - Place BUY order for 200 shares at 100.
   - Execute trade at 100 with commission applied.

3. **Add second asset position via trade**
   - Asset: `XYZ`
   - Price: `50`
   - Commission rate: same (unless overridden).
   - Place BUY order for 300 shares at 50.
   - Execute trade at 50 with commission applied.

### Expected Behavior

- Portfolio after step 1:
  - Cash: `50,000`
  - No asset positions.
- After first trade:
  - Cash: `50,000 - (200 * 100) - commission_1`
  - Position `ABC`:
    - Shares: `200`
    - `avg_cost`: `100` (plus optional commission embedding rule, depending on design)
  - `total_commission_paid` includes `commission_1`.
- After second trade:
  - Cash: `previous_cash - (300 * 50) - commission_2`
  - Position `XYZ`:
    - Shares: `300`
    - `avg_cost`: `50` (with same rule as above)
  - `total_commission_paid` includes `commission_1 + commission_2`.
- Invariants:
  - No negative cash.
  - Positions match executed trades.
  - Portfolio total value (cash + positions) is consistent with executed trades.

This scenario can be used for:

- Repository tests (create/read/update portfolio and positions).
- Integration tests for `SubmitOrderUC` + `ExecuteOrderUC` + `IPositionRepository`.

---

## Scenario E – Simulation vs Trade Consistency

**Purpose:**  
Ensure that **simulation** and **live trading flows** yield consistent decisions when using the same price series and configuration, and that simulation remains read-only on production state.

### Initial State

- Portfolio: `PBAL-SIM-001`
- Asset: `ABC`
- Position:
  - Cash: `10,000`
  - Shares: `0`
  - Anchor: `100`
  - `total_commission_paid`: `0`
  - `total_dividends_received`: `0`
- Config (same for simulation and live):
  - Trigger thresholds: ±3%
  - Guardrails: 0–50% stock, `max_trade_pct_of_position` = 10%
  - Commission rate: `0.10%`

### Price Path (Shared)

Same path used for both simulation and live trading:

- `t0`: `100`
- `t1`: `96.9` (down)
- `t2`: `100`
- `t3`: `103.2` (up)

### Two Modes

1. **Live Mode**
   - Use `LiveTradingOrchestrator` with:
     - Real `IPositionRepository` (or test repository)
     - Real domain services (`PriceTrigger`, `GuardrailEvaluator`)
   - Run through the price series step by step.

2. **Simulation Mode**
   - Use `SimulationOrchestrator` with:
     - `IHistoricalPriceProvider` returning the same price series.
     - Separate `ISimulationPositionRepository` (isolated storage).
   - Run through the same series.

### Expected Behavior

- For each timestep, the **trigger decisions** and **guardrail decisions** must be the same in both modes (given identical config and state).
- The **sequence of intended trades** (BUY/SELL with quantities) must match between live mode and simulation.
- Simulation:
  - Writes only to simulation repositories (e.g., `SimulationResult`, `SimPosition`).
  - Does **not** modify live `Position`, `Order`, or `Trade` entities.
- Optional: final simulated portfolio state should be numerically comparable to the live portfolio state (within the limits of how execution is modeled).

This scenario is critical to validate:

- Domain logic is shared correctly between live and simulation.
- Infrastructure and repositories are the only differences between the two modes.
- No hidden coupling between simulation and production state.

---

## Notes for Test Implementation

- Scenario A, B, C are ideal for:
  - Unit tests of `PriceTrigger` and `GuardrailEvaluator`.
  - Integration tests of `LiveTradingOrchestrator` with in-memory adapters.

- Scenario D is ideal for:
  - Repository tests.
  - End-to-end order + execution + position update tests.

- Scenario E is ideal for:
  - Consistency tests between `LiveTradingOrchestrator` and `SimulationOrchestrator`.
  - Ensuring simulation isolation guarantees are upheld.

These scenarios should be treated as **canonical**:  
if implementation and tests diverge from them, the scenarios win and the code must be corrected.
