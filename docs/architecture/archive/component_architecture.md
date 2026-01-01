# Component Architecture

This document provides detailed component architecture diagrams for the Volatility Balancing system.

## System Overview

```mermaid
graph TB
  subgraph "Client Layer"
    WEB["Web Browser"]
    MOBILE["Mobile App (Future)"]
  end

  subgraph "Frontend Layer"
    REACT["React SPA"]
    COMPONENTS["UI Components"]
    HOOKS["Custom Hooks"]
    STATE["State Management"]
  end

  subgraph "API Gateway Layer"
    LB["Load Balancer"]
    API_GW["API Gateway"]
  end

  subgraph "Backend Services"
    AUTH["Authentication Service"]
    POSITION["Position Service"]
    ORDER["Order Service"]
    DIVIDEND["Dividend Service"]
    MARKET["Market Data Service"]
  end

  subgraph "Data Layer"
    DB["PostgreSQL"]
    CACHE["Redis Cache"]
    FILES["File Storage"]
  end

  subgraph "External Services"
    YFIN["YFinance API"]
    BROKER["Brokerage APIs"]
    NOTIFY["Notification Service"]
  end

  WEB --> REACT
  MOBILE --> REACT
  REACT --> COMPONENTS
  REACT --> HOOKS
  REACT --> STATE

  REACT --> LB
  LB --> API_GW
  API_GW --> AUTH
  API_GW --> POSITION
  API_GW --> ORDER
  API_GW --> DIVIDEND
  API_GW --> MARKET

  POSITION --> DB
  ORDER --> DB
  DIVIDEND --> DB
  MARKET --> CACHE

  POSITION --> CACHE
  ORDER --> CACHE

  MARKET --> YFIN
  ORDER --> BROKER
  AUTH --> NOTIFY
```

## Frontend Component Architecture

```mermaid
graph TB
  subgraph "React Application"
    subgraph "Pages"
      DASH["Dashboard"]
      POS["Positions"]
      TRADE["Trading"]
      SIM["Simulation"]
      ANAL["Analytics"]
    end

    subgraph "Components"
      LAYOUT["Layout"]
      NAV["Navigation"]
      CARDS["Position Cards"]
      CHARTS["Charts"]
      FORMS["Forms"]
    end

    subgraph "Hooks"
      POS_HOOK["usePositions"]
      TRADE_HOOK["useTrading"]
      MARKET_HOOK["useMarketData"]
    end

    subgraph "State Management"
      ZUSTAND["Zustand Store"]
      QUERY["React Query"]
    end

    subgraph "Services"
      API["API Client"]
      UTILS["Utilities"]
    end
  end

  DASH --> CARDS
  POS --> CARDS
  TRADE --> FORMS
  SIM --> CHARTS
  ANAL --> CHARTS

  CARDS --> POS_HOOK
  FORMS --> TRADE_HOOK
  CHARTS --> MARKET_HOOK

  POS_HOOK --> API
  TRADE_HOOK --> API
  MARKET_HOOK --> API

  API --> ZUSTAND
  API --> QUERY
```

## Backend Service Architecture

```mermaid
graph TB
  subgraph "FastAPI Application"
    subgraph "Presentation Layer"
      ROUTES["API Routes"]
      MIDDLEWARE["Middleware"]
      VALIDATION["Request Validation"]
    end

    subgraph "Application Layer"
      ORCH_LIVE["Live Trading Orchestrator"]
      ORCH_SIM["Simulation Orchestrator"]
      UC_POS["Position Use Cases<br/>(Legacy)"]
      UC_ORDER["Order Use Cases<br/>(Legacy)"]
      UC_DIV["Dividend Use Cases"]
      UC_MKT["Market Use Cases"]
      PORTS["Application Ports<br/>IMarketDataProvider<br/>IOrderService<br/>IPositionRepository"]
      DTO["Data Transfer Objects"]
    end

    subgraph "Domain Layer"
      ENTITIES["Domain Entities"]
      VO["Value Objects<br/>MarketQuote<br/>PositionState<br/>TriggerConfig<br/>GuardrailConfig<br/>TradeIntent"]
      DS["Domain Services<br/>PriceTrigger<br/>GuardrailEvaluator"]
      RULES["Business Rules"]
    end

    subgraph "Infrastructure Layer"
      REPO_SQL["SQL Repositories"]
      REPO_REDIS["Redis Repositories"]
      REPO_MEM["Memory Repositories"]
      MKT_ADAPTER["Market Data Adapter"]
      TIME_SVC["Time Service"]
    end
  end

  ROUTES --> ORCH_LIVE
  ROUTES --> ORCH_SIM
  ROUTES --> UC_POS
  ROUTES --> UC_ORDER
  ROUTES --> UC_DIV
  ROUTES --> UC_MKT

  ORCH_LIVE --> DS
  ORCH_SIM --> DS
  ORCH_LIVE --> PORTS
  ORCH_SIM --> PORTS

  UC_POS --> ENTITIES
  UC_ORDER --> ENTITIES
  UC_DIV --> ENTITIES
  UC_MKT --> ENTITIES

  ENTITIES --> VO
  ENTITIES --> RULES
  DS --> VO

  UC_POS --> PORTS
  UC_ORDER --> PORTS
  UC_DIV --> PORTS
  UC_MKT --> PORTS

  PORTS --> REPO_SQL
  PORTS --> REPO_REDIS
  PORTS --> REPO_MEM

  UC_MKT --> MKT_ADAPTER
  ORCH_LIVE --> MKT_ADAPTER
  ORCH_SIM --> MKT_ADAPTER
  UC_POS --> TIME_SVC
  UC_ORDER --> TIME_SVC
  ORCH_LIVE --> TIME_SVC
  ORCH_SIM --> TIME_SVC
```

## Data Flow Architecture

```mermaid
graph LR
  subgraph "User Interface"
    UI["React Components"]
  end

  subgraph "API Layer"
    API["FastAPI Routes"]
    VAL["Pydantic Validation"]
  end

  subgraph "Business Logic"
    UC["Use Cases"]
    ENT["Domain Entities"]
  end

  subgraph "Data Access"
    REPO["Repositories"]
    CACHE["Cache Layer"]
  end

  subgraph "Storage"
    DB["PostgreSQL"]
    REDIS["Redis"]
  end

  subgraph "External"
    YFIN["YFinance"]
    BROKER["Brokerage"]
  end

  UI -->|HTTP/JSON| API
  API --> VAL
  VAL --> UC
  UC --> ENT
  UC --> REPO
  REPO --> CACHE
  REPO --> DB
  CACHE --> REDIS
  UC --> YFIN
  UC --> BROKER
```

## Microservices Architecture (Future)

```mermaid
graph TB
  subgraph "API Gateway"
    GATEWAY["Kong/Envoy"]
  end

  subgraph "Core Services"
    POS_SVC["Position Service"]
    ORDER_SVC["Order Service"]
    DIV_SVC["Dividend Service"]
    MKT_SVC["Market Data Service"]
  end

  subgraph "Supporting Services"
    AUTH_SVC["Auth Service"]
    NOTIFY_SVC["Notification Service"]
    AUDIT_SVC["Audit Service"]
  end

  subgraph "Data Services"
    DB_SVC["Database Service"]
    CACHE_SVC["Cache Service"]
    FILE_SVC["File Service"]
  end

  subgraph "External Services"
    YFIN_EXT["YFinance API"]
    BROKER_EXT["Brokerage APIs"]
  end

  GATEWAY --> POS_SVC
  GATEWAY --> ORDER_SVC
  GATEWAY --> DIV_SVC
  GATEWAY --> MKT_SVC

  POS_SVC --> AUTH_SVC
  ORDER_SVC --> AUTH_SVC
  DIV_SVC --> AUTH_SVC

  POS_SVC --> AUDIT_SVC
  ORDER_SVC --> AUDIT_SVC
  DIV_SVC --> AUDIT_SVC

  POS_SVC --> DB_SVC
  ORDER_SVC --> DB_SVC
  DIV_SVC --> DB_SVC
  MKT_SVC --> CACHE_SVC

  MKT_SVC --> YFIN_EXT
  ORDER_SVC --> BROKER_EXT
```

## Security Architecture

```mermaid
graph TB
  subgraph "Client Security"
    HTTPS["HTTPS/TLS"]
    CSP["Content Security Policy"]
    CORS["CORS Headers"]
  end

  subgraph "API Security"
    AUTH["Authentication"]
    AUTHZ["Authorization"]
    RATE["Rate Limiting"]
    VALID["Input Validation"]
  end

  subgraph "Data Security"
    ENCRYPT["Encryption at Rest"]
    TRANSPORT["Encryption in Transit"]
    SECRETS["Secrets Management"]
  end

  subgraph "Network Security"
    VPC["VPC"]
    SG["Security Groups"]
    WAF["Web Application Firewall"]
  end

  HTTPS --> AUTH
  CSP --> AUTHZ
  CORS --> RATE

  AUTH --> ENCRYPT
  AUTHZ --> TRANSPORT
  RATE --> SECRETS

  ENCRYPT --> VPC
  TRANSPORT --> SG
  SECRETS --> WAF
```

## Monitoring Architecture

```mermaid
graph TB
  subgraph "Application Metrics"
    APP["Application Logs"]
    PERF["Performance Metrics"]
    ERR["Error Tracking"]
  end

  subgraph "Infrastructure Metrics"
    CPU["CPU Usage"]
    MEM["Memory Usage"]
    DISK["Disk Usage"]
    NET["Network I/O"]
  end

  subgraph "Business Metrics"
    TRADES["Trade Volume"]
    PNL["P&L Tracking"]
    RISK["Risk Metrics"]
  end

  subgraph "Monitoring Stack"
    PROM["Prometheus"]
    GRAF["Grafana"]
    JAEGER["Jaeger"]
    ALERT["AlertManager"]
  end

  APP --> PROM
  PERF --> PROM
  ERR --> PROM

  CPU --> PROM
  MEM --> PROM
  DISK --> PROM
  NET --> PROM

  TRADES --> PROM
  PNL --> PROM
  RISK --> PROM

  PROM --> GRAF
  PROM --> JAEGER
  PROM --> ALERT
```

## Component Dependencies

```mermaid
graph TD
  subgraph "Frontend Dependencies"
    REACT_DEP["React 18"]
    TS_DEP["TypeScript"]
    VITE_DEP["Vite"]
    TAILWIND_DEP["Tailwind CSS"]
    RQ_DEP["React Query"]
    ROUTER_DEP["React Router"]
    CHARTS_DEP["Recharts"]
    ZUSTAND_DEP["Zustand"]
  end

  subgraph "Backend Dependencies"
    FASTAPI_DEP["FastAPI"]
    PYDANTIC_DEP["Pydantic"]
    SQLALCHEMY_DEP["SQLAlchemy"]
    REDIS_DEP["Redis"]
    YFINANCE_DEP["yfinance"]
    PYTZ_DEP["pytz"]
  end

  subgraph "Database Dependencies"
    POSTGRES_DEP["PostgreSQL"]
    SQLITE_DEP["SQLite"]
    REDIS_DB_DEP["Redis"]
  end

  subgraph "Testing Dependencies"
    PYTEST_DEP["pytest"]
    RUF_DEP["ruff"]
    MYPY_DEP["mypy"]
    JEST_DEP["Jest"]
    RTL_DEP["React Testing Library"]
  end

  REACT_DEP --> TS_DEP
  TS_DEP --> VITE_DEP
  VITE_DEP --> TAILWIND_DEP
  TAILWIND_DEP --> RQ_DEP
  RQ_DEP --> ROUTER_DEP
  ROUTER_DEP --> CHARTS_DEP
  CHARTS_DEP --> ZUSTAND_DEP

  FASTAPI_DEP --> PYDANTIC_DEP
  PYDANTIC_DEP --> SQLALCHEMY_DEP
  SQLALCHEMY_DEP --> REDIS_DEP
  REDIS_DEP --> YFINANCE_DEP
  YFINANCE_DEP --> PYTZ_DEP

  SQLALCHEMY_DEP --> POSTGRES_DEP
  SQLALCHEMY_DEP --> SQLITE_DEP
  REDIS_DEP --> REDIS_DB_DEP

  FASTAPI_DEP --> PYTEST_DEP
  PYTEST_DEP --> RUF_DEP
  RUF_DEP --> MYPY_DEP

  REACT_DEP --> JEST_DEP
  JEST_DEP --> RTL_DEP
```
