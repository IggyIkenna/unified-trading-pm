---
doc_type: issue
title: >-
  deployment-ui's /fleet page removed entirely — supersedes the 2026-06-10 v2 decision now that fleet git-health's only
  home is a top-bar popover on agent-orchestrator's own per-VM dashboard
summary: >-
  Operator reported (2026-07-27) that deployment-ui's /fleet page (https://uts-shared-deployment-api-cldtjniqvq-an.a.
  run.app/fleet) was the wrong place for fleet KPIs/git-health — nobody visits deployment-ui's cross-VM /fleet page
  anymore, and the operator's actual daily workflow is agent-orchestrator's own per-VM Dashboard
  (https://agent-orchestrator.odum-research.com/vm/<id>), which never had the feature at all. Root cause: AF-5's KPI
  page + FleetGit's git-health page were both built as SEPARATE top-level pages reachable only via the cross-VM Landing
  screen ("/") — a screen that stopped being a daily-use page once the fleet dropped from ~11 VMs to 1 (single-VM
  architecture, 2026-06-27). A parity check confirmed deployment-ui's /fleet was a thin proxy of agent-orchestrator's
  own git-health computation (not a second data pipeline) with exactly one feature AO's own page lacked (per-slot
  snapshot-age) and two AO had that deployment-ui lacked (a GH-rate-limit widget + the git_red_sustain_secs-gated
  red/amber threshold matching the Slack pager, which deployment-ui's page never actually read off the wire despite the
  field being present in the proxied payload). Resolution: (1) added both KPIs and git-health as top-bar popovers on
  agent-orchestrator's own per-VM Dashboard (no navigation needed from wherever the operator already is); (2) ported the
  one feature deployment-ui uniquely had (snapshot-age) into AO's own FleetGit.tsx before removing anything; (3) deleted
  deployment-ui's /fleet page, nav entry, FleetGit.tsx, its API-client types/function, and the now-dead deployment-api
  proxy route + mocks + tests; (4) repointed the two live cross-links that pointed at /fleet (RepoCi.tsx's "Fleet Git"
  cross-link → external link to the AO dashboard; CockpitHealth's "Fleet VMs" landing tile → /deployments, since that
  tile's own VM-census framing already described data that lives there since the 2026-07-21 Fleet-tab consolidation, not
  git-health). All four repos' quality gates + test suites green.
status: resolved
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator, deployment-ui, deployment-api, unified-trading-pm]
scope: [engineer, admin]
tags:
  [
    agent-orchestrator,
    deployment-ui,
    deployment-api,
    fleet,
    git-health,
    kpi,
    dashboard,
    ui,
    consolidation,
    decision-reversal,
  ]
related:
  [
    /plans/archive/2026_07/ao_fleet_observability_kpis_2026_07_20.md,
    /codex/05-infrastructure/deployment-observability.md,
    /plans/archive/2026_07/deployment_ui_fleet_tab_consolidation_2026_07_21.md,
    /plans/active/monitoring_control_plane_master_2026_06_10.md,
    /codex/04-architecture/agent-orchestrator-alerting.md,
  ]
created: 2026-07-27
last_updated: "2026-07-27"
parent_epic: orchestrator_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 0.6
assigned_role: backend_engineer
drift_direction: advance-code
depends_on: []
source: >-
  Operator, interactive session 2026-07-27: "we can also remove the [deployment-ui /fleet] page from deployment-ui since
  thats not the right place for it... check if there are any things that are not present in the deployment-ui page that
  we dont have here and both are using same backend code as well" — followed by an explicit choice, when asked, to
  "Delete it anyway, port snapshot-age into AO's popover first" over keeping deployment-ui's page.
locked_by:
resolved_by: "cicd plan_health gate worker, 2026-07-27 (plan-hygiene NA-corpus ratchet triage)"
---

# deployment-ui `/fleet` removed — fleet git-health consolidates onto agent-orchestrator's own dashboard

> **🟢 RESOLVED 2026-07-27** — fix shipped and verified across all four repos this doc names (agent-orchestrator
> `tsc`/`vitest`/`vite build` clean; deployment-ui `tsc`/`eslint`/`vitest` clean; deployment-api full `quality-gates.sh`
> green; unified-trading-pm doc updates). Zero open follow-up todos — this doc is itself a closed-out record, not a
> dispatch (see "Gate" section below). Archived per `/codex/11-project-management/issue-doc-lifecycle.md` trigger 2
> (commit-SHA-fixes-the-issue).

## What triggered this

The operator was looking at agent-orchestrator's own per-VM Dashboard
(`https://agent-orchestrator.odum-research.com/vm/ikenna-vm`) expecting to see fleet-efficiency KPIs (boots/dispatches/
done conversion, per-account usage — shipped by `ao_fleet_observability_kpis_2026_07_20.md`'s AF-5/AF-5-followup todos)
and saw nothing. Investigation found the feature WAS live (bundle verified, endpoint verified, Firebase deploy pipeline
verified green across dozens of recent runs) but reachable only via a "Fleet KPIs →" button on the cross-VM Landing page
at root `/` — a page the operator explicitly said they stopped visiting once the fleet dropped from ~11 VMs to 1
(single-VM architecture, 2026-06-27 per `agent-orchestrator-single-vm-architecture.md`). Separately, the operator
pointed at deployment-ui's own `/fleet` page (a DIFFERENT app, a DIFFERENT URL) and asked whether it was now redundant
with the fix already added to AO's own dashboard.

## Parity check (why this wasn't a blind delete)

A research pass traced both pages to their actual backend logic before any deletion:

- **Same computation, one owner**: deployment-ui's `/fleet` page called `deployment-api`'s
  `GET /repo-ci/fleet-git-health`, which was a THIN PROXY — `_repo_ci_fleet.py::fetch_fleet_git_health` did nothing but
  `GET https://api.agent-orchestrator.odum-research.com/api/fleet/git-health?scope=fleet` with a Bearer token from
  Secret Manager, and passed the JSON through unmodified. The actual computation (per-slot dirty/behind/diverged state,
  drift violations, reporter/ff-pull cron liveness) lives in exactly one place:
  `agent-orchestrator/server/routes/ git_health.py`. Deleting deployment-ui's page removes a presentation layer only,
  not a second data pipeline.
- **deployment-ui had one thing AO's own page lacked**: per-slot snapshot-age (`slot.reported_at`, already on the wire,
  never rendered by AO's `FleetGit.tsx`). Ported into `agent-orchestrator/dashboard/src/FleetGit.tsx`'s `SlotRow` (a
  `snap:{age}` chip, mirroring the existing `ff:{result}` chip) BEFORE deleting deployment-ui's copy.
- **AO's own page had two things deployment-ui lacked**: a GitHub-rate-limit widget (deployment-ui has an equivalent,
  but only on its separate `/ci` page, not `/fleet`), and — the more important gap — a 90-min "sustained red" threshold
  (`git_red_sustain_secs`, matching the exact threshold the Slack git-health pager uses) gating red vs. amber coloring.
  deployment-ui's `FleetGit.tsx` never read this field off the wire despite it being present in the proxied payload, so
  the two pages could disagree about whether a given state was actually alert-worthy. These stay AO-only — no reason to
  duplicate them into a page that no longer exists.
- **Prior operator decisions on this exact page**: `monitoring_control_plane_master_2026_06_10.md`'s "operator decision
  REVISION (2026-06-10 v2)" explicitly made deployment-ui the primary fleet-git-health surface ("one devops pane"), and
  `deployment_ui_fleet_tab_consolidation_2026_07_21.md` re-examined and KEPT that page five weeks later (trimming it to
  git-health-only, not removing it). Both were genuine, deliberate decisions — this issue explicitly supersedes them for
  fleet git-health specifically, given the intervening single-VM architecture change and the operator's direct
  instruction in this session, not a silent reversal.

## What changed

- **`agent-orchestrator`** (`dashboard/src/layout.tsx`, `dashboard/src/App.tsx`, `dashboard/src/FleetGit.tsx`): added
  `FleetKpisMenu`/`FleetGitMenu` top-bar popovers (reusing `FleetKpis`/`FleetGit` unchanged, no `onBack`) next to the
  Snapshot button on the per-VM Dashboard's `TopBar`; ported per-slot snapshot-age into `FleetGit.tsx`'s `SlotRow`.
- **`deployment-ui`**: deleted `src/pages/FleetGit.tsx`; removed `CockpitFleet`/`FleetTab` from `Cockpit.tsx`; removed
  the `/fleet` route + the `/infra → /fleet` redirect (now dead-ends at the catch-all) from `App.tsx`; removed the
  "Fleet" nav item + its `PLAIN_ROUTE_TO_TAB_ID` entry from `NavMenu.tsx` (renamed the now-Fleet-less "Fleet & Cost"
  heading to "Cost & Artifacts"); removed `FleetGit*` types + `getFleetGitHealth()` from `api/client.ts`; removed
  `mockFleetGitHealth()` from `lib/mock-api.ts`; repointed `RepoCi.tsx`'s "Fleet Git" cross-link to an external link
  (`https://agent-orchestrator.odum-research.com/`, same `data-testid`); repointed `Cockpit.tsx`'s CockpitHealth landing
  tile ("Fleet VMs (GCP+AWS)") from `/fleet` to `/deployments` (its own VM-census metric text already describes data
  that lives there since the 2026-07-21 consolidation); updated `NavMenu.test.tsx`, `TopNavBar.test.tsx`,
  `Cockpit.test.tsx` for the new canonical-entry counts (16→15) and removed routes.
- **`deployment-api`**: deleted `routes/_repo_ci_fleet.py`; removed the `GET /fleet-git-health` route + its imports from
  `routes/repo_ci.py`; removed `FleetGitHealthProxyDict` from `routes/_repo_ci_types.py`; removed
  `_mock_fleet_git_health()` + its import from `routes/_repo_ci_mocks.py`; removed `TestFleetGitHealthMock`/
  `TestFleetGitHealthDegrade` from `tests/unit/test_repo_ci_routes.py`.
- **`unified-trading-pm`**: this doc; `/codex/05-infrastructure/deployment-observability.md` new section "Fleet tab
  REMOVED entirely" (supersedes-note on the 2026-06-10 v2 decision + the 2026-07-21 consolidation, `code_refs` pruned of
  the deleted `FleetGit.tsx` path); `monitoring_control_plane_master_2026_06_10.md`'s Progress Log records the
  supersession (see that plan directly).

## Evidence

- `agent-orchestrator`: `tsc --noEmit` clean, `vitest run` 154/154 passed, `vite build` succeeds.
- `deployment-ui`: `tsc --noEmit` clean, `eslint src` clean, `vitest run` 1096 passed / 16 skipped, `tsc && vite build`
  succeeds.
- `deployment-api`: full `quality-gates.sh` green (139s first run, pytest phase included — subsequent identical-tree
  runs correctly hit the green-content-sentinel fast path and skip re-verification).
- Live verification (pre-removal, same session): `agent-orchestrator.odum-research.com`'s served JS bundle contained
  `FleetKpis`/`fleet-kpis` strings; `GET /api/fleet-kpis` returned 401 (auth-gated, not 404 missing); the Firebase
  dashboard-deploy workflow (`deploy-dashboard.yml`) showed ~15 consecutive green runs over the prior 24h, one landing 8
  minutes before the check.

## Gate

Every repo's own quality gate green (cited above); every dead reference removed or repointed (verified via a corpus-wide
grep for `"/fleet"`, `FleetGit`, `fleet_git_health`, `fleet-git-health` across both frontend repos and the
deployment-api backend — the one surviving literal match is the new "removed routes" test entry that intentionally pins
`/fleet`'s absence). No open follow-up work — this is a closed-out record, not a dispatch.
