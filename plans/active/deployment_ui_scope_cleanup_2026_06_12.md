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
- [ ] [CODE] P2. [UI] Phase 3 — **deployment-ui: DELETE only `Dart.tsx` + `ClientSubscriptions.tsx`** (+ their routes in
      `App.tsx`, nav entries in `Header.tsx`, `*.test.tsx`, mock handlers). **KEEP** MlExperiments / StrategyBacktests /
      ExecutionBacktests (dual-cut: they remain the deploy surface here). Keep LandingTabs (Overview/Epics/Repos
      CI/Alerts/Fleet Git) + all ops pages. `pw:L2` must stay green (update specs referencing the 2 deleted pages).
      Repo: deployment-ui.
- [ ] [VERIFY] P2. Phase 4 — both stacks up; UTS-UI research surfaces can deploy live against deployment-api; the 3
      launch consoles still work in deployment-ui; Dart + ClientSubscriptions gone from deployment-ui; `/repos` +
      `/epics` tabs still clickable + URL-synced. Evidence: pw:L2 both repos.
- [ ] [DOCS] P2. Phase 5 — codex SSOT update: `codex/04-architecture/` UI-split note (deployment-ui = devops + deploy
      pane incl. the 3 launch consoles; unified-trading-system-ui = trading/research/client surface that can ALSO deploy
      through the shared deployment-api; DART lives only in UTS-UI). Extend CLAUDE.md repo-map line with the dual-cut
      deploy rule.

## Discovered findings (provenance: this plan, 2026-06-12 slot-3)

- [ ] [SCRIPT] P2. **DEFERRED — INFRA BUG (not this plan's scope; surfaced shipping Phase 2)**: the canonical
      `scripts/setup.sh` mis-detects `unified-trading-system-ui` as a Python repo. Detection is
      `IS_UI_REPO = package.json     present AND pyproject.toml ABSENT` (setup.sh L165-167), but UTS-UI carries an
      intentional **config-only** `pyproject.toml` (no `[build-system]`, Python tooling for `scripts/` only — per
      `tooling_config_standardization_2026_05_26.md`). So setup.sh runs the Python path and `uv pip install -e .` fails
      ("Multiple top-level packages discovered in a flat-layout: app/lib/hooks/components/node_modules…"), exit 1.
      Because `quickmerge.sh` is `set -e` and runs `setup.sh --check || setup.sh`, a cold env (where `--check` fails) →
      full `setup.sh` → abort → **UTS-UI quickmerge is blocked**. Today it only ships because a prior `.venv` makes
      `--check` pass (fragile). Fix: in the canonical PM `scripts/setup.sh`, treat
      `package.json present AND pyproject.toml has no     `[build-system]` table` as a UI repo (config-only pyproject) →
      skip the Python path; roll out fleet-wide. Repo: unified-trading-pm (`scripts/setup.sh` + rollout). Affects any
      frontend repo carrying a config-only pyproject.
