---
doc_type: codex-ssot
title: UI / Service Separation
summary: >-
  Rule: UI code never lives inside a service repo — every UI is its own git repo consuming services over HTTP/SSE with
  TypeScript-only quality gates; includes the UI→API repo/dev-port mapping and known violations to extract.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [client-reporting-api, deployment-api, deployment-service, deployment-ui, execution-service, unified-trading-pm]
scope: [engineer]
tags: [ui, frontend, refactor, service-separation]
related:
  [
    /codex/06-coding-standards/ui-branding.md,
    /codex/06-coding-standards/ui-testing-layers.md,
    /codex/05-infrastructure/ui-dependency-matrix.md,
  ]
created: 2026-03-27
authoritative_for: [UI/service repo separation rule]
referenced_by: [/codex/06-coding-standards/ui-branding.md]
owner:
last_reviewed:
code_refs:
---

# UI / Service Separation

**Last Updated:** 2026-02-28 **Cursor rule:** `.cursor/rules/ui-service-separation.mdc` (enforcement) **SSOT for repo
registry:** `unified-trading-pm/workspace-manifest.json`

---

## Rule

> UI code must **never** live inside a service repo. Every UI is its own git repo. Services expose HTTP (FastAPI +
> OAuth). UIs consume them over HTTP/SSE.

---

## Why

Service repos contain Python engines, tests, and deployment artifacts. Mixing React/TypeScript into a service repo
creates:

- Dual quality gates in a single repo (Python + TypeScript)
- Bloated Docker images (Node dependencies in a Python service image)
- Blurred ownership boundaries (who owns the service engine? the UI? both?)
- CI/CD complexity — Cloud Build steps for both `pytest` and `npm test`

---

## The Correct Pattern

```
execution-service/              ← Python FastAPI service engine — no UI code
  execution_service/
  tests/
  cloudbuild.yaml               ← Python quality gates only

execution-results-api/          ← FastAPI API gateway: typed endpoints, OAuth, SSE
  execution_results_api/
  tests/
  cloudbuild.yaml               ← Python quality gates only

trading-analytics-ui/           ← React/TypeScript — consumes execution-results-api
  src/
  package.json
  cloudbuild.yaml               ← TypeScript quality gates only (tsc, ESLint, playwright)
```

---

## Enforcement

**DO:**

- Build a new UI repo when a UI is needed (`<function>-ui/` naming convention)
- Service exposes REST + SSE endpoints (FastAPI)
- UI accesses service via HTTP with Google OAuth Bearer token
- UI repo has TypeScript quality gates only (`tsc`, `ESLint`, `playwright`)
- Service repo has Python quality gates only (`ruff`, `basedpyright`, `pytest`)
- Every new UI gets `.env.local.example` — see `05-infrastructure/ui-dependency-matrix.md` for port assignments

**NEVER:**

- `ui/`, `frontend/`, `static/`, `visualizer-ui/` inside a Python service repo
- `package.json`, `node_modules/`, `*.tsx`, `*.jsx` inside a service repo
- A FastAPI sub-app nested inside another service repo (extract to its own `*-api` repo)
- Co-locating React build output in a service Docker image

---

## UI → API Repo Mapping

| UI Repo                  | API Repo                | Dev Port |
| ------------------------ | ----------------------- | -------- |
| `deployment-ui`          | `deployment-api`        | 8001     |
| `live-health-monitor-ui` | `deployment-api`        | 8001     |
| `batch-audit-ui`         | `deployment-api`        | 8001     |
| `logs-dashboard-ui`      | `deployment-api`        | 8001     |
| `ml-training-ui`         | `deployment-api`        | 8001     |
| `onboarding-ui`          | `deployment-api`        | 8001     |
| `trading-analytics-ui`   | `execution-results-api` | 8002     |
| `strategy-ui`            | `execution-results-api` | 8002     |
| `execution-analytics-ui` | `execution-results-api` | 8002     |
| `settlement-ui`          | `execution-results-api` | 8002     |
| `client-reporting-ui`    | `client-reporting-api`  | 8003     |

Full wiring details: `05-infrastructure/ui-dependency-matrix.md`

---

## Known Violations (extract these)

These are active violations tracked in `consolidated_remaining_work.plan.md`:

| Violation                                                                                      | Task ID                                 | Fix                                            |
| ---------------------------------------------------------------------------------------------- | --------------------------------------- | ---------------------------------------------- |
| `execution-service/visualizer-ui/` — React app inside Python service                           | `arch-exec-services-visualizer-extract` | Extract to `execution-visualizer-ui` repo      |
| `execution-service/visualizer-api/` — FastAPI inside Python service                            | `arch-exec-services-visualizer-extract` | Merge into `execution-results-api` or new repo |
| ~~`deployment-service/ui/`~~ — **RESOLVED** (2026-03-03): extracted to `deployment-ui` repo ✅ | `arch-deployment-v3-ui-extract`         | **DONE** — `deployment-ui` is its own repo     |

---

## Creating a New UI Repo

If a service needs a UI and none exists yet, creating a new repo is the correct approach.

**Preferred: Add to the unified platform** (unified-trading-system-ui) as a new route under the appropriate route group.
This avoids repo proliferation and shares shells, auth, and design tokens automatically.

**Alternative: Standalone satellite UI** (when the surface is truly independent):

```
<function>-ui/
  src/
    main.tsx
    App.tsx
    components/
  package.json          (React 19, Vite 6, TypeScript)
  .env.local.example    (VITE_API_URL=http://localhost:<port>, VITE_ENV=local)
  cloudbuild.yaml
  README.md
```

**Unified platform** (unified-trading-system-ui) uses **Next.js 16 App Router**:

```
app/(<group>)/<domain>/
  page.tsx              ← Route entry point
  layout.tsx            ← Optional domain-specific layout
components/<domain>/    ← Domain-specific components
```

Follow the UI setup checklist: `05-infrastructure/ui-setup-checklist.md`
