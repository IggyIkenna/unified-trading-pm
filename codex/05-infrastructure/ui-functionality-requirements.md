---
doc_type: codex-ssot
title: UI Functionality Requirements — Unified Trading System
summary:
  SUPERSEDED by ui-architecture.md; retained for UI screens/features/user-roles detail — active deployment-ui
  functionality plus the archived split-UI domain reference (onboarding/strategy/settlement/live-health/etc.) and v0
  consolidation guidance.
status: superseded
nature: ssot
asset_group: [meta]
stage: [meta]
repos:
  [
    alerting-service,
    batch-live-reconciliation-service,
    client-reporting-api,
    deployment-api,
    deployment-ui,
    execution-service,
  ]
scope: [engineer, admin]
tags: [ui, infrastructure, superseded, consolidation]
related: [/codex/05-infrastructure/ui-architecture.md, /codex/05-infrastructure/ui-dependency-matrix.md]
created: 2026-03-27
authoritative_for: []
referenced_by:
  [
    /codex/05-infrastructure/ui-architecture.md,
    /codex/05-infrastructure/ui-dependency-matrix.md,
    /codex/06-coding-standards/ui-testing-layers.md,
    codex/DEPRECATED_UIS_NOTICE.md,
  ]
owner:
last_reviewed: 2026-05-13
code_refs:
superseded_by: ui-architecture.md
---

> **🟡 SUPERSEDED 2026-05-13 by [`ui-architecture.md`](./ui-architecture.md)**
>
> This doc remains for screens / features / user roles / consolidation guidance detail. New readers should start at
> `ui-architecture.md` for the navigation index. Full content merge into `ui-architecture.md` tracked in
> [`codex_doc_currency_and_consolidation_post_cutover_2026_05_12.md`](../../plans/archive/codex_doc_currency_and_consolidation_post_cutover_2026_05_12.md)
> Sweep 2 (UI-17 finding).

# UI Functionality Requirements — Unified Trading System

**Purpose:** Reference for UI capabilities and how they map to APIs and the Python pipeline. For **current** product
work, implement features in **`unified-trading-system-ui`** and **`deployment-ui`** only; split UI repos listed in
**workspace-root `archive/README.md`** are **ARCHIVED — reference only** (not in `workspace-manifest.json`
repositories).

**Last Updated:** 2026-03-24 **Related:** `ui-dependency-matrix.md` (API wiring, ports), `workspace-manifest.json` (repo
registry), `unified-trading-pm/scripts/dev/ui-api-mapping.json` (active UI/API stacks)

---

## Executive Summary

The **active** product surface is **two UIs**: **`unified-trading-system-ui`** (consolidated trading, reporting, admin,
and domain flows) and **`deployment-ui`** (deployment orchestration with `deployment-api`). Former split UIs
(`strategy-ui`, `client-reporting-ui`, `live-health-monitor-ui`, etc.) and related APIs (`execution-results-api`,
`batch-audit-api`, `config-api`, …) live under **`archive/`** — see **`archive/README.md`**.

This document still defines:

1. **What each UI domain covered** — screens, features, user workflows (active + archived reference)
2. **Which APIs backed each domain** — endpoint mapping (verify live routes against manifest-listed repos)
3. **User roles and auth** — who uses what
4. **Backend services** — the Python pipeline that feeds data
5. **Consolidation notes** — historical v0 guidance; prefer extending `unified-trading-system-ui` for new work

---

## 1. UI Domain Overview

### 1.1 Active (manifest — implement here)

| Domain            | UI Repo                     | Status     | Primary User         | Purpose                                                              | Auth         |
| ----------------- | --------------------------- | ---------- | -------------------- | -------------------------------------------------------------------- | ------------ |
| **Trading / Ops** | `unified-trading-system-ui` | **active** | Trader / Ops / Admin | Consolidated product surface (multi-stack per `ui-api-mapping.json`) | Varies       |
| **Deployment**    | `deployment-ui`             | **active** | DevOps / Ops         | Deploy services, monitor builds, config                              | Google OAuth |

### 1.2 ARCHIVED — reference only (`archive/README.md`)

| Domain                  | UI Repo                | Status   | Primary User     | Purpose                                               | Auth                 |
| ----------------------- | ---------------------- | -------- | ---------------- | ----------------------------------------------------- | -------------------- |
| **Onboarding**          | onboarding-ui          | archived | Trader / Admin   | Clients, strategies, venues, API keys, risk config    | Google OAuth (admin) |
| **Execution Analytics** | execution-analytics-ui | archived | Quant / Trader   | Backtest runs, results, analysis                      | None (internal)      |
| **Strategy**            | strategy-ui            | archived | Quant / Trader   | Strategy definitions, live trading, backtest, configs | None (internal)      |
| **Settlement**          | settlement-ui          | archived | Ops / Finance    | Positions, invoices, reports, T+1 settlement          | None (internal)      |
| **Live Health**         | live-health-monitor-ui | archived | Trader           | Live positions, P&L, health, alerts, kill switch      | None (internal)      |
| **Logs**                | logs-dashboard-ui      | archived | Engineer / Ops   | Log stream, events, alerts, CI/CD history             | None (internal)      |
| **ML Training**         | ml-training-ui         | archived | Data Scientist   | Experiments, model registry, deployment status        | Google OAuth         |
| **Trading Analytics**   | trading-analytics-ui   | archived | Trader / Ops     | Order book, latency, recon, manual order entry        | None (internal)      |
| **Batch Audit**         | batch-audit-ui         | archived | Ops / Compliance | Batch jobs, audit trail, data completeness            | None (internal)      |
| **Client Reporting**    | client-reporting-ui    | archived | Account Manager  | Client reports, performance, P&L                      | Per-client JWT       |
| **User Management**     | user-management-ui     | archived | Admin            | User lifecycle (onboard/modify/offboard)              | Google OAuth (admin) |
| **Admin**               | unified-admin-ui       | archived | Admin            | Admin portal — config-api era                         | Google OAuth         |

---

## 2. Detailed Functionality by Domain

Sections **2.2 onward** describe **archived** split UIs (see `archive/README.md`). They are retained for diffing and
migration reference; **do not treat them as current delivery targets.**

### 2.1 Deployment (deployment-ui) — **active**

**Who:** DevOps, deployment engineers **API:** `deployment-api` (port per
`unified-trading-pm/scripts/dev/ui-api-mapping.json`, typically 8004)

| Screen         | Route             | Functionality                                                                                                 |
| -------------- | ----------------- | ------------------------------------------------------------------------------------------------------------- |
| Deploy         | `/deploy`         | Submit deployment — select service, mode (batch/live), image version, feature branch, date range, asset scope |
| Data Status    | `/data-status`    | GCS data readiness — which files exist for date range and scope                                               |
| Builds         | `/builds`         | Cloud Build history — trigger status, logs link, commit SHA, duration                                         |
| Readiness      | `/readiness`      | Service readiness probe — all services healthy before live deploy                                             |
| Service Status | `/service-status` | Cloud Run status — deployed version, instance count, health per service                                       |
| Config         | `/config`         | Active deployment config viewer                                                                               |
| History        | `/history`        | Past deployments — version, status, triggered-by, timestamps                                                  |
| Overview       | `/overview`       | Workspace-level deployment tracking, epics                                                                    |

**Key actions:** `POST /cloud-builds/trigger` (OAuth-gated), `GET /service-status`, `GET /data-status`

---

### 2.2 Onboarding (onboarding-ui) — **ARCHIVED — reference only**

**Who:** Traders, admins, onboarding team **API:** `config-api` (**archived** repo — see `archive/README.md`)

| Screen          | Route             | Functionality                                                   |
| --------------- | ----------------- | --------------------------------------------------------------- |
| Clients         | `/clients`        | Create/manage clients, capital allocation, risk limits          |
| Client Detail   | `/clients/:id`    | Per-client config, linked strategies, account breakdown         |
| Strategies      | `/strategies`     | Configure strategy definitions, link to clients                 |
| Strategy Detail | `/strategies/:id` | Parameters, performance summary, deployment state               |
| Venues          | `/venues`         | Add exchanges/brokers, test connectivity, map instruments       |
| Venue Detail    | `/venues/:id`     | Connection config, instrument mappings, API credential status   |
| API Keys        | `/api-keys`       | Store and rotate encrypted API keys per venue                   |
| Risk            | `/risk`           | System-wide risk thresholds, position limits, drawdown controls |
| Audit Log       | `/audit`          | Config change history with diffs — who changed what, when       |

**Key actions:** CRUD on clients, strategies, venues, API keys; Secret Manager integration for credentials

---

### 2.3 Execution Analytics (execution-analytics-ui) — **ARCHIVED — reference only**

**Who:** Quants, traders **API:** `execution-results-api` (**archived** — see `archive/README.md`)

| Screen           | Route           | Functionality                                                     |
| ---------------- | --------------- | ----------------------------------------------------------------- |
| Run Backtest     | `/run-backtest` | Submit backtest job — date range, parameter overrides             |
| Results          | `/results`      | Browse completed backtest results for all strategies              |
| Grid Results     | `/grid-results` | Multi-parameter sweep results — compare across the parameter grid |
| Analysis         | `/analysis`     | Statistical analysis — Sharpe, drawdown, win rate                 |
| Deep Dive        | `/deep-dive`    | Trade-level breakdown for any backtest run                        |
| Compare          | `/compare`      | Side-by-side comparison of two or more runs                       |
| Config Browser   | `/configs`      | Browse and view strategy config files                             |
| Config Generator | `/generate`     | Generate new strategy configs via guided wizard                   |
| Instruments      | `/instruments`  | Instrument catalogue with metadata search and filter              |
| Availability     | `/availability` | Data availability matrix per instrument and date range            |

**Key endpoints:** `/api/v1/results`, `/api/v1/analysis`, `/api/v1/backtest`, `/api/v1/validate`, `/api/v1/config`,
`/api/v1/data`, `/api/v1/fills`, SSE fill stream

---

### 2.4 Strategy (strategy-ui) — **ARCHIVED — reference only**

**Who:** Quants, traders **API:** `execution-results-api` (**archived** — see `archive/README.md`)

| Screen           | Route           | Functionality                                                |
| ---------------- | --------------- | ------------------------------------------------------------ |
| All Strategies   | `/strategies`   | List all strategy definitions with status, mode, key metrics |
| Live Trading     | `/live`         | Real-time view — positions, risk, alerts                     |
| Run Backtest     | `/run-backtest` | Submit backtest job                                          |
| Results          | `/results`      | Browse backtest results                                      |
| Grid Results     | `/grid-results` | Multi-parameter sweep results                                |
| Analysis         | `/analysis`     | Statistical analysis — Sharpe, drawdown, win rate            |
| Deep Dive        | `/deep-dive`    | Trade-level breakdown                                        |
| Compare          | `/compare`      | Side-by-side comparison                                      |
| Config Browser   | `/configs`      | Browse strategy config files                                 |
| Config Generator | `/generate`     | Generate new configs                                         |
| Instruments      | `/instruments`  | Instrument catalogue                                         |
| Availability     | `/availability` | Data availability matrix                                     |

**Note:** Strategy UI shares many execution-analytics endpoints; backtest runs use a separate local Python process
(port 5001) for job execution.

---

### 2.5 Settlement (settlement-ui) — **ARCHIVED — reference only**

**Who:** Ops, finance, reconciliation team **API:** `trading-analytics-api` (**archived** — see `archive/README.md`) —
historic `/settlement/*` and `/settlements/*` routes

| Screen      | Route          | Functionality                                                              |
| ----------- | -------------- | -------------------------------------------------------------------------- |
| Positions   | `/positions`   | Settled and open positions with realised P&L, by client/strategy/account   |
| Invoices    | `/invoices`    | Fee invoices and cash flow statements per client and period                |
| Reports     | `/reports`     | Settlement reports — downloadable summaries for date range                 |
| Settlements | `/settlements` | Settlement lifecycle — expected vs actual fills, breaks, resolution status |

---

### 2.6 Live Health Monitor (live-health-monitor-ui) — **ARCHIVED — reference only**

**Who:** Traders (live trading desk) **API:** `execution-results-api` (**archived**); manual trade instructions →
execution-service (historic env patterns)

| Screen        | Route        | Functionality                                                                |
| ------------- | ------------ | ---------------------------------------------------------------------------- |
| Dashboard     | `/dashboard` | Real-time positions, unrealised P&L, live risk metrics, stat cards           |
| System Health | `/health`    | Per-service health — connected/degraded/down, data freshness per feed        |
| Alerts        | `/alerts`    | Active and historical alerts — risk breaches, stale data, kill switch events |

**Special:** Live streaming status indicator (green dot, pulsing) reflecting data feed connection state; kill switch
controls; manual trade entry form

---

### 2.7 Logs Dashboard (logs-dashboard-ui) — **ARCHIVED — reference only**

**Who:** Engineers, operators **API:** `batch-audit-api` (**archived** — see `archive/README.md`)

| Screen     | Route       | Functionality                                                                     |
| ---------- | ----------- | --------------------------------------------------------------------------------- |
| Log Stream | `/logs`     | Live and historical log stream — filter by service, severity, time range, keyword |
| Log Detail | `/logs/:id` | Full detail — context, stack trace, correlation ID                                |
| Events     | `/events`   | System event feed — trade lifecycle, config changes, deployment events            |
| Alerts     | `/alerts`   | Alert history — triggered rules, delivery status, acknowledgement                 |
| CI/CD      | `/cicd`     | Cloud Build and GitHub Actions run history — build status, logs, trigger context  |

---

### 2.8 ML Training (ml-training-ui) — **ARCHIVED — reference only**

**Who:** Data scientists, quants **API:** `ml-training-api` (**archived** — see `archive/README.md`)

| Screen            | Route              | Functionality                                                                       |
| ----------------- | ------------------ | ----------------------------------------------------------------------------------- |
| Experiments       | `/experiments`     | List all training runs — status, config, metrics summary                            |
| Experiment Detail | `/experiments/:id` | Full detail — hyperparameters, training curves, evaluation metrics                  |
| Models            | `/models`          | Model registry — all trained model versions, performance metrics, deployment status |

---

### 2.9 Trading Analytics (trading-analytics-ui) — **ARCHIVED — reference only**

**Who:** Traders, ops **API:** `trading-analytics-api` (**archived** — see `archive/README.md`)

| Screen            | Route                     | Functionality                                                                 |
| ----------------- | ------------------------- | ----------------------------------------------------------------------------- |
| Trading Desk      | `/trading-desk`           | Live trade feed, P&L per trade, manual order entry form                       |
| Order Book        | `/orderbook`              | Live and snapshot order book depth — bid/ask levels, spread, liquidity viz    |
| Latency Analytics | `/latency`                | Execution latency — P50/P95/P99 per venue, spike detection, historical trends |
| Reconciliation    | `/recon`                  | Reconciliation run list — date-indexed batch recon jobs                       |
| Recon Detail      | `/recon/:date`            | Per-date recon — matched trades, unmatched breaks, tolerances                 |
| Deviation Drill   | `/recon/:date/deviations` | Drill into specific deviations                                                |

---

### 2.10 Batch Audit (batch-audit-ui) — **ARCHIVED — reference only**

**Who:** Ops, compliance **API:** `batch-audit-api` (**archived** — see `archive/README.md`)

| Screen            | Route               | Functionality                                                                                  |
| ----------------- | ------------------- | ---------------------------------------------------------------------------------------------- |
| Batch Jobs        | `/jobs`             | Job list — all batch runs with status (COMPLETED/RUNNING/FAILED/PENDING), timing, triggered-by |
| Job Detail        | `/jobs/:id`         | Full detail — step-by-step event trail, logs, input/output paths, error details                |
| Audit Trail       | `/audit/trail`      | Filterable event log — search by date range, job type, status, correlation ID                  |
| Data Completeness | `/audit/health`     | GCS path presence matrix — which instruments/dates have data, which are missing                |
| Compliance        | `/audit/compliance` | Compliance violation tracker — severity-classified rule breaches with status and resolution    |

**Reference UI:** batch-audit-ui is the reference for visual polish. Verify shared ui-kit components here first.

---

### 2.11 Client Reporting (client-reporting-ui) — **ARCHIVED — reference only**

**Who:** Account managers, client-facing ops **API:** **`client-reporting-api` remains active**; standalone
`client-reporting-ui` is **archived**. Client reporting UX is integrated into **`unified-trading-system-ui`** per
`ui-api-mapping.json`.

| Screen          | Route          | Functionality                                                                                  |
| --------------- | -------------- | ---------------------------------------------------------------------------------------------- |
| Reports         | `/reports`     | Browse generated reports — filter by client, period, report type; download or preview          |
| Performance     | `/performance` | Portfolio performance — returns chart, drawdown, Sharpe ratio, benchmark comparison per client |
| Generate Report | `/generate`    | Trigger new report generation — select client, period, report type, output format              |

**Auth:** Per-client JWT; client-reporting-api aggregates PnL, positions, fills for external clients

---

### 2.12 User Management (user-management-ui) — **ARCHIVED — reference only**

**Who:** Admins **API:** User lifecycle is **`auth-api` + `unified-trading-system-ui`** in the active workspace;
standalone `user-management-ui` is **archived** (see `archive/README.md` and `ui-api-mapping.json` `user-management`
stack).

| Screen      | Route        | Functionality                        |
| ----------- | ------------ | ------------------------------------ |
| Users       | `/users`     | User list; onboard, modify, offboard |
| User Detail | `/users/:id` | Per-user config, permissions, audit  |

**Note:** Admin UI; OAuth admin auth. Mock mode uses client-side fetch intercepts.

---

## 3. Shared UI Components and Auth

| Package                       | Status     | Purpose                                                                                          |
| ----------------------------- | ---------- | ------------------------------------------------------------------------------------------------ |
| **unified-trading-system-ui** | **active** | In-repo components, auth, and layouts — canonical shared surface                                 |
| **unified-trading-ui-kit**    | archived   | Historic shared package — see `archive/README.md`                                                |
| **unified-trading-ui-auth**   | archived   | Historic auth package — see `archive/README.md`                                                  |
| **unified-admin-ui**          | archived   | Admin monorepo era — see `archive/README.md`                                                     |
| **Embedded deployment panel** | reference  | Legacy pattern from split UIs; align new work with `deployment-ui` / `unified-trading-system-ui` |

---

## 4. API → UI Mapping (Consolidated)

Ports: use **`ui-api-mapping.json`** as SSOT; table ports are illustrative.

| API Service           | Port (typical) | Status     | Serves / served UIs                                                               | Key Routes                                                                                                                                         |
| --------------------- | -------------- | ---------- | --------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| deployment-api        | 8004           | **active** | **deployment-ui**                                                                 | `/deployments`, `/cloud-builds/trigger`, `/services`, `/service-status`, `/data-status`, `/config`, `/checklist`, `/log-analysis`, `/infra/health` |
| unified-trading-api   | 8030           | **active** | **unified-trading-system-ui**                                                     | Domain routes per repo                                                                                                                             |
| auth-api              | 8200           | **active** | **unified-trading-system-ui** (admin / user flows)                                | JWT, OAuth, provisioning                                                                                                                           |
| client-reporting-api  | 8014           | **active** | **unified-trading-system-ui** (client reporting stack)                            | `/reports`, `/clients`, `/portfolio`                                                                                                               |
| config-api            | —              | archived   | onboarding-ui, settlement-ui, strategy-ui, unified-admin-ui (**archived** UIs)    | Historic config CRUD — see `archive/README.md`                                                                                                     |
| execution-results-api | —              | archived   | trading-analytics-ui, live-health-monitor-ui, execution-analytics-ui, strategy-ui | Historic analytics — see `archive/README.md`                                                                                                       |
| ml-training-api       | —              | archived   | ml-training-ui                                                                    | See `archive/README.md`                                                                                                                            |
| trading-analytics-api | —              | archived   | trading-analytics-ui, settlement-ui                                               | See `archive/README.md`                                                                                                                            |
| batch-audit-api       | —              | archived   | batch-audit-ui, logs-dashboard-ui                                                 | See `archive/README.md`                                                                                                                            |
| ml-inference-api      | —              | archived   | (historic)                                                                        | See `archive/README.md`                                                                                                                            |

---

## 5. Backend Services (Python Pipeline)

The UIs consume data produced by this 7-layer pipeline:

| Layer                     | Services                                                                                                                                                                                                                              | Output                                 |
| ------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------- |
| L1 — Reference Data       | instruments-service, features-service (calendar family)                                                                                                                                                                               | Instrument universe, trading calendars |
| L2 — Raw Market Data      | market-tick-data-service                                                                                                                                                                                                              | Raw ticks                              |
| L3 — Processing           | market-data-processing-service                                                                                                                                                                                                        | OHLCV candles                          |
| L4 — Features             | features-service (delta-one family), features-service (volatility family), features-service (onchain family), features-service (cross-instrument family), features-service (multi-timeframe family), features-service (sports family) | Feature vectors                        |
| L5 — ML                   | ml-training-service, ml-inference-service                                                                                                                                                                                             | Trained models, predictions            |
| L6 — Strategy & Execution | strategy-service, execution-service                                                                                                                                                                                                   | Orders, fills                          |
| L7 — Post-Trade           | position-balance-monitor-service, risk-and-exposure-service, pnl-attribution-service                                                                                                                                                  | P&L, risk metrics, position state      |

**Additional services:** batch-live-reconciliation-service (T+1 orchestrator), alerting-service (cross-domain alerts).

**APIs (active manifest subset):** `deployment-api`, `unified-trading-api`, `auth-api`, `client-reporting-api`,
`batch-audit-api`, `config-api`, `trading-analytics-api`, `ml-training-api`, `ml-inference-api`, …) — see
**`archive/README.md`**.

---

## 6. User Roles and Auth Summary

| Role                     | Active UIs                                           | Auth / notes                                                        |
| ------------------------ | ---------------------------------------------------- | ------------------------------------------------------------------- |
| **DevOps / Ops**         | deployment-ui, unified-trading-system-ui (as needed) | Google OAuth for deployment writes; see `deployment-api`            |
| **Trader / Quant / Ops** | unified-trading-system-ui                            | Varies by route (internal JWT / OAuth per `auth-api` and UI)        |
| **Account Manager**      | unified-trading-system-ui                            | Per-client JWT where client reporting is exposed                    |
| **Admin**                | unified-trading-system-ui                            | Admin flows via `auth-api` + UI (standalone admin UIs **archived**) |

**ARCHIVED — reference only:** Former role→UI matrix used split UIs (`batch-audit-ui`, `strategy-ui`, `onboarding-ui`,
…) — see `archive/README.md`.

---

## 7. Current Wired Status (from ui-dependency-matrix)

| UI Repo                   | Status     | Notes                                                     |
| ------------------------- | ---------- | --------------------------------------------------------- |
| unified-trading-system-ui | **active** | See repo docs, `dev-tiers.sh`, and tier-zero testing docs |
| deployment-ui             | **active** | Pair with `deployment-api` per `ui-api-mapping.json`      |

**ARCHIVED — reference only:** Split UI “wired status” rows applied to repos under **`archive/`** only; they are not
current delivery targets. See **`archive/README.md`**.

---

## 8. Recommendations for Vercel v0 App Consolidation

**Current direction:** Extend **`unified-trading-system-ui`** (and **`deployment-ui`** for ops) rather than reviving
split UIs in `archive/`.

### 8.1 Suggested App Structure

For greenfield consolidation (historical note — largely superseded by `unified-trading-system-ui`):

1. **Admin / Ops Hub** — use **deployment-ui** + admin routes in **unified-trading-system-ui** (archived: onboarding-ui,
   user-management-ui, batch-audit-ui, logs-dashboard-ui)
2. **Trading Hub** — **unified-trading-system-ui** (archived: strategy-ui, execution-analytics-ui,
   live-health-monitor-ui, trading-analytics-ui, settlement-ui)
3. **ML Hub** — integrate into **unified-trading-system-ui** or future manifest-listed UI (archived: ml-training-ui)
4. **Client Hub** — **unified-trading-system-ui** client reporting stack + **client-reporting-api** (archived:
   standalone client-reporting-ui)

### 8.2 Must-Have Features

- **Single sign-on** — Google OAuth / JWT via **`auth-api`** and patterns in **unified-trading-system-ui** (historic:
  unified-trading-ui-auth **archived**)
- **Deployment** — **deployment-ui** + `deployment-api` for service rollouts
- **Mock mode** — `VITE_MOCK_API=true` (and related flags) per active UI docs
- **Port mapping** — **`unified-trading-pm/scripts/dev/ui-api-mapping.json`** (SSOT)

### 8.3 API Endpoints to Implement First (active workspace)

1. **unified-trading-api** — domain routes consumed by **unified-trading-system-ui**
2. **auth-api** — login, tokens, admin provisioning
3. **deployment-api** — `/service-status`, `/data-status`, `/cloud-builds/trigger`, `/services`
4. **client-reporting-api** — `/reports`, `/clients`, `/portfolio` (as wired in UI)

**ARCHIVED — reference only:** Historic priority list included **execution-results-api**, **trading-analytics-api**,
**batch-audit-api**, **config-api** — see **`archive/README.md`**.

### 8.4 Gaps to Address

- **Surface coverage** — track remaining feature gaps inside **unified-trading-system-ui** against sections 2.x
  (archived reference) and product backlog
- **ml-inference-service / API** — Python services may remain active while standalone **ml-inference-api** repo is
  **archived**; align docs with `workspace-manifest.json`
- **Port mapping** — **SSOT:** `ui-api-mapping.json`; ignore historic 8001–8003-only docs unless reading **archived**
  trees

---

## 9. References

- **Archived repos (not in manifest):** workspace-root **`archive/README.md`**
- **UI Dependency Matrix:** `05-infrastructure/ui-dependency-matrix.md`
- **Port mapping:** `unified-trading-pm/scripts/dev/ui-api-mapping.json`
- **Repo registry:** `unified-trading-pm/workspace-manifest.json`
- **Pipeline layers:** `04-architecture/runtime-deployment-topology.md`
- **Runtime topology:** `unified-trading-pm/configs/runtime-topology.yaml`
- **SSOT index:** `00-SSOT-INDEX.md`
