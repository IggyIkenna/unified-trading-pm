---
doc_type: issue
title:
  features-sports-service — deployment-ui per-feature-group coverage tab + "register a new feature" codex playbook never
  built
summary: >-
  Triaging archived-plan debt for `features_sports_honest_coverage_2026_05_05.plan.md` found its Phase 8 UI/docs cluster
  only partially shipped: the drift-alert comparator (`coverage_drift.py`/`DriftEvent`) landed at
  `deployment-api@acd2d25`, but the deployment-ui surface that would actually show a per-feature-group honest-coverage
  breakdown (Phase 8.A) and the codex playbook documenting how to register a new feature calculator against the
  Phase-1/2/3 architecture (Phase 8.C) were never built. No active plan references either deliverable.
status: resolved
nature: issue
asset_group: [sports]
stage: [meta]
repos: [deployment-ui, deployment-api]
scope: [engineer]
tags: [features-sports, deployment-ui, coverage, honest-coverage, codex, playbook, orphaned-work, plan-debt]
related:
  [
    plans/archive/features_sports_honest_coverage_2026_05_05.plan.md,
    plans/active/issues/pm_qg_plan_discipline_and_frontmatter_regression_2026_07_21.md,
  ]
created: "2026-07-21"
parent_epic: sports_master
priority: P3
assigned_vm: planning
execution_scope: orchestrator-agent
drift_direction: advance-code
source: [pm_qg_plan_discipline_and_frontmatter_regression-004]
resolved_by:
  deployment-ui@d8def9c, deployment-api@47802dc5, unified-api-contracts@018c3ca6 deployment-ui@d8def9c,
  unified-trading-pm@codex/02-data/sports-feature-calculator-registration-playbook.md, deployment-api@47802dc5,
  unified-api-contracts@018c3ca6
locked_by:
depends_on: []
---

# What I found

`features_sports_honest_coverage_2026_05_05.plan.md` Phase 8 ("UI polish + drift monitoring") had 3 items:

- P8.A — a deployment-ui tab/panel surfacing per-feature-group honest-coverage (the `upstream_missing` vs
  `out_of_coverage` distinction Phase 2 built, and the per-calculator coverage rows Phase 3's `_sports_honest_coverage`
  axis produces).
- P8.B — a drift comparator between two coverage snapshots. **Shipped**: `deployment-api@acd2d25` (`coverage_drift.py`,
  `DriftEvent`, 14 tests). Per the plan's own handoff doc, "only the cron entrypoint + dashboard wiring is left."
- P8.C — a codex doc explaining how to register a new feature calculator so it gets the Phase-1/2/3 coverage-gating
  treatment automatically (UAC `FEATURE_UPSTREAM_REQUIREMENTS` entry, `_gate_then_run` wiring, deployment-api
  per-calc-meta entry).

Grepped all of `plans/active/*.md` and `codex/02-data/` for any reference to a features-sports coverage tab or a
feature-registration playbook — none found. The architecture these two items would surface/document is real and shipped;
only the presentation layer and the docs are missing.

# Why it matters

Without P8.A, the honest-coverage distinction the rest of the plan built (Phases 1-3, all shipped) is only visible via
manifest queries or the operator CLI (`honest_coverage_report.py`) — not to anyone using deployment-ui day-to-day.
Without P8.C, whoever next adds a sports feature calculator has to reverse-engineer the coverage-gating contract from
code rather than following a documented recipe — a recurring source of drift risk on a subsystem the codex already flags
as needing better documentation.

# Recommended decision

File as a P3 backlog item — neither is blocking, both are worth picking up opportunistically.

## Todos

- [x] ✅ [UI] P3. Build a deployment-ui panel/tab surfacing per-feature-group honest coverage for sports (reading the
      Phase-3 `_sports_honest_coverage` axis + the drift comparator's `DriftEvent` output). pw:L2 regression spec
      required per the UI testing-layers codex. (repo: deployment-ui) — deployment-ui@d8def9c | pw:L2 ✓ | regression:
      tests/smoke/sports_feature_coverage_card.spec.ts. Shipped `SportsFeatureCoverageCard` on the
      features-sports-service Data Status tab, reading the 3 feature-rollup data_types
      (FIXTURE_FEATURES/ODDS_FEATURES/DERIVED_FEATURES) that `sports_honest_coverage()` already serves over HTTP via
      `GET /api/data-status/turbo` — verified live (found/expected shards + per-league `missing_dates`), previously only
      reachable 5 levels deep in the generic drilldown. **Scope note**: the per-CALCULATOR (34-calculator,
      `FEATURES_SPORTS_PER_CALC_META`) breakdown and the `DriftEvent` comparator output are NOT reachable over HTTP yet
      — verified no route/cron wraps either (`coverage_drift.py` has zero caller in `deployment_api/routes/`/`main.py`).
      Rendering those would mean inventing a shape the backend doesn't return (forbidden by the UI-testing-layers
      "render exactly what the API returns" rule), so the card shows the 3 rollups it CAN honestly render plus an
      explicit "not wired yet" note pointing at todo 3 below (INFRA, the remaining wiring for `DriftEvent`; the
      per-calculator HTTP route is a further follow-up beyond this card's scope). Unit spec:
      `tests/unit/components/SportsFeatureCoverageCard.test.tsx`.
- [x] ✅ [DOC] P3. Write a codex playbook under `codex/02-data/` documenting how to register a new sports feature
      calculator against the coverage-gating architecture (UAC `FEATURE_UPSTREAM_REQUIREMENTS` entry, `_gate_then_run`
      wiring in features-service, the deployment-api per-calc-meta entry each new calculator needs). (repo:
      unified-trading-pm) — `codex/02-data/sports-feature-calculator-registration-playbook.md`. Covers the 2 real touch
      points (UAC `FEATURE_UPSTREAM_REQUIREMENTS` entry; the `gate(...)` call in the features-service dispatcher wired
      through `_gate_then_run`/`check_calculator_coverage`) + 1 conditional touch point (`DATA_TYPE_TO_REF_KEY` only for
      a genuinely new upstream data_type), plus an explicit correction of the todo's own premise: deployment-api's
      `FEATURES_SPORTS_PER_CALC_META` is auto-derived (a dict comprehension over `FEATURE_UPSTREAM_REQUIREMENTS`,
      `sports_helpers.py`) — there is no manual per-calc-meta entry to add, and the playbook says so explicitly so
      future authors don't duplicate work. Includes a worked example (`set_piece_calculator`).
- [x] ✅ [INFRA] P3. Wire the drift comparator's cron entrypoint + dashboard alert (the one remaining piece of the
      otherwise-shipped P8.B). (repo: deployment-api) — `deployment-api@47802dc5` + `unified-api-contracts@018c3ca6`.
      Built a daily snapshot-write + comparator worker (`deployment_api/scripts/coverage_drift_worker.py`) mirroring the
      two existing in-service Cloud-Scheduler-POST workers in this repo (`data_status_rollup_worker.py`/`_rollup.py`,
      `cost_snapshot_worker.py`) rather than a standalone Cloud Run Job (this repo's native pandas compute crashes on
      gen2 Jobs — R7 follow-up #4). **Snapshot**: reads a bounded 30-day trailing window of the features-sports-service
      manifest via `read_manifest_index`'s predicate-pushdown `date_window` (no whole-corpus walk), filtered to
      `known_calculators()`, writes a per-day parquet under `coverage-drift-snapshots/sports/{date}.parquet` in
      deployment-api's existing state bucket (mirrors `cost_observability/snapshot.py` — no dedicated bucket for a
      handful of small daily blobs). **Compare**: loads today's + 7-days-back snapshot (graceful `None` — not an error —
      for the first week with no baseline), calls the already-shipped `detect_drift()`, and persists one alert per
      `DriftEvent` via the existing `_persist_alert()` ledger (`deployments_inventory.py`) — the same ledger
      `GET /api/alerts` already serves to deployment-ui's dashboard, so **zero reader-side changes** were needed for the
      "dashboard alert" half. **Route**: `POST /api/data-status/sports/coverage-drift-run` (new
      `_coverage_drift_run.py`, registered on the shared data-status router — inherits the router's existing
      `verify_any_auth`), mirroring `_rollup.py`'s exact in-service-POST pattern. **Scheduler**: registered
      `sports-coverage-drift` in UAC's `SCHEDULER_REGISTRY` (`0 2 * * *` daily, `target_kind=CLOUD_RUN`,
      `target_ref=deployment-api`, `asset_group=sports`) — the SSOT this workspace's governance rule requires before any
      real `gcloud scheduler jobs create`. Deliberately deviated from 2 details in the stale pre-implementation HANDOFF
      doc, with reasoning: (1) cadence — HANDOFF/plan text said "hourly," but the shipped comparator + its own docstring
      already commit to "daily vs N-days-back," which is also the only cadence a 30-day trailing-window percentage can
      meaningfully move on — hourly would need a wholly different, much narrower windowing scheme; (2) repo — HANDOFF
      said "Cloud Run Job in deployment-service," but this todo's own scope line names `deployment-api`, and the
      comparator's actual compute (pure pandas over an already-bounded manifest slice) is cheap enough for the
      in-service-route pattern, avoiding a new VM/Job entirely. Tests: `tests/unit/test_coverage_drift_worker.py` (17
      new tests: snapshot projection/write/read round-trip + graceful-missing, drift-check alert-persist-on-threshold +
      no-alert-on-missing-baseline, route dispatch) + `unified-api-contracts/tests/unit/test_scheduler_registry.py` (2
      new assertions for the registry entry). Both repos' full `quality-gates.sh` green (a hardcoded-prod-GCP-project-ID
      string I'd used in a test mock tripped this repo's codex-compliance ratchet at 6/5 on the first run — fixed to a
      generic placeholder, re-verified back to 5/5 before shipping). Not done: the per-CALCULATOR (34-calculator)
      HTTP-reachable breakdown referenced in todo 1's scope note is a distinct, larger follow-up beyond this todo.

## Codex SSOTs

`codex/02-data/availability-manifest-and-data-status.md`, `codex/02-data/honest-coverage-model.md`.

## RE-TRIAGE (2026-07-23)

**Verdict: RESOLVED BY LATER WORK.** All 3 todos were already checked `[x]` in this doc with cited commits — re-verified
each deliverable actually exists in the current codebase (frontmatter `status` was simply never flipped to match):

- `deployment-ui/src/components/SportsFeatureCoverageCard.tsx` +
  `tests/unit/components/SportsFeatureCoverageCard.test.tsx`
  - `tests/smoke/sports_feature_coverage_card.spec.ts` all present on disk; `git log -1 d8def9c` =
    `feat(data-status): sports feature coverage card (Phase 8.A)`.
- `codex/02-data/sports-feature-calculator-registration-playbook.md` present in this repo.
- `deployment-api/deployment_api/scripts/coverage_drift_worker.py` +
  `deployment_api/routes/data_status/_coverage_drift_run.py` present; `git log -1 47802dc5` (deployment-api) =
  `feat(data-status): wire sports coverage-drift cron entrypoint + dashboard alert (Phase 8.B)`; `git log -1 018c3ca6`
  (unified-api-contracts) = `feat(scheduler): register sports-coverage-drift Cloud Scheduler entry (Phase 8.B)`, and
  `sports-coverage-drift` confirmed present in `unified_api_contracts/canonical/crosscutting/scheduler_registry.py`.

Flipped `status: open` → `resolved` and filled `resolved_by:` accordingly. No new gap found.
