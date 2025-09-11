#!/usr/bin/env python3
import os, shutil, datetime

today = datetime.date.today().isoformat()

def write(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content.lstrip())

write("docs/README.md", f"""
# Volatility Balancing — Docs Index
Front-matter for each file:
---
owner: <team>
status: draft
last_updated: {today}
related: []
---
""")

write("docs/product/PRD_TEMPLATE.md", f"""
---
owner: PM
status: draft
last_updated: {today}
---
# <Feature> — PRD
## Summary
## Goals / Non-Goals
## Stories
## Metrics
## Risks
""")

write("docs/architecture/ARCH_TEMPLATE.md", f"""
---
owner: Eng
status: draft
last_updated: {today}
---
# <Feature> — Technical Design

```mermaid
flowchart LR
  WEB[Next.js] --> APIG[API Gateway]
  APIG --> API[FastAPI]
  API --> DB[(Postgres)]
""")

write("docs/adr/ADR_TEMPLATE.md", f"""
owner: Architecture
status: proposed
last_updated: {today}
ADR-XXXX: <Decision Title>
Context
Decision
Consequences
Alternatives

""")
