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

deployment-ui is the **single devops pane** (deploy/CI/fleet/data-status/alerts). At some point trading-research
surfaces were built into it. This plan migrates them to `unified-trading-system-ui` (the trading/user surface) and
deletes them from deployment-ui — clean break, no parallel paths. **Timing gate (operator)**: execute when the commit
stream is relatively clean (post the 2026-06-11 CI-repair wave; check the Repos CI tab for a quiet fleet).

## Pre-audit manifest (what got misbuilt where — audited 2026-06-12, slot-3)

MIGRATE to unified-trading-system-ui (trading/research UX; ~1,280 lines + tests):

| deployment-ui page              | Route                           | What it is                                                          | Backend it calls (STAYS in deployment-api) |
| ------------------------------- | ------------------------------- | ------------------------------------------------------------------- | ------------------------------------------ |
| `Dart.tsx` (288L)               | `/dart`                         | "DART Terminal — DeFi archetype visualization + manual trade entry" | promote/manual_pending routes              |
| `MlExperiments.tsx` (389L)      | `/research/ml-experiments`      | ML experiment VM launch console + run browser                       | `POST /api/ml/experiment/launch`           |
| `StrategyBacktests.tsx` (327L)  | `/research/strategy-backtests`  | strategy backtest launch console + results                          | `POST /api/strategy/backtest/launch`       |
| `ExecutionBacktests.tsx` (275L) | `/research/execution-backtests` | execution backtest launch console + results                         | `POST /api/execution/backtest/launch`      |

STAYS in deployment-ui (genuinely devops): VmDeployments/VmDetail/LiveDeployments, DeployTrigger/History, DailyCosts,
SafetyOps (kill-switch Layer-0), Chaos (FORBIDDEN-in-prod injection testing), RepoCi, EpicsPlans, Alerts, FleetGit,
data-status surfaces.

DECIDE-IN-PHASE-1 (one borderline): `ClientSubscriptions.tsx` (328L, `/client-subscriptions`, binds client_id → SLATier)
— client admin lives in UTS-UI (user-management was folded there), but the SLA tier drives deployment behaviour.
Recommendation: MIGRATE (client-facing admin), deployment-api route stays.

ALREADY-SATISFIED (no work): "CI/CD clickable through the CI/CD tab + epics via the epics tab, not separate pages" —
`/repos` and `/epics` are URL-synced `LandingTabs` tabs in the home shell since 2026-06-10 (regression: deployment-ui
`tests/smoke/url-sync.spec.ts` + `epics-tab.spec.ts`). The cleanup must PRESERVE this shape.

## Phases

- [ ] [AUDIT] P2. Phase 1 — confirm the migrate-set + the ClientSubscriptions call with a fresh grep (pages may have
      moved since 2026-06-12); enumerate every nav/header/route/mock/test referencing the 4-5 pages in BOTH repos
      (deployment-ui `App.tsx` routes 142-155 + nav; UTS-UI `app/(ops)`/`(platform)` groups for placement). Repo:
      deployment-ui + unified-trading-system-ui.
- [ ] [CODE] P2. [UI] Phase 2 — port the research surfaces into unified-trading-system-ui (Next.js app-router pages
      under `app/(ops)/research/` + DART under `app/(ops)/dart/`; client components calling deployment-api via the
      existing API-base config — the launch/list endpoints stay in deployment-api, no backend move). Mock-mode parity +
      component tests; pw:L2 on UTS-UI per its gate. Repo: unified-trading-system-ui.
- [ ] [CODE] P2. [UI] Phase 3 — DELETE the migrated pages + routes + nav entries + mocks + tests from deployment-ui (no
      shims, no redirects left behind beyond a one-line route → UTS-UI URL pointer if the operator wants one); keep
      LandingTabs (Overview/Epics/Repos CI/Alerts/Fleet Git) + ops pages intact; pw:L2 must stay green (update specs
      that referenced deleted pages). Repo: deployment-ui.
- [ ] [VERIFY] P2. Phase 4 — both stacks up; every migrated surface reachable in UTS-UI and live against deployment-api;
      deployment-ui nav contains ONLY devops surfaces; `/repos` + `/epics` tabs verified clickable + URL-synced.
      Evidence: pw:L2 both repos + screenshots in the plan.
- [ ] [DOCS] P2. Phase 5 — codex SSOT update: `codex/04-architecture/` UI-split note (deployment-ui = devops pane;
      unified-trading-system-ui = trading/user surface incl. research consoles + DART) so the next agent doesn't
      re-confuse the two; CLAUDE.md repo-map line already says it — extend with the research-console rule.
