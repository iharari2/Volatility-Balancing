# Product Requirements Document: Volatility-Balancing

## Overview

A deterministic, guardrail-based trading robot for managing equity positions with cash reserves, supporting simulation based on historical data, analytics, and live trading. The system uses a "Position Cell Model" where each position is a self-contained trading cell combining stock and cash with independent strategy configuration.

## Problem Statement

Manual portfolio rebalancing based on volatility is time-consuming and prone to emotional decision-making. This system automates the process using deterministic rules:

- **Trigger-based trading**: Buy when price drops, sell when price rises (relative to an anchor)
- **Guardrail enforcement**: Never exceed allocation limits, preventing over/under-leveraging
- **Audit trail**: Every decision is logged for transparency and analysis

**Target Users**: Individual investors and traders who want systematic, rule-based volatility trading without manual intervention.

## Goals

1. Automate volatility-based trading decisions using deterministic rules
2. Enforce strict guardrails to prevent excessive risk
3. Provide simulation capabilities for backtesting strategies
4. Support parameter optimization to find optimal trigger/guardrail settings
5. Maintain complete audit trail of all trading decisions
6. Short term goal: No direct broker integration: orders are proposals, not auto-executed. Order excuation is assumed by algo based on market price
7. Future goal: Direct broker integration

## Non-Goals

1. High-frequency trading (microsecond execution)
2. Complex derivatives or options trading
3. Multi-asset correlation strategies

---

## Core Features

### Position Cell Model

Each position is a self-contained "cell" with:

- **Stock holding**: Ticker symbol and quantity
- **Cash reserve**: Dedicated cash for this position
- **Anchor price**: Reference price for trigger calculations
- **Strategy config**: Triggers, guardrails, and order policy

Positions operate independently, each with their own volatility trading rules.

### Trading Logic

#### Trigger Mechanism

The system uses an **anchor price** as a baseline and triggers trades when price moves beyond thresholds:

```
Price Change % = ((Current Price - Anchor Price) / Anchor Price) × 100

BUY Trigger:  Price Change % <= -down_threshold_pct  (price dropped)
SELL Trigger: Price Change % >= +up_threshold_pct   (price rose)
```

**Example**: Anchor $100, thresholds ±3%

- Price $97 → BUY trigger (down 3%)
- Price $103 → SELL trigger (up 3%)

#### Order Sizing Formula

```
ΔQ = (P_anchor / P_current - 1) × r × ((Stock_Value + Cash) / P_current)

Where:
  r = rebalance_ratio (default 1.667)
```

#### Guardrail System

| Guardrail                 | Description                          |
| ------------------------- | ------------------------------------ |
| min_stock_pct             | Minimum stock allocation (e.g., 30%) |
| max_stock_pct             | Maximum stock allocation (e.g., 70%) |
| max_trade_pct_of_position | Maximum single trade size            |
| max_orders_per_day        | Daily order limit                    |

Orders are automatically trimmed to respect guardrails. Post-trade validation ensures compliance.

### Simulation Mode

Run backtests on historical data:

- Select ticker and date range
- Configure trigger thresholds and guardrails
- Choose resolution (1min, 5min, 15min, 30min, 1hour, daily)
- Analyze results: total return, trade count, P&L chart, compare simulated results to actual ticker performance
-

### Live Trading Mode

Continuous trading worker that:

- Polls market data at configurable intervals
- Evaluates positions against triggers
- Proposes orders when triggers fire
- Exceute orders with Broker (stub for now) and log commissition
- Logs all decisions to audit trail

### Parameter Optimization

Grid search over parameter combinations:

- Define ranges for trigger thresholds and guardrails
- Run simulations for each combination
- Rank results by metrics (Sharpe ratio, total return, max drawdown)
- Visualize results with heatmaps

### Analytics & Reporting

- Portfolio overview with KPIs
- Position-level P&L tracking
- Event timeline and audit trail
- Excel export for all data types

### Dividend Handling

The system tracks dividends through their full lifecycle: announcement → ex-dividend → payment.

#### Dividend Lifecycle

```
1. ANNOUNCEMENT
   └─ Dividend announced with ex_date, pay_date, amount per share

2. EX-DIVIDEND DATE (T)
   ├─ Anchor price adjusted: new_anchor = old_anchor - dividend_per_share
   ├─ Create DividendReceivable record
   │   ├─ gross_amount = shares_held × dividend_per_share
   │   ├─ withholding_tax = gross_amount × withholding_tax_rate
   │   └─ net_amount = gross_amount - withholding_tax
   └─ Position.dividend_receivable += net_amount

3. PAYMENT DATE (T + ~30 days)
   ├─ Position.cash += net_amount
   ├─ Position.dividend_receivable -= net_amount
   ├─ Position.total_dividends_received += net_amount
   └─ DividendReceivable.status = "paid"
```

#### Anchor Price Adjustment

On ex-dividend date, the market price naturally drops by approximately the dividend amount (this is standard market behavior - the stock is now worth less because it no longer carries the dividend entitlement).

We adjust the anchor price by the same amount to prevent false BUY triggers:

```
Example:
  Before ex-div: Anchor = $100, Market Price = $100 (no trigger)
  Dividend: $2 per share

  On ex-div date, market price drops to ~$98 (normal market behavior)

  Without anchor adjustment:
    Market Price = $98, Anchor = $100
    Price change = -2% → potential false BUY trigger
    (but nothing actually changed - shareholder receives $2 dividend)

  With anchor adjustment:
    New anchor = $100 - $2 = $98
    Market Price = $98, Anchor = $98
    Price change = 0% → no false trigger (correct behavior)
```

The anchor adjustment ensures the trigger logic sees the dividend as a neutral event - the shareholder's total value (stock + dividend receivable) is unchanged.

#### Tax Handling

| Field | Description | Default |
|-------|-------------|---------|
| withholding_tax_rate | Tax withheld at source | 25% |
| gross_amount | Total dividend before tax | shares × dps |
| withholding_tax | Tax amount withheld | gross × rate |
| net_amount | Amount credited to cash | gross - tax |

The withholding rate is configurable per position to handle different tax treaties and account types.

#### Dividend in Simulations

Simulations can include historical dividend data:
- Fetched from market data provider (yfinance)
- Applied at correct ex-dividend dates
- Affects anchor price and cash flow
- Included in total return calculations

### Market Data Sources

The system must clearly distinguish between real and synthetic data sources.

#### Data Source Types

| Source | Use Case | Indicator |
|--------|----------|-----------|
| **LIVE** | Production trading, real-time decisions | `source: "live"` or `source: "yfinance"` |
| **HISTORICAL** | Simulations using real past data | `source: "historical"` |
| **MOCK/SYNTHETIC** | Unit tests, integration tests, demos | `source: "mock"` or `source: "deterministic"` |

#### Requirements

1. **Clear labeling**: Every price data point must include its source type
2. **No mixing**: Live trading must never use mock data; system should reject mock data in production mode
3. **Visual distinction**: UI should clearly indicate when viewing mock/test data (e.g., banner, different color scheme)
4. **Audit trail**: All events must log the data source used for the decision
5. **Test isolation**: Mock data adapters used only in test configurations, never injected in production DI container

#### Implementation

```
PriceData:
  ticker: str
  price: float
  timestamp: datetime
  source: "live" | "historical" | "mock" | "deterministic"
  is_real_data: bool  # True for live/historical, False for mock/deterministic
```

The `is_real_data` flag provides a simple boolean check for guards:
```
if not price_data.is_real_data and environment == "production":
    raise DataSourceError("Cannot use synthetic data in production")
```

---

## API Specification

### Core Endpoints

| Method | Path          | Description  |
| ------ | ------------- | ------------ |
| GET    | `/v1/healthz` | Health check |
| GET    | `/v1/version` | Version info |

### Portfolio Management

| Method | Path                                               | Description                  |
| ------ | -------------------------------------------------- | ---------------------------- |
| POST   | `/v1/tenants/{tenant_id}/portfolios`               | Create portfolio             |
| GET    | `/v1/tenants/{tenant_id}/portfolios`               | List portfolios              |
| GET    | `/v1/tenants/{tenant_id}/portfolios/{id}`          | Get portfolio                |
| PUT    | `/v1/tenants/{tenant_id}/portfolios/{id}`          | Update portfolio             |
| DELETE | `/v1/tenants/{tenant_id}/portfolios/{id}`          | Delete portfolio             |
| GET    | `/v1/tenants/{tenant_id}/portfolios/{id}/overview` | Portfolio overview with KPIs |
| GET    | `/v1/tenants/{tenant_id}/portfolios/{id}/config`   | Get configuration            |
| PUT    | `/v1/tenants/{tenant_id}/portfolios/{id}/config`   | Update configuration         |

### Position Management

| Method | Path                                                     | Description         |
| ------ | -------------------------------------------------------- | ------------------- |
| GET    | `/v1/tenants/{t}/portfolios/{p}/positions`               | List positions      |
| POST   | `/v1/tenants/{t}/portfolios/{p}/positions`               | Create position     |
| POST   | `/v1/tenants/{t}/portfolios/{p}/positions/{id}/start`    | Start trading       |
| POST   | `/v1/tenants/{t}/portfolios/{p}/positions/{id}/pause`    | Pause trading       |
| GET    | `/v1/tenants/{t}/portfolios/{p}/positions/{id}/cockpit`  | Position cockpit    |
| GET    | `/v1/tenants/{t}/portfolios/{p}/positions/{id}/timeline` | Evaluation timeline |
| GET    | `/v1/tenants/{t}/portfolios/{p}/positions/{id}/events`   | Event log           |

### Trading

| Method | Path                                 | Description                |
| ------ | ------------------------------------ | -------------------------- |
| POST   | `/v1/positions/{id}/tick`            | Execute one trading cycle  |
| POST   | `/v1/positions/{id}/evaluate`        | Evaluate with manual price |
| POST   | `/v1/positions/{id}/evaluate/market` | Evaluate with live market  |
| POST   | `/v1/positions/{id}/anchor`          | Set anchor price           |

### Continuous Trading Worker

| Method | Path                        | Description              |
| ------ | --------------------------- | ------------------------ |
| POST   | `/v1/trading/start/{id}`    | Start continuous trading |
| POST   | `/v1/trading/stop/{id}`     | Stop trading             |
| POST   | `/v1/trading/pause/{id}`    | Pause trading            |
| POST   | `/v1/trading/resume/{id}`   | Resume trading           |
| GET    | `/v1/trading/status/{id}`   | Get trading status       |
| GET    | `/v1/trading/active`        | List active positions    |
| GET    | `/v1/trading/worker/status` | Worker status            |
| POST   | `/v1/trading/worker/enable` | Enable/disable worker    |

### Simulation

| Method | Path                          | Description            |
| ------ | ----------------------------- | ---------------------- |
| POST   | `/v1/simulation/run`          | Run simulation         |
| GET    | `/v1/simulations/`            | List simulations       |
| GET    | `/v1/simulations/{id}`        | Get simulation results |
| GET    | `/v1/simulations/{id}/export` | Export to Excel        |

### Optimization

| Method | Path                                     | Description                |
| ------ | ---------------------------------------- | -------------------------- |
| POST   | `/v1/optimization/configs`               | Create optimization config |
| POST   | `/v1/optimization/configs/{id}/start`    | Start optimization         |
| GET    | `/v1/optimization/configs/{id}/progress` | Get progress               |
| GET    | `/v1/optimization/configs/{id}/results`  | Get results                |
| GET    | `/v1/optimization/configs/{id}/heatmap`  | Get heatmap data           |

### Market Data

| Method | Path                             | Description               |
| ------ | -------------------------------- | ------------------------- |
| GET    | `/v1/market/status`              | Market open/closed status |
| GET    | `/v1/market/price/{ticker}`      | Current price             |
| GET    | `/v1/market/historical/{ticker}` | Historical data           |

### Dividends

| Method | Path                                                              | Description                    |
| ------ | ----------------------------------------------------------------- | ------------------------------ |
| POST   | `/v1/dividends/announce`                                          | Announce new dividend          |
| GET    | `/v1/dividends/market/{ticker}/info`                              | Get dividend info from market  |
| GET    | `/v1/dividends/market/{ticker}/upcoming`                          | Get upcoming dividends         |
| POST   | `/api/tenants/{t}/portfolios/{p}/positions/{id}/process-ex-dividend` | Process ex-dividend date    |
| POST   | `/api/tenants/{t}/portfolios/{p}/positions/{id}/process-payment`  | Process dividend payment       |
| GET    | `/api/tenants/{t}/portfolios/{p}/positions/{id}/status`           | Get dividend status            |

### Excel Export

| Method | Path                                 | Description          |
| ------ | ------------------------------------ | -------------------- |
| GET    | `/v1/excel/positions/export`         | Export all positions |
| GET    | `/v1/excel/trades/export`            | Export all trades    |
| GET    | `/v1/excel/simulation/{id}/export`   | Export simulation    |
| GET    | `/v1/excel/optimization/{id}/export` | Export optimization  |
| GET    | `/v1/excel/timeline/export`          | Export timeline      |

---

## Data Model

### Position

| Field               | Type            | Description          |
| ------------------- | --------------- | -------------------- |
| id                  | string          | Unique identifier    |
| tenant_id           | string          | Multi-tenant support |
| portfolio_id        | string          | Parent portfolio     |
| asset_symbol        | string          | Stock ticker         |
| qty                 | float           | Shares held          |
| cash                | float           | Cash reserve         |
| anchor_price        | float?          | Reference price      |
| avg_cost            | float?          | Average cost basis   |
| dividend_receivable | float           | Pending dividends    |
| guardrails          | GuardrailPolicy | Position guardrails  |
| order_policy        | OrderPolicy     | Order rules          |

### Order

| Field                    | Type                      | Description            |
| ------------------------ | ------------------------- | ---------------------- |
| id                       | string                    | Unique identifier      |
| position_id              | string                    | Position reference     |
| side                     | BUY/SELL                  | Order direction        |
| qty                      | float                     | Share quantity         |
| status                   | submitted/filled/rejected | Order state            |
| commission_rate_snapshot | float?                    | Commission at creation |

### Trade

| Field       | Type     | Description       |
| ----------- | -------- | ----------------- |
| id          | string   | Unique identifier |
| order_id    | string   | Original order    |
| side        | BUY/SELL | Trade direction   |
| qty         | float    | Executed quantity |
| price       | float    | Execution price   |
| commission  | float    | Commission paid   |
| executed_at | datetime | Execution time    |

### Event

| Field       | Type     | Description                       |
| ----------- | -------- | --------------------------------- |
| id          | string   | Unique identifier                 |
| position_id | string   | Position reference                |
| type        | string   | Event type (trigger, trade, etc.) |
| inputs      | dict     | Input parameters                  |
| outputs     | dict     | Results/calculations              |
| message     | string   | Human-readable description        |
| ts          | datetime | Timestamp                         |

### Dividend

| Field               | Type     | Description                      |
| ------------------- | -------- | -------------------------------- |
| id                  | string   | Unique identifier                |
| ticker              | string   | Stock symbol                     |
| ex_date             | datetime | Ex-dividend date                 |
| pay_date            | datetime | Payment date                     |
| dps                 | decimal  | Dividend per share               |
| currency            | string   | Currency (default: USD)          |
| withholding_tax_rate| float    | Tax rate (default: 0.25)         |

### DividendReceivable

| Field            | Type                    | Description                |
| ---------------- | ----------------------- | -------------------------- |
| id               | string                  | Unique identifier          |
| position_id      | string                  | Position reference         |
| dividend_id      | string                  | Reference to Dividend      |
| shares_at_record | float                   | Shares held on record date |
| gross_amount     | decimal                 | Amount before tax          |
| withholding_tax  | decimal                 | Tax withheld               |
| net_amount       | decimal                 | Amount after tax           |
| status           | pending/paid/cancelled  | Receivable state           |
| created_at       | datetime                | When created (ex-div date) |
| paid_at          | datetime?               | When paid                  |

---

## User Interface

### Design Reference

**Figma**: [Volatility-Balancing GUI Screens](https://www.figma.com/make/FZGuv7vVjwaiKV8JvzPFmD/Volatility-Balancing-GUI-Screens)

This is the source of truth for UI design. The implementation should follow these designs.

**Storybook**: Component documentation and interactive playground

- Run locally: `cd frontend && npm run storybook`
- Documents all reusable components with props, variants, and usage examples
- Use for developing components in isolation before integrating into pages
- Serves as living documentation that stays in sync with code

### Pages

| Page             | Path                                       | Purpose                       |
| ---------------- | ------------------------------------------ | ----------------------------- |
| Overview         | `/`                                        | Dashboard with portfolio KPIs |
| Portfolios       | `/portfolios`                              | Manage multiple portfolios    |
| Portfolio Detail | `/portfolios/:id`                          | Single portfolio overview     |
| Positions        | `/portfolios/:id/positions`                | Manage position cells         |
| Position Detail  | `/portfolios/:id/positions/:id`            | Single position trading       |
| Trading Console  | `/trading`                                 | Real-time trading control     |
| Trade Cockpit    | `/trade/:portfolioId/position/:positionId` | Position-specific trading     |
| Analytics        | `/analytics`                               | Performance analysis          |
| Audit Trail      | `/audit`                                   | Decision logs and traces      |
| Simulation Lab   | `/simulation`                              | Backtesting                   |
| Settings         | `/settings`                                | System configuration          |

### Key Features by Page

**Overview**: KPI cards, asset allocation chart, recent trades, trigger events

**Positions**: Tabbed interface (Positions, Trade, Analytics, Cash, Strategy Config), add/edit positions, cash deposits/withdrawals

**Trading Console**: Worker controls, active positions table, activity log with expandable details

**Simulation Lab**: Date range picker, resolution selector, trigger/guardrail config, results visualization

**Audit Trail**: Filter by asset/date/source, trace search, expandable event details

---

## User Flows

### 1. Create and Monitor a Position

1. Navigate to Portfolios → Create Portfolio
2. Add position with ticker and initial cash
3. Set anchor price (or auto-set from market)
4. Configure triggers and guardrails
5. Start trading
6. Monitor via Trading Console or Position Cockpit

### 2. Run a Simulation

1. Navigate to Simulation Lab
2. Select ticker and date range
3. Configure resolution and parameters
4. Click "Run Simulation"
5. Review results: P&L, trade log, metrics
6. Export to Excel if needed

### 3. Optimize Parameters

1. Create optimization config with parameter ranges
2. Start optimization run
3. Monitor progress
4. Review results ranked by metric
5. Use heatmap to visualize parameter sensitivity
6. Apply optimal parameters to live trading

### 4. Dividend Processing

1. System detects upcoming ex-dividend date (from market data or manual announcement)
2. On ex-dividend date:
   - Anchor price automatically adjusted downward by dividend amount
   - DividendReceivable created with gross/net amounts and tax
   - Position's dividend_receivable field updated
3. On payment date:
   - Process payment via API or automated worker
   - Net amount added to position cash
   - Receivable marked as paid
4. View dividend history in position events/audit trail

---

## Success Metrics

| Metric                  | Target                              |
| ----------------------- | ----------------------------------- |
| Simulation accuracy     | Deterministic, reproducible results |
| Trade execution latency | < 5s from trigger to order proposal |
| Guardrail compliance    | 100% (no trades violating limits)   |
| Audit coverage          | 100% of decisions logged            |
| UI responsiveness       | < 2s page load                      |

---

## Open Questions

1. Broker integration scope - which brokers to support first?
   - Not detirmied first. Prefered Candidates Meitav, , Excellence trade, others can be considered
2. Multi-asset position cells - support for hedged positions?
3. Mobile interface requirements
   - Future Low priority
4. Alert/notification system for trigger events
   -Yes. Configrable medium priority

---

## Deployment & Operations

### Git Branching Strategy

We use **GitHub Flow** - a simple, lightweight branching strategy:

```
main (production-ready)
  │
  ├── feature/add-widget     ← short-lived feature branch
  ├── fix/order-validation   ← short-lived bugfix branch
  └── hotfix/critical-bug    ← emergency fixes
```

**Rules:**
- `main` is always deployable
- All work happens in short-lived feature branches
- PRs require review before merging to main
- Delete branches after merge

### Pull Request Process

1. Create feature branch from `main`
2. Implement changes with tests
3. Open PR with description of changes
4. CI runs automatically (lint, tests, build)
5. Obtain code review approval
6. Squash and merge to `main`
7. CI runs on main → Manual approval → Deploy to production

### Versioning

We use **date-based versioning** in format `vYYYY.MM.DD`:

| Scenario | Version Example |
|----------|-----------------|
| First release of the day | `v2025.01.27` |
| Second release same day | `v2025.01.27.2` |
| Third release same day | `v2025.01.27.3` |
| Hotfix release | `v2025.01.27-hotfix.1` |

Tags are created automatically after successful production deployment.

### CI/CD Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│                    ON PULL REQUEST                               │
├─────────────┬─────────────┬─────────────┬───────────────────────┤
│   Lint      │ Unit Tests  │ Integration │  Frontend Build       │
│   (strict)  │ (70% cov)   │   Tests     │                       │
└─────────────┴─────────────┴─────────────┴───────────────────────┘
                              │
                    (All must pass for merge)
                              │
┌─────────────────────────────────────────────────────────────────┐
│                    ON PUSH TO MAIN                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   Same CI checks → Manual Approval Gate → Deploy to Production   │
│                    (GitHub Environment)   (SSM + deploy.sh)      │
│                              ↓                                   │
│                    Post-deploy smoke tests                       │
│                              ↓                                   │
│                    Tag release: vYYYY.MM.DD                      │
└─────────────────────────────────────────────────────────────────┘
```

**Quality Gates:**
- **Lint**: Ruff with strict settings, no warnings allowed
- **Unit Tests**: Minimum 70% code coverage required
- **Integration Tests**: All tests must pass
- **Frontend Build**: TypeScript compilation must succeed

### Trading-Aware Deployment

**Preferred deployment windows (US Eastern Time):**
1. Weekends (market closed)
2. Weekday evenings after 8:00 PM ET
3. Weekday mornings before 9:00 AM ET

**Avoid:** 9:30 AM - 4:00 PM ET (regular market hours)

**If deploying during market hours:**
1. Pause trading worker via API: `POST /v1/trading/worker/enable` with `enabled: false`
2. Wait for pending orders to settle
3. Deploy
4. Verify with smoke tests
5. Resume trading worker: `POST /v1/trading/worker/enable` with `enabled: true`

The deploy script includes a safety check that warns when deploying during market hours.

### Rollback Procedure

```bash
# Quick rollback to previous version
./deploy.sh --rollback

# Rollback to specific version
./deploy.sh v2025.01.26
```

**Decision Matrix - When to Rollback:**

| Issue | Action |
|-------|--------|
| Health check failing | Immediate rollback |
| Trading worker stopped | Immediate rollback |
| Market data errors | Investigate 5 min, then rollback |
| Non-critical UI bug | Create hotfix, no rollback |
| Performance degradation | Investigate, rollback if user-impacting |

### Release Checklist

Before deploying to production:

- [ ] All CI checks passing on main
- [ ] Code review approved
- [ ] No active trading warnings (check trading safety script)
- [ ] Deployment window is appropriate (prefer off-market hours)
- [ ] Rollback plan understood

After deployment:

- [ ] Smoke tests pass
- [ ] `/v1/healthz` returns 200
- [ ] `/v1/version` shows expected version
- [ ] Trading worker status is healthy (if applicable)
- [ ] No errors in application logs
