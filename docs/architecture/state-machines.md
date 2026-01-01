```mermaid
stateDiagram-v2
  READY --> RUNNING
  RUNNING --> PAUSED
  PAUSED --> RUNNING
  RUNNING --> ERROR
```
