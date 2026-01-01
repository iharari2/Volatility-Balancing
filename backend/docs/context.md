```mermaid
flowchart LR
  U[User] --> UI[React Web GUI]
  UI --> API[Backend API]
  API --> DB[(Database)]
  API --> MQ[(Event Queue)]
  API --> MD[Market Data]
  API --> BR[Broker]
```
