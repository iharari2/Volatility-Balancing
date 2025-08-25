python3 - <<'PY'
import os, shutil, sys, datetime, textwrap

repo = "."
docs = os.path.join(repo, "docs")
os.makedirs(os.path.join(docs, "product"), exist_ok=True)
os.makedirs(os.path.join(docs, "architecture"), exist_ok=True)
os.makedirs(os.path.join(docs, "adr"), exist_ok=True)
os.makedirs(os.path.join(docs, "runbooks"), exist_ok=True)
os.makedirs(os.path.join(docs, "api"), exist_ok=True)
os.makedirs(".github", exist_ok=True)
os.makedirs(".github/workflows", exist_ok=True)

today = datetime.date.today().isoformat()

def w(path, content):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content.lstrip())

# --- Files ---
w("docs/README.md", f"""
# Volatility Balancing — Docs Index
Source of truth for specs. Changes land via Pull Request with reviewers: CTO (Architecture), PM (Product), QA (Testability).

## Conventions
Each file has front‑matter:
---
owner: <team-or-person>
status: draft|review|approved|deprecated
last_updated: YYYY-MM-DD
related: []
---
Folders:
- /product — PRDs & functional specs
- /architecture — system/tech designs & API contracts
- /adr — Architecture Decision Records
- /runbooks — operational playbooks
- /api — OpenAPI and API governance
""")

w("docs/product/PRD_TEMPLATE.md", f"""
---
owner: PM Team
status: draft
last_updated: {today}
related: []
---
# <Feature Name> — PRD
## 1. Summary (What & Why)
## 2. Goals / Non‑Goals
## 3. User Stories & Acceptance Criteria
## 4. Metrics
## 5. UX Notes
## 6. Risks & Compliance
## 7. Open Questions
""")

w("docs/architecture/ARCH_TEMPLATE.md", f"""
---
owner: Platform Eng
status: draft
last_updated: {today}
related: []
---
# <Feature Name> — Technical Design

## 1. Overview
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
