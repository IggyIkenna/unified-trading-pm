---
doc_type: issue
title: DART manual-trade UI — 5-surface MVP build (master Group G Item 23)
summary:
status: resolved
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [execution-service, strategy-service, unified-api-contracts, unified-trading-pm, unified-trading-system-ui]
scope: [engineer, admin]
tags: []
related: []
created: 2026-05-10
author: agent-dart-mvp
source:
  [
    unified-trading-pm/plans/active/cross_cutting_may_23_deliverables_2026_05_08.md (Phase 4 BUILD scope),
    unified-trading-pm/plans/archive/2026_07/master_to_live_defi_2026_05_23.md (Group G Item 23),
    unified-trading-pm/codex/09-strategy/architecture-v2/cross-cutting/dart-manual-trade-spec.md,
    unified-trading-pm/codex/09-strategy/architecture-v2/cross-cutting/operational-modes-matrix.md,
    execution-service/execution_service/api/manual_instruction_api.py (existing 682-line backend),
    execution-service/execution_service/api/preview_routes.py (existing 320-line backend),
    unified-trading-system-ui/app/(platform)/services/dart/locked/page.tsx (UI stub),
  ]
locked_by: live-defi-rollout
locked_since: 2026-05-10
execution:
  {
    owner: cross_cutting_may_23_deliverables Phase 4 — daily Tab assignment in next work-split,
    cadence: one-shot (build-out) + per-PR (regression smokes once shipped),
    verifier:
      Playwright e2e `dart-manual-trade-flow.spec.ts` GREEN against mock-API + integration smoke against Tier-2 stack,
    last_executed: NEVER,
  }
---

# DART manual-trade UI — 5-surface MVP build (master Group G Item 23)

> **Severity**: P0 — May-23 cutover deadline critical path; Group G operator-UX prerequisite for live trading. **Blast
> radius**: unified-trading-system-ui (~10-15 new files), execution-service (3 endpoints already shipped, need
> verification + tests), strategy-service (1 new endpoint + 1 new UAC type), unified-api-contracts (operational-mode
> facade re-export). **Suggested owner**: next daily work-split Phase 4 — beefier Tab on Ikenna side because design
> spans 4 repos (UI + 2 services + UAC).

## What I found (build-readiness audit 2026-05-10)

This issue captures the full work needed for master Group G Item 23 — the DART manual-trade gate. An agent attempted the
build in a single session but discovered:

1. **Backend execution-service scaffolding is already extensive and shipped.**
   - `execution-service/execution_service/api/manual_instruction_api.py` (682 lines) — `/manual` router with
     `POST /manual/submit`, amend, cancel handlers. Uses `LiveOrchestrator.execute(instruction: StrategyInstruction)` —
     same path as automation per the "Batch = Live" rule.
   - `execution-service/execution_service/api/preview_routes.py` (320 lines) — `/preview` router for risk + slippage
     preview.
   - `execution-service/execution_service/api/manual_schemas.py` (107 lines) — `ManualInstructionRequest` /
     `ManualInstructionResponse` / `AmendInstructionRequest` / `CancelInstructionRequest` Pydantic models.
   - `ManualOperationHandler` (`execution_service/operations/manual.py`) owns lazy-init of per-venue orchestrators.
   - Auth via `GoogleOIDCAuth` + slowapi rate limiter pattern already wired.

   **The `POST /api/dart/manual-trade` and `POST /api/dart/preview` endpoints I was asked to build already exist as
   `POST /manual/submit` and `POST /preview/*`.** No new backend route files needed; the UI calls the existing routes.
   **VERIFIED-NOT-BUILT-FROM-SCRATCH.**

2. **Strategy-service has NO operational-mode endpoint.**
   - `strategy-service/strategy_service/api/main.py` (93 lines) wires `make_health_router` + `make_sse_router` +
     `restriction_profile_router` + `registry_router` + signal-broadcast router.
   - **No `POST /api/archetypes/{id}/operational-mode` endpoint exists.** This is the manual→DART→automated flip
     switch's backend dependency — must be built.
   - `OperationalMode` enum DOES exist in UAC at `unified_api_contracts.internal.OperationalMode` (LIVE / MANUAL /
     BACKTEST / PAPER). Use this; do NOT invent a new enum.

3. **UI surface is a stub — no DART terminal exists.**
   - `unified-trading-system-ui/app/(platform)/services/dart/` has ONLY `locked/page.tsx` (the upgrade-to-DART-Full
     paywall) plus dashboard tile metadata referencing the route key `dart-terminal`.
   - **No `app/(platform)/services/dart/terminal/page.tsx` route file exists.** The "stub" referenced in the master plan
     refers to the route KEY in dashboard metadata, not an actual route file.
   - `components/dart/strategy-param-version-bump-modal.tsx` exists (a single modal for param version bumps).
   - **No ManualTradeForm / TradePreview / ExecutionDispatch / TradeMonitor / AutomationToggle components exist
     anywhere.**

4. **Critical UI integration patterns are foreign-owned and parallel-agent-active.**
   - Widget pattern (`useAssetGroupData` hook, `WidgetComponentProps`, mock-handler integration via
     `lib/api/mock-handler.ts`, persona authorization via `DemoPlanToggle`, Firebase emulator wiring under
     `app/(platform)/services/`, Tier 0/1/2 mode axes via `VITE_MOCK_API`/`VITE_SKIP_AUTH` envvars) is extensive.
   - Touching these without the deep ownership context of the `unified-trading-system-ui` repo (~13 UIs, 5+ widget
     conventions, persona-based ACL on every route, Firebase + mock-API dual-layer) carries high foreign-edit risk per
     CLAUDE.md "Two teammates × multiple parallel agents" rule.
   - Single-session build by an agent unfamiliar with these conventions would create a hollow MVP that drifts from
     existing patterns and requires rework.

## Why it matters

- **May-23 deadline critical.** Item 23 is the last Group G operator-UX prerequisite. Without it, operator cannot
  manually first-trade an archetype before flipping to automation — the gate is undefined.
- **Backend is half-shipped already.** Every day that passes without UI integration, the existing `/manual` + `/preview`
  routes drift further from any consumer (risk of the same rot pattern as `colocated_engine.py:306` per the runbook
  governance issue doc).
- **Strategy-service operational-mode endpoint is a hard prerequisite** for the AutomationToggle surface. Without
  shipping the endpoint, the whole flip-switch UX is blocked.
- **Per "Batch = Live" rule the manual path MUST go through `LiveOrchestrator.execute(StrategyInstruction)` — same code
  path as automation.** Existing backend already does this; UI must NOT build a parallel path.

## Recommended decision (full spec — paste-ready for next work-split tab)

### Phase A — Strategy-service operational-mode endpoint (~0.5 AI-day, single-repo, crisp)

Owner: Harsh-side spawn or Ikenna inline.

1. **UAC** — re-export `OperationalMode` from `unified_api_contracts.internal` via the strategy facade if needed by the
   route (verify import path; existing `from unified_api_contracts.internal import OperationalMode` already works for
   service-internal use).

2. **strategy-service** — author `strategy_service/api/operational_mode_router.py`:

   ```python
   from fastapi import APIRouter, HTTPException, Path
   from pydantic import BaseModel
   from unified_api_contracts.internal import OperationalMode
   from strategy_service.config import get_config

   class OperationalModeRequest(BaseModel):
       mode: OperationalMode

   class OperationalModeResponse(BaseModel):
       archetype_id: str
       previous_mode: OperationalMode
       new_mode: OperationalMode
       transition_at: str  # ISO 8601

   def make_operational_mode_router() -> APIRouter:
       router = APIRouter(prefix="/api/archetypes", tags=["operational-mode"])

       @router.post("/{archetype_id}/operational-mode", response_model=OperationalModeResponse)
       async def set_operational_mode(
           archetype_id: str = Path(..., min_length=1),
           request: OperationalModeRequest,
       ) -> OperationalModeResponse:
           # 1. Load archetype config from registry (existing registry_router pattern)
           # 2. Validate transition: MANUAL→DART→LIVE allowed; LIVE→MANUAL allowed (kill-switch path)
           # 3. Persist new mode to archetype config (Firestore / GCS — match existing registry write pattern)
           # 4. Emit OPERATIONAL_MODE_CHANGED event via log_event for audit trail
           # 5. Return prev/new/timestamp
           ...
       return router
   ```

3. **strategy-service** — wire `app.include_router(make_operational_mode_router())` in `api/main.py:create_app()`
   alongside the existing routers.
4. **Tests** — `strategy-service/tests/unit/test_operational_mode_router.py` covering: valid transition, invalid
   transition (e.g. MANUAL→LIVE without DART intermediate), 404 for unknown archetype, audit event emitted.
5. **Quality gate** — `cd strategy-service && bash scripts/quality-gates.sh` GREEN.

### Phase B — Verify + harden existing execution-service `/manual` + `/preview` routes (~0.25 AI-day)

Owner: same tab as Phase A or parallel.

1. Read `manual_instruction_api.py` + `preview_routes.py` end-to-end; verify they accept the `StrategyArchetype` axis
   from UAC `ARCHETYPE_CAPABILITY_REGISTRY` (the `(archetype_id, venue, side)` triple the UI form will submit).
2. Add `GET /api/dart/instructions/{id}/status` endpoint if not already covered — this is the TradeMonitor poll path.
   Likely lives in `manual_instruction_api.py` as a new route or in a new `instructions_status_routes.py`.
3. Quality gate `cd execution-service && bash scripts/quality-gates.sh` GREEN.
4. **No backend rename** — UI consumes existing `/manual/submit` + `/preview/*` routes. The earlier task brief's
   `/api/dart/manual-trade` naming was wrong; the routes already exist under `/manual` + `/preview` and renaming would
   bundle a strategy-service-style refactor across consumers.

### Phase C — UI 5-surface MVP (~3-4 AI-days, requires deep UI repo familiarity) — **PARTIAL-RESOLVED-VIA-OPTION-C 2026-05-10 (unified-trading-system-ui@`64660edd`)**

> **Status update 2026-05-10:** A narrow option-c slice shipped — the 2 genuinely greenfield surfaces (`TradeMonitor` +
> `AutomationToggle`) plus a thin DART terminal landing page that links to the **existing** `manual-trading-panel` Sheet
> (`unified-trading-system-ui/components/trading/manual/{manual-trading-panel,single-order-form,mass-quote-panel}.tsx`,
> 1,256 lines — already shipped pre-this-task). Per CLAUDE.md "Grep-Then-Read, Not Grep-Then-Conclude" the original
> Phase C scope re-built ManualTradeForm / TradePreview / ExecutionDispatch (items 3-5 + 9-10 below) which **already
> exist** under `components/trading/manual/`; option-c skipped them and linked to the existing Sheet instead.
>
> **Shipped by `unified-trading-system-ui@64660edd`:**
>
> - `components/dart/trade-monitor.tsx` — covers item 7 below (5s polling against `/api/instructions/{id}/status`,
>   status badge, filled-qty / avg-fill-price / unrealized-P&L surfaces, last-good-snapshot preservation on transient
>   errors). 8 unit tests in `tests/unit/components/dart/trade-monitor.test.tsx`.
> - `components/dart/automation-toggle.tsx` — covers item 8 below (POST `/api/archetypes/{id}/operational-mode`, MANUAL
>   → PAPER → LIVE forward graph + LIVE → MANUAL kill-switch, surfaces server-enforced 409s verbatim, transition buttons
>   disabled during in-flight requests). 10 unit tests in `tests/unit/components/dart/automation-toggle.test.tsx`.
> - `app/(platform)/services/dart/terminal/page.tsx` — covers item 2 below in slim form (lists every archetype from
>   `ARCHETYPE_METADATA`, mounts AutomationToggle per row, renders TradeMonitor when `?instruction=<id>` URL param is
>   present, links to existing `manual-trading-panel` Sheet via `/services/trading/overview`). Persona ACL gates
>   admin/internal/client → page; everyone else punted to `/services/dart/locked?from=terminal`.
> - `tests/e2e/playbooks/dart-cockpit/phase-c-terminal-flow.spec.ts` — 5 Playwright specs covering page render,
>   archetype list, manual-trade-link route, TradeMonitor mount on URL param, locked-redirect for unauthorised personas.
>
> **Phase C remainder — explicitly DEFERRED to a dedicated successor plan** (these are NOT shipped by `64660edd`):
>
> - **Item 3 (ManualTradeForm)** + **Item 4 (TradePreview)** + **Item 5 (ExecutionDispatch)** + **Item 9
>   (lib/api/dart-client.ts)** + **Item 10 (lib/api/mocks/dart.ts)** — already exist in `components/trading/manual/`
>   (manual-trading-panel.tsx + single-order-form.tsx + mass-quote-panel.tsx). The "Phase C remainder" is a Sheet →
>   route refactor + ExecutionDispatch endpoint rename from `/preview/<archetype>` + `/manual/submit` to the
>   dart-client.ts shape. Successor plan filename: TBD — operator triages whether the existing Sheet pattern (Phase C as
>   shipped) is sufficient for the May-23 cutover. If a dedicated route surface is required, the successor plan owns the
>   refactor.
> - **Item 6 (per-instruction monitor route `/dart/terminal/[instructionId]/page.tsx`)** — current option-c renders the
>   monitor inline via `?instruction=<id>` URL param. Dedicated route is a UX-polish item, not a P0.
> - **Item 11 (`tests/e2e/dart-manual-trade-flow.spec.ts` covering full submit → preview → confirm → monitor flow
>   end-to-end)** — replaced this cycle by `phase-c-terminal-flow.spec.ts` covering the page-mount + monitor surface;
>   full-flow e2e ships with the successor plan once the Sheet → route refactor lands.
>
> **Why option-c was the right shape:** the 2026-05-08 9-agent audit ("Grep-Then-Read" reference incident #4) already
> flagged that `manual_instruction_api.py` + `preview_routes.py` + `manual_schemas.py` + `preview_schemas.py` +
> `ManualOperationHandler` were all already shipped on the backend; the Phase C original scope assumed those needed
> building. The same shape applies on the UI: `manual-trading-panel.tsx` already provides the form + preview +
> execution-dispatch surface. Option-c verified-via-grep-then-read that 5 of 11 surfaces existed; shipped only the 3
> genuinely greenfield ones. Saved ~2-3 AI-days of duplicate-effort builds per CLAUDE.md "Plans Run To Actual
> Completion" anti-pattern.

Owner: dedicated UI tab; should NOT be combined with Phase A/B due to foreign-edit risk.

**Read-first list (before any UI edit):**

- `unified-trading-system-ui/components/widgets/options/dart-options-analytics.tsx` — widget shape SSOT
- `unified-trading-system-ui/lib/hooks/use-asset-group-data.ts` — data hook pattern
- `unified-trading-system-ui/lib/api/mock-handler.ts` — mock-API integration
- `unified-trading-system-ui/lib/api/typed-fetch.ts` — typed fetch wrapper
- `unified-trading-system-ui/components/shared/error-boundary.tsx` — error boundary pattern
- `unified-trading-system-ui/components/platform/research-family-shell.tsx` — service shell pattern
- `unified-trading-system-ui/components/shell/service-tabs.tsx` — sub-route tab nav
- `unified-trading-system-ui/app/(platform)/services/execution/layout.tsx` — sibling service layout reference
- `unified-trading-system-ui/app/(platform)/services/execution/[executionId]/page.tsx` — sibling per-instance route
- Persona ACL: `lib/auth/personas.ts` (must DART-Full-gate the new routes)
- Firebase tier wiring: `unified-trading-pm/codex/14-customer-journeys/authentication/firebase-local.md`
- Mode axes: `unified-trading-pm/codex/05-infrastructure/runtime-tiers-and-deployment.md`

**File creation plan (~10-12 new files):**

1. `app/(platform)/services/dart/layout.tsx` (~20 lines) — `ResearchFamilyShell` wrapper + `DART_TABS` array.
2. `app/(platform)/services/dart/terminal/page.tsx` (~50 lines) — main terminal route, reads `?archetype=&venue=` from
   query, mounts ManualTradeForm + ActiveInstructionsList side by side.
3. `components/dart/manual-trade-form.tsx` (~150 lines) — Form fields per spec:
   - `archetype` dropdown (UAC `StrategyArchetype` enum values from a fixtures mock or registry endpoint)
   - `venue` dropdown filtered by archetype's `ARCHETYPE_CAPABILITY_REGISTRY[archetype].supported_venues`
   - `side` (LONG/SHORT toggle)
   - `size_pct_nav` (number, 0-100)
   - `limit_price` (number, optional)
   - `algo` dropdown (from `_SUPPORTED_ALGOS`: MARKET / TWAP / VWAP / ICEBERG / SOR / BEST_PRICE / BENCHMARK_FILL)
   - `dry_run` checkbox (default true)
   - Submit → calls `POST /preview/<archetype>` then routes to `/dart/terminal/preview/<correlation_id>`
4. `components/dart/trade-preview.tsx` (~120 lines) — Receives preview response, displays projected fill price /
   slippage / collateral required / max-drawdown impact / risk-check pass/fail per rule. Confirm button → calls
   `POST /manual/submit`; Cancel returns to form.
5. `components/dart/execution-dispatch.tsx` (~80 lines) — Submission glue (fetch wrapper + error handling +
   correlation_id capture). Returns instruction_id + redirects to monitor.
6. `app/(platform)/services/dart/terminal/[instructionId]/page.tsx` (~40 lines) — Per-instruction monitor route.
7. `components/dart/trade-monitor.tsx` (~150 lines) — Live status poller against
   `GET /api/dart/instructions/{id}/status` (polling at 2s while pending, 5s once filled). Displays filled qty / avg
   fill price / unrealized P&L / status badge. Subscribes to Firestore for real-time fills if available; polling
   fallback otherwise.
8. `components/dart/automation-toggle.tsx` (~80 lines) — Per-archetype toggle switch (MANUAL / DART / LIVE / PAPER).
   Calls `POST /api/archetypes/{archetype_id}/operational-mode` on change. Displays current mode + transition history
   from a server query. **MUST hard-confirm dialog before flipping to LIVE** (Group G operator-UX requirement).
9. `lib/api/dart-client.ts` (~100 lines) — Typed wrappers around the 4 backend endpoints (`/preview`, `/manual/submit`,
   `/manual/instructions/{id}/status`, `/api/archetypes/{id}/operational-mode`). Mirrors the
   `lib/api/strategy-versions.ts` shape.
10. `lib/api/mocks/dart.ts` (~150 lines) — Mock fixtures for the 4 endpoints (preview response, submit response, status
    poll, mode flip). Wired into `mock-handler.ts` so widgets render against fixtures when `VITE_MOCK_API=true`.
11. `tests/e2e/dart-manual-trade-flow.spec.ts` (~200 lines) — Playwright spec covering:
    - Form validation (size > 0, archetype required, venue must be supported by archetype)
    - Preview displays risk-check + slippage estimate
    - Confirm submits to `/manual/submit` and routes to monitor
    - Monitor renders status updates (poll-driven test against mock fixture)
    - Automation toggle confirms before flipping to LIVE
    - Persona ACL: `prospect-signals-only` cannot reach `/dart/terminal` (404 / locked redirect)
12. `tests/unit/components/dart/manual-trade-form.test.tsx` + `tests/unit/components/dart/trade-preview.test.tsx`
    - `tests/unit/components/dart/automation-toggle.test.tsx` — vitest unit tests per component.

**Persona ACL** — DART terminal route `/dart/terminal/*` MUST require DART-Full plan; non-DART personas redirect to
`/dart/locked?from=terminal`. This wiring lives in `lib/auth/personas.ts` + middleware; matches the existing
`/dart/locked` page.

**Quality gates** —

- `cd unified-trading-system-ui && CI=true npm test -- --run` GREEN
- `cd unified-trading-system-ui && VITE_MOCK_API=true npx vite build` GREEN
- `cd unified-trading-system-ui && npx playwright test tests/e2e/dart-manual-trade-flow.spec.ts` GREEN

### Phase D — Codex audit + master plan flip (~0.25 AI-day)

1. Update `unified-trading-pm/codex/09-strategy/architecture-v2/cross-cutting/dart-manual-trade-spec.md` with the
   shipped surface paths.
2. Update `unified-trading-pm/codex/09-strategy/architecture-v2/cross-cutting/operational-modes-matrix.md` with the
   shipped strategy-service `/api/archetypes/{id}/operational-mode` endpoint reference.
3. Flip master Group G Item 23 checkbox + cross_cutting Phase 4 BUILD checkboxes per `Commit + Push + Flip` HARD RULE.
4. Last-verified date update in master plan continuous-verification column.

### Why split Phases A/B (backend) from Phase C (UI) into separate work-split tabs

- Phase A/B are **single-repo, crisp boundary, foreign-edit-risk LOW** — strategy-service has minimal in-flight churn on
  the api/ surface; execution-service's `/manual` + `/preview` are live and stable.
- Phase C is **multi-component, foreign-pattern-heavy, foreign-edit-risk HIGH** — UI repo has extensive parallel-agent
  conventions (mock-handler, persona ACL, Firebase emulator, widget shell, persona toggle). A single tab unfamiliar with
  these will either misintegrate or take 2x the AI-days.
- Recommend: **Phase A+B in one tab (Tab Y on Harsh side, ~1 AI-day) → Phase C in dedicated UI tab (Tab Z on Ikenna
  side, ~3-4 AI-days, Opus full-window with read-first list above)** → Phase D either tab once both ship.

## Out-of-scope (explicit deferrals)

- **Real backend integration testing against staged secrets / Tenderly fork** — deferred to next-cycle live-trading
  rehearsal plan; the smoke harness in this plan exercises mock fixtures only. Operator first-trades will exercise real
  integration.
- **DART-Full plan billing / payment flow** — out of scope; existing `/dart/locked` upgrade page is the entry surface.
- **Multi-archetype concurrent monitor** — Phase C ships single-archetype monitor; multi-archetype dashboard is a
  post-cutover polish item.
- **Telemetry / OpenTelemetry traces for the manual-trade path** — covered by execution-service's existing trace wiring;
  no UI-side trace work needed for MVP.

## Composes with

- `master_to_live_defi_2026_05_23.md` Group G Item 23.
- `cross_cutting_may_23_deliverables_2026_05_08.md` Phase 4 BUILD scope.
- `Two teammates × multiple parallel agents — don't edit unfamiliar files` HARD RULE — split Phase A/B (low risk) from
  Phase C (high risk).
- `Plans Run To Actual Completion` HARD RULE — Phase D's plan-flip must wait for actual Playwright GREEN against the
  shipped backend, not just code-shipped.
- `Runbook Execution-Owner SSOT` — once shipped, `dart-manual-trade-flow.spec.ts` becomes the per-PR regression smoke
  (cadence: per-PR; verifier: Playwright GREEN).
