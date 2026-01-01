# Sequence Examples (Mermaid)

This document contains comprehensive sequence diagrams for the Volatility Balancing system.

## Position Evaluation Flow

```mermaid
sequenceDiagram
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

## Order Submission Flow

```mermaid
sequenceDiagram
  participant FE as Frontend
  participant API as FastAPI Router
  participant UC as SubmitOrderUC
  participant POS as Position Entity
  participant REPO as Repository
  participant IDEM as Idempotency Service
  participant DB as Database

  FE->>API: POST /positions/{id}/orders
  Note over FE,API: Headers: Idempotency-Key
  API->>UC: Execute order submission
  UC->>IDEM: Check idempotency key
  alt Key exists
    IDEM-->>UC: Return existing result
  else New key
    UC->>REPO: Load position
    REPO->>DB: SELECT position data
    DB-->>REPO: Position data
    REPO-->>UC: Position entity
    UC->>POS: Validate order
    POS-->>UC: Validation result
    alt Valid
      UC->>REPO: Save order
      UC->>IDEM: Store idempotency key
      UC->>API: Return success
    else Invalid
      UC->>API: Return error
    end
  end
  API-->>FE: Order response
```

## Dividend Processing Flow

```mermaid
sequenceDiagram
  participant API as FastAPI Router
  participant UC as ProcessDividendUC
  participant POS as Position Entity
  participant REPO as Repository
  participant MKT as Market Data
  participant DB as Database

  API->>UC: POST /dividends/announce
  UC->>MKT: Get dividend data
  MKT-->>UC: Dividend information
  UC->>REPO: Save dividend
  UC->>REPO: Find affected positions
  REPO->>DB: SELECT positions by ticker
  DB-->>REPO: Position data
  REPO-->>UC: Position entities
  loop For each position
    UC->>POS: Add dividend receivable
    UC->>REPO: Update position
  end
  UC->>API: Return success
  API-->>API: Dividend announced
```

## Order Filling Flow (Broker Callback)

```mermaid
sequenceDiagram
  participant BRK as Brokerage
  participant API as FastAPI Router
  participant UC as ExecuteOrderUC
  participant POS as Position Entity
  participant REPO as Repository
  participant DB as Database

  BRK->>API: POST /orders/{id}/fill
  Note over BRK,API: Webhook with fill details
  API->>UC: Execute order fill
  UC->>REPO: Load order
  REPO->>DB: SELECT order data
  DB-->>REPO: Order data
  REPO-->>UC: Order entity
  UC->>REPO: Load position
  REPO->>DB: SELECT position data
  DB-->>REPO: Position data
  REPO-->>UC: Position entity
  UC->>POS: Update position with fill
  POS-->>UC: Updated position
  UC->>REPO: Save updated position
  UC->>REPO: Save trade record
  UC->>API: Return success
  API-->>BRK: Acknowledgment
```

## Position Creation Flow

```mermaid
sequenceDiagram
  participant FE as Frontend
  participant API as FastAPI Router
  participant UC as CreatePositionUC
  participant POS as Position Entity
  participant REPO as Repository
  participant DB as Database

  FE->>API: POST /positions
  API->>UC: Execute position creation
  UC->>POS: Create new position
  POS-->>UC: Position entity
  UC->>REPO: Save position
  REPO->>DB: INSERT position data
  DB-->>REPO: Success
  REPO-->>UC: Position saved
  UC->>API: Return position details
  API-->>FE: Position created
```

## Market Data Integration Flow

```mermaid
sequenceDiagram
  participant UC as Use Case
  participant MKT as YFinance Adapter
  participant YFIN as YFinance API
  participant CACHE as Cache Layer
  participant DB as Database

  UC->>MKT: Get market data for ticker
  MKT->>CACHE: Check cache
  alt Cache hit
    CACHE-->>MKT: Cached data
  else Cache miss
    MKT->>YFIN: Fetch real-time data
    YFIN-->>MKT: Market data
    MKT->>CACHE: Store in cache
  end
  MKT-->>UC: Market data
  UC->>UC: Process with market data
```

## Error Handling Flow

```mermaid
sequenceDiagram
  participant FE as Frontend
  participant API as FastAPI Router
  participant UC as Use Case
  participant REPO as Repository
  participant DB as Database

  FE->>API: API Request
  API->>UC: Execute use case
  UC->>REPO: Database operation
  REPO->>DB: Query database
  alt Success
    DB-->>REPO: Data
    REPO-->>UC: Entity
    UC-->>API: Success response
    API-->>FE: 200 OK
  else Error
    DB-->>REPO: Error
    REPO-->>UC: Exception
    UC-->>API: Error response
    API-->>FE: 4xx/5xx Error
  end
```
