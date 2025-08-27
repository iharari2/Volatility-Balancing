# Volatility Balancing (MVP)
Semi-passive, mean-reversion paper-trading platform on blue-chip equities.# Docs‑as‑Code Repo Bootstrap

## Directory Layout

## Repo layout
- **/frontend** – web UI
- **/backend** – FastAPI services (domain, ports, adapters, services, api)
- **/infra** – IaC & deployment
- **/scripts** – dev utilities
- **/docs** – PRDs, architecture, ADRs, runbooks, OpenAPI

### Docs
- `/docs/product` – PRDs & acceptance criteria
- `/docs/architecture` – designs, sequence diagrams, API contract docs
- `/docs/adr` – Architecture Decision Records
- `/docs/runbooks` – build/run/ops playbooks
- `/docs/api` – OpenAPI specs + governance rules

### Backend structure
See `/backend/app` for domain/ports/adapters/services/api breakdown.

```
/docs
  /product
    PRD_TEMPLATE.md
  /architecture
    ARCH_TEMPLATE.md
    SEQUENCE_EXAMPLE.md
  /adr
    ADR_TEMPLATE.md
  /runbooks
    RUNBOOK_TEMPLATE.md
  /api
    OPENAPI_README.md
  README.md

/.github
  PULL_REQUEST_TEMPLATE_docs.md
/README.md
/.editorconfig
/.gitignore
/.pre-commit-config.yaml
/LICENSE

/docs/                     # All human-facing docs live here
  /product/                # PRDs & functional specs
  /architecture/           # system/tech designs & API *contracts* docs
  /adr/                    # Architecture Decision Records
  /runbooks/               # operational playbooks (build/run/support)
  /api/                    # OpenAPI YAML/JSON + API governance docs
  index.md                 # docs landing page

/backend/                  # Server code (FastAPI, services, adapters)
  /app/                    # <-- keep "app" *inside* backend, not top-level
    /api/                  # FastAPI routers + DTOs
    /services/             # orchestration (order, strategy, settlement)
    /domain/               # pure domain (models, rules)
    /ports/                # interfaces
    /adapters/             # memory/db/redis/broker implementations
    /config.py
    /main.py               # ASGI entrypoint
  /tests/
    /unit/
    /integration/
  pyproject.toml
  uv.lock | poetry.lock

/frontend/                 # Web UI code
  /src/
  /public/
  package.json
  vite.config.ts

/infra/                    # IaC + deployment
  /k8s/                    # manifests/helm
  /terraform/              # infra provisioning
  /environments/           # staging/prod overlays
  /scripts/                # infra-related helpers (kubectl, tf wrappers)

/scripts/                  # Dev scripts (lint, format, data, one-offs)
  makefile targets map here (or keep a Makefile at root)

/tools/                    # (optional) shared dev tooling, codegen, linters

/.github/
  /workflows/              # CI/CD pipelines
  CODEOWNERS


Backend internal layout 
/backend/app/
  /domain/
    models.py         # Position, Order, Trade, Event, enums
    rules/
      guardrails.py
      triggers.py
      tax.py
  /ports/
    repositories.py   # PositionRepo, OrderRepo, TradeRepo, EventRepo
    services.py       # IdempotencyPort, PricingPort, EventBusPort, ClockPort
  /adapters/
    memory/           # in-memory repos & idempotency
    db/               # future SQLAlchemy repos
    redis/            # idempotency SETNX
    broker/           # execution stub/real
  /services/
    order_service.py      # submit->validate->execute->settle->events
    strategy_service.py   # evaluate triggers, max-per-day, idempotent keys
    settlement_service.py # dividends, fees; apply to position
    evaluation_service.py # KPIs, guardrail status
  /api/
    dto.py               # Pydantic schemas
    routes_orders.py     # /v1/positions/{id}/orders
    routes_positions.py
    routes_health.py
    mappers.py
  main.py



---

## /docs/README.md

````markdown
# Volatility Balancing — Docs Index

**Source of truth** for specs. Changes land via Pull Request (PR) with reviewers: **CTO** (Architecture), **PM** (Product), **QA** (Testability).

## Conventions
- All docs in **Markdown** with Mermaid diagrams.
- Each file includes front‑matter:
  ```yaml
  ---
  owner: <team-or-person>
  status: draft|review|approved|deprecated
  last_updated: YYYY-MM-DD
  related: [links to PRDs/ADRs/Issues]
  ---
````

* Link issues as `#123` and PRs as `!45` (or GitHub `#45`).

## Folders

* `/product` — PRDs & functional specs
* `/architecture` — system/tech designs & API contracts
* `/adr` — Architecture Decision Records
* `/runbooks` — operational playbooks
* `/api` — OpenAPI and API governance

## Review Workflow (Docs PRs)

1. Author opens PR changing docs + code if applicable.
2. PM reviews **What/Why**; CTO reviews **How/Security**.
3. Merge only when PRD & Arch diffs are consistent; create/append ADR if decision changed.

````

---

## /docs/product/PRD_TEMPLATE.md
```markdown
---
owner: PM Team
status: draft
last_updated: 2025-08-24
related: ["/docs/architecture/ARCH_TEMPLATE.md", "ADR-0001"]
---
# <Feature Name> — PRD

## 1. Summary (What & Why)
- One paragraph stating the user problem and business goal.

## 2. Goals / Non‑Goals
- **Goals:** …
- **Out of scope:** …

## 3. User Stories & Acceptance Criteria
- As an <investor>, I want … so that …
- **AC:** Given … When … Then …

## 4. Metrics / Success
- e.g., % time within guardrails, hit rate, fee drag.

## 5. UX Notes
- Screens affected, states, empty/error states.
- Link to wireframes.

## 6. Risks & Compliance
- PCI/PII impact, disclosures, rate limits, auditability.

## 7. Open Questions
- …
````

---

## /docs/architecture/ARCH\_TEMPLATE.md

````markdown
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
````

## 3. Data Model

* Tables/fields, indexes; migration plan.

## 4. API Contracts

* Endpoints, request/response JSON; error codes.

## 5. Sequence / Lifecycle

* Key interactions and timeouts.

## 6. Security & Compliance

* AuthN/Z, scopes, secrets, encryption, audit.

## 7. Observability

* Logs, metrics, tracing, DLQs.

## 8. Rollout Plan

* Flags, phases, backout, runbook links.

## 9. Alternatives Considered

* Summarize options with trade‑offs.

````

---

## /docs/architecture/SEQUENCE_EXAMPLE.md
```markdown
# Sequence Examples (Mermaid)

## Tick → Trade
```mermaid
sequenceDiagram
  participant MD as Market Data
  participant DEC as Decision Engine
  participant ORD as Order Manager
  participant BRK as Brokerage
  participant DB as Postgres
  MD->>DEC: PriceEvent
  DEC->>DB: Load position & config
  DEC->>DEC: Evaluate triggers & size
  alt Skip
    DEC-->>DB: Event(reason="min_notional")
  else Send order
    DEC-->>ORD: OrderIntent
    ORD->>BRK: Submit
    BRK-->>ORD: Fill
    ORD->>DB: Update cash/anchor/events
  end
````

````

---

## /docs/adr/ADR_TEMPLATE.md
```markdown
---
owner: Architecture
status: approved|proposed
last_updated: 2025-08-24
related: []
---
# ADR-XXXX: <Decision Title>

## Context
- What problem are we solving?

## Decision
- The choice made (e.g., **Modular monolith on AWS Lambda with FastAPI**).

## Consequences
- Positive/negative outcomes, risks, follow‑ups.

## Alternatives
- Options considered and why not chosen.

## References
- Links to PRs, issues, benchmarks.
````

---

## /docs/runbooks/RUNBOOK\_TEMPLATE.md

```markdown
---
owner: SRE/Platform
status: draft
last_updated: 2025-08-24
---
# <Runbook Name>

## Summary
- When to use this, severity, primary on‑call.

## Preconditions
- Feature flags, credentials, tools required.

## Procedure
1) …
2) …

## Validation & Rollback
- How to confirm success, rollback steps.

## Dashboards & Alerts
- Links to CloudWatch, Grafana.
```

---

## /docs/api/OPENAPI\_README.md

```markdown
# API Governance
- All external HTTP APIs must be captured in **OpenAPI 3.0** under `/docs/api/openapi.yaml`.
- Changes require a docs PR; CI validates schema.

## Local Preview
- Use Redocly or Swagger‑UI to render.

## Versioning
- SemVer on endpoints; breaking changes require major bump and deprecation notes in PRD.
```

---

## /.github/PULL\_REQUEST\_TEMPLATE\_docs.md

```markdown
## Docs Checklist
- [ ] PRD updated (What/Why)
- [ ] Architecture updated (How)
- [ ] ADR added/updated (Decision)
- [ ] Runbook updated (Operate)
- [ ] Diagrams (Mermaid) render locally
- [ ] Security/Compliance reviewed

## Links
- PRD:
- Arch:
- ADR:
- Runbook:
```

## Quick Start
```bash
make up setup migrate
make run-api     # http://localhost:8000
make run-web     # http://localhost:3000
```
