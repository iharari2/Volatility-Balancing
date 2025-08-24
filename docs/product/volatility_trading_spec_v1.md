# Volatility-Triggered Buy/Sell with Guardrails — Functional Specification

## 1. Summary (What & Why)
**What:** Auto-manage a blue-chip equity position using user-defined % thresholds around the last executed trade price. When price rises by ≥X%, **sell**; when it falls by ≥X%, **buy**. Trade size is formula-driven and then trimmed to respect guardrails (cash vs. asset bands). Multiple orders can occur per day; some days none.

**Why:** Deliver semi-passive mean-reversion captures while keeping portfolio within user-tolerant risk bounds and providing auditable reasoning.

---

## 2. Key Definitions & Defaults
- **Anchor price (P_anchor):** Last executed trade price.
- **Trigger threshold (τ):** Default ±3% relative to P_anchor.
- **Commission:** Default 0.01% of order notional.
- **Minimum order threshold (min_notional):** Configurable; default $100.
- **Rebalance ratio (r):** Default 1.6667.
- **Guardrails (g_low, g_high):** Asset% ∈ [25%, 75%].
- **Portfolio state:**
  - A_t = price × shares
  - C_t = Cash value
  - V_t = A_t + C_t

---

## 3. Triggers
- **Sell trigger:** P ≥ P_anchor × (1 + τ)
- **Buy trigger:** P ≤ P_anchor × (1 − τ)
- After trade: reset P_anchor := execution_price.
- **Multiple same-day trades** allowed. Hidden cap = 5/day.

---

## 4. Order Sizing
Formula:
```
ΔQ_raw = (P_anchor / P) × r × ((A + C) / P)
```
- Sell trigger → order −ΔQ_raw (capped by holdings).
- Buy trigger → order +ΔQ_raw (capped by cash & guardrails).
- Fractional shares allowed by default.

---

## 5. Guardrails
- Enforce Asset% ∈ [25%, 75%] post-trade.
- If proposed q breaches guardrail, trim so A'/V' = nearest bound.
- If drifted outside bounds without a trade, auto-rebalance to boundary.

---

## 6. Order Validation
Skip if:
- Notional < min_notional
- Insufficient cash/shares after trim
- Market closed / halted
- In-flight duplicate order

---

## 7. Fees & Accounting
- Commission = notional × 0.0001.
- Buy: C := C − (q×P) − commission.
- Sell: C := C + |q|×P − commission.

---

## 8. Eventing & Reasoning
Every evaluation stores an **Event** with:
- **Type:** `threshold_crossed`, `order_submitted`, `order_trimmed_guardrail`, `order_rejected_min`, `order_filled`, `anchor_updated`, `auto_guardrail_rebalance`, `ex_div_announced`, `ex_div_effective`, `anchor_adjusted_for_dividend`, `dividend_cash_received`
- **Inputs:** P, P_anchor, τ, r, A, C, V, g_low, g_high, min_notional, commission_rate, DPS, withholding_tax_rate, price_source
- **Outputs:** side, quantity, reasoning string, final post-trade state
- **Timeline UI** shows plain-language reasoning.

---

## 9. Ex-Dividend Handling

### Objectives
- Prevent false triggers on ex-div day.
- Correctly adjust portfolio economics.
- Make adjustments transparent.

### Rules
- **Anchor adjustment:** On ex-date with dividend per share (DPS = d), set:
  - `P_anchor := P_anchor − d`
- **Dividend receivable:**
  - Gross = DPS × shares_at_record
  - Net = Gross − (Gross × withholding_tax_rate)
  - Default withholding_tax_rate = 25% (configurable)
- **Valuation:** Use `C_effective = Cash + DividendReceivable` in formulas & guardrails.
- **Pay date:** Move receivable → Cash, clear receivable.

### Events
- `ex_div_announced` {ex_date, pay_date, dps, currency}
- `ex_div_effective` {gross, net, receivable_created}
- `anchor_adjusted_for_dividend` {old_anchor, dps, new_anchor}
- `dividend_cash_received` {amount_net, receivable_cleared}

### UX
- Position Card badge: “Ex-dividend $0.82/sh; Receivable $82.00; Anchor adjusted to $149.18.”
- Cash panel shows Receivable + Paid.

---

## 10. Price Feed Policy
- **Reference price:** Last trade (if age ≤3s & within ±1% of mid); otherwise mid-quote.
- **Execution drift check:** If price moves >20bps from evaluation → submit, re-evaluate.
- **Outlier filter:** Ignore ticks >10σ vs. 1-min volatility.
- **After hours:** Triggers off by default.
- **Events include:** `price_source`, tick age, last trade, mid.

---

## 11. UX (MVP Screens)
- **Strategy Config:** thresholds, rebalance ratio, commission, min order, guardrails, fractional toggle, max orders/day, withholding rate, after-hours toggle.
- **Position Card:** current price, anchor, next action, proposed vs. trimmed qty, projected Asset%.
- **Event Timeline:** inputs → decision → outputs.
- **Performance View:** asset return, portfolio return, P&L, fees, turnover, guardrail breaches.

---

## 12. Success Metrics
- % time within guardrails
- Avg slippage (bps)
- Trade hit rate after triggers
- Turnover & fee drag
- % orders skipped by min_notional
- Dividend capture accuracy

---

## 13. Compliance & Risk
- Disclosures on turnover, fees, and tax.
- Execution policy: market vs. limit per region.
- Audit logs exportable; no PII beyond config.
- Settlement T+1 handling; no negative buying power.

---

## 14. Out of Scope (Next)
- Multi-asset guardrails
- Dynamic thresholds
- DRIP (reinvestment of dividends)
- Smart slicing (TWAP)
- Tax-lot optimization

---

## Defaults Recap
- Trigger threshold: ±3%
- Commission: 0.01%
- Min order: $100
- Rebalance ratio: 1.6667
- Guardrails: [25%, 75%]
- Max orders/day: 5
- Withholding tax: 25%
- Reference price: Last trade (fresh, in-line)

