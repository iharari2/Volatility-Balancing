# Screen Structure Specification

## Overview

The application has three main screens, each with a distinct purpose and data focus:

1. **Portfolio Screen** - Portfolio list and aggregated information
2. **Position Screen** - Detailed position information per position cell
3. **Trade Screen** - Real-time trading data flow, events, and algorithm behavior

## 1. Portfolio Screen

### Purpose

List portfolios and show aggregated information across all positions.

### Display Requirements

#### Portfolio List

- List all portfolios for the tenant
- Show portfolio metadata:
  - Portfolio name
  - Portfolio type (LIVE/SIM/SANDBOX)
  - Trading state (READY/RUNNING/PAUSED/ERROR/NOT_CONFIGURED)
  - Created/updated dates

#### Aggregated Information (Per Portfolio)

When a portfolio is selected, show:

**Portfolio Summary:**

- Total portfolio value (sum of all position cells)
- Total cash (sum of all position cash)
- Total stock value (sum of all position stock values)
- Number of positions
- Portfolio-level return
- Weighted alpha (across all positions)

**Position List (Summary View):**

- List of all positions in the portfolio
- For each position, show:
  - Asset symbol
  - Total value (cash + stock)
  - Position return %
  - Alpha %
  - Status (Active/Paused)
- Click on position → Navigate to Position Screen

**Portfolio Configuration:**

- Default strategy parameters
- Trading hours policy
- Portfolio-level settings

### Layout

```
┌─────────────────────────────────────────────────────┐
│ Portfolio Management                                 │
├─────────────────────────────────────────────────────┤
│                                                      │
│  Portfolio List (Left Sidebar)                      │
│  ┌──────────────────────────────────────────────┐  │
│  │ Portfolio 1 (LIVE)                          │  │
│  │ Portfolio 2 (SIM)                            │  │
│  │ Portfolio 3 (SANDBOX)                         │  │
│  └──────────────────────────────────────────────┘  │
│                                                      │
│  Selected Portfolio: Portfolio 1                   │
│  ┌──────────────────────────────────────────────┐  │
│  │ Portfolio Summary:                            │  │
│  │ • Total Value: $75,500                        │  │
│  │ • Total Cash: $25,000 (33%)                   │  │
│  │ • Total Stock: $50,500 (67%)                  │  │
│  │ • Positions: 3                                 │  │
│  │ • Portfolio Return: +2.1%                     │  │
│  │ • Weighted Alpha: +0.3%                       │  │
│  └──────────────────────────────────────────────┘  │
│                                                      │
│  Positions (Summary):                                │
│  ┌──────────────────────────────────────────────┐  │
│  │ Asset  | Value    | Return | Alpha | Status │  │
│  │ AAPL   | $25,000  | +5.2%  | +2.2% | Active │  │
│  │ MSFT   | $30,000  | +2.1%  | -0.5% | Active │  │
│  │ GOOGL  | $20,000  | -1.5%  | -3.2% | Paused │  │
│  └──────────────────────────────────────────────┘  │
│                                                      │
│  [View Position Details] → Navigate to Position    │
│  [Configure Portfolio]                              │
└─────────────────────────────────────────────────────┘
```

### Key Features

- **Aggregated View**: All metrics are portfolio-level aggregations
- **Position Summary**: Quick overview of each position
- **Navigation**: Click position → Go to Position Screen
- **Portfolio Actions**: Create, edit, delete portfolios

## 2. Position Screen

### Purpose

Show detailed information for a single position cell, including all position-specific data.

### Display Requirements

#### Position Cell Details

**Value Components:**

- Cash balance (position-specific)
- Stock holdings (qty, current price)
- Stock value (qty × price)
- Total value (cash + stock)
- Allocation % (cash % and stock %)

**Market Data:**

- Current price (prominently displayed)
- Price change (absolute and percentage)
- Open, High, Low, Close (OHLC)
- Volume
- Bid/Ask spread
- Market hours status (Open/Closed)
- Last update timestamp

**Anchor Information:**

- Current anchor price
- Anchor date/time
- Deviation from anchor (%)
- Buy trigger price
- Sell trigger price

**Performance Metrics:**

- Position return % (total value change)
- Stock return % (price change)
- Alpha % (outperformance)
- Initial value
- Current value
- Performance chart (position vs stock over time)

**Trading Activity:**

- Total trades count
- Total commissions paid
- Total dividends received
- Last trade date/time
- Recent trades list

**Strategy Configuration:**

- Trigger thresholds (up/down %)
- Guardrail limits (min/max stock %)
- Rebalance ratio
- Commission rate
- Trading status (Active/Paused)

**Activities/Events:**

- Recent position events
- Trade history
- Dividend history
- Configuration changes
- Anchor price changes

### Layout

```
┌─────────────────────────────────────────────────────┐
│ AAPL Position Cell - Detailed View                  │
├─────────────────────────────────────────────────────┤
│                                                      │
│  Value Breakdown:                                    │
│  ┌──────────────────────────────────────────────┐  │
│  │ Cash:        $10,000  (40%)                   │  │
│  │ Stock:       100 shares @ $155 = $15,500 (60%)│  │
│  │ Total Value: $25,500                          │  │
│  └──────────────────────────────────────────────┘  │
│                                                      │
│  Market Data:                                        │
│  ┌──────────────────────────────────────────────┐  │
│  │ Current: $155.20  |  Change: +$0.20 (+0.13%) │  │
│  │ Open: $154.50  |  High: $155.50  |  Low: $154.00│ │
│  │ Close: $155.00  |  Volume: 45.2M              │  │
│  │ Bid: $155.18  |  Ask: $155.22  |  Spread: $0.04│ │
│  └──────────────────────────────────────────────┘  │
│                                                      │
│  Anchor & Triggers:                                  │
│  ┌──────────────────────────────────────────────┐  │
│  │ Anchor: $150.00  |  Set: 2025-01-15 10:00 AM  │  │
│  │ Deviation: +3.47%                              │  │
│  │ Buy Trigger:  $154.50 (+3.0%)                  │  │
│  │ Sell Trigger: $154.50 (+3.0%)                 │  │
│  └──────────────────────────────────────────────┘  │
│                                                      │
│  Performance:                                        │
│  ┌──────────────────────────────────────────────┐  │
│  │ Position Return: +5.2%  ↑                     │  │
│  │ Stock Return:    +3.0%  ↑                     │  │
│  │ Alpha:           +2.2%  ✓ Outperforming      │  │
│  │ [Performance Chart: Position vs Stock]        │  │
│  └──────────────────────────────────────────────┘  │
│                                                      │
│  Trading Activity:                                   │
│  ┌──────────────────────────────────────────────┐  │
│  │ Total Trades: 12                               │  │
│  │ Commissions: $15.20                            │  │
│  │ Dividends: $125.00                             │  │
│  │ Last Trade: 2 hours ago                        │  │
│  └──────────────────────────────────────────────┘  │
│                                                      │
│  Strategy:                                           │
│  ┌──────────────────────────────────────────────┐  │
│  │ Triggers: ±3.0%                              │  │
│  │ Guardrails: 25% - 75%                        │  │
│  │ Rebalance: 1.67x                              │  │
│  │ Status: ACTIVE                                │  │
│  └──────────────────────────────────────────────┘  │
│                                                      │
│  Recent Activities:                                  │
│  ┌──────────────────────────────────────────────┐  │
│  │ [Event timeline: trades, dividends, config]  │  │
│  └──────────────────────────────────────────────┘  │
│                                                      │
│  [Edit Strategy] [Deposit Cash] [Withdraw Cash]    │
│  [Set Anchor] [View Trade Screen] [Export Data]   │
└─────────────────────────────────────────────────────┘
```

### Key Features

- **Position-Specific**: All data scoped to this position cell
- **Comprehensive Details**: Market data, cash, anchor, performance, activities
- **Performance Tracking**: Position vs stock comparison
- **Activity History**: Complete event timeline
- **Actions**: Configure, deposit/withdraw, set anchor, navigate to Trade Screen

## 3. Trade Screen

### Purpose

Show detailed data flow, market events, algorithm behaviors, and events history for real-time trading monitoring.

### Display Requirements

#### Data Flow Visualization

**Market Data Flow:**

- Real-time price updates
- Price feed status
- Data source (Yahoo Finance, etc.)
- Update frequency
- Last update timestamp

**Algorithm Behavior:**

- Current evaluation state
- Trigger evaluation results
- Guardrail checks
- Order sizing calculations
- Decision reasoning

**Trading Status:**

- Active positions being monitored
- Position selection (view one position at a time)
- Trading state (RUNNING/PAUSED/ERROR)

#### Market Events

**Real-Time Events:**

- Price updates
- Market open/close
- Ex-dividend dates
- Trigger crossings
- Guardrail violations

**Event Timeline:**

- Chronological event log
- Event type, timestamp, details
- Filter by event type
- Search events

#### Algorithm Behaviors

**Decision Process:**

- Trigger evaluation: Current price vs anchor
- Deviation calculation
- Trigger status (approaching/fired)
- Guardrail evaluation
- Order size calculation
- Final decision (BUY/SELL/SKIP)

**Algorithm State:**

- Current position state
- Pending orders
- Recent decisions
- Decision reasoning

#### Events History

**Complete Event Log:**

- All events for selected position
- Event types:
  - Market data updates
  - Trigger evaluations
  - Order submissions
  - Order fills
  - Guardrail checks
  - Algorithm decisions
  - Configuration changes
- Filterable and searchable
- Exportable

### Layout

```
┌─────────────────────────────────────────────────────┐
│ Trade Screen - Real-Time Trading Monitor            │
├─────────────────────────────────────────────────────┤
│                                                      │
│  Position Selector:                                  │
│  ┌──────────────────────────────────────────────┐  │
│  │ [AAPL ▼] [MSFT] [GOOGL]                       │  │
│  │ Selected: AAPL Position Cell                   │  │
│  └──────────────────────────────────────────────┘  │
│                                                      │
│  Data Flow:                                          │
│  ┌──────────────────────────────────────────────┐  │
│  │ Market Data Feed:                              │  │
│  │ • Source: Yahoo Finance                        │  │
│  │ • Status: Active ✓                            │  │
│  │ • Last Update: 2 seconds ago                  │  │
│  │ • Current Price: $155.20                      │  │
│  │ • Update Frequency: 6 minutes                 │  │
│  └──────────────────────────────────────────────┘  │
│                                                      │
│  Algorithm Behavior:                                 │
│  ┌──────────────────────────────────────────────┐  │
│  │ Current Evaluation:                            │  │
│  │ • Anchor: $150.00                             │  │
│  │ • Current: $155.20                            │  │
│  │ • Deviation: +3.47%                            │  │
│  │ • Trigger Status: ⚠️ SELL TRIGGER APPROACHING │  │
│  │ • Guardrail Check: ✓ Within limits (60%)      │  │
│  │ • Order Size: 10 shares                        │  │
│  │ • Decision: SELL (trigger fired)               │  │
│  │ • Reasoning: Price exceeded +3.0% trigger    │  │
│  └──────────────────────────────────────────────┘  │
│                                                      │
│  Market Events (Real-Time):                         │
│  ┌──────────────────────────────────────────────┐  │
│  │ [Event Stream]                                 │  │
│  │ 14:32:15 - Price Update: $155.20              │  │
│  │ 14:32:10 - Trigger Evaluated: SELL           │  │
│  │ 14:32:05 - Guardrail Check: PASS              │  │
│  │ 14:31:50 - Order Submitted: SELL 10 shares    │  │
│  │ 14:31:45 - Order Filled: SELL 10 @ $155.15   │  │
│  └──────────────────────────────────────────────┘  │
│                                                      │
│  Events History:                                    │
│  ┌──────────────────────────────────────────────┐  │
│  │ [Filter: All Events ▼] [Search: ...]          │  │
│  │                                                │  │
│  │ Date/Time    | Type        | Details          │  │
│  │ 2025-01-20   | Price Update| $155.20         │  │
│  │ 14:32:15     |              |                  │  │
│  │ 2025-01-20   | Trigger      | SELL triggered  │  │
│  │ 14:32:10     |              | +3.47% > +3.0%  │  │
│  │ 2025-01-20   | Order Fill   | SELL 10 @ $155.15│ │
│  │ 14:31:45     |              |                  │  │
│  │ ...          | ...          | ...              │  │
│  └──────────────────────────────────────────────┘  │
│                                                      │
│  [Pause Trading] [Resume Trading] [Export Events]  │
└─────────────────────────────────────────────────────┘
```

### Key Features

- **Real-Time Monitoring**: Live data flow and events
- **Algorithm Transparency**: Show decision process and reasoning
- **Event History**: Complete chronological log
- **Position-Specific**: Focus on one position at a time
- **Trading Control**: Start/pause/resume trading

## Navigation Flow

```
Portfolio Screen
    ↓ (Click Position)
Position Screen
    ↓ (Click "View Trade Screen")
Trade Screen
    ↓ (Back to Position)
Position Screen
    ↓ (Back to Portfolio)
Portfolio Screen
```

## Data Scope

### Portfolio Screen

- **Scope**: Portfolio-level aggregations
- **Data**: Sum of all positions, portfolio config
- **Focus**: Overview and summary

### Position Screen

- **Scope**: Single position cell
- **Data**: Position-specific details, market data, performance, activities
- **Focus**: Complete position information

### Trade Screen

- **Scope**: Single position cell (real-time)
- **Data**: Data flow, algorithm behavior, events
- **Focus**: Trading process and decision-making

## API Endpoints

### Portfolio Screen

- `GET /api/tenants/{tenant_id}/portfolios` - List portfolios
- `GET /api/tenants/{tenant_id}/portfolios/{portfolio_id}/overview` - Portfolio overview with aggregated data

### Position Screen

- `GET /api/tenants/{tenant_id}/portfolios/{portfolio_id}/positions/{position_id}` - Position details
- `GET /api/tenants/{tenant_id}/portfolios/{portfolio_id}/positions/{position_id}/events` - Position events

### Trade Screen

- `GET /api/tenants/{tenant_id}/portfolios/{portfolio_id}/positions/{position_id}/trade-status` - Trading status
- `GET /api/tenants/{tenant_id}/portfolios/{portfolio_id}/positions/{position_id}/events` - Real-time events
- `WebSocket /ws/trading/{position_id}` - Real-time market data and events (optional)

---

_Last updated: 2025-01-XX_







