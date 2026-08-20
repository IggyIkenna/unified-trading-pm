---
doc_type: plan
title: Sports Track H — registry-aware honest-coverage denominator (gated on league_id migration prereqs)
summary: >-
  Extracted, verbatim, from `sports_consolidated_native_ao_extract_2026_07_25.md`'s Track H denominator todo — 4
  consecutive same-day dispatches (slots 11, 7, 10, 15 on 2026-07-28) confirmed the same 2 real blockers
  (`odds_horizon_bucket` MDPS reprocess + `batch_footystats` copy+swap) remain unshipped, and a priority-999 backlog
  park did not hard-block re-dispatch because no machine `depends_on` existed. This plan is machine-gated via
  `depends_on`+`gate_on_depends: true` on `sports_track_h_denominator_prereqs_2026_07_28.md` so the dispatcher itself
  withholds this todo until both prerequisites are genuinely `done`, converting the issue-doc prose-block into a real
  dispatch gate.
status: active
nature: process
asset_group: [sports]
stage: [data]
repos: [deployment-api]
scope: [engineer]
tags: [sports, ao-dispatch, close-out, native-extract, plan-hygiene, coverage]
related:
  [
    /plans/active/sports_consolidated_native_ao_extract_2026_07_25.md,
    /plans/active/sports_track_h_denominator_prereqs_2026_07_28.md,
    /plans/active/issues/sports_league_id_namespace_migration_2026_07_20.md,
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
  ]
created: "2026-07-28"
last_updated: "2026-08-03"
parent_epic: sports_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.24
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [sports_track_h_denominator_prereqs_2026_07_28]
gate_on_depends: true
source: >-
  Operator-directed split (2026-07-28, answering blocked question BLK-2f9e7680) of
  `sports_consolidated_native_ao_extract_2026_07_25.md`'s Track H todo, so its 25 other independent todos keep
  dispatching without this one's 999-priority bounce, and so the 2 real prerequisites become a machine dispatch gate
  rather than issue-doc prose.
assigned_role: data_engineering
sequential: false
drift_direction: advance-code
context_scope:
  [
    /codex/02-data/honest-coverage-model.md,
    /plans/active/sports_track_h_denominator_prereqs_2026_07_28.md,
    /plans/active/issues/sports_league_id_namespace_migration_2026_07_20.md,
    deployment-api/deployment_api/services/data_status/coverage.py,
    /plans/active/sports_consolidated_native_ao_extract_2026_07_25.md,
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
  ]
---

# Sports Track H — registry-aware honest-coverage denominator (gated)

> **Machine-gated on `sports_track_h_denominator_prereqs_2026_07_28.md`** (`depends_on` + `gate_on_depends: true`) — the
> dispatcher will not queue the todo below until both of that plan's todos are `done`. Do not re-dispatch this manually
> before then; if it is ever offered despite the gate, that is itself the orchestration gap already flagged to the
> operator (park-priority-doesn't-hard-block-redispatch) recurring and should be reported, not worked around.

## Todos

- [ ] [CODE] P1. **Track H — implement the registry-aware honest-coverage denominator in
      `compute_coverage_for_bucket()`** (deployment-api) — sports coverage % must reflect "captured / UAC registry
      universe," not "captured / raw manifest." **REQUIRED FIRST STEP (live-probe, do not trust the source todo's
      "largely executed" framing at face value)**: run a live manifest census confirming 0 sports manifest rows still
      carry non-registry-form `league_id` strings; if any non-registry rows remain, STOP and report instead of shipping
      the denominator change (a registry-membership test cannot be correct while non-registry rows exist). (repo:
      deployment-api). **Done when**: the live-probe confirms 0 non-registry `league_id` rows AND the denominator code
      change ships, verified against a real bucket. Source: `sports_consolidated_closeout_2026_07_19.md:536-541`. **RUN
      2026-07-28 (slot-11)**: required first step executed — STOP condition fired, correctly did not ship. Live probe
      against `market-data-tick-sports-prd-central-element-323112` found 55,160 genuine non-canonical `league_id` rows
      (57,942 raw non-registry rows minus 2,782 blank/`NaN` sentinel, out of 516,196 total), concentrated in the
      still-outstanding `batch_mdps_odds_horizon_bucket` (42,652) + `batch_footystats` (14,668) pipeline_modes — exactly
      the two deferred shapes `issues/sports_league_id_namespace_migration_2026_07_20.md`'s own STATUS 2026-07-25 named
      as not yet migrated. Full method + numbers in that doc's "LIVE-PROBE 2026-07-28" section. **RE-DISPATCH CHECK
      2026-07-28 (slot-7)**: re-verified shipped-status rather than re-running the full census — coverage-registry
      refresh confirmed DONE (`unified-api-contracts@8e8d2e5b`/`@804858c9`); the other 2 blockers still outstanding.
      **RE-DISPATCH CHECK 2026-07-28 (slot-10)**: re-verified again, both blockers still unshipped; filed `/blocked`
      recommending a backlog park. **RE-DISPATCH CHECK 2026-07-28 (slot-15)**: re-verified a 4th time (unchanged),
      renewed the park recommendation (`BLK-2f9e7680`); operator directed this SPLIT into a machine-gated plan instead
      of a priority-only park. Still blocked on both prerequisites landing — re-run the probe once
      `sports_track_h_denominator_prereqs_2026_07_28.md` is fully `done`, not before.

## Progress Log

### 2026-07-28 (slot-15) — extracted from sports_consolidated_native_ao_extract_2026_07_25.md, machine-gated

See `sports_track_h_denominator_prereqs_2026_07_28.md`'s Progress Log for the split rationale. The original plan's Track
H line is replaced with a non-checkbox pointer to this plan (so it stops being offered as an open todo there).

- **context-scout 2026-08-01**: populated/refreshed context_scope (4 entries).
- **context-scout 2026-08-03**: re-verified context_scope (6 entries) -- already accurate (source path
  `coverage.py::compute_coverage_for_bucket()` matches the todo's own cited function); no change needed.
