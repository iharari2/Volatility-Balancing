# Deployment Architecture

This document describes the deployment architecture for the Volatility Balancing system.

## Development Environment

```mermaid
graph TB
  subgraph "Development Environment"
    subgraph "Frontend"
      DEV_FE["React Dev Server<br/>localhost:3000"]
    end

    subgraph "Backend"
      DEV_API["FastAPI Server<br/>localhost:8000"]
      DEV_DB["SQLite Database<br/>vb.sqlite"]
      DEV_REDIS["Redis (Optional)<br/>localhost:6379"]
    end

    subgraph "External Services"
      YFIN["YFinance API<br/>Public API"]
    end
  end

  DEV_FE -->|HTTP| DEV_API
  DEV_API --> DEV_DB
  DEV_API --> DEV_REDIS
  DEV_API --> YFIN
```

## Production Environment

```mermaid
graph TB
  subgraph "Production Environment"
    subgraph "Load Balancer"
      LB["Load Balancer<br/>nginx/ALB"]
    end

    subgraph "Frontend"
      PROD_FE["React SPA<br/>Static Files"]
      CDN["CDN<br/>CloudFront/S3"]
    end

    subgraph "Backend Services"
      API1["FastAPI Instance 1<br/>Container"]
      API2["FastAPI Instance 2<br/>Container"]
      API3["FastAPI Instance N<br/>Container"]
    end

    subgraph "Data Layer"
      PROD_DB["PostgreSQL<br/>RDS/Aurora"]
      PROD_REDIS["Redis<br/>ElastiCache"]
      PROD_S3["S3 Bucket<br/>Static Assets"]
    end

    subgraph "External Services"
      YFIN_PROD["YFinance API<br/>Rate Limited"]
      BROKER["Brokerage APIs<br/>Production"]
    end

    subgraph "Monitoring"
      LOGS["CloudWatch Logs"]
      METRICS["CloudWatch Metrics"]
      ALARMS["CloudWatch Alarms"]
    end
  end

  LB --> PROD_FE
  LB --> API1
  LB --> API2
  LB --> API3

  PROD_FE --> CDN
  CDN --> PROD_S3

  API1 --> PROD_DB
  API2 --> PROD_DB
  API3 --> PROD_DB

  API1 --> PROD_REDIS
  API2 --> PROD_REDIS
  API3 --> PROD_REDIS

  API1 --> YFIN_PROD
  API2 --> YFIN_PROD
  API3 --> YFIN_PROD

  API1 --> BROKER
  API2 --> BROKER
  API3 --> BROKER

  API1 --> LOGS
  API2 --> LOGS
  API3 --> LOGS

  LOGS --> METRICS
  METRICS --> ALARMS
```

## Container Architecture

```mermaid
graph TB
  subgraph "Docker Compose (Development)"
    subgraph "Frontend Container"
      FE_CONTAINER["nginx:alpine<br/>Serves React SPA"]
    end

    subgraph "Backend Container"
      API_CONTAINER["python:3.11-slim<br/>FastAPI Application"]
    end

    subgraph "Database Container"
      DB_CONTAINER["postgres:15<br/>Database"]
    end

    subgraph "Cache Container"
      REDIS_CONTAINER["redis:7-alpine<br/>Cache & Idempotency"]
    end
  end

  FE_CONTAINER -->|HTTP| API_CONTAINER
  API_CONTAINER -->|SQL| DB_CONTAINER
  API_CONTAINER -->|Redis Protocol| REDIS_CONTAINER
```

## Kubernetes Deployment

```mermaid
graph TB
  subgraph "Kubernetes Cluster"
    subgraph "Ingress"
      INGRESS["Ingress Controller<br/>nginx-ingress"]
    end

    subgraph "Frontend Namespace"
      FE_POD1["Frontend Pod 1"]
      FE_POD2["Frontend Pod 2"]
      FE_SVC["Frontend Service"]
    end

    subgraph "Backend Namespace"
      API_POD1["API Pod 1"]
      API_POD2["API Pod 2"]
      API_POD3["API Pod 3"]
      API_SVC["API Service"]
    end

    subgraph "Data Namespace"
      DB_POD["PostgreSQL Pod"]
      REDIS_POD["Redis Pod"]
      DB_SVC["Database Service"]
      REDIS_SVC["Redis Service"]
    end

    subgraph "Monitoring Namespace"
      PROMETHEUS["Prometheus"]
      GRAFANA["Grafana"]
      JAEGER["Jaeger Tracing"]
    end
  end

  INGRESS --> FE_SVC
  INGRESS --> API_SVC

  FE_SVC --> FE_POD1
  FE_SVC --> FE_POD2

  API_SVC --> API_POD1
  API_SVC --> API_POD2
  API_SVC --> API_POD3

  API_POD1 --> DB_SVC
  API_POD2 --> DB_SVC
  API_POD3 --> DB_SVC

  API_POD1 --> REDIS_SVC
  API_POD2 --> REDIS_SVC
  API_POD3 --> REDIS_SVC

  DB_SVC --> DB_POD
  REDIS_SVC --> REDIS_POD

  API_POD1 --> PROMETHEUS
  API_POD2 --> PROMETHEUS
  API_POD3 --> PROMETHEUS

  PROMETHEUS --> GRAFANA
  API_POD1 --> JAEGER
  API_POD2 --> JAEGER
  API_POD3 --> JAEGER
```

## Infrastructure as Code

```mermaid
graph TB
  subgraph "Terraform Configuration"
    subgraph "Networking"
      VPC["VPC"]
      SUBNETS["Private/Public Subnets"]
      SG["Security Groups"]
      NACL["Network ACLs"]
    end

    subgraph "Compute"
      ECS["ECS Cluster"]
      FARGATE["Fargate Tasks"]
      ALB["Application Load Balancer"]
    end

    subgraph "Data"
      RDS["RDS PostgreSQL"]
      ELASTICACHE["ElastiCache Redis"]
      S3["S3 Buckets"]
    end

    subgraph "Security"
      IAM["IAM Roles & Policies"]
      KMS["KMS Keys"]
      SECRETS["Secrets Manager"]
    end

    subgraph "Monitoring"
      CW["CloudWatch"]
      XRAY["X-Ray"]
      SNS["SNS Topics"]
    end
  end

  VPC --> SUBNETS
  SUBNETS --> SG
  SG --> NACL

  ALB --> ECS
  ECS --> FARGATE

  FARGATE --> RDS
  FARGATE --> ELASTICACHE
  FARGATE --> S3

  FARGATE --> IAM
  RDS --> KMS
  ELASTICACHE --> KMS
  S3 --> KMS

  FARGATE --> SECRETS
  RDS --> SECRETS

  FARGATE --> CW
  FARGATE --> XRAY
  CW --> SNS
```

## Environment Configuration

### Development

- **Frontend**: React dev server with hot reload
- **Backend**: FastAPI with auto-reload
- **Database**: SQLite for simplicity
- **Cache**: Optional Redis for testing
- **External**: YFinance API (rate limited)

### Staging

- **Frontend**: Static build served by nginx
- **Backend**: FastAPI in Docker container
- **Database**: PostgreSQL on RDS
- **Cache**: Redis on ElastiCache
- **External**: YFinance API + Broker sandbox

### Production

- **Frontend**: CDN-distributed static files
- **Backend**: Multiple FastAPI instances behind load balancer
- **Database**: PostgreSQL on RDS with read replicas
- **Cache**: Redis cluster on ElastiCache
- **External**: YFinance API + Production broker APIs
- **Monitoring**: Full observability stack

## Security Considerations

### Network Security

- VPC with private subnets for backend services
- Public subnets only for load balancers
- Security groups with least privilege access
- WAF for additional protection

### Data Security

- Encryption at rest for all data stores
- Encryption in transit (TLS 1.3)
- Secrets managed through AWS Secrets Manager
- Regular security updates and patches

### Application Security

- Input validation and sanitization
- Rate limiting and DDoS protection
- Idempotency keys for order deduplication
- Audit trails for all operations

## Scalability

### Horizontal Scaling

- Stateless backend services
- Load balancer distribution
- Database read replicas
- Redis cluster mode

### Vertical Scaling

- Auto-scaling groups for backend
- Database instance scaling
- Cache memory scaling
- CDN for global distribution

## Disaster Recovery

### Backup Strategy

- Automated database backups
- Cross-region replication
- Point-in-time recovery
- Configuration backup

### Recovery Procedures

- RTO: 4 hours for full recovery
- RPO: 1 hour maximum data loss
- Automated failover for critical services
- Manual procedures for complex scenarios
