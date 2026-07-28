---
doc_type: plan
title: MDPS `odds_horizon_bucket` Step-7 reprocess — gated on the raw `batch_odds_api` league_id re-fix
summary: >-
  Extracted from `sports_track_h_denominator_prereqs_2026_07_28.md`'s todo 1 — dispatched 2026-07-28 (slot 12), which
  found the todo's own stated prerequisite ("raw content is already canonical per the shipped `batch_odds_api`
  migration") false: a fresh census measured 99,607 non-registry raw rows today, contradicting
  `sports_league_id_namespace_migration_2026_07_20.md`'s "STATUS 2026-07-25" claim. This plan is machine-gated via
  `depends_on`+`gate_on_depends: true` on `issues/sports_batch_odds_api_league_id_canonicalization_regressed_2026_07_28.md`
  so the dispatcher withholds the reprocess job until the raw prerequisite is genuinely fixed, instead of being
  re-offered to another slot that would hit the same unreachable done-when a 3rd time.
status: active
nature: process
asset_group: [sports]
stage: [data]
repos: [market-data-processing-service]
scope: [engineer]
tags: [sports, league-id, migration, prereqs, ao-dispatch, plan-hygiene, machine-gate]
related:
  [
    /plans/active/issues/sports_batch_odds_api_league_id_canonicalization_regressed_2026_07_28.md,
    /plans/active/sports_track_h_denominator_prereqs_2026_07_28.md,
    /plans/active/sports_track_h_denominator_gated_2026_07_28.md,
    /plans/active/issues/sports_league_id_namespace_migration_2026_07_20.md,
  ]
created: "2026-07-28"
last_updated: "2026-07-28"
parent_epic: sports_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [sports_batch_odds_api_league_id_canonicalization_regressed_2026_07_28]
gate_on_depends: true
source: >-
  Operator-directed split (2026-07-28, answering blocked question BLK-ad4aa20d): re-dispatching this Step-7 todo before
  the raw batch_odds_api league_id residual is fixed would waste a 3rd multi-hour multi-VM reprocess run that provably
  cannot reach its own done-when (it derives output from raw content). Machine-gated rather than left as a bare
  unchecked todo so the dispatcher itself withholds it, per the same pattern already used for
  `sports_track_h_denominator_gated_2026_07_28.md`.
assigned_role: data_engineering
sequential: false
drift_direction: advance-code
---

# MDPS `odds_horizon_bucket` Step-7 reprocess (gated)

> **Machine-gated on `issues/sports_batch_odds_api_league_id_canonicalization_regressed_2026_07_28.md`**
> (`depends_on` + `gate_on_depends: true`) — the dispatcher will not queue the todo below until that issue doc's raw
> re-fix todo is `done`. Do not re-dispatch this manually before then; re-running the reprocess against a still-dirty
> raw `batch_odds_api` shape cannot reach this todo's own done-when (Constraint 2 — MDPS derives its output partition
> from the raw content column, not the GCS path).

## Todos

- [ ] [CODE] P1. **Re-run the MDPS `odds_horizon_bucket` reprocess (Step 7 of the league_id namespace migration).**
      `market-data-processing-service/.../reprocess_sports_odds.py` must be re-run for the historical days so its
      `bucketed.parquet` output regenerates under the now-canonical `league_id=` partition. **Mitigate the features
      double-count hazard** (STOP condition 7 in `issues/sports_league_id_namespace_migration_2026_07_20.md`): do the
      reprocess + stale-object delete inside a drained per-day window, not as a slow background copy — the script's
      own `_delete_stale_shards` reconcile (per-date, synchronous within `_write_bucketed_output`) already covers this,
      confirmed by reading `reprocess_sports_odds.py` 2026-07-28 (slot 12). **Done when**: a fresh live manifest census
      (`read_availability_index(bucket, columns=["league_id","pipeline_mode"])`, `pipeline_mode=batch_mdps_odds_horizon_bucket`,
      values checked against the full `unified_api_contracts.canonical.domain.sports.league_data.LEAGUE_REGISTRY` key
      set — not a narrower check) shows 0 rows carrying a non-registry `league_id`, AND a features read for a
      migrated day returns a single non-doubled row set. (repo: market-data-processing-service)

## Progress Log

### 2026-07-28 (slot-12) — extracted from `sports_track_h_denominator_prereqs_2026_07_28.md`, machine-gated

Dispatched `sports_track_h_denominator_prereqs-001` (this todo, then living in
`sports_track_h_denominator_prereqs_2026_07_28.md`). Before launching the multi-hour multi-VM reprocess job, verified
the todo's own stated prerequisite with a fresh manifest census — it does not hold: raw `batch_odds_api` still carries
99,607 non-registry `league_id` rows (full detail + method:
`issues/sports_batch_odds_api_league_id_canonicalization_regressed_2026_07_28.md`). Declined to launch the reprocess
(would not reach done-when; a 3rd blind run of this exact job already flagged wasteful once,
`issues/mdps_odds_horizon_bucket_launch_prep_stale_todo_duplicate_dispatch_2026_07_27.md`). Filed the issue doc,
escalated via `/blocked` (`BLK-ad4aa20d`); operator answered A (leave unchecked, route the raw re-fix through the
backlog, machine-gate this todo on it) — this doc + gate is that instruction executed. The original
`sports_track_h_denominator_prereqs_2026_07_28.md` now carries a non-checkbox pointer here instead of this todo
(its sibling `batch_footystats` todo is unaffected — independent work, ungated).
