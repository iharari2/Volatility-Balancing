```markdown
# Volatility Balancing — PRD & GUI Lockup (v1.0)

**Doc owner:** Fintech Product Manager  
**Date:** 2025‑09‑28  
**Product area:** Web app (desktop‑first, responsive)  
**Vision alignment:** Empower semi‑passive investors to capture mean‑reversion on blue‑chip equities with transparent, compliant, low‑risk tooling.

---

## 1) Problem & Goals
**Problem.** Retail and pro‑sumer investors lack a coherent workspace to (a) manage a volatility‑balanced portfolio, (b) run/monitor 24×7 algorithmic execution, and (c) simulate/optimize strategies with explainability and data export for compliance and debugging.

**Primary goals**
- Create & manage portfolios containing positions (assets) + per‑position cash buffers & config.
- 24×7 Robotrade execution & monitoring with guardrails and pause/kill controls.
- Historical simulation (single position & multi‑asset portfolio) with configurable algorithms & constraints.
- Optimization incl. heatmaps to visualize parameter impact on KPIs.
- Analysis hub aggregating market, simulation, and live trade results + raw data export to Excel/CSV.

**Non‑goals (v1):** social features, options/derivatives, mobile‑only experience, broker onboarding flows beyond OAuth, custom scripting languages.

**Target users**
- **Prosumer investors** (hands‑on, data‑driven, $50k–$1M AUM).  
- **RIA/Family office analysts** (needs audit/export).  
- **Quant‑curious retail** (guided presets, safe defaults).

**Success metrics (12 weeks post‑launch)**
- TPA (time‑to‑productive action) \<= 30 min from first login.  
- \>= 60% users run \>= 1 simulation and create \>= 1 position in week 1.  
- \<= 0.5% trade job fatal errors/day; MTTR < 10 min.  
- Export adoption: \>= 40% of active users export at least once/month.  
- NPS \>= 40; Task‑success (create pos + start robotrade) \>= 85%.

---

## 2) Scope (MVP vs Next)
| Area | MVP (v1) | Next (v1.x) |
|---|---|---|
| Portfolio | Create/edit/delete portfolio; positions with cash link; per‑position config; P/L & risk snapshots | Multi‑currency, model portfolios, goal tracking |
| Trade (Robotrade) | Start/stop/pause; status; per‑position runtime metrics; alerts; broker connection | Multi‑broker routing, smart order types, paper/live switch |
| Simulation | Single/multi‑asset backtests; walk‑forward split; result tables & charts | Monte Carlo, custom factor inject, regime detection |
| Optimization | Grid/heatmap across 2–3 params; KPI goals (CAGR, Sharpe, MDD) | Bayesian opt, Pareto front, constraint solver |
| Analysis | Charts: equity curve, drawdown, exposure; Compare Sim vs Live; exports | Report templates, cohort analysis |
| Compliance | Audit trail, read‑only mode, GDPR export/delete | Policy engine, e‑sign risk ACK |

---

## 3) Information Architecture
- **Global:** Top nav tabs — *Portfolio*, *Trade*, *Simulation*, *Optimization*, *Analysis*, *Settings*.  
- **Left rail:** Contextual tree (Portfolios → Positions).  
- **Main content:** Data grids, charts, editors.  
- **Right panel (dockable):** Run console/logs/alerts.

---

## 4) Key Screens & Lockups (Low‑Fi)
(ASCII wireframes omitted for brevity — see original PRD)

---

## 5) Detailed Requirements
### 5.1 Portfolio & Positions
**Data fields**
- Portfolio: id, name, base currency, creation date, status, AUM, risk profile.
- Position: id, ticker, exchange, qty, basis, linked cash amount/ratio, config version, notes.
- Config per position: band %, ATR window, entry/exit thresholds, position sizing rule, max exposure %, max DD %, trading hours, fees model.

**Core actions**
- Create/Edit/Delete portfolio and position.  
- Link cash to a position: fixed $ or % of portfolio cash; auto‑rebalance toggle.  
- Versioned configs: save named presets, diff view, roll‑back.

**Acceptance criteria**
- Can create a portfolio with at least one position and cash link in < 2 min.  
- Config validation: hard ranges, semantic checks (e.g., exit must loosen than entry), warnings if constraints conflict.

---

### 5.2 Robotrade Execution & Monitoring
Controls, runtime metrics, resilience, alerts (see original PRD for detail).

---

### 5.3 Simulation
Inputs, engine, outputs, acceptance criteria (see original PRD).

---

### 5.4 Optimization (Heatmaps)
Grid search across 2–3 parameters with visualization and stability view.

---

### 5.5 Analysis & Explainability
Dashboards, explainability per trade, exports (CSV/XLSX/PNG/PDF).

---

## 6) UX Guidelines & Components
Design system: 8px spacing, accessible colors, 12‑col grid, dark/light themes.

---

## 7) Data, Privacy, and Compliance
GDPR compliance, audit logs, explainability, SSO/RBAC.

---

## 8) Telemetry & Observability
UX funnels, system metrics, status page.

---

## 9) Non‑Functional Requirements
Performance, availability, internationalization, browser support.

---

## 10) Release Plan (MVP → v1.1)
| Phase | Epic | Key Deliverables |
|---|---|---|
| Sprint 1–2 | Portfolio Core | CRUD, grid, position config schema, cash link, validation |
| Sprint 3–4 | Simulation Lab | Run engine integration, results views, exports |
| Sprint 5 | Optimization | Heatmap grid, top‑n picker, apply‑to‑config |
| Sprint 6 | Robotrade | Start/pause/stop, metrics tiles, log stream, alerts |
| Sprint 7 | Analysis | Comparison dashboards, explainability view, PDF/CSV/XLSX |
| Sprint 8 | Compliance & Settings | OAuth brokers, audit trail, GDPR tools |

---

## 11) Detailed UI Spec (Highlights)
- Portfolio list with extended market data, computed guardrails, and position totals.
- Position detail with OHLC, anchor price, dividend yield/value, H/L triggers, performance since start.
- Transactions table (price, qty, $value, cash, commission, slippage, resulting balances).

---

## 12) API & Data Contracts (UI Expectations)
- Market Data: `GET /api/market/ohlc`, `GET /api/market/dividends`.  
- Transactions: `GET/POST /api/positions/{id}/transactions`.  
- Computed metrics: `GET /api/positions/{id}/metrics`.  
- Plus simulation, optimization, robotrade, exports, audit (see original PRD).

---

## 13) Acceptance Test Scenarios
1. Create portfolio with 2 positions and cash links → validate → save.  
2. Run simulation → export trades.  
3. Heatmap optimization → apply best params.  
4. Start robotrade → monitor metrics/logs → pause → resume → stop.  
5. Compare Sim vs Live → export explainability PDF.

---

## 14) Risks & Mitigations
- Data drift, over‑optimization, execution risk, compliance.

---

## 15) AI Dev Tool Blocks
- Component inventory (AppShell, PortfolioList, PositionDetail, RobotradeConsole, SimulationLab, Optimization, AnalysisHub, Settings).  
- Param dictionary, event tracking IDs, formula definitions for guardrails, trigger prices, totals.

---

## 16) Next Steps
- Validate with pilot users.  
- Break down into component tickets and API stubs.  
- Produce high‑fidelity designs.
```

