# Development Plan Status

**Last Updated**: 2026-04-08 (post-Iteration 27)

> Iteration details are summarized in [`unified_development_plan.md`](unified_development_plan.md).
> This file tracks per-commit specifics for reference.

---

## Iteration Log

| # | Iteration | Commit | Notes |
|---|-----------|--------|-------|
| 1 | Algorithm Correctness Audit | `23c220b` | 90 unit tests across 6 files |
| 2 | EC2 Deployment Runbook | `f00d647` | Runbook, .env.example, systemd, deploy script |
| 3 | UX Foundation | `0a95142` | Toast, ConfirmDialog, ErrorBoundary |
| 4 | Form Validation | `6b63bbf` | FormField, numeric input constraints |
| 5 | Repo Cleanup | `65e87a7` | Archive legacy docs/scripts, remove deprecated routes |
| 6 | Trade Tracking (Backend) | `069e326` | Order/trade enrichment, pagination, explainability API |
| 7 | Trade Tracking (Frontend) | `45e926f`, `6eddece` | Guardrail defaults 25%/75%, server-side pagination, order status filter |
| 8 | Monitoring & Alerting | `1d0af9d` | Alert system (6 conditions), webhook delivery, structured logging |
| 9 | Fix Pre-existing Test Failures | `87512d6` | 24 failures + 3 errors fixed; 118 integration tests passing |
| 10 | Remove Redundant Audit Trail | `d1ad201` | Deleted 10 files (−2,383 lines) |
| 11 | Dividends UI | `ccadf2e` | Route fix, dividendApi wired, workspace tab, datetime bug in OrderStatusWorker |
| — | Bug: Order fill persistence | `8ffca72` | `filled_qty`/`avg_fill_price` not persisted — fixed |
| 12 | Optimization & Heatmap Page | — | OptimizationPage, routing, nav entry |
| 13 | Monitoring Dashboard | `1fd6dcb` | Health cards, alerts table, webhook config, 30s auto-refresh |
| 14 | Real Simulation Engine | — | Real SimulationUnifiedUC runs, market data prefetch, 10 metrics, non-blocking start |
| 15 | Persist + Export + Tests | — | SQL optimization repos, Excel wired to 6 tables, pytest-xdist, dividend dedup fix |
| 16 | Fix CI/CD Pipeline | `45a1893` | YAML fix, all 4 CI jobs green, migration bug fix, rerun/delete simulation buttons |
| 17 | Broker Integration (Alpaca) | — | AlpacaBrokerAdapter in DI, broker status endpoint, alpaca-py dep |
| — | Fix: Workspace Excel Export | `9ff4544` | Orders scoped to position, Events tab export button |
| — | Fix: Dividend Excel Export | `8e9f65a` | Backend endpoint + multi-sheet workbook + frontend download |
| — | Fix: Orders/Trades Excel Export | `b7fbbde` | Real trades/orders data in trading Excel; API limits raised to 5000 |
| 20 | Analysis Enhancements | `51797af` | Overview tables real data, PerformanceChart vs market API, commission/dividend/guardrail charts |
| 20b | Optimization Config Management | — | PUT/DELETE/reset endpoints + edit/rerun/delete UI |
| 21 | Analytics Deep Enhancements | — | Date range, resolution, benchmarks, Excel export, event markers fix |
| 22 | JWT Authentication | — | User accounts, JWT tokens, protected routes, login page, tenant isolation |
| — | JWT Auth Polish | `9f0d85f`, `3734b17`, `33694a3`, `d0a862c` | tenant_id wiring, user footer, passlib→bcrypt, fake data removal |
| — | JWT Deploy & Tests | `3a95e23`, `6d02f2f`, `c6600d8`, `fdbd964` | .env JWT vars, smoke.sh auth, EC2 runbook, 14 auth integration tests |
| 23 | Schema & Endpoints | `e18d10f`, `cf7028a` | Alembic migrations for schema management; adjust + anchor endpoints for manual position management |
| 24 | Remove Dual Evaluation Paths | `8ba41d6`, `421b763`, `53cc1ea`, `fc65acc` | Pending order guard, dual-path fix, auth headers fix, orchestrator rewrite (−486 lines) |
| 25 | Audit Traceability Tool | `f10a158` | `scripts/audit_traceability.py` CLI; 28 integration tests; checks GAP-1 through GAP-4 |
| 26 | Real-time Data UI Indicators | — | `MarketDataBadge` component; freshness dot + source chip + elapsed timer; wired into OverviewTab, TradingTab, WorkspaceTopBar |
| 27 | Fly.io Migration | `0074885`–`5f6afb9` | Dockerfile, fly.toml, Neon DB, Cloudflare Pages frontend, CI/CD via flyctl; CORS + lint fixes |
