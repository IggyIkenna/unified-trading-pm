---
title:
  "deployment-ui scope cleanup — move trading/research surfaces to unified-trading-system-ui; keep the devops pane lean"
parent_epic: deployment_and_user_management_master
assigned_vm: vm-cross-cutting
priority: P2
status: active
estimate_class: refactor
estimate_baseline_ai_days: 4.0
estimate_calibrated_ai_days: 1.6
created: 2026-06-12
source:
  - 'operator direction 2026-06-12: "deployment ui needs a cleanup — at some point confused the Unified Trading System
    UI with the Deployment UI and started building Dart stuff and ML stuff in there, which is totally pointless there.
    Figure out what it was trying to build; build it into the Unified Trading System UI; clean up the Deployment UI;
    keep CI/CD clickable through the CI/CD tab and epics via the epics tab."'
related_plans:
  - plans/active/monitoring_control_plane_master_2026_06_10.md
  - plans/active/ci_dashboard_deployment_ui_2026_06_10.md
locked_by: live-defi-rollout
locked_since: 2026-06-12
---

# deployment-ui scope cleanup — trading/research surfaces → unified-trading-system-ui

## Scope

> **REVISED 2026-06-12 (operator decision — DUAL-CUT, supersedes the incorporate-then-DELETE framing below).** The
> original framing assumed the 3 research-launch pages were pure duplicates to move out of deployment-ui. They are NOT.
> Operator clarification 2026-06-12: _"dual cut functionality when it comes to launching… launching is supposed to be
> like launching a deployment… the deploy button service is all services, so that remains the same — give it a CLI
> argument which points it to configs. That deployment UI should show that, as it already does, and machine learning and
> everything should be incorporated in that as a service that you can deploy. You've got the deployment API which does
> the backend for that — that should ALSO be facilitated to be available for the unified trading system UI so that we
> can deploy through there, where we have more of the stuff around how we configure / view results / experiments, but
> it's still hooking up to the same deployment-api backend."_ Net model:
>
> - **deployment-api** (`/api/{ml/experiment,strategy/backtest,execution/backtest}/launch` — real, tested routes in
>   `deployment_api/routes/*_launch.py`) is the single deploy/launch backend. UNCHANGED. "Launch = deploy = watch a
>   deployment"; a deploy points a CLI at configs.
> - **deployment-ui** KEEPS the 3 launch consoles (ML / strategy / execution backtests) — they belong here as "deploy
>   <service> as a deployment", alongside the existing generic deploy mechanism (`DeployTrigger`/`DeployLiveCluster`/
>   lifecycle). They are NOT deleted. (Optional polish: align their framing under the deploy surface — not required for
>   this plan.)
> - **unified-trading-system-ui** gains the ability to ALSO trigger those same deployment-api launches, wrapped in the
>   research context (config + results/experiment viewing), via the already-wired `apiUrls.deployment` base URL
>   (`lib/config/api.ts`). This is the genuine NEW build — added as deploy actions ON the existing read-only
>   `services/research/{ml,strategy,execution}` surfaces, gated to internal/admin persona.
> - **`Dart.tsx`** in deployment-ui IS a pure duplicate of UTS-UI's far-richer `services/dart/terminal` (manual-trade,
>   not deploy) → DELETE (the only deletion in this plan).
> - **`ClientSubscriptions.tsx`** → MIGRATE to UTS-UI `manage` area (operator-confirmed); deployment-api route stays.

deployment-ui is the **devops + deploy pane** (deploy/launch any service / CI / fleet / data-status / alerts);
unified-trading-system-ui is the **trading + research + client surface** that can ALSO deploy through the shared
deployment-api. **Timing gate (operator)**: execute when the commit stream is relatively clean (check the Repos CI tab
for a quiet fleet).

## Pre-audit manifest (disposition — audited 2026-06-12, slot-3; REVISED to dual-cut)

| deployment-ui page               | deployment-api backend (STAYS)        | UTS-UI counterpart                                                                       | Disposition (REVISED)                                                                                     |
| -------------------------------- | ------------------------------------- | ---------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------- |
| `Dart.tsx` (288L, /dart)         | promote/manual_pending                | `services/dart/terminal` (+`locked`,`components/dart/*`) — far richer                    | **DELETE** from deployment-ui (pure duplicate; gap-diff empty)                                            |
| `MlExperiments.tsx` (389L)       | `POST /api/ml/experiment/launch`      | `services/research/ml` (read-only browse today)                                          | **KEEP in deployment-ui** + **ADD deploy action in UTS-UI** `research/ml`                                 |
| `StrategyBacktests.tsx` (327L)   | `POST /api/strategy/backtest/launch`  | `services/research/strategy/backtests` (in-app `/api/execution/backtests`, different op) | **KEEP in deployment-ui** + **ADD deploy action in UTS-UI** `research/strategy`                           |
| `ExecutionBacktests.tsx` (275L)  | `POST /api/execution/backtest/launch` | `services/execution/*` (read-only)                                                       | **KEEP in deployment-ui** + **ADD deploy action in UTS-UI** `research/execution` (or `research/strategy`) |
| `ClientSubscriptions.tsx` (328L) | `/api/subscriptions` CRUD             | `services/manage/*` (clients/users folded in)                                            | **MIGRATE** to UTS-UI `manage`; DELETE from deployment-ui                                                 |

Launch endpoint shapes (from `deployment-ui/src/api/deploymentApi.ts`, all → `LaunchResult`):
`MlExperimentParams{asset_group, instruments[], target_types?, timeframes?, start_date?, end_date?, operation?, machine?, dry_run?}`
· `StrategyBacktestParams{archetype, start_date, end_date, grid_density?, force?, dry_run?}` ·
`ExecutionBacktestParams{archetype, tick_interval?, continuous?, force?, dry_run?}`.

STAYS in deployment-ui unchanged (genuinely devops): VmDeployments/VmDetail/LiveDeployments, DeployTrigger/History,
DailyCosts, SafetyOps (kill-switch Layer-0), Chaos, RepoCi, EpicsPlans, Alerts, FleetGit, data-status surfaces — PLUS
the 3 launch consoles above (now confirmed KEEP).

ALREADY-SATISFIED (no work): "CI/CD clickable through the CI/CD tab + epics via the epics tab, not separate pages" —
`/repos` and `/epics` are URL-synced `LandingTabs` tabs in the home shell since 2026-06-10 (regression: deployment-ui
`tests/smoke/url-sync.spec.ts` + `epics-tab.spec.ts`). The cleanup must PRESERVE this shape.

## Phases

- [x] ✅ [AUDIT] P2. Phase 1 — audited 2026-06-12 (slot-3). Confirmed all 5 pages present
      (`deployment-ui/src/pages/{Dart,MlExperiments,StrategyBacktests,ExecutionBacktests,ClientSubscriptions}.tsx`),
      their routes (`App.tsx` L144-155), nav (`Header.tsx` `NAV_LINKS` L59-70 + mobile menu), tests
      (`src/pages/*.test.tsx`), mocks (`src/lib/mock-api.ts`). Confirmed deployment-api launch routes exist
      (`deployment_api/routes/{ml_experiment,strategy_backtest,execution_backtest}_launch.py`, unit-tested). Confirmed
      UTS-UI counterparts: `services/dart/terminal` (richer than Dart.tsx → delete), `services/research/ml` (read-only),
      `services/research/strategy/backtests` (posts to a DIFFERENT in-app endpoint), no SLA-tier surface in `manage`.
      Confirmed `apiUrls.deployment` already wired in UTS-UI `lib/config/api.ts`. Operator dual-cut decision recorded in
      Scope above. Repo: deployment-ui + unified-trading-system-ui.
- [x] ✅ [CODE] P2. [UI] Phase 2a — **UTS-UI: deploy-through-deployment-api for ML research**. DONE 2026-06-12 —
      unified-trading-system-ui@08ff0742. **Placement deviation (better)**: instead of bolting an action onto the
      data-dense `research/ml` page, built ONE `app/(platform)/services/research/deploy/page.tsx` "Deploy / Launch"
      console (internal/admin-gated via `useAuth().isInternal()`) with 3 tabs — ML / Strategy / Execution — each a
      config form → its launch hook → a `LaunchResult` panel (vm_name / correlation_id / dry-run badge / `events_uri`
      watch link). Lower regression risk + matches the operator "deploy button = pick a service" framing. ML tab POSTs
      `MlExperimentParams` → `/api/deploy/ml-experiment/launch` (collision-free rewrite, since `/api/ml/*` already
      routes to unified-trading-api). Hook `hooks/api/use-deployment-launch.ts`; types
      `lib/api/deployment-launch-client.ts`; mock-parity in `lib/api/mock-handler.ts`. NO firebase-admin (deployment-api
      proxy via Next rewrite). Repo: unified-trading-system-ui.
- [x] ✅ [CODE] P2. [UI] Phase 2b — **UTS-UI: strategy + execution backtest deploy actions**. DONE 2026-06-12 —
      unified-trading-system-ui@08ff0742. Strategy + Execution tabs of the deploy console: `StrategyBacktestParams` →
      `/api/deploy/strategy-backtest/launch`, `ExecutionBacktestParams` → `/api/deploy/execution-backtest/launch`
      (collision-free prefixes; distinct from the existing in-app `/api/execution/backtests` dialog — this is the
      VM-launch/deploy path). Mock parity + component test. Repo: unified-trading-system-ui.
- [x] ✅ [CODE] P2. [UI] Phase 2c — **UTS-UI: migrate ClientSubscriptions → `manage`**. DONE 2026-06-12 —
      unified-trading-system-ui@08ff0742. `app/(platform)/services/manage/subscriptions/page.tsx` (client_id→SLA-tier
      CRUD: list + create + edit) wired to `/api/subscriptions` (GET/POST/PUT) via
      `hooks/api/use-client-subscriptions.ts`; "Subscriptions" added to `MANAGE_TABS` in
      `components/shell/service-tabs.tsx`. Mock parity + component test. Repo: unified-trading-system-ui.
- [x] ✅ [VERIFY] P2. Phase 2-gate — DONE 2026-06-12 — unified-trading-system-ui@08ff0742 | pw:L2 ✓
      (`npx playwright test --project=chromium tests/smoke/` 17/17 passed; flake only under 2-worker parallelism, green
      serial) | regression: tests/smoke/deploy-and-subscriptions.smoke.spec.ts (+ component test
      tests/services/deploy-console.test.tsx, 4/4). QG-green (base-ui: typecheck+lint+276 tests+50.2% cov+build). Repo:
      unified-trading-system-ui.
- [x] ✅ [CODE] P2. [UI] Phase 3 — **deployment-ui: deleted `Dart.tsx` + `ClientSubscriptions.tsx`**. DONE 2026-06-12 —
      deployment-ui@91c810c (−996 lines). Removed both pages + their `*.test.tsx`, routes in `App.tsx`, nav entries in
      `Header.tsx` (+ mobile menu + `Header.test.tsx` assertion), dead subscription API fns in `api/client.ts`, dead
      types (`IsolationPolicy`/`SLATier`/`ServiceIsolationSpec`/`ClientServiceOverride`/`ClientSubscription`) in
      `types/index.ts`, and the `/subscriptions` mock + `_mockClientSubscription` helper in `lib/mock-api.ts`. Updated
      the 2 smoke specs (`nav_and_header`, `accessibility_audit`) that referenced `/dart`. **KEPT** MlExperiments /
      StrategyBacktests / ExecutionBacktests + their routes/nav/tests (dual-cut). Kept LandingTabs + all ops pages.
      Verified: typecheck + lint + 838 unit tests + build green. Repo: deployment-ui.
- [x] ✅ [VERIFY] P2. Phase 4 — DONE 2026-06-12. UTS-UI@08ff0742 | pw:L2 ✓ 17/17 (deploy console + subscriptions
      reachable, live against deployment-api via `/api/deploy/*` + `/api/subscriptions` rewrites). deployment-ui@91c810c
      | pw:L2: nav-routing 4/4 + ML/Strategy/Exec/Chaos page-render smoke pass; the 3 launch consoles +
      `/repos`+`/epics` tabs intact; Dart + ClientSubscriptions gone. **Known pre-existing flake (NOT this change)**:
      `nav_and_header.spec.ts` "VM Deployments / Live deployments page renders" fail on
      `waitForLoadState('networkidle')` (polling pages never idle) — PROVEN pre-existing by re-running on the clean
      stashed tree (same 2 fail; both untouched routes). Evidence: tests/smoke/nav_and_header.spec.ts +
      tests/smoke/deploy-and-subscriptions.smoke.spec.ts.
- [x] ✅ [DOCS] P2. Phase 5 — DONE 2026-06-12. Added a "UI surface split — deployment-ui (devops + deploy pane) vs
      unified-trading-system-ui (trading/research/client)" subsection to
      `codex/04-architecture/runtime-deployment-topology.md` (dual-cut deploy model, `/api/deploy/*` rewrite rationale,
      DART-only-in-UTS-UI, deployment-api = single shared deploy/subscriptions backend). Extended the CLAUDE.md repo-map
      line (`cursor-configs/CLAUDE.md` § System-First Architecture) with the dual-cut deploy rule + SSOT pointer. Repo:
      unified-trading-pm.

## Discovered findings (provenance: this plan, 2026-06-12 slot-3)

- [x] ✅ [SCRIPT] P2. **INFRA BUG FIXED 2026-06-12** (operator-requested follow-up). The canonical `scripts/setup.sh`
      mis-detected `unified-trading-system-ui` as a Python repo: detection was
      `IS_UI_REPO = package.json present AND     pyproject.toml ABSENT`, but UTS-UI carries an intentional
      **config-only** `pyproject.toml` (no `[build-system]`, no `[project]` — tooling-only: ruff/basedpyright on
      `scripts/`, stdlib-only codemods, ZERO declared deps; per `tooling_config_standardization_2026_05_26.md`). So
      setup.sh ran the Python path and `uv pip install -e .` failed ("Multiple top-level packages discovered in a
      flat-layout: app/lib/hooks/…"), exit 1; since `quickmerge.sh` is `set -e` and runs `setup.sh --check || setup.sh`,
      a cold env (`--check` fails) → full `setup.sh` → abort → UTS-UI quickmerge blocked. **Fix** (PM `scripts/setup.sh`
      landed with this flip + UTS-UI copy `unified-trading-system-ui@6c9680d9`): (1) detection broadened —
      `package.json` present AND a config-only pyproject (no `[build-system]` AND no `[project]`) → Node/UI path (npm,
      **no per-repo venv** — the Python tooling runs from the workspace venv, the scripts have no deps); (2) defensive
      guard added to step-8 editable-install — skip `uv pip install -e .` when the pyproject has no `[build-system]`
      (protects PM + any config-only repo that reaches the Python path). Verified: UTS-UI full `setup.sh` now exits 0
      via the UI path; the setup.sh-only quickmerge succeeded with its own `setup.sh --check` passing (no Python abort).
      UTS-UI is the only repo with this package.json+config-only-pyproject shape today, so blast radius is contained;
      the new branches are inert for all other repos. Repo: unified-trading-pm (`scripts/setup.sh`, the SSOT) +
      propagated to unified-trading-system-ui. A future `rollout-quality-gates-unified.py` re-propagates the canonical
      fleet-wide.
