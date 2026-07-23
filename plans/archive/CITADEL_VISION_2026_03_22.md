---
doc_type: plan
title: Citadel-Grade System Vision — 2026-03-22
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos:
  [
    client-reporting-api,
    deployment-ui,
    execution-service,
    strategy-service,
    system-integration-tests,
    unified-api-contracts,
  ]
scope: [engineer, admin]
tags: []
related: []
created: "2026-03-22"
---

# Citadel-Grade System Vision — 2026-03-22

## Shared Context for All Agents

This document is the SSOT for the system-wide refactor. Every agent executing any of the 8 workstreams MUST read and
follow this vision. No agent should make decisions that conflict with this document.

---

## Completion path — finishing the Citadel epic

Use this section as the **close-out order** after feature work slows down. SSOT for task IDs:
`agent8_e2e_tests_quality_2026_03_22.md`.

| Step | Owner                         | What “done” means                                                                                                                                                                                                                                                                                                      |
| ---- | ----------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1    | **Agent 8 (remaining todos)** | Finish open items in agent8 plan (currently **~19 todo / ~21 done** — run `rg 'status: todo' plans/active/agent8*.md` to refresh). Priority: **UI build + vitest** (`a8-p1-ui-build`, `a8-p1-ui-vitest`), then **Phase 8** verification todos (`a8-p8-*`: QG on API + UI, tier/readiness E2E, redundant mock removal). |
| 2    | **Quality gates**             | `unified-trading-api` and `unified-trading-system-ui` both pass `bash scripts/quality-gates.sh` on the branch that merges the epic.                                                                                                                                                                                    |
| 3    | **Hardening (small PRs)**     | **API:** implement real **`upstream_checks`** in `GET /readiness` when Tier 2 is declared; quarantine or delete legacy `mock_data/state_store.py` per agent8 `a8-p8-verify-no-redundant-impl`. **UI:** fix **UI_STRUCTURE_MANIFEST.json** drift (e.g. BatchLiveRail no longer orphaned).                               |
| 4    | **Playwright / CI**           | Mock-mode E2E green in CI (auth + trading API + UI); optional **`e2e/tier-readiness.spec.ts`** per agent8 `a8-p8-sit-tier-readiness`.                                                                                                                                                                                  |
| 5    | **SIT (optional gate)**       | `system-integration-tests` smoke for staging — not in agent8 repo list; add only if epic `completion_gates.deployment` requires D3.                                                                                                                                                                                    |
| 6    | **Plan hygiene**              | When step 1–4 are true: mark agent8 todos **done**, set epic status to allow archive per `PLAN_FORMAT.md`, remove `locked_by` on agent8 when the locking branch/epic allows (human).                                                                                                                                   |

**Minimum bar to call the demo “Citadel-complete” for **code**: steps **1–2** + Tier 1 Playwright green. **Tier 2**
(real service processes + readiness truthfulness) requires step **3\*\* readiness probes and configured upstream URLs.

---

## Core Principles

1. **ONE UI** — `unified-trading-system-ui` is the only consumer-facing frontend. All 13 satellite UIs (batch-audit-ui,
   client-reporting-ui, deployment-ui, execution-analytics-ui, live-health-monitor-ui, logs-dashboard-ui,
   ml-training-ui, onboarding-ui, settlement-ui, strategy-ui, trading-analytics-ui, user-management-ui) are archived.
   Their functionality is absorbed into the main UI.

2. **THREE APIs** — The system has 3 API gateways:
   - `auth-api` — SSO/token issuance, user/org management, entitlements (no core trading logic)
   - `client-reporting-api` — Client-facing reporting, invoicing, regulatory, document management (needs only API keys
     and reporting logic, no core system services)
   - `unified-trading-api` — Trading system gateway (all internal + external trading functionality) The 8 remaining
     ml-inference-api, ml-training-api, trading-analytics-api) are absorbed into unified-trading-api.

3. **90% CODE SHARING** — Mock and real modes share the same route handlers (on the gateway), the same service layer,
   the same filtering/pagination logic. Only the data source differs (MockStateStore vs backend service calls).
   **Default integration path:** the UI calls the real HTTP APIs (`unified-trading-api`, `auth-api`,
   `client-reporting-api`); each gateway handles mock vs live internally. **Exception — Tier 0 (offline / API not
   ready):** the UI may run with an in-browser or same-origin mock that implements the **same OpenAPI operations** and
   an in-memory store, so product work continues without `unified-trading-api` running. Tier 0 is not a second ad-hoc
   data universe: it stays aligned via OpenAPI types, UAC schemas, shared seed fixtures, and contract checks against
   Tier 1. See **Runtime convergence tiers** (below).

4. **DIRECT-TO-TABS** — No intermediate landing pages with feature cards. Clicking a lifecycle nav item goes directly to
   the first tab of that service. Tabs ARE the navigation within a service.

5. **VISIBLE UX** — Every function must have a visible button/control. No hidden functionality. Reset Demo, Live/Batch
   toggle, Persona switcher, Org selector — all visible in the shell at all times.

6. **9 SERVICES** — The platform has exactly 9 service areas, each with tabbed navigation: Data, Research, Promote,
   Trading, Execution, Observe, Manage, Reports, Admin/Ops. Execution is separate from Trading because it's a distinct
   commercial offering — clients can subscribe to execution (algos, venue connectivity, TCA) independently.

---

## Runtime convergence tiers (topology × external data × API availability)

Work can progress at **three cumulative tiers** without blocking: each tier is **strictly more faithful** to production
than the last. Two ideas stay **orthogonal**:

- **Call topology** — who is in the HTTP/process graph (UI-only vs gateway vs full microservice fleet).
- **External data / risk posture** — `mock_mode`, testnet, emulators, VCR, vs live venues. Services can run the **same
  code paths** with **non-prod** adapters; that is still “real engine” topology.

### Real engines vs in-browser mocks (clarification)

**“Run real services” does not mean “traffic crosses the public internet.”** It means **real checked-out service repos**
(`strategy-service`, `execution-service`, …) started with each service’s **CLI** as **OS processes** on a developer
machine (or any host) — typically the same **sibling clone** pattern as `setup-workspace.sh` and
`workspace-manifest.json` `dependencies[]`. **Localhost HTTP** from UI → `unified-trading-api` → `strategy-service` is
still **real engine code**, not a TypeScript reimplementation. **Tier 0 (in-browser / no `:8030`)** is only for when
those Python processes are **intentionally absent**; it is not the definition of “mock mode.”

### Local dev mesh (single machine, sibling clones)

- **Self-contained UI workflow:** `unified-trading-system-ui` setup may, behind an **env flag**, **clone sibling repos**
  at manifest-aligned versions so a developer working **only** in the UI repo (or a sparse checkout) still runs the
  **same service revisions** as the full workspace — functionality tracks the services without vendoring multi‑MB domain
  data into the UI git tree.
- **Mock / non-prod:** Services run with CLI + env that select **mock adapters**, emulators, testnet, or
  `CLOUD_MOCK_MODE` as policy dictates. They may still **read/write cloud storage** for large blobs, shared caches, or
  reference datasets — “local process” ≠ “offline”; it means **not** depending on a long-lived K8s deployment to exist
  before you can dev.
- **Bulk domain data:** Registries and heavy artifacts stay **out of the UI repo** (cloud, CDN, versioned JSON from UAC
  / seed pipelines); **engines** stay in sibling service repos.

### UI → gateway integration profiles

1. **Slim (API-only):** UI points at `UNIFIED_TRADING_API_BASE_URL` (and auth/reporting URLs). **No** local clone of
   strategy/execution/etc. on that laptop — the gateway runs elsewhere (staging, teammate, CI).
2. **Full local mesh:** UI startup (env) triggers **clone + run** for **siblings + `unified-trading-api`** per manifest;
   all listeners on **localhost**; the UI talks **only via HTTP** to gateways (never embed Python in the Next.js
   bundle). Same effective topology as “full workspace on one machine” today.

### Gateway → downstream target modes (`LiveDomainService` and successors)

One gateway codebase; **two configuration shapes** (not duplicated business logic):

1. **Co-located fleet:** Service base URLs point at **localhost** (or docker-compose network) where processes were
   started from **cloned sibling repos** — laptop and many integration tests.
2. **Networked fleet:** Base URLs point at **remote** processes (cloud Run, staging k8s, another VPC). **Ports, TLS, and
   auth** are config-only.

**Production evolution:** Hops may become **Pub/Sub, Redis, or internal buses** instead of raw HTTP between every pair;
the invariant remains **real orchestration against real engine processes**, not reimplemented logic in the gateway.

### Tier 0 — UI-only trading API (no HTTP to `unified-trading-api`)

**When:** `unified-trading-api` is down, not merged yet, or developers want **zero** Python gateway processes for UI
work.

**Shape:**

- No requests to the trading gateway port (`:8030` by convention). Auth and client-reporting may still use their
  gateways if running, or be mocked behind the same env flag — product choice.
- **State:** trading-domain reads/writes live in an **in-memory (or IndexedDB) store inside the browser** — fully
  self-contained for everything that fits in RAM.
- **Large domain data:** instrument registries, representative samples, static reference tables, and other **bulk**
  payloads may load over the network from **cloud storage / CDN / versioned JSON artifacts** (exported from UAC or the
  same seed pipeline as the API). That does **not** violate Tier 0: the **trading API process** is still absent; only
  read-mostly reference data crosses the wire.
- **Semantics:** the in-UI layer should mirror **`MockDomainService` behavior** and **OpenAPI** response shapes — not
  arbitrary fixtures. **Service Python does not execute inside the browser**; when you need **real engines**, use
  **sibling clones + local processes** (sections above), not a bigger JS bundle. Tier 0 alignment uses **shared
  contracts** (OpenAPI codegen, JSON Schema, exported seed JSON) and **tests** that compare Tier 0 responses to Tier 1
  curl fixtures.

**Sensible?** Yes, for velocity and demos when the gateway is unavailable. **Risk:** behavioral drift vs the server.
**Mitigation:** OpenAPI SSOT, shared seeds (Agent 6), and periodic contract tests — not hand-written MSW handlers that
diverge from `unified-trading-api`.

### Tier 1 — Gateway + libraries, no (or minimal) cross-service HTTP

**When:** Laptop demo, fast CI, partial stack.

**Shape:** `unified-trading-api` runs; **MockStateStore** (UTL) backs mock mode on the gateway; **no** fan-out to
strategy-service, execution-service, etc., or only **selective** HTTP (e.g. reporting proxy). Same FastAPI routes and
service layer as production gateway; **process graph** is not the full fleet.

### Tier 2 — Full fleet topology, mock-friendly backends

**When:** Staging, SIT, integration tests that must prove **wiring**.

**Shape:** Gateway **calls** real service processes at **configured URLs** (localhost from sibling clones **or** remote
hosts — **equivalent** for parity). Each downstream service may run **`mock_mode`**, testnet, or emulators — **same
orchestration graph as production**, different credentials and side effects. This is **full engine + wire** parity;
“mock” here means **external I/O posture**, not “skip microservices” and not “must be in the cloud.”

### Progression rule

Features may land at **Tier 0** first, then gain assurance at **Tier 1** (curl + gateway), then **Tier 2** (fleet —
**including** localhost sibling mesh). **Authoritative trading behavior** remains **defined and tested at the API**
(curl / integration tests); Tier 0 is a **contract-preserving projector** for the UI when the gateway is absent — not a
permanent second backend. Prefer **full local mesh + mock_mode services** over Tier 0 when the goal is **engine**
fidelity without a remote cluster.

---

## Runtime mode: env vars, CLI, health, and UI truthfulness

This section is the **implementation SSOT** for “what to build” so every combination of tier, mesh, and environment is
**explicit**, **observable**, and **fails loudly** when prerequisites are missing. Applies to **dev, staging, and prod**
(the values change; the **contract** does not).

### 1. Configuration surface (env + CLI) — single matrix

**Principle:** No silent fallbacks. **Declared mode** + **effective mode** may differ only when the UI/API shows **why**
(readiness / banner).

| Concern                        | Typical variables / CLI                                                                                         | Notes                                                                                                                                                                       |
| ------------------------------ | --------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Deployment environment**     | `DEPLOYMENT_ENV` or `NODE_ENV` + explicit `APP_ENV=development\|staging\|production`                            | UI: `NEXT_PUBLIC_APP_ENV` (must be public for badge). Never rely on `NODE_ENV` alone for staging vs prod.                                                                   |
| **UI integration profile**     | `NEXT_PUBLIC_UI_INTEGRATION=slim\|full_mesh\|tier0_offline`                                                     | **slim** = HTTP to remote/local API only. **full_mesh** = bootstrap may clone siblings + start processes (script/CLI). **tier0_offline** = in-browser API mock, no `:8030`. |
| **API base URLs**              | `NEXT_PUBLIC_UNIFIED_TRADING_API_URL`, auth, reporting                                                          | Slim profile; full_mesh may still use localhost defaults.                                                                                                                   |
| **Gateway data path**          | `UNIFIED_TRADING_API_USE_MOCK_DOMAIN_SERVICE=true\|false` (or existing `CLOUD_MOCK_MODE` / `data_mode` per UCI) | Tier 1 **MockStateStore** vs **LiveDomainService** fan-out.                                                                                                                 |
| **Gateway downstream targets** | `LIVE_SERVICE_STRATEGY_URL`, `LIVE_SERVICE_EXECUTION_URL`, … or **one** `SERVICE_MESH_CONFIG` / discovery file  | Co-located vs networked; empty or localhost per tier.                                                                                                                       |
| **Local mesh bootstrap**       | `scripts/dev-start.sh --profile full-mesh` (or UI `pnpm run dev:mesh`)                                          | Clones + starts siblings + API; manifest pins versions. **CLI must print** effective profile and missing repos.                                                             |
| **Per-service mock**           | Existing service CLI flags + `CLOUD_MOCK_MODE`, provider keys                                                   | Each service logs **effective** mock/live at startup.                                                                                                                       |

**CLI rules:** Any dev entrypoint that starts multiple processes **must** (1) parse the same env names as CI/staging
templates in PM, (2) **exit non-zero** with a **clear message** if `NEXT_PUBLIC_UI_INTEGRATION=full_mesh` but a required
repo failed clone, (3) print a one-line **effective summary** (profile + tier + mock flags).

### 2. Health vs readiness — machine-readable mode and gaps

**`GET /health` (liveness):** Process up; minimal dependencies (optional).

**`GET /readiness` (or extended `GET /health` in dev only — pick one per repo and document):** JSON body **must**
include, for `unified-trading-api` and each long-lived service:

- `app_env`: `development` \| `staging` \| `production`
- `declared_runtime_tier`: what config **asked** for (0 / 1 / 2 or enum)
- `effective_runtime_tier`: what is **actually** satisfiable (may be lower if upstreams down)
- `mock_domain_service`: bool (gateway using MockStateStore path)
- `external_data_mocked`: bool (aggregate: emulators / testnet / `CLOUD_MOCK_MODE`)
- `upstream_checks`: array of
  `{ "name": "strategy-service", "required_for_tier": 2, "ok": false, "url": "...", "error": "connection refused" }`
- `degraded_reasons`: string[] for logs and UI banners

**Rules:**

- If **declared** tier is 2 but a **required** upstream is down → `effective_runtime_tier` ≤ what still works, HTTP
  **503** on readiness (or **200 with `ok: false`** — pick one standard; gateway should be consistent across envs).
- **Startup logs:** WARN when `declared` ≠ `effective` or when running Tier 1 but env hints Tier 2.

Downstream services **must** expose the same **shape** (subset allowed) so the gateway can aggregate for the UI **System
Health** surface.

### 3. UI: always show where you are and what is missing

**Global shell (every env, not only mock):**

- **Environment badge:** `DEV` \| `STAGING` \| `PROD` (color-coded). Sourced from `NEXT_PUBLIC_APP_ENV` + build-time
  injection for prod.
- **Runtime strip** (compact, Row 1 or debug bar): **Tier** (0/1/2), **Integration** (slim / mesh / offline), **Data:**
  Mock store vs Live fan-out, **API:** Reachable / Degraded / Offline (from polling readiness).
- **Blocking banner** when user or config expects Tier 2 but readiness shows missing upstreams — text must name
  **which** service and **which** env var or port fixes it (link to internal runbook or tooltip).
- **Debug footer** (existing plan): extends to show **effective** tier + link “View readiness JSON” for developers when
  `NEXT_PUBLIC_DEBUG_RUNTIME=true`.

**Observe > System Health** (or equivalent tab): table of services from **aggregated readiness**; red/yellow/green; last
error string; **required for current tier** column.

**Prod:** Same badges (no secrets); readiness may be auth-gated; degraded state still visible to ops roles.

### 4. Implementation checklist (repos)

| Repo / artifact                      | Change                                                                                                                                         |
| ------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| **unified-trading-api**              | Implement readiness JSON above; aggregate optional upstream probes when `LiveDomainService`; clear errors when tier unsatisfied.               |
| **unified-trading-system-ui**        | Read `NEXT_PUBLIC_*`; shell badges; poll trading + auth readiness; banners; wire System Health tab to aggregated endpoint or parallel fetches. |
| **Sibling services**                 | Standardize readiness field subset + startup WARN on config mismatch.                                                                          |
| **unified-trading-pm**               | `dev-start.sh` / compose templates: document env matrix; same keys as staging secret templates; fail-fast messages.                            |
| **unified-config-interface / codex** | Document canonical env names if not already (avoid drift).                                                                                     |

### 5. Agent ownership (for execution)

- **Agent 1 (shell):** Runtime strip, banners, System Health wiring, debug footer extensions — see `agent1` plan todo.
- **Agent 5 (gateway):** Readiness schema, upstream checks, tier semantics — see `agent5` plan todo.
- **Agent 7 (observe):** System Health tab consumes readiness; align with shell.

---

## Service Architecture

### Global Shell (Every Authenticated Page)

```
Row 1 LEFT:   [Logo] Acquire | Build | Promote | Run | Execute | Observe | Manage | Report
Row 1 CENTER: [All Orgs ▾] [All Clients ▾] [All Strategies ▾] [$41M] [28.9M exposed]
Row 1 RIGHT:  [Search ⌘K] [🔔] [Odum Internal ▾] [User ▾]
Row 2:        Tab1 | Tab2 | Tab3 | Tab4 | Tab5          [Live ◉ / As-Of 📅]
Breadcrumbs:  Trading > Terminal
Env strip:    [DEV] Tier 2 · Mesh · Live fan-out · API OK   (all envs; prod uses PROD styling)
Debug Footer: [Reset Demo] [Mock Mode ◉] [Persona: Admin ▾]  (mock / debug flags only)
```

### Global Scope Filters (Row 1 Center — EVERY service page)

- **Org dropdown** — filter all data by organization. Admin sees all orgs; clients see only theirs.
- **Client dropdown** — filter by client within the selected org. Cascading from org selection.
- **Strategy dropdown** — filter by strategy. Most services support this. Admin/Ops may not.
- These filters are in `components/platform/global-scope-filters.tsx` (already exists, wired in lifecycle-nav.tsx center
  section)
- The orphaned `OrgClientSelector` component should be verified as wired into GlobalScopeFilters
- Every service tab reads from `useGlobalScope()` store and filters its data accordingly
- Service-specific filters (venue, instrument, date range, severity) appear in Row 2 or within the tab content using the
  `FilterBar` component — same UX look and feel across all services

### Service 1: DATA (Acquire)

- Entry: `/services/data/overview`
- Tabs: Pipeline Status | Coverage Matrix | Missing Data | Venue Health | Markets | ETL Logs
- All pages EXIST and are kept as-is

### Service 2: RESEARCH & BACKTESTING (Build)

- Entry: `/services/research/overview`
- Tabs: Research Hub | Features | ML Models | Strategies | Compare | Signals | Execution Research
- ML Models tab has sub-tabs: Overview | Experiments | Training | Validation | Registry | Monitoring | Deploy |
  Governance
- ABSORBS: strategy-ui wizard, ml-training-ui experiment tracking

### Service 3: PROMOTE (Promote)

- Entry: `/services/research/strategy/candidates`
- Tabs: Review Queue | Execution Analysis | Risk Review | Approval Status
- RESTORE: CandidateBasket component (orphaned, exists on disk)

### Service 4: TRADING (Run)

- Entry: `/services/trading/overview` (the terminal — NOT a card landing)
- Tabs: Terminal | Positions | Orders | Accounts | Markets | Strategies
- ALSO: /dashboard (Command Center) as separate entry under Run
- RESTORE: BatchLiveRail (orphaned), ManualTradingPanel (deleted in 5c24fa2)
- NOTE: Execution Analytics moved to its own service (Service 5)

### Service 5: EXECUTION (Execute)

- Entry: `/services/execution/overview`
- Tabs: Analytics | Algos | Venues | TCA | Benchmarks | Candidates | Handoff
- Lifecycle stage: "Execute" (between Run and Observe)
- Distinct commercial offering: clients subscribe to execution algos, venue connectivity, and TCA independently. Basic
  clients can observe trades on the terminal; execution subscribers get access to advanced algos, custom execution
  strategies, and venue analytics.
- ABSORBS: execution-analytics-ui, trading-analytics-ui
- Entitlement: `execution-basic` (venue status, fill quality) or `execution-full` (algos, TCA, custom strategies)

### Service 6: OBSERVE (Observe)

- Entry: `/services/observe/risk` (or `/services/trading/risk` — shared route)
- Tabs: Risk Dashboard | Alerts | News | Strategy Health | System Health
- ABSORBS: live-health-monitor-ui, logs-dashboard-ui

### Service 7: MANAGE (Manage)

- Entry: `/services/manage/clients`
- Tabs: Clients | Mandates | Fees | Users | Compliance
- ABSORBS: onboarding-ui, user-management-ui

### Service 8: REPORTS (Report)

- Entry: `/services/reports/overview`
- Tabs: P&L Attribution | Executive | Settlement | Reconciliation | Regulatory
- ABSORBS: client-reporting-ui, settlement-ui

### Service 9: ADMIN/OPS (Internal Only)

- Entry: `/admin`
- Tabs: Admin Dashboard | Config | DevOps | Jobs | Services | Data ETL
- ABSORBS: deployment-ui (8-tab richness), batch-audit-ui
- HIDDEN from client personas

---

## Routes to REMOVE

- `/services/[key]` dynamic card landing page
- `/services/overview` hub page (replace with `/dashboard` as post-login landing)
- `/portal/*` (all 8 pages — dead redirects)
- SERVICE_SECTIONS and SERVICE_REGISTRY card definitions

## Components to RESTORE (from orphaned code or git history)

- `BatchLiveRail` — components/platform/batch-live-rail.tsx (zero imports, wire it)
- `FilterBar` — components/platform/filter-bar.tsx (zero imports, wire it)
- `CandidateBasket` — components/platform/candidate-basket.tsx (wire it)
- `LiveAsOfToggle` — components/platform/live-asof-toggle.tsx (verify wired in service layouts)
- `ManualTradingPanel` — restore from git commit 5c24fa2 (live-health-monitor-ui)
- `resetDemo()` — lib/reset-demo.ts (exists, wire to visible Debug Footer button)

## Satellite UIs to ARCHIVE

batch-audit-ui, client-reporting-ui, deployment-ui, execution-analytics-ui, live-health-monitor-ui, logs-dashboard-ui,
ml-training-ui, onboarding-ui, settlement-ui, strategy-ui, trading-analytics-ui, user-management-ui

## Reference Material

- `_reference/` folder in unified-trading-system-ui has versa-\* repos with patterns to absorb
- REFERENCE_MAPPING.md documents which reference maps to which service area

---

## API Architecture

### 3 API Gateways

#### auth-api (Port 8200)

- OAuth providers (Google, Microsoft, Slack), JWT issuance, session management
- User/org/entitlement CRUD, API key management
- No core trading logic — purely auth/admin
- UI routes: `/login`, `/signup`, persona switching

#### client-reporting-api (Port 8014)

- Client-facing: P&L reports, invoices, compliance, documents, DocuSign
- Routes: /reports, /pnl, /alerts, /invoices, /compliance, /documents, /docusign, /sports, /streaming
- Auth: API key + JWT Bearer (client-scoped, no system access)
- UI routes: `/services/reports/*` (P&L, Executive, Settlement, Regulatory)
- Separate because: client-facing, needs only API keys + reporting logic, no core services

#### unified-trading-api (Port 8030)

- Trading system gateway: all internal + external trading functionality
- 14 domain routers: market-data, execution, positions, analytics, ml, audit, config, alerts, risk, instruments,
  deployment, service-status, users, websocket
- UI routes: everything except /services/reports/\* and auth flows

### Service Layer Pattern (MANDATORY)

```python
# Route (shared, identical for mock and real):
@router.get("/orders")
async def get_orders(service: OrderService = Depends(get_order_service)):
    return await service.list_orders(filters)

# Service interface:
class OrderService(Protocol):
    async def list_orders(self, filters) -> PaginatedResponse: ...

# Mock implementation:
class MockOrderService:
    def __init__(self, store: MockStateStore): ...
    async def list_orders(self, filters):
        records = self.store.list("orders")
        # SAME filtering, pagination, sorting logic as real
        return paginate(apply_filters(records, filters))

# Real implementation:
class LiveOrderService:
    async def list_orders(self, filters):
        response = await self.execution_service_client.get_orders(filters)
        return paginate(response)

# Factory (injected via Depends):
def get_order_service(request: Request) -> OrderService:
    if request.app.state.mock_mode:
        return MockOrderService(mock_store)
    return LiveOrderService()
```

### Mock State

- Uses UTL MockStateStore (JSONL persistence in .local-dev-cache/)
- `POST /admin/reset` endpoint to reset all mock state to seed values
- Org-scoped filtering: mock data filtered by org from JWT token
- Deterministic seeding for CI (MOCK_STATE_MODE=deterministic)

---

## Auth & Personas

### Personas (same in auth-api and UI)

- Admin: Full system access, all services visible
- Internal Trader: Platform + wildcard, admin/manage hidden
- Client Full (Alpha Capital): All services except manage/admin
- Client Premium (Vertex Partners): Data + Execution + Strategy
- Client Data Only (Beta Fund): Data service only, rest shows "Upgrade" badges

### Post-Login Flow

- Admin/Internal → /dashboard (Command Center)
- Client Full/Premium → /dashboard (filtered to their org)
- Client Data Only → /services/data/overview

---

## SSOT Sync Infrastructure (CRITICAL — Central to Everything)

The system has a comprehensive sync pipeline in `unified-trading-pm/scripts/`. These scripts are the backbone of the
multi-repo architecture — they keep registries, schemas, configs, and types aligned across 65+ repos. **Every agent MUST
understand and use this pipeline.**

### Master Alignment Pipeline (Run FIRST, before any work)

```bash
# Full 9-stage alignment check + auto-fix
cd /Users/ikennaigboaka/Code/unified-trading-system-repos
bash unified-trading-pm/scripts/repo-management/run-version-alignment.sh --fix
```

This runs: tracked-ignored audit → broken symlinks → import pattern check → npm drift → uv.lock drift → dep caps →
self-version parity → remote version drift → derive manifests → check alignment → validate uv sources → constraints
resolution.

### Pipeline 1: UAC → UI Reference Data (128 venues, all registries)

```bash
# Generates ui-reference-data.json (2,297 lines) from UAC registries
# Includes: 128 venues, capability declarations, enums, config schemas, rate limits, instrument specs
cd unified-api-contracts
.venv/bin/python scripts/generate_ui_reference_data.py --output ../unified-trading-system-ui/context/api-contracts/openapi/ui-reference-data.json
```

**SSOT scripts (all in `unified-trading-pm/scripts/openapi/`):**

- `generate_ui_reference_data.py` (371 lines) — UAC/UIC enums, registries, config schemas → JSON for UI
- `generate_config_registry.py` (247 lines) — extracts all Pydantic config classes from 25+ repos
- `generate_system_topology.py` (256 lines) — aggregates all PM manifests into single topology
- `generate_unified_spec.py` (508 lines) — merges OpenAPI specs from all 16 FastAPI services

**When to run:** After ANY change to UAC registries, UIC schemas, or service configs. **Automated:** GHA
`uac-registry-sync.yml` triggers on UAC commits → regenerates → opens PR in UI repo.

### Pipeline 2: API → UI TypeScript Types

```bash
cd unified-trading-api && CLOUD_MOCK_MODE=true .venv/bin/python -m unified_trading_api.main &
sleep 3
curl http://localhost:8030/openapi.json > ../unified-trading-system-ui/lib/registry/openapi.json
cd ../unified-trading-system-ui && npm run generate:types
kill %1
```

**Automated:** GHA `uic-openapi-sync.yml` triggers on UIC commits → regenerates TypeScript types → opens PR.

### Pipeline 3: Persona/Org Alignment

**SSOT:** `unified-trading-api/mock_data/personas.py` (121 lines, already exists)

- auth-api `mock_data.py` must use same org IDs and entitlement keys
- UI `hooks/use-auth.ts` persona definitions must match
- `scripts/verify_persona_alignment.py` validates all three match

### Pipeline 4: Strategy Manifest Alignment

**SSOT:** `unified-trading-pm/strategy-manifest.json`

```bash
# Validate strategy manifest completeness and references
python unified-trading-pm/scripts/validation/validate-strategy-manifest.py

# Check strategy-instrument capability matrix
python unified-trading-pm/scripts/manifest/check-strategy-instruments.py
```

### Pipeline 5: Dependency Alignment

```bash
# Generate derived manifest from all pyproject.toml files
python unified-trading-pm/scripts/manifest/generate-derived-manifest.py

# Check alignment: manifest vs code imports vs constraints
python unified-trading-pm/scripts/manifest/check-dependency-alignment.py

# Auto-fix internal dependency misalignment
python unified-trading-pm/scripts/manifest/fix-internal-dependency-alignment.py --apply

# Auto-fix external dependency versions to match canonical
python unified-trading-pm/scripts/manifest/fix_external_dependency_alignment.py --apply
```

### Pipeline 6: Architecture Validation

```bash
# Check Citadel import rules (UAC facade-only, no cross-service imports)
python unified-trading-pm/scripts/validation/check-import-patterns.py

# Find all coding violations (try/except imports, os.getenv, type:ignore)
python unified-trading-pm/scripts/validation/find-coding-violations.py

# Check schema provenance (schemas in correct SSOT, not re-defined)
python unified-trading-pm/scripts/validation/check_schema_provenance.py

# Check UI→API flow coverage
python unified-trading-pm/scripts/checkers/check_ui_api_flow_coverage.py
```

### Key Manifest Files (Data-Driven SSOTs)

| File                         | Location        | Purpose                                                |
| ---------------------------- | --------------- | ------------------------------------------------------ |
| `workspace-manifest.json`    | PM root         | All 65+ repos: versions, tiers, deps, CI status        |
| `workspace-constraints.toml` | PM root         | External dep version SSOT                              |
| `strategy-manifest.json`     | PM root         | All strategies: IDs, venues, maturity, capabilities    |
| `data-flow-manifest.json`    | PM root         | Data pipeline: instruments→tick-data→features→strategy |
| `ui-api-mapping.json`        | PM scripts/dev/ | Service→port mapping for local dev                     |
| `ui-reference-data.json`     | UAC openapi/    | Generated: 128 venues, enums, registries for UI        |

### Current Drift Status (2026-03-22)

- ui-reference-data.json is OUT OF SYNC with UAC (generator output changed)
- OpenAPI spec in UI may not match current API routes
- strategy-manifest.json has 18 strategies — needs expansion to 50+
- **These MUST be re-synced before agents start UI→API integration work**
- Agent 8 is responsible for running ALL sync pipelines after Agents 5-6 finish

---

## Real-Time Data Architecture (CRITICAL for Demo Feel)

### Live Data Persistence

Both mock and production modes read live data from the **same directory structure**:
`.local-dev-cache/unified-trading-api/`. The MockStateStore (from UTL) persists all live-domain collections as JSONL
files here. In production, the same directory structure would be populated by real service writes. This means:

- `positions_live.jsonl` — real-time positions (updated by WebSocket or polling)
- `orders_live.jsonl` — real-time orders
- `pnl_live.jsonl` — real-time PnL snapshots
- `tickers_live.jsonl` — latest ticker prices
- `alerts_live.jsonl` — real-time alerts (new alerts arrive, can be acknowledged)
- `risk_live.jsonl` — real-time risk exposure (updated as positions change)

### Batch/Live Switch

The **only difference** between batch and live mode is which collection the API reads from:

- **Live mode** (`mode=live`): reads from `{domain}_live` collections — real-time, mutable, updated by WebSocket feed
- **Batch mode** (`mode=batch&as_of=2026-03-21`): reads from `{domain}_batch` collections — T+1 reconciled, immutable
  snapshots

The switch is clean because both live in the same `.local-dev-cache/` directory. The UI sends `mode` and `as_of` query
params; the API reads from the correct collection. No separate data stores, no environment variable changes.

**This applies to ALL domain data — no exceptions.** Positions, orders, fills, PnL, tickers, alerts, risk exposure,
settlements, strategy health — every domain has `_live` and `_batch` variants. The service engine logic (filtering,
pagination, aggregation, org-scoping) is >90% identical between modes. The ONLY difference is the storage collection
name. No separate code paths, no mode-specific business logic.

### Batch Data Characteristics (vs Live)

- Batch PnL includes reconciliation adjustments (slightly different from live)
- Batch positions may lag by 1-2 fills (unreconciled fills not yet in batch)
- Batch prices are official close prices, live prices are last tick
- Batch has exact fee breakdowns, live has estimated fees
- Batch alerts are the reconciled alert history — all alerts have final status (acknowledged/escalated/resolved). Live
  alerts include new unacknowledged alerts that arrived since the batch cut.
- Batch risk is end-of-day risk snapshot. Live risk updates as positions and prices change.

### WebSocket Mock Feed

The unified-trading-api WebSocket endpoint (`/ws`) MUST emit simulated price ticks in mock mode:

- **Brownian motion** price generator for subscribed instruments (ALL instruments from `representative_sample.py`)
- **Tick interval**: 500ms-2000ms (randomized for realism)
- **Data**: `{ instrument, price, volume, bid, ask, timestamp }`
- Ticks update the `tickers_live` collection in MockStateStore (so REST endpoints reflect current prices)
- The UI Trading Terminal subscribes on mount, unsubscribes on unmount
- This is what makes the terminal feel **alive** — prices moving, charts updating, order book shifting

### Real-Time PnL Propagation (CRITICAL — Server-Side, Not UI Logic)

Price ticks MUST flow through to PnL. The calculation happens in the **mock service layer**, NOT in the UI.

**Server-side flow (Agent 5 — MockDomainService):**

1. WebSocket tick generator updates `tickers_live` collection with new prices
2. On each tick batch, MockDomainService recalculates positions:
   - For each position where `instrument == tick.instrument`:
     `unrealized_pnl = (tick.price - position.entry_price) * position.quantity * side_multiplier`
   - Update `positions_live` collection in MockStateStore
3. Aggregate strategy-level PnL from updated positions:
   - Group positions by strategy_id, sum unrealized_pnl per strategy
   - Update `pnl_live` collection
4. Emit WebSocket messages:
   - `{ channel: "positions", type: "pnl_update", data: { positions: [...] } }`
   - `{ channel: "analytics", type: "pnl_snapshot", data: { strategies: [...] } }`

**Client-side flow (Agent 2 — UI):**

1. Dashboard subscribes to `analytics` WebSocket channel
2. Strategy performance cards update PnL values on each snapshot
3. Equity curves append new data points in real-time
4. Position table updates PnL column from `positions` channel

**Why server-side:** This ensures the same PnL calculation logic works when the service is real. The UI is purely visual
— it renders what the WebSocket tells it. If you can't see PnL updating via `wscat`, it shouldn't update in the UI
either.

**Test:** `wscat -c ws://localhost:8030/ws` → subscribe to positions channel → observe PnL values changing as ticks
arrive. If this works, the UI just renders it.

### OHLCV Candle Data

The API must serve historical candle data (`GET /market-data/candles?instrument=BTC-USDT&interval=1h&limit=200`):

- Seed 200 candles per instrument per interval (1m, 5m, 1h, 1d)
- Generated procedurally: Brownian motion with realistic volume profiles (higher volume at opens/closes)
- At least 10 instruments with candle data

### Order Book Depth

The API must serve order book snapshots (`GET /market-data/orderbook?instrument=BTC-USDT`):

- 20 bid levels + 20 ask levels per instrument
- Realistic spread (0.01-0.05% of price)
- Depth decreasing away from mid-price
- In mock mode, regenerated with slight randomization on each request (simulates market movement)

---

## Auth Architecture (3-API Integration)

### Auth Flow

- **Login**: UI redirects to `/login` → user picks persona (mock) or OAuth provider (real) → auth-api issues JWT → UI
  stores token → UI reads entitlements from token claims → UI renders appropriate service access
- **Persona switching**: Clicking a different persona in the debug footer **redirects to login page** with the new
  persona pre-selected. It does NOT instant-swap — the user must click "Sign In" to complete the switch. This ensures
  the JWT is properly re-issued and all API calls use the new token.
- **Logout**: UI clears token → redirects to `/login`

### auth-api Integration (Port 8200)

- **MUST be added to** `ui-api-mapping.json` and `dev-start.sh` service_workers
- UI's `next.config.mjs` already has rewrite: `/api/auth/:path*` → `http://localhost:8200/:path*`
- In mock mode with `DISABLE_AUTH=true`: auth-api still runs but skips token validation, issues demo JWTs
- **Remove MSW auth handlers** — the UI should call auth-api directly, even in mock mode. Auth-api has its own
  `mock_data.py` with demo personas that must align with unified-trading-api's `personas.py`

### client-reporting-api Integration (Port 8014)

Reports service routes MUST go to client-reporting-api, not unified-trading-api:

- **Option A (recommended)**: unified-trading-api acts as proxy — `/reporting/*` routes forward to
  `http://localhost:8014/api/*`. This keeps the UI simple (one API base URL).
- **Option B**: UI has separate base URL for reports. Add `NEXT_PUBLIC_REPORTING_URL=http://localhost:8014` env var and
  update `lib/api/fetch.ts` to route `/reporting/*` and `/reports/*` paths to this URL.

Choose Option A for simplicity. unified-trading-api's `routes/reporting.py` becomes a thin proxy in real mode and serves
from MockStateStore in mock mode (mirroring client-reporting-api's data).

### Dev Stack Changes Required

1. Add auth-api to `ui-api-mapping.json`: `{ "name": "auth-api", "api_port": 8200, "module": "auth_api" }`
2. Add auth-api to `dev-start.sh` service_workers section
3. Remove MSW auth handlers from UI (`lib/mocks/handlers/auth.ts`)
4. Verify auth-api `mock_data.py` persona IDs match unified-trading-api `personas.py`

---

## Visual Polish Standards (Agents MUST Follow)

### Loading States (MANDATORY)

Every page that fetches data from the API MUST show **skeleton placeholders** (not "Loading..." text) while data loads:

- Use the existing `<Skeleton>` component from `components/ui/skeleton.tsx`
- Pattern: `if (isLoading) return <PageSkeleton />` where `PageSkeleton` mimics the page layout with shimmer bars
- Tables: show 5 skeleton rows with column-width-appropriate shimmer bars
- Cards: show card outline with shimmer content
- Charts: show chart area outline with shimmer
- This is the difference between "prototype" and "production" feel

### Command Palette (Wire Existing Component)

The `<Command>` component from `components/ui/command.tsx` (cmdk library) MUST be wired to:

- Global `Cmd+K` / `Ctrl+K` keyboard shortcut
- Search across: services, strategies, instruments, recent pages
- Quick actions: Reset Demo, Switch Persona, Toggle Batch/Live
- Render in the shell layout so it's available on every page

### Notification Bell (Wire to Real Alerts)

The bell icon in `lifecycle-nav.tsx` MUST:

- Show actual alert count from `GET /alerts/active?acknowledged=false` (not hardcoded "3")
- Open a dropdown with the 5 most recent alerts (severity badge + message + timestamp)
- "View All" link navigates to `/services/observe/alerts`
- Acknowledge action calls `POST /alerts/{id}/acknowledge` inline

---

## Current State Baseline (Verified 2026-03-22)

Agents MUST read this before planning work. Several areas are further along than initial estimates:

### Already Done (Do NOT redo)

- **API service layer**: `services/` exists with `DomainService` Protocol (base.py), `MockDomainService`
  (mock_service.py), `LiveDomainService` (live_service.py), factory.py with `get_service(request)` DI. All 19 routes
  already use this pattern — NO if/else mock checks remain.
- **WebSocket**: `routes/websocket.py` is 4,859 lines with channel-based multiplexing (market-data, positions, alerts,
  health, execution), synthetic tick generator, per-client subscription tracking.
- **personas.py**: 121 lines in `unified_trading_api/mock_data/personas.py` — 4 orgs, 5 personas, entitlements. Matches
  auth-api's `mock_data.py`.
- **auth-api**: Fully implemented — port 8200, JWT issuance (HS256, 1h access / 7d refresh), 5 mock users, mock login
  flow. Has `mock_data.py` and `mock_state.py`.
- **Dark mode**: Already the only theme. `ui-prefs-store.ts` has `theme: "dark"`, `theme-provider.tsx` wraps
  `next-themes`, all shadcn/ui components use CSS variables with dark mode support. No work needed.
- **Execution service pages**: All 7 tabs exist as real pages (298-405 lines each): overview, algos, venues, tca,
  benchmarks, candidates, handoff. Layout exists.
- **UI page richness**: 49 of 60 service pages are real (100-2000+ lines). Only 11 are stubs (24 lines each).

### Still Needed (Confirmed gaps)

- **MockStateStore migration**: state_store.py is still 68 lines, in-memory only. UTL MockStateStore (JSONL persistence,
  .local-dev-cache/) NOT yet adopted.
- **Seed data enrichment**: No PnL time-series, no OHLCV candles, no ticker seeds, no batch/live separation, no
  org-scoped data. seed.py is 1,323 lines covering basic domains only.
- **MSW removal**: `lib/mocks/` (18 handlers + fixtures) still exists. `lib/trading-data.ts` (1000+ lines) still used by
  Dashboard.
- **Debug footer**: Does not exist.
- **Skeleton loading variants**: Only base `skeleton.tsx` exists. No table/card/chart variants.
- **auth-api dev stack**: NOT in ui-api-mapping.json, NOT started by dev-start.sh.
- **E2E tests**: Only 2 Playwright specs (smoke.spec.ts, trader.spec.ts).
- **API tests**: Only 3 test files. Coverage far below 80%.
- **11 stub pages**: orders, accounts, settlement, reconciliation, regulatory, news, strategy-health, coverage, missing,
  venues (data), logs — all 24 lines.
- **Orphaned components**: filter-bar (0 imports), candidate-basket (0 imports). batch-live-rail partially wired (2
  imports). live-asof-toggle partially wired (4 imports).
- **Portal pages**: 9 dead redirect pages still exist.
- **Card landing [key]**: Still exists.

---

## Error States & Empty States (MANDATORY — All Agents)

Every page and component that loads data MUST handle these states. This is the difference between a prototype and a
production-grade demo.

### Error Boundaries

- Create `components/ui/error-boundary.tsx` — React error boundary that catches render errors, shows recovery UI (not
  white screen)
- Create `components/ui/api-error.tsx` — standard error display for failed API calls: icon, message, "Retry" button
- Pattern: `if (isError) return <ApiError error={error} onRetry={refetch} />`
- Toast notifications for non-blocking errors (failed acknowledge, failed order placement)

### Empty States

- Create `components/ui/empty-state.tsx` — standard empty state: icon, title, description, optional action button
- Pattern: `if (data.length === 0) return <EmptyState title="No positions" description="..." />`
- Every table, list, and grid MUST show an empty state — not a blank area
- Empty states should be contextual: "No alerts — all systems normal" (positive), "No orders yet — place your first
  trade" (actionable)

### Access Denied States

- Client persona navigating to a service they lack entitlements for: show "Upgrade" card with service description and
  "Contact Sales" button — NOT a 403 or blank page
- Non-admin accessing /admin: redirect to /dashboard

### WebSocket Disconnection

- Subtle banner "Reconnecting..." when WebSocket disconnects
- Auto-reconnect with exponential backoff (1s, 2s, 4s, max 30s)
- On reconnect, refetch latest data to catch up on missed ticks

---

## Responsive Layout (MANDATORY for Demo)

Primary target is desktop (1440px+), but demo MUST be presentable on:

- **Laptop** (1280px): All content visible, may scroll instead of side-by-side panels
- **Tablet** (768px-1024px): Lifecycle nav collapses to hamburger. Global scope filters stack vertically. Tables use
  horizontal scroll. Charts resize.
- **Below 768px**: Not required — show "Best viewed on desktop" message

### Key Responsive Rules

- Lifecycle nav: desktop = full horizontal bar; tablet = hamburger with slide-out drawer
- Global scope filters: desktop = inline in nav center; tablet = collapsible filter panel below nav
- Trading Terminal: desktop = chart + order book + order form side-by-side; tablet = stacked vertically
- Data tables: always use `overflow-x-auto` wrapper — never break table layout
- Dashboard cards: desktop = 4-column grid; tablet = 2-column; mobile = 1-column
- Use Tailwind responsive prefixes (`md:`, `lg:`) — no custom media queries

---

## Latency Simulation (MANDATORY for Demo Realism)

Mock APIs returning data in <1ms makes the demo feel fake. Loading skeletons flash invisibly.

### Implementation

- Add `MOCK_LATENCY_MS` environment variable (default: 0 in CI/deterministic, 150 in interactive mode)
- In `MockDomainService`, add `await asyncio.sleep(latency_ms / 1000)` before returning data
- Latency slightly randomized: `base_ms + random.randint(0, base_ms // 2)` (e.g., 150-225ms)
- WebSocket ticks are NOT delayed (already have 500-2000ms intervals)
- POST endpoints (create order, acknowledge alert) use lower latency (50-100ms) for snappy feel
- `POST /admin/reset` has zero latency

---

## PDF/CSV Report Generation (Reports Service)

Reports service MUST support downloading, not just viewing data on screen.

### CSV Export (Client-Side — All Data Tables)

- Add "Export CSV" button on every data table (P&L, settlements, orders, positions)
- Use client-side CSV generation from already-loaded data — no API endpoint needed
- Pattern: serialize visible columns → Blob → trigger download

### PDF Report (API-Side — Reports Service Only)

- "Generate PDF Report" button on P&L Attribution and Executive tabs
- API endpoint `POST /reporting/generate` accepts `{ type, client_id, date_range, format }`
- In mock mode: return a pre-generated sample PDF from `mock_data/sample_reports/`
- UX: click "Generate" → spinner → "Download Ready" toast with download link

---

## Cross-Domain Data Consistency (Seed Data Quality)

Mock data MUST be internally consistent. Inconsistencies destroy credibility in demos.

### Rules

1. **Price consistency**: OHLCV candle close prices MUST match prices used for that day's PnL calculation
2. **Reference integrity**: Every `strategy_id` in positions/orders MUST exist in strategies. Every `order_id` in fills
   MUST exist in orders. Every `org_id` MUST exist in organizations.
3. **Temporal consistency**: No position `opened_at` before strategy `inception_date`. No fills after market close. PnL
   time-series starts at strategy inception.
4. **Aggregation consistency**: Sum of position-level PnL per strategy approximately equals strategy reported PnL
5. **Batch/live consistency**: Batch = slightly stale version of live — not completely different data

### Validation

- `seed.py` MUST include `validate_consistency()` that checks all rules above
- Runs automatically after `seed_all_domains()`, raises on violation
- Agent 8's seed quality tests MUST verify consistency

---

## Codegen Pipeline Scripts (Create If Missing)

The SSOT Codegen Pipelines require scripts that may not yet exist. Agents MUST verify and create:

### Pipeline 1: UAC → UI Reference Data

- **Script**: `unified-api-contracts/scripts/generate_ui_reference_data.py`
- **If missing**: Create it — reads UAC registries (venues, instruments, enums, config schemas, error codes), outputs
  JSON consumable by UI
- **Output**: `unified-trading-system-ui/lib/registry/ui-reference-data.json`

### Pipeline 2: API → UI TypeScript Types

- **Verify**: `npm run generate:types` in `unified-trading-system-ui/package.json`
- **If missing**: Add: `"generate:types": "openapi-typescript lib/registry/openapi.json -o lib/types/api-generated.ts"`
- **Dependency**: `openapi-typescript` must be in devDependencies

### Pipeline 3: Persona Alignment

- **Script**: Create `unified-trading-api/scripts/verify_persona_alignment.py`
- **Checks**: auth-api org IDs == unified-trading-api personas.py org IDs == UI use-auth.ts persona names

---

## Code Splitting & Performance (ONE UI Consolidation)

Consolidating 13 UIs into one creates bundle size risk. Mitigate:

- Use Next.js `dynamic()` imports for heavy components (charting libraries, data grids, deployment forms)
- Each service area's page components should be lazily loaded
- Charts (candlestick, equity curve, heatmap) MUST use dynamic imports with `ssr: false`
- Target: initial bundle < 500KB, per-service chunks < 200KB each
- Verify with `NEXT_PUBLIC_MOCK_API=true npx next build` — check output for chunk sizes

---

## Agent Completion Protocol (MANDATORY after every todo)

Every agent MUST follow this protocol after completing work:

1. **TICK THE PLAN** — Change `- [ ]` to `- [x]` in the plan file for completed todos.

2. **RUN TESTS** — `bash scripts/quality-gates.sh` in every repo modified. If a test breaks:
   - Test logic WRONG (tests old pattern your refactor correctly replaced) → fix the test
   - Test logic RIGHT (catches real bug in refactor) → fix the refactor, not the test
   - The refactor plan is canonical, but tests provide quality guidance you MUST respect.

3. **HARDEN THE RULES** — Prevent future agents from undoing your work:
   - Deleted route? Add to `redirects_only` in next.config.mjs with comment explaining why.
   - Created new pattern? Add architectural comment at top of file.
   - Wired orphaned component? Remove from `orphaned_components_to_wire` in manifest.
   - Added API endpoint? Run `npm run generate:types` to update TypeScript types.

4. **UPDATE THE MANIFEST** — `UI_STRUCTURE_MANIFEST.json`:
   - Change page states (STUB → REAL), update line counts, add API hooks.
   - Remove completed items from `routes_to_delete`, `orphaned_components_to_wire`, `dead_tab_sets`.

5. **UPDATE DOCS** — If your change affects architecture: update CODEBASE_STRUCTURE.md, ROUTES.md,
   SERVICE_COMPLETION_STATUS.md, or repo-level CLAUDE.md/.cursorrules as needed.

6. **COMMIT WITH CONTEXT** — Every commit message must explain WHY and reference the plan todo ID.

---

## Cross-Agent Interface Contracts (BINDING — All Agents Must Follow)

These are the exact names, shapes, and conventions that multiple agents depend on. If any agent deviates, the
integration breaks silently. Treat these as immutable contracts.

### MockStateStore Collection Names (Agent 5 creates, Agent 6 seeds, Agents 2-4/7 read via API)

```
# Live collections (mutable, persisted to .local-dev-cache/)
# Updated by WebSocket ticks, manual actions, alert engine
positions_live, orders_live, fills_live, tickers_live, pnl_live,
alerts_live, risk_live, pnl_timeseries_live,
candles_1m, candles_5m, candles_1h, candles_1d,

# Shared collections (same in live and batch — reference data, not time-varying)
strategies, strategy_configs, organizations, clients,
ml_models, ml_experiments, ml_features, ml_training_jobs,
invoices, documents, services_health, fee_schedules,
mandates, users, compliance_rules, news, audit_trail, batch_jobs,

# Batch collections (immutable T+1 reconciled snapshots, re-seeded on reset)
# >90% same data shape as live — only storage differs
positions_batch, orders_batch, fills_batch, tickers_batch,
pnl_batch, pnl_timeseries_batch,
alerts_batch, risk_batch
```

**Key principle:** Every domain that has time-varying data gets both `_live` and `_batch` variants. The API service
layer code is >90% identical — same filtering, pagination, org-scoping, aggregation. The ONLY branching is which
collection to read from based on the `mode` query param. No mode-specific business logic.

### Org IDs (Agent 6 defines in personas.py, auth-api must match, UI must match)

```
odum-internal   — Odum Internal (admin + internal-trader personas)
acme            — Alpha Capital (client-full persona)
vertex          — Vertex Partners (client-premium persona)
beta            — Beta Fund (client-data-only persona)
```

### Persona Names (must be identical across auth-api, unified-trading-api, UI)

```
admin           — org: odum-internal, entitlements: ["*"]
internal-trader — org: odum-internal, entitlements: ["platform", "wildcard"]
client-full     — org: acme, entitlements: ["data", "research", "trading", "execution", "observe", "reports"]
client-premium  — org: vertex, entitlements: ["data", "execution", "research"]
client-data-only — org: beta, entitlements: ["data"]
```

### WebSocket Message Format (Agent 5 sends, Agent 2 consumes)

```jsonc
// Client → Server (subscribe)
{ "action": "subscribe", "channel": "market-data", "instruments": ["BTC-USDT", "ETH-USDT"] }

// Client → Server (unsubscribe)
{ "action": "unsubscribe", "channel": "market-data", "instruments": ["BTC-USDT"] }

// Server → Client (tick)
{ "channel": "market-data", "type": "tick", "data": {
    "instrument": "BTC-USDT", "price": 67234.50, "volume": 1.23,
    "bid": 67230.00, "ask": 67239.00, "timestamp": "2026-03-22T14:30:00Z"
}}

// Server → Client (alert)
{ "channel": "alerts", "type": "new_alert", "data": {
    "id": "alert-001", "severity": "high", "message": "...", "timestamp": "..."
}}
```

### API Query Params for Batch/Live (Agent 5 implements, Agents 2-4/7 send from UI)

```
GET /positions/active?mode=live                    → reads positions_live
GET /positions/active?mode=batch&as_of=2026-03-21  → reads positions_batch
GET /analytics/timeseries?mode=live                → reads pnl_timeseries_live
GET /analytics/timeseries?mode=batch               → reads pnl_timeseries_batch
```

Default (no mode param) = live. The UI sends the mode from `useGlobalScope().scope.mode`.

### Skeleton Component Names (Agent 1 creates, Agents 2-4/7 import)

```
components/ui/table-skeleton.tsx      — export TableSkeleton({ rows?: number, columns?: number })
components/ui/card-grid-skeleton.tsx   — export CardGridSkeleton({ cards?: number })
components/ui/chart-skeleton.tsx       — export ChartSkeleton({ height?: number })
```

### Debug Footer Props (Agent 1 creates, used in unified-shell.tsx)

```tsx
// The debug footer reads from these sources:
const { user } = useAuth(); // persona name, org
const { scope, setMode } = useGlobalScope(); // live/batch mode
const mockMode = process.env.NEXT_PUBLIC_MOCK_API === "true";

// Reset Demo calls:
// 1. POST /admin/reset (API — clears MockStateStore)
// 2. resetDemo() from lib/reset-demo.ts (UI — clears local state)
// 3. router.refresh() (reloads current page data)
```

### Entitlement Checks (All UI agents must use this pattern)

```tsx
// In any service page that needs entitlement gating:
const { hasEntitlement } = useAuth();
if (!hasEntitlement("execution")) return <UpgradeCard service="Execution" />;
```

---

## Full Instrument Coverage (MANDATORY — Use the Entire Registry)

The system has **128 venues** in UAC and **50+ representative instruments** in
`unified-api-contracts/registry/representative_sample.py`. The mock generators and seed data MUST cover ALL instruments
the registry provides — not an arbitrary subset of 10.

### What Actually Exists in `representative_sample.py` (verified 2026-03-22)

- 7 CeFi spot (Binance BTC/ETH/SOL, Coinbase BTC, Bybit ETH, OKX BTC, Upbit BTC)
- 6 CeFi perpetuals (Binance-Futures, Deribit, Hyperliquid, OKX, Bybit, Aster)
- 1 CeFi futures config (Deribit BTC — generates dated futures dynamically)
- 4 TradFi equities (AAPL, QQQ, GLD, VIX)
- 3 TradFi futures (ES, ZB, ZN — CME/ICE)
- 18 DeFi instruments (Aave V3 aTokens+debtTokens, Compound V3, Uniswap V2/V3/V4, Lido, EtherFi, Morpho, Curve, Ethena,
  Euler)
- 4 Sports instruments (Polymarket prediction markets, Betfair exchange odds, Pinnacle fixed odds)
- Options chain config (Deribit BTC — generates strikes/expiries dynamically from ref_date)

### SSOT Chain

1. **UAC `representative_sample.py`** — Layer 1 deterministic instrument specs. This is the SSOT for what instruments
   exist. **Seed generators MUST import from this file, not hardcode instrument lists.**
2. **`generate_ui_reference_data.py`** — syncs UAC registries (venues, instruments, enums, capabilities) to
   `ui-reference-data.json` (2,297 lines, already generated).
3. **`seed.py`** — imports `CEFI_SPOT_SPECS`, `CEFI_PERPETUAL_SPECS`, `TRADFI_EQUITY_SPECS`, `TRADFI_FUTURES_SPECS`,
   `DEFI_INSTRUMENT_SPECS`, `SPORTS_INSTRUMENT_SPECS` from `representative_sample` and generates candles, tickers,
   positions for ALL of them programmatically. If UAC registry expands, seed expands automatically — no seed.py change.
4. **UI** — reads `ui-reference-data.json` for dropdowns, selectors, and validation.

### What This Means for Each Agent

- **Agent 5/6**: Seed candles, tickers, and order books for ALL instruments in representative_sample.py — not a
  hardcoded list of 10. Use the registry programmatically:
  `from unified_api_contracts.registry.representative_sample import ...` The seed generator iterates ALL spec lists. If
  a new instrument is added to UAC, it appears on next `POST /admin/reset`.
- **Agent 2**: Instrument selector on Trading Terminal must list ALL instruments from ui-reference-data.json.
- **Agent 8**: After Agents 5-6 finish, re-run `generate_ui_reference_data.py` to sync any registry changes to the UI.

---

## 50+ Strategy Expansion (MANDATORY — Config-Driven, Not Code-Path-Driven)

Currently 18 strategies are seeded. The codex documents **13 code-complete archetypes + 4 documented-only** across
CeFi/TradFi/DeFi/Sports. We MUST expand to **50+ strategies** using representative combinations.

### Expansion Approach (Config, Not Code — CRITICAL DISTINCTION)

The system is designed so that strategies are **config, not code**. The `EventDrivenStrategyEngine` in strategy-service
is parameterised by subscription config (see `/codex/09-strategy/cross-cutting/config-architecture.md`). Each strategy
is a config entry defining: archetype, asset_group, instruments[], trigger subscriptions, risk_limits. Expanding to 50+
strategies means adding config entries and seeding matching data — **NOT adding new strategy engine code paths**.

This is NOT 10x the strategy-service work. It is expanding the config registry + seed data.

### Existing Code-Complete Archetypes (from codex/09-strategy/)

| Archetype       | CeFi                       | TradFi                   | DeFi                    | Sports                    | Status        |
| --------------- | -------------------------- | ------------------------ | ----------------------- | ------------------------- | ------------- |
| Momentum        | cefi_momentum.py           | —                        | —                       | —                         | Code complete |
| Mean Reversion  | mean_reversion_strategy.py | —                        | —                       | —                         | Code complete |
| ML Directional  | —                          | tradfi_ml_directional.py | —                       | ml_sports_strategy.py     | Code complete |
| Options ML      | —                          | options_ml_strategy.py   | —                       | —                         | Code complete |
| Basis Trade     | —                          | —                        | defi_basis.py           | —                         | Code complete |
| Staked Basis    | —                          | —                        | defi_staked_basis.py    | —                         | Code complete |
| Recursive Basis | —                          | —                        | defi_recursive_basis.py | —                         | Code complete |
| AAVE Lending    | —                          | —                        | defi_lending.py         | —                         | Code complete |
| Arbitrage       | —                          | —                        | —                       | arbitrage_strategy.py     | Code complete |
| Value Betting   | —                          | —                        | —                       | value_betting_strategy.py | Code complete |
| Market Making   | Documented                 | Documented               | Documented              | Documented                | Config only   |
| AMM LP          | —                          | —                        | Documented              | —                         | Config only   |

**Target 50+ by combining:**

| Archetype       | CeFi   | TradFi | DeFi   | Sports | Prediction | Total  |
| --------------- | ------ | ------ | ------ | ------ | ---------- | ------ |
| Market Making   | 3      | 2      | 2      | 2      | 1          | 10     |
| ML Directional  | 3      | 2      | 1      | 2      | 1          | 9      |
| Momentum        | 2      | 2      | 1      | —      | —          | 5      |
| Mean Reversion  | 2      | 1      | 1      | —      | —          | 4      |
| Basis Trade     | 2      | —      | 2      | —      | —          | 4      |
| Statistical Arb | 2      | 2      | —      | —      | —          | 4      |
| Yield           | —      | —      | 3      | —      | —          | 3      |
| Arbitrage       | 1      | —      | 1      | 2      | 1          | 5      |
| Options         | 1      | 2      | —      | —      | —          | 3      |
| Value Betting   | —      | —      | —      | 3      | —          | 3      |
| **Total**       | **16** | **11** | **11** | **9**  | **3**      | **50** |

### What This Means for Each Agent

- **Agent 6**: Expand `seed.py` strategies from 18 to 50+ using this matrix. Each strategy gets: name (following
  `{CATEGORY}_{INSTRUMENT}_{ARCHETYPE}_{MODE}_{TIMEFRAME}` convention), org_id, PnL time-series, positions, orders.
- **Agent 6**: Update `strategy-registry.ts` to include all 50+ strategies with proper archetype/category metadata.
- **Agent 5**: No API changes needed — strategies are data, not endpoints.
- **Agent 3**: Strategy comparison and backtest pages should handle 50+ strategies (virtualized tables if needed).

### SSOT Alignment Required

- `unified-trading-codex/09-strategy/` documents all archetypes — verify registry covers all documented types.
- `unified-api-contracts` strategy type enums must include all archetypes.
- `unified-internal-contracts` strategy schemas must support all execution modes.
- `strategy-registry.ts` (1,863 lines) must be updated to include all 50+ strategies.

---

## Technical Indicators on Candlestick Charts (lightweight-charts)

**lightweight-charts v5.1.0** (by TradingView) is already installed. It natively supports overlay series for technical
indicators. Do NOT rebuild indicator math from scratch — use existing open-source finance libraries.

### Implementation

- **Library**: Use `lightweight-charts` built-in `addLineSeries()` for overlay indicators on the candlestick chart.
- **Indicator computation**: Use a lightweight client-side library (e.g., `technicalindicators` npm package, or compute
  from OHLCV data directly — SMA/EMA are trivial).
- **Required indicators** (toggleable via toolbar above chart):
  - SMA (Simple Moving Average) — 20, 50, 200 period
  - EMA (Exponential Moving Average) — 12, 26
  - Bollinger Bands — 20 period, 2 std dev
  - Volume bars (already implemented via histogram series)
- **Nice-to-have** (Phase 2):
  - RSI (separate pane below chart)
  - MACD (separate pane below chart)
- **Indicator toolbar**: Row of toggle buttons above chart: `[SMA] [EMA] [BB] [RSI] [MACD] [Vol]`
- **DEPENDENCY**: Agent 2 implements. Requires Agent 6's OHLCV candle data (200+ candles per instrument).

---

## TanStack Table for Institutional Blotters (MANDATORY)

The current shadcn `<Table>` is semantic HTML only — no column reordering, no virtualization, no persistence. Every data
table in the platform MUST use TanStack Table for institutional-grade blotter UX.

### Requirements

- **Install**: `npm install @tanstack/react-table @tanstack/react-virtual`
- **Create**: `components/ui/data-table.tsx` — reusable wrapper around TanStack Table with:
  - Column sorting (click header to sort)
  - Column visibility toggle (hide/show columns via dropdown)
  - Column resizing (drag column borders)
  - Row virtualization for 1000+ rows (via @tanstack/react-virtual)
  - Persistent column preferences (save to Zustand `ui-prefs-store.ts` → localStorage)
- **Apply to**: ALL data tables across all services (positions, orders, fills, alerts, settlements, users, experiments,
  backtests, audit trail, deployment history)
- **DEPENDENCY**: Agent 1 creates the `data-table.tsx` component (Phase 5). Agents 2-4, 7 adopt it for their tables.

---

## Workspace Layout Persistence

Zustand `ui-prefs-store.ts` already exists with sidebar collapse and theme preferences. Extend it for workspace
persistence:

### Requirements

- **Filter persistence**: Global scope filters (org, client, strategy, mode) persist to localStorage via Zustand
  `persist` middleware. When user reloads, filters are restored.
- **Column preferences**: Per-table column visibility and order saved to localStorage (via TanStack Table + Zustand).
- **Panel sizes**: `react-resizable-panels` (already installed) sizes persist to localStorage.
- **DEPENDENCY**: Agent 1 extends `ui-prefs-store.ts` (Phase 5). Other agents wire their components to it.

---

## Guided Tour / Onboarding Walkthrough

First-time users (especially demo clients) need a guided tour highlighting key features.

### Requirements

- **Install**: `npm install react-joyride` (or equivalent)
- **Create**: `components/platform/guided-tour.tsx` — wraps react-joyride with platform-specific steps.
- **Tour steps** (triggered on first login or via "Take Tour" button in debug footer):
  1. Global scope filters — "Filter all data by organization and strategy"
  2. Lifecycle navigation — "Navigate the full trading lifecycle: Acquire → Build → Run → Execute → Observe"
  3. Trading Terminal — "Real-time prices, order entry, and position management"
  4. Command Palette — "Press Cmd+K to search anything"
  5. Batch/Live toggle — "Switch between real-time and reconciled historical data"
  6. Reset Demo — "Reset all data to initial state"
- **Persistence**: Tour completion saved to localStorage. Don't show again unless "Take Tour" clicked.
- **DEPENDENCY**: Agent 1 creates (Phase 5, after navigation is finalized). No upstream blockers.

---

## Desktop Notifications & Sound Alerts

### Requirements

- **Browser Notification API**: Request permission on first login. For critical/high severity alerts, push a desktop
  notification (even when tab is not focused).
- **Sound**: Subtle audio ping for critical alerts (use Web Audio API or a small .mp3). Configurable in ui-prefs-store.
- **Toast notifications** (Sonner — already installed): Wire for ALL mutation responses:
  - Order placed → success toast
  - Alert acknowledged → success toast
  - Report generated → "Download Ready" toast with link
  - Reset Demo → "Demo reset to initial state" toast
  - Any API error → error toast with message
- **DEPENDENCY**: Agent 1 wires Sonner toasts + notification permission (Phase 5). Agent 2 wires for trading mutations.
  Agent 5 must have alert endpoints working.

---

## Excel Export (XLSX)

CSV is insufficient for institutional clients. Every data table MUST support Excel export.

### Requirements

- **Install**: `npm install xlsx` (SheetJS — MIT licensed, client-side)
- **Create**: `lib/utils/export.ts` with `exportTableToXlsx(data, columns, filename)` alongside existing
  `exportTableToCsv()`.
- **Every "Export CSV" button** becomes a split button: `[Export ▾]` → dropdown with "CSV" and "Excel" options.
- **Excel formatting**: Headers bold, number columns right-aligned, date columns formatted, sheet name = table title.
- **Reports Excel**: Multi-sheet workbook — P&L Attribution on sheet 1, positions on sheet 2, orders on sheet 3.
- **DEPENDENCY**: Agent 2 creates `export.ts` utility (Phase 7). All agents use it for their tables.

---

## Print-Optimized Reports

Reports service pages MUST be printable for client distribution.

### Requirements

- **Print CSS**: Add `@media print` styles in `globals.css`:
  - Hide navigation, debug footer, filters, buttons
  - Full-width tables with borders
  - Page breaks between sections (`break-before: page`)
  - Company logo header + timestamp footer on each page
  - Charts rendered at print resolution
- **"Print Report" button**: On P&L Attribution and Executive tabs, next to "Generate PDF". Calls `window.print()`.
- **DEPENDENCY**: Agent 4 implements (Phase 7). No upstream blockers.

---

## Separation of Concerns (MANDATORY — All Agents)

The UI should NEVER do service logic. Everything demonstrable in the UI must also be achievable via API/service calls
(scripts, CLI, curl). The backend must be complete enough that the frontend is purely visual.

### Layer Responsibilities

| Layer                                                         | Responsible For                                                        | NOT Responsible For                                              |
| ------------------------------------------------------------- | ---------------------------------------------------------------------- | ---------------------------------------------------------------- |
| **UAC Registry** (`representative_sample.py`)                 | Instrument specs, venue capabilities, enums                            | Seed data, API routes, UI rendering                              |
| **Service Engine** (strategy-service, execution-service etc.) | Strategy logic, PnL calculation, risk assessment                       | HTTP, WebSocket, UI rendering                                    |
| **Mock Service Layer** (`MockDomainService`)                  | Same filtering/pagination/PnL-recalc as real, backed by MockStateStore | UI components, client-side computation                           |
| **API Routes** (`unified-trading-api`)                        | HTTP surface, WebSocket emission, auth, org-scoping                    | Business logic (delegate to service layer)                       |
| **UI** (`unified-trading-system-ui`)                          | Visual rendering, chart overlays, indicator math, export formatting    | Data generation, PnL calculation, filtering logic, mock fixtures |

### The Curl Test

**If you can't demonstrate a feature by running a `curl` command against the API, the logic is in the wrong layer.**

Examples:

- PnL calculation: `curl /analytics/pnl` must return correct PnL — NOT computed in the UI from raw positions
- Org filtering: `curl /positions/active -H "Authorization: Bearer {client_token}"` must return only that client's data
- Strategy list: `curl /analytics/strategies` must return all 50+ strategies — NOT hardcoded in `trading-data.ts`
- Batch/live switch: `curl /positions/active?mode=batch` vs `curl /positions/active?mode=live` must return different
  data

### No Two Sources of Truth for Service Logic

- If the UI has a `lib/trading-data.ts` that generates strategies client-side, AND the API has `seed.py` that generates
  strategies server-side — that is TWO sources of truth. Delete the client-side one. The UI calls the API.
- If the UI computes PnL from positions client-side, AND the API recalculates PnL server-side — the UI version must be
  deleted. The UI renders what the API returns.
- If the UI has MSW handlers that return mock data, AND the API has MockDomainService — MSW must be removed. One mock
  source: the API service layer.

### Missing Service Functionality

If a feature is needed for the demo and the service engine doesn't support it:

1. **Check if the service exists** — it probably does (67 repos covering every domain)
2. **Add the feature to the existing service** — don't work around it
3. **If the service's mock_mode provider is missing the feature** — add it to the mock provider in that service
4. **The unified-trading-api MockDomainService** is a gateway-level mock. It reads from MockStateStore which is seeded
   with data that represents what the real services would return. It does NOT replace the services — it simulates their
   output for the demo.

---

## Data Freshness Indicators (MANDATORY for Production Feel)

Production trading systems always show data staleness. This is critical for the batch/live story — WebSocket-fed panels
should be visually distinct from batch data panels.

### Implementation

- Create `components/ui/data-freshness.tsx`:
  - Shows "Updated Xs ago" or "Live" badge based on `lastUpdated` timestamp
  - Green dot: < 5s (or WebSocket-connected)
  - Yellow: 5-30s
  - Red: > 30s or disconnected
- Render on every data panel header that uses real-time or recently-fetched data
- WebSocket-fed panels (Trading Terminal, Positions, Dashboard PnL): show "Live" with green dot
- REST-fetched panels (Reports, Manage): show relative timestamp from last successful React Query fetch
- Batch mode panels: show "As of {date}" badge (no staleness indicator — batch is a snapshot by definition)

---

## Key Technical Rules

- `uv pip install` not `pip install`
- `bash scripts/quality-gates.sh` for tests (never pytest directly)
- `bash scripts/quickmerge.sh "message" --agent` for commits (never git push directly)
- `basedpyright` not `pyright`
- No `os.getenv()` — use `UnifiedCloudConfig`
- Flat deps only in pyproject.toml (no optional-dependencies)
- Each repo has its own .venv for quality gates

---

## Gap Classification Framework (Added 2026-03-22)

Every missing demo capability falls into ONE of three categories. Agents MUST identify the category BEFORE writing code,
because the fix location differs:

| Category                             | Meaning                                | Fix Location                                                                      |
| ------------------------------------ | -------------------------------------- | --------------------------------------------------------------------------------- |
| **Type 1: Service Missing**          | No service implements this             | Add to real service repo                                                          |
| **Type 2: UI Visualization Missing** | Service has it, UI doesn't show it     | UI components + API hooks. If API doesn't proxy, add MockDomainService simulation |
| **Type 3: Not Mockable**             | Service has it, mock can't simulate it | Add mock simulation in MockDomainService using seeded data                        |

**Full gap analysis:** `.cursor/plans/GAP_CLASSIFICATION_2026_03_22.md`

### Key Findings (2026-03-22 Service Audit)

Services that have RICH functionality the UI plans didn't originally cover:

- **risk-and-exposure-service**: VaR (6 methods), stress scenarios (GFC/COVID/Crypto), correlation matrix, regime
  detection, 6-check pre-trade engine, delta-gamma VaR, DeFi reconciliation
- **execution-service**: PreTradeRiskEngine, 7 execution algos, 3-state circuit breaker, kill switch, drain mode, MiFID
  II/FCA compliance, OptionsComboHandler
- **features-volatility-service**: Black-Scholes + Black-76 Greeks, GEX, vol surface (ATM/skew/butterfly/term
  structure), realized vol (Parkinson/Yang-Zhang)
- **strategy-service**: 25+ code-complete strategies, 5-dim signal vector, options ML (3 prediction types), risk monitor
  (Aave health factor)
- **position-balance-monitor-service**: Portfolio Greeks aggregation (delta/gamma/theta/vega/rho)

**The only Type 1 gap (genuinely missing):** FX conversion / multi-currency. Trivial to mock with static rates.
Everything else is Type 2 (UI gap) or Type 3 (mock gap) — the real services already have the functionality.
