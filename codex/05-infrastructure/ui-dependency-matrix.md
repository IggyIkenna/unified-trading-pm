---
doc_type: codex-ssot
title: UI Dependency Matrix
summary:
  SUPERSEDED by ui-architecture.md; retained for UI→API wiring detail — the active deployment-ui↔deployment-api
  dependency, the archived split-UI/API reference tables, the OAuth-gated deployment-trigger flow, and local-dev port
  assignments.
status: superseded
nature: ssot
asset_group: [meta]
stage: [meta]
repos:
  [
    client-reporting-api,
    deployment-api,
    deployment-service,
    deployment-ui,
    system-integration-tests,
    unified-trading-api,
  ]
scope: [engineer, admin]
tags: [ui, infrastructure, deployment, superseded, api]
related: [/codex/05-infrastructure/ui-architecture.md, /codex/05-infrastructure/ui-functionality-requirements.md]
created: 2026-03-27
authoritative_for: []
referenced_by:
  [
    /codex/05-infrastructure/ui-architecture.md,
    /codex/05-infrastructure/ui-functionality-requirements.md,
    /codex/06-coding-standards/ui-service-separation.md,
  ]
owner:
last_reviewed: 2026-05-13
code_refs:
superseded_by: ui-architecture.md
---

> **🟡 SUPERSEDED 2026-05-13 by [`ui-architecture.md`](./ui-architecture.md)**
>
> This doc remains for API wiring / ports / repo registry / dependency matrix detail. New readers should start at
> `ui-architecture.md` for the navigation index. Full content merge into `ui-architecture.md` tracked in
> [`codex_doc_currency_and_consolidation_post_cutover_2026_05_12.md`](../../plans/archive/codex_doc_currency_and_consolidation_post_cutover_2026_05_12.md)
> Sweep 2 (UI-17 finding).

# UI Dependency Matrix

**Last Updated:** 2026-03-24 **SSOT for repo registry:** `unified-trading-pm/workspace-manifest.json` **SSOT for API
routes:** `deployment-api/api/routes/` (extracted from UTD V3 — see task `deployment-v3-four-way-split`)

**Related:** `ui-functionality-requirements.md` — detailed screens, features, user roles, and v0 consolidation guidance.

## Active product UIs (current workspace)

The **active** product surface is **`unified-trading-system-ui`** (primary trading and operations) plus
**`deployment-ui`** (deployment orchestration with `deployment-api`). Port and API pairings are defined in
`unified-trading-pm/scripts/dev/ui-api-mapping.json`.

**ARCHIVED — reference only:** Split UIs (`strategy-ui`, `live-health-monitor-ui`, `batch-audit-ui`,
`client-reporting-ui`, etc.), archived APIs (`execution-results-api`, `batch-audit-api`, `config-api`, …), and related
repos are listed in **workspace-root `archive/README.md`** — they are **not** in `workspace-manifest.json`
`repositories`. The tables below retain historical wiring notes; treat rows marked **archived** as read-only reference
when diffing old code.

---

## UI → API Service Dependencies

| UI Repo         | Status     | Primary API(s)                   | OAuth Required         | Dev Port(s) | Key Functionality                                                                              |
| --------------- | ---------- | -------------------------------- | ---------------------- | ----------- | ---------------------------------------------------------------------------------------------- |
| `deployment-ui` | **active** | `deployment-api` (UTDV3 FastAPI) | **Yes** (Google OAuth) | 5183        | Cloud Build triggers, service restarts, deployment status, shard management, config management |

### ARCHIVED — reference only (see `archive/README.md`)

| UI Repo                  | Status   | Primary API(s)                                                   | OAuth Required            | Dev Port(s) | Key Functionality                                                            |
| ------------------------ | -------- | ---------------------------------------------------------------- | ------------------------- | ----------- | ---------------------------------------------------------------------------- |
| `live-health-monitor-ui` | archived | `deployment-api` (`/service-status` routes)                      | No (read-only)            | (historic)  | Real-time service health, uptime, manual trading controls, SSE health stream |
| `batch-audit-ui`         | archived | `deployment-api` (`/data-status`, `/checklist`, `/log-analysis`) | No (read-only)            | (historic)  | Batch job status, audit logs, checklist compliance                           |
| `logs-dashboard-ui`      | archived | `deployment-api` (`/log-analysis`)                               | No (read-only)            | (historic)  | Log streaming, error analysis, deployment history                            |
| `ml-training-ui`         | archived | `deployment-api` (`/deployments`, ML routes)                     | **Yes** (model push)      | (historic)  | ML model deployment, versioning, A/B configs                                 |
| `trading-analytics-ui`   | archived | `execution-results-api`                                          | No                        | (historic)  | P&L attribution, Sharpe ratio, win rate, trade history, backtest analytics   |
| `strategy-ui`            | archived | `execution-results-api`                                          | No                        | (historic)  | Strategy performance, live positions, risk metrics                           |
| `execution-analytics-ui` | archived | `execution-results-api`                                          | No                        | (historic)  | Backtest run management, results browsing, report generation                 |
| `settlement-ui`          | archived | `execution-results-api`                                          | No                        | (historic)  | Settlement data, T+1 reconciliation, execution records                       |
| `client-reporting-ui`    | archived | `client-reporting-api`                                           | **Yes** (per-client auth) | (historic)  | Client P&L reports, portfolio summaries, custom report export                |
| `onboarding-ui`          | archived | `deployment-api` (`/config`, `/capabilities`) + Secret Manager   | **Yes** (admin)           | (historic)  | New client onboarding, API key setup, credential provisioning                |

---

## API Service Endpoints

**Active APIs** (representative; full list: `workspace-manifest.json`, `ui-api-mapping.json`): `deployment-api`,

| API Service                 | Repo                                                             | Status     | Type          | Key Routes                                                                                                                                                                    | OAuth                                       | Cloud Run URL pattern                          |
| --------------------------- | ---------------------------------------------------------------- | ---------- | ------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------- | ---------------------------------------------- |
| Deployment Orchestrator API | `deployment-api` (standalone repo, imports `deployment-service`) | **active** | `api-service` | `/deployments`, `/cloud-builds/trigger`, `/services`, `/service-status`, `/data-status`, `/config`, `/checklist`, `/capabilities`, `/log-analysis`, `/infra/health` (Layer 2) | `GoogleOAuthMiddleware` on all write routes | `https://deployment-api-<hash>-uc.a.run.app`   |
| Unified Trading API         | `unified-trading-api`                                            | **active** | `api-service` | Domain routes per repo (consolidated trading surface for `unified-trading-system-ui`)                                                                                         | Varies                                      | Per Cloud Run deployment                       |
| Auth API                    | `auth-api`                                                       | **active** | `api-service` | JWT, OAuth exchange, provisioning                                                                                                                                             | Varies                                      | Per Cloud Run deployment                       |
| Client Reporting Service    | `client-reporting-api`                                           | **active** | `api-service` | `/reports`, `/clients`, `/portfolio`                                                                                                                                          | Per-client JWT                              | `https://client-reporting-<hash>-uc.a.run.app` |
| Execution Results API       | `execution-results-api`                                          | archived   | `api-service` | `/executions`, `/backtests`, `/analytics`, `/reports`                                                                                                                         | None (internal)                             | (historic — see `archive/README.md`)           |

---

## Deployment Trigger Flow (OAuth-Gated)

```
User (Google account in allowed domain)
  │
  ▼
deployment-ui  ── HTTPS POST /cloud-builds/trigger ──►  deployment-api
                                                              │
                                                    GoogleOAuthMiddleware
                                                    (unified_trading_services)
                                                              │
                                                    allowed_domains check
                                                              │
                                                              ▼
                                                    Cloud Build API (GCP)
                                                              │
                                                              ▼
                                                    Cloud Run service restart
```

**OAuth gate is in:** `deployment-api/api/auth_middleware.py` (via `GoogleOAuthMiddleware` from
`unified_trading_services`) **Allowed domains config:** `deployment-api/api/settings.py` **Cloud Build trigger route:**
`deployment-api/api/routes/cloud_builds.py` — `POST /trigger` **Service restart route:**
`deployment-api/api/routes/deployments.py` — `POST /deployments` **Infra health route:**
`deployment-api/api/routes/infra.py` — `GET /infra/health` (Layer 2 verification)

Any UI can call the deployment trigger endpoint. The OAuth middleware enforces authentication. This is the ONLY path for
production restarts — direct Cloud Build calls are blocked in production.

**Post-deploy validation flow:**

1. `POST /cloud-builds/trigger` → deploy service
2. `GET /infra/health` → Layer 2 (infra verify) must pass
3. Trigger `system-integration-tests` Layer 3a (smoke) → must pass
4. Trigger `system-integration-tests` Layer 3b (full E2E) → marks deployment "healthy"

See SSOT: `06-coding-standards/integration-testing-layers.md`

---

## Local Development Setup

**Active:** Use `unified-trading-system-ui/scripts/dev-tiers.sh` and
`unified-trading-pm/scripts/dev/ui-api-mapping.json` for ports. **Archived** split UIs under `archive/` used historic
ports below for reference only.

Each active UI uses a `.env.local` file to point to local API instances. Copy from `.env.local.example` in each UI repo.

### Port Assignments (local dev)

| Port       | Service                                                              |
| ---------- | -------------------------------------------------------------------- |
| 8004       | `deployment-api` (FastAPI; see repo for module path)                 |
| 8014       | `client-reporting-api`                                               |
| 8030       | `unified-trading-api`                                                |
| 8200       | `auth-api`                                                           |
| (historic) | `execution-results-api` — **archived** repo; see `archive/README.md` |

### `.env.local` template (deployment-ui → deployment-api)

```env
# deployment-ui — use port from ui-api-mapping.json (e.g. 8004)
VITE_API_URL=http://localhost:8004
VITE_OAUTH_CLIENT_ID=<google-oauth-client-id>
VITE_OAUTH_DOMAIN=<your-allowed-domain.com>
VITE_ENV=local
```

### `.env.local` template (unified-trading-system-ui)

Follow `unified-trading-system-ui/.env.example` and `ui-api-mapping.json` stacks (`unified-trading`, `deployment`,
`client-reporting`, `user-management`).

### ARCHIVED — reference only (split UIs in `archive/`)

Historic templates when those repos lived at workspace root:

```env
# Archived UIs calling deployment-api (ports were often 8001 in old docs)
# VITE_API_URL=http://localhost:<port-from-historic-doc>

# Archived UIs calling execution-results-api (repo archived — see archive/README.md)
# VITE_API_URL=http://localhost:<historic-port>
```

### Starting local APIs (quickstart)

```bash
# Example: deployment-api + deployment-ui (ports per ui-api-mapping.json)
cd deployment-api && source .venv/bin/activate
uvicorn api.main:app --reload --port 8004

cd deployment-ui && npm run dev

# Full stack: prefer unified-trading-system-ui
cd unified-trading-system-ui && bash scripts/dev-tiers.sh --tier 1
```

---

## Cloud Deployment (Production)

In Cloud Run, each UI is a static build served behind the API (or via CDN). The `VITE_API_URL` is injected at build time
as a Cloud Build substitution variable:

```yaml
# cloudbuild.yaml (each UI repo)
substitutions:
  _API_URL: "https://deployment-api-${_HASH}-uc.a.run.app"
steps:
  - name: node:20
    args: ["npm", "run", "build"]
    env:
      - "VITE_API_URL=${_API_URL}"
```

After the 4-way split (`deployment-v3-four-way-split`), `deployment-ui` is a standalone React repo. Its static build is
served via CDN or mounted in the `deployment-api` container. The Python orchestrator logic lives in
`deployment-service`, which `deployment-api` imports as a dependency.

---

## Status by UI

| UI Repo                     | Status     | Notes                                                   |
| --------------------------- | ---------- | ------------------------------------------------------- |
| `unified-trading-system-ui` | **active** | Canonical product UI — see repo docs and `dev-tiers.sh` |
| `deployment-ui`             | **active** | Ops / deployment surface with `deployment-api`          |

### ARCHIVED — reference only

| UI Repo                  | Status   | Notes                                                                      |
| ------------------------ | -------- | -------------------------------------------------------------------------- |
| `live-health-monitor-ui` | archived | In workspace-root `archive/` — see `archive/README.md`                     |
| `trading-analytics-ui`   | archived | Same                                                                       |
| `batch-audit-ui`         | archived | Same                                                                       |
| `strategy-ui`            | archived | Same                                                                       |
| `ml-training-ui`         | archived | Same                                                                       |
| `logs-dashboard-ui`      | archived | Same                                                                       |
| `execution-analytics-ui` | archived | Same                                                                       |
| `client-reporting-ui`    | archived | Same (capability merged into unified-trading-system-ui per ui-api-mapping) |
| `settlement-ui`          | archived | Same                                                                       |
| `onboarding-ui`          | archived | Same                                                                       |

Legacy blocker tasks for split UIs may still appear in old plans; they do not apply to archived trees.

---

## References

- **Archived repos (not in manifest):** workspace-root **`archive/README.md`**
- **Topology DAG:** `04-architecture/TOPOLOGY-DAG.md`
- **Deployment split:** task `deployment-v3-four-way-split`
- **Integration testing layers:** `06-coding-standards/integration-testing-layers.md`
- **Repo registry:** `unified-trading-pm/workspace-manifest.json`
- **UI/API ports:** `unified-trading-pm/scripts/dev/ui-api-mapping.json`
