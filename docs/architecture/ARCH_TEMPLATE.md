---
owner: Platform Eng
status: draft
last_updated: 2025-08-24
related: ["../product/PRD_TEMPLATE.md", "../adr/ADR_TEMPLATE.md"]
---
# <Feature Name> — Technical Design

## 1. Overview
- Brief context and decision summary.

## 2. Architecture Diagram
```mermaid
flowchart LR
  WEB[Next.js] --> APIG[API Gateway]
  APIG --> API[FastAPI]
  API --> PG[(Postgres)]
  API --> EVT(EventBridge)
  EVT --> DEC[Decision Engine]
  DEC --> ORD[Order Manager]
  ORD --> BRK[Broker]
