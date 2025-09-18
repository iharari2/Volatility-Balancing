# Volatility Balancing — Architecture v1 (MVP)

> Semi‑passive, rules‑based trading for blue‑chip equities with transparent guardrails and full auditability.

---

## 1) TL;DR

- **Frontend:** React + TypeScript, Vite, Tailwind CSS, Recharts, React Query, React Router
- **Backend:** Python **FastAPI** with Clean Architecture (Domain-Driven Design)
- **Data:** SQLite (development) / PostgreSQL (production), Redis for caching and idempotency
- **Architecture:** Hexagonal Architecture with dependency injection, event-driven design
- **Integrations:** YFinance for market data, pluggable brokerage adapters
- **Security:** Idempotency keys, request validation, audit trails

---

## 2) Component Model

```mermaid
flowchart TB
  subgraph Frontend["Frontend - React SPA"]
    WEB["React App\nDashboard / Positions / Trading / Analytics"]
    COMP["Components\nPositionCard, TradingInterface, Charts"]
    HOOKS["Custom Hooks\nusePositions, useTrading"]
  end

  subgraph Backend["Backend - FastAPI + Clean Architecture"]
    API["FastAPI Router\n/positions, /orders, /dividends, /health"]

    subgraph Application["Application Layer"]
      UC["Use Cases\nEvaluatePosition, SubmitOrder, ProcessDividend"]
      DTO["DTOs\nRequest/Response Models"]
    end

    subgraph Domain["Domain Layer"]
      ENT["Entities\nPosition, Order, Event, Dividend"]
      VO["Value Objects\nGuardrails, OrderPolicy, Types"]
      PORTS["Ports\nRepository Interfaces"]
    end

    subgraph Infrastructure["Infrastructure Layer"]
      REPO["Repositories\nSQL, Memory, Redis"]
      MKT["Market Data\nYFinance Adapter"]
      TIME["Time\nClock Service"]
    end
  end

  subgraph Data["Data Layer"]
    SQLITE[(SQLite/PostgreSQL)]
    REDIS[(Redis Cache)]
  end

  WEB -->|HTTPS JSON| API
  API --> UC
  UC --> ENT
  UC --> PORTS
  PORTS --> REPO
  REPO --> SQLITE
  REPO --> REDIS
  MKT --> UC
  TIME --> UC

  subgraph External["External Services"]
    YFIN["YFinance API"]
    BROKER["Brokerage APIs\n(Pluggable)"]
  end

  MKT --> YFIN
  UC --> BROKER
```

---

## 3) Core Sequence (Tick → Trade)

```mermaid
sequenceDiagram
  autonumber
  participant FE as Frontend
  participant API as FastAPI Router
  participant UC as EvaluatePositionUC
  participant POS as Position Entity
  participant REPO as Repository
  participant MKT as Market Data
  participant DB as Database

  FE->>API: POST /positions/{id}/evaluate?price=150.0
  API->>UC: Execute evaluation
  UC->>REPO: Load position
  REPO->>DB: SELECT position data
  DB-->>REPO: Position data
  REPO-->>UC: Position entity
  UC->>MKT: Get current market data
  MKT-->>UC: Price data
  UC->>POS: Evaluate triggers & sizing
  POS-->>UC: Order decision
  alt Skip (below threshold)
    UC->>REPO: Save event (skip reason)
  else Submit order
    UC->>REPO: Save order intent
    UC->>API: Return order response
  end
  API-->>FE: Order response
```

---

## 4) Order Lifecycle (State Machine)

```mermaid
stateDiagram-v2
  [*] --> Evaluated
  Evaluated --> Skipped: below_min / market_closed / dup / insufficient
  Evaluated --> Submitted
  Submitted --> Filled
  Submitted --> ReEval: drift>20bps
  ReEval --> Submitted
  Filled --> AnchorUpdated
  AnchorUpdated --> [*]
```

---

## 5) Data Model (Current Implementation)

- **positions**(id, ticker, qty, cash, anchor_price, dividend_receivable, withholding_tax_rate, created_at, updated_at)
- **orders**(id, position_id, side, qty, status, idempotency_key, request_signature, created_at, updated_at)
- **events**(id, position_id, type, inputs, outputs, message, ts)
- **dividends**(id, ticker, ex_date, pay_date, dps, currency, withholding_tax_rate, created_at)
- **dividend_receivables**(id, position_id, dividend_id, amount, status, created_at)

**Notes**

- Event store is append‑only; derive metrics & timeline from events
- Dividend receivable is included in effective cash for sizing/guardrails
- Idempotency keys prevent duplicate orders

---

## 6) APIs (Current Implementation)

- `GET /v1/healthz` → Health check
- `GET /v1/positions` → List all positions
- `POST /v1/positions` → Create new position
- `GET /v1/positions/{id}` → Get position details
- `POST /v1/positions/{id}/anchor` → Set anchor price
- `POST /v1/positions/{id}/evaluate` → Evaluate position with current price
- `POST /v1/positions/{id}/orders` → Submit order
- `POST /v1/orders/{id}/fill` → Fill order (broker callback)
- `GET /v1/dividends` → List dividends
- `POST /v1/dividends/announce` → Announce dividend
- `POST /v1/dividends/pay` → Process dividend payment

---

## 7) Domain Model (UML)

```mermaid
classDiagram
  class Position {
    +String id
    +String ticker
    +Float qty
    +Float cash
    +Float anchor_price
    +Float dividend_receivable
    +Float withholding_tax_rate
    +GuardrailPolicy guardrails
    +OrderPolicy order_policy
    +DateTime created_at
    +DateTime updated_at
    +set_anchor_price(price)
    +get_effective_cash()
    +adjust_anchor_for_dividend(dps)
  }

  class Order {
    +String id
    +String position_id
    +OrderSide side
    +Float qty
    +String status
    +String idempotency_key
    +DateTime created_at
    +DateTime updated_at
  }

  class Event {
    +String id
    +String position_id
    +String type
    +Dict inputs
    +Dict outputs
    +String message
    +DateTime ts
  }

  class Dividend {
    +String id
    +String ticker
    +DateTime ex_date
    +DateTime pay_date
    +Decimal dps
    +String currency
    +Float withholding_tax_rate
    +calculate_gross_amount(shares)
    +calculate_net_amount(shares)
  }

  class GuardrailPolicy {
    +Float min_qty
    +Float min_notional
    +Float lot_size
    +Float qty_step
    +ActionBelowMin action_below_min
  }

  class OrderPolicy {
    +Float trigger_threshold_pct
    +Float rebalance_ratio
    +Float commission_rate
    +Boolean allow_after_hours
  }

  Position ||--o{ Order : has
  Position ||--o{ Event : generates
  Position ||--o{ DividendReceivable : has
  Position ||--|| GuardrailPolicy : uses
  Position ||--|| OrderPolicy : uses
  Dividend ||--o{ DividendReceivable : creates
```

---

## 8) Clean Architecture Layers

```mermaid
graph TB
  subgraph "Domain Layer (Core Business Logic)"
    ENT[Entities]
    VO[Value Objects]
    PORTS[Ports/Interfaces]
  end

  subgraph "Application Layer (Use Cases)"
    UC[Use Cases]
    DTO[DTOs]
  end

  subgraph "Infrastructure Layer (External Concerns)"
    REPO[Repositories]
    MKT[Market Data]
    TIME[Time Services]
  end

  subgraph "Presentation Layer (API)"
    API[FastAPI Routes]
    MID[Middleware]
  end

  API --> UC
  UC --> ENT
  UC --> PORTS
  PORTS --> REPO
  REPO --> ENT
  MKT --> UC
  TIME --> UC
```

---

## 9) Technology Stack

- **Frontend:** React 18, TypeScript, Vite, Tailwind CSS, Recharts, React Query, React Router
- **Backend:** Python 3.11+, FastAPI, Pydantic, SQLAlchemy
- **Database:** SQLite (dev), PostgreSQL (prod)
- **Cache:** Redis
- **Market Data:** YFinance
- **Architecture:** Clean Architecture / Hexagonal Architecture
- **Testing:** Pytest, FastAPI TestClient
- **Documentation:** OpenAPI 3.0, Mermaid diagrams

---

## 10) Security & Compliance

- Request validation via Pydantic models
- Idempotency keys for order deduplication
- Input sanitization and type checking
- Audit trails via event store
- No PII storage beyond configuration

---

## 11) Deployment & Development

- **Development:** Local SQLite, in-memory repositories
- **Production:** PostgreSQL, Redis, containerized deployment
- **Configuration:** Environment variables for persistence backends
- **Testing:** Unit tests, integration tests, API tests

---

## 12) Observability

- Structured logging with request IDs
- Event store for audit trails
- Health check endpoints
- Error handling and validation

---

## 13) Future Enhancements

- Multi-asset portfolio allocation
- Dynamic thresholds
- DRIP (Dividend Reinvestment Plan)
- TWAP (Time-Weighted Average Price)
- Tax-lot optimization
- Real-time WebSocket updates
- Advanced analytics and reporting
