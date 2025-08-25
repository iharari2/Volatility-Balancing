
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
