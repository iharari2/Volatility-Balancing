```mermaid
erDiagram
  PORTFOLIOS ||--o{ POSITIONS : contains
  PORTFOLIOS ||--|| PORTFOLIO_CASH : has
  PORTFOLIOS ||--|| PORTFOLIO_CONFIG : uses
  PORTFOLIOS ||--o{ ORDERS : creates
  ORDERS ||--o{ TRADES : fills
  PORTFOLIOS ||--o{ EVENTS : logs
```
