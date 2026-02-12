# Development Plan Status

**Last Updated**: February 12, 2026
**Project**: Volatility Balancing System

---

## Completed Iterations (1-8)

| # | Iteration | Commit | Summary |
|---|-----------|--------|---------|
| 1 | Algorithm Correctness Audit | `23c220b` | 90 unit tests across 6 files validating order sizing, triggers, guardrails, commission |
| 2 | EC2 Deployment Runbook | `f00d647` | Runbook, .env.example, systemd service template, deploy script |
| 3 | UX Foundation | `0a95142` | Toast notifications, ConfirmDialog, ErrorBoundary components |
| 4 | Form Validation | `6b63bbf` | FormField component, numeric input constraints |
| 5 | Repo Cleanup | `65e87a7` | Archive legacy docs/scripts, remove deprecated routes |
| 6 | Unified Trade Tracking (Backend) | `069e326` | Order/trade enrichment, pagination, explainability API |
| 7 | Trade Tracking Frontend + Guardrail Fix | `45e926f`, `6eddece` | Guardrail defaults 25%/75%, server-side pagination, order status filter |
| 8 | Monitoring & Alerting | `1d0af9d` | Alert system (6 conditions), webhook delivery, enhanced health, structured logging |

**Test suite**: 534 passed, 24 pre-existing failures (orders API, cancel/status, gate1 deterministic), 11 skipped

---

## Iteration 9: Fix Pre-existing Test Failures

**Priority**: High
**Effort**: Medium

The test suite has 24 pre-existing failures and 3 errors across 4 test files. These block CI/CD adoption and mask real regressions.

| Test File | Failures | Root Cause |
|-----------|----------|------------|
| `test_orders_api.py` | 14 failures + 3 errors | Route paths changed, endpoints return 404 |
| `test_orders_cancel_status.py` | 9 failures | Same route/endpoint mismatch |
| `test_orders_list.py` | 1 failure | Same route/endpoint mismatch |
| `test_gate1_deterministic_ticks.py` | 2 failures | SQLite NOT NULL constraint on `dividend_applied` column |
| `test_main_app.py` | 1 failure | `test_endpoint_discovery` expects removed `/v1/orders/{order_id}/fill` path |

**Tasks**:
- Fix or remove order API integration tests to match current route structure
- Fix gate1 deterministic tick test (missing `dividend_applied` column in INSERT)
- Update endpoint discovery test to reflect current API surface
- Target: 0 failures, green CI

---

## Iteration 10: Wire Audit Trail API to UI

**Priority**: Medium
**Ref**: FEAT-2

**Current State**:
- `AuditTrailPage` UI exists with filtering (asset, date range, event type, source, trace ID)
- Backend `/v1/audit/traces` endpoint exists
- UI currently shows placeholder / "under migration to real-time logs"

**Tasks**:
- Wire `AuditTrailPage` to fetch from `/v1/audit/traces` API
- Implement trace list pagination
- Enable trace detail expansion with full event payloads
- Verify JSON export per trace works end-to-end

**Files**: `frontend/src/features/audit/AuditTrailPage.tsx`, `backend/app/routes/audit.py`

---

## Iteration 11: Wire Dividends API to UI + Export

**Priority**: Medium
**Ref**: FEAT-1, FEAT-3

**Current State**:
- `DividendsTab` UI exists with upcoming/history sections
- Returns empty mock data (TODO comment indicates API fetch needed)
- Backend has dividend entities and processing logic but no dedicated listing endpoint

**Tasks**:
- Create backend `GET /v1/positions/{id}/dividends` endpoint (or portfolio-scoped)
- Query dividend events from position_evaluation_timeline or dividend tables
- Wire `DividendsTab` to fetch from API
- Add dividend tracker dashboard (upcoming ex-dates, received payments)
- Add Excel/CSV export button for dividend history

**Files**: `frontend/src/features/positions/DividendsTab.tsx`, dividend routes

---

## Iteration 12: Heatmap Visualization

**Priority**: Medium

**Current State**:
- Backend heatmap data structures and API endpoints exist (70% complete)
- No frontend visualization component

**Tasks**:
- Create interactive heatmap visualization component (e.g., D3.js or recharts)
- Wire to existing `/v1/optimization/configs/{id}/heatmap` endpoint
- Parameter sensitivity display with color-coded cells
- Hover tooltips showing metric values
- Axis labels for parameter ranges

---

## Iteration 13: Monitoring Frontend Dashboard

**Priority**: Medium

**Current State**:
- Backend monitoring endpoints complete (Iteration 8): `/v1/system/status`, `/v1/alerts`, webhook config
- No frontend dashboard

**Tasks**:
- Create system status dashboard page showing component health, uptime, worker status
- Alert list with acknowledge/resolve actions
- Webhook configuration UI
- Auto-refresh with configurable interval
- Visual indicators for healthy/degraded/unhealthy states

---

## Iteration 14: CI/CD Pipeline

**Priority**: High

**Current State**:
- GitHub repo, EC2 runtime with systemd, SSM access
- No automated CI/CD pipeline
- Deploy script exists (`scripts/vb-deploy`)

**Tasks**:
- GitHub Actions workflow: lint (ruff), unit tests, integration tests, frontend build
- Gate on test pass + TypeScript compilation
- Automated deployment to EC2 on push to main (with manual approval)
- Post-deploy smoke test (`scripts/smoke.sh`)
- Trading-aware deployment checks (warn during market hours)

---

## Iteration 15: Broker Integration (Alpaca)

**Priority**: High
**Ref**: PRD Goal #7

**Current State**:
- `IBrokerService` port defined, `StubBrokerAdapter` implemented
- `BrokerIntegrationService` and `OrderStatusWorker` wired
- `APP_BROKER=alpaca` env var placeholder exists but falls back to stub

**Tasks**:
- Implement `AlpacaBrokerAdapter` against Alpaca Trading API
- Paper trading mode first, then live
- Order submission, status polling, fill reconciliation
- Credential management via env vars
- Integration tests with Alpaca sandbox

---

## Open Feature Requests

| ID | Feature | Priority | Status |
|----|---------|----------|--------|
| FEAT-1 | Dividend tracker (view + export) | Medium | Planned (Iteration 11) |
| FEAT-2 | Wire Audit Trail API to UI | Medium | Planned (Iteration 10) |
| FEAT-3 | Wire Dividends API to UI + export | Medium | Planned (Iteration 11) |

---

## Backlog (Unprioritized)

These items come from the PRD and unified development plan but are not yet scheduled:

- **Debug checkbox for export filtering** — filter "all events" vs "successful transactions only"
- **Position change logging** — simple change log entries on position modifications
- **Real-time data UI** — data source selector, live vs cached indicators
- **Mobile responsive design** — optimize for tablet/mobile
- **Multi-asset correlation** — portfolio-level cross-position analysis
- **Dynamic thresholds** — adaptive parameter adjustment based on market regime
- **DRIP support** — automated dividend reinvestment
- **Tax-lot optimization** — tax-efficient trading strategies
- **PostgreSQL migration** — move from SQLite to PostgreSQL for production

---

## Previously Resolved Issues

All issues from the original tracker have been fixed:

| Category | IDs | Count |
|----------|-----|-------|
| Portfolio Config | CP-1 through CP-4 | 4 fixed |
| Simulation | SIM-1 through SIM-4 | 4 fixed |
| Navigation | NAV-1 | 1 fixed |
| Analytics | ANA-1 through ANA-7 | 7 fixed |
| Visualization | VIS-1 | 1 fixed |
| Settings | SET-1 | 1 fixed |
| **Total** | | **18 fixed** |
