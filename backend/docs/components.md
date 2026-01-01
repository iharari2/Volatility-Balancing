```mermaid
flowchart LR
  Orchestrator --> EvaluatePositionUC
  EvaluatePositionUC --> PriceTrigger
  EvaluatePositionUC --> GuardrailEvaluator
  Orchestrator --> SubmitOrderUC
  SubmitOrderUC --> OrderRepo
  SubmitOrderUC --> BrokerAdapter
  ExecuteOrderUC --> PositionRepo
  ExecuteOrderUC --> CashRepo
  All --> EventLogger
```
