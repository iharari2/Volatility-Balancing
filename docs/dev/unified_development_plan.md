---
owner: Development Team
status: active
last_updated: 2026-04-14
---

# Volatility Balancing — Development Plan

## Current State

**Phase 1 complete. Fly.io migration complete.** Test suite: 603 passed (13 skipped) | Ruff clean | TypeScript clean | CI: all 4 jobs green → deploys to Fly.io.

| Area | Completion |
|---|---|
| Portfolio Management | 100% ✅ |
| Simulation | 100% ✅ |
| Parameter Optimization | 100% ✅ |
| Excel Export | 100% ✅ |
| Broker Integration (Alpaca) | 100% ✅ |
| Monitoring Dashboard | 100% ✅ |
| Authentication (JWT + multi-tenant) | 100% ✅ |
| Analytics & Reporting | 100% ✅ |
| Event Tracking / Explainability | 100% ✅ |
| Trading Interface | 100% ✅ |
| Real-time Data UI | 100% ✅ |

---

## Completed Iterations

| # | Iteration | Key Deliverable |
|---|---|---|
| 1 | Algorithm Correctness Audit | 90 unit tests — order sizing, triggers, guardrails, commission |
| 2 | EC2 Deployment Runbook | Runbook, systemd template, deploy script |
| 3 | UX Foundation | Toast, ConfirmDialog, ErrorBoundary |
| 4 | Form Validation | FormField component, numeric input constraints |
| 5 | Repo Cleanup | Archive legacy docs/scripts, remove deprecated routes |
| 6 | Trade Tracking (Backend) | Order/trade enrichment, pagination, explainability API |
| 7 | Trade Tracking (Frontend) | Guardrail defaults 25%/75%, server-side pagination |
| 8 | Monitoring & Alerting | 6-condition alert system, webhook delivery, structured logging |
| 9 | Test Fixes | All 118 integration tests passing |
| 10 | Remove Audit Trail | Deleted 10 files (−2,383 lines); evaluation timeline is canonical |
| 11 | Dividends UI | Workspace tab, dividendApi wired, datetime timezone bug fix |
| 12 | Optimization Page | Config list, heatmap, results view, routing + nav |
| 13 | Monitoring Dashboard | Health cards, alerts table, webhook config UI, 30s auto-refresh |
| 14 | Real Simulation Engine | Replaced mock metrics with SimulationUnifiedUC; 10 real metrics; prefetch market data once |
| 15 | Persist + Export | SQL optimization repos, Excel wired to 6 tables, pytest-xdist parallel |
| 16 | CI/CD Fix | All 4 CI jobs green; migration fix, ESLint config, coverage threshold |
| 17 | Broker Integration (Alpaca) | AlpacaBrokerAdapter wired in DI, broker status endpoint (`GET /v1/broker/status`) |
| — | Bug Fixes | Order fill persistence, workspace Orders Excel scoped to position, Dividends Excel export |
| 20 | Analysis Enhancements | Real data in overview tables; PerformanceChart vs market API; commission, dividend, guardrail band charts in simulation |
| 20b | Optimization Config Management | Edit, rerun, delete actions on saved configs (backend PUT/DELETE/reset + frontend UI) |
| 21 | Analytics Deep Enhancements | Date range + chart brush, resolution (daily/weekly/hourly), benchmark selector, analytics Excel export, event markers fix |
| 22 | JWT Authentication | User accounts, JWT tokens, protected routes, login page, change-password, tenant isolation |
| 23 | Schema & Endpoints | Alembic migrations for schema management; manual adjust + anchor endpoints |
| 24 | Remove Dual Evaluation Paths | Single evaluation path via `evaluate_with_market_data()`; −486 lines; eliminates duplicate orders |
| 25 | Audit Traceability Tool | CLI script + 28 integration tests verifying cross-table consistency (timeline ↔ orders ↔ trades) |
| 26 | Real-time Data UI Indicators | `MarketDataBadge` component; freshness dot + source chip + elapsed timer wired into OverviewTab, TradingTab, WorkspaceTopBar |
| 27 | Fly.io Migration | Replaced EC2+SSM with Fly.io (backend) + Cloudflare Pages (frontend) + Neon (PostgreSQL); CI deploys via `flyctl deploy`; ~$3/month |
| 28 | User Management Console | Admin UI at `/admin/users` (owner-only); list/edit-role/enable-disable users; `set-role` CLI subcommand; `GET|PATCH /v1/admin/users` endpoints |
| 29 | Bug Fixes: Onboarding, Orders, Simulation | Fix blank onboarding page; fix Orders 404 (route prefix `/api/` → `/v1/`); fix onboarding field names + error formatting; add impersonation escape hatch; fix simulation future-date error (cap vs reject); add daily fetch retry logic; add TopBar user menu with logout |

---

## Roadmap

### Phase 2: Environment Separation — Next

Establish proper Dev / Staging / Production environments.

**Dev**: Docker Compose, SQLite, mock services, hot reload
**Staging**: AWS mirrors prod, PostgreSQL, paper trading, full CI/CD
**Production**: HA PostgreSQL, live trading, monitoring, disaster recovery

Deliverables:
- Terraform IaC modules per environment
- Separate AWS accounts with network isolation
- Automated deployment pipeline with manual prod approval gate
- Environment-specific secrets management

**Success criteria**: Complete isolation, zero data leakage between environments, 100% IaC coverage.

---

### Phase 3: Production Deployment

- **Frontend**: S3 + CloudFront
- **Backend**: FastAPI on AWS Lambda + API Gateway
- **Database**: PostgreSQL RDS + Redis ElastiCache
- **Auth**: AWS Cognito + KMS encryption
- **Async workers**: EventBridge → SQS → Lambda
- **Observability**: CloudWatch dashboards, centralized logging, alerting

**Success criteria**: 99.9% uptime, <100ms API response times, zero security vulnerabilities.

---

### Phase 4: Advanced Trading Features

- Multi-asset portfolio allocation
- Dynamic / adaptive trigger thresholds
- DRIP (dividend reinvestment)
- Tax-lot optimization
- TWAP order execution
- Advanced risk controls (real-time exposure monitoring)
- Multi-tenant architecture

**Success criteria**: 10+ concurrent users, 100+ positions managed, <1s real-time updates.

---

### Phase 5: Scale & Enterprise

- Sub-second execution, HFT capabilities
- ML-based parameter optimization
- Additional broker integrations (Meitav, Excellence Trade, others)
- Webhook / notification system
- Enterprise compliance (FINRA, SEC, GDPR/CCPA)

**Success criteria**: Sub-100ms execution, 1000+ API req/sec, 99.99% uptime.

---

## Backlog (Unscheduled)

- Debug checkbox for export filtering (events vs successful transactions only)
- Position change logging
- Real-time data UI indicators (live vs cached source)
- Mobile / tablet responsive design
- **PostgreSQL migration** — move dev off SQLite
- Dynamic thresholds
- DRIP support
- Tax-lot optimization
- Notification / alert system (configurable, medium priority)
