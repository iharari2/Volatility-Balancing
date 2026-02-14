# Development Plan Status

**Last Updated**: February 15, 2026
**Project**: Volatility Balancing System

---

## Completed Iterations (1-10)

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
| 9 | Fix Pre-existing Test Failures | `87512d6` | Fixed all 24 pre-existing failures + 3 errors across 5 test files; 118 integration tests passing |
| 10 | Remove Redundant Audit Trail | `d1ad201` | Deleted 10 files (JSONL logger, event ports, audit route, UI page, docs), cleaned event_logger from orchestrators/services/DI; net -2,383 lines |
| 11 | Wire Dividends API to UI + Workspace Tab | — | Fixed backend route paths, wired frontend dividendApi with tenant/portfolio params, added Dividends workspace tab, deleted skeleton DividendsTab, fixed naive-vs-aware datetime bug in OrderStatusWorker |

**Test suite**: 561 passed (13 skipped), ruff clean, TypeScript clean, frontend builds clean

---

## Iteration 11: Wire Dividends API to UI + Workspace Tab — COMPLETE

**Priority**: Medium
**Ref**: FEAT-1, FEAT-3

**What was done**:
- **Backend route fix**: Removed `/api` prefix from 3 dividend sub-paths (`status`, `process-ex-dividend`, `process-payment`) so full URLs follow `GET /v1/dividends/tenants/{t}/portfolios/{p}/positions/{pos}/status`
- **Frontend API layer**: Updated `dividendApi` methods (`getPositionStatus`, `processExDividend`, `processPayment`) to accept `tenantId`/`portfolioId` and construct correct URL paths
- **React Query hooks**: Updated all position-scoped hooks in `useDividends.ts` to pass tenant/portfolio params
- **DividendManagement component**: Added `tenantId`/`portfolioId` to props, threaded through to hooks; also fixed usage in legacy `PositionDetail.tsx`
- **Workspace Dividends tab**: Added `'dividends'` to `WorkspaceTab` union, added tab with `DollarSign` icon in `DetailTabBar`, created new `DividendsTab` wrapper in workspace tabs, wired rendering in `RightPanel`
- **Deleted skeleton**: Removed old `DividendsTab.tsx` (mock data) from `features/positions/`, cleaned up import in `PositionsPage.tsx`
- **Test fixes**: Updated integration tests (`test_dividend_api.py`, `test_main_app.py`) to use new route paths
- **Bug fix**: Fixed `TypeError: can't subtract offset-naive and offset-aware datetimes` in `OrderStatusWorker` — added `_ensure_aware()` helper applied at all 3 datetime arithmetic sites (Phase 1 stuck orders, Phase 3 IOC/FOK, stale DAY order check)

**Files modified** (10 files):
- `backend/app/routes/dividends.py` — route path fix
- `backend/application/services/order_status_worker.py` — datetime bug fix
- `backend/tests/integration/test_dividend_api.py` — test URL updates
- `backend/tests/integration/test_main_app.py` — test URL updates
- `frontend/src/lib/api.ts` — dividendApi URL + params
- `frontend/src/hooks/useDividends.ts` — hook params
- `frontend/src/components/DividendManagement.tsx` — props
- `frontend/src/pages/PositionDetail.tsx` — plumb tenant/portfolio to DividendManagement
- `frontend/src/features/workspace/WorkspaceContext.tsx` — tab type
- `frontend/src/features/workspace/components/RightPanel/DetailTabBar.tsx` — tab entry
- `frontend/src/features/workspace/components/RightPanel/RightPanel.tsx` — tab rendering

**Files created** (1):
- `frontend/src/features/workspace/components/tabs/DividendsTab.tsx`

**Files deleted** (1):
- `frontend/src/features/positions/DividendsTab.tsx`

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
| ~~FEAT-1~~ | ~~Dividend tracker (view + export)~~ | ~~Medium~~ | Done — Iteration 11 (UI wired to API, workspace tab added) |
| ~~FEAT-2~~ | ~~Wire Audit Trail API to UI~~ | ~~Medium~~ | Removed — audit trail deleted in Iteration 10; evaluation timeline is the canonical source |
| ~~FEAT-3~~ | ~~Wire Dividends API to UI + export~~ | ~~Medium~~ | Done — Iteration 11 (API connected, Excel export TBD as backlog) |

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
