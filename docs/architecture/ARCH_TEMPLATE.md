---
owner: Eng
status: draft
last_updated: 2025-08-24
---
# <Feature> — Technical Design

```mermaid
flowchart LR
  WEB[Next.js] --> APIG[API Gateway]
  APIG --> API[FastAPI]
  API --> DB[(Postgres)]
