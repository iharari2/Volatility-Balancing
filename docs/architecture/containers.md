```mermaid
flowchart TB
  UI[React SPA] --> API[FastAPI]
  API --> DB[(Postgres/SQLite)]
  API --> MQ[(Queue)]
  Worker --> DB
  Worker --> MQ
```
